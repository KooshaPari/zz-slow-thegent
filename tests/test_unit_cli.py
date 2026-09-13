"""Unit tests for CLI resolution logic."""

import getpass
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest
import typer
from typer.testing import CliRunner

from thegent.cli.commands import impl as cli_impl
from thegent.cli.commands.cli import logs_cmd, stop_cmd
from thegent.cli.commands.impl import (
    _compose_owner_tag,
    _default_owner_tag,
    _resolve_cwd,
    _resolve_droids_dir,
)
from thegent.config import ThegentSettings
from thegent.main import app

runner = CliRunner()


@pytest.mark.unit
class TestInjectTimeConstraint:
    """Tests for cli_impl._inject_time_constraint."""

    def test_appends_constraint(self) -> None:
        # @trace FR-CLI-001
        """Constraint is appended to prompt."""
        result = cli_impl._inject_time_constraint("List dirs", 60)
        assert "List dirs" in result
        assert "TIME CONSTRAINT" in result
        assert "60" in result
        assert "tool calls" in result

    def test_computes_tool_calls_from_timeout(self) -> None:
        # @trace FR-CLI-001
        """N tool calls ≈ timeout / 2.3."""
        result = cli_impl._inject_time_constraint("x", 23)
        # 23/2.3 = 10
        assert "10" in result or "9" in result or "11" in result  # allow rounding

    def test_min_one_tool_call(self) -> None:
        # @trace FR-CLI-001
        """At least 1 tool call for very short timeout."""
        result = cli_impl._inject_time_constraint("x", 1)
        assert "1" in result
        assert "TIME CONSTRAINT" in result


@pytest.mark.unit
class TestResolveCwd:
    """Tests for _resolve_cwd."""

    def test_explicit_cd_exists(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Explicit --cd with existing dir returns that path."""
        sub = tmp_path / "sub"
        sub.mkdir()
        assert _resolve_cwd(sub) == sub.resolve()

    def test_explicit_cd_nonexistent_raises(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Explicit --cd with nonexistent dir raises BadParameter."""
        bad = tmp_path / "nonexistent"
        with pytest.raises(typer.BadParameter, match="does not exist"):
            _resolve_cwd(bad)

    def test_explicit_cd_expands_user(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-CLI-002
        """Explicit --cd expands ~."""
        home = Path.home()
        with patch.object(Path, "expanduser", return_value=home):
            with patch.object(Path, "is_dir", return_value=True):
                with patch.object(Path, "resolve", return_value=home):
                    result = _resolve_cwd(Path("~"))
                    assert result is not None

    def test_infer_from_git(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Cwd inferred when .git exists."""
        (tmp_path / ".git").mkdir()
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=tmp_path):
            assert _resolve_cwd(None) == tmp_path

    def test_infer_from_factory(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Cwd inferred when .factory exists."""
        (tmp_path / ".factory").mkdir()
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=tmp_path):
            assert _resolve_cwd(None) == tmp_path

    def test_infer_from_pyproject(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Cwd inferred when pyproject.toml exists."""
        (tmp_path / "pyproject.toml").touch()
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=tmp_path):
            assert _resolve_cwd(None) == tmp_path

    def test_infer_from_parent_factory(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Cwd inferred from parent when parent has .factory."""
        parent = tmp_path / "parent"
        parent.mkdir()
        (parent / ".factory").mkdir()
        child = parent / "child"
        child.mkdir()
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=child):
            assert _resolve_cwd(None) == parent

    def test_ambiguous_returns_none(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """Returns None when no project indicators (ambiguous cwd)."""
        # Use /tmp or similar bare dir - no .git, .factory, pyproject.toml
        bare = tmp_path / "bare"
        bare.mkdir()
        # Ensure no project indicators
        assert not (bare / ".git").exists()
        assert not (bare / ".factory").exists()
        assert not (bare / "pyproject.toml").exists()
        assert not (bare.parent / ".factory").exists()
        with patch("thegent.cli.commands.impl.Path.cwd", return_value=bare):
            result = _resolve_cwd(None)
        assert result is None


@pytest.mark.unit
class TestResolveDroidsDir:
    """Tests for _resolve_droids_dir."""

    def test_project_droids_takes_precedence(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """When cwd has .factory/droids, use that."""
        droids = tmp_path / ".factory" / "droids"
        droids.mkdir(parents=True)
        settings = ThegentSettings()
        result = _resolve_droids_dir(tmp_path, settings)
        assert result == droids.resolve()

    def test_fallback_to_config(self, tmp_path: Path) -> None:
        # @trace FR-CLI-002
        """When cwd has no .factory/droids, use config."""
        settings = ThegentSettings()
        result = _resolve_droids_dir(tmp_path, settings)
        assert result == settings.factory_droids_dir.expanduser().resolve()

    def test_none_cwd_uses_config(self) -> None:
        # @trace FR-CLI-002
        """When cwd is None, use config."""
        settings = ThegentSettings()
        result = _resolve_droids_dir(None, settings)
        assert result == settings.factory_droids_dir.expanduser().resolve()


@pytest.mark.unit
class TestOwnerTag:
    """Tests for owner tag resolution and scoping."""

    def test_owner_tag_prefers_explicit_override(self, tmp_path: Path) -> None:
        # @trace FR-CLI-003
        """Explicit THGENT_OWNER_TAG bypasses composed tags."""
        with patch.dict("os.environ", {"THGENT_OWNER_TAG": "explicit-user:scope"}):
            assert _default_owner_tag(tmp_path) == "explicit-user:scope"

    def test_owner_tag_appends_scope(self, tmp_path: Path) -> None:
        # @trace FR-CLI-003
        """THGENT_OWNER_SCOPE is appended when present."""
        cwd = tmp_path / "repo"
        cwd.mkdir()
        base = f"{getpass.getuser()}:{cwd.name}"
        with patch.dict("os.environ", {"THGENT_OWNER_SCOPE": "agent-group"}):
            assert _default_owner_tag(cwd) == f"{base}:agent-group"

    def test_owner_tag_expands_scope_placeholders(self, tmp_path: Path) -> None:
        # @trace FR-CLI-003
        """Scope supports placeholders for stable per-process tags."""
        cwd = tmp_path / "repo"
        cwd.mkdir()
        scope = "node-{pid}-{cwd}"
        expected = _compose_owner_tag(getpass.getuser(), cwd, scope=scope)
        with patch.dict("os.environ", {"THGENT_OWNER_SCOPE": scope}):
            assert _default_owner_tag(cwd) == expected


@pytest.mark.unit
class TestSessionCommands:
    """Tests for bg/session lifecycle commands."""

    def test_bg_registers_session_metadata(self, tmp_path: Path) -> None:
        # @trace FR-CLI-004
        session_dir = tmp_path / "sessions"

        class _Proc:
            pid = 43210

        with (
            patch("thegent.cli.commands.cli.subprocess.Popen", return_value=_Proc()),
            patch.dict(
                "os.environ",
                {
                    "THGENT_SESSION_DIR": str(session_dir),
                },
            ),
        ):
            # Put options first (Click/Typer parses options-after-positionals as commands)
            result = runner.invoke(
                app,
                [
                    "bg",
                    f"--cd={tmp_path}",
                    "--owner=test-owner",
                    "say hi",
                    "cursor-agent",
                ],
            )

        assert result.exit_code == 0
        files = list((session_dir / "test-owner").glob("*.json"))
        assert len(files) == 1
        meta = json.loads(files[0].read_text(encoding="utf-8"))
        assert meta["agent"] == "cursor-agent"
        assert meta["pid"] == 43210

    def test_run_model_first_invalid_provider_shows_available(self, tmp_path: Path) -> None:
        # @trace FR-CLI-004
        """When -P provider doesn't serve model, error includes 'Available: ...' (Phase 11)."""
        (tmp_path / ".git").mkdir()
        result = runner.invoke(
            app,
            [
                "run",
                "-M",
                "gemini-3-flash",
                "-P",
                "minimax",
                f"--cd={tmp_path}",
                "prompt",
            ],
        )
        assert result.exit_code == 1
        assert "not available via provider 'minimax'" in result.stdout
        assert "Available:" in result.stdout
        assert "gemini" in result.stdout

    def test_status_reads_session(self, tmp_path: Path) -> None:
        # @trace FR-CLI-004
        session_dir = tmp_path / "sessions"
        scoped = session_dir / "ppid_1"
        scoped.mkdir(parents=True)
        sid = "sid-1"
        meta = {
            "session_id": sid,
            "agent": "cursor-agent",
            "owner": "ppid:1",
            "pid": 99999999,
        }
        (scoped / f"{sid}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")
        (scoped / f"{sid}.rc").write_text("0\n", encoding="utf-8")
        with patch.dict("os.environ", {"THGENT_SESSION_DIR": str(session_dir)}):
            result = runner.invoke(app, ["status", sid])
        assert result.exit_code == 0
        assert '"status": "exited:0"' in result.stdout

    def test_stop_wind_down_exits_within_grace(self, tmp_path: Path) -> None:
        # @trace FR-CLI-004
        session_dir = tmp_path / "sessions"
        scoped = session_dir / "owner"
        scoped.mkdir(parents=True)
        sid = "sid-wd-ok"
        meta = {
            "session_id": sid,
            "agent": "cursor-agent",
            "owner": "owner",
            "pid": 12345,
        }
        (scoped / f"{sid}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")

        calls = {"n": 0}

        def fake_running(_pid: int) -> bool:
            calls["n"] += 1
            return calls["n"] == 1

        with patch.dict("os.environ", {"THGENT_SESSION_DIR": str(session_dir)}):
            with patch("thegent.cli.commands.cli._is_pid_running", side_effect=fake_running):
                with patch("thegent.cli.commands.cli.os.killpg") as killpg:
                    stop_cmd(sid, force=False, wind_down=True, grace=1)
                    killpg.assert_called_once()

    def test_stop_wind_down_reports_still_running_after_grace(self, tmp_path: Path) -> None:
        # @trace FR-CLI-004
        session_dir = tmp_path / "sessions"
        scoped = session_dir / "owner"
        scoped.mkdir(parents=True)
        sid = "sid-wd-timeout"
        meta = {
            "session_id": sid,
            "agent": "cursor-agent",
            "owner": "owner",
            "pid": 54321,
        }
        (scoped / f"{sid}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")

        with patch.dict("os.environ", {"THGENT_SESSION_DIR": str(session_dir)}):
            with patch("thegent.cli.commands.cli._is_pid_running", return_value=True):
                with patch("thegent.cli.commands.cli.os.killpg") as killpg:
                    with patch("thegent.cli.commands.cli.time.sleep"):
                        with patch(
                            "thegent.cli.commands.cli.time.time",
                            side_effect=[0.0, 0.3, 0.7, 1.2],
                        ):
                            stop_cmd(sid, force=False, wind_down=True, grace=1)
                            # Wind-down sends SIGTERM then, after the grace
                            # period elapses, escalates to SIGKILL.
                            assert killpg.call_count == 2
                            killpg.assert_any_call(54321, 15)  # SIGTERM
                            killpg.assert_any_call(54321, 9)  # SIGKILL

    def test_logs_follow_times_out_without_pid_completion(self, tmp_path: Path) -> None:
        # @trace FR-CLI-004
        """Follow mode returns timeout exit when process is still running."""
        session_dir = tmp_path / "sessions"
        scoped = session_dir / "owner"
        scoped.mkdir(parents=True)
        sid = "sid-log-timeout"
        meta = {
            "session_id": sid,
            "agent": "cursor-agent",
            "owner": "owner",
            "pid": 55555,
        }
        (scoped / f"{sid}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")
        (scoped / f"{sid}.stdout.log").write_text("ready\n", encoding="utf-8")

        t = {"now": 0.0}

        def _fake_time() -> float:
            t["now"] += 0.25
            return t["now"]

        with patch.dict("os.environ", {"THGENT_SESSION_DIR": str(session_dir)}):
            with patch("thegent.cli.commands.cli._is_pid_running", return_value=True):
                with (
                    patch("thegent.cli.commands.cli.time.time", _fake_time),
                    patch("thegent.cli.commands.cli.time.sleep"),
                ):
                    with pytest.raises(typer.Exit) as exc:
                        logs_cmd(session_id=sid, follow=True, tail=20, timeout=1)
        assert exc.value.exit_code == 124


@pytest.mark.unit
class TestObserveSummaryImpl:
    """Tests for observe summary aggregator behavior."""

    def test_observe_summary_impl_accepts_budget_and_provider_filters(
        # @trace FR-CLI-005
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Summary respects caller-provided budgets and provider filter."""

        class _FakeTelemetry:
            def __init__(self, _session_dir) -> None:
                pass

            def get_fallback_kpis(
                self,
                limit: int = 500,
                structural_budget_pct: float = 5.0,
                semantic_budget_pct: float = 10.0,
                provider: str | None = None,
            ) -> dict:
                assert limit == 123
                assert structural_budget_pct == 7.5
                assert semantic_budget_pct == 12.5
                assert provider == "gemini"
                return {
                    "total": 8,
                    "fallback_rate": 0.25,
                    "success_rate": 0.75,
                    "avg_confidence": 0.91,
                    "structural_drift_pct": 1.5,
                    "semantic_drift_pct": 2.0,
                    "by_provider": {
                        "gemini": {
                            "fallback_rate": 0.25,
                            "success_rate": 0.75,
                            "avg_confidence": 0.91,
                            "total": 8,
                        }
                    },
                }

            def detect_drift(self, window_size: int = 50) -> list[str]:
                assert window_size == 20
                return []

            def get_drift_budget_status(self, structural_budget_pct, semantic_budget_pct, limit=500):
                assert structural_budget_pct == 7.5
                assert semantic_budget_pct == 12.5
                assert limit == 123
                return {
                    "within_budget": True,
                    "structural_rate_pct": 1.5,
                    "semantic_rate_pct": 2.0,
                    "structural_budget_pct": structural_budget_pct,
                    "semantic_budget_pct": semantic_budget_pct,
                }

        class _FakeEscalationQueue:
            def __init__(self, _session_dir) -> None:
                pass

            def list_pending(self, past_sla_only: bool = False, limit: int = 50) -> list[dict]:
                assert limit >= 20
                if past_sla_only:
                    return [
                        {
                            "run_id": "run-1",
                            "owner": "owner-1",
                            "agent": "agent-a",
                            "lane": "standard",
                            "reason": "policy denied",
                            "priority": 2,
                            "sla_minutes": 15,
                            "blocked_at_utc": "2026-01-01T00:00:00+00:00",
                            "escalate_by_utc": "2025-01-01T00:00:00+00:00",
                        }
                    ]
                return [
                    {
                        "run_id": "run-1",
                        "owner": "owner-1",
                        "agent": "agent-a",
                        "lane": "standard",
                        "reason": "policy denied",
                        "priority": 2,
                        "sla_minutes": 15,
                        "blocked_at_utc": "2026-01-01T00:00:00+00:00",
                        "escalate_by_utc": "2025-01-01T00:00:00+00:00",
                        "past_sla": True,
                    },
                    {
                        "run_id": "run-2",
                        "owner": "owner-2",
                        "agent": "agent-b",
                        "lane": "standard",
                        "reason": "timeout",
                        "priority": 1,
                        "sla_minutes": 30,
                        "blocked_at_utc": "2026-01-02T00:00:00+00:00",
                        "escalate_by_utc": "2026-01-02T12:00:00+00:00",
                        "past_sla": False,
                    },
                ]

        monkeypatch.setattr("thegent.contracts.telemetry.ContractTelemetry", _FakeTelemetry)
        monkeypatch.setattr("thegent.execution.EscalationQueue", _FakeEscalationQueue)

        result = cli_impl.observe_summary_impl(
            limit=123,
            drift_window=20,
            structural_budget_pct=7.5,
            semantic_budget_pct=12.5,
            provider="gemini",
            top_escalations=1,
        )

        assert result["status"] == "critical"
        assert result["drift"]["within_budget"] is True
        assert result["drift"]["structural_budget_pct"] == 7.5
        assert result["drift"]["semantic_budget_pct"] == 12.5
        assert result["kpis"]["total_events"] == 8
        assert result["escalation"]["backlog_count"] == 2
        assert result["escalation"]["past_sla_count"] == 1
        assert result["escalation"]["top_escalations_count"] == 1
        assert result["escalation"]["top_escalations"][0]["run_id"] == "run-1"
        assert "Escalation backlog critical" in result["alerts"][0]

    def test_observe_summary_impl_trend_samples_controls_query_and_summary(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Trend sample request is passed through and trend summary is populated."""

        class _FakeTelemetry:
            def __init__(self, _session_dir) -> None:
                pass

            def get_fallback_kpis(
                self,
                limit: int = 500,
                structural_budget_pct: float = 5.0,
                semantic_budget_pct: float = 10.0,
                provider: str | None = None,
            ) -> dict:
                return {
                    "total": 1,
                    "fallback_rate": 0.0,
                    "success_rate": 1.0,
                    "avg_confidence": 0.97,
                    "structural_drift_pct": 0.1,
                    "semantic_drift_pct": 0.2,
                    "by_provider": {},
                }

            def detect_drift(self, window_size: int = 50) -> list[str]:
                return []

            def get_drift_budget_status(self, structural_budget_pct, semantic_budget_pct, limit=500):
                return {
                    "within_budget": True,
                    "structural_rate_pct": 0.0,
                    "semantic_rate_pct": 0.0,
                    "structural_budget_pct": structural_budget_pct,
                    "semantic_budget_pct": semantic_budget_pct,
                }

        class _FakeEscalationQueue:
            def __init__(self, _session_dir) -> None:
                pass

            def list_pending(self, past_sla_only: bool = False, limit: int = 50) -> list[dict]:
                return []

        monkeypatch.setattr("thegent.contracts.telemetry.ContractTelemetry", _FakeTelemetry)
        monkeypatch.setattr("thegent.execution.EscalationQueue", _FakeEscalationQueue)
        snapshot_file = tmp_path / "observe_summary_snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_file))

        result = cli_impl.observe_summary_impl(
            limit=50,
            drift_window=10,
            structural_budget_pct=5.0,
            semantic_budget_pct=10.0,
            provider=None,
            trend_samples=3,
            top_escalations=2,
        )

        assert result["trend_summary"]["enabled"] is True
        assert result["trend_summary"]["trend_samples_requested"] == 3
        assert result["trend_summary"]["trend_effective_samples"] == 3
        assert result["trend_summary"]["history_sample_count"] == 0
        assert result["generated_query"]["trend_samples"] == 3
        assert result["trend_summary"]["trend_snapshot_health"] in {
            "good",
            "warning",
            "degraded",
            "critical",
        }
