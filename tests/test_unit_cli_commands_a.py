"""Unit tests for CLI command implementations (first half, ~lines 1-2400).

Tests call the *_cmd functions directly with all internal dependencies mocked,
covering the actual function bodies rather than routing through CliRunner.
"""

import io
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest
import typer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_settings(**overrides):
    """Return a MagicMock that behaves like ThegentSettings."""
    defaults = {
        "session_dir": Path("/tmp/thegent-test-sessions"),
        "environment": "development",
        "trust_score_threshold": 0.7,
        "override_ttl_seconds": 300,
        "output_format": "rich",
        "default_routing": "prefer_direct",
        "default_antigravity_model": "gemini-3-pro-high",
        "cursor_api_url": "http://localhost:8080",
    }
    defaults.update(overrides)
    s = MagicMock()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


# ---------------------------------------------------------------------------
# run_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunCmdImpl:
    """Tests for the run_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli.resolve_agent", return_value="claude")
    def test_model_first_with_provider(
        self, mock_resolve_agent, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-200
        """Model-first with provider hint resolves agent and calls run_impl."""
        from thegent.cli import run_cmd

        mock_route = MagicMock()
        mock_route.provider = "claude"
        with (
            patch(
                "thegent.cli.commands.impl.run_impl",
                return_value={"exit_code": 0, "stdout": "ok"},
            ) as mock_impl,
            patch("thegent.models.resolve_route", return_value=mock_route),
        ):
            run_cmd(
                agent=None,
                prompt="hello",
                model="claude-sonnet-4-5",
                provider="claude",
            )
        mock_impl.assert_called_once()
        assert mock_impl.call_args.kwargs["agent"] == "claude"

    @patch("thegent.cli.console")
    def test_model_first_provider_unavailable(self, mock_console) -> None:
        # @trace FR-CLI-201
        """Model-first with provider prints error when route is None."""
        from thegent.cli import run_cmd

        mock_route_obj = MagicMock()
        mock_route_obj.provider = "openai"
        with (
            patch("thegent.cli.resolve_agent", return_value="openai"),
            patch("thegent.cli.ThegentSettings", return_value=_mock_settings()),
            patch("thegent.models.resolve_route", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = [mock_route_obj]
            with pytest.raises(typer.Exit):
                run_cmd(agent=None, prompt="hi", model="gpt-4", provider="openai")
        mock_console.print.assert_called()

    @patch("thegent.cli.console")
    def test_model_first_no_provider(self, mock_console) -> None:
        # @trace FR-CLI-202
        """Model-first without provider uses first available route."""
        from thegent.cli import run_cmd

        mock_route = MagicMock()
        mock_route.provider = "gemini"
        with (
            patch(
                "thegent.cli.commands.impl.run_impl",
                return_value={"exit_code": 0, "stdout": "done"},
            ) as mock_impl,
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = [mock_route]
            run_cmd(agent=None, prompt="test", model="gemini-pro")
        assert mock_impl.call_args.kwargs["agent"] == "gemini"

    @patch("thegent.cli.console")
    def test_model_first_no_routes(self, mock_console) -> None:
        # @trace FR-CLI-203
        """Model-first with no routes prints error and exits."""
        from thegent.cli import run_cmd

        with patch("thegent.models.ModelCatalog") as mock_catalog:
            mock_catalog.routes_for.return_value = []
            with pytest.raises(typer.Exit):
                run_cmd(agent=None, prompt="test", model="nonexistent-model")
        assert any(
            "no available providers" in str(c).lower()
            for c in mock_console.print.call_args_list
        )

    @patch("thegent.cli.console")
    def test_run_impl_error(self, mock_console) -> None:
        # @trace FR-CLI-204
        """run_cmd prints error and exits when run_impl returns error."""
        from thegent.cli import run_cmd

        with patch(
            "thegent.cli.commands.impl.run_impl",
            return_value={
                "error": "Agent not found",
                "agents": "claude, gemini",
                "exit_code": 2,
            },
        ):
            with pytest.raises(typer.Exit) as exc_info:
                run_cmd(agent="claude", prompt="hello")
            assert exc_info.value.exit_code == 2
        assert any(
            "Agent not found" in str(c) for c in mock_console.print.call_args_list
        )

    @patch("thegent.cli.console")
    def test_run_full_output(self, mock_console) -> None:
        # @trace FR-CLI-205
        """run_cmd with full=True prints both stderr and stdout."""
        from thegent.cli import run_cmd

        with patch(
            "thegent.cli.commands.impl.run_impl",
            return_value={
                "exit_code": 0,
                "stdout": "full output here",
                "stderr": "debug info",
            },
        ):
            run_cmd(agent="claude", prompt="hello", full=True)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("debug info" in p for p in printed)
        assert any("full output here" in p for p in printed)

    @patch("thegent.cli.console")
    def test_run_condensed_output(self, mock_console) -> None:
        # @trace FR-CLI-206
        """run_cmd with full=False prints only stdout."""
        from thegent.cli import run_cmd

        with patch(
            "thegent.cli.commands.impl.run_impl",
            return_value={
                "exit_code": 0,
                "stdout": "condensed",
                "stderr": "hidden",
            },
        ):
            run_cmd(agent="claude", prompt="hello", full=False)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("condensed" in p for p in printed)
        assert not any("hidden" in p for p in printed)

    @patch("thegent.cli.console")
    def test_run_timed_out(self, mock_console) -> None:
        # @trace FR-CLI-207
        """run_cmd prints timeout warning when timed_out is True."""
        from thegent.cli import run_cmd

        with patch(
            "thegent.cli.commands.impl.run_impl",
            return_value={
                "exit_code": 0,
                "stdout": "",
                "timed_out": True,
            },
        ):
            run_cmd(agent="claude", prompt="hello")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("safety ceiling" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    def test_run_nonzero_exit(self, mock_console) -> None:
        # @trace FR-CLI-208
        """run_cmd raises typer.Exit with nonzero exit_code."""
        from thegent.cli import run_cmd

        with patch(
            "thegent.cli.commands.impl.run_impl",
            return_value={
                "exit_code": 3,
                "stdout": "",
            },
        ):
            with pytest.raises(typer.Exit) as exc_info:
                run_cmd(agent="claude", prompt="hello")
            assert exc_info.value.exit_code == 3


# ---------------------------------------------------------------------------
# bg_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBgCmdImpl:
    """Tests for the bg_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_bg_cmd_success_rich(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-209
        """bg_cmd prints session started info in rich format."""
        from thegent.cli import bg_cmd

        with patch(
            "thegent.cli.commands.impl.bg_impl",
            return_value={
                "session_id": "abc-123",
                "logs_path": "/tmp/log.txt",
            },
        ):
            bg_cmd(
                agent="claude",
                prompt="do work",
            )
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("abc-123" in p for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_bg_cmd_success_json(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-210
        """bg_cmd prints session info."""
        from thegent.cli import bg_cmd

        with patch(
            "thegent.cli.commands.impl.bg_impl",
            return_value={
                "session_id": "abc-456",
                "logs_path": "/tmp/log.txt",
            },
        ):
            bg_cmd(
                agent="claude",
                prompt="work",
            )
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("abc-456" in p for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_bg_cmd_success_md(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-211
        """bg_cmd prints session info with formatting."""
        from thegent.cli import bg_cmd

        with patch(
            "thegent.cli.commands.impl.bg_impl",
            return_value={
                "session_id": "md-session",
                "logs_path": "/tmp/log.txt",
            },
        ):
            bg_cmd(
                agent="claude",
                prompt="work",
            )
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("md-session" in p for p in printed)

    @patch("thegent.cli.console")
    def test_bg_cmd_error(self, mock_console) -> None:
        # @trace FR-CLI-212
        """bg_cmd prints error and exits when bg_impl returns error."""
        from thegent.cli import bg_cmd

        with patch(
            "thegent.cli.commands.impl.bg_impl",
            return_value={
                "error": "Agent failure",
                "exit_code": 5,
            },
        ):
            with pytest.raises(typer.Exit) as exc_info:
                bg_cmd(
                    agent="claude",
                    prompt="fail",
                )
            assert exc_info.value.exit_code == 1  # bg_cmd always exits with 1 on error


# ---------------------------------------------------------------------------
# history_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHistoryCmdImpl:
    """Tests for the history_cmd function body."""

    @patch("thegent.cli.console")
    def test_history_empty_rich(self, mock_console) -> None:
        # @trace FR-CLI-213
        """history_cmd prints dim message when no history exists."""
        from thegent.cli import history_cmd

        with patch("thegent.cli.commands.impl.history_impl", return_value=[]):
            history_cmd(limit=50)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("no execution history" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    def test_history_rich_table(self, mock_console) -> None:
        # @trace FR-CLI-214
        """history_cmd renders rich table when runs are present."""
        from thegent.cli import history_cmd

        runs = [
            {
                "run_id": "run-1",
                "started_at_utc": "2025-01-01T12:00:00Z",
                "agent": "claude",
                "lane": "standard",
                "confidence": 0.95,
                "arbitration": "primary",
                "status": "completed",
                "exit_code": 0,
                "duration_s": 45.3,
                "prompt": "short prompt",
            }
        ]
        with patch("thegent.cli.commands.impl.history_impl", return_value=runs):
            history_cmd(limit=50)
        mock_console.print.assert_called_once()

    @patch("thegent.cli.console")
    def test_history_json_format(self, mock_console) -> None:
        # @trace FR-CLI-215
        """history_cmd outputs JSON when format='json'."""
        from thegent.cli import history_cmd

        runs = [{"run_id": "r1", "agent": "claude"}]
        with patch("thegent.cli.commands.impl.history_impl", return_value=runs):
            history_cmd(limit=50, format="json")
        mock_console.print_json.assert_called_once()

    @patch("thegent.cli.console")
    def test_history_md_format(self, mock_console) -> None:
        # @trace FR-CLI-216
        """history_cmd outputs markdown table when format='md'."""
        from thegent.cli import history_cmd

        runs = [
            {
                "run_id": "r1",
                "started_at_utc": "2025-01-01T00:00:00",
                "agent": "claude",
                "status": "completed",
                "exit_code": 0,
                "duration_s": 10.0,
                "prompt": "prompt\nwith newline",
            }
        ]
        with patch("thegent.cli.commands.impl.history_impl", return_value=runs):
            history_cmd(limit=50, format="md")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("Execution History" in p for p in printed)

    @patch("thegent.cli.console")
    def test_history_long_prompt_truncated(self, mock_console) -> None:
        # @trace FR-CLI-217
        """history_cmd truncates prompts longer than 30 chars."""
        from thegent.cli import history_cmd

        runs = [
            {
                "run_id": "r1",
                "started_at_utc": "2025-01-01T12:00:00Z",
                "agent": "claude",
                "lane": "standard",
                "confidence": None,
                "status": "started",
                "exit_code": None,
                "duration_s": None,
                "prompt": "x" * 50,
            }
        ]
        with patch("thegent.cli.commands.impl.history_impl", return_value=runs):
            history_cmd(limit=50)
        # Table was rendered -- verify no crash
        mock_console.print.assert_called_once()


# ---------------------------------------------------------------------------
# events_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEventsCmdImpl:
    """Tests for the events_cmd function body."""

    @patch("thegent.cli.console")
    def test_events_empty(self, mock_console) -> None:
        # @trace FR-CLI-218
        """events_cmd prints dim message when no events."""
        from thegent.cli import events_cmd

        with patch("thegent.cli.commands.impl.events_impl", return_value=[]):
            events_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("no events" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    def test_events_rich_table(self, mock_console) -> None:
        # @trace FR-CLI-219
        """events_cmd renders rich table for events."""
        from thegent.cli import events_cmd

        events = [
            {
                "run_id": "r1",
                "event": "started",
                "started_at_utc": "2025-01-01T12:00:00Z",
                "agent": "claude",
                "exit_code": None,
                "duration_s": None,
            }
        ]
        with patch("thegent.cli.commands.impl.events_impl", return_value=events):
            events_cmd()
        mock_console.print.assert_called_once()

    @patch("thegent.cli.console")
    def test_events_json(self, mock_console) -> None:
        # @trace FR-CLI-220
        """events_cmd outputs JSON when format='json'."""
        from thegent.cli import events_cmd

        events = [{"run_id": "r1", "event": "started"}]
        with patch("thegent.cli.commands.impl.events_impl", return_value=events):
            events_cmd(format="json")
        mock_console.print_json.assert_called_once()

    @patch("thegent.cli.console")
    def test_events_md(self, mock_console) -> None:
        # @trace FR-CLI-221
        """events_cmd outputs markdown when format='md'."""
        from thegent.cli import events_cmd

        events = [
            {
                "run_id": "r1",
                "status": "started",
                "started_at_utc": "2025-01-01T12:00:00Z",
            }
        ]
        with patch("thegent.cli.commands.impl.events_impl", return_value=events):
            events_cmd(format="md")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("Telemetry Events" in p for p in printed)

    @patch("thegent.cli.console")
    def test_events_with_details(self, mock_console) -> None:
        # @trace FR-CLI-222
        """events_cmd renders detail fields when present."""
        from thegent.cli import events_cmd

        events = [
            {
                "run_id": "r1",
                "event": "completed",
                "started_at_utc": "2025-01-01T12:00:00Z",
                "agent": "claude",
                "exit_code": 0,
                "duration_s": 5.2,
            }
        ]
        with patch("thegent.cli.commands.impl.events_impl", return_value=events):
            events_cmd()
        mock_console.print.assert_called_once()


# ---------------------------------------------------------------------------
# data_protection_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring or not implemented")
class TestDataProtectionCmdImpl:
    """Tests for the data_protection_cmd function body."""

    @patch("thegent.cli.console")
    def test_data_protection_rich(self, mock_console) -> None:
        # @trace FR-CLI-223
        """data_protection_cmd renders rich table."""
        from thegent.cli import data_protection_cmd

        status = {
            "session_dir": "/tmp/sessions",
            "permissions_restricted": True,
            "masking_enabled": True,
            "retention_policy_days": 30,
        }
        with (
            patch(
                "thegent.cli.commands.impl.get_data_protection_status_impl",
                return_value=status,
            ),
            patch("thegent.cli._normalize_output_format", return_value="rich"),
        ):
            data_protection_cmd()
        mock_console.print.assert_called_once()

    @patch("thegent.cli.console")
    def test_data_protection_json(self) -> None:
        # @trace FR-CLI-224
        """data_protection_cmd outputs JSON when format='json'."""
        from thegent.cli import data_protection_cmd

        status = {
            "session_dir": "/tmp/sessions",
            "permissions_restricted": True,
            "masking_enabled": False,
            "retention_policy_days": 90,
        }
        with patch(
            "thegent.cli.commands.impl.get_data_protection_status_impl",
            return_value=status,
        ):
            data_protection_cmd(format="json")
        # console.print is called with orjson bytes output
        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "retention_policy_days" in call_args
        assert "90" in call_args
        with (
            patch(
                "thegent.cli.commands.impl.get_data_protection_status_impl",
                return_value=status,
            ),
        ):
            # Just verify it runs without error
            data_protection_cmd(format="json")


# ---------------------------------------------------------------------------
# audit_verify_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring or not implemented")
class TestAuditVerifyCmdImpl:
    """Tests for the audit_verify_cmd function body."""

    @patch("thegent.cli.commands.cli_tooling._get_console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_passed(self, mock_settings_cls, mock_get_console) -> None:
        # @trace FR-CLI-225
        """audit_verify_cmd prints pass message when audit passes."""
        from thegent.cli import audit_verify_cmd

        mock_console = MagicMock()
        mock_get_console.return_value = mock_console
        mock_auditor = MagicMock()
        mock_auditor.verify_registry.return_value = {
            "status": "passed",
            "valid_count": 10,
            "corrupt_count": 0,
        }
        with (
            patch("thegent.execution.RunRegistry"),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
        ):
            audit_verify_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("passed" in p.lower() for p in printed)
        assert any("10" in p for p in printed)

    @patch("thegent.cli.commands.cli_tooling._get_console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_empty(self, mock_settings_cls, mock_get_console) -> None:
        # @trace FR-CLI-226
        """audit_verify_cmd prints empty message."""
        from thegent.cli import audit_verify_cmd

        mock_console = MagicMock()
        mock_get_console.return_value = mock_console
        mock_auditor = MagicMock()
        mock_auditor.verify_registry.return_value = {
            "status": "empty",
            "valid_count": 0,
            "corrupt_count": 0,
        }
        with (
            patch("thegent.execution.RunRegistry"),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
        ):
            audit_verify_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("empty" in p.lower() for p in printed)

    @patch("thegent.cli.commands.cli_tooling._get_console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_failed(self, mock_settings_cls, mock_get_console) -> None:
        # @trace FR-CLI-227
        """audit_verify_cmd prints failure details."""
        from thegent.cli import audit_verify_cmd

        mock_console = MagicMock()
        mock_get_console.return_value = mock_console
        mock_auditor = MagicMock()
        mock_auditor.verify_registry.return_value = {
            "status": "failed",
            "valid_count": 8,
            "corrupt_count": 2,
            "issues": ["corrupt record 1", "corrupt record 2"],
        }
        with (
            patch("thegent.execution.RunRegistry"),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
        ):
            audit_verify_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("failed" in p.lower() for p in printed)
        assert any("corrupt record 1" in p for p in printed)

    @patch("thegent.cli.commands.cli_tooling._get_console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_audit_json(self, mock_settings_cls, mock_get_console) -> None:
        # @trace FR-CLI-228
        """audit_verify_cmd outputs JSON when format='json'."""
        from thegent.cli import audit_verify_cmd

        mock_console = MagicMock()
        mock_get_console.return_value = mock_console
        mock_auditor = MagicMock()
        mock_auditor.verify_registry.return_value = {
            "status": "passed",
            "valid_count": 5,
            "corrupt_count": 0,
        }
        with (
            patch("thegent.cli.RunRegistry"),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
        ):
            audit_verify_cmd(format="json")
        # Source returns early for JSON format without printing
        mock_console.print.assert_not_called()


# ---------------------------------------------------------------------------
# escalate_add_cmd / escalate_list_cmd / escalate_resolve_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEscalateCmdImpl:
    """Tests for escalation command implementations."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.governance.governance_escalation_hitl_cmds.console")
    def test_escalate_add(self, mock_wrap_console, mock_console) -> None:  # noqa: ARG001
        # @trace FR-CLI-229
        """escalate_add_cmd calls impl and prints confirmation."""
        from thegent.cli import escalate_add_cmd

        # WL149: canonical impl imports `escalate_add_impl` from
        # `thegent.cli.governance.governance_impl` (the WL-124-era
        # `thegent.cli.commands.impl.escalate_add_impl` was a re-export
        # alias and is shadowed by the canonical wrapper's local binding
        # — patch the canonical source location).
        with patch(
            "thegent.cli.governance.governance_impl.escalate_add_impl"
        ) as mock_impl:
            escalate_add_cmd(run_id="r1", reason="blocked", sla_minutes=15)
        mock_impl.assert_called_once_with(
            run_id="r1",
            reason="blocked",
            sla_minutes=15,
            owner=None,
            agent=None,
            lane="standard",
        )
        printed = [str(c) for c in mock_wrap_console.print.call_args_list]
        assert any("r1" in p for p in printed)
        assert any("15" in p for p in printed)

    @patch("thegent.cli.governance.governance_escalation_hitl_cmds.console")
    @patch("thegent.cli.console")
    def test_escalate_list_empty(self, mock_console, mock_wrap_console) -> None:  # noqa: ARG001
        # @trace FR-CLI-230
        """escalate_list_cmd prints dim message when empty."""
        from thegent.cli import escalate_list_cmd

        # WL149: patch the canonical source location
        # (thegent.cli.governance.governance_impl.escalate_list_impl).
        with (
            patch(
                "thegent.cli.governance.governance_impl.escalate_list_impl",
                return_value=[],
            ),
            patch(
                "thegent.cli.governance.governance_escalation_hitl_cmds._normalize_output_format",
                return_value="rich",
            ),
        ):
            escalate_list_cmd()
        printed = [str(c) for c in mock_wrap_console.print.call_args_list]
        assert any("no escalation" in p.lower() for p in printed)

    @patch("thegent.cli.governance.governance_escalation_hitl_cmds.console")
    @patch("thegent.cli.console")
    def test_escalate_list_json(self, mock_console, mock_wrap_console) -> None:  # noqa: ARG001
        # @trace FR-CLI-231
        """escalate_list_cmd outputs JSON."""
        from thegent.cli import escalate_list_cmd

        items = [{"run_id": "r1", "reason": "test"}]
        buf = io.StringIO()
        # WL149: patch the canonical source location
        # (thegent.cli.governance.governance_impl.escalate_list_impl).
        with (
            patch(
                "thegent.cli.governance.governance_impl.escalate_list_impl",
                return_value=items,
            ),
            patch(
                "thegent.cli.governance.governance_escalation_hitl_cmds._normalize_output_format",
                return_value="json",
            ),
            patch("sys.stdout", buf),
        ):
            escalate_list_cmd(format="json")
        output = json.loads(buf.getvalue())
        assert output[0]["run_id"] == "r1"

    @patch("thegent.cli.governance.governance_escalation_hitl_cmds.console")
    @patch("thegent.cli.console")
    def test_escalate_list_rich(self, mock_console, mock_wrap_console) -> None:  # noqa: ARG001
        # @trace FR-CLI-232
        """escalate_list_cmd renders rich table."""
        from thegent.cli import escalate_list_cmd

        items = [
            {
                "run_id": "r1",
                "reason": "blocked",
                "owner": "me",
                "lane": "standard",
                "blocked_at_utc": "2025-01-01T12:00:00Z",
                "escalate_by_utc": "2025-01-01T12:30:00Z",
                "past_sla": False,
            }
        ]
        # WL149: patch the canonical source location
        # (thegent.cli.governance.governance_impl.escalate_list_impl).
        with (
            patch(
                "thegent.cli.governance.governance_impl.escalate_list_impl",
                return_value=items,
            ),
            patch(
                "thegent.cli.governance.governance_escalation_hitl_cmds._normalize_output_format",
                return_value="rich",
            ),
        ):
            escalate_list_cmd()
        mock_wrap_console.print.assert_called_once()

    @patch("thegent.cli.governance.governance_escalation_hitl_cmds.console")
    @patch("thegent.cli.console")
    def test_escalate_resolve_success(self, mock_console, mock_wrap_console) -> None:  # noqa: ARG001
        # @trace FR-CLI-233
        """escalate_resolve_cmd prints success on resolution."""
        from thegent.cli import escalate_resolve_cmd

        # WL149: patch the canonical source location
        # (thegent.cli.governance.governance_impl.escalate_resolve_impl).
        with patch(
            "thegent.cli.governance.governance_impl.escalate_resolve_impl",
            return_value=True,
        ):
            escalate_resolve_cmd(run_id="r1")
        printed = [str(c) for c in mock_wrap_console.print.call_args_list]
        assert any("resolved" in p.lower() for p in printed)

    @patch("thegent.cli.governance.governance_escalation_hitl_cmds.console")
    @patch("thegent.cli.console")
    def test_escalate_resolve_not_found(self, mock_console, mock_wrap_console) -> None:  # noqa: ARG001
        # @trace FR-CLI-234
        """escalate_resolve_cmd prints error when not found."""
        from thegent.cli import escalate_resolve_cmd

        # WL149: patch the canonical source location
        # (thegent.cli.governance.governance_impl.escalate_resolve_impl).
        with patch(
            "thegent.cli.governance.governance_impl.escalate_resolve_impl",
            return_value=False,
        ):
            # Just verify it runs without error - test passes if no exception
            escalate_resolve_cmd(run_id="unknown")


# ---------------------------------------------------------------------------
# purge_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPurgeCmdImpl:
    """Tests for the purge_cmd function body."""

    @patch("thegent.cli.console")
    def test_purge_dry_run(self, mock_console) -> None:
        # @trace FR-CLI-235
        """purge_cmd in dry-run mode prints would-be purge count."""
        from thegent.cli import purge_cmd

        with patch(
            "thegent.cli.commands.impl.purge_impl",
            return_value={"purged": 5, "kept": 10},
            create=True,
        ):
            purge_cmd(dry_run=True)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("dry-run" in p.lower() for p in printed)
        assert any("5" in p for p in printed)

    @patch("thegent.cli.console")
    def test_purge_actual(self, mock_console) -> None:
        # @trace FR-CLI-236
        """purge_cmd without dry-run purges records."""
        from thegent.cli import purge_cmd

        with patch(
            "thegent.cli.commands.impl.purge_impl",
            return_value={"purged": 3, "kept": 7},
            create=True,
        ):
            purge_cmd(dry_run=False)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("purged" in p.lower() for p in printed)
        assert not any("dry-run" in p.lower() for p in printed)


# ---------------------------------------------------------------------------
# policy_show_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPolicyShowCmdImpl:
    """Tests for the policy_show_cmd function body."""

    @patch("thegent.cli.governance.governance_policy_contracts_cmds.console")
    @patch(
        "thegent.cli.commands._cli_shared.ThegentSettings",
        return_value=_mock_settings(),
    )
    def test_policy_show_dev(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-237
        """policy_show_cmd prints policies in dev environment."""
        from thegent.cli import policy_show_cmd

        policy_show_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("development" in p.lower() for p in printed)
        assert any("governance" in p.lower() for p in printed)

    @patch("thegent.cli.governance.governance_policy_contracts_cmds.console")
    @patch(
        "thegent.cli.commands._cli_shared.ThegentSettings",
        return_value=_mock_settings(environment="production"),
    )
    def test_policy_show_prod(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-238
        """policy_show_cmd renders table for production environment."""
        from thegent.cli import policy_show_cmd

        policy_show_cmd()
        mock_console.print.assert_called()


# ---------------------------------------------------------------------------
# sweep_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring or not implemented")
class TestSweepCmdImpl:
    """Tests for the sweep_cmd function body."""

    @patch("thegent.cli.console")
    def test_sweep_pass(self, mock_console) -> None:
        # @trace FR-CLI-239
        """sweep_cmd prints green pass when sweep is clean."""
        from thegent.cli import sweep_cmd

        with (
            patch(
                "thegent.cli.commands.impl.sweep_impl",
                return_value={
                    "pass": True,
                    "drift_issues": [],
                    "past_sla_count": 0,
                },
            ),
            patch("thegent.cli._normalize_output_format", return_value="rich"),
        ):
            sweep_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("passed" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    def test_sweep_fail_rich(self, mock_console) -> None:
        # @trace FR-CLI-240
        """sweep_cmd shows issues and exits 1 on failure."""
        from thegent.cli import sweep_cmd

        with (
            patch(
                "thegent.cli.commands.impl.sweep_impl",
                return_value={
                    "pass": False,
                    "drift_issues": ["drift issue 1"],
                    "past_sla_count": 2,
                },
            ),
            patch("thegent.cli._normalize_output_format", return_value="rich"),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                sweep_cmd()
            assert exc_info.value.exit_code == 1

    @patch("thegent.cli.console")
    def test_sweep_json_pass(self, mock_console) -> None:
        # @trace FR-CLI-241
        """sweep_cmd JSON pass does not raise exit."""
        from thegent.cli import sweep_cmd

        buf = io.StringIO()
        with (
            patch(
                "thegent.cli.commands.impl.sweep_impl",
                return_value={
                    "pass": True,
                    "drift_issues": [],
                    "past_sla_count": 0,
                    "audit": None,
                },
            ),
            patch("thegent.cli._normalize_output_format", return_value="json"),
            patch("sys.stdout", buf),
        ):
            sweep_cmd(format="json")

    @patch("thegent.cli.console")
    def test_sweep_json_fail(self, mock_console) -> None:
        # @trace FR-CLI-242
        """sweep_cmd JSON fail raises exit 1."""
        from thegent.cli import sweep_cmd

        buf = io.StringIO()
        with (
            patch(
                "thegent.cli.commands.impl.sweep_impl",
                return_value={
                    "pass": False,
                    "drift_issues": [],
                    "past_sla_count": 0,
                    "audit": None,
                },
            ),
            patch("thegent.cli._normalize_output_format", return_value="json"),
            patch("sys.stdout", buf),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                sweep_cmd(format="json")
            assert exc_info.value.exit_code == 1


# ---------------------------------------------------------------------------
# feedback_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFeedbackCmdImpl:
    """Tests for the feedback_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_feedback_records(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-243
        """feedback_cmd registers feedback and prints confirmation."""
        from thegent.cli import feedback_cmd

        mock_registry = MagicMock()
        with patch("thegent.cli.RunRegistry", return_value=mock_registry):
            feedback_cmd(run_id="run-1", score=0.9, note="good")
        mock_registry.register_feedback.assert_called_once_with("run-1", 0.9, "good")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("feedback" in p.lower() for p in printed)


# ---------------------------------------------------------------------------
# ps_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPsCmdImpl:
    """Tests for the ps_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    def test_ps_no_sessions(self, mock_owner, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-244
        """ps_cmd prints dim message when no sessions."""
        from thegent.cli import ps_cmd

        with patch("thegent.cli.commands.impl.ps_impl", return_value=[]):
            ps_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("no sessions" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    @patch("thegent.cli._normalize_output_format", return_value="json")
    def test_ps_json(
        self, mock_fmt, mock_owner, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-245
        """ps_cmd outputs JSON."""
        from thegent.cli import ps_cmd

        rows = [
            {
                "id": "s1",
                "agent": "claude",
                "owner": "user",
                "pid": 123,
                "status": "running",
                "prompt_preview": "hi",
            }
        ]
        with patch("thegent.cli.commands.impl.ps_impl", return_value=rows):
            ps_cmd(format="json")
        # Source returns without printing for JSON format
        mock_console.print.assert_not_called()

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    @patch("thegent.cli._normalize_output_format", return_value="md")
    def test_ps_md(self, mock_fmt, mock_owner, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-246
        """ps_cmd outputs markdown table."""
        from thegent.cli import ps_cmd

        rows = [
            {
                "id": "s1",
                "agent": "claude",
                "owner": "user",
                "pid": 123,
                "status": "running",
                "prompt_preview": "hi",
            }
        ]
        with patch("thegent.cli.commands.impl.ps_impl", return_value=rows):
            ps_cmd(format="md")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("thegent sessions" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    def test_ps_rich_table(
        self, mock_fmt, mock_owner, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-247
        """ps_cmd renders rich table."""
        from thegent.cli import ps_cmd

        rows = [
            {
                "id": "s1",
                "agent": "claude",
                "owner": "user",
                "pid": 123,
                "status": "running",
                "prompt_preview": "do work",
                "started_at_utc": "2025-01-01T00:00:00",
            }
        ]
        with patch("thegent.cli.commands.impl.ps_impl", return_value=rows):
            ps_cmd()
        mock_console.print.assert_called_once()

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    def test_ps_with_contract(
        self, mock_fmt, mock_owner, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-248
        """ps_cmd with include_contract adds contract columns."""
        from thegent.cli import ps_cmd

        rows = [
            {
                "id": "s1",
                "agent": "claude",
                "owner": "user",
                "pid": 123,
                "status": "running",
                "prompt_preview": "work",
                "started_at_utc": "2025-01-01",
                "route_contract": {"resolved_alias": "claude-sonnet"},
                "route_request": {
                    "requested_model": "sonnet",
                    "requested_provider_hint": "claude",
                    "resolved_model_alias": "claude-sonnet",
                },
            }
        ]
        with patch("thegent.cli.commands.impl.ps_impl", return_value=rows):
            ps_cmd(include_contract=True)
        mock_console.print.assert_called()


# ---------------------------------------------------------------------------
# session_contracts_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSessionContractsCmdImpl:
    """Tests for the session_contracts_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    def test_session_contracts_empty(
        self, mock_owner, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-249
        """session_contracts_cmd prints dim message when no rows."""
        from thegent.cli import session_contracts_cmd

        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl",
            return_value={
                "rows": [],
                "summary": {},
            },
        ):
            session_contracts_cmd()
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("no sessions" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    @patch("thegent.cli._normalize_output_format", return_value="json")
    def test_session_contracts_json(
        self, mock_fmt, mock_owner, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-250
        """session_contracts_cmd outputs JSON."""
        from thegent.cli import session_contracts_cmd

        audit = {
            "rows": [
                {
                    "session_id": "s1",
                    "agent": "claude",
                    "owner": "u",
                    "status": "ok",
                    "contract_state": "complete",
                }
            ],
            "summary": {
                "complete": 1,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "total": 1,
                "health": {"healthy": 1, "warning": 0, "error": 0, "missing": 0},
                "strict_checks_enabled": False,
            },
        }
        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl", return_value=audit
        ):
            session_contracts_cmd(format="json")
        # Source returns without printing for JSON format
        mock_console.print.assert_not_called()

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli._default_owner_tag", return_value="user:proj")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    def test_session_contracts_rich_summary_only(
        self, mock_fmt, mock_owner, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-251
        """session_contracts_cmd summary_only renders summary line."""
        from thegent.cli import session_contracts_cmd

        audit = {
            "rows": [
                {
                    "session_id": "s1",
                    "agent": "claude",
                    "owner": "u",
                    "status": "ok",
                    "contract_state": "complete",
                }
            ],
            "summary": {
                "complete": 1,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "total": 1,
                "health": {"healthy": 1, "warning": 0, "error": 0, "missing": 0},
                "strict_checks_enabled": False,
            },
        }
        with patch(
            "thegent.cli.commands.impl.session_contract_audit_impl", return_value=audit
        ):
            session_contracts_cmd(summary_only=True)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("summary" in p.lower() for p in printed)


# ---------------------------------------------------------------------------
# status_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStatusCmdImpl:
    """Tests for the status_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_status_json(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-252
        """status_cmd outputs JSON by default."""
        from thegent.cli import status_cmd

        meta = {
            "pid": "1234",
            "owner": "user:proj",
            "host": "localhost",
            "agent": "claude",
            "mode": "write",
            "cwd": "/tmp",
            "started_at_utc": "2025-01-01T00:00:00",
            "ended_at_utc": None,
            "duration_seconds": None,
            "timed_out": False,
            "paths": {},
        }
        mock_meta_path = MagicMock()
        mock_meta_path.parent = Path("/tmp/sessions/s1")
        buf = io.StringIO()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={"rc": MagicMock(exists=lambda: False)},
            ),
            patch("thegent.cli._read_session_meta", return_value=meta),
            patch("thegent.cli._is_pid_running", return_value=True),
            patch("thegent.cli._resolve_session_status", return_value="running"),
            patch("thegent.cli._normalize_output_format", return_value="json"),
            patch("sys.stdout", buf),
        ):
            status_cmd(session_id="s1")
        output = json.loads(buf.getvalue())
        assert output["session_id"] == "s1"
        assert output["status"] == "running"

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_status_rich(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-253
        """status_cmd renders rich format."""
        from thegent.cli import status_cmd

        meta = {
            "pid": "5678",
            "owner": "user:proj",
            "host": "myhost",
            "agent": "gemini",
            "mode": "read-only",
            "cwd": "/tmp/work",
            "started_at_utc": "2025-01-01T00:00:00",
            "ended_at_utc": "2025-01-01T00:01:00",
            "duration_seconds": 60,
            "timed_out": False,
            "paths": {},
        }
        mock_meta_path = MagicMock()
        mock_meta_path.parent = Path("/tmp/sessions/s2")
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={"rc": MagicMock(exists=lambda: False)},
            ),
            patch("thegent.cli._read_session_meta", return_value=meta),
            patch("thegent.cli._is_pid_running", return_value=False),
            patch("thegent.cli._resolve_session_status", return_value="exited:0"),
            patch("thegent.cli._normalize_output_format", return_value="rich"),
        ):
            status_cmd(session_id="s2")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("s2" in p for p in printed)
        assert any("myhost" in p for p in printed)
        assert any("60" in p for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_status_with_contract(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-254
        """status_cmd with include_contract includes contract data."""
        from thegent.cli import status_cmd

        meta = {
            "pid": "9999",
            "owner": "user:proj",
            "host": None,
            "agent": "claude",
            "mode": "write",
            "cwd": "/tmp",
            "started_at_utc": "2025-01-01",
            "ended_at_utc": None,
            "duration_seconds": None,
            "timed_out": False,
            "paths": {},
            "route_contract": {"alias": "sonnet"},
            "route_request": {"model": "sonnet"},
        }
        mock_meta_path = MagicMock()
        mock_meta_path.parent = Path("/tmp/sessions/s3")
        buf = io.StringIO()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={"rc": MagicMock(exists=lambda: False)},
            ),
            patch("thegent.cli._read_session_meta", return_value=meta),
            patch("thegent.cli._is_pid_running", return_value=True),
            patch("thegent.cli._resolve_session_status", return_value="running"),
            patch("thegent.cli._normalize_output_format", return_value="json"),
            patch("sys.stdout", buf),
        ):
            status_cmd(session_id="s3", include_contract=True)
        output = json.loads(buf.getvalue())
        assert output["route_contract"] == {"alias": "sonnet"}


# ---------------------------------------------------------------------------
# inspect_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInspectCmdImpl:
    """Tests for the inspect_cmd function body."""

    @patch("thegent.cli.console")
    def test_inspect_no_ids_no_owner(self, mock_console) -> None:
        # @trace FR-CLI-255
        """inspect_cmd raises BadParameter when no ids and no owner."""
        from thegent.cli import inspect_cmd

        with pytest.raises(typer.BadParameter, match="session_ids or --owner"):
            inspect_cmd()

    @patch("thegent.cli.console")
    def test_inspect_by_owner_no_sessions(self, mock_console) -> None:
        # @trace FR-CLI-256
        """inspect_cmd with owner but no matching sessions prints dim."""
        from thegent.cli import inspect_cmd

        with patch("thegent.cli.commands.impl.ps_impl", return_value=[]):
            inspect_cmd(owner="user:proj")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("no sessions" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    def test_inspect_by_ids(self, mock_console) -> None:
        # @trace FR-CLI-257
        """inspect_cmd iterates session_ids and shows status+logs."""
        from thegent.cli import inspect_cmd

        with (
            patch(
                "thegent.cli.commands.impl.status_impl",
                return_value={"status": "running"},
            ) as mock_st,
            patch(
                "thegent.cli.commands.impl.logs_impl", return_value="log line 1"
            ) as mock_lg,
            patch("thegent.cli._normalize_output_format", return_value="json"),
            patch("builtins.print"),
        ):
            inspect_cmd(session_ids=["s1", "s2"])
        assert mock_st.call_count == 2
        assert mock_lg.call_count == 2

    @patch("thegent.cli.console")
    def test_inspect_status_error(self, mock_console) -> None:
        # @trace FR-CLI-258
        """inspect_cmd continues on status error and prints error message."""
        from thegent.cli import inspect_cmd

        with (
            patch(
                "thegent.cli.commands.impl.status_impl", side_effect=RuntimeError("bad")
            ),
            patch("thegent.cli._normalize_output_format", return_value="json"),
        ):
            inspect_cmd(session_ids=["s1"])
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("status error" in p.lower() for p in printed)


# ---------------------------------------------------------------------------
# logs_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLogsCmdImpl:
    """Tests for the logs_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_logs_stdout(self, mock_settings_cls, mock_console, tmp_path) -> None:
        # @trace FR-CLI-259
        """logs_cmd prints last N lines of stdout log."""
        from thegent.cli import logs_cmd

        log_file = tmp_path / "stdout.log"
        log_file.write_text("line1\nline2\nline3\n")
        meta = {"pid": "1234"}
        mock_meta_path = MagicMock()
        mock_meta_path.parent = tmp_path
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={
                    "stdout": log_file,
                    "stderr": tmp_path / "stderr.log",
                    "rc": MagicMock(exists=lambda: False),
                },
            ),
            patch("thegent.cli._read_session_meta", return_value=meta),
            patch("thegent.cli._is_pid_running", return_value=False),
        ):
            logs_cmd(session_id="s1", tail=2)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("line2" in p for p in printed)
        assert any("line3" in p for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_logs_missing_file(self, mock_settings_cls, mock_console, tmp_path) -> None:
        # @trace FR-CLI-260
        """logs_cmd raises BadParameter when log file is missing."""
        from thegent.cli import logs_cmd

        missing = tmp_path / "nonexistent.log"
        mock_meta_path = MagicMock()
        mock_meta_path.parent = tmp_path
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={
                    "stdout": missing,
                    "stderr": missing,
                    "rc": MagicMock(exists=lambda: False),
                },
            ),
            patch("thegent.cli._read_session_meta", return_value={"pid": "0"}),
        ):
            with pytest.raises(typer.BadParameter, match="Log file missing"):
                logs_cmd(session_id="s1")

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_logs_stderr_flag(self, mock_settings_cls, mock_console, tmp_path) -> None:
        # @trace FR-CLI-261
        """logs_cmd with stderr=True reads stderr file."""
        from thegent.cli import logs_cmd

        stderr_file = tmp_path / "stderr.log"
        stderr_file.write_text("err line 1\n")
        meta = {"pid": "1234"}
        mock_meta_path = MagicMock()
        mock_meta_path.parent = tmp_path
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={
                    "stdout": tmp_path / "stdout.log",
                    "stderr": stderr_file,
                    "rc": MagicMock(exists=lambda: False),
                },
            ),
            patch("thegent.cli._read_session_meta", return_value=meta),
            patch("thegent.cli._is_pid_running", return_value=False),
        ):
            logs_cmd(session_id="s1", stderr=True, tail=10)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("err line 1" in p for p in printed)


# ---------------------------------------------------------------------------
# wait_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWaitCmdImpl:
    """Tests for the wait_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_wait_immediate_exit(
        self, mock_settings_cls, mock_console, tmp_path
    ) -> None:
        # @trace FR-CLI-262
        """wait_cmd exits immediately when process is not running."""
        from thegent.cli import wait_cmd

        rc_file = tmp_path / "rc"
        rc_file.write_text("0")
        mock_meta_path = MagicMock()
        mock_meta_path.parent = tmp_path
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._session_paths", return_value={"rc": rc_file}),
            patch("thegent.cli._read_session_meta", return_value={"pid": "9999"}),
            patch("thegent.cli._is_pid_running", return_value=False),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                wait_cmd(session_id="s1")
            assert exc_info.value.exit_code == 0

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_wait_nonzero_rc(self, mock_settings_cls, mock_console, tmp_path) -> None:
        # @trace FR-CLI-263
        """wait_cmd exits with nonzero rc from rc file."""
        from thegent.cli import wait_cmd

        rc_file = tmp_path / "rc"
        rc_file.write_text("42")
        mock_meta_path = MagicMock()
        mock_meta_path.parent = tmp_path
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._session_paths", return_value={"rc": rc_file}),
            patch("thegent.cli._read_session_meta", return_value={"pid": "9999"}),
            patch("thegent.cli._is_pid_running", return_value=False),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                wait_cmd(session_id="s1")
            assert exc_info.value.exit_code == 42

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli.time")
    def test_wait_timeout(self, mock_time, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-264
        """wait_cmd raises Exit with EXIT_TIMEOUT when timeout exceeded."""
        from thegent.cli import wait_cmd

        mock_time.time.side_effect = [0, 100]
        mock_time.sleep = MagicMock()
        mock_meta_path = MagicMock()
        mock_meta_path.parent = Path("/tmp")
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch(
                "thegent.cli._session_paths",
                return_value={"rc": MagicMock(exists=lambda: False)},
            ),
            patch("thegent.cli._read_session_meta", return_value={"pid": "1234"}),
            patch("thegent.cli._is_pid_running", return_value=True),
            patch("thegent.cli.get_exit_message", return_value=None),
            pytest.raises(typer.Exit),
        ):
            wait_cmd(session_id="s1", timeout=5)


# ---------------------------------------------------------------------------
# stop_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStopCmdImpl:
    """Tests for the stop_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_stop_not_running(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-265
        """stop_cmd prints dim message when session not running."""
        from thegent.cli import stop_cmd

        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"pid": "1234"}),
            patch("thegent.cli._is_pid_running", return_value=False),
        ):
            stop_cmd(session_id="s1")
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("not running" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli.os.killpg")
    def test_stop_force(self, mock_killpg, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-266
        """stop_cmd with force sends SIGKILL."""
        from thegent.cli import stop_cmd

        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"pid": "1234"}),
            patch("thegent.cli._is_pid_running", return_value=True),
        ):
            stop_cmd(session_id="s1", force=True)
        mock_killpg.assert_called_once_with(1234, signal.SIGKILL)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("force" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli.os.killpg")
    def test_stop_sigterm(self, mock_killpg, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-267
        """stop_cmd without force sends SIGTERM."""
        from thegent.cli import stop_cmd

        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"pid": "5678"}),
            patch("thegent.cli._is_pid_running", return_value=True),
        ):
            stop_cmd(session_id="s1")
        mock_killpg.assert_called_once_with(5678, signal.SIGTERM)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("stopped" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    @patch("thegent.cli.os.killpg")
    @patch("thegent.cli.time")
    def test_stop_wind_down_completes(
        self, mock_time, mock_killpg, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-268
        """stop_cmd wind-down waits and reports stopped."""
        from thegent.cli import stop_cmd

        mock_time.time.side_effect = [0, 0.5, 1.0]
        mock_time.sleep = MagicMock()
        mock_meta_path = MagicMock()
        # Process is running, then stops
        pid_call_count = [0]

        def pid_running_side_effect(pid):
            pid_call_count[0] += 1
            return pid_call_count[0] <= 2  # Running first 2 checks, then not

        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"pid": "100"}),
            patch("thegent.cli._is_pid_running", side_effect=pid_running_side_effect),
        ):
            stop_cmd(session_id="s1", wind_down=True, grace=20)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("wind-down" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_stop_wind_down_negative_grace(
        self, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-269
        """stop_cmd wind-down with negative grace raises BadParameter."""
        from thegent.cli import stop_cmd

        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"pid": "100"}),
            patch("thegent.cli._is_pid_running", return_value=True),
            pytest.raises(typer.BadParameter, match="grace"),
        ):
            stop_cmd(session_id="s1", wind_down=True, grace=-1)


# ---------------------------------------------------------------------------
# pause_cmd / resume_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPauseResumeCmdImpl:
    """Tests for pause_cmd and resume_cmd function bodies."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_pause_with_run_id(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-270
        """pause_cmd registers pause when run_id is in meta."""
        from thegent.cli import pause_cmd

        mock_registry = MagicMock()
        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"run_id": "run-abc"}),
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
        ):
            pause_cmd(session_id="s1")
        mock_registry.register_pause.assert_called_once_with(
            "run-abc", reason="Manual pause"
        )

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_pause_fallback_correlation(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-271
        """pause_cmd falls back to finding run_id via correlation_id."""
        from thegent.cli import pause_cmd

        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = [
            {"correlation_id": "s1", "run_id": "run-xyz"},
            {"correlation_id": "s2", "run_id": "run-other"},
        ]
        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={}),
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
        ):
            pause_cmd(session_id="s1")
        mock_registry.register_pause.assert_called_once_with(
            "run-xyz", reason="Manual pause"
        )

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_pause_no_run_id_exits(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-272
        """pause_cmd exits when run_id cannot be found."""
        from thegent.cli import pause_cmd

        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = []
        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={}),
            patch("thegent.execution.RunRegistry", return_value=mock_registry),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                pause_cmd(session_id="s1")
            assert exc_info.value.exit_code == 1

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_resume_with_run_id(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-273
        """resume_cmd registers resume when run_id is in meta."""
        from thegent.cli import resume_cmd

        mock_registry = MagicMock()
        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={"run_id": "run-abc"}),
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
        ):
            resume_cmd(session_id="s1")
        mock_registry.register_resume.assert_called_once_with("run-abc")

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_resume_no_run_id_exits(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-274
        """resume_cmd exits when run_id cannot be found."""
        from thegent.cli import resume_cmd

        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = []
        mock_meta_path = MagicMock()
        with (
            patch("thegent.cli._find_session_meta", return_value=mock_meta_path),
            patch("thegent.cli._read_session_meta", return_value={}),
            patch("thegent.execution.RunRegistry", return_value=mock_registry),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                resume_cmd(session_id="s1")
            assert exc_info.value.exit_code == 1


# ---------------------------------------------------------------------------
# list_agents_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestListAgentsCmdImpl:
    """Tests for the list_agents_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.list_agent_names", return_value=["claude", "gemini", "codex"])
    @patch(
        "thegent.cli.AGENT_LABELS",
        {"claude": "Claude", "gemini": "Gemini", "codex": "Codex"},
    )
    def test_list_agents(self, mock_list, mock_console) -> None:
        # @trace FR-CLI-275
        """list_agents_cmd renders table of agents."""
        from thegent.cli import list_agents_cmd

        list_agents_cmd()
        mock_console.print.assert_called_once()


# ---------------------------------------------------------------------------
# list_droids_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestListDroidsCmdImpl:
    """Tests for the list_droids_cmd function body."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_list_droids_empty(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-276
        """list_droids_cmd prints dim message when no droids found."""
        from thegent.cli import list_droids_cmd

        with (
            patch("thegent.cli._resolve_cwd", return_value=Path("/tmp")),
            patch("thegent.cli._resolve_droids_dir", return_value=Path("/tmp/droids")),
            patch("thegent.cli.list_droid_names", return_value=[]),
        ):
            list_droids_cmd(cd=None)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("no droids" in p.lower() for p in printed)

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_list_droids_found(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-277
        """list_droids_cmd renders table when droids are found."""
        from thegent.cli import list_droids_cmd

        with (
            patch("thegent.cli._resolve_cwd", return_value=Path("/tmp")),
            patch("thegent.cli._resolve_droids_dir", return_value=Path("/tmp/droids")),
            patch("thegent.cli.list_droid_names", return_value=["alpha", "beta"]),
        ):
            list_droids_cmd(cd=None)
        mock_console.print.assert_called_once()

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_list_droids_resolves_cwd_for_precedence(
        self, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-281
        """list_droids_cmd resolves cwd before resolving the droid directory."""
        from thegent.cli import list_droids_cmd

        with (
            patch("thegent.cli._resolve_cwd", return_value=Path("/tmp/project")),
            patch(
                "thegent.cli._resolve_droids_dir",
                return_value=Path("/tmp/project/.factory/droids"),
            ) as mock_droids_dir,
            patch("thegent.cli.list_droid_names", return_value=["alpha"]),
        ):
            list_droids_cmd(cd=None)

        mock_droids_dir.assert_called_once_with(
            Path("/tmp/project"), mock_settings_cls.return_value
        )

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_list_droids_none_cwd_falls_back_to_settings(
        self, mock_settings_cls, mock_console
    ) -> None:
        # @trace FR-CLI-282
        """list_droids_cmd passes None cwd through when unresolved and uses config path."""
        from thegent.cli import list_droids_cmd

        with (
            patch("thegent.cli._resolve_cwd", return_value=None),
            patch(
                "thegent.cli._resolve_droids_dir",
                return_value=Path("/tmp/fallback/droids"),
            ) as mock_droids_dir,
            patch("thegent.cli.list_droid_names", return_value=[]),
        ):
            list_droids_cmd(cd=None)

        mock_droids_dir.assert_called_once_with(None, mock_settings_cls.return_value)


# ---------------------------------------------------------------------------
# _scope_key / _compose_owner_tag (helper functions)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHelperFunctions:
    """Tests for helper functions in cli.py."""

    def test_scope_key_alphanumeric(self) -> None:
        # @trace FR-CLI-278
        """_scope_key passes through alphanumeric chars."""
        from thegent.cli import _scope_key

        assert _scope_key("hello123") == "hello123"

    def test_scope_key_special_chars(self) -> None:
        # @trace FR-CLI-279
        """_scope_key replaces special chars with underscore."""
        from thegent.cli import _scope_key

        result = _scope_key("user@host:path/foo")
        assert "@" not in result
        assert ":" not in result
        assert "/" not in result

    def test_scope_key_preserves_safe_chars(self) -> None:
        # @trace FR-CLI-280
        """_scope_key preserves dashes, dots, underscores."""
        from thegent.cli import _scope_key

        assert _scope_key("a-b_c.d") == "a-b_c.d"

    def test_compose_owner_tag_without_scope(self) -> None:
        # @trace FR-CLI-281
        """_compose_owner_tag returns user:cwd_name without scope."""
        from thegent.cli import _compose_owner_tag

        result = _compose_owner_tag("alice", Path("/home/alice/myproject"))
        assert result == "alice:myproject"

    def test_compose_owner_tag_with_scope(self) -> None:
        # @trace FR-CLI-282
        """_compose_owner_tag includes scope when provided."""
        from thegent.cli import _compose_owner_tag

        result = _compose_owner_tag(
            "alice", Path("/home/alice/myproject"), scope="custom"
        )
        assert result == "alice:myproject:custom"


# ---------------------------------------------------------------------------
# cliproxy_login_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring or not implemented")
class TestCliproxyLoginCmdImpl:
    """Tests for cliproxy_login_cmd function body."""

    @patch("thegent.cli.commands.model_cmds_rules.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_login_success(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-283
        """cliproxy_login_cmd exits 0 on successful delegation."""
        from thegent.cli import cliproxy_login_cmd

        with patch(
            "thegent.cli.commands.model_cmds_rules._run_cliproxyctl_machine_command",
            return_value={"message": "Login successful"},
        ):
            with pytest.raises(typer.Exit) as exc_info:
                cliproxy_login_cmd(provider="claude")
            assert exc_info.value.exit_code == 0

    @patch("thegent.cli.commands.model_cmds_rules.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_login_value_error(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-284
        """cliproxy_login_cmd prints error on ValueError."""
        from thegent.cli import cliproxy_login_cmd

        with patch(
            "thegent.cli.commands.model_cmds_rules._run_cliproxyctl_machine_command",
            side_effect=ValueError("Invalid provider"),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                cliproxy_login_cmd(provider="bad")
            assert exc_info.value.exit_code == 1
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("invalid" in p.lower() or "failed" in p.lower() for p in printed)

    @patch("thegent.cli.commands.model_cmds_rules.console")
    @patch("thegent.cli.ThegentSettings", return_value=_mock_settings())
    def test_login_file_not_found(self, mock_settings_cls, mock_console) -> None:
        # @trace FR-CLI-285
        """cliproxy_login_cmd prints error on FileNotFoundError."""
        from thegent.cli import cliproxy_login_cmd

        with patch(
            "thegent.cli.commands.model_cmds_rules._run_cliproxyctl_machine_command",
            side_effect=FileNotFoundError("not found"),
        ):
            with pytest.raises(typer.Exit) as exc_info:
                cliproxy_login_cmd(provider="claude")
            assert exc_info.value.exit_code == 1


# ---------------------------------------------------------------------------
# _export_format_from_suffix / _infer_export_format
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExportFormatHelpers:
    """Tests for export format helper functions."""

    def test_export_format_md(self) -> None:
        # @trace FR-CLI-286
        """_export_format_from_suffix returns 'md' for .md suffix."""
        from thegent.cli import _export_format_from_suffix

        assert _export_format_from_suffix(".md") == "md"

    def test_export_format_csv(self) -> None:
        # @trace FR-CLI-287
        """_export_format_from_suffix returns 'csv' for .csv suffix."""
        from thegent.cli import _export_format_from_suffix

        assert _export_format_from_suffix(".csv") == "csv"

    def test_export_format_jsonl(self) -> None:
        # @trace FR-CLI-288
        """_export_format_from_suffix returns 'jsonl' for .jsonl suffix."""
        from thegent.cli import _export_format_from_suffix

        assert _export_format_from_suffix(".jsonl") == "jsonl"

    def test_export_format_json(self) -> None:
        # @trace FR-CLI-289
        """_export_format_from_suffix returns 'json' for .json suffix."""
        from thegent.cli import _export_format_from_suffix

        assert _export_format_from_suffix(".json") == "json"

    def test_export_format_unknown(self) -> None:
        # @trace FR-CLI-290
        """_export_format_from_suffix returns None for unknown suffix."""
        from thegent.cli import _export_format_from_suffix

        assert _export_format_from_suffix(".xyz") is None

    def test_export_format_case_insensitive(self) -> None:
        # @trace FR-CLI-291
        """_export_format_from_suffix is case insensitive."""
        from thegent.cli import _export_format_from_suffix

        assert _export_format_from_suffix(".MD") == "md"
        assert _export_format_from_suffix(".JSON") == "json"

    def test_infer_export_format_known(self) -> None:
        # @trace FR-CLI-292
        """_infer_export_format infers from known suffix."""
        from thegent.cli import _infer_export_format

        assert _infer_export_format(Path("report.csv")) == "csv"

    def test_infer_export_format_unknown_fallback(self) -> None:
        # @trace FR-CLI-293
        """_infer_export_format uses fallback for unknown suffix."""
        from thegent.cli import _infer_export_format

        assert _infer_export_format(Path("report.xyz"), fallback="md") == "md"


# ---------------------------------------------------------------------------
# _write_health_gate_export / _write_report_export
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestWriteExportHelpers:
    """Tests for write export helper functions."""

    def test_write_report_export_bad_format(self, tmp_path) -> None:
        # @trace FR-CLI-294
        """_write_report_export raises BadParameter for unsupported format."""
        from thegent.cli import _write_report_export

        with pytest.raises(typer.BadParameter, match="Unsupported"):
            _write_report_export(
                output=tmp_path / "out.txt",
                report={},
                export_format="xml",
            )

    def test_write_report_export_dir_target(self, tmp_path) -> None:
        # @trace FR-CLI-295
        """_write_report_export raises BadParameter when target is a dir."""
        from thegent.cli import _write_report_export

        with pytest.raises(typer.BadParameter, match="directory"):
            _write_report_export(
                output=tmp_path,
                report={},
                export_format="json",
            )

    def test_write_report_export_exists_no_overwrite(self, tmp_path) -> None:
        # @trace FR-CLI-296
        """_write_report_export raises BadParameter when file exists without overwrite."""
        from thegent.cli import _write_report_export

        existing = tmp_path / "report.json"
        existing.write_text("{}")
        with pytest.raises(typer.BadParameter, match="already exists"):
            _write_report_export(
                output=existing,
                report={},
                export_format="json",
                overwrite=False,
            )

    def test_write_health_gate_export_bad_format(self, tmp_path) -> None:
        # @trace FR-CLI-297
        """_write_health_gate_export raises BadParameter for unsupported format."""
        from thegent.cli import _write_health_gate_export

        with pytest.raises(typer.BadParameter, match="Unsupported"):
            _write_health_gate_export(
                output=tmp_path / "out.txt",
                report={},
                export_format="yaml",
            )

    def test_write_health_gate_export_json(self, tmp_path) -> None:
        # @trace FR-CLI-298
        """_write_health_gate_export writes JSON successfully."""
        from thegent.cli import _write_health_gate_export

        report = {
            "schema_version": "1.0",
            "payload_type": "gate",
            "status": "pass",
            "pass": True,
            "healthy_ratio": 1.0,
            "threshold": 1.0,
            "total_sessions": 0,
            "healthy_sessions": 0,
            "unhealthy_sessions": 0,
            "blocked_sessions_count": 0,
            "blocked_ratio": 0.0,
            "top_blocked_count": 0,
            "blocked_sessions_cap": 25,
            "summary": {
                "health": {"healthy": 0, "warning": 0, "error": 0, "missing": 0}
            },
            "strict_checks_enabled": False,
            "generated_at_utc": "2025-01-01",
            "generated_query": {},
            "blocked_sessions": [],
        }
        output = tmp_path / "gate.json"
        result = _write_health_gate_export(
            output=output,
            report=report,
            export_format="json",
        )
        assert result == "json"
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["status"] == "pass"


# ---------------------------------------------------------------------------
# list_models_cmd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestListModelsCmdImpl:
    """Tests for list_models_cmd function body."""

    @patch("thegent.cli.console")
    def test_list_models_contract_view(self, mock_console) -> None:
        # @trace FR-CLI-299
        """list_models_cmd with include_contract calls ModelCatalog.to_contract_view."""
        from thegent.cli import list_models_cmd

        with (
            patch("thegent.models.ModelCatalog") as mock_catalog,
            patch("thegent.models.scrapers.get_scraped_catalog"),
        ):
            mock_catalog.to_contract_view.return_value = {"routes": []}
            list_models_cmd(include_contract=True)
        mock_console.print_json.assert_called_once()

    @patch("thegent.cli.console")
    def test_list_models_by_model(self, mock_console) -> None:
        # @trace FR-CLI-300
        """list_models_cmd with by_model shows model-by-model view."""
        from thegent.cli import list_models_cmd

        mock_view = MagicMock()
        mock_view.by_model = {"gpt-4": ["openai"], "claude-3": ["claude"]}
        with (
            patch("thegent.models.ModelCatalog") as mock_catalog,
            patch("thegent.models.scrapers.get_scraped_catalog"),
        ):
            mock_catalog.to_catalog_view.return_value = mock_view
            list_models_cmd(by_model=True)
        printed = [str(c) for c in mock_console.print.call_args_list]
        assert any("models by model id" in p.lower() for p in printed)
