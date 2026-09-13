from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .config import (
    _REFRESH_CADENCE_RE,
    DEFAULT_MODULE_REFRESH_CADENCE,
    DEFAULT_SHARED_MODULE_REPO_EXCLUDE,
    SUPPORTED_MODULE_MANIFEST_SCHEMA_VERSIONS,
)
from .discovery import discover_local_git_repos
from .helpers import (
    _select_module_repos,
)
from .models import ModuleManifest
from .paths import (
    phenotype_repos_root,
    projects_modules_root,
    validate_family_name,
)


def _manifest_payload_repo_ids(payload: Any) -> list[str] | None:
    if not isinstance(payload, dict):
        return None
    raw_ids = payload.get("repo_ids")
    if not isinstance(raw_ids, list):
        return None
    repo_ids: list[str] = []
    for value in raw_ids:
        if not isinstance(value, str):
            return None
        repo_ids.append(value)
    return repo_ids


def _compatible_module_manifest(existing_payload: Any, next_payload: Any) -> bool:
    if existing_payload == next_payload:
        return True
    existing_ids = _manifest_payload_repo_ids(existing_payload)
    next_ids = _manifest_payload_repo_ids(next_payload)
    if existing_ids is None or next_ids is None:
        return False
    existing_core = dict(existing_payload)
    next_core = dict(next_payload)
    existing_core.pop("repo_ids", None)
    next_core.pop("repo_ids", None)
    if existing_core != next_core:
        return False
    return set(existing_ids).issubset(next_ids) or set(next_ids).issubset(existing_ids)


def _normalize_name_list(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        name = value.strip()
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        normalized.append(name)
    return normalized


def _normalize_name_set(values: list[str] | None) -> set[str]:
    return set(_normalize_name_list(values))


def _resolve_module_manifest_path(module: str) -> Path:
    from .paths import (
        module_manifest_path,
        phenotype_root,
        projects_modules_root,
    )

    normalized_module = module.strip()
    if not normalized_module:
        raise ValueError("module manifest not found: <empty>")

    is_path_like = ("/" in normalized_module) or ("\\" in normalized_module)
    candidates: list[Path] = []

    def _add(path: Path) -> None:
        manifest_path = path if path.name == "manifest.json" else path / "manifest.json"
        if manifest_path not in candidates:
            candidates.append(manifest_path)

    if is_path_like:
        explicit_path = Path(normalized_module).expanduser()
        _add(explicit_path)
        if not explicit_path.is_absolute():
            _add(phenotype_root() / explicit_path)

        if explicit_path.is_absolute() and explicit_path.exists():
            if explicit_path.is_file() and explicit_path.name == "manifest.json":
                return explicit_path
            if explicit_path.is_dir() and (explicit_path / "manifest.json").exists():
                return explicit_path / "manifest.json"

        normalized_parts = [part.lower() for part in explicit_path.as_posix().split("/")]
        if "modules" in normalized_parts:
            modules_index = normalized_parts.index("modules")
            if modules_index + 1 < len(normalized_parts):
                _add(projects_modules_root() / normalized_parts[modules_index + 1])
        else:
            _add(projects_modules_root() / explicit_path.name)

        for candidate in candidates:
            if candidate.exists():
                return candidate
    else:
        module_name = validate_family_name(normalized_module)
        module_path = module_manifest_path(module_name)
        _add(module_path)
        if module_path.exists():
            return module_path

    raise ValueError(f"module manifest not found: {module}")


def _validate_module_repos_payload_field(
    payload: dict[str, Any],
    *,
    field: str,
) -> list[str]:
    raw = payload.get(field)
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"module manifest field '{field}' must be a list")
    values: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            raise ValueError(f"module manifest field '{field}' contains non-string entry")
        repo_id = value.strip()
        if not repo_id:
            continue
        values.append(repo_id)
    return values


def _validate_module_repos_payload_map(
    payload: dict[str, Any],
    *,
    field: str,
) -> dict[str, str]:
    raw = payload.get(field)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"module manifest field '{field}' must be an object")
    items: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ValueError(f"module manifest field '{field}' contains non-string key")
        repo_id = key.strip()
        if not repo_id:
            raise ValueError(f"module manifest field '{field}' contains empty repo id")
        if not isinstance(value, str):
            raise ValueError(f"module manifest field '{field}' requires string values")
        item = value.strip()
        if not item:
            raise ValueError(f"module manifest field '{field}' for repo '{repo_id}' must not be empty")
        items[repo_id] = item
    return items


def _validate_module_manifest_schema_version(
    module: str,
    payload: dict[str, Any],
) -> int:
    schema_version = payload.get("schema_version")
    if schema_version is None:
        return 1
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise ValueError(f"module manifest '{module}' schema_version must be an integer")
    if schema_version not in SUPPORTED_MODULE_MANIFEST_SCHEMA_VERSIONS:
        raise ValueError(f"module manifest '{module}' has unsupported schema_version: {schema_version}")
    return schema_version


def _validate_module_owners(payload: dict[str, Any], *, field: str) -> list[str]:
    raw = payload.get(field)
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"module manifest field '{field}' must be a list")
    owners: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            raise ValueError(f"module manifest field '{field}' contains non-string entry")
        owner = item.strip()
        if not owner:
            continue
        normalized_owner = owner.lower()
        if normalized_owner in seen:
            continue
        seen.add(normalized_owner)
        owners.append(normalized_owner)
    return owners


def _validate_module_refresh_cadence(payload: dict[str, Any], *, field: str) -> str:
    raw = payload.get(field, DEFAULT_MODULE_REFRESH_CADENCE)
    if not isinstance(raw, str):
        raise ValueError(f"module manifest field '{field}' must be a string")
    cadence = raw.strip().lower()
    if not cadence:
        raise ValueError(f"module manifest field '{field}' cannot be empty")
    if not _REFRESH_CADENCE_RE.match(cadence):
        raise ValueError(
            f"module manifest field '{field}' must be one of "
            f"never, manual, daily, weekly, monthly, yearly, hourly, every-<duration>"
        )
    return cadence


def _normalize_repo_id_list(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        repo_id = value.strip()
        if not repo_id:
            continue
        if repo_id in seen:
            continue
        seen.add(repo_id)
        normalized.append(repo_id)
    return normalized


__all__ = [
    "audit_shared_modules",
    "audit_shared_modules_across_repos",
    "build_module_manifest_payload",
    "list_modules",
    "load_module_manifest",
    "load_module_repos",
    "sync_project_modules_from_repos",
]


def audit_shared_modules(target: str, family: str | None = None) -> dict[str, Any]:
    from . import service as _svc

    lock = _svc.load_target_lock(target, family=family)
    module_map: dict[str, list[str]] = {}
    for repo in lock.repos:
        src_root = Path(repo.repo_path) / "src"
        if not src_root.exists() or not src_root.is_dir():
            continue
        for child in src_root.iterdir():
            if not child.is_dir():
                continue
            if not (child / "__init__.py").exists():
                continue
            owners = module_map.setdefault(child.name, [])
            owners.append(repo.repo_id)

    shared = {module: sorted(set(owners)) for module, owners in module_map.items() if len(set(owners)) >= 2}
    return {
        "target": target,
        "shared_modules": shared,
        "repo_count": len(lock.repos),
        "module_count": len(module_map),
    }


def audit_shared_modules_across_repos(
    *,
    source_root: Path | None = None,
    include_repos: list[str] | None = None,
    exclude_repos: list[str] | None = None,
    min_repo_count: int = 2,
    exclude_modules: list[str] | None = None,
    include_modules: list[str] | None = None,
    include_repo_modules_root: bool = True,
    skip_repos: list[str] | None = None,
) -> dict[str, Any]:
    source = source_root or phenotype_repos_root()
    include_specs = _normalize_name_list(include_repos)
    exclude_specs = _normalize_name_set(exclude_repos)
    additional_excludes = _normalize_name_set(skip_repos)
    effective_excludes = sorted(exclude_specs | DEFAULT_SHARED_MODULE_REPO_EXCLUDE | additional_excludes)
    excluded_modules = _normalize_name_set(exclude_modules)
    included_modules = _normalize_name_set(include_modules)

    candidates = discover_local_git_repos(
        root=source,
        include=include_specs or None,
        exclude=effective_excludes or None,
    )

    repo_paths: list[tuple[str, Path]] = []
    for candidate in candidates:
        if candidate.repo_id in additional_excludes:
            continue
        repo_paths.append((candidate.repo_id, candidate.path))

    discovered_module_map: dict[str, set[str]] = {}
    shared_candidate_module_map: dict[str, set[str]] = {}
    for repo_id, repo_path in repo_paths:
        src_root = repo_path / "src"
        if src_root.exists() and src_root.is_dir():
            for child in src_root.iterdir():
                if not child.is_dir():
                    continue
                if not (child / "__init__.py").exists():
                    continue
                module = child.name
                if included_modules and module not in included_modules:
                    continue
                if module in excluded_modules:
                    continue
                discovered_module_map.setdefault(module, set()).add(repo_id)

        if include_repo_modules_root:
            modules_root = repo_path / "modules"
            if not (modules_root.exists() and modules_root.is_dir()):
                continue
            for child in modules_root.iterdir():
                if not child.is_dir() or not (child / "manifest.json").is_file():
                    continue
                module = child.name
                if included_modules and module not in included_modules:
                    continue
                if module in excluded_modules:
                    continue
                shared_candidate_module_map.setdefault(module, set()).add(repo_id)

    shared_modules = {
        module: sorted(repos)
        for module, repos in (
            shared_candidate_module_map if include_repo_modules_root else discovered_module_map
        ).items()
        if len(repos) >= max(min_repo_count, 2)
    }

    discovered_modules = {module: set(repos) for module, repos in discovered_module_map.items()}
    if include_repo_modules_root:
        for module, repos in shared_candidate_module_map.items():
            discovered_modules.setdefault(module, set()).update(repos)
        discovered_modules = {module: sorted(repos) for module, repos in discovered_modules.items()}
    existing = set(list_modules())
    candidate_modules = sorted(
        module for module, repos in shared_modules.items() if include_repo_modules_root and module not in existing
    )

    return {
        "source_root": str(source),
        "repo_count": len(repo_paths),
        "module_count": len(discovered_modules),
        "shared_modules": shared_modules,
        "shared_module_count": len(shared_modules),
        "moduleization_candidates": candidate_modules,
        "excluded_repos": effective_excludes,
        "excluded_modules": sorted(excluded_modules),
        "module_repo_map": discovered_modules,
        "include_repo_modules_root": bool(include_repo_modules_root),
    }


def sync_project_modules_from_repos(
    *,
    source_root: Path | None = None,
    destination_root: Path | None = None,
    include_repos: list[str] | None = None,
    exclude_repos: list[str] | None = None,
    include_modules: list[str] | None = None,
    exclude_modules: list[str] | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    source = source_root or phenotype_repos_root()
    destination = destination_root or projects_modules_root()
    destination = destination_root
    if destination is None:
        candidate = source.parent / "projects" / "modules" if source_root is not None else None
        if (
            os.environ.get("THGENT_PHENOTYPE_ROOT") is None
            and candidate is not None
            and candidate.as_posix() != projects_modules_root().as_posix()
        ):
            destination = candidate
        else:
            destination = projects_modules_root()
    include_specs = _normalize_name_list(include_repos)
    exclude_specs = _normalize_name_set(exclude_repos)
    effective_excludes = sorted(exclude_specs | DEFAULT_SHARED_MODULE_REPO_EXCLUDE)
    included_modules = _normalize_name_set(include_modules)
    excluded_modules = _normalize_name_set(exclude_modules)

    discovered_repos = discover_local_git_repos(
        root=source,
        include=include_specs or None,
        exclude=effective_excludes or None,
    )

    discovered: dict[str, Path] = {}
    discovered_from: dict[str, str] = {}
    for repo_candidate in discovered_repos:
        modules_root = repo_candidate.path / "modules"
        if not modules_root.exists() or not modules_root.is_dir():
            continue
        for entry in modules_root.iterdir():
            if not entry.is_dir():
                continue
            module_name = entry.name
            if included_modules and module_name not in included_modules:
                continue
            if module_name in excluded_modules:
                continue
            manifest = entry / "manifest.json"
            if not manifest.is_file():
                continue
            payload = manifest.read_text(encoding="utf-8")
            try:
                parsed = json.loads(payload)
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"invalid module manifest in {repo_candidate.repo_id}: {entry.name}") from exc

            if not isinstance(parsed, dict):
                raise ValueError(
                    f"invalid module manifest in {repo_candidate.repo_id}: {entry.name} payload must be an object"
                )

            existing_repo = discovered.get(module_name)
            if existing_repo is not None:
                with open(existing_repo, encoding="utf-8") as existing_stream:
                    existing_payload = json.load(existing_stream)
                if _compatible_module_manifest(existing_payload, parsed):
                    if set(_manifest_payload_repo_ids(existing_payload) or []) < set(
                        _manifest_payload_repo_ids(parsed) or []
                    ):
                        discovered[module_name] = manifest
                        discovered_from[module_name] = repo_candidate.repo_id
                    continue
                if not dry_run:
                    raise ValueError(
                        f"conflicting manifests for module '{module_name}': "
                        f"{discovered_from[module_name]} and {repo_candidate.repo_id}"
                    )
                continue

            discovered[module_name] = manifest
            discovered_from[module_name] = repo_candidate.repo_id

    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []

    for module_name, manifest in sorted(discovered.items()):
        destination_dir = destination / module_name
        destination_manifest = destination_dir / "manifest.json"
        payload_text = manifest.read_text(encoding="utf-8")
        if destination_manifest.exists() and not overwrite:
            skipped.append(module_name)
            continue
        if dry_run:
            if destination_manifest.exists():
                updated.append(module_name)
            else:
                created.append(module_name)
            continue

        destination_dir.mkdir(parents=True, exist_ok=True)
        parsed = json.loads(payload_text)
        is_new = not destination_manifest.exists()
        destination_manifest.write_text(
            json.dumps(parsed, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        if is_new:
            created.append(module_name)
        else:
            updated.append(module_name)

    return {
        "source_root": str(source),
        "destination_root": str(destination),
        "discovered_modules": sorted(discovered),
        "created": sorted(created),
        "updated": sorted(updated),
        "skipped": sorted(skipped),
        "dry_run": dry_run,
        "overwrite": overwrite,
    }


def list_modules() -> list[str]:
    root = projects_modules_root()
    if not root.exists():
        return []

    return sorted(entry.name for entry in root.iterdir() if entry.is_dir() and (entry / "manifest.json").is_file())


def build_module_manifest_payload(module_name: str, repo_ids: list[str]) -> dict[str, Any]:
    from .config import SCAN_SHARED_REPOS_SCHEMA_VERSION

    sorted_repos = sorted(repo_ids)
    return {
        "schema_version": SCAN_SHARED_REPOS_SCHEMA_VERSION,
        "repo_patterns": sorted_repos,
        "default_ref": "HEAD",
        "repo_ref_overrides": {},
        "repo_runner_overrides": {},
        "repo_command_overrides": {},
        "repo_env_profile_overrides": {},
        "matched_repos": sorted_repos,
    }


def load_module_manifest(module: str) -> ModuleManifest:
    manifest_path = _resolve_module_manifest_path(module)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid module manifest for {module}: malformed json") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"invalid module manifest for {module}: payload must be an object")

    schema_version = int(payload.get("schema_version", 1))
    if schema_version != 1:
        raise ValueError(f"unsupported schema version {schema_version} for manifest: {module}")

    owners: list[str] = []
    if "owners" in payload:
        _validate_module_owners(payload, field="owners")
        raw_owners = payload["owners"]
        if isinstance(raw_owners, list):
            seen: set[str] = set()
            for o in raw_owners:
                normalized = o.lower().strip()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    owners.append(normalized)

    refresh_cadence: str | None = None
    if "refresh_cadence" in payload:
        _validate_module_refresh_cadence(payload, field="refresh_cadence")
        refresh_cadence = str(payload["refresh_cadence"]).lower().strip()

    raw_patterns = payload.get("repo_patterns")
    if raw_patterns is None:
        repo_patterns: list[str] = ["*"]
    elif isinstance(raw_patterns, list) and all(isinstance(p, str) for p in raw_patterns):
        repo_patterns = raw_patterns
    else:
        raise ValueError(f"invalid repo_patterns in manifest: {module}")

    temp_manifest = ModuleManifest(schema_version=schema_version, repo_patterns=repo_patterns)
    selected_repos = _select_module_repos(temp_manifest)
    repo_ids = sorted(r.name for r in selected_repos)

    def _load_str_dict(key: str) -> dict[str, str]:
        raw = payload.get(key)
        if raw is None:
            return {}
        if not isinstance(raw, dict):
            raise ValueError(f"invalid {key} in manifest: {module}")
        return {str(k): str(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, str)}

    return ModuleManifest(
        schema_version=schema_version,
        repo_patterns=repo_patterns,
        owners=owners,
        refresh_cadence=refresh_cadence,
        default_ref=str(payload.get("default_ref", "HEAD")),
        repo_ids=repo_ids,
        repo_ref_overrides=_load_str_dict("repo_ref_overrides"),
        repo_runner_overrides=_load_str_dict("repo_runner_overrides"),
        repo_command_overrides=_load_str_dict("repo_command_overrides"),
        repo_env_profile_overrides=_load_str_dict("repo_env_profile_overrides"),
    )


def load_module_repos(
    module: str,
    *,
    available_repo_ids: list[str] | None = None,
) -> list[str]:
    return load_module_manifest(module, available_repo_ids=available_repo_ids)["repo_ids"]
