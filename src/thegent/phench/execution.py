from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import (
    ENV_FILE,
    RUNTIME_FILE,
)
from .env_doctor import run_env_doctor
from .helpers import (
    _parse_lock,
    _stable_payload_hash,
)
from .models import RepoSelection, RunnerCatalog
from .runner import build_runner_catalog
from .store import dual_write, read_dual


def _normalize_repo_map(values: dict[str, str] | None, *, label: str) -> dict[str, str]:
    if values is None:
        return {}
    normalized: dict[str, str] = {}
    for repo_id, value in values.items():
        if not isinstance(repo_id, str):
            raise ValueError(f"{label} keys must be strings")
        normalized_key = repo_id.strip()
        if not normalized_key:
            raise ValueError(f"{label} contains empty key")
        if not isinstance(value, str):
            raise ValueError(f"{label} values must be strings")
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(
                f"{label} value for repo '{normalized_key}' cannot be empty"
            )
        normalized[normalized_key] = normalized_value
    return normalized


def _materialization_entry(item: dict[str, Any]) -> tuple[str, Path]:
    repo_id = item.get("repo_id")
    checkout_path = item.get("checkout_path")
    if not isinstance(repo_id, str) or not repo_id.strip():
        raise ValueError("invalid runtime materialization entry: missing repo_id")
    if not isinstance(checkout_path, str) or not checkout_path.strip():
        raise ValueError(
            f"invalid runtime materialization entry for {repo_id}: missing checkout_path"
        )
    return repo_id, Path(checkout_path).resolve()


def _materialization_checkouts(
    materializations: list[dict[str, Any]],
) -> list[Path]:
    return [
        checkout
        for _, checkout in (_materialization_entry(item) for item in materializations)
    ]


def _run_env_doctor_for_materializations(
    target: str,
    materializations: list[dict[str, Any]],
    family: str | None = None,
) -> dict[str, Any]:

    report = run_env_doctor(target, _materialization_checkouts(materializations))
    dual_write(target, ENV_FILE, report, family=family)
    return asdict(report)


def _materialization_lookup(
    repo_id: str | None,
    repo_ids: list[str] | None,
    all_repos: bool,
    materializations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not materializations:
        raise ValueError(
            "target has no runtime materialization; run target materialize"
        )

    if all_repos:
        return [dict(item) for item in materializations]

    if repo_id is not None:
        selected = next(
            (item for item in materializations if item.get("repo_id") == repo_id), None
        )
        if selected is None:
            raise ValueError(f"repo_id not materialized: {repo_id}")
        return [dict(selected)]

    if repo_ids is not None:
        index = {
            repo_id: item
            for item in materializations
            for repo_id in [item.get("repo_id")]
            if isinstance(repo_id, str)
        }
        if not index:
            raise ValueError(
                "target has no runtime materialization; run target materialize"
            )
        requested: list[str] = []
        seen: set[str] = set()
        for requested_repo_id in repo_ids:
            if requested_repo_id in seen:
                continue
            seen.add(requested_repo_id)
            if requested_repo_id not in index:
                raise ValueError(f"repo_id not materialized: {requested_repo_id}")
            requested.append(requested_repo_id)
        return [dict(index[rid]) for rid in requested]

    return [dict(item) for item in materializations[:1]]


def _run_single_repo_target(
    checkout_path: Path,
    catalog: RunnerCatalog,
    runner: str | None,
    command_name: str | None,
    non_interactive: bool = False,
    env_overrides: dict[str, str] | None = None,
) -> int:
    from .runner import pick_command_interactive, run_command

    if command_name and not runner:
        raise ValueError("--command requires --runner")
    if runner and command_name:
        return run_command(
            checkout_path, runner, command_name, env_overrides=env_overrides
        )

    if runner and not command_name:
        options = [command for command in catalog.commands if command.runner == runner]
        if not options:
            raise ValueError(f"runner has no discovered commands: {runner}")
        return run_command(
            checkout_path, runner, options[0].name, env_overrides=env_overrides
        )

    if non_interactive:
        raise ValueError(
            "runner policy is required for non-interactive execution; pass --runner or configure preferred_runner"
        )

    selected = pick_command_interactive(catalog)
    return run_command(
        checkout_path, selected.runner, selected.name, env_overrides=env_overrides
    )


def _resolve_repo_runner_and_command(
    repo_id: str,
    repo: RepoSelection,
    catalog: RunnerCatalog,
    cli_runner: str | None,
    cli_command: str | None,
    repo_runner_override: str | None = None,
    repo_command_override: str | None = None,
    enforce_no_interactive: bool = False,
) -> tuple[str | None, str | None]:
    runner = repo_runner_override or cli_runner or repo.preferred_runner
    command_name = repo_command_override or cli_command or repo.preferred_command

    if command_name and not runner:
        raise ValueError(
            f"repo '{repo_id}' requires a runner for command '{command_name}'"
        )

    if not runner:
        if enforce_no_interactive:
            raise ValueError(
                f"repo '{repo_id}' requires runner policy (--runner or preferred_runner) "
                "for non-interactive/all-repos execution."
            )
        return None, command_name

    if command_name:
        return runner, command_name

    available = [command for command in catalog.commands if command.runner == runner]
    if not available:
        raise ValueError(
            f"runner '{runner}' has no discovered commands in repo '{repo_id}'"
        )
    if enforce_no_interactive and len(available) > 1:
        raise ValueError(
            f"repo '{repo_id}' with runner '{runner}' requires explicit command "
            "for non-interactive/all-repos execution."
        )
    return runner, available[0].name


__all__ = [
    "build_project_execution_matrix",
    "run_target",
]


def build_project_execution_matrix(
    target: str,
    family: str | None = None,
    snapshot_id: str | None = None,
    repo_id: str | None = None,
    repo_ids: list[str] | None = None,
    repo_ref_overrides: dict[str, str] | None = None,
    repo_runner_overrides: dict[str, str] | None = None,
    repo_command_overrides: dict[str, str] | None = None,
    repo_env_profile_overrides: dict[str, str] | None = None,
    runner: str | None = None,
    command_name: str | None = None,
    selected_ref: str | None = None,
    all_repos: bool = False,
    env_profile: str | None = None,
    non_interactive: bool = False,
    validate_commands: bool = False,
    sort_repos: bool = False,
) -> dict[str, Any]:
    from .git_ops import materialize_repo_checkout, resolve_ref_to_sha
    from .target import (
        get_env_profile,
        load_target_lock,
        run_env_doctor_for_target,
        show_target_snapshot,
    )

    lock_hash = None
    snapshot_hash = None
    runtime_hash = None

    if snapshot_id is not None:
        snapshot = show_target_snapshot(target, snapshot_id, family=family)
        runtime = snapshot.get("runtime")
        if not isinstance(runtime, dict):
            raise ValueError(f"snapshot '{snapshot_id}' has no runtime payload")
        materializations = runtime.get("repo_materializations")
        if not isinstance(materializations, list) or not materializations:
            raise ValueError(
                f"snapshot '{snapshot_id}' has no runtime materialization; create snapshot after materialize"
            )
        snapshot_lock = snapshot.get("lock")
        if not isinstance(snapshot_lock, dict):
            raise ValueError(f"snapshot '{snapshot_id}' has invalid lock payload")
        lock = _parse_lock(snapshot_lock)
        report = _run_env_doctor_for_materializations(
            target, materializations, family=family
        )
        lock_hash = str((snapshot_lock or {}).get("lock_hash", ""))
        snapshot_hash = str(snapshot.get("snapshot_hash", ""))
        runtime_hash = str(snapshot.get("runtime_hash", ""))
        if not runtime_hash:
            runtime_hash = _stable_payload_hash(runtime)
    else:
        report = run_env_doctor_for_target(target, family=family)
        runtime = read_dual(target, RUNTIME_FILE, family=family)
        materializations = runtime.get("repo_materializations")
        lock = load_target_lock(target, family=family)
        lock_hash = lock.lock_hash

    if report["doctor_status"] != "pass":
        missing = ", ".join(report["missing_requirements"])
        raise RuntimeError(f"env doctor failed, missing requirements: {missing}")

    if repo_id is not None and repo_ids is not None:
        raise ValueError("repo_id and repo_ids are mutually exclusive")
    if repo_ids is not None:
        repo_ids = [repo for repo in repo_ids if repo]
        if not repo_ids:
            raise ValueError("repo_ids cannot be empty")

    if repo_ref_overrides is None:
        repo_ref_overrides_normalized = {}
    else:
        repo_ref_overrides_normalized = _normalize_repo_map(
            repo_ref_overrides, label="repo_ref_overrides"
        )

    repo_runner_overrides_normalized = _normalize_repo_map(
        repo_runner_overrides,
        label="repo_runner_overrides",
    )
    repo_command_overrides_normalized = _normalize_repo_map(
        repo_command_overrides,
        label="repo_command_overrides",
    )
    repo_env_profile_overrides_normalized = _normalize_repo_map(
        repo_env_profile_overrides,
        label="repo_env_profile_overrides",
    )

    if all_repos and repo_ids is not None:
        raise ValueError("repo_ids is not compatible with --all-repos")

    if repo_id is not None and not repo_id.strip():
        raise ValueError("repo_id cannot be empty")

    if repo_ids is not None:
        repo_index = {item.strip(): item.strip() for item in repo_ids}
        repo_ids = list(repo_index.values())
        unknown_override = [
            item for item in repo_ref_overrides_normalized if item not in repo_index
        ]
        if unknown_override:
            raise ValueError(f"repo_id not materialized: {unknown_override[0]}")
        unknown_runner_override = [
            item for item in repo_runner_overrides_normalized if item not in repo_index
        ]
        if unknown_runner_override:
            raise ValueError(f"repo_id not materialized: {unknown_runner_override[0]}")
        unknown_command_override = [
            item for item in repo_command_overrides_normalized if item not in repo_index
        ]
        if unknown_command_override:
            raise ValueError(f"repo_id not materialized: {unknown_command_override[0]}")
        unknown_env_profile_override = [
            item
            for item in repo_env_profile_overrides_normalized
            if item not in repo_index
        ]
        if unknown_env_profile_override:
            raise ValueError(
                f"repo_id not materialized: {unknown_env_profile_override[0]}"
            )

    if not isinstance(materializations, list) or not materializations:
        raise ValueError(
            "target has no runtime materialization; run target materialize"
        )

    if all_repos:
        selected_items = [dict(item) for item in materializations]
    else:
        selected_items = _materialization_lookup(
            repo_id,
            repo_ids=repo_ids,
            all_repos=False,
            materializations=materializations,
        )

    if repo_id is not None:
        repo_ids = [repo_id]

    lock_index = {entry.repo_id: entry for entry in lock.repos}
    enforce_no_interactive = non_interactive or all_repos

    plans: list[dict[str, Any]] = []
    for item in selected_items:
        item_repo_id, item_checkout = _materialization_entry(item)
        lock_repo = lock_index.get(item_repo_id)
        if lock_repo is None:
            raise ValueError(f"repo_id not in target lock: {item_repo_id}")

        if (repo_ref := repo_ref_overrides_normalized.get(item_repo_id)) is not None:
            ref_source = "repo_override"
        elif selected_ref is not None:
            repo_ref = selected_ref
            ref_source = "cli_ref"
        elif lock_repo.preferred_ref is not None:
            repo_ref = lock_repo.preferred_ref
            ref_source = "preferred_ref"
        elif lock_repo.selected_ref is not None:
            repo_ref = lock_repo.selected_ref
            ref_source = "selected_ref"
        else:
            repo_ref = None
            ref_source = "materialized_ref"

        if repo_ref is not None:
            resolved = resolve_ref_to_sha(Path(lock_repo.repo_path), repo_ref)
            materialize_repo_checkout(
                Path(lock_repo.repo_path), item_checkout, resolved
            )
            item["resolved_sha"] = resolved
        else:
            resolved = item.get("resolved_sha")

        repo_runner_override = repo_runner_overrides_normalized.get(item_repo_id)
        repo_command_override = repo_command_overrides_normalized.get(item_repo_id)
        repo_env_profile = repo_env_profile_overrides_normalized.get(
            item_repo_id, env_profile
        )
        env_overrides = get_env_profile(target, profile=repo_env_profile, family=family)

        if validate_commands:
            catalog = build_runner_catalog(target, item_checkout)
            repo_runner, repo_command = _resolve_repo_runner_and_command(
                item_repo_id,
                lock_repo,
                catalog,
                cli_runner=runner,
                cli_command=command_name,
                repo_runner_override=repo_runner_override,
                repo_command_override=repo_command_override,
                enforce_no_interactive=enforce_no_interactive,
            )
        else:
            repo_runner = repo_runner_override or runner or lock_repo.preferred_runner
            repo_command = (
                repo_command_override or command_name or lock_repo.preferred_command
            )
            if repo_command and not repo_runner:
                raise ValueError(
                    f"repo '{item_repo_id}' requires a runner for command '{repo_command}'"
                )

        plans.append(
            {
                "repo_id": item_repo_id,
                "repo_path": lock_repo.repo_path,
                "checkout_path": item["checkout_path"],
                "lock_selected_ref": lock_repo.selected_ref,
                "lock_preferred_ref": lock_repo.preferred_ref,
                "effective_ref": repo_ref,
                "effective_ref_source": ref_source,
                "resolved_sha": resolved,
                "effective_runner": repo_runner,
                "effective_command": repo_command,
                "effective_env_profile": repo_env_profile,
                "env_overrides": env_overrides,
                "preferred_runner": lock_repo.preferred_runner,
                "preferred_command": lock_repo.preferred_command,
            }
        )

    if sort_repos:
        plans.sort(key=lambda item: str(item["repo_id"]))

    return {
        "target": target,
        "family": family,
        "lock_hash": lock_hash,
        "snapshot_hash": snapshot_hash,
        "runtime_hash": runtime_hash,
        "snapshot_id": snapshot_id,
        "all_repos": all_repos,
        "non_interactive": non_interactive,
        "repo_count": len(plans),
        "repos": plans,
    }


def run_target(
    target: str,
    family: str | None = None,
    snapshot_id: str | None = None,
    repo_id: str | None = None,
    repo_ids: list[str] | None = None,
    repo_ref_overrides: dict[str, str] | None = None,
    repo_runner_overrides: dict[str, str] | None = None,
    repo_command_overrides: dict[str, str] | None = None,
    repo_env_profile_overrides: dict[str, str] | None = None,
    runner: str | None = None,
    command_name: str | None = None,
    selected_ref: str | None = None,
    all_repos: bool = False,
    execution_mode: str = "serial",
    env_profile: str | None = None,
    non_interactive: bool = False,
) -> int:
    matrix = build_project_execution_matrix(
        target=target,
        family=family,
        snapshot_id=snapshot_id,
        repo_id=repo_id,
        repo_ids=repo_ids,
        repo_ref_overrides=repo_ref_overrides,
        repo_runner_overrides=repo_runner_overrides,
        repo_command_overrides=repo_command_overrides,
        repo_env_profile_overrides=repo_env_profile_overrides,
        runner=runner,
        command_name=command_name,
        selected_ref=selected_ref,
        all_repos=all_repos,
        env_profile=env_profile,
        non_interactive=non_interactive,
        validate_commands=True,
        sort_repos=False,
    )

    if execution_mode not in {"serial", "parallel"}:
        raise ValueError("execution_mode must be one of: serial, parallel")

    if command_name is not None and command_name.startswith("-"):
        raise ValueError("command names cannot start with '-'")

    runs: list[
        tuple[Path, RunnerCatalog, str | None, str | None, dict[str, str] | None]
    ] = []
    for item in matrix["repos"]:
        checkout_path = Path(item["checkout_path"])
        catalog = build_runner_catalog(target, checkout_path)
        runs.append(
            (
                checkout_path,
                catalog,
                item["effective_runner"],
                item["effective_command"],
                item.get("env_overrides"),
            )
        )

    if execution_mode == "parallel" and len(runs) > 1:
        with ThreadPoolExecutor(max_workers=len(runs)) as pool:
            futures = [
                pool.submit(
                    _run_single_repo_target,
                    checkout_path,
                    effective_catalog,
                    effective_runner,
                    effective_command,
                    non_interactive,
                    env_overrides,
                )
                for checkout_path, effective_catalog, effective_runner, effective_command, env_overrides in runs
            ]
            results = [future.result() for future in futures]
        nonzero = [code for code in results if code != 0]
        return nonzero[0] if nonzero else 0

    for (
        checkout,
        effective_catalog,
        effective_runner,
        effective_command,
        env_overrides,
    ) in runs:
        code = _run_single_repo_target(
            checkout,
            effective_catalog,
            effective_runner,
            effective_command,
            non_interactive,
            env_overrides,
        )
        if code != 0:
            return code
    return 0
