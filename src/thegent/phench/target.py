from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import (
    ENV_FILE,
    LOCK_FILE,
    PROFILE_FILE,
    RUNNER_FILE,
    RUNTIME_FILE,
    SNAPSHOT_DIR,
)
from .discovery import RepoCandidate, discover_local_git_repos
from .env_doctor import run_env_doctor
from .git_ops import (
    detect_head_branch,
    list_timeline,
    materialize_repo_checkout,
    resolve_ref_to_sha,
    sanitize_repo_id,
)
from .helpers import (
    _lock_hash,
    _parse_lock,
    _repo_id_from_path,
    _select_module_repos,
    _stable_payload_hash,
)


def _snapshot_id() -> str:
    import secrets
    from datetime import UTC, datetime

    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"


def _list_targets_in_root(root: Path, family_prefix: str | None) -> list[str]:
    found: list[str] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if (entry / ".phench" / LOCK_FILE).exists():
            if family_prefix is None:
                found.append(entry.name)
            else:
                found.append(f"{family_prefix}/{entry.name}")
    return sorted(found)


def _append_repo_selection(
    lock: TargetLock,
    repo_path: Path,
    selected_ref: str,
    *,
    module_name: str | None = None,
    selected_runner: str | None = None,
    selected_command: str | None = None,
    selected_env_profile: str | None = None,
    repo_id: str | None = None,
    worktree_path: str | None = None,
) -> None:
    rid = repo_id or _repo_id_from_path(repo_path)
    lock.repos = [entry for entry in lock.repos if entry.repo_id != rid]
    lock.repos.append(
        RepoSelection(
            repo_id=rid,
            repo_path=str(repo_path.resolve()),
            selected_ref=selected_ref,
            module_name=module_name,
            selected_runner=selected_runner,
            selected_command=selected_command,
            selected_env_profile=selected_env_profile,
            source_worktree_path=worktree_path,
            resolved_sha=None,
        )
    )


from .models import (
    ModuleManifest,
    RepoSelection,
    RunnerCatalog,
    RuntimeRepo,
    RuntimeState,
    TargetLock,
    TargetMode,
)
from .modules import load_module_manifest
from .paths import (
    mirror_target_state_root,
    phenotype_repos_root,
    projects_root,
    target_repos_root,
    target_root,
    target_state_root,
    validate_family_name,
)
from .runner import build_runner_catalog
from .store import dual_write, read_dual, sync_dual, utc_now_iso

__all__ = [
    "add_module_to_target",
    "add_repo",
    "bootstrap_target",
    "build_catalog",
    "create_target_snapshot",
    "discover_repos",
    "get_env_profile",
    "import_repos",
    "init_target",
    "list_target_snapshots",
    "list_targets",
    "load_target_lock",
    "lock_target",
    "materialize_target",
    "run_env_doctor_for_target",
    "set_env_profile",
    "set_repo_ref",
    "show_target_snapshot",
    "sync_target",
    "target_status",
    "target_timeline",
]


def import_repos(
    target: str,
    family: str | None = None,
    source_root: Path | None = None,
    selected_ref: str = "HEAD",
    preferred_runner: str | None = None,
    preferred_command: str | None = None,
    preferred_ref: str | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    repo_ids: list[str] | None = None,
    auto_lock: bool = True,
) -> TargetLock:
    """Import discovered repositories into an existing target."""
    repo_root = source_root or phenotype_repos_root()
    candidates = discover_local_git_repos(
        root=repo_root, include=include, exclude=exclude
    )
    if not candidates:
        raise ValueError(f"no repos discovered under: {repo_root}")

    by_id = {item.repo_id: item.path for item in candidates}
    if repo_ids:
        selected = []
        for repo_id in repo_ids:
            path = by_id.get(repo_id)
            if not path:
                raise ValueError(f"repo_id not discovered: {repo_id}")
            selected.append(RepoCandidate(repo_id=repo_id, path=path))
    else:
        selected = candidates

    for item in selected:
        add_repo(
            target,
            family=family,
            repo_path=str(item.path),
            selected_ref=selected_ref,
            repo_id=item.repo_id,
            preferred_runner=preferred_runner,
            preferred_command=preferred_command,
            preferred_ref=preferred_ref,
        )

    if auto_lock:
        return lock_target(target, family=family)
    return load_target_lock(target, family=family)


def create_target_snapshot(
    target: str,
    family: str | None = None,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    lock = load_target_lock(target, family=family)
    snapshot_id = snapshot_id or _snapshot_id()
    filename = f"{SNAPSHOT_DIR}/{snapshot_id}.json"

    runtime_payload: dict[str, Any] | None = None
    env_payload: dict[str, Any] | None = None
    runner_payload: dict[str, Any] | None = None

    try:
        runtime_payload = read_dual(target, RUNTIME_FILE, family=family)
    except FileNotFoundError:
        runtime_payload = None
    try:
        env_payload = read_dual(target, ENV_FILE, family=family)
    except FileNotFoundError:
        env_payload = None
    try:
        runner_payload = read_dual(target, RUNNER_FILE, family=family)
    except FileNotFoundError:
        runner_payload = None

    snapshot = {
        "snapshot_id": snapshot_id,
        "created_at_utc": utc_now_iso(),
        "target_name": target,
        "lock": asdict(lock),
        "lock_hash": lock.lock_hash,
        "runtime": runtime_payload,
        "env": env_payload,
        "runner_catalog": runner_payload,
    }
    snapshot["runtime_hash"] = (
        _stable_payload_hash(runtime_payload)
        if isinstance(runtime_payload, dict)
        else ""
    )
    snapshot["env_hash"] = (
        _stable_payload_hash(env_payload) if isinstance(env_payload, dict) else ""
    )
    snapshot["runner_catalog_hash"] = (
        _stable_payload_hash(runner_payload) if isinstance(runner_payload, dict) else ""
    )
    snapshot["snapshot_hash"] = _stable_payload_hash(
        {k: snapshot[k] for k in snapshot if k != "snapshot_hash"}
    )
    result = dual_write(target, filename, snapshot, family=family)
    return {
        "snapshot_id": snapshot_id,
        "filename": filename,
        "target": target,
        "written_at_utc": snapshot["created_at_utc"],
        **result,
    }


def list_target_snapshots(
    target: str, family: str | None = None
) -> list[dict[str, Any]]:
    directories = [
        target_state_root(target, family=family) / SNAPSHOT_DIR,
        mirror_target_state_root(target, family=family) / SNAPSHOT_DIR,
    ]
    snapshots: list[dict[str, Any]] = []
    files: dict[str, Path] = {}
    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            filename = path.name
            files.setdefault(filename, path)

    for filename in sorted(files):
        rel_filename = f"{SNAPSHOT_DIR}/{filename}"
        try:
            payload = read_dual(target, rel_filename, family=family)
        except FileNotFoundError:
            continue
        if not isinstance(payload, dict):
            continue
        snapshots.append(
            {
                "snapshot_id": str(payload.get("snapshot_id", Path(filename).stem)),
                "filename": rel_filename,
                "created_at_utc": str(payload.get("created_at_utc", "")),
                "target_name": str(payload.get("target_name", "")),
                "lock_hash": str((payload.get("lock") or {}).get("lock_hash", "")),
                "runtime_hash": str(payload.get("runtime_hash", "")),
                "snapshot_hash": str(payload.get("snapshot_hash", "")),
            }
        )
    return snapshots


def show_target_snapshot(
    target: str, snapshot_id: str, family: str | None = None
) -> dict[str, Any]:
    filename = f"{SNAPSHOT_DIR}/{snapshot_id}.json"
    return read_dual(target, filename, family=family)


def discover_repos(
    root: Path | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[RepoCandidate]:
    """Discover available local repositories for bootstrap workflows."""
    return discover_local_git_repos(root=root, include=include, exclude=exclude)


def bootstrap_target(
    target: str,
    mode: TargetMode,
    family: str | None = None,
    source_root: Path | None = None,
    selected_ref: str = "HEAD",
    preferred_runner: str | None = None,
    preferred_command: str | None = None,
    preferred_ref: str | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    repo_ids: list[str] | None = None,
    auto_lock: bool = True,
) -> TargetLock:
    """Create a target and add discovered repositories from a workspace."""
    if mode not in {"repo", "stack"}:
        raise ValueError("mode must be one of: repo, stack")

    repo_root = source_root or phenotype_repos_root()
    candidates = discover_local_git_repos(
        root=repo_root, include=include, exclude=exclude
    )
    if not candidates:
        raise ValueError(f"no repos discovered under: {repo_root}")

    by_id = {item.repo_id: item.path for item in candidates}
    if repo_ids:
        selected = []
        for repo_id in repo_ids:
            path = by_id.get(repo_id)
            if not path:
                raise ValueError(f"repo_id not discovered: {repo_id}")
            selected.append(RepoCandidate(repo_id=repo_id, path=path))
    else:
        selected = candidates

    lock = init_target(target, mode=mode, family=family)
    for item in selected:
        add_repo(
            target,
            family=family,
            repo_path=str(item.path),
            selected_ref=selected_ref,
            repo_id=item.repo_id,
            preferred_runner=preferred_runner,
            preferred_command=preferred_command,
            preferred_ref=preferred_ref,
        )
    if auto_lock:
        lock = lock_target(target, family=family)
    return lock


def set_repo_ref(
    target: str,
    repo_id: str,
    selected_ref: str,
    family: str | None = None,
) -> TargetLock:
    """Update a single repo selection ref in a target and relock the target."""
    lock = load_target_lock(target, family=family)
    updated = False
    for repo in lock.repos:
        if repo.repo_id == repo_id:
            repo.selected_ref = selected_ref
            repo.resolved_sha = None
            updated = True
            break
    if not updated:
        raise ValueError(f"repo_id not in target: {repo_id}")
    lock.created_at_utc = utc_now_iso()
    lock.lock_hash = _lock_hash(lock)
    dual_write(target, LOCK_FILE, lock, family=family)
    return lock_target(target, family=family)


def init_target(target: str, mode: TargetMode, family: str | None = None) -> TargetLock:
    root = target_root(target, family=family)
    root.mkdir(parents=True, exist_ok=True)
    (root / "repos").mkdir(parents=True, exist_ok=True)

    lock = TargetLock(
        schema_version=1,
        target_name=target,
        mode=mode,
        repos=[],
        lock_hash="",
        created_at_utc=utc_now_iso(),
    )
    lock.lock_hash = _lock_hash(lock)
    dual_write(target, LOCK_FILE, lock, family=family)
    return lock


def load_target_lock(target: str, family: str | None = None) -> TargetLock:
    payload = read_dual(target, LOCK_FILE, family=family)
    return _parse_lock(payload)


def add_repo(
    target: str,
    repo_path: str,
    selected_ref: str,
    family: str | None = None,
    repo_id: str | None = None,
    worktree_path: str | None = None,
    preferred_runner: str | None = None,
    preferred_command: str | None = None,
    preferred_ref: str | None = None,
) -> TargetLock:
    lock = load_target_lock(target, family=family)
    repo = Path(repo_path).expanduser().resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        raise ValueError(f"repo is not a git checkout: {repo}")

    rid = repo_id or sanitize_repo_id(repo.name)
    lock.repos = [entry for entry in lock.repos if entry.repo_id != rid]
    lock.repos.append(
        RepoSelection(
            repo_id=rid,
            repo_path=str(repo),
            selected_ref=selected_ref,
            source_worktree_path=worktree_path,
            resolved_sha=None,
            preferred_runner=preferred_runner,
            preferred_command=preferred_command,
            preferred_ref=preferred_ref,
        )
    )
    lock.created_at_utc = utc_now_iso()
    lock.lock_hash = _lock_hash(lock)
    dual_write(target, LOCK_FILE, lock, family=family)
    return lock


def add_module_to_target(
    target: str,
    module_name: str,
    selected_ref: str | None = None,
    exclude_repos: set[str] | None = None,
    family: str | None = None,
) -> TargetLock:
    if not module_name.strip():
        raise ValueError("module name cannot be empty")
    if "/" in module_name or "\\" in module_name or ".." in module_name:
        raise ValueError(f"invalid module name: {module_name}")

    manifest = load_module_manifest(module_name)
    manifest_obj = ModuleManifest(
        schema_version=manifest["schema_version"],
        repo_patterns=manifest.get("repo_patterns", []),
        owners=manifest.get("owners", []),
        refresh_cadence=manifest.get("refresh_cadence", "never"),
        default_ref=manifest.get("default_ref", "HEAD"),
        repo_ids=manifest.get("repo_ids", []),
        repo_ref_overrides=manifest.get("repo_ref_overrides", {}),
        repo_runner_overrides=manifest.get("repo_runner_overrides", {}),
        repo_command_overrides=manifest.get("repo_command_overrides", {}),
        repo_env_profile_overrides=manifest.get("repo_env_profile_overrides", {}),
    )
    lock = load_target_lock(target, family=family)

    candidates = _select_module_repos(manifest_obj, exclude_repos=exclude_repos)
    if not candidates:
        raise ValueError(f"module {module_name} selected no matching repos")

    fallback_ref = selected_ref or manifest_obj.default_ref
    for candidate in candidates:
        repo_id = _repo_id_from_path(candidate)
        _append_repo_selection(
            lock,
            candidate,
            selected_ref=manifest_obj.repo_ref_overrides.get(repo_id, fallback_ref),
            module_name=module_name,
            selected_runner=manifest_obj.repo_runner_overrides.get(repo_id),
            selected_command=manifest_obj.repo_command_overrides.get(repo_id),
            selected_env_profile=manifest_obj.repo_env_profile_overrides.get(repo_id),
        )

    lock.created_at_utc = utc_now_iso()
    lock.lock_hash = _lock_hash(lock)
    dual_write(target, LOCK_FILE, lock, family=family)
    return lock


def lock_target(target: str, family: str | None = None) -> TargetLock:
    lock = load_target_lock(target, family=family)
    if not lock.repos:
        raise ValueError("target has no repos; add at least one repo before lock")

    for repo in lock.repos:
        resolved = resolve_ref_to_sha(Path(repo.repo_path), repo.selected_ref)
        repo.resolved_sha = resolved

    lock.created_at_utc = utc_now_iso()
    lock.lock_hash = _lock_hash(lock)
    dual_write(target, LOCK_FILE, lock, family=family)
    return lock


def materialize_target(target: str, family: str | None = None) -> RuntimeState:
    lock = load_target_lock(target, family=family)
    if not lock.repos:
        raise ValueError("target has no repos")

    runtime_repos: list[RuntimeRepo] = []
    repos_root = target_repos_root(target, family=family)
    repos_root.mkdir(parents=True, exist_ok=True)

    for repo in lock.repos:
        if not repo.resolved_sha:
            raise ValueError(
                f"repo {repo.repo_id} is not locked; run target lock first"
            )
        checkout_path = repos_root / repo.repo_id
        materialize_repo_checkout(
            Path(repo.repo_path), checkout_path, repo.resolved_sha
        )
        runtime_repos.append(
            RuntimeRepo(
                repo_id=repo.repo_id,
                checkout_path=str(checkout_path),
                resolved_sha=repo.resolved_sha,
                head_branch=detect_head_branch(checkout_path),
            )
        )

    runtime = RuntimeState(
        target_name=target,
        materialized_root=str(target_root(target, family=family)),
        repo_materializations=runtime_repos,
        materialized_at_utc=utc_now_iso(),
    )
    dual_write(target, RUNTIME_FILE, runtime, family=family)

    report = run_env_doctor(target, [Path(r.checkout_path) for r in runtime_repos])
    dual_write(target, ENV_FILE, report, family=family)

    return runtime


def target_status(target: str, family: str | None = None) -> dict[str, Any]:
    lock = load_target_lock(target, family=family)
    runtime_payload: dict[str, Any] | None = None
    env_payload: dict[str, Any] | None = None
    try:
        runtime_payload = read_dual(target, RUNTIME_FILE, family=family)
    except FileNotFoundError:
        runtime_payload = None
    try:
        env_payload = read_dual(target, ENV_FILE, family=family)
    except FileNotFoundError:
        env_payload = None

    snapshots = list_target_snapshots(target, family=family)
    latest_snapshot = snapshots[0] if snapshots else None

    if latest_snapshot is not None:
        latest_snapshot = dict(latest_snapshot)
        latest_snapshot = {
            "snapshot_id": latest_snapshot.get("snapshot_id"),
            "filename": latest_snapshot.get("filename"),
            "created_at_utc": latest_snapshot.get("created_at_utc"),
            "lock_hash": latest_snapshot.get("lock_hash"),
            "runtime_hash": latest_snapshot.get("runtime_hash"),
            "snapshot_hash": latest_snapshot.get("snapshot_hash"),
        }

    return {
        "target": target,
        "mode": lock.mode,
        "repos": [asdict(r) for r in lock.repos],
        "lock_hash": lock.lock_hash,
        "created_at_utc": lock.created_at_utc,
        "runtime": runtime_payload,
        "env": env_payload,
        "latest_snapshot": latest_snapshot,
        "snapshot": latest_snapshot,
    }


def target_timeline(
    target: str,
    family: str | None = None,
    repo_id: str | None = None,
    limit: int = 30,
    branch: str | None = None,
) -> dict[str, Any]:
    lock = load_target_lock(target, family=family)
    if not lock.repos:
        raise ValueError("target has no repos")

    if repo_id:
        chosen = next((repo for repo in lock.repos if repo.repo_id == repo_id), None)
        if not chosen:
            raise ValueError(f"repo_id not found in target: {repo_id}")
    else:
        chosen = lock.repos[0]

    timeline = list_timeline(Path(chosen.repo_path), limit=limit, branch=branch)
    return {
        "target": target,
        "repo_id": chosen.repo_id,
        "repo_path": chosen.repo_path,
        "selected_ref": timeline["selected_ref"],
        "resolved_sha": chosen.resolved_sha,
        **timeline,
    }


def list_targets(family: str | None = None) -> list[str]:
    if family is not None:
        root = projects_root() / validate_family_name(family)
        if not root.exists():
            return []
        return sorted(
            entry.name
            for entry in root.iterdir()
            if entry.is_dir() and (entry / ".phench" / LOCK_FILE).exists()
        )

    root = projects_root()
    if not root.exists():
        return []
    targets: list[str] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if (entry / ".phench" / LOCK_FILE).exists():
            targets.append(entry.name)
        else:
            targets.extend(_list_targets_in_root(entry, family_prefix=entry.name))
    unique: list[str] = sorted(set(targets), key=lambda value: ("/" in value, value))
    return unique


def set_env_profile(
    target: str, profile: str, values: dict[str, str], family: str | None = None
) -> dict[str, Any]:
    if not profile.strip():
        raise ValueError("profile name cannot be empty")
    normalized = {str(k): str(v) for k, v in values.items()}
    try:
        state = read_dual(target, PROFILE_FILE, family=family)
    except FileNotFoundError:
        state = {"active_profile": profile, "profiles": {}}
    profiles = state.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile] = normalized
    state = {"active_profile": profile, "profiles": profiles}
    dual_write(target, PROFILE_FILE, state, family=family)
    return state


def get_env_profile(
    target: str, profile: str | None = None, family: str | None = None
) -> dict[str, str]:
    try:
        state = read_dual(target, PROFILE_FILE, family=family)
    except FileNotFoundError:
        return {}
    profiles = state.get("profiles")
    if not isinstance(profiles, dict):
        return {}
    selected = profile or str(state.get("active_profile", ""))
    payload = profiles.get(selected)
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def build_catalog(
    target: str, repo_id: str | None = None, family: str | None = None
) -> RunnerCatalog:
    runtime = read_dual(target, RUNTIME_FILE, family=family)
    materializations = runtime.get("repo_materializations")
    if not isinstance(materializations, list) or not materializations:
        raise ValueError(
            "target has no runtime materialization; run target materialize"
        )

    selected = materializations[0]
    if repo_id:
        selected = next(
            (item for item in materializations if item.get("repo_id") == repo_id), None
        )
        if not selected:
            raise ValueError(f"repo_id not materialized: {repo_id}")
    checkout = Path(str(selected.get("checkout_path", ""))).resolve()
    catalog = build_runner_catalog(target, checkout)
    dual_write(target, RUNNER_FILE, catalog, family=family)
    return catalog


def run_env_doctor_for_target(target: str, family: str | None = None) -> dict[str, Any]:
    from dataclasses import asdict as _asdict

    runtime = read_dual(target, RUNTIME_FILE, family=family)
    materializations = runtime.get("repo_materializations")
    if not isinstance(materializations, list) or not materializations:
        raise ValueError(
            "target has no runtime materialization; run target materialize"
        )
    checkouts = [
        Path(str(item.get("checkout_path", ""))).resolve() for item in materializations
    ]
    report = run_env_doctor(target, checkouts)
    dual_write(target, ENV_FILE, report, family=family)
    return _asdict(report)


def sync_target(
    target: str, prefer: str | None = None, family: str | None = None
) -> dict[str, Any]:
    results = {}
    for filename in (LOCK_FILE, RUNTIME_FILE, ENV_FILE, RUNNER_FILE, PROFILE_FILE):
        try:
            results[filename] = sync_dual(
                target, filename, prefer=prefer, family=family
            )
        except FileNotFoundError:
            continue
    if not results:
        raise FileNotFoundError("No state files to sync")
    return results
