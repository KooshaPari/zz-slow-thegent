"""Unit tests for the modular CLI app entrypoints."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import orjson as json
from typer.testing import CliRunner

from thegent.cli.apps.main import app

runner = CliRunner()


def test_top_level_ps_shortcut_routes_to_run_ps() -> None:
    """`thegent ps` should route through the run stream implementation."""
    with patch("thegent.cli.apps.run.run_ps") as mock_run_ps:
        result = runner.invoke(
            app,
            ["ps", "--all", "--owner", "alice", "--format", "json", "--include-contract"],
        )

    assert result.exit_code == 0
    mock_run_ps.assert_called_once_with(
        all_sessions=True,
        owner="alice",
        format="json",
        include_contract=True,
    )


def test_top_level_do_shortcut_routes_to_run_agent() -> None:
    """`thegent do` should route through the run stream implementation."""
    with patch("thegent.cli.apps.run.run_agent") as mock_run_agent:
        result = runner.invoke(app, ["do", "hello"])

    assert result.exit_code == 0
    mock_run_agent.assert_called_once_with(prompt="hello")


def test_top_level_phench_target_init_routes_to_service(tmp_path: Path, monkeypatch) -> None:
    """`thegent phench target init` should dispatch through the phench app entrypoint."""
    phenotype_root = tmp_path / "Phenotype"
    mirror_root = tmp_path / "home-phench"
    monkeypatch.setenv("THGENT_PHENOTYPE_ROOT", str(phenotype_root))
    monkeypatch.setenv("THGENT_PHENCH_HOME_ROOT", str(mirror_root))

    with patch("thegent.cli.apps.phench.init_target") as mock_init_target:
        mock_init_target.return_value = SimpleNamespace(target_name="alpha", mode="repo", lock_hash="abc123")
        result = runner.invoke(app, ["phench", "target", "init", "alpha", "--family", "acme"])

    assert result.exit_code == 0
    mock_init_target.assert_called_once_with("alpha", mode="repo", family="acme")


def test_phench_target_bootstrap_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.bootstrap_target") as mock_bootstrap_target:
        mock_bootstrap_target.return_value = SimpleNamespace(
            target_name="alpha",
            mode="stack",
            repos=[],
            lock_hash="abc123",
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "target",
                "bootstrap",
                "alpha",
                "--mode",
                "stack",
                "--source-root",
                "/tmp/repos",
                "--ref",
                "main",
            ],
        )

    assert result.exit_code == 0
    mock_bootstrap_target.assert_called_once_with(
        target="alpha",
        mode="stack",
        source_root=Path("/tmp/repos"),
        selected_ref="main",
        preferred_runner=None,
        preferred_command=None,
        preferred_ref=None,
        include=None,
        exclude=None,
        repo_ids=None,
        auto_lock=True,
        family=None,
    )


def test_phench_modules_audit_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.audit_shared_modules_across_repos") as mock_audit:
        mock_audit.return_value = {
            "source_root": "/tmp/repos",
            "repo_count": 1,
            "module_count": 1,
            "shared_modules": {},
            "shared_module_count": 0,
            "moduleization_candidates": [],
            "module_repo_map": {},
            "excluded_repos": ["tmp"],
            "excluded_modules": [],
            "include_repo_modules_root": True,
        }
        result = runner.invoke(
            app,
            [
                "phench",
                "modules",
                "audit",
                "--source-root",
                "/tmp/repos",
                "--include-repo",
                "repo-a",
                "--exclude-repo",
                "repo-b",
                "--skip-repo",
                "repo-skip",
                "--min-repo-count",
                "3",
                "--include-module",
                "thegent-app",
                "--exclude-module",
                "legacy",
                "--no-include-repo-modules-root",
            ],
        )

    assert result.exit_code == 0
    mock_audit.assert_called_once_with(
        source_root=Path("/tmp/repos"),
        include_repos=["repo-a"],
        exclude_repos=["repo-b"],
        min_repo_count=3,
        include_modules=["thegent-app"],
        exclude_modules=["legacy"],
        include_repo_modules_root=False,
        skip_repos=["repo-skip"],
    )


def test_phench_modules_sync_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.sync_project_modules_from_repos") as mock_sync:
        mock_sync.return_value = {
            "created": ["thegent-app"],
            "updated": [],
            "skipped": [],
            "discovered_modules": ["thegent-app"],
            "source_root": "/tmp/repos",
            "destination_root": "/tmp/dest",
            "dry_run": True,
            "overwrite": False,
        }
        result = runner.invoke(
            app,
            [
                "phench",
                "modules",
                "sync",
                "--source-root",
                "/tmp/repos",
                "--destination-root",
                "/tmp/dest",
                "--include-repo",
                "repo-a",
                "--exclude-repo",
                "repo-b",
                "--include-module",
                "thegent-app",
                "--exclude-module",
                "legacy",
                "--overwrite",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0
    mock_sync.assert_called_once_with(
        source_root=Path("/tmp/repos"),
        destination_root=Path("/tmp/dest"),
        include_repos=["repo-a"],
        exclude_repos=["repo-b"],
        include_modules=["thegent-app"],
        exclude_modules=["legacy"],
        overwrite=True,
        dry_run=True,
    )


def test_phench_target_import_repos_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.import_repos") as mock_import_repos:
        mock_import_repos.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[SimpleNamespace(repo_id="repo", selected_ref="HEAD", resolved_sha=None)],
            lock_hash="abc123",
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "target",
                "import-repos",
                "alpha",
                "--source-root",
                "/tmp/repos",
                "--ref",
                "main",
                "--include",
                "*-repo",
                "--exclude",
                "tmp*",
                "--repo-id",
                "repo-a",
                "--repo-id",
                "repo-b",
            ],
        )

    assert result.exit_code == 0
    mock_import_repos.assert_called_once_with(
        target="alpha",
        source_root=Path("/tmp/repos"),
        selected_ref="main",
        preferred_runner=None,
        preferred_command=None,
        preferred_ref=None,
        include=["*-repo"],
        exclude=["tmp*"],
        repo_ids=["repo-a", "repo-b"],
        auto_lock=True,
        family=None,
    )


def test_phench_target_set_ref_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.set_repo_ref") as mock_set_repo_ref:
        mock_set_repo_ref.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[SimpleNamespace(repo_id="repo", selected_ref="main", resolved_sha="abc")],
            lock_hash="abc123",
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "target",
                "set-ref",
                "alpha",
                "--repo-id",
                "repo",
                "--ref",
                "main",
            ],
        )

    assert result.exit_code == 0
    mock_set_repo_ref.assert_called_once_with("alpha", repo_id="repo", selected_ref="main", family=None)


def test_phench_target_add_repo_routes_policy_fields_to_service() -> None:
    with patch("thegent.cli.apps.phench.add_repo") as mock_add_repo:
        mock_add_repo.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[
                SimpleNamespace(
                    repo_id="repo",
                    selected_ref="main",
                    preferred_runner="task",
                    preferred_command="hello",
                    preferred_ref="feature",
                    resolved_sha="deadbeef",
                )
            ],
            lock_hash="abc123",
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "target",
                "add-repo",
                "alpha",
                "--repo",
                "/tmp/repo",
                "--ref",
                "main",
                "--preferred-ref",
                "feature",
                "--preferred-runner",
                "task",
                "--preferred-command",
                "hello",
                "--repo-id",
                "repo",
                "--worktree",
                "/tmp/worktree",
            ],
        )

    assert result.exit_code == 0
    mock_add_repo.assert_called_once_with(
        "alpha",
        repo_path="/tmp/repo",
        selected_ref="main",
        repo_id="repo",
        worktree_path="/tmp/worktree",
        preferred_runner="task",
        preferred_command="hello",
        preferred_ref="feature",
        family=None,
    )


def test_phench_repos_discover_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.discover_repos") as mock_discover_repos:
        mock_discover_repos.return_value = []
        result = runner.invoke(
            app,
            [
                "phench",
                "repos",
                "discover",
                "--repo-root",
                "/tmp/repos",
            ],
        )

    assert result.exit_code == 0
    mock_discover_repos.assert_called_once_with(
        root=Path("/tmp/repos"),
        include=None,
        exclude=None,
    )


def test_phench_timeline_branch_filter_dispatches_to_service() -> None:
    with patch("thegent.cli.apps.phench.target_timeline") as mock_timeline:
        mock_timeline.return_value = {"selected_ref": "main"}
        result = runner.invoke(
            app,
            [
                "phench",
                "timeline",
                "alpha",
                "--branch",
                "feature",
                "--limit",
                "5",
            ],
        )

    assert result.exit_code == 0
    mock_timeline.assert_called_once_with(
        "alpha",
        repo_id=None,
        limit=5,
        branch="feature",
        family=None,
    )


def test_phench_run_dispatches_ref_and_mode_to_service() -> None:
    with patch("thegent.cli.apps.phench.run_target") as mock_run_target:
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "run",
                "alpha",
                "--repo-id",
                "repo-a",
                "--runner",
                "task",
                "--command",
                "hello",
                "--ref",
                "feature-x",
                "--mode",
                "parallel",
                "--all-repos",
                "--env-profile",
                "ci",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id="repo-a",
        runner="task",
        command_name="hello",
        selected_ref="feature-x",
        all_repos=True,
        execution_mode="parallel",
        env_profile="ci",
        non_interactive=True,
        family=None,
    )


def test_phench_run_dispatches_branch_alias_and_no_interactive() -> None:
    with patch("thegent.cli.apps.phench.run_target") as mock_run_target:
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "run",
                "alpha",
                "--runner",
                "task",
                "--command",
                "hello",
                "--branch",
                "feature-branch",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id=None,
        runner="task",
        command_name="hello",
        selected_ref="feature-branch",
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_run_ref_and_branch_conflict_is_rejected() -> None:
    result = runner.invoke(
        app,
        [
            "phench",
            "run",
            "alpha",
            "--ref",
            "main",
            "--branch",
            "feature",
        ],
    )

    assert result.exit_code != 0
    assert "--ref and --branch are mutually exclusive" in (result.stdout + result.stderr)


def test_phench_run_dispatches_snapshot_id_to_service() -> None:
    with patch("thegent.cli.apps.phench.run_target") as mock_run_target:
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "run",
                "alpha",
                "--snapshot-id",
                "snapshot-001",
            ],
        )

    assert result.exit_code == 0
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id="snapshot-001",
        repo_id=None,
        runner=None,
        command_name=None,
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=False,
        family=None,
    )


def test_phench_projects_run_non_interactive_dispatches_prepare_and_run() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
    )
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.lock_target") as mock_lock_target,
        patch("thegent.cli.apps.phench.materialize_target") as mock_materialize_target,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--all-repos",
                "--runner",
                "task",
                "--command",
                "hello",
                "--ref",
                "feature-x",
                "--mode",
                "parallel",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_load_target_lock.assert_called_once_with("alpha", family=None)
    mock_lock_target.assert_called_once_with("alpha", family=None)
    mock_materialize_target.assert_called_once_with("alpha", family=None)
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id=None,
        runner="task",
        command_name="hello",
        selected_ref="feature-x",
        all_repos=True,
        execution_mode="parallel",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_projects_run_dispatches_snapshot_to_service_without_prepare() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
    )
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.lock_target") as mock_lock_target,
        patch("thegent.cli.apps.phench.materialize_target") as mock_materialize_target,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--snapshot-id",
                "snapshot-001",
                "--runner",
                "task",
                "--command",
                "hello",
            ],
        )

    assert result.exit_code == 0
    mock_load_target_lock.assert_called_once_with("alpha", family=None)
    mock_lock_target.assert_not_called()
    mock_materialize_target.assert_not_called()
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id="snapshot-001",
        repo_id="repo-a",
        runner="task",
        command_name="hello",
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=False,
        family=None,
    )


def test_phench_projects_matrix_dispatches_resolved_kwargs_and_prints_payload() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.build_project_execution_matrix") as mock_build_matrix,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
        )
        matrix_payload = {
            "target": "alpha",
            "family": None,
            "snapshot_id": None,
            "all_repos": True,
            "repo_count": 1,
            "repos": [
                {
                    "repo_id": "repo-a",
                    "repo_path": "/tmp/repo-a",
                    "checkout_path": "/tmp/repo-a",
                    "effective_runner": "task",
                    "effective_command": "hello",
                    "effective_env_profile": None,
                }
            ],
        }
        mock_build_matrix.return_value = matrix_payload
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "matrix",
                "--target",
                "alpha",
                "--all-repos",
                "--runner",
                "task",
                "--command",
                "hello",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == matrix_payload
    mock_build_matrix.assert_called_once()
    call_kwargs = mock_build_matrix.call_args.kwargs
    assert call_kwargs["runner"] == "task"
    assert call_kwargs["command_name"] == "hello"
    assert call_kwargs["all_repos"] is True
    assert call_kwargs["selected_ref"] is None
    assert call_kwargs["non_interactive"] is True
    assert call_kwargs["sort_repos"] is True


def test_phench_projects_matrix_module_merges_overrides_and_respects_non_interactive() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
        patch("thegent.cli.apps.phench.build_project_execution_matrix") as mock_build_matrix,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[
                SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
                SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
            ],
        )
        mock_load_module_manifest.return_value = {
            "repo_ids": ["repo-a"],
            "repo_ref_overrides": {"repo-a": "release"},
            "repo_runner_overrides": {},
            "repo_command_overrides": {},
            "repo_env_profile_overrides": {},
        }
        mock_build_matrix.return_value = {"target": "alpha", "repos": []}
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "matrix",
                "--target",
                "alpha",
                "--module",
                "thegent-app",
                "--repo-ref",
                "repo-a@staging",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_load_module_manifest.assert_called_once_with(
        "thegent-app",
        available_repo_ids=["repo-a", "repo-b"],
    )
    call_kwargs = mock_build_matrix.call_args.kwargs
    assert call_kwargs["repo_ids"] == ["repo-a"]
    assert call_kwargs["repo_ref_overrides"] == {"repo-a": "staging"}
    assert call_kwargs["non_interactive"] is True


def test_phench_projects_matrix_include_and_exclude_repo_filters_module_scope() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
        patch("thegent.cli.apps.phench.build_project_execution_matrix") as mock_build_matrix,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[
                SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
                SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
                SimpleNamespace(repo_id="repo-c", selected_ref="main", resolved_sha="deadbabe"),
            ],
        )
        mock_load_module_manifest.return_value = {
            "repo_ids": ["repo-a", "repo-c"],
            "repo_ref_overrides": {},
            "repo_runner_overrides": {},
            "repo_command_overrides": {},
            "repo_env_profile_overrides": {},
        }
        mock_build_matrix.return_value = {"target": "alpha", "repos": []}
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "matrix",
                "--target",
                "alpha",
                "--module",
                "thegent-app",
                "--include-repo",
                "repo-*",
                "--exclude-repo",
                "repo-c",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    call_kwargs = mock_build_matrix.call_args.kwargs
    assert call_kwargs["repo_ids"] == ["repo-a"]


def test_phench_projects_matrix_excluded_repo_ref_is_rejected() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.build_project_execution_matrix") as mock_build_matrix,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[
                SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
                SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
            ],
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "matrix",
                "--target",
                "alpha",
                "--repo-ref",
                "repo-b@release",
                "--exclude-repo",
                "repo-b",
            ],
        )

    assert result.exit_code != 0
    assert "repo-ref repo-id not in target lock: repo-b" in (result.stdout + result.stderr)
    mock_build_matrix.assert_not_called()


def test_phench_projects_matrix_non_interactive_requires_target() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.build_project_execution_matrix") as mock_build_matrix,
    ):
        mock_list_targets.return_value = ["alpha"]
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "matrix",
                "--all-repos",
                "--no-interactive",
                "--runner",
                "task",
                "--command",
                "hello",
            ],
        )

    assert result.exit_code != 0
    mock_build_matrix.assert_not_called()
    assert "--target is required when --no-interactive is set" in (result.stdout + result.stderr)


def test_phench_projects_modules_lists_manifest_names(tmp_path: Path) -> None:
    phenotype_root = tmp_path / "Phenotype"
    modules_root = phenotype_root / "projects" / "modules"
    (modules_root / "thegent-app").mkdir(parents=True, exist_ok=True)
    (modules_root / "platform-core").mkdir(parents=True, exist_ok=True)
    (modules_root / "legacy").mkdir(parents=True, exist_ok=True)
    (modules_root / "legacy" / "manifest.json").write_text("{}", encoding="utf-8")
    (modules_root / "thegent-app" / "manifest.json").write_text("{}", encoding="utf-8")
    (modules_root / "platform-core" / "manifest.json").write_text("{}", encoding="utf-8")

    env = {"THGENT_PHENOTYPE_ROOT": str(phenotype_root)}
    result = runner.invoke(app, ["phench", "projects", "modules"], env=env)

    assert result.exit_code == 0
    assert json.loads(result.stdout) == ["legacy", "platform-core", "thegent-app"]


def test_phench_projects_modules_loads_manifest() -> None:
    with patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest:
        mock_load_module_manifest.return_value = {
            "repo_ids": ["repo-a", "repo-b"],
            "owners": ["owner-a", "owner-b"],
            "refresh_cadence": "weekly",
            "repo_ref_overrides": {},
            "repo_runner_overrides": {},
            "repo_command_overrides": {},
            "repo_env_profile_overrides": {},
        }
        result = runner.invoke(
            app,
            ["phench", "projects", "modules", "--module", "thegent-app"],
        )

    assert result.exit_code == 0
    mock_load_module_manifest.assert_called_once_with(
        "thegent-app",
        available_repo_ids=None,
    )
    assert json.loads(result.stdout) == {
        "repo_ids": ["repo-a", "repo-b"],
        "owners": ["owner-a", "owner-b"],
        "refresh_cadence": "weekly",
        "repo_ref_overrides": {},
        "repo_runner_overrides": {},
        "repo_command_overrides": {},
        "repo_env_profile_overrides": {},
        "module": "thegent-app",
    }


def test_phench_projects_modules_loads_manifest_with_target_filter() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            repos=[
                SimpleNamespace(repo_id="repo-a"),
                SimpleNamespace(repo_id="repo-b"),
                SimpleNamespace(repo_id="repo-c"),
            ],
        )
        mock_load_module_manifest.return_value = {
            "repo_ids": ["repo-a", "repo-c"],
            "repo_ref_overrides": {"repo-a": "main"},
            "repo_runner_overrides": {},
            "repo_command_overrides": {},
            "repo_env_profile_overrides": {},
        }
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "modules",
                "--module",
                "thegent-app",
                "--target",
                "alpha",
            ],
        )

    assert result.exit_code == 0
    mock_load_module_manifest.assert_called_once_with(
        "thegent-app",
        available_repo_ids=["repo-a", "repo-b", "repo-c"],
    )
    assert json.loads(result.stdout)["module"] == "thegent-app"
    assert json.loads(result.stdout)["target"] == "alpha"


def test_phench_projects_run_repo_ref_map_dispatches_per_repo_state() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[
            SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
            SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
        ],
    )
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.lock_target") as mock_lock_target,
        patch("thegent.cli.apps.phench.materialize_target") as mock_materialize_target,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--repo-ref",
                "repo-a@feature-x",
                "--repo-ref",
                "repo-b@release-y",
                "--runner",
                "task",
                "--command",
                "hello",
                "--env-profile",
                "ci",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_load_target_lock.assert_called_once_with("alpha", family=None)
    mock_lock_target.assert_called_once_with("alpha", family=None)
    mock_materialize_target.assert_called_once_with("alpha", family=None)
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id=None,
        repo_ids=["repo-a", "repo-b"],
        repo_ref_overrides={"repo-a": "feature-x", "repo-b": "release-y"},
        runner="task",
        command_name="hello",
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile="ci",
        non_interactive=True,
        family=None,
    )


def test_phench_projects_run_include_repo_filter_reduces_repo_id_scope() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
    )
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--repo-id",
                "repo-a",
                "--include-repo",
                "repo-a",
                "--snapshot-id",
                "snapshot-001",
                "--runner",
                "task",
                "--command",
                "hello",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id="snapshot-001",
        repo_id="repo-a",
        runner="task",
        command_name="hello",
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_projects_run_excluded_repo_id_is_rejected() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
    )
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--repo-id",
                "repo-a",
                "--exclude-repo",
                "repo-a",
                "--snapshot-id",
                "snapshot-001",
                "--runner",
                "task",
                "--command",
                "hello",
            ],
        )

    assert result.exit_code != 0
    assert "repo filters resolved to no repositories" in (result.stdout + result.stderr)
    mock_run_target.assert_not_called()


def test_phench_projects_run_module_uses_manifest_subset_and_overrides() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[
            SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
            SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
            SimpleNamespace(repo_id="repo-c", selected_ref="main", resolved_sha="deadbabe"),
        ],
    )
    module_overrides = {
        "repo_ids": ["repo-a", "repo-c"],
        "repo_ref_overrides": {"repo-a": "staging"},
        "repo_runner_overrides": {"repo-c": "task"},
        "repo_command_overrides": {"repo-c": "hello"},
        "repo_env_profile_overrides": {"repo-a": "ci"},
    }
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
        patch("thegent.cli.apps.phench.lock_target") as mock_lock_target,
        patch("thegent.cli.apps.phench.materialize_target") as mock_materialize_target,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_load_module_manifest.return_value = module_overrides
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--module",
                "thegent-app",
                "--runner",
                "task",
                "--command",
                "hello",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_load_module_manifest.assert_called_once_with(
        "thegent-app",
        available_repo_ids=["repo-a", "repo-b", "repo-c"],
    )
    mock_load_target_lock.assert_called_once_with("alpha", family=None)
    mock_lock_target.assert_called_once_with("alpha", family=None)
    mock_materialize_target.assert_called_once_with("alpha", family=None)
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id=None,
        repo_ids=["repo-a", "repo-c"],
        repo_ref_overrides={"repo-a": "staging"},
        runner="task",
        command_name="hello",
        repo_runner_overrides={"repo-c": "task"},
        repo_command_overrides={"repo-c": "hello"},
        repo_env_profile_overrides={"repo-a": "ci"},
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_projects_run_module_with_all_repos_fails() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
        )
        mock_load_module_manifest.return_value = {
            "repo_ids": ["repo-a"],
            "repo_ref_overrides": {},
            "repo_runner_overrides": {},
            "repo_command_overrides": {},
            "repo_env_profile_overrides": {},
        }
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--module",
                "thegent-app",
                "--all-repos",
            ],
        )

    assert result.exit_code != 0
    mock_run_target.assert_not_called()
    output = result.stdout + result.stderr
    assert "--module is not compatible with --all-repos" in output


def test_phench_projects_run_module_repo_ref_merges_cli_and_manifest_overrides() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[
            SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
            SimpleNamespace(repo_id="repo-c", selected_ref="main", resolved_sha="deadcafe"),
        ],
    )
    module_overrides = {
        "repo_ids": ["repo-a", "repo-c"],
        "repo_ref_overrides": {"repo-a": "staging", "repo-c": "release"},
        "repo_runner_overrides": {},
        "repo_command_overrides": {},
        "repo_env_profile_overrides": {},
    }
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
        patch("thegent.cli.apps.phench.lock_target"),
        patch("thegent.cli.apps.phench.materialize_target"),
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_load_module_manifest.return_value = module_overrides
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--module",
                "thegent-app",
                "--repo-ref",
                "repo-a@feature-x",
                "--runner",
                "task",
                "--command",
                "hello",
                "--no-interactive",
            ],
        )

    assert result.exit_code == 0
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id=None,
        repo_ids=["repo-a", "repo-c"],
        repo_ref_overrides={"repo-a": "feature-x", "repo-c": "release"},
        runner="task",
        command_name="hello",
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_projects_run_repo_ref_rejects_all_repos() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--repo-ref",
                "repo-a@feature-x",
                "--all-repos",
                "--runner",
                "task",
                "--command",
                "hello",
            ],
        )

    assert result.exit_code != 0
    mock_run_target.assert_not_called()
    output = result.stdout + result.stderr
    assert "repo-ref is not compatible with --all-repos" in output


def _run_phench_projects_split_lane_smoke(
    module: str,
    manifest_repo_ids: list[str],
    expected_available_repo_ids: list[str],
    expected_repo_ids: list[str],
    include_repos: list[str] | None,
    exclude_repos: list[str] | None,
) -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[
            SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
            SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
            SimpleNamespace(repo_id="repo-c", selected_ref="main", resolved_sha="deadbabe"),
            SimpleNamespace(repo_id="repo-d", selected_ref="main", resolved_sha="cafe000"),
            SimpleNamespace(repo_id="repo-e", selected_ref="main", resolved_sha="facefeed"),
            SimpleNamespace(repo_id="repo-f", selected_ref="main", resolved_sha="f00df00d"),
        ],
    )

    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench_projects.load_module_manifest") as mock_load_module_manifest,
        patch("thegent.cli.apps.phench.lock_target") as mock_lock_target,
        patch("thegent.cli.apps.phench.materialize_target") as mock_materialize_target,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = lock
        mock_load_module_manifest.return_value = {
            "repo_ids": manifest_repo_ids,
            "repo_ref_overrides": {},
            "repo_runner_overrides": {},
            "repo_command_overrides": {},
            "repo_env_profile_overrides": {},
        }
        mock_run_target.return_value = 0

        cmd = [
            "phench",
            "projects",
            "run",
            "--target",
            "alpha",
            "--module",
            module,
            "--runner",
            "task",
            "--command",
            "hello",
            "--no-interactive",
        ]
        for include_repo in include_repos or []:
            cmd.extend(["--include-repo", include_repo])
        for exclude_repo in exclude_repos or []:
            cmd.extend(["--exclude-repo", exclude_repo])

        result = runner.invoke(app, cmd)

    assert result.exit_code == 0
    mock_load_module_manifest.assert_called_once_with(
        module,
        available_repo_ids=expected_available_repo_ids,
    )
    mock_lock_target.assert_called_once_with("alpha", family=None)
    mock_materialize_target.assert_called_once_with("alpha", family=None)
    mock_run_target.assert_called_once_with(
        "alpha",
        snapshot_id=None,
        repo_id=None,
        repo_ids=expected_repo_ids,
        runner="task",
        command_name="hello",
        selected_ref=None,
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_projects_run_split_lane_smoke_app_filters_repos() -> None:
    _run_phench_projects_split_lane_smoke(
        module="thegent-app",
        manifest_repo_ids=["repo-a", "repo-b", "repo-c"],
        expected_available_repo_ids=["repo-a", "repo-c"],
        expected_repo_ids=["repo-a", "repo-c"],
        include_repos=["repo-[a-c]"],
        exclude_repos=["repo-b"],
    )


def test_phench_projects_run_split_lane_smoke_mcp_filters_repos() -> None:
    _run_phench_projects_split_lane_smoke(
        module="thegent-mcp",
        manifest_repo_ids=["repo-b", "repo-c", "repo-d"],
        expected_available_repo_ids=["repo-b", "repo-d"],
        expected_repo_ids=["repo-b", "repo-d"],
        include_repos=["repo-[b-d]"],
        exclude_repos=["repo-c"],
    )


def test_phench_projects_run_split_lane_smoke_control_plane_filters_repos() -> None:
    _run_phench_projects_split_lane_smoke(
        module="thegent-control-plane",
        manifest_repo_ids=["repo-c", "repo-d"],
        expected_available_repo_ids=["repo-d"],
        expected_repo_ids=["repo-d"],
        include_repos=["repo-[c-d]"],
        exclude_repos=["repo-c"],
    )


def test_phench_projects_run_split_lane_smoke_execution_filters_repos() -> None:
    _run_phench_projects_split_lane_smoke(
        module="thegent-execution",
        manifest_repo_ids=["repo-a", "repo-e", "repo-f"],
        expected_available_repo_ids=["repo-a", "repo-b", "repo-c", "repo-d", "repo-e"],
        expected_repo_ids=["repo-a", "repo-e"],
        include_repos=["repo-[a-z]"],
        exclude_repos=["repo-f"],
    )


def test_phench_projects_run_split_lane_smoke_governance_filters_repos() -> None:
    _run_phench_projects_split_lane_smoke(
        module="thegent-governance",
        manifest_repo_ids=["repo-e", "repo-f"],
        expected_available_repo_ids=["repo-e"],
        expected_repo_ids=["repo-e"],
        include_repos=["repo-[e-f]"],
        exclude_repos=["repo-f"],
    )


def test_phench_projects_run_interactive_selection_uses_target_repo_and_ref_choices() -> None:
    lock = SimpleNamespace(
        target_name="alpha",
        repos=[
            SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef"),
            SimpleNamespace(repo_id="repo-b", selected_ref="main", resolved_sha="deadcafe"),
        ],
    )
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
        patch("thegent.cli.apps.phench.target_timeline") as mock_timeline,
        patch("thegent.cli.apps.phench.lock_target") as mock_lock_target,
        patch("thegent.cli.apps.phench.materialize_target") as mock_materialize_target,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
        patch("thegent.cli.apps.phench_projects.IntPrompt.ask") as mock_prompt,
    ):
        mock_list_targets.return_value = ["alpha", "beta"]
        mock_load_target_lock.return_value = lock
        mock_timeline.return_value = {
            "branches": ["main", "feature"],
            "tags": ["v1.0"],
            "recent": ["a1b2c3 commit one", "d4e5f6 commit two"],
        }
        mock_run_target.return_value = 0
        mock_prompt.side_effect = [2, 1, 3]
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--runner",
                "task",
                "--command",
                "hello",
                "--timeline-limit",
                "5",
            ],
        )

    assert result.exit_code == 0
    mock_prompt.assert_called()
    mock_load_target_lock.assert_called_once_with("beta", family=None)
    mock_timeline.assert_called_once_with("beta", repo_id="repo-a", limit=5, family=None)
    mock_lock_target.assert_called_once_with("beta", family=None)
    mock_materialize_target.assert_called_once_with("beta", family=None)
    mock_run_target.assert_called_once_with(
        "beta",
        snapshot_id=None,
        repo_id="repo-a",
        runner="task",
        command_name="hello",
        selected_ref="feature",
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=False,
        family=None,
    )


def test_phench_projects_run_non_interactive_requires_target_or_all() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--no-interactive",
                "--all-repos",
                "--runner",
                "task",
                "--command",
                "hello",
            ],
        )

    assert result.exit_code != 0
    mock_run_target.assert_not_called()
    output = result.stdout + result.stderr
    assert "--target is required when --no-interactive is set" in output


def test_phench_projects_run_non_interactive_single_repo_requires_ref_or_branch() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
        patch("thegent.cli.apps.phench.load_target_lock") as mock_load_target_lock,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_load_target_lock.return_value = SimpleNamespace(
            target_name="alpha",
            repos=[SimpleNamespace(repo_id="repo-a", selected_ref="main", resolved_sha="deadbeef")],
        )
        result = runner.invoke(
            app,
            [
                "phench",
                "projects",
                "run",
                "--target",
                "alpha",
                "--no-interactive",
                "--repo-id",
                "repo-a",
            ],
        )

    assert result.exit_code != 0
    mock_run_target.assert_not_called()
    output = result.stdout + result.stderr
    assert "Invalid value: --ref/--branch is required when --no-interactive is set for" in output


def test_phench_projects_status_routes_to_target_status() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.target_status") as mock_status,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_status.return_value = {
            "target": "alpha",
            "repos": [{"repo_id": "repo-a"}],
        }
        result = runner.invoke(app, ["phench", "projects", "status", "--target", "alpha"])

    assert result.exit_code == 0
    mock_status.assert_called_once_with("alpha", family=None)
    assert '"target": "alpha"' in result.stdout


def test_phench_tui_runs_selected_target_repo_and_ref() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.target_status") as mock_status,
        patch("thegent.cli.apps.phench.target_timeline") as mock_timeline,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
        patch("thegent.cli.apps.phench_observability.IntPrompt.ask") as mock_prompt,
    ):
        mock_list_targets.return_value = ["alpha", "beta"]
        mock_status.side_effect = [
            {"repos": [{"repo_id": "repo-a"}, {"repo_id": "repo-b"}]},
            {"repos": [{"repo_id": "repo-a"}, {"repo_id": "repo-b"}]},
        ]
        mock_timeline.return_value = {
            "branches": ["main", "feature"],
            "tags": ["v1"],
            "recent": ["a1 commit one", "b2 commit two"],
        }
        mock_run_target.return_value = 0
        mock_prompt.side_effect = [2, 1, 3]
        result = runner.invoke(
            app,
            [
                "phench",
                "tui",
                "--runner",
                "task",
                "--command",
                "hello",
            ],
        )

    assert result.exit_code == 0
    assert mock_timeline.call_count >= 1
    mock_run_target.assert_called_once_with(
        "beta",
        repo_id="repo-a",
        runner="task",
        command_name="hello",
        selected_ref="feature",
        all_repos=False,
        execution_mode="serial",
        env_profile=None,
        non_interactive=False,
        family=None,
    )


def test_phench_tui_all_repos_no_interactive_allows_policy_defaults() -> None:
    with (
        patch("thegent.cli.apps.phench.list_targets") as mock_list_targets,
        patch("thegent.cli.apps.phench.target_status") as mock_status,
        patch("thegent.cli.apps.phench.target_timeline") as mock_timeline,
        patch("thegent.cli.apps.phench.run_target") as mock_run_target,
    ):
        mock_list_targets.return_value = ["alpha"]
        mock_status.return_value = {"repos": [{"repo_id": "repo-a"}, {"repo_id": "repo-b"}]}
        mock_timeline.return_value = {
            "branches": [],
            "tags": [],
            "recent": ["a1b2c3 commit one", "d4e5f6 commit two"],
        }
        mock_run_target.return_value = 0
        result = runner.invoke(
            app,
            [
                "phench",
                "tui",
                "--no-interactive",
                "--all-repos",
            ],
        )

    assert result.exit_code == 0
    mock_run_target.assert_called_once_with(
        "alpha",
        repo_id=None,
        runner=None,
        command_name=None,
        selected_ref=None,
        all_repos=True,
        execution_mode="serial",
        env_profile=None,
        non_interactive=True,
        family=None,
    )


def test_phench_snapshot_create_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.create_target_snapshot") as mock_create_snapshot:
        mock_create_snapshot.return_value = {"snapshot_id": "snap-001", "target": "alpha"}
        result = runner.invoke(
            app,
            [
                "phench",
                "snapshot",
                "create",
                "alpha",
                "--snapshot-id",
                "snap-001",
            ],
        )

    assert result.exit_code == 0
    mock_create_snapshot.assert_called_once_with("alpha", snapshot_id="snap-001", family=None)


def test_phench_snapshot_list_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.list_target_snapshots") as mock_list_snapshots:
        mock_list_snapshots.return_value = []
        result = runner.invoke(
            app,
            [
                "phench",
                "snapshot",
                "list",
                "alpha",
            ],
        )

    assert result.exit_code == 0
    mock_list_snapshots.assert_called_once_with("alpha", family=None)


def test_phench_snapshot_show_routes_to_service() -> None:
    with patch("thegent.cli.apps.phench.show_target_snapshot") as mock_show_snapshot:
        mock_show_snapshot.return_value = {"snapshot_id": "snap-001", "target_name": "alpha"}
        result = runner.invoke(
            app,
            [
                "phench",
                "snapshot",
                "show",
                "alpha",
                "snap-001",
            ],
        )

    assert result.exit_code == 0
    mock_show_snapshot.assert_called_once_with("alpha", "snap-001", family=None)


def test_global_setup_command_delegates_to_setup_cmd() -> None:
    """`thegent setup` should run the legacy setup command implementation."""
    with patch("thegent.cli.apps.main.model_cmds.setup_cmd") as mock_setup_cmd:
        result = runner.invoke(
            app,
            ["setup", "--no-wizard", "--full", "--hooks", "--skills", "--harness"],
        )

    assert result.exit_code == 0
    mock_setup_cmd.assert_called_once()
    kwargs = mock_setup_cmd.call_args.kwargs
    assert kwargs["wizard"] is False
    assert kwargs["full"] is True
    assert kwargs["hooks"] is True
    assert kwargs["skills"] is True
    assert kwargs["harness"] is True


def test_global_git_command_group_is_registered() -> None:
    """`thegent git` must appear as a first-class command in help output."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "git" in result.stdout


def test_global_git_help_exits_zero() -> None:
    """`thegent git --help` should execute through the registered git typer app."""
    result = runner.invoke(app, ["git", "--help"])

    assert result.exit_code == 0
    assert "Usage: thegent git" in result.stdout
