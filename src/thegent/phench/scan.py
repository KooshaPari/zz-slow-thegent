from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_EXCLUDED_REPOS,
    SCAN_SHARED_REPOS_DEFAULT_MODULE_PREFIX,
    SCAN_SHARED_REPOS_MANIFEST_AUDIT_FILENAME,
    SCAN_SHARED_REPOS_MANIFEST_INDEX_FILENAME,
    SCAN_SHARED_REPOS_MANIFEST_INDEX_SUMMARY_FILENAME,
    SCAN_SHARED_REPOS_MAX_NAME_LENGTH,
    SCAN_SHARED_REPOS_RECOMMENDED_MODULE_COUNT_LIMIT,
    SCAN_SHARED_REPOS_ROOT_MODE_REPOS,
    SCAN_SHARED_REPOS_ROOT_MODE_WORKTREES,
    SCAN_SHARED_REPOS_SCHEMA_VERSION,
)
from .git_ops import sanitize_repo_id
from .helpers import _repo_id_from_path
from .modules import build_module_manifest_payload
from .paths import module_manifests_root, phenotype_root
from .store import utc_now_iso

__all__ = [
    "build_scan_candidates",
    "materialize_module_candidate_manifest",
    "materialize_scan_candidate_manifest",
    "scan_shared_modules_across_repos",
]


def _append_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def _sorted_repo_paths(repo_paths: dict[str, str]) -> dict[str, str]:
    return {repo_id: repo_paths[repo_id] for repo_id in sorted(repo_paths)}


def _ensure_non_symlink_path(path: Path) -> None:
    current = path
    while current != current.parent:
        if current.exists() and current.is_symlink():
            raise ValueError(f"path component is a symlink: {current}")
        current = current.parent


def _normalize_candidate_module_name(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    return slug or "module"


def _truncate_module_name(
    value: str, *, max_length: int = SCAN_SHARED_REPOS_MAX_NAME_LENGTH
) -> str:
    return value[:max_length] if len(value) > max_length else value


def _candidate_conflict_suffix(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def _build_candidate_name(base: str, *, suffix: str | None = None) -> str:
    if suffix:
        suffix_fragment = f"-{suffix}"
        allowed = max(SCAN_SHARED_REPOS_MAX_NAME_LENGTH - len(suffix_fragment), 1)
        base_prefix = _truncate_module_name(base, max_length=allowed)
        return f"{base_prefix}{suffix_fragment}"
    return _truncate_module_name(base)


def _build_scannable_candidate_name(
    base: str, used_names: set[str], *, max_attempts: int = 25
) -> str:
    attempt = 0
    candidate_name = _build_candidate_name(base)
    while candidate_name in used_names:
        attempt += 1
        if attempt > max_attempts:
            raise RuntimeError(f"unable to resolve unique candidate name for: {base}")
        candidate_name = _build_candidate_name(
            base, suffix=_candidate_conflict_suffix(f"{base}:{attempt}")
        )
    return candidate_name


def _build_recommended_modules(
    shared_modules: dict[str, list[str]],
    depends_on_by_module: dict[str, set[str]] | None = None,
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for module_name, repos in shared_modules.items():
        if not repos:
            continue
        depends_on = (
            sorted(depends_on_by_module.get(module_name, set()))
            if depends_on_by_module
            else []
        )
        recommendations.append(
            {
                "module": module_name,
                "repo_count": len(repos),
                "repo_ids": sorted(repos),
                "depends_on_count": len(depends_on),
                "depends_on": depends_on,
            }
        )
    return sorted(
        recommendations,
        key=lambda item: (
            -item["repo_count"],
            -item["depends_on_count"],
            item["module"],
        ),
    )


def _read_index_payload(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    existing = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(existing, list):
        raise ValueError(f"invalid manifest index format: {path}")
    payload: list[dict[str, Any]] = []
    for item in existing:
        if not isinstance(item, dict):
            continue
        payload.append(item)
    return payload


def _write_json_lines(path: Path, payload: dict[str, Any]) -> None:
    _ensure_non_symlink_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload) + "\n")


def _build_candidate_manifest_index_summary(
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    module_names = sorted(
        {str(item.get("module_name", "")) for item in entries if isinstance(item, dict)}
    )
    module_manifest_paths = {
        item.get("module_name", ""): str(item.get("manifest_path", ""))
        for item in entries
        if isinstance(item, dict) and item.get("module_name")
    }
    return {
        "generated_at": utc_now_iso(),
        "module_count": len(module_names),
        "manifest_count": len(entries),
        "module_names": module_names,
        "module_manifest_paths": module_manifest_paths,
    }


def _validate_candidate_name_regex(pattern: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"invalid candidate-name regex: {pattern}") from exc


def _candidate_manifest_path(output_dir: Path, module_name: str) -> Path:
    return output_dir / module_name / "manifest.json"


def _read_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"manifest content must be a JSON object: {path}")
    return payload


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    _ensure_non_symlink_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _resolve_candidate_inclusion(
    *,
    candidates: bool,
    omit_candidates: bool,
) -> bool:
    if candidates and omit_candidates:
        raise ValueError("cannot set both --candidates and --omit-candidates")
    return bool(candidates) and not omit_candidates


def _validate_excluded_repo_ids(exclude_repos: Iterable[str]) -> set[str]:
    normalized: set[str] = set()
    for repo_name in exclude_repos:
        candidate = repo_name.strip()
        if not candidate:
            raise ValueError("exclude repo id cannot be blank")
        sanitized = sanitize_repo_id(candidate)
        if sanitized != candidate:
            raise ValueError(f"invalid repo id: {candidate}")
        normalized.add(sanitized)
    return normalized


def _collect_candidate_repos(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if not root.is_dir():
        return []
    return sorted(
        [
            entry
            for entry in root.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        ]
    )


def _resolve_worktree_roots() -> list[Path]:
    base_root = phenotype_root()
    return sorted(
        [
            entry
            for entry in base_root.iterdir()
            if entry.is_dir() and entry.name.endswith("-wtrees")
        ]
    )


def _collect_worktree_repos(root: Path) -> list[Path]:
    if root.name == "src":
        return [root.parent]
    if root.name.endswith("-wtrees"):
        return _collect_candidate_repos(root)
    if (root / "src").exists():
        return [root]
    return _collect_candidate_repos(root)


def _repos_root_metadata(
    repos_root: Path | None,
    root_mode: str,
) -> tuple[Path, list[Path], str, list[str]]:
    if root_mode not in {
        SCAN_SHARED_REPOS_ROOT_MODE_REPOS,
        SCAN_SHARED_REPOS_ROOT_MODE_WORKTREES,
    }:
        raise ValueError(
            f"repos_root_mode must be one of: {SCAN_SHARED_REPOS_ROOT_MODE_REPOS}, {SCAN_SHARED_REPOS_ROOT_MODE_WORKTREES}"
        )

    warnings: list[str] = []
    phenotype = phenotype_root()
    base_root = repos_root if repos_root is not None else None
    if base_root is None:
        if root_mode == SCAN_SHARED_REPOS_ROOT_MODE_REPOS:
            base_root = phenotype / "repos"
            hint = f"defaulted repos_root to {base_root} using repos_root_mode={root_mode}; pass --repos-root to override"
            return base_root, _collect_candidate_repos(base_root), hint, []

        worktree_roots = _resolve_worktree_roots()
        candidate_paths: list[Path] = []
        for worktree_root in worktree_roots:
            candidate_paths.extend(_collect_worktree_repos(worktree_root))
        hint = "resolved worktree scan roots from phenotype_root/*-wtrees"
        if not candidate_paths:
            _append_warning(
                warnings,
                "no worktree roots found under phenotype_root; verify -wtrees directories exist",
            )
        return phenotype, sorted(candidate_paths), hint, warnings

    explicit_root = base_root.expanduser().resolve()
    if not explicit_root.exists():
        _append_warning(warnings, f"repos_root does not exist: {explicit_root}")
        return (
            explicit_root,
            [],
            f"explicit repos_root provided but path missing: {explicit_root}",
            warnings,
        )
    if root_mode == SCAN_SHARED_REPOS_ROOT_MODE_REPOS:
        hint = f"scanning repos mode from explicit root: {explicit_root}"
        if phenotype not in explicit_root.parents and explicit_root != phenotype:
            _append_warning(
                warnings,
                "scan configured outside THGENT_PHENOTYPE_ROOT; explicit repo path provenance retained in result",
            )
        return explicit_root, _collect_candidate_repos(explicit_root), hint, warnings

    hint = f"scanning worktrees from explicit root: {explicit_root}"
    if explicit_root.name.endswith("-wtrees"):
        _append_warning(
            warnings, "scanning nested worktree directory with -wtrees suffix"
        )
    if (explicit_root / "src").exists() and explicit_root.name != "src":
        hint = f"explicit worktree-style repo root provided: {explicit_root}"
    return explicit_root, _collect_worktree_repos(explicit_root), hint, warnings


def _find_repo_modules(repo_path: Path) -> set[str]:
    src_root = repo_path / "src"
    if not src_root.exists() or not src_root.is_dir():
        return set()
    modules: set[str] = set()
    for child in src_root.iterdir():
        if not child.is_dir():
            continue
        if not (child / "__init__.py").exists():
            continue
        modules.add(child.name)
    return modules


def _collect_shared_modules(
    repo_modules: dict[str, set[str]],
    *,
    min_repo_count: int = 2,
) -> dict[str, list[str]]:
    return {
        module_name: sorted(repos)
        for module_name, repos in repo_modules.items()
        if len(repos) >= min_repo_count
    }


def _iter_repo_python_files(repo_path: Path) -> list[Path]:
    files: list[Path] = []
    src_root = repo_path / "src"
    if not src_root.exists():
        return files
    for file_path in src_root.rglob("*.py"):
        if file_path.is_file():
            files.append(file_path)
    return files


def _extract_imports_from_python(code: str) -> set[str]:
    imports: set[str] = set()
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(str(exc)) from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue
            if node.module:
                imports.add(node.module)
    return imports


def _resolve_candidate_dependency(
    imported_name: str,
    known_modules: set[str],
    current_module: str,
) -> str | None:
    parts = imported_name.split(".")
    if not parts:
        return None
    candidate = parts[0]
    if candidate == current_module:
        return None
    if candidate in known_modules:
        return candidate
    return None


def _find_repo_module_dependencies(
    repo_path: Path,
) -> tuple[dict[str, set[str]], list[dict[str, str]]]:
    modules = _find_repo_modules(repo_path)
    if not modules:
        return {}, []

    dependencies: dict[str, set[str]] = {module: set() for module in modules}
    warnings: list[dict[str, str]] = []

    for py_file in _iter_repo_python_files(repo_path):
        try:
            imports = _extract_imports_from_python(py_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            warnings.append(
                {
                    "repo_file": str(py_file),
                    "reason": "python-parse-error",
                    "detail": str(exc),
                }
            )
            continue

        module_name = py_file.relative_to(repo_path).parts
        if len(module_name) < 2 or module_name[0] != "src":
            continue
        current_module = module_name[1]
        if current_module not in modules:
            continue
        for imported in imports:
            dep = _resolve_candidate_dependency(imported, modules, current_module)
            if dep is not None:
                dependencies[current_module].add(dep)

    return dependencies, warnings


def build_scan_candidates(
    shared_modules: dict[str, list[str]],
    *,
    module_prefix: str = SCAN_SHARED_REPOS_DEFAULT_MODULE_PREFIX,
    depends_on_by_module: dict[str, set[str]] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    used_names: set[str] = set()

    for module_name, repos in sorted(shared_modules.items(), key=lambda item: item[0]):
        if not repos:
            continue
        sorted_repos = sorted(repos)
        prefix = _normalize_candidate_module_name(module_prefix)
        base = _normalize_candidate_module_name(module_name)
        candidate_name = _build_scannable_candidate_name(
            f"{prefix}-{base}-{len(sorted_repos)}", used_names
        )
        used_names.add(candidate_name)

        depends_on = (
            sorted(depends_on_by_module.get(module_name, set()))
            if depends_on_by_module
            else []
        )

        manifest_template = build_module_manifest_payload(module_name, sorted_repos)
        candidates.append(
            {
                "module": module_name,
                "module_name": candidate_name,
                "repo_ids": sorted_repos,
                "repo_count": len(sorted_repos),
                "depends_on_count": len(depends_on),
                "depends_on": depends_on,
                "manifest_template": manifest_template,
            }
        )

    return sorted(
        candidates,
        key=lambda item: (
            -item["repo_count"],
            -item["depends_on_count"],
            item["module"],
            item["module_name"],
        ),
    )


def materialize_scan_candidate_manifest(
    candidate: dict[str, Any],
    *,
    output_dir: Path,
    dry_run: bool = False,
    update_index: bool = True,
) -> dict[str, Any]:
    module_name = str(candidate.get("module_name", "")).strip()
    repo_ids = candidate.get("repo_ids", [])
    if not module_name:
        raise ValueError("candidate module_name cannot be empty")
    if not isinstance(repo_ids, list):
        raise ValueError("candidate repo_ids must be a list")
    if (
        not isinstance(module_name, str)
        or "/" in module_name
        or "\\" in module_name
        or ".." in module_name
    ):
        raise ValueError(f"invalid module_name: {module_name}")

    manifest_path = _candidate_manifest_path(output_dir, module_name)
    manifest_before: dict[str, Any] | None = None
    if manifest_path.exists():
        manifest_before = _read_json_dict(manifest_path)
    manifest_payload = candidate.get("manifest_template")
    if not isinstance(manifest_payload, dict):
        manifest_payload = build_module_manifest_payload(
            str(candidate.get("module", "")), [str(repo_id) for repo_id in repo_ids]
        )

    if not dry_run and manifest_before is not None:
        if manifest_before != manifest_payload:
            raise ValueError(
                f"manifest conflict for {module_name}; existing file differs: {manifest_path}"
            )

    if not dry_run:
        _write_manifest(manifest_path, manifest_payload)

    index_path = output_dir / SCAN_SHARED_REPOS_MANIFEST_INDEX_FILENAME
    existing_index = _read_index_payload(index_path) if update_index else []
    index_entry = {
        "module_name": module_name,
        "manifest_path": str(manifest_path),
        "repo_count": len(repo_ids),
        "generated_at": utc_now_iso(),
    }
    next_index = deepcopy(existing_index)
    if update_index:
        updated = False
        for entry in next_index:
            if not isinstance(entry, dict):
                continue
            if entry.get("module_name") == module_name:
                entry.update(deepcopy(index_entry))
                updated = True
                break
        if not updated:
            next_index.append(index_entry)
        next_index = sorted(next_index, key=lambda item: str(item.get("module_name")))

    index_summary_path = output_dir / SCAN_SHARED_REPOS_MANIFEST_INDEX_SUMMARY_FILENAME
    index_summary_payload = _build_candidate_manifest_index_summary(
        next_index if update_index else existing_index
    )

    audit_path = output_dir / SCAN_SHARED_REPOS_MANIFEST_AUDIT_FILENAME
    _ensure_non_symlink_path(manifest_path)
    _ensure_non_symlink_path(index_path)
    _ensure_non_symlink_path(index_summary_path)
    _ensure_non_symlink_path(audit_path)
    audit_entry = {
        "event": "manifest-materialization",
        "timestamp": utc_now_iso(),
        "module": str(candidate.get("module", "")),
        "module_name": module_name,
        "manifest_path": str(manifest_path),
        "repo_ids": sorted([str(repo_id) for repo_id in repo_ids]),
        "dry_run": dry_run,
        "index_updated": bool(update_index),
    }

    if not dry_run and update_index:
        index_path.write_text(json.dumps(next_index, indent=2) + "\n", encoding="utf-8")
        index_summary_path.write_text(
            json.dumps(index_summary_payload, indent=2) + "\n", encoding="utf-8"
        )
        _write_json_lines(audit_path, audit_entry)

    result = {
        "module": str(candidate.get("module", "")),
        "module_name": module_name,
        "manifest_path": str(manifest_path),
        "repos": sorted([str(repo_id) for repo_id in repo_ids]),
        "manifest_payload": manifest_payload,
        "manifest_after": manifest_payload,
        "dry_run": dry_run,
        "manifest_before": manifest_before,
        "index_before": existing_index if update_index else None,
        "index_after": next_index if update_index else None,
        "index_summary": index_summary_payload,
        "index_summary_path": str(index_summary_path),
    }

    return result


def scan_shared_modules_across_repos(
    repos_root: Path | None = None,
    *,
    exclude_repos: set[str] | None = None,
    min_repo_count: int = 2,
    repos_root_mode: str | None = None,
    candidate_name_regex: str | None = None,
    candidates: bool = False,
    omit_candidates: bool = False,
) -> dict[str, Any]:
    if min_repo_count < 2:
        raise ValueError("min_repo_count must be at least 2")

    root_mode = repos_root_mode or SCAN_SHARED_REPOS_ROOT_MODE_REPOS
    root, candidate_paths, root_mode_hint, warnings = _repos_root_metadata(
        repos_root, root_mode
    )
    if not candidate_paths:
        return {
            "scan_schema_version": SCAN_SHARED_REPOS_SCHEMA_VERSION,
            "repos_root": str(root),
            "repos_root_mode": root_mode,
            "root_mode_hint": root_mode_hint,
            "warnings": warnings,
            "repo_paths": {},
            "shared_modules": {},
            "shared_count": 0,
            "module_count": 0,
            "repo_count": 0,
            "excluded_repos": sorted(DEFAULT_EXCLUDED_REPOS),
            "examined_repos": [],
            "min_repo_count": min_repo_count,
            "module_candidates": [],
            "recommended_modules": [],
        }

    excluded = _validate_excluded_repo_ids(exclude_repos or set())
    effective_excludes = sorted(DEFAULT_EXCLUDED_REPOS | excluded)
    repo_modules: dict[str, set[str]] = {}
    repo_dependencies: dict[str, set[str]] = {}
    warnings = list(warnings)

    if candidate_name_regex is not None:
        compiled_name_regex = _validate_candidate_name_regex(candidate_name_regex)
    else:
        compiled_name_regex = None

    examined_repos: list[str] = []
    repo_paths: dict[str, str] = {}
    for repo_path in candidate_paths:
        repo_id = _repo_id_from_path(repo_path)
        if repo_id in effective_excludes:
            continue
        examined_repos.append(repo_id)
        repo_paths[repo_id] = str(repo_path)
        modules = _find_repo_modules(repo_path)
        for module_name in modules:
            repo_modules.setdefault(module_name, set()).add(repo_id)

        module_dependencies, dep_warnings = _find_repo_module_dependencies(repo_path)
        for dep_module, deps in module_dependencies.items():
            repo_dependencies.setdefault(dep_module, set()).update(deps)
        for dep_warning in dep_warnings:
            _append_warning(
                warnings, f"{dep_warning['repo_file']}: {dep_warning['reason']}"
            )

    shared_modules = _collect_shared_modules(
        repo_modules, min_repo_count=min_repo_count
    )
    include_candidates = _resolve_candidate_inclusion(
        candidates=candidates,
        omit_candidates=omit_candidates,
    )
    candidates = (
        []
        if not include_candidates
        else build_scan_candidates(
            shared_modules, depends_on_by_module=repo_dependencies
        )
    )
    if compiled_name_regex is not None:
        if not include_candidates:
            _append_warning(
                warnings, "candidate-name-regex ignored when candidates are omitted"
            )
        else:
            candidates = [
                item
                for item in candidates
                if compiled_name_regex.search(str(item.get("module", "")))
            ]

    recommendations = _build_recommended_modules(
        shared_modules, depends_on_by_module=repo_dependencies
    )[:SCAN_SHARED_REPOS_RECOMMENDED_MODULE_COUNT_LIMIT]

    return {
        "scan_schema_version": SCAN_SHARED_REPOS_SCHEMA_VERSION,
        "repos_root": str(root),
        "repos_root_mode": root_mode,
        "shared_modules": shared_modules,
        "root_mode_hint": root_mode_hint,
        "warnings": warnings,
        "repo_paths": _sorted_repo_paths(repo_paths),
        "shared_count": len(shared_modules),
        "module_count": len(repo_modules),
        "repo_count": len(examined_repos),
        "excluded_repos": effective_excludes,
        "examined_repos": examined_repos,
        "min_repo_count": min_repo_count,
        "module_candidates": candidates,
        "recommended_modules": recommendations,
    }


def materialize_module_candidate_manifest(
    module: str,
    *,
    repos_root: Path | None = None,
    repos_root_mode: str | None = None,
    repos: list[str] | None = None,
    min_repo_count: int = 2,
    module_prefix: str = SCAN_SHARED_REPOS_DEFAULT_MODULE_PREFIX,
    output_dir: Path | None = None,
    dry_run: bool = False,
    update_index: bool = True,
) -> dict[str, Any]:
    if not module.strip():
        raise ValueError("module name cannot be empty")
    if min_repo_count < 2:
        raise ValueError("min_repo_count must be at least 2")

    state = scan_shared_modules_across_repos(
        repos_root=repos_root,
        repos_root_mode=repos_root_mode,
        min_repo_count=min_repo_count,
    )
    shared_modules = state.get("shared_modules")
    if not isinstance(shared_modules, dict) or module not in shared_modules:
        raise ValueError(
            f"module {module} is not shared at min_repo_count={min_repo_count}"
        )

    selected_repos = sorted(shared_modules[module])
    if repos:
        selected_repos = sorted(set(repos) & set(selected_repos))
        if len(selected_repos) < min_repo_count:
            raise ValueError(
                f"module {module} has insufficient pinned repos after filtering: {len(selected_repos)} < {min_repo_count}"
            )

    candidates = build_scan_candidates(
        {module: selected_repos}, module_prefix=module_prefix
    )
    if not candidates:
        raise ValueError(f"module {module} has no qualifying repos")
    candidate = candidates[0]
    target_output_dir = (output_dir or module_manifests_root()).expanduser().resolve()
    return materialize_scan_candidate_manifest(
        candidate,
        output_dir=target_output_dir,
        dry_run=dry_run,
        update_index=update_index,
    )
