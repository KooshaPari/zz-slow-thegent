"""E2E tests for thegent CLI (read-only, deterministic)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import orjson as json
import pytest

from tests.e2e.cli_assertions import load_cli_json
from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
class TestListAgents:
    """E2E tests for list-agents command."""

    def test_list_agents_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-agents exits 0."""
        result = runner.invoke(app, ["list-agents"])
        assert result.exit_code == 0

    def test_list_agents_contains_gemini(self) -> None:
        # @trace FR-CLI-001
        """Output contains gemini (deterministic)."""
        result = runner.invoke(app, ["list-agents"])
        assert "gemini" in result.stdout

    def test_list_agents_contains_all_expected(self) -> None:
        # @trace FR-CLI-001
        """Output contains all providers including minimax, glm, antigravity."""
        result = runner.invoke(app, ["list-agents"])
        for name in ["gemini", "codex", "copilot", "cursor", "claude", "antigravity", "minimax", "glm"]:
            assert name in result.stdout


@pytest.mark.e2e
class TestListDroids:
    """E2E tests for list-droids command."""

    def test_list_droids_exits_zero(self, project_root: Path) -> None:
        # @trace FR-CLI-001
        """list-droids exits 0 when droids exist."""
        # Use --cd=/path (Typer/Click parses path as command when space-separated)
        result = runner.invoke(app, ["list-droids", f"--cd={project_root}"])
        assert result.exit_code == 0

    def test_list_droids_contains_plan_orchestrator(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """Output contains plan-orchestrator when project has .factory/droids."""
        droids_dir = tmp_path / ".factory" / "droids"
        droids_dir.mkdir(parents=True)
        (droids_dir / "plan-orchestrator.md").write_text("# Plan Orchestrator\n")
        result = runner.invoke(app, ["list-droids", f"--cd={tmp_path}"])
        assert result.exit_code == 0
        assert "plan-orchestrator" in result.stdout


@pytest.mark.e2e
class TestClodeCommands:
    """E2E tests for clode shims and help text."""

    def test_clode_help_exits_zero(self) -> None:
        """`thegent clode --help` exits 0."""
        result = runner.invoke(app, ["clode", "--help"])
        assert result.exit_code == 0
        assert "thegent clode" in result.stdout
        assert "glm" in result.stdout

    def test_clode_no_subcommand_defaults_to_nim_interactive(self, monkeypatch) -> None:
        """`thegent clode` defaults to Nim-backed interactive session."""
        calls: list[str] = []

        def fake_run(provider: str) -> None:
            calls.append(provider)

        monkeypatch.setattr("thegent.clode_main._run_claude_interactive", fake_run)
        result = runner.invoke(app, ["clode"])
        assert result.exit_code == 0
        assert calls == ["nim"]

    def test_clode_install_links_force_rewrites_wrappers(self, tmp_path: Path, monkeypatch) -> None:
        """`thegent clode install-links --force` creates clode -> thegent-shims link."""
        (tmp_path / "thegent-shims").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (tmp_path / "thegent-shims").chmod(0o755)
        monkeypatch.setattr("thegent.clode_main.shutil.which", lambda _name: None)

        # Start with legacy files to ensure --force path is exercised.
        (tmp_path / "clode").write_text("legacy")
        result = runner.invoke(
            app,
            [
                "clode",
                "install-links",
                f"--bin-dir={tmp_path}",
                "--force",
            ],
        )
        assert result.exit_code == 0
        wrapper = tmp_path / "clode"
        assert wrapper.is_symlink()
        assert wrapper.resolve() == (tmp_path / "thegent-shims").resolve()

    def test_clode_glm_policy_round_robin_cycles_and_cheapest(self, monkeypatch) -> None:
        """`thegent clode glm` routes through policy-defined backends."""
        calls: list[str] = []

        def fake_run(provider: str) -> None:
            calls.append(provider)

        monkeypatch.setattr("thegent.clode_main._run_claude_interactive", fake_run)
        monkeypatch.setattr("thegent.clode_main._GLM_POLICY_COUNTER", {"glm": 0})
        result = runner.invoke(app, ["clode", "glm", "--policy", "round_robin"])
        assert result.exit_code == 0
        assert calls == ["nim"]

        result = runner.invoke(app, ["clode", "glm", "--policy", "round_robin"])
        assert result.exit_code == 0
        assert calls == ["nim", "kilo"]

        result = runner.invoke(app, ["clode", "glm", "--policy", "cheapest"])
        assert result.exit_code == 0
        assert calls[-1] == "nim"

    def test_clode_glm_prefer_openrouter(self, monkeypatch) -> None:
        """`thegent clode glm --prefer openrouter` routes directly to openrouter."""
        calls: list[str] = []

        def fake_run(provider: str) -> None:
            calls.append(provider)

        monkeypatch.setattr("thegent.clode_main._run_claude_interactive", fake_run)
        result = runner.invoke(app, ["clode", "glm", "--prefer", "openrouter"])
        assert result.exit_code == 0
        assert calls == ["openrouter"]

    def test_clode_glm_invalid_policy(self) -> None:
        """`thegent clode glm --policy bad` exits 1 with policy error."""
        result = runner.invoke(app, ["clode", "glm", "--policy", "badpolicy"])
        assert result.exit_code == 1


@pytest.mark.e2e
class TestRunAmbiguousCwd:
    """E2E tests for run with ambiguous cwd (no project indicators)."""

    def test_ambiguous_cwd_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Run from bare dir exits 1 with message."""
        bare = tmp_path / "bare"
        bare.mkdir()
        monkeypatch.chdir(bare)
        result = runner.invoke(app, ["run", "test", "gemini"])
        assert result.exit_code == 1
        assert "Ambiguous cwd" in result.stdout or "Provide --cd" in result.stdout


@pytest.mark.e2e
class TestRunWithExplicitCd:
    """E2E tests for run with explicit --cd (read-only)."""

    def test_unknown_agent_exits_one(self, project_root: Path) -> None:
        # @trace FR-CLI-001
        """Unknown agent exits 1 with message."""
        # Options first (Typer parses options-after-positionals as commands)
        result = runner.invoke(
            app,
            ["run", "agent", "test prompt", "--agent", "nonexistent-agent-xyz", "-d", str(project_root)],
        )
        assert result.exit_code == 1
        assert result.stdout.strip()

    def test_unknown_agent_suggests_agents_list(
        # @trace FR-CLI-001
        self,
        project_root: Path,
        tmp_path: Path,
    ) -> None:
        """Invoking unknown agent (e.g. plan-orchestrator) suggests agent list."""
        result = runner.invoke(
            app,
            ["run", "agent", "test prompt", "--agent", "plan-orchestrator", "-d", str(tmp_path)],
        )
        assert result.exit_code == 1
        assert result.stdout.strip()


@pytest.mark.e2e
class TestSessionContractHealthGate:
    """E2E tests for session-contract-health-gate command."""

    def test_health_gate_exits_zero_with_empty_sessions(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Health gate exits 0 when no sessions (empty state passes)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate"])
        assert result.exit_code == 0

    def test_health_gate_format_json_has_schema(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Health gate --format json outputs schema_version and payload_type."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert data.get("schema_version") == "health-schema-v1"
        assert data.get("payload_type") == "session_contract_health_gate"
        assert "pass" in data
        assert "status" in data

    def test_health_gate_output_to_file(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Health gate --output writes artifact with --overwrite."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        out_path = tmp_path / "gate.json"
        result = runner.invoke(
            app,
            ["session-contract-health-gate", "--output", str(out_path), "--overwrite"],
        )
        assert result.exit_code == 0
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert data.get("payload_type") == "session_contract_health_gate"


@pytest.mark.e2e
class TestSessionContractHealthReport:
    """E2E tests for session-contract-health-report command."""

    def test_health_report_exits_zero_with_empty_sessions(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Health report exits 0 when no sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-report"])
        assert result.exit_code == 0

    def test_health_report_format_json_has_schema(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Health report --format json outputs schema_version and payload_type."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-report", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert data.get("schema_version") == "health-schema-v1"
        assert data.get("payload_type") == "session_contract_health_report"
        assert "status" in data
        assert "health" in data


@pytest.mark.e2e
class TestResolveModelRoute:
    """E2E tests for resolve-model-route command."""

    def test_resolve_known_model_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route gemini-3-flash exits 0."""
        result = runner.invoke(app, ["resolve-model-route", "gemini-3-flash"])
        assert result.exit_code == 0

    def test_resolve_known_model_output_has_route(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route output has route_found and resolved_route."""
        result = runner.invoke(app, ["resolve-model-route", "gemini-3-flash"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert data.get("route_found") is True
        assert "resolved_route" in data
        assert data["resolved_route"].get("provider") == "gemini"
        assert data["resolved_route"].get("schema_version") == 1

    def test_resolve_unknown_model_exits_one(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route unknown model exits 1."""
        result = runner.invoke(app, ["resolve-model-route", "unknown-model-xyz"])
        assert result.exit_code == 1


@pytest.mark.e2e
class TestListModels:
    """E2E tests for list-models command."""

    def test_list_models_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-models exits 0."""
        result = runner.invoke(app, ["list-models"])
        assert result.exit_code == 0

    def test_list_models_contains_gemini(self) -> None:
        # @trace FR-CLI-001
        """list-models output contains gemini."""
        result = runner.invoke(app, ["list-models"])
        assert "gemini" in result.stdout


@pytest.mark.e2e
class TestModelsContract:
    """E2E tests for models contract command."""

    def test_models_contract_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """models contract exits 0."""
        result = runner.invoke(app, ["models", "contract"])
        assert result.exit_code == 0

    def test_models_contract_output_has_schema_version(self) -> None:
        # @trace FR-CLI-001
        """models contract output has schema_version."""
        result = runner.invoke(app, ["models", "contract"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert data.get("schema_version") == 1
        assert "backend_types" in data
        assert "policy_names" in data


@pytest.mark.e2e
class TestHistory:
    """E2E tests for history command."""

    def test_history_exits_zero_with_empty_registry(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """History exits 0 when run registry is empty."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history"])
        assert result.exit_code == 0
        assert "No runs" in result.stdout or "No execution history" in result.stdout

    def test_history_format_json_with_empty_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """History --format json with empty registry exits 0 (early return or [])."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "--format", "json"])
        assert result.exit_code == 0
        # Empty registry: either early-return "No runs" or JSON []
        if result.stdout.strip().startswith("["):
            data = load_cli_json(result.stdout)
            assert isinstance(data, list)
            assert len(data) == 0
        else:
            assert "No runs" in result.stdout or "No execution history" in result.stdout


@pytest.mark.e2e
class TestPs:
    """E2E tests for ps command."""

    def test_ps_exits_zero_with_empty_sessions(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps exits 0 when no sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout

    def test_ps_format_json_with_empty_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps --format json with empty sessions exits 0 (early return or [])."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps", "--format", "json"])
        assert result.exit_code == 0
        # Empty: either early-return "No sessions" or JSON []
        if result.stdout.strip().startswith("["):
            data = load_cli_json(result.stdout)
            assert isinstance(data, list)
            assert len(data) == 0
        else:
            assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestSessionContracts:
    """E2E tests for session-contracts command."""

    def test_session_contracts_exits_zero_with_empty(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts exits 0 when no sessions match."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestStatusLogsWaitStop:
    """E2E tests for status, logs, wait, stop with unknown session."""

    def test_status_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """status with unknown session_id exits 2 with Session not found."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["status", "session_unknown_e2e_123"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_logs_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """logs with unknown session_id exits 2 with Session not found."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["logs", "session_unknown_e2e_456"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr or "Log file missing" in result.stderr

    def test_wait_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """wait with unknown session_id exits 2 with Session not found."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["wait", "session_unknown_e2e_789"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_stop_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """stop with unknown session_id exits 2 with Session not found."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["stop", "session_unknown_e2e_999"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


@pytest.mark.e2e
class TestInspect:
    """E2E tests for inspect command."""

    def test_inspect_with_owner_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """inspect --owner when no sessions exits 0 with No sessions found."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["inspect", "--owner", "e2e_test_owner_xyz"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestDagList:
    """E2E tests for dag list command."""

    def test_dag_list_no_dag_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag list with --cd to dir without .factory/dag-session.md exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()  # project indicator
        result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert result.exit_code == 1
        assert "DAG session not found" in result.stdout or "DAG session not found" in result.stderr

    def test_dag_list_empty_dag_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag list with empty dag-session.md exits 0 with No tasks."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = "# DAG Session\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        (factory / "dag-session.md").write_text(dag_content)
        result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert result.exit_code == 0
        assert "No tasks" in result.stdout

    def test_dag_list_ambiguous_cwd_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag list from bare dir without --cd exits 1 with Ambiguous cwd."""
        bare = tmp_path / "bare"
        bare.mkdir()
        monkeypatch.chdir(bare)
        result = runner.invoke(app, ["dag", "list"])
        assert result.exit_code == 1
        assert "Ambiguous cwd" in result.stdout or "Provide --cd" in result.stdout


@pytest.mark.e2e
class TestDagValidate:
    """E2E tests for dag validate command."""

    def test_dag_validate_no_dag_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag validate with --cd to dir without dag-session.md exits 2."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        result = runner.invoke(app, ["dag", "validate", "--cd", str(project)])
        assert result.exit_code == 2
        assert "DAG session not found" in result.stdout or "DAG session not found" in result.stderr

    def test_dag_validate_valid_empty_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag validate with valid empty dag-session.md exits 0."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = "# DAG Session\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        (factory / "dag-session.md").write_text(dag_content)
        result = runner.invoke(app, ["dag", "validate", "--cd", str(project)])
        assert result.exit_code == 0
        assert "DAG valid" in result.stdout


@pytest.mark.e2e
class TestSessionContractHealthTrend:
    """E2E tests for session-contract-health-trend command."""

    def test_health_trend_exits_zero_with_empty_snapshots(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend exits 0 when no snapshots."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend"])
        assert result.exit_code == 0

    def test_health_trend_format_json_has_schema(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --format json has schema fields."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "schema_version" in data or "payload_type" in data
        assert "snapshot_count" in data or "trend_payload_type" in data


@pytest.mark.e2e
class TestPolicyProfile:
    """E2E tests for --policy-profile on health gate and report."""

    def test_health_gate_policy_profile_strict_ci(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --policy-profile strict_ci exits 0 with empty sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            ["session-contract-health-gate", "--policy-profile", "strict_ci"],
        )
        assert result.exit_code == 0
        assert "policy_profile" in result.stdout or "strict_ci" in result.stdout

    def test_health_report_policy_profile_warn_only(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --policy-profile warn_only exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            ["session-contract-health-report", "--policy-profile", "warn_only"],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestModelsRefresh:
    """E2E tests for models refresh command."""

    def test_models_refresh_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """models refresh exits 0 (cache empty or invalidated)."""
        result = runner.invoke(app, ["models", "refresh"])
        assert result.exit_code == 0
        assert "cache" in result.stdout.lower()


@pytest.mark.e2e
class TestDagStatusReadySync:
    """E2E tests for dag status, ready, sync commands."""

    def _empty_dag_project(self, tmp_path: Path) -> Path:
        """Create project with empty valid dag-session.md."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = "# DAG Session\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        (factory / "dag-session.md").write_text(dag_content)
        return project

    def test_dag_status_no_dag_exits_one(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag status with no dag-session.md exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        result = runner.invoke(app, ["dag", "status", "--cd", str(project)])
        assert result.exit_code == 1
        assert "DAG session not found" in result.stdout or "DAG session not found" in result.stderr

    def test_dag_status_empty_dag_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag status with empty DAG exits 0 with No tasks with session_id."""
        project = self._empty_dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "status", "--cd", str(project)])
        assert result.exit_code == 0
        assert "No tasks with session_id" in result.stdout

    def test_dag_ready_no_dag_exits_one(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag ready with no dag-session.md exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        result = runner.invoke(app, ["dag", "ready", "--cd", str(project)])
        assert result.exit_code == 1
        assert "DAG session not found" in result.stdout or "DAG session not found" in result.stderr

    def test_dag_ready_empty_dag_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag ready with empty DAG exits 0 with No ready tasks."""
        project = self._empty_dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "ready", "--cd", str(project)])
        assert result.exit_code == 0
        assert "No ready tasks" in result.stdout

    def test_dag_sync_no_dag_exits_one(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag sync with no dag-session.md exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        result = runner.invoke(app, ["dag", "sync", "--cd", str(project)])
        assert result.exit_code == 1
        assert "DAG session not found" in result.stdout or "DAG session not found" in result.stderr

    def test_dag_sync_empty_dag_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag sync with empty DAG exits 0 (no running sessions to sync)."""
        project = self._empty_dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "sync", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestListModelsIncludeContract:
    """E2E tests for list-models --include-contract."""

    def test_list_models_include_contract_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-models --include-contract exits 0."""
        result = runner.invoke(app, ["list-models", "--include-contract"])
        assert result.exit_code == 0

    def test_list_models_include_contract_output_has_schema(self) -> None:
        # @trace FR-CLI-001
        """list-models --include-contract outputs JSON with schema_version and routes."""
        result = runner.invoke(app, ["list-models", "--include-contract"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "schema_version" in data
        assert "routes" in data or "contract" in data


@pytest.mark.e2e
class TestResolveModelRoutePolicy:
    """E2E tests for resolve-model-route with different --policy values."""

    def test_resolve_model_route_policy_prefer_proxy(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route --policy prefer_proxy exits 0 with route."""
        result = runner.invoke(app, ["resolve-model-route", "gemini-3-flash", "--policy", "prefer_proxy"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert data.get("route_found") is True
        assert data.get("policy") == "prefer_proxy"

    def test_resolve_model_route_policy_failover(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route --policy failover exits 0 with available_routes."""
        result = runner.invoke(app, ["resolve-model-route", "gemini-3-flash", "--policy", "failover"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "available_routes" in data or data.get("route_found") is True


@pytest.mark.e2e
class TestNoWorseThanBaseline:
    """E2E tests for --no-worse-than-baseline on health gate and report."""

    def test_health_gate_no_worse_than_baseline_empty_baseline(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Gate with --no-worse-than-baseline and no baseline exits 0 (pass)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            ["session-contract-health-gate", "--no-worse-than-baseline"],
        )
        assert result.exit_code == 0

    def test_health_report_no_worse_than_baseline_empty_baseline(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Report with --no-worse-than-baseline and no baseline exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            ["session-contract-health-report", "--no-worse-than-baseline"],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagAdd:
    """E2E tests for dag add command."""

    def test_dag_add_then_list(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
    ) -> None:
        """dag add creates task; dag list shows it."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = "# DAG Session\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        (factory / "dag-session.md").write_text(dag_content)

        add_result = runner.invoke(
            app,
            ["dag", "add", "T1", "gemini", "test prompt", "--cd", str(project)],
        )
        assert add_result.exit_code == 0
        assert "Added task T1" in add_result.stdout

        list_result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "T1" in list_result.stdout
        assert "gemini" in list_result.stdout

    def test_dag_add_duplicate_exits_one(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag add with existing task_id exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = "# DAG Session\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n| T1 | gemini | p1 | — | pending |\n"
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(
            app,
            ["dag", "add", "T1", "gemini", "other prompt", "--cd", str(project)],
        )
        assert result.exit_code == 1
        assert "already exists" in result.stdout or "already exists" in result.stderr


@pytest.mark.e2e
class TestDagRemoveUpdateCancel:
    """E2E tests for dag remove, update, cancel commands."""

    def _project_with_task(self, tmp_path: Path, task_id: str = "T1") -> Path:
        """Create project with single task."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            f"| {task_id} | gemini | test | — | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)
        return project

    def test_dag_remove_then_list(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag remove removes task; dag list shows No tasks."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(app, ["dag", "remove", "T1", "--cd", str(project)])
        assert result.exit_code == 0
        assert "Removed task T1" in result.stdout

        list_result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "No tasks" in list_result.stdout

    def test_dag_remove_nonexistent_exits_one(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag remove with nonexistent task_id exits 1."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(app, ["dag", "remove", "T99", "--cd", str(project)])
        assert result.exit_code == 1
        assert "not found" in result.stdout or "not found" in result.stderr

    def test_dag_update_status_then_list(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag update --status done updates task; dag list shows done."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(app, ["dag", "update", "T1", "--status", "done", "--cd", str(project)])
        assert result.exit_code == 0

        list_result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "done" in list_result.stdout

    def test_dag_cancel_then_list(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag cancel sets status cancelled; dag list shows cancelled."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(app, ["dag", "cancel", "T1", "--cd", str(project)])
        assert result.exit_code == 0
        assert "Cancelled task T1" in result.stdout

        list_result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "cancelled" in list_result.stdout


@pytest.mark.e2e
class TestDagListFormat:
    """E2E tests for dag list --format md."""

    def test_dag_list_format_md_has_table(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag list --format md outputs markdown table with task."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "list", "--format", "md", "--cd", str(project)])
        assert result.exit_code == 0
        assert "## DAG Session" in result.stdout
        assert "| id |" in result.stdout
        assert "T1" in result.stdout


@pytest.mark.e2e
class TestSessionContractsFormat:
    """E2E tests for session-contracts --format json."""

    def test_session_contracts_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --format json exits 0 (empty: No sessions; non-empty: rows+summary)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--format", "json"])
        assert result.exit_code == 0
        # Empty sessions: early return with "No sessions" text
        if result.stdout.strip().startswith("{"):
            data = load_cli_json(result.stdout)
            assert "rows" in data
            assert "summary" in data
        else:
            assert "No sessions" in result.stdout or "contract" in result.stdout.lower()


@pytest.mark.e2e
class TestResolveModelRouteInvalidPolicy:
    """E2E tests for resolve-model-route with invalid policy."""

    def test_resolve_model_route_invalid_policy_exits_one(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route with invalid --policy exits 1."""
        result = runner.invoke(app, ["resolve-model-route", "gemini-3-flash", "--policy", "invalid_policy_xyz"])
        assert result.exit_code == 1
        assert "Invalid" in result.stdout or "policy" in result.stdout.lower() or "prefer_direct" in result.stdout


@pytest.mark.e2e
class TestDagValidationErrors:
    """E2E tests for dag add/update validation errors."""

    def _project_with_task(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | test | — | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)
        return project

    def test_dag_add_invalid_depends_on_exits_two(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag add with --depends-on referencing nonexistent task exits 2."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(
            app,
            ["dag", "add", "T2", "gemini", "prompt", "--depends-on", "T99", "--cd", str(project)],
        )
        assert result.exit_code == 2
        assert "does not exist" in result.stdout or "does not exist" in result.stderr

    def test_dag_update_invalid_status_exits_two(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag update with invalid --status exits 2."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(
            app,
            ["dag", "update", "T1", "--status", "invalid_status", "--cd", str(project)],
        )
        assert result.exit_code == 2
        assert "Invalid status" in result.stdout or "Invalid status" in result.stderr


@pytest.mark.e2e
class TestDagRunDryRun:
    """E2E tests for dag run --dry-run."""

    def test_dag_run_dry_run_no_ready_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag run --dry-run with no ready tasks exits 0 with No ready tasks."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "run", "--dry-run", "--cd", str(project)])
        assert result.exit_code == 0
        assert "No ready tasks" in result.stdout

    def test_dag_run_dry_run_with_ready_shows_would_run(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag run --dry-run with ready task shows Would run."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello world | — | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "run", "--dry-run", "--cd", str(project)])
        assert result.exit_code == 0
        assert "Would run" in result.stdout
        assert "T1" in result.stdout
        assert "gemini" in result.stdout


@pytest.mark.e2e
class TestListModelsByModel:
    """E2E tests for list-models --by-model."""

    def test_list_models_by_model_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-models --by-model exits 0."""
        result = runner.invoke(app, ["list-models", "--by-model"])
        assert result.exit_code == 0
        assert "Models by model ID" in result.stdout or "gemini" in result.stdout


@pytest.mark.e2e
class TestResolveModelRouteProvider:
    """E2E tests for resolve-model-route with --provider."""

    def test_resolve_model_route_with_provider_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route with --provider exits 0 with resolved route."""
        result = runner.invoke(
            app,
            ["resolve-model-route", "gemini-3-flash", "--provider", "gemini"],
        )
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert data.get("route_found") is True
        assert data.get("resolved_route", {}).get("provider") == "gemini"


@pytest.mark.e2e
class TestDagAddDependsOn:
    """E2E tests for dag add with --depends-on."""

    def test_dag_add_with_depends_on_then_list(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag add T2 with --depends-on T1; both appear in list."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | first | — | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(
            app,
            ["dag", "add", "T2", "gemini", "second", "--depends-on", "T1", "--cd", str(project)],
        )
        assert result.exit_code == 0
        assert "Added task T2" in result.stdout

        list_result = runner.invoke(app, ["dag", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "T1" in list_result.stdout
        assert "T2" in list_result.stdout


@pytest.mark.e2e
class TestDagReadyWithDeps:
    """E2E tests for dag ready with dependency chain."""

    def test_dag_ready_shows_t1_when_t2_depends_on_t1(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """When T2 depends on T1, only T1 is ready (T1 pending, T2 blocked)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | first | — | pending |\n"
            "| T2 | gemini | second | T1 | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "ready", "--cd", str(project)])
        assert result.exit_code == 0
        assert "T1" in result.stdout
        assert "T2" not in result.stdout or "No ready" in result.stdout

    def test_dag_ready_shows_t2_after_t1_done(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """When T1 is done, T2 becomes ready."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | first | — | done |\n"
            "| T2 | gemini | second | T1 | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "ready", "--cd", str(project)])
        assert result.exit_code == 0
        assert "T2" in result.stdout
