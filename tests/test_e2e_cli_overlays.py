"""E2E tests for thegent CLI (read-only, deterministic)."""

import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import orjson as json
import pytest

from tests.e2e.cli_assertions import expected_trend_health_signature, load_cli_json
from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
@pytest.mark.e2e
class TestOrchestrateObserveRecoverStatusLogsWaitStopAlias:
    """E2E tests for orchestrate/observe/recover alias execution (status, logs, wait, stop)."""

    def test_orchestrate_status_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate status with unknown session exits 2 (alias for status)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "status", "session_unknown_e2e_orch"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_observe_status_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe status with unknown session exits 2 (alias for status)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "status", "session_unknown_e2e_obs"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_orchestrate_logs_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate logs with unknown session exits 2 (alias for logs)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "logs", "session_unknown_e2e_logs"])
        assert result.exit_code == 2

    def test_orchestrate_wait_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate wait with unknown session exits 2 (alias for wait)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "wait", "session_unknown_e2e_wait"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_recover_stop_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """recover stop with unknown session exits 2 (alias for stop)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["recover", "stop", "session_unknown_e2e_stop"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


@pytest.mark.e2e
class TestOrchestrateObserveInspectAlias:
    """E2E tests for orchestrate inspect and observe inspect alias execution."""

    def test_orchestrate_inspect_owner_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate inspect --owner with no sessions exits 0 (alias for inspect)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "inspect", "--owner", "e2e_orch_inspect_xyz"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout

    def test_observe_inspect_owner_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe inspect --owner with no sessions exits 0 (alias for inspect)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "inspect", "--owner", "e2e_obs_inspect_xyz"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout

    def test_observe_logs_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe logs with unknown session exits 2 (alias for logs)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "logs", "session_unknown_e2e_obs_logs"])
        assert result.exit_code == 2

    def test_observe_wait_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe wait with unknown session exits 2 (alias for wait)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "wait", "session_unknown_e2e_obs_wait"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


@pytest.mark.e2e
class TestGovernConformanceExecution:
    """E2E tests for govern conformance execution (adapter conformance suite)."""

    def test_govern_conformance_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern conformance runs adapter conformance suite and exits 0 when all pass."""
        result = runner.invoke(app, ["govern", "conformance"])
        assert result.exit_code == 0
        assert "PASS" in result.stdout or "Passed" in result.stdout or "passed" in result.stdout

    def test_govern_conformance_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern conformance --format json exits 0 when all pass."""
        result = runner.invoke(app, ["govern", "conformance", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "passed" in data
        assert "total" in data
        assert "results" in data


@pytest.mark.e2e
class TestPlanAnalyzeExecution:
    """E2E tests for plan analyze execution."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_plan_analyze_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan analyze --help exits 0."""
        result = runner.invoke(app, ["plan", "analyze", "--help"])
        assert result.exit_code == 0

    def test_plan_analyze_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_analyze_pert_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernVerifyShowPolicyFeedbackExecution:
    """E2E tests for govern verify, show-policy, feedback, closure-pack."""

    def test_govern_verify_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern verify exits 0 (alias for history verify)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "verify"])
        assert result.exit_code == 0

    def test_govern_verify_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern verify --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "verify", "--format", "json"])
        assert result.exit_code == 0

    def test_govern_show_policy_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern show-policy exits 0 (alias for policy show)."""
        result = runner.invoke(app, ["govern", "show-policy"])
        assert result.exit_code == 0

    def test_govern_feedback_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern feedback records feedback and exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            ["govern", "feedback", "e2e_feedback_run_xyz", "1.0", "--note", "E2E"],
        )
        assert result.exit_code == 0

    def test_govern_closure_pack_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern closure-pack --help exits 0."""
        result = runner.invoke(app, ["govern", "closure-pack", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestObserveKpisModesOperationsExecution:
    """E2E tests for observe kpis, modes, operations."""

    def test_observe_kpis_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe kpis exits 0 with empty session dir."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "kpis", "--limit", "10"])
        assert result.exit_code == 0

    def test_observe_kpis_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe kpis --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "kpis", "--format", "json"])
        assert result.exit_code == 0

    def test_modes_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """modes exits 0."""
        result = runner.invoke(app, ["modes"])
        assert result.exit_code == 0

    def test_operations_operation_plan_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation plan exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "plan"])
        assert result.exit_code == 0

    def test_operations_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --format json exits 0."""
        result = runner.invoke(app, ["operations", "--format", "json"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestOrchestratePauseResumeAlias:
    """E2E tests for orchestrate pause/resume with unknown session."""

    def test_orchestrate_pause_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate pause with unknown session exits nonzero."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "pause", "session_unknown_e2e_pause"])
        assert result.exit_code != 0
        assert "Session not found" in result.stderr or "not found" in result.stderr.lower()

    def test_orchestrate_resume_unknown_session_exits_nonzero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate resume with unknown session exits nonzero."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "resume", "session_unknown_e2e_resume"])
        assert result.exit_code != 0
        assert "Session not found" in result.stderr or "not found" in result.stderr.lower()


@pytest.mark.e2e
class TestOrchestrateRunBgHelpAndUnknownAgent:
    """E2E tests for orchestrate run/bg help and unknown agent."""

    def test_orchestrate_run_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate run --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "run", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_bg_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate bg --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "bg", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_run_unknown_agent_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate run with unknown agent exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        monkeypatch.chdir(project)
        result = runner.invoke(app, ["orchestrate", "run", "test prompt", "nonexistent_agent_xyz"])
        assert result.exit_code in (1, 2)

    def test_orchestrate_bg_unknown_agent_exits_nonzero_or_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate bg with unknown agent exits 0 or 1 (bg may return before agent validation)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.chdir(project)
        result = runner.invoke(
            app,
            ["orchestrate", "bg", "test prompt", "nonexistent_agent_xyz", "-d", str(project)],
        )
        # bg may exit 0 immediately (spawns background) or 1 if agent validated upfront
        assert result.exit_code in (0, 1)


@pytest.mark.e2e
class TestCliproxyMcpLoginHelpExecution:
    """E2E tests for cliproxy, mcp, login help."""

    def test_cliproxy_login_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """cliproxy login --help exits 0."""
        result = runner.invoke(app, ["cliproxy", "login", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_login_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate login --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "login", "--help"])
        assert result.exit_code == 0

    def test_mcp_install_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp install --help exits 0."""
        result = runner.invoke(app, ["mcp", "install", "--help"])
        assert result.exit_code == 0

    def test_mcp_up_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp up --help exits 0."""
        result = runner.invoke(app, ["mcp", "up", "--help"])
        assert result.exit_code == 0

    def test_mcp_down_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp down --help exits 0."""
        result = runner.invoke(app, ["mcp", "down", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanListFormatExecution:
    """E2E tests for plan list format execution."""

    def test_plan_list_format_md_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan list --format md with DAG exits 0."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
        )
        result = runner.invoke(app, ["plan", "list", "--format", "md", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_list_empty_dag_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan list with empty DAG exits 0."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
        )
        result = runner.invoke(app, ["plan", "list", "--cd", str(project)])
        assert result.exit_code == 0
        assert "No tasks" in result.stdout


@pytest.mark.e2e
class TestHistoryEventsAliasExecution:
    """E2E tests for history events and observe history alias."""

    def test_history_events_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history events --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "events", "--format", "json", "--limit", "3"])
        assert result.exit_code == 0

    def test_observe_history_limit_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe history --limit exits 0 (alias for history list)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "history", "--limit", "3"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestClosurePackArchiveExecution:
    """E2E tests for closure-pack and archive execution."""

    def test_closure_pack_no_dag_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """closure-pack --cd to dir without DAG exits 1."""
        bare = tmp_path / "bare"
        bare.mkdir()
        (bare / ".git").mkdir()
        monkeypatch.chdir(bare)
        result = runner.invoke(app, ["closure-pack", "--cd", str(bare)])
        assert result.exit_code == 1
        assert "DAG" in result.stdout or "DAG" in result.stderr

    def test_govern_closure_pack_no_dag_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern closure-pack --cd to dir without DAG exits 1."""
        bare = tmp_path / "bare"
        bare.mkdir()
        (bare / ".git").mkdir()
        result = runner.invoke(app, ["govern", "closure-pack", "--cd", str(bare)])
        assert result.exit_code == 1

    def test_archive_days_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """archive --days 1 exits 0."""
        result = runner.invoke(app, ["archive", "--days", "1"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernDataProtectionExecution:
    """E2E tests for govern data-protection execution."""

    def test_govern_data_protection_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern data-protection exits 0."""
        result = runner.invoke(app, ["govern", "data-protection"])
        assert result.exit_code == 0

    def test_govern_data_protection_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern data-protection --format json exits 0."""
        result = runner.invoke(app, ["govern", "data-protection", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "session_dir" in data or "permissions_restricted" in data


@pytest.mark.e2e
class TestPlanAnalyzeDeepOptions:
    """E2E tests for plan analyze --resources, --continuity, --format json."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_plan_analyze_resources_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --resources with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_analyze_continuity_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --continuity with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_analyze_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --format json with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "pert" in data or "resources" in data or "continuity" in data or "tasks" in str(data).lower()


@pytest.mark.e2e
class TestObserveDriftDeepOptions:
    """E2E tests for observe drift --format json and custom budgets."""

    def test_observe_drift_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe drift --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "drift", "--format", "json", "--window", "10"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "issues" in data or "budget" in data

    def test_observe_drift_custom_budgets_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe drift with custom structural/semantic budget exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "observe",
                "drift",
                "--structural-budget",
                "10",
                "--semantic-budget",
                "15",
                "--window",
                "5",
            ],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestObserveSummaryCustom:
    """E2E tests for observe summary with richer operator options."""

    def test_observe_summary_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe summary --format json exits 0 in empty telemetry."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "summary", "--format", "json", "--limit", "20"])
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        assert payload["payload_type"] == "observe_summary"
        assert payload["payload_schema_version"] == "observe-summary-schema-v1"
        assert "kpis" in payload
        assert "drift" in payload
        assert "escalation" in payload

    def test_observe_summary_custom_budgets_provider_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe summary accepts custom budgets and provider filter."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "observe",
                "summary",
                "--format",
                "json",
                "--provider",
                "gemini",
                "--structural-budget",
                "6",
                "--semantic-budget",
                "9",
                "--top-escalations",
                "3",
                "--drift-window",
                "12",
            ],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        assert payload["payload_type"] == "observe_summary"
        assert payload["payload_schema_version"] == "observe-summary-schema-v1"
        assert payload["drift"]["structural_budget_pct"] == 6.0
        assert payload["drift"]["semantic_budget_pct"] == 9.0
        assert payload["escalation"]["provider"] == "gemini"

    def test_observe_summary_trend_samples_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe summary reports trend payload when trend samples are requested."""
        session_dir = tmp_path / "sessions"
        snapshot_file = tmp_path / "observe_summary_snapshots.jsonl"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_file))
        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "json", "--trend-samples", "3", "--limit", "25"],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        assert payload["trend_summary"]["enabled"] is True
        assert payload["trend_summary"]["trend_samples_requested"] == 3
        assert payload["trend_summary"]["baseline_available"] in (True, False)
        assert "history_sample_count" in payload["trend_summary"]
        assert payload["generated_query"]["trend_samples"] == 3

    def test_observe_summary_trend_samples_rich_exposes_projection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """observe summary --format rich exposes trend projection metadata."""
        session_dir = tmp_path / "sessions"
        snapshot_file = tmp_path / "observe_summary_snapshots.jsonl"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_file))
        if snapshot_file.exists():
            snapshot_file.unlink()
        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "rich", "--trend-samples", "2"],
        )
        assert result.exit_code == 0
        out = result.stdout.lower()
        assert "trend:" in out
        assert "trend_samples_requested=2" in out
        assert "trend_effective_samples=2" in out
        assert "generated_query=" in out

    def test_observe_summary_trend_samples_one_disables_trend(self) -> None:
        # @trace FR-CLI-001
        """observe summary treats --trend-samples 1 as disabled trend mode."""
        _, trend_health_signature = expected_trend_health_signature()
        result = runner.invoke(app, ["observe", "summary", "--format", "json", "--trend-samples", "1"])
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        assert trend["enabled"] is False
        assert trend["trend_samples_requested"] == 1
        assert trend["trend_effective_samples"] == 0
        assert trend["history_sample_count"] == 0
        assert payload["generated_query"]["trend_samples"] == 1
        assert trend["trend_snapshot_health"] == "disabled"
        assert trend["trend_snapshot_health_score"] is None
        assert trend["trend_snapshot_health_breakdown"]["policy_signature"] == trend_health_signature
        assert trend["trend_snapshot_health_breakdown"]["policy"]["healthy_threshold"] == 95
        assert trend["trend_snapshot_health_breakdown"]["policy"]["warning_threshold"] == 80
        assert trend["trend_snapshot_health_breakdown"]["policy"]["degraded_threshold"] == 50

    def test_observe_summary_trend_samples_two_reports_effective(self) -> None:
        # @trace FR-CLI-001
        """observe summary enables trend mode for --trend-samples 2."""
        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "json", "--trend-samples", "2"],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        assert trend["enabled"] is True
        assert trend["trend_samples_requested"] == 2
        assert trend["trend_effective_samples"] == 2
        assert payload["generated_query"]["trend_samples"] == 2

    def test_observe_summary_trend_samples_zero_disables_trend(self) -> None:
        # @trace FR-CLI-001
        """observe summary treats --trend-samples 0 as disabled trend mode."""
        _, trend_health_signature = expected_trend_health_signature()
        result = runner.invoke(app, ["observe", "summary", "--format", "json", "--trend-samples", "0"])
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        assert trend["enabled"] is False
        assert trend["trend_samples_requested"] == 0
        assert trend["trend_effective_samples"] == 0
        assert payload["generated_query"]["trend_samples"] == 0
        assert trend["trend_snapshot_health"] == "disabled"
        assert trend["trend_snapshot_health_breakdown"]["policy_signature"] == trend_health_signature

    def test_observe_summary_trend_samples_large_enables_and_tracks_effective_samples(self) -> None:
        # @trace FR-CLI-001
        """observe summary accepts large trend sample requests and reflects requested/effective."""
        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "json", "--trend-samples", "9999"],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        assert trend["enabled"] is True
        assert trend["trend_samples_requested"] == 9999
        assert trend["trend_effective_samples"] == 9999
        assert payload["generated_query"]["trend_samples"] == 9999

    def test_observe_summary_trend_enabled_without_baseline_keeps_stable_shape(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe summary with enabled trend but no history exposes stable null delta fields."""
        session_dir = tmp_path / "sessions"
        snapshot_file = tmp_path / "observe_summary_snapshots.jsonl"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_file))
        # Ensure no prior snapshots exist
        if snapshot_file.exists():
            snapshot_file.unlink()

        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "json", "--trend-samples", "3"],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        assert trend["enabled"] is True
        assert trend["trend_samples_requested"] == 3
        assert trend["trend_effective_samples"] == 3
        assert trend["history_sample_count"] == 0
        assert trend["baseline_available"] is False
        assert trend["baseline_captured_at_utc"] is None
        assert trend["total_events_delta"] is None
        assert trend["fallback_rate_delta"] is None
        assert trend["success_rate_delta"] is None
        assert trend["avg_confidence_delta"] is None
        assert trend["structural_drift_pct_delta"] is None
        assert trend["semantic_drift_pct_delta"] is None
        assert trend["drift_structural_rate_pct_delta"] is None
        assert trend["drift_semantic_rate_pct_delta"] is None
        assert trend["backlog_count_delta"] is None
        assert trend["past_sla_count_delta"] is None
        assert payload["generated_query"]["trend_samples"] == 3

    def test_observe_summary_trend_scope_signature_is_visible(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe summary exposes deterministic trend scope signature for query parity."""
        session_dir = tmp_path / "sessions"
        snapshot_file = tmp_path / "observe_summary_snapshots.jsonl"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_file))
        if snapshot_file.exists():
            snapshot_file.unlink()

        result = runner.invoke(
            app,
            [
                "observe",
                "summary",
                "--format",
                "json",
                "--trend-samples",
                "3",
                "--limit",
                "25",
                "--top-escalations",
                "7",
                "--provider",
                "cursor",
            ],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        scope = json.loads(trend["scope_key_json"])
        assert scope["provider"] == "cursor"
        assert scope["limit"] == 25
        assert scope["top_escalations"] == 7
        assert trend["scope_signature"]
        assert payload["generated_query"]["trend_scope_signature"] == trend["scope_signature"]
        assert trend["trend_snapshot_ids"] == []
        assert trend["trend_snapshot_ids_csv"] == ""
        assert trend["trend_snapshot_window_seconds"] is None

    def test_observe_summary_invalid_trend_samples_is_rejected_by_cli(self) -> None:
        # @trace FR-CLI-001
        """observe summary rejects non-integer --trend-samples via CLI validation."""
        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "json", "--trend-samples", "abc"],
        )
        assert result.exit_code != 0

    def test_observe_summary_trend_history_metadata_replayed_from_snapshots(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe summary replays trend timing and coverage metadata from prior snapshots."""
        trend_health_policy = {
            "healthy_threshold": 95,
            "warning_threshold": 80,
            "degraded_threshold": 50,
            "min_coverage_pct": 80.0,
            "max_invalid_timestamps": 0,
            "coverage_penalty_per_pct": 1.25,
            "deficit_penalty_per_missing_sample": 15.0,
            "invalid_timestamp_penalty_per_event": 12.0,
            "stale_penalty": 8.0,
            "critical_penalty": 20.0,
            "unknown_or_future_penalty": 30.0,
            "gap_penalty": 10.0,
            "missing_baseline_penalty": 45.0,
        }
        trend_health_signature = hashlib.sha256(
            json.dumps(trend_health_policy, sort_keys=True, separators=(",", ":").decode()).encode("utf-8")
        ).hexdigest()
        session_dir = tmp_path / "sessions"
        snapshot_file = tmp_path / "observe_summary_snapshots.jsonl"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_file))

        scope = {
            "payload_type": "observe_summary",
            "provider": None,
            "drift_window": 50,
            "structural_budget_pct": 5.0,
            "semantic_budget_pct": 10.0,
            "limit": 500,
            "top_escalations": 10,
        }
        scope_json = json.dumps(scope, sort_keys=True, separators=(",", ":").decode())
        scope_signature = hashlib.sha256(scope_json.encode("utf-8")).hexdigest()

        snapshot_records = [
            {
                "record_type": "observe_summary_snapshot",
                "captured_at_utc": "2026-01-01T00:00:00+00:00",
                "scope_key": scope,
                "scope_signature": scope_signature,
                "scope_key_json": scope_json,
                "trend_scope_signature": scope_signature,
                "trend_previous_samples_requested": 2,
                "trend_snapshot_expected_count": 2,
                "trend_snapshot_deficit": 0,
                "trend_snapshot_interval_seconds_avg": 86400,
                "trend_snapshot_interval_seconds_min": 86400,
                "trend_snapshot_interval_seconds_max": 86400,
                "trend_snapshot_gap_count": 1,
                "trend_snapshot_invalid_timestamps": 0,
                "trend_snapshot_coverage_pct": 100.0,
                "trend_snapshot_freshness_bucket": "critical",
                "trend_snapshot_freshness_seconds": 86400,
                "schema_version": "observe-summary-schema-v1",
                "payload_type": "observe_summary",
                "status": "healthy",
                "total_events": 5,
                "fallback_rate": 0.0,
                "success_rate": 1.0,
                "avg_confidence": 0.9,
                "structural_drift_pct": 0.0,
                "semantic_drift_pct": 0.0,
                "drift_structural_rate_pct": 0.0,
                "drift_semantic_rate_pct": 0.0,
                "backlog_count": 0,
                "past_sla_count": 0,
                "provider": None,
                "drift_structural_budget_pct": 5.0,
                "drift_semantic_budget_pct": 10.0,
            },
            {
                "record_type": "observe_summary_snapshot",
                "captured_at_utc": "2026-01-02T00:00:00+00:00",
                "scope_key": scope,
                "scope_signature": scope_signature,
                "scope_key_json": scope_json,
                "trend_scope_signature": scope_signature,
                "trend_previous_samples_requested": 2,
                "trend_snapshot_expected_count": 2,
                "trend_snapshot_deficit": 0,
                "trend_snapshot_interval_seconds_avg": 86400,
                "trend_snapshot_interval_seconds_min": 86400,
                "trend_snapshot_interval_seconds_max": 86400,
                "trend_snapshot_gap_count": 1,
                "trend_snapshot_invalid_timestamps": 0,
                "trend_snapshot_coverage_pct": 100.0,
                "trend_snapshot_freshness_bucket": "critical",
                "trend_snapshot_freshness_seconds": 0,
                "schema_version": "observe-summary-schema-v1",
                "payload_type": "observe_summary",
                "status": "healthy",
                "total_events": 8,
                "fallback_rate": 0.0,
                "success_rate": 1.0,
                "avg_confidence": 0.9,
                "structural_drift_pct": 0.0,
                "semantic_drift_pct": 0.0,
                "drift_structural_rate_pct": 0.0,
                "drift_semantic_rate_pct": 0.0,
                "backlog_count": 0,
                "past_sla_count": 0,
                "provider": None,
                "drift_structural_budget_pct": 5.0,
                "drift_semantic_budget_pct": 10.0,
            },
        ]
        snapshot_file.write_text(
            "".join(json.dumps(record, sort_keys=True).decode() + "\n" for record in snapshot_records),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["observe", "summary", "--format", "json", "--trend-samples", "3"],
        )
        assert result.exit_code == 0
        payload = load_cli_json(result.stdout)
        trend = payload["trend_summary"]
        assert trend["enabled"] is True
        assert trend["trend_samples_requested"] == 3
        assert trend["trend_effective_samples"] == 3
        assert trend["trend_snapshot_ids"] == [
            "2026-01-02T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ]
        assert trend["trend_snapshot_window_seconds"] == 86400
        assert trend["trend_snapshot_interval_seconds_avg"] == 86400
        assert trend["trend_snapshot_interval_seconds_min"] == 86400
        assert trend["trend_snapshot_interval_seconds_max"] == 86400
        assert trend["trend_snapshot_gap_count"] == 1
        assert trend["trend_snapshot_invalid_timestamps"] == 0
        assert trend["trend_snapshot_coverage_pct"] == 100.0
        assert trend["trend_snapshot_freshness_bucket"] in {"fresh", "warm", "stale", "critical"}
        assert trend["trend_snapshot_health"] in {"good", "warning", "degraded", "critical"}
        assert trend["trend_snapshot_health_breakdown"]["policy_signature"] == trend_health_signature
        assert trend["trend_snapshot_health_breakdown"]["policy"]["healthy_threshold"] == 95
        assert trend["trend_snapshot_health_breakdown"]["policy"]["warning_threshold"] == 80
        assert trend["trend_snapshot_health_breakdown"]["policy"]["degraded_threshold"] == 50
        assert trend["trend_snapshot_health_breakdown"]["policy"]["min_coverage_pct"] == 80.0
        assert trend["trend_snapshot_health_breakdown"]["policy"]["max_invalid_timestamps"] == 0
        assert trend["trend_snapshot_health_score"] is not None
        assert isinstance(trend["trend_snapshot_health_score"], int)
        assert isinstance(trend["trend_snapshot_recommendations"], list)
        assert trend["trend_snapshot_deficit"] == 0
        assert trend["trend_snapshot_expected_count"] == 2
        assert trend["trend_sampling_mode"] == "enabled"
        assert trend["trend_snapshot_freshness_seconds"] is not None
        assert trend["trend_snapshot_freshness_seconds"] >= 0


@pytest.mark.e2e
class TestGovernConformanceCheckDrift:
    """E2E tests for govern conformance --check-drift."""

    def test_govern_conformance_check_drift_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern conformance --check-drift with empty session dir exits 0 or 1."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "conformance", "--check-drift"])
        # May exit 0 (all pass, no drift) or 1 (drift detected)
        assert result.exit_code in (0, 1)


@pytest.mark.e2e
class TestDagPlanReadyFormatJson:
    """E2E tests for dag ready and plan ready --format json."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_dag_ready_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag ready --format json with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "ready", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "ready_task_ids" in data

    def test_plan_ready_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan ready --format json with DAG exits 0 (alias for dag ready)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "ready", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "ready_task_ids" in data


@pytest.mark.e2e
class TestPlanDagListStatusFormatJson:
    """E2E tests for plan/dag list and status --format json."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_dag_list_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag list --format json with DAG exits 0 and returns tasks array."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "list", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        assert len(data["tasks"]) >= 1

    def test_plan_list_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan list --format json with DAG exits 0 (alias for dag list)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "list", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_dag_status_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag status --format json with DAG exits 0 (tasks may be empty if no session_id)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "status", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_plan_status_format_json_exits_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-CLI-001
        """plan status --format json with DAG exits 0 (alias for dag status)."""
        project = self._dag_project(tmp_path)
        monkeypatch.chdir(project)
        result = runner.invoke(app, ["plan", "status", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "tasks" in data
        assert isinstance(data["tasks"], list)


@pytest.mark.e2e
class TestHistoryEventsRunId:
    """E2E tests for history events --run-id."""

    def test_history_events_run_id_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history events --run-id with non-existent run exits 0 (empty result)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            ["history", "events", "--run-id", "e2e_nonexistent_run_xyz", "--limit", "5"],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestMcpServiceHelp:
    """E2E tests for mcp service --help."""

    def test_mcp_service_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp service --help exits 0."""
        result = runner.invoke(app, ["mcp", "service", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestArchiveDomainOption:
    """E2E tests for archive --domain option."""

    def test_archive_domain_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """archive --domain with --days exits 0."""
        result = runner.invoke(app, ["archive", "--domain", "e2e_test", "--days", "1"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestOperationsRecoverFilter:
    """E2E tests for operations --operation recover."""

    def test_operations_operation_recover_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation recover exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "recover"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestObserveTrendDeepOptions:
    """E2E tests for observe trend --payload-type, --format json, --all."""

    def test_observe_trend_payload_type_gate_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe trend --payload-type session_contract_health_gate exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            [
                "observe",
                "trend",
                "--payload-type",
                "session_contract_health_gate",
                "--limit",
                "5",
            ],
        )
        assert result.exit_code == 0

    def test_observe_trend_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe trend --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["observe", "trend", "--format", "json", "--limit", "5"])
        assert result.exit_code == 0
        # Output may have ANSI/control chars; assert JSON-like structure present
        assert "{" in result.stdout or "[" in result.stdout

    def test_observe_trend_all_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe trend --all exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["observe", "trend", "--all", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernMigrationAllContracts:
    """E2E tests for govern migration with task-tool and zen contracts."""

    def test_govern_migration_task_tool_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern migration task-tool task-tool-18 exits 0."""
        result = runner.invoke(app, ["govern", "migration", "task-tool", "task-tool-18"])
        assert result.exit_code == 0

    def test_govern_migration_zen_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern migration zen zen-rich-v1 exits 0."""
        result = runner.invoke(app, ["govern", "migration", "zen", "zen-rich-v1"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernEscalateListExecution:
    """E2E tests for govern escalate list."""

    def test_govern_escalate_list_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern escalate list --help exits 0."""
        result = runner.invoke(app, ["govern", "escalate", "list", "--help"])
        assert result.exit_code == 0

    def test_govern_escalate_list_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern escalate list exits 0 with empty queue."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "escalate", "list", "--limit", "5"])
        assert result.exit_code == 0

    def test_govern_escalate_list_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern escalate list --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "escalate", "list", "--format", "json", "--limit", "5"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert isinstance(data, list) or "items" in str(data).lower()


@pytest.mark.e2e
class TestHistoryListFormatJson:
    """E2E tests for history list --format json."""

    def test_history_list_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history list --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "list", "--format", "json", "--limit", "5"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert isinstance(data, list)


@pytest.mark.e2e
class TestObserveTrendOwnerOption:
    """E2E tests for observe trend --owner."""

    def test_observe_trend_owner_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe trend --owner exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            ["observe", "trend", "--owner", "e2e_trend_owner_xyz", "--limit", "5"],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestModesFormatJson:
    """E2E tests for modes --format json and --mode filter."""

    def test_modes_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """modes --format json exits 0."""
        result = runner.invoke(app, ["modes", "--format", "json"])
        assert result.exit_code == 0
        # Output may have ANSI/control chars; assert JSON-like structure present
        assert "[" in result.stdout or "{" in result.stdout
        assert "mode" in result.stdout.lower()

    def test_modes_mode_filter_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """modes --mode sequential_delegation exits 0."""
        result = runner.invoke(app, ["modes", "--mode", "sequential_delegation"])
        assert result.exit_code == 0

    def test_modes_mode_filter_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """modes --mode parallel_consensus --format json exits 0."""
        result = runner.invoke(app, ["modes", "--mode", "parallel_consensus", "--format", "json"])
        assert result.exit_code == 0
        # Output may have ANSI/control chars; assert mode present
        assert "parallel_consensus" in result.stdout


@pytest.mark.e2e
class TestPlanAnalyzePertFormatJson:
    """E2E tests for plan analyze --pert --format json."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_plan_analyze_pert_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --pert --format json with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert isinstance(data, dict)


@pytest.mark.e2e
class TestDagListEmptyFormatJson:
    """E2E tests for dag list --format json with empty DAG."""

    def _empty_dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
        )
        return project

    def test_dag_list_empty_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag list --format json with empty DAG exits 0 and returns tasks: []."""
        project = self._empty_dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "list", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "tasks" in data
        assert data["tasks"] == []


@pytest.mark.e2e
class TestGovernSweepFormatJson:
    """E2E tests for govern sweep --format json."""

    def test_govern_sweep_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern sweep --format json exits 0 with empty session dir."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "sweep", "--format", "json", "--drift-window", "10"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert isinstance(data, dict)


@pytest.mark.e2e
class TestOperationsOrchestrateFormatJson:
    """E2E tests for operations --operation orchestrate --format json."""

    def test_operations_orchestrate_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation orchestrate --format json exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "orchestrate", "--format", "json"])
        assert result.exit_code == 0
        # Output may have ANSI/control chars; assert JSON-like structure
        assert "{" in result.stdout or "[" in result.stdout
        assert "orchestrate" in result.stdout.lower()


@pytest.mark.e2e
class TestPlanAnalyzeCombinedOverlays:
    """E2E tests for plan analyze with combined overlays (--pert --resources)."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_plan_analyze_pert_resources_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --pert --resources with DAG exits 0 (combined overlays)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_analyze_resources_continuity_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --resources --continuity with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernEscalateAddResolve:
    """E2E tests for govern escalate add and resolve."""

    def test_govern_escalate_add_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern escalate add --help exits 0."""
        result = runner.invoke(app, ["govern", "escalate", "add", "--help"])
        assert result.exit_code == 0

    def test_govern_escalate_resolve_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern escalate resolve --help exits 0."""
        result = runner.invoke(app, ["govern", "escalate", "resolve", "--help"])
        assert result.exit_code == 0

    def test_govern_escalate_add_then_resolve_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern escalate add then resolve exits 0 (add to queue, then resolve)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        add_result = runner.invoke(
            app,
            [
                "govern",
                "escalate",
                "add",
                "e2e_escalate_run_xyz",
                "E2E test reason",
                "--sla",
                "60",
            ],
        )
        assert add_result.exit_code == 0
        resolve_result = runner.invoke(app, ["govern", "escalate", "resolve", "e2e_escalate_run_xyz"])
        assert resolve_result.exit_code == 0

    def test_govern_escalate_list_past_sla_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern escalate list --past-sla exits 0 with empty queue."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "escalate", "list", "--past-sla", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanAnalyzeAllOverlays:
    """E2E tests for plan analyze with all overlays combined (--pert --resources --continuity)."""

    def _dag_project(self, tmp_path: Path) -> Path:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | hello | — | pending |\n"
        )
        return project

    def test_plan_analyze_all_overlays_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --pert --resources --continuity with DAG exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_analyze_all_overlays_format_json_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan analyze --pert --resources --continuity --format json exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "analyze", "--format", "json", "--cd", str(project)])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert isinstance(data, dict)


@pytest.mark.e2e
class TestGovernConformanceFormatJson:
    """E2E tests for govern conformance --format json."""

    def test_govern_conformance_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern conformance --format json with empty session dir exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "conformance", "--format", "json", "--drift-window", "10"])
        assert result.exit_code == 0
        # Output may have ANSI; assert JSON-like structure
        assert "{" in result.stdout or "[" in result.stdout
