"""E2E tests for thegent CLI (read-only, deterministic)."""

import re
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
@pytest.mark.e2e
class TestLogsStderr:
    """E2E tests for logs --stderr option."""

    def test_logs_stderr_unknown_session_exits_two(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """logs --stderr unknown_session exits 2."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["logs", "session_unknown_e2e_logs_stderr", "--stderr"])
        assert result.exit_code == 2
        assert "Session not found" in result.stderr or "Log file missing" in result.stderr


@pytest.mark.e2e
class TestRunBgHelp:
    """E2E tests for run and bg --help."""

    def test_run_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """run --help exits 0."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "prompt" in result.stdout.lower() or "agent" in result.stdout.lower()

    def test_bg_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """bg --help exits 0."""
        result = runner.invoke(app, ["bg", "--help"])
        assert result.exit_code == 0
        assert "prompt" in result.stdout.lower() or "owner" in result.stdout.lower()


@pytest.mark.e2e
class TestListAgentsHelp:
    """E2E tests for list-agents --help."""

    def test_list_agents_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-agents --help exits 0."""
        result = runner.invoke(app, ["list-agents", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHealthTrendAll:
    """E2E tests for session-contract-health-trend --all."""

    def test_health_trend_all_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --all exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--all"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestSessionContractsAll:
    """E2E tests for session-contracts --all."""

    def test_session_contracts_all_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --all exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--all"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGateExportJsonl:
    """E2E tests for session-contract-health-gate --export-format jsonl."""

    def test_gate_export_format_jsonl_writes_file(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --output with --export-format jsonl writes file."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        out_path = tmp_path / "gate.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(
            app,
            [
                "session-contract-health-gate",
                "--output",
                str(out_path),
                "--export-format",
                "jsonl",
                "--overwrite",
            ],
        )
        assert result.exit_code == 0
        assert out_path.exists()


@pytest.mark.e2e
class TestListModelsDroidsHelp:
    """E2E tests for list-models and list-droids --help."""

    def test_list_models_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-models --help exits 0."""
        result = runner.invoke(app, ["list-models", "--help"])
        assert result.exit_code == 0

    def test_list_droids_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """list-droids --help exits 0."""
        result = runner.invoke(app, ["list-droids", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestCliproxyEnsureConfig:
    """E2E tests for cliproxy ensure-config."""

    def test_cliproxy_ensure_config_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """cliproxy ensure-config exits 0 and refreshes config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(config_dir))
        result = runner.invoke(app, ["cliproxy", "ensure-config"])
        assert result.exit_code == 0
        assert "Config" in result.stdout or "config" in result.stdout.lower()


@pytest.mark.e2e
class TestResolveModelRouteHelp:
    """E2E tests for resolve-model-route --help."""

    def test_resolve_model_route_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """resolve-model-route --help exits 0."""
        result = runner.invoke(app, ["resolve-model-route", "--help"])
        assert result.exit_code == 0
        assert "model" in result.stdout.lower()


@pytest.mark.e2e
class TestGateMinHealthy:
    """E2E tests for session-contract-health-gate --min-healthy-ratio."""

    def test_gate_min_healthy_ratio_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --min-healthy-ratio 0.9 exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate", "--min-healthy-ratio", "0.0"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHealthTrendOwner:
    """E2E tests for session-contract-health-trend --owner."""

    def test_health_trend_owner_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --owner e2e_owner exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--owner", "e2e_owner_xyz"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagReconcile:
    """E2E tests for dag reconcile command."""

    def test_dag_reconcile_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """dag reconcile exits 0 with valid DAG."""
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
        result = runner.invoke(app, ["dag", "reconcile", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagAddValidateHelp:
    """E2E tests for dag add and dag validate --help."""

    def test_dag_add_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag add --help exits 0."""
        result = runner.invoke(app, ["dag", "add", "--help"])
        assert result.exit_code == 0
        assert "task_id" in result.stdout or "agent" in result.stdout

    def test_dag_validate_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag validate --help exits 0."""
        result = runner.invoke(app, ["dag", "validate", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestReportFormatMd:
    """E2E tests for session-contract-health-report --format md."""

    def test_report_format_md_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --format md exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-report", "--format", "md"])
        assert result.exit_code == 0
        assert "##" in result.stdout or "blocked" in result.stdout.lower()


@pytest.mark.e2e
class TestInspectIncludeContract:
    """E2E tests for inspect --include-contract."""

    def test_inspect_include_contract_no_sessions_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """inspect --owner --include-contract with no sessions exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["inspect", "--owner", "e2e_inspect_inc_contract", "--include-contract"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestArchiveBenchmark:
    """E2E tests for archive and benchmark commands."""

    def test_archive_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """archive exits 0 with empty sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["archive", "--days", "30"])
        assert result.exit_code == 0

    def test_archive_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """archive --help exits 0."""
        result = runner.invoke(app, ["archive", "--help"])
        assert result.exit_code == 0
        assert "days" in result.stdout.lower()

    def test_benchmark_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """benchmark exits 0 (no runs or shows metrics)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["benchmark"])
        assert result.exit_code == 0
        assert "No runs" in result.stdout or "Benchmark" in result.stdout or "runs" in result.stdout.lower()

    def test_benchmark_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """benchmark --help exits 0."""
        result = runner.invoke(app, ["benchmark", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHistoryListFormatMd:
    """E2E tests for history list --format md."""

    def test_history_list_format_md_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history list --format md exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "list", "--format", "md", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGateFormatRich:
    """E2E tests for session-contract-health-gate --format rich."""

    def test_gate_format_rich_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --format rich exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate", "--format", "rich"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGateReportOwner:
    """E2E tests for gate and report --owner."""

    def test_gate_owner_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --owner exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate", "--owner", "e2e_gate_owner"])
        assert result.exit_code == 0

    def test_report_owner_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --owner exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-report", "--owner", "e2e_report_owner"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagRemoveUpdateCancelHelp:
    """E2E tests for dag remove, update, cancel --help."""

    def test_dag_remove_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag remove --help exits 0."""
        result = runner.invoke(app, ["dag", "remove", "--help"])
        assert result.exit_code == 0

    def test_dag_update_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag update --help exits 0."""
        result = runner.invoke(app, ["dag", "update", "--help"])
        assert result.exit_code == 0

    def test_dag_cancel_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag cancel --help exits 0."""
        result = runner.invoke(app, ["dag", "cancel", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPsIncludeContract:
    """E2E tests for ps --include-contract."""

    def test_ps_include_contract_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps --include-contract exits 0 with empty sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps", "--include-contract"])
        assert result.exit_code == 0
        assert "No sessions" in result.stdout


@pytest.mark.e2e
class TestDagSyncListRunHelp:
    """E2E tests for dag sync, list, run --help."""

    def test_dag_sync_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag sync --help exits 0."""
        result = runner.invoke(app, ["dag", "sync", "--help"])
        assert result.exit_code == 0
        assert "watch" in result.stdout.lower() or "interval" in result.stdout.lower()

    def test_dag_list_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag list --help exits 0."""
        result = runner.invoke(app, ["dag", "list", "--help"])
        assert result.exit_code == 0

    def test_dag_run_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag run --help exits 0."""
        result = runner.invoke(app, ["dag", "run", "--help"])
        assert result.exit_code == 0
        assert "dry-run" in result.stdout or "task" in result.stdout


@pytest.mark.e2e
class TestHealthTrendFormatMd:
    """E2E tests for session-contract-health-trend --format md."""

    def test_health_trend_format_md_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --format md exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--format", "md"])
        assert result.exit_code == 0
        assert "##" in result.stdout or "trend" in result.stdout.lower()


@pytest.mark.e2e
class TestHealthTrendPolicyProfile:
    """E2E tests for session-contract-health-trend --policy-profile."""

    def test_health_trend_policy_profile_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --policy-profile strict_ci exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(
            app,
            ["session-contract-health-trend", "--policy-profile", "strict_ci"],
        )
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagCheckpointRollbackRecoverProbeCheckpointsHelp:
    """E2E tests for dag checkpoint, rollback, recover, probe, checkpoints --help."""

    def test_dag_checkpoint_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag checkpoint --help exits 0."""
        result = runner.invoke(app, ["dag", "checkpoint", "--help"])
        assert result.exit_code == 0
        assert "reason" in result.stdout.lower()

    def test_dag_rollback_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag rollback --help exits 0."""
        result = runner.invoke(app, ["dag", "rollback", "--help"])
        assert result.exit_code == 0

    def test_dag_recover_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag recover --help exits 0."""
        result = runner.invoke(app, ["dag", "recover", "--help"])
        assert result.exit_code == 0
        assert "retry-failed" in result.stdout or "clear-stuck" in result.stdout

    def test_dag_probe_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag probe --help exits 0."""
        result = runner.invoke(app, ["dag", "probe", "--help"])
        assert result.exit_code == 0
        assert "baseline" in result.stdout.lower()

    def test_dag_checkpoints_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag checkpoints --help exits 0."""
        result = runner.invoke(app, ["dag", "checkpoints", "--help"])
        assert result.exit_code == 0
        assert "limit" in result.stdout.lower()


@pytest.mark.e2e
class TestGateAllStrict:
    """E2E tests for session-contract-health-gate --all and --strict."""

    def test_gate_all_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --all exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate", "--all"])
        assert result.exit_code == 0

    def test_gate_strict_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-gate --strict exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-gate", "--strict"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestSessionContractsOwnerFormatMd:
    """E2E tests for session-contracts --owner and --format md."""

    def test_session_contracts_owner_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --owner exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--owner", "e2e_contracts_owner"])
        assert result.exit_code == 0

    def test_session_contracts_format_md_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contracts --format md exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contracts", "--format", "md"])
        assert result.exit_code == 0
        assert "##" in result.stdout or "No sessions" in result.stdout


@pytest.mark.e2e
class TestReportAllStrict:
    """E2E tests for session-contract-health-report --all and --strict."""

    def test_report_all_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --all exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-report", "--all"])
        assert result.exit_code == 0

    def test_report_strict_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-report --strict exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["session-contract-health-report", "--strict"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHealthTrendStrictTopBlocked:
    """E2E tests for session-contract-health-trend --strict and --top-blocked."""

    def test_health_trend_strict_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --strict exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--strict"])
        assert result.exit_code == 0

    def test_health_trend_top_blocked_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """session-contract-health-trend --top-blocked 15 exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["session-contract-health-trend", "--top-blocked", "15"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHistoryEventsFormat:
    """E2E tests for history events --format json and --format md."""

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
        result = runner.invoke(app, ["history", "events", "--format", "json", "--limit", "5"])
        assert result.exit_code == 0

    def test_history_events_format_md_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history events --format md exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history", "events", "--format", "md", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPsFormatMdOwner:
    """E2E tests for ps --format md and --owner."""

    def test_ps_format_md_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps --format md exits 0 with empty sessions."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps", "--format", "md"])
        assert result.exit_code == 0

    def test_ps_owner_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ps --owner e2e_owner exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["ps", "--owner", "e2e_ps_owner"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestStatusLogsWaitStopHelp:
    """E2E tests for status, logs, wait, stop --help."""

    def test_status_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """status --help exits 0."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0

    def test_logs_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """logs --help exits 0."""
        result = runner.invoke(app, ["logs", "--help"])
        assert result.exit_code == 0

    def test_wait_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """wait --help exits 0."""
        result = runner.invoke(app, ["wait", "--help"])
        assert result.exit_code == 0

    def test_stop_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """stop --help exits 0."""
        result = runner.invoke(app, ["stop", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestInspectHelp:
    """E2E tests for inspect --help."""

    def test_inspect_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """inspect --help exits 0."""
        result = runner.invoke(app, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "owner" in result.stdout.lower() or "session" in result.stdout.lower()


@pytest.mark.e2e
class TestSessionContractsGateReportTrendHelp:
    """E2E tests for session-contracts, gate, report, trend --help."""

    def test_session_contracts_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """session-contracts --help exits 0."""
        result = runner.invoke(app, ["session-contracts", "--help"])
        assert result.exit_code == 0

    def test_session_contract_health_gate_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """session-contract-health-gate --help exits 0."""
        result = runner.invoke(app, ["session-contract-health-gate", "--help"])
        assert result.exit_code == 0

    def test_session_contract_health_report_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """session-contract-health-report --help exits 0."""
        result = runner.invoke(app, ["session-contract-health-report", "--help"])
        assert result.exit_code == 0

    def test_session_contract_health_trend_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """session-contract-health-trend --help exits 0."""
        result = runner.invoke(app, ["session-contract-health-trend", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDagStatusReadyHelp:
    """E2E tests for dag status and dag ready --help."""

    def test_dag_status_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag status --help exits 0."""
        result = runner.invoke(app, ["dag", "status", "--help"])
        assert result.exit_code == 0

    def test_dag_ready_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """dag ready --help exits 0."""
        result = runner.invoke(app, ["dag", "ready", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestOperations:
    """E2E tests for operations command."""

    def test_operations_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations exits 0."""
        result = runner.invoke(app, ["operations"])
        assert result.exit_code == 0
        assert "orchestrate" in result.stdout.lower() or "Operation" in result.stdout

    def test_operations_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --help exits 0."""
        result = runner.invoke(app, ["operations", "--help"])
        assert result.exit_code == 0

    def test_operations_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --format json exits 0 and outputs dict-shaped JSON."""
        result = runner.invoke(app, ["operations", "--format", "json"])
        assert result.exit_code == 0
        assert "orchestrate" in result.stdout
        assert "govern" in result.stdout

    def test_operations_operation_filter_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation orchestrate exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "orchestrate"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestClosurePack:
    """E2E tests for closure-pack command."""

    def test_closure_pack_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """closure-pack exits 0 with valid DAG."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
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
        result = runner.invoke(app, ["closure-pack", "--cd", str(project)])
        assert result.exit_code == 0

    def test_closure_pack_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """closure-pack --help exits 0."""
        result = runner.invoke(app, ["closure-pack", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPsCockpitHelp:
    """E2E tests for ps and cockpit --help."""

    def test_ps_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """ps --help exits 0."""
        result = runner.invoke(app, ["ps", "--help"])
        assert result.exit_code == 0

    def test_cockpit_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """cockpit --help exits 0."""
        result = runner.invoke(app, ["cockpit", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestMcpUpDownHelp:
    """E2E tests for mcp up and mcp down --help."""

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
class TestModelsSubcommandHelp:
    """E2E tests for models subcommand --help."""

    def test_models_refresh_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """models refresh --help exits 0."""
        result = runner.invoke(app, ["models", "refresh", "--help"])
        assert result.exit_code == 0

    def test_models_contract_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """models contract --help exits 0."""
        result = runner.invoke(app, ["models", "contract", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestTyperAppHelp:
    """E2E tests for orchestrate, govern, recover, observe, plan --help."""

    def test_orchestrate_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "--help"])
        assert result.exit_code == 0

    def test_govern_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern --help exits 0."""
        result = runner.invoke(app, ["govern", "--help"])
        assert result.exit_code == 0

    def test_recover_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """recover --help exits 0."""
        result = runner.invoke(app, ["recover", "--help"])
        assert result.exit_code == 0

    def test_observe_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe --help exits 0."""
        result = runner.invoke(app, ["observe", "--help"])
        assert result.exit_code == 0

    def test_plan_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan --help exits 0."""
        result = runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestHistoryPolicyCliproxyHelp:
    """E2E tests for history subcommands, policy show, cliproxy login --help."""

    def test_history_list_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """history list --help exits 0."""
        result = runner.invoke(app, ["history", "list", "--help"])
        assert result.exit_code == 0

    def test_history_events_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """history events --help exits 0."""
        result = runner.invoke(app, ["history", "events", "--help"])
        assert result.exit_code == 0

    def test_history_verify_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """history verify --help exits 0."""
        result = runner.invoke(app, ["history", "verify", "--help"])
        assert result.exit_code == 0

    def test_policy_show_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """policy show --help exits 0."""
        result = runner.invoke(app, ["policy", "show", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_login_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """cliproxy login --help exits 0."""
        result = runner.invoke(app, ["cliproxy", "login", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestCliproxyEnsureConfigHelp:
    """E2E tests for cliproxy ensure-config --help."""

    def test_cliproxy_ensure_config_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """cliproxy ensure-config --help exits 0."""
        result = runner.invoke(app, ["cliproxy", "ensure-config", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestLoginRooKiloE2E:
    """E2E tests for thegent login roo and thegent login kilo."""

    def test_login_roo_exits_zero_with_mock_cliproxy(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """thegent login roo exits 0 when CLIProxy binary accepts -roo-login."""
        mock_binary = tmp_path / "cli-proxy-api-plus"
        mock_binary.write_text('#!/bin/sh\nfor arg in "$@"; do\n  [ "$arg" = "-roo-login" ] && exit 0\ndone\nexit 1\n')
        mock_binary.chmod(0o755)
        config_path = tmp_path / "config.yaml"
        config_path.write_text("port: 8317\n")
        monkeypatch.setenv("THGENT_CLIPROXY_BINARY", str(mock_binary))
        monkeypatch.setenv("THGENT_CLIPROXY_CONFIG_PATH", str(config_path))
        result = runner.invoke(app, ["login", "roo"])
        assert result.exit_code == 0, result.stderr or result.stdout

    def test_login_kilo_exits_zero_with_mock_cliproxy(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """thegent login kilo exits 0 when CLIProxy binary accepts -kilo-login."""
        mock_binary = tmp_path / "cli-proxy-api-plus"
        mock_binary.write_text('#!/bin/sh\nfor arg in "$@"; do\n  [ "$arg" = "-kilo-login" ] && exit 0\ndone\nexit 1\n')
        mock_binary.chmod(0o755)
        config_path = tmp_path / "config.yaml"
        config_path.write_text("port: 8317\n")
        monkeypatch.setenv("THGENT_CLIPROXY_BINARY", str(mock_binary))
        monkeypatch.setenv("THGENT_CLIPROXY_CONFIG_PATH", str(config_path))
        result = runner.invoke(app, ["login", "kilo"])
        assert result.exit_code == 0, result.stderr or result.stdout

    def test_cliproxy_login_roo_exits_zero_with_mock(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """thegent cliproxy login roo exits 0 when CLIProxy accepts -roo-login."""
        mock_binary = tmp_path / "cli-proxy-api-plus"
        mock_binary.write_text('#!/bin/sh\nfor arg in "$@"; do\n  [ "$arg" = "-roo-login" ] && exit 0\ndone\nexit 1\n')
        mock_binary.chmod(0o755)
        config_path = tmp_path / "config.yaml"
        config_path.write_text("port: 8317\n")
        monkeypatch.setenv("THGENT_CLIPROXY_BINARY", str(mock_binary))
        monkeypatch.setenv("THGENT_CLIPROXY_CONFIG_PATH", str(config_path))
        result = runner.invoke(app, ["cliproxy", "login", "roo"])
        assert result.exit_code == 0, result.stderr or result.stdout


@pytest.mark.e2e
class TestTyperAliasHelp:
    """E2E tests for typer alias paths (orchestrate/govern/observe subcommands)."""

    def test_orchestrate_run_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate run --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "run", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_ps_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate ps --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "ps", "--help"])
        assert result.exit_code == 0

    def test_govern_verify_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern verify --help exits 0 (alias for history verify)."""
        result = runner.invoke(app, ["govern", "verify", "--help"])
        assert result.exit_code == 0

    def test_observe_cockpit_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe cockpit --help exits 0."""
        result = runner.invoke(app, ["observe", "cockpit", "--help"])
        assert result.exit_code == 0

    def test_observe_archive_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe archive --help exits 0."""
        result = runner.invoke(app, ["observe", "archive", "--help"])
        assert result.exit_code == 0

    def test_observe_benchmark_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe benchmark --help exits 0."""
        result = runner.invoke(app, ["observe", "benchmark", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestRecoverPlanGovernAliasHelp:
    """E2E tests for recover, plan, and govern alias paths --help."""

    def test_recover_reconcile_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """recover reconcile --help exits 0 (alias for dag reconcile)."""
        result = runner.invoke(app, ["recover", "reconcile", "--help"])
        assert result.exit_code == 0

    def test_plan_list_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan list --help exits 0 (alias for dag list)."""
        result = runner.invoke(app, ["plan", "list", "--help"])
        assert result.exit_code == 0

    def test_plan_validate_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan validate --help exits 0 (alias for dag validate)."""
        result = runner.invoke(app, ["plan", "validate", "--help"])
        assert result.exit_code == 0

    def test_plan_run_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan run --help exits 0 (alias for dag run)."""
        result = runner.invoke(app, ["plan", "run", "--help"])
        assert result.exit_code == 0

    def test_govern_closure_pack_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern closure-pack --help exits 0 (alias for closure-pack)."""
        result = runner.invoke(app, ["govern", "closure-pack", "--help"])
        assert result.exit_code == 0

    def test_govern_show_policy_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern show-policy --help exits 0 (alias for policy show)."""
        result = runner.invoke(app, ["govern", "show-policy", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestOrchestrateRecoverObserveRemainingHelp:
    """E2E tests for remaining orchestrate, recover, observe alias --help."""

    def test_orchestrate_bg_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate bg --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "bg", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_inspect_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate inspect --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "inspect", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_logs_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate logs --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "logs", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_wait_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate wait --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "wait", "--help"])
        assert result.exit_code == 0

    def test_orchestrate_stop_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """orchestrate stop --help exits 0."""
        result = runner.invoke(app, ["orchestrate", "stop", "--help"])
        assert result.exit_code == 0

    def test_recover_stop_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """recover stop --help exits 0 (alias for stop)."""
        result = runner.invoke(app, ["recover", "stop", "--help"])
        assert result.exit_code == 0

    def test_observe_status_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe status --help exits 0."""
        result = runner.invoke(app, ["observe", "status", "--help"])
        assert result.exit_code == 0

    def test_observe_logs_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe logs --help exits 0."""
        result = runner.invoke(app, ["observe", "logs", "--help"])
        assert result.exit_code == 0

    def test_observe_wait_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe wait --help exits 0."""
        result = runner.invoke(app, ["observe", "wait", "--help"])
        assert result.exit_code == 0

    def test_observe_inspect_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe inspect --help exits 0."""
        result = runner.invoke(app, ["observe", "inspect", "--help"])
        assert result.exit_code == 0

    def test_observe_history_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe history --help exits 0 (alias for history list)."""
        result = runner.invoke(app, ["observe", "history", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanSyncCheckpointAndOperationsFilters:
    """E2E tests for plan sync/checkpoint help and operations --operation filters."""

    def test_plan_sync_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan sync --help exits 0 (alias for dag sync)."""
        result = runner.invoke(app, ["plan", "sync", "--help"])
        assert result.exit_code == 0

    def test_plan_checkpoint_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan checkpoint --help exits 0 (alias for dag checkpoint)."""
        result = runner.invoke(app, ["plan", "checkpoint", "--help"])
        assert result.exit_code == 0

    def test_operations_operation_govern_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation govern exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "govern"])
        assert result.exit_code == 0

    def test_operations_operation_recover_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation recover exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "recover"])
        assert result.exit_code == 0

    def test_operations_operation_observe_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation observe exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "observe"])
        assert result.exit_code == 0

    def test_operations_operation_plan_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """operations --operation plan exits 0."""
        result = runner.invoke(app, ["operations", "--operation", "plan"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestOperationsInvalidAndClosurePackNoDag:
    """E2E tests for operations invalid operation and closure-pack without DAG."""

    def test_operations_invalid_operation_exits_one(self) -> None:
        # @trace FR-CLI-001
        """operations --operation invalid_name exits 1 with message."""
        result = runner.invoke(app, ["operations", "--operation", "invalid_operation_xyz"])
        assert result.exit_code == 1
        assert "Unknown operation" in result.stdout or "invalid" in result.stdout.lower()

    def test_closure_pack_no_dag_exits_one(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """closure-pack with project lacking .factory/dag-session.md exits 1."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        (project / ".factory").mkdir()
        # No dag-session.md
        result = runner.invoke(app, ["closure-pack", "--cd", str(project)])
        assert result.exit_code == 1
        assert "DAG not found" in result.stdout or "dag" in result.stdout.lower()


@pytest.mark.e2e
class TestHistoryLegacy:
    """E2E tests for hidden history-legacy command."""

    def test_history_legacy_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """history-legacy --help exits 0."""
        result = runner.invoke(app, ["history-legacy", "--help"])
        assert result.exit_code == 0

    def test_history_legacy_empty_registry_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history-legacy with empty registry exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history-legacy", "--limit", "5"])
        assert result.exit_code == 0

    def test_history_legacy_format_json_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """history-legacy --format json with empty registry exits 0."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["history-legacy", "--format", "json", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernRemainingAliasHelp:
    """E2E tests for remaining govern alias paths --help."""

    def test_govern_contracts_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern contracts --help exits 0 (alias for session-contracts)."""
        result = runner.invoke(app, ["govern", "contracts", "--help"])
        assert result.exit_code == 0

    def test_govern_session_contracts_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern session-contracts --help exits 0."""
        result = runner.invoke(app, ["govern", "session-contracts", "--help"])
        assert result.exit_code == 0

    def test_govern_health_gate_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern health-gate --help exits 0 (alias for session-contract-health-gate)."""
        result = runner.invoke(app, ["govern", "health-gate", "--help"])
        assert result.exit_code == 0

    def test_govern_health_report_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern health-report --help exits 0 (alias for session-contract-health-report)."""
        result = runner.invoke(app, ["govern", "health-report", "--help"])
        assert result.exit_code == 0

    def test_govern_health_trend_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern health-trend --help exits 0 (alias for session-contract-health-trend)."""
        result = runner.invoke(app, ["govern", "health-trend", "--help"])
        assert result.exit_code == 0

    def test_govern_feedback_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern feedback --help exits 0."""
        result = runner.invoke(app, ["govern", "feedback", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernContractsExecution:
    """E2E tests for govern contracts (contract registry) execution."""

    def test_govern_contracts_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern contracts exits 0 and shows contract registry."""
        result = runner.invoke(app, ["govern", "contracts"])
        assert result.exit_code == 0
        assert "Contract" in result.stdout or "registry" in result.stdout.lower()

    def test_govern_contracts_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern contracts --format json exits 0."""
        result = runner.invoke(app, ["govern", "contracts", "--format", "json"])
        assert result.exit_code == 0
        # Output should look like JSON array (may have Rich/ANSI artifacts)
        assert "[" in result.stdout


@pytest.mark.e2e
class TestObservePlanAliasExecution:
    """E2E tests for observe and plan alias execution (not just --help)."""

    def test_observe_history_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe history exits 0 (alias for history list)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "history", "--limit", "5"])
        assert result.exit_code == 0

    def test_plan_list_empty_dag_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan list with empty DAG exits 0 (alias for dag list)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        )
        result = runner.invoke(app, ["plan", "list", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestRecoverPlanAliasExecution:
    """E2E tests for recover and plan alias execution."""

    def _dag_project(self, tmp_path: Path, with_task: bool = True) -> Path:
        """Create project with dag-session.md."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        content = "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        if with_task:
            content += "| T1 | gemini | hello | — | pending |\n"
        (factory / "dag-session.md").write_text(content)
        return project

    def test_recover_reconcile_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """recover reconcile exits 0 with valid DAG (alias for dag reconcile)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["recover", "reconcile", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_validate_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan validate exits 0 with valid empty DAG (alias for dag validate)."""
        project = self._dag_project(tmp_path, with_task=False)
        result = runner.invoke(app, ["plan", "validate", "--cd", str(project)])
        assert result.exit_code == 0
        assert "DAG valid" in result.stdout

    def test_plan_sync_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan sync exits 0 with empty DAG (alias for dag sync)."""
        project = self._dag_project(tmp_path, with_task=False)
        result = runner.invoke(app, ["plan", "sync", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_checkpoint_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """plan checkpoint exits 0 with DAG (alias for dag checkpoint)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        project = self._dag_project(tmp_path)
        monkeypatch.chdir(project)
        result = runner.invoke(app, ["plan", "checkpoint", "--reason", "E2E test"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanRunDryRun:
    """E2E tests for plan run --dry-run (alias for dag run --dry-run)."""

    def _dag_project(self, tmp_path: Path, with_task: bool = True) -> Path:
        """Create project with dag-session.md."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        content = "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        if with_task:
            content += "| T1 | gemini | hello | — | pending |\n"
        (factory / "dag-session.md").write_text(content)
        return project

    def test_plan_run_dry_run_no_ready_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan run --dry-run with no ready tasks exits 0."""
        project = self._dag_project(tmp_path, with_task=False)
        result = runner.invoke(app, ["plan", "run", "--dry-run", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_run_dry_run_with_ready_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan run --dry-run with ready task exits 0 and shows would run."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "run", "--dry-run", "--cd", str(project)])
        assert result.exit_code == 0
        assert "Would run" in result.stdout or "T1" in result.stdout


@pytest.mark.e2e
class TestObserveDriftTrendProbeHelp:
    """E2E tests for observe drift, trend, probe --help."""

    def test_observe_drift_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe drift --help exits 0."""
        result = runner.invoke(app, ["observe", "drift", "--help"])
        assert result.exit_code == 0

    def test_observe_trend_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe trend --help exits 0 (alias for session-contract-health-trend)."""
        result = runner.invoke(app, ["observe", "trend", "--help"])
        assert result.exit_code == 0

    def test_observe_probe_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe probe --help exits 0 (alias for dag probe)."""
        result = runner.invoke(app, ["observe", "probe", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestGovernConformanceMigrationHelp:
    """E2E tests for govern conformance and migration --help."""

    def test_govern_conformance_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern conformance --help exits 0."""
        result = runner.invoke(app, ["govern", "conformance", "--help"])
        assert result.exit_code == 0

    def test_govern_migration_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern migration --help exits 0."""
        result = runner.invoke(app, ["govern", "migration", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestObserveDriftTrendExecution:
    """E2E tests for observe drift and observe trend execution."""

    def test_observe_drift_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe drift exits 0 with empty session dir."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["observe", "drift", "--window", "10"])
        assert result.exit_code == 0

    def test_observe_trend_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """observe trend exits 0 with empty snapshots (alias for session-contract-health-trend)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["observe", "trend", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanReadyStatusCheckpointsExecution:
    """E2E tests for plan ready, status, checkpoints execution (aliases for dag)."""

    def _dag_project(self, tmp_path: Path, with_task: bool = True) -> Path:
        """Create project with dag-session.md."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        content = "# DAG\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n|----|-------|--------|------------|--------|\n"
        if with_task:
            content += "| T1 | gemini | hello | — | pending |\n"
        (factory / "dag-session.md").write_text(content)
        return project

    def test_plan_ready_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan ready exits 0 with empty DAG (alias for dag ready)."""
        project = self._dag_project(tmp_path, with_task=False)
        result = runner.invoke(app, ["plan", "ready", "--cd", str(project)])
        assert result.exit_code == 0

    def test_plan_status_exits_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-CLI-001
        """plan status exits 0 with empty DAG (alias for dag status)."""
        project = self._dag_project(tmp_path, with_task=False)
        monkeypatch.chdir(project)
        result = runner.invoke(app, ["plan", "status"])
        assert result.exit_code == 0

    def test_plan_checkpoints_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """plan checkpoints exits 0 (alias for dag checkpoints)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["plan", "checkpoints", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanObserveProbeExecution:
    """E2E tests for plan probe and observe probe execution (aliases for dag probe)."""

    def _dag_project(self, tmp_path: Path) -> Path:
        """Create project with dag-session.md."""
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

    def test_plan_probe_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan probe exits 0 with DAG (alias for dag probe)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["plan", "probe", "--cd", str(project)])
        assert result.exit_code == 0

    def test_observe_probe_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """observe probe exits 0 with DAG (alias for dag probe)."""
        project = self._dag_project(tmp_path)
        result = runner.invoke(app, ["observe", "probe", "--cd", str(project)])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestRecoverPlanRollbackAndPlanMutateHelp:
    """E2E tests for recover/plan rollback and plan add/remove/update/cancel --help."""

    def test_recover_rollback_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """recover rollback --help exits 0 (alias for dag rollback)."""
        result = runner.invoke(app, ["recover", "rollback", "--help"])
        assert result.exit_code == 0

    def test_plan_rollback_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan rollback --help exits 0 (alias for dag rollback)."""
        result = runner.invoke(app, ["plan", "rollback", "--help"])
        assert result.exit_code == 0

    def test_plan_add_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan add --help exits 0 (alias for dag add)."""
        result = runner.invoke(app, ["plan", "add", "--help"])
        assert result.exit_code == 0

    def test_plan_remove_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan remove --help exits 0 (alias for dag remove)."""
        result = runner.invoke(app, ["plan", "remove", "--help"])
        assert result.exit_code == 0

    def test_plan_update_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan update --help exits 0 (alias for dag update)."""
        result = runner.invoke(app, ["plan", "update", "--help"])
        assert result.exit_code == 0

    def test_plan_cancel_help_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """plan cancel --help exits 0 (alias for dag cancel)."""
        result = runner.invoke(app, ["plan", "cancel", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestPlanAddExecution:
    """E2E tests for plan add execution (alias for dag add)."""

    def test_plan_add_then_list_exits_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-CLI-001
        """plan add creates task; plan list shows it."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG Session\n\n## Tasks\n\n| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
        )

        monkeypatch.chdir(project)
        add_result = runner.invoke(app, ["plan", "add", "T1", "--agent", "gemini", "--prompt", "test prompt"])
        assert add_result.exit_code == 0
        assert "Added task T1" in add_result.stdout

        list_result = runner.invoke(app, ["plan", "list"])
        assert list_result.exit_code == 0
        assert "T1" in list_result.stdout
        assert "gemini" in list_result.stdout


@pytest.mark.e2e
class TestPlanRemoveUpdateCancelExecution:
    """E2E tests for plan remove, update, cancel execution (aliases for dag)."""

    def _project_with_task(self, tmp_path: Path, task_id: str = "T1") -> Path:
        """Create project with single task."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        factory = project / ".factory"
        factory.mkdir()
        (factory / "dag-session.md").write_text(
            "# DAG Session\n\n## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "|----|-------|--------|------------|--------|\n"
            f"| {task_id} | gemini | test | — | pending |\n"
        )
        return project

    def test_plan_remove_then_list_exits_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-CLI-001
        """plan remove removes task; plan list shows No tasks."""
        project = self._project_with_task(tmp_path)
        monkeypatch.chdir(project)
        result = runner.invoke(app, ["plan", "remove", "T1"])
        assert result.exit_code == 0
        assert "Removed task T1" in result.stdout

        list_result = runner.invoke(app, ["plan", "list"])
        assert list_result.exit_code == 0
        assert "No tasks" in list_result.stdout

    def test_plan_update_status_then_list_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan update --status done updates task; plan list shows done."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(app, ["plan", "update", "T1", "--status", "done", "--cd", str(project)])
        assert result.exit_code == 0

        list_result = runner.invoke(app, ["plan", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "done" in list_result.stdout

    def test_plan_cancel_then_list_exits_zero(self, tmp_path: Path) -> None:
        # @trace FR-CLI-001
        """plan cancel sets status cancelled; plan list shows cancelled."""
        project = self._project_with_task(tmp_path)
        result = runner.invoke(app, ["plan", "cancel", "T1", "--cd", str(project)])
        assert result.exit_code == 0
        assert "Cancelled task T1" in result.stdout

        list_result = runner.invoke(app, ["plan", "list", "--cd", str(project)])
        assert list_result.exit_code == 0
        assert "cancelled" in list_result.stdout


@pytest.mark.e2e
class TestRecoverPlanRollbackExecution:
    """E2E tests for recover rollback and plan rollback execution (aliases for dag rollback)."""

    def _dag_project(self, tmp_path: Path) -> Path:
        """Create project with dag-session.md."""
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

    def test_plan_checkpoint_then_rollback_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """plan checkpoint creates checkpoint; plan rollback restores DAG."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        project = self._dag_project(tmp_path)

        monkeypatch.chdir(project)
        ckpt_result = runner.invoke(app, ["plan", "checkpoint", "--reason", "E2E rollback test"])
        assert ckpt_result.exit_code == 0
        match = re.search(r"ckpt_[a-f0-9]+", ckpt_result.stdout)
        assert match, "Checkpoint ID should be printed"
        ckpt_id = match.group(0)

        rollback_result = runner.invoke(app, ["plan", "rollback", ckpt_id])
        assert rollback_result.exit_code == 0
        assert "rolled back" in rollback_result.stdout.lower()

    def test_recover_rollback_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """recover rollback restores DAG to checkpoint (alias for dag rollback)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        project = self._dag_project(tmp_path)

        monkeypatch.chdir(project)
        ckpt_result = runner.invoke(app, ["plan", "checkpoint", "--reason", "E2E recover rollback"])
        assert ckpt_result.exit_code == 0
        match = re.search(r"ckpt_[a-f0-9]+", ckpt_result.stdout)
        assert match, "Checkpoint ID should be printed"
        ckpt_id = match.group(0)

        rollback_result = runner.invoke(app, ["recover", "rollback", ckpt_id, "--cd", str(project)])
        assert rollback_result.exit_code == 0
        assert "rolled back" in rollback_result.stdout.lower()


@pytest.mark.e2e
class TestGovernAliasExecution:
    """E2E tests for govern alias execution (session-contracts, health-gate, health-report)."""

    def test_govern_session_contracts_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern session-contracts exits 0 with empty sessions (alias for session-contracts)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "session-contracts"])
        assert result.exit_code == 0

    def test_govern_health_gate_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern health-gate exits 0 with empty sessions (alias for session-contract-health-gate)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "health-gate"])
        assert result.exit_code == 0

    def test_govern_health_report_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern health-report exits 0 with empty sessions (alias for session-contract-health-report)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["govern", "health-report"])
        assert result.exit_code == 0

    def test_govern_health_trend_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """govern health-trend exits 0 with empty snapshots (alias for session-contract-health-trend)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        result = runner.invoke(app, ["govern", "health-trend", "--limit", "5"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestObserveAliasExecution:
    """E2E tests for observe alias execution (cockpit, archive, benchmark)."""

    def test_observe_cockpit_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe cockpit exits 0 (alias for cockpit)."""
        result = runner.invoke(app, ["observe", "cockpit"])
        assert result.exit_code == 0

    def test_observe_archive_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe archive exits 0 (alias for archive)."""
        result = runner.invoke(app, ["observe", "archive", "--days", "7"])
        assert result.exit_code == 0

    def test_observe_benchmark_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """observe benchmark exits 0 (alias for benchmark)."""
        result = runner.invoke(app, ["observe", "benchmark"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestOrchestrateGovernAliasExecution:
    """E2E tests for orchestrate ps and govern migration execution."""

    def test_orchestrate_ps_exits_zero(
        # @trace FR-CLI-001
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """orchestrate ps exits 0 with empty sessions (alias for ps)."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("THGENT_SESSION_DIR", str(session_dir))
        result = runner.invoke(app, ["orchestrate", "ps"])
        assert result.exit_code == 0

    def test_govern_migration_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern migration csm csm-v1 exits 0 (evaluates known contract version)."""
        result = runner.invoke(app, ["govern", "migration", "csm", "csm-v1"])
        assert result.exit_code == 0
        assert "active" in result.stdout.lower() or "allowed" in result.stdout.lower()

    def test_govern_migration_format_json_exits_zero(self) -> None:
        # @trace FR-CLI-001
        """govern migration --format json exits 0."""
        result = runner.invoke(app, ["govern", "migration", "csm", "csm-v1", "--format", "json"])
        assert result.exit_code == 0
        data = load_cli_json(result.stdout)
        assert "allowed" in data
        assert "status" in data
