"""E2E tests for thegent CLI (read-only, deterministic)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.e2e.cli_assertions import load_cli_json
from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
class TestListModelsProvider:
    """E2E tests for list-models with provider filter."""

    def test_list_models_provider_gemini_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-models gemini exits 0."""
        result = runner.invoke(app, ["list-models", "gemini"])
        assert result.exit_code == 0
        assert "gemini" in result.stdout.lower()


@pytest.mark.e2e
class TestDagValidateInvalid:
    """E2E tests for dag validate with invalid DAG."""

    def test_dag_validate_unknown_agent_exits_two(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag validate with unknown agent in task exits 2."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | unknown-agent-xyz | test | — | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "validate", "--cd", str(project)])
        assert result.exit_code == 2
        assert "Unknown agent" in result.stdout or "unknown-agent" in result.stdout

    def test_dag_validate_cycle_exits_two(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag validate with cycle (T1->T2->T1) exits 2."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | first | T2 | pending |\n"
            "| T2 | gemini | second | T1 | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "validate", "--cd", str(project)])
        assert result.exit_code == 2
        assert "cycle" in result.stdout.lower() or "Cycle" in result.stdout


@pytest.mark.e2e
class TestSessionContractsOptions:
    """E2E tests for session-contracts --missing-only and --summary-only."""

    def test_session_contracts_missing_only_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --missing-only exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--missing-only"])
        assert result.exit_code == 0

    def test_session_contracts_summary_only_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --summary-only exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--summary-only"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHelp:
    """E2E tests for --help."""

    def test_app_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """thegent --help exits 0."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "thegent" in result.stdout or "Usage" in result.stdout

    def test_dag_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """thegent dag --help exits 0."""
        result = runner.invoke(app, ["dag", "--help"])
        assert result.exit_code == 0
        assert "dag" in result.stdout.lower() or "list" in result.stdout


@pytest.mark.e2e
class TestHistoryLimit:
    """E2E tests for history --limit."""

    def test_history_limit_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history --limit 5 exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestSessionContractsStrict:
    """E2E tests for session-contracts --strict."""

    def test_session_contracts_strict_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --strict exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--strict"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPsAll:
    """E2E tests for ps --all."""

    def test_ps_all_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps --all exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps", "--all"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestHealthTrendPayloadType:
    """E2E tests for session-contract-health-trend --payload-type."""

    def test_health_trend_payload_type_gate_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --payload-type session_contract_health_gate exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            ["session-contract-health-trend", "--payload-type", "session_contract_health_gate"],
        )
        assert result.exit_code == 0
        assert "gate" in result.stdout.lower() or "trend" in result.stdout.lower()


@pytest.mark.e2e
class TestStatusFormat:
    """E2E tests for status --format and --include-contract."""

    def test_status_format_json_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """status unknown_session --format json exits 2 (option parses correctly)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["status", "session_unknown_e2e_format", "--format", "json"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_status_include_contract_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """status unknown_session --include-contract exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["status", "session_unknown_e2e_inc", "--include-contract"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


@pytest.mark.e2e
class TestDagRunDryRunWithTask:
    """E2E tests for dag run --dry-run --task."""

    def test_dag_run_dry_run_task_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag run --dry-run --task T1 with T1 ready shows Would run T1."""
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

        result = runner.invoke(app, ["dag", "run", "--dry-run", "--task", "T1", "--cd", str(project)])
        assert result.exit_code == 0
        assert "Would run" in result.stdout
        assert "T1" in result.stdout

    def test_dag_run_dry_run_task_not_ready_exits_one(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag run --dry-run --task T2 when T2 depends on T1 (pending) exits 1."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        dag_content = (
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            "| T1 | gemini | step 1 | — | pending |\n"
            "| T2 | gemini | step 2 | T1 | pending |\n"
        )
        (factory / "dag-session.md").write_text(dag_content)

        result = runner.invoke(app, ["dag", "run", "--dry-run", "--task", "T2", "--cd", str(project)])
        assert result.exit_code == 1
        assert "not ready" in result.stdout or "not ready" in result.stderr


@pytest.mark.e2e
class TestRegressionTolerance:
    """E2E tests for gate/report --regression-tolerance."""

    def test_gate_regression_tolerance_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --regression-tolerance 0.1 exits 0 with no sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "session-contract-health-gate",
                "--regression-tolerance",
                "0.1",
            ],
        )
        assert result.exit_code == 0

    def test_report_regression_tolerance_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --regression-tolerance 0.05 exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "session-contract-health-report",
                "--regression-tolerance",
                "0.05",
            ],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestModelsHelp:
    """E2E tests for models subcommand help."""

    def test_models_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """models --help exits 0."""
        result = runner.invoke(app, ["models", "--help"])
        assert result.exit_code == 0
        assert "Model catalog" in result.stdout or "refresh" in result.stdout


@pytest.mark.e2e
class TestDagCheckpoint:
    """E2E tests for dag checkpoint, checkpoints, recover, probe, rollback."""

    def test_dag_checkpoint_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag checkpoint exits 0 and creates checkpoint."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
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
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["dag", "checkpoint", "--cd", str(project), "--reason", "E2E test"])
        assert result.exit_code == 0

    def test_dag_checkpoints_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag checkpoints exits 0 (no checkpoints or lists them)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["dag", "checkpoints", "--limit", "5"])
        assert result.exit_code == 0
        assert "No checkpoints" in result.stdout or "Checkpoint" in result.stdout

    def test_dag_recover_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag recover exits 0 with DAG."""
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
        result = runner.invoke(app, ["dag", "recover", "retry-failed", "--cd", str(project)])
        assert result.exit_code == 0

    def test_dag_probe_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag probe exits 0 with DAG (no baseline or shows message)."""
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
        result = runner.invoke(app, ["dag", "probe", "--cd", str(project)])
        assert result.exit_code == 0
        assert "baseline" in result.stdout.lower() or "regression" in result.stdout.lower()

    def test_dag_rollback_unknown_checkpoint_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag rollback with unknown checkpoint_id exits 1."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
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
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["dag", "rollback", "ckpt_unknown_e2e", "--cd", str(project)])
        assert result.exit_code == 1
        assert "Checkpoint not found" in result.stdout or "Checkpoint not found" in result.stderr


@pytest.mark.e2e
class TestReportOutput:
    """E2E tests for session-contract-health-report --output."""

    def test_report_output_writes_artifact(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --output writes artifact with --overwrite."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        out_path = tmp_path / "report.json"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "session-contract-health-report",
                "--output",
                str(out_path),
                "--overwrite",
            ],
        )
        assert result.exit_code == 0
        assert out_path.exists()


@pytest.mark.e2e
class TestDagRecoverActions:
    """E2E tests for dag recover clear-stuck and reset-retries."""

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

    def test_dag_recover_clear_stuck_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag recover clear-stuck exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "recover", "clear-stuck", "--cd", str(project)])
        assert result.exit_code == 0

    def test_dag_recover_reset_retries_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag recover reset-retries exits 0."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["dag", "recover", "reset-retries", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagFormatOptions:
    """E2E tests for dag status and dag ready --format."""

    def test_dag_status_format_md_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag status --format md exits 0."""
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
        result = runner.invoke(app, ["dag", "status", "--cd", str(project), "--format", "md"])
        assert result.exit_code == 0

    def test_dag_ready_format_md_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag ready --format md exits 0."""
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
        result = runner.invoke(app, ["dag", "ready", "--cd", str(project), "--format", "md"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestMcpHelp:
    """E2E tests for mcp subcommand help."""

    def test_mcp_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp --help exits 0."""
        result = runner.invoke(app, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "install" in result.stdout or "MCP" in result.stdout


@pytest.mark.e2e
class TestInspectFormat:
    """E2E tests for inspect --format json."""

    def test_inspect_format_json_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """inspect --owner --format json with no sessions exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["inspect", "--owner", "e2e_inspect_format", "--format", "json"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout or "[]" in result.stdout


@pytest.mark.e2e
class TestLoginServeHelp:
    """E2E tests for login and serve --help."""

    def test_login_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """login --help exits 0."""
        result = runner.invoke(app, ["login", "--help"])
        assert result.exit_code == 0
        assert "provider" in result.stdout.lower() or "OAuth" in result.stdout

    def test_serve_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """serve --help exits 0."""
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "host" in result.stdout.lower() or "port" in result.stdout


@pytest.mark.e2e
class TestDagProbeBaselineId:
    """E2E tests for dag probe --baseline-id."""

    def test_dag_probe_unknown_baseline_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """dag probe --baseline-id unknown exits 1."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
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
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["dag", "probe", "--baseline-id", "ckpt_unknown_e2e", "--cd", str(project)])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()


@pytest.mark.e2e
class TestHealthTrendReportPayload:
    """E2E tests for session-contract-health-trend --payload-type report."""

    def test_health_trend_payload_type_report_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --payload-type session_contract_health_report exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--payload-type",
                "session_contract_health_report",
            ],
        )
        assert result.exit_code == 0
        assert "report" in result.stdout.lower() or "trend" in result.stdout.lower()


@pytest.mark.e2e
class TestGateExportFormat:
    """E2E tests for session-contract-health-gate --export-format."""

    def test_gate_export_format_md_writes_file(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --output with --export-format md writes markdown."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        out_path = tmp_path / "gate.md"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "session-contract-health-gate",
                "--output",
                str(out_path),
                "--export-format",
                "md",
                "--overwrite",
            ],
        )
        assert result.exit_code == 0
        assert out_path.exists()
        content = out_path.read_text()
        assert "pass" in content.lower() or "blocked" in content.lower() or "status" in content.lower()


@pytest.mark.e2e
class TestHistoryVerify:
    """E2E tests for history verify command."""

    def test_history_verify_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history verify exits 0 with empty registry."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "verify"])
        assert result.exit_code == 0
        assert "Audit" in result.stdout or "verified" in result.stdout.lower() or "empty" in result.stdout.lower()

    def test_history_verify_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history verify --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "verify", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "status" in data


@pytest.mark.e2e
class TestPolicyShow:
    """E2E tests for policy show command."""

    def test_policy_show_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """policy show exits 0."""
        result = runner.invoke(app, ["policy", "show"])
        assert result.exit_code == 0
        assert "Policy" in result.stdout or "Governance" in result.stdout


@pytest.mark.e2e
class TestCliproxyHelp:
    """E2E tests for cliproxy subcommand help."""

    def test_cliproxy_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """cliproxy --help exits 0."""
        result = runner.invoke(app, ["cliproxy", "--help"])
        assert result.exit_code == 0
        assert "login" in result.stdout


@pytest.mark.e2e
class TestMcpInstallHelp:
    """E2E tests for mcp install --help."""

    def test_mcp_install_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp install --help exits 0."""
        result = runner.invoke(app, ["mcp", "install", "--help"])
        assert result.exit_code == 0
        assert "client" in result.stdout.lower() or "cursor" in result.stdout.lower()


@pytest.mark.e2e
class TestReportExportOptions:
    """E2E tests for session-contract-health-report export and top-blocked options."""

    def test_report_export_format_csv_writes_file(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --output with --export-format csv writes CSV."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        out_path = tmp_path / "report.csv"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "session-contract-health-report",
                "--output",
                str(out_path),
                "--export-format",
                "csv",
                "--overwrite",
            ],
        )
        assert result.exit_code == 0
        assert out_path.exists()

    def test_report_top_blocked_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --top-blocked 10 exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--top-blocked", "10"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestCockpit:
    """E2E tests for cockpit command."""

    def test_cockpit_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """cockpit exits 0 with empty sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["cockpit"])
        assert result.exit_code == 0
        assert "Sessions" in result.stdout or "Orchestration" in result.stdout


@pytest.mark.e2e
class TestHistoryEventsList:
    """E2E tests for history events and history list."""

    def test_history_events_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history events exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "events", "--limit", "5"])
        assert result.exit_code == 0

    def test_history_list_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history list exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "list", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestStopOptions:
    """E2E tests for stop --force and --wind-down options."""

    def test_stop_force_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """stop --force unknown_session exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["stop", "--force", "session_unknown_e2e_stop_force"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr

    def test_stop_wind_down_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """stop --wind-down unknown_session exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["stop", "--wind-down", "session_unknown_e2e_wind_down"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


@pytest.mark.e2e
class TestMcpServiceHelp:
    """E2E tests for mcp service --help."""

    def test_mcp_service_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """mcp service --help exits 0."""
        result = runner.invoke(app, ["mcp", "service", "--help"])
        assert result.exit_code == 0
        assert "action" in result.stdout.lower() or "install" in result.stdout.lower()


@pytest.mark.e2e
class TestLogsWaitOptions:
    """E2E tests for logs and wait option parsing."""

    def test_logs_tail_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """logs --tail 10 unknown_session exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["logs", "session_unknown_e2e_logs_tail", "--tail", "10"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr or "Log file missing" in result.stderr

    def test_wait_timeout_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """wait --timeout 5 unknown_session exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["wait", "session_unknown_e2e_wait_to", "--timeout", "5"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


@pytest.mark.e2e
class TestHealthTrendOutput:
    """E2E tests for session-contract-health-trend --output and --limit."""

    def test_health_trend_output_writes_file(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --output writes artifact."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        out_path = tmp_path / "trend.json"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--output",
                str(out_path),
                "--overwrite",
            ],
        )
        assert result.exit_code == 0
        assert out_path.exists()

    def test_health_trend_limit_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --limit 5 exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPsFormat:
    """E2E tests for ps --format json."""

    def test_ps_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps --format json exits 0 with empty sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps", "--format", "json"])
        assert result.exit_code == 0
        out = result.stdout.strip()
        assert "No sessions" in out or (out.startswith(("[", "{")))


@pytest.mark.e2e
class TestInspectTail:
    """E2E tests for inspect --tail option."""

    def test_inspect_tail_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """inspect --owner --tail 20 with no sessions exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["inspect", "--owner", "e2e_inspect_tail", "--tail", "20"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestDagRunOptions:
    """E2E tests for dag run --max-parallel and --lane."""

    def test_dag_run_dry_run_max_parallel_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag run --dry-run --max-parallel 2 exits 0."""
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
        result = runner.invoke(
            app,
            ["dag", "run", "--dry-run", "--max-parallel", "2", "--cd", str(project)],
        )
        assert result.exit_code == 0
        assert "Would run" in result.stdout or "No ready" in result.stdout

    def test_dag_run_dry_run_lane_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag run --dry-run --lane standard exits 0."""
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
        result = runner.invoke(
            app,
            ["dag", "run", "--dry-run", "--lane", "standard", "--cd", str(project)],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHistoryEventsRunId:
    """E2E tests for history events --run-id."""

    def test_history_events_run_id_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history events --run-id some_id exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "events", "--run-id", "run_e2e_xyz", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHealthTrendFormat:
    """E2E tests for session-contract-health-trend --format."""

    def test_health_trend_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --format json exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "snapshots" in data or "trend_payload_type" in data


@pytest.mark.e2e
class TestPolicyHelp:
    """E2E tests for policy subcommand help."""

    def test_policy_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """policy --help exits 0."""
        result = runner.invoke(app, ["policy", "--help"])
        assert result.exit_code == 0
        assert "show" in result.stdout


@pytest.mark.e2e
class TestOperations:
    """E2E tests for operations command (universal operation taxonomy)."""

    def test_operations_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations exits 0."""
        result = runner.invoke(app, ["operations"])
        assert result.exit_code == 0
        assert "orchestrate" in result.stdout or "govern" in result.stdout

    def test_operations_format_json(self) -> None:
        # @trace FR-CLI-001
        """operations --format json exits 0 with valid JSON."""
        result = runner.invoke(app, ["operations", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "orchestrate" in data
        assert "govern" in data
        assert "recover" in data
        assert "observe" in data
        assert "plan" in data

    def test_operations_filter_orchestrate(self) -> None:
        # @trace FR-CLI-001
        """operations --operation orchestrate exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "orchestrate"])
        assert result.exit_code == 0
        assert "run" in result.stdout or "bg" in result.stdout


@pytest.mark.e2e
class TestFeedback:
    """E2E tests for feedback command."""

    def test_feedback_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """feedback run_id score exits 0 and records feedback."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["feedback", "run_e2e_feedback_xyz", "0.85", "--note", "E2E test"])
        assert result.exit_code == 0
        assert "Feedback recorded" in result.stdout

    def test_feedback_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """feedback --help exits 0."""
        result = runner.invoke(app, ["feedback", "--help"])
        assert result.exit_code == 0
        assert "run_id" in result.stdout or "score" in result.stdout


@pytest.mark.e2e
class TestHistoryHelp:
    """E2E tests for history subcommand help."""

    def test_history_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """history --help exits 0."""
        result = runner.invoke(app, ["history", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout or "verify" in result.stdout


@pytest.mark.e2e
class TestInspectStderr:
    """E2E tests for inspect --stderr option."""

    def test_inspect_stderr_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """inspect --owner --stderr with no sessions exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["inspect", "--owner", "e2e_inspect_stderr", "--stderr"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestStopGrace:
    """E2E tests for stop --grace option."""

    def test_stop_grace_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """stop --grace 10 unknown_session exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["stop", "--grace", "10", "session_unknown_e2e_grace"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr


# Preserve legacy monolithic collection parity: these names are redefined later
# in subsequent segments and should not be collected from this segment.
TestHistoryEventsRunId.__test__ = False
TestMcpServiceHelp.__test__ = False
TestOperations.__test__ = False
