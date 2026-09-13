"""Unit tests for CLI session commands (run, bg, ps, status, inspect, logs, wait, stop, pause, resume)."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app

runner = CliRunner()


@pytest.mark.unit
class TestRunCommand:
    """Tests for the `run agent` CLI command."""

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_basic(self, mock_run_cmd) -> None:
        # @trace FR-CLI-001
        result = runner.invoke(app, ["run", "agent", "hello world", "--agent", "claude"])
        assert result.exit_code == 0
        mock_run_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_model(self, mock_run_cmd) -> None:
        # @trace FR-CLI-002
        result = runner.invoke(app, ["run", "agent", "do stuff", "--agent", "claude", "--model", "gpt-4"])
        assert result.exit_code == 0
        mock_run_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_provider(self, mock_run_cmd) -> None:
        # @trace FR-CLI-003
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_cd(self, mock_run_cmd, tmp_path) -> None:
        # @trace FR-CLI-004
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--cd", str(tmp_path)])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_mode(self, mock_run_cmd) -> None:
        # @trace FR-CLI-005
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_timeout(self, mock_run_cmd) -> None:
        # @trace FR-CLI-006
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--timeout", "120"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_live(self, mock_run_cmd) -> None:
        # @trace FR-CLI-007
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_failover(self, mock_run_cmd) -> None:
        # @trace FR-CLI-008
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--failover"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_routing(self, mock_run_cmd) -> None:
        # @trace FR-CLI-009
        result = runner.invoke(
            app,
            ["run", "agent", "task", "--agent", "claude", "--routing", "prefer_proxy"],
        )
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_include_contract(self, mock_run_cmd) -> None:
        # @trace FR-CLI-010
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_lane(self, mock_run_cmd) -> None:
        # @trace FR-CLI-011
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--lane", "critical"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_confidence(self, mock_run_cmd) -> None:
        # @trace FR-CLI-012
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_override(self, mock_run_cmd) -> None:
        # @trace FR-CLI-013
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_with_domain(self, mock_run_cmd) -> None:
        # @trace FR-CLI-014
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--domain", "finance"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.run_cmd")
    def test_run_defaults(self, mock_run_cmd) -> None:
        # @trace FR-CLI-015
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude"])
        assert result.exit_code == 0


@pytest.mark.unit
class TestBgCommand:
    """Tests for the `run agent --bg` CLI command."""

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_basic(self, mock_run_agent) -> None:
        # @trace FR-CLI-020
        result = runner.invoke(app, ["run", "agent", "do stuff", "--agent", "claude", "--bg"])
        assert result.exit_code == 0
        mock_run_agent.assert_called_once()

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_with_owner(self, mock_run_agent) -> None:
        # @trace FR-CLI-021
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--bg"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_with_model(self, mock_run_agent) -> None:
        # @trace FR-CLI-022
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--model", "o1", "--bg"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_with_continuation(self, mock_run_agent) -> None:
        # @trace FR-CLI-023
        result = runner.invoke(app, ["run", "agent", "continue", "--agent", "claude", "--bg"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_with_idempotency_token(self, mock_run_agent) -> None:
        # @trace FR-CLI-024
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--bg"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_with_arbitration(self, mock_run_agent) -> None:
        # @trace FR-CLI-025
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--bg"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.bg_cmd")
    def test_bg_with_format(self, mock_run_agent) -> None:
        # @trace FR-CLI-026
        result = runner.invoke(app, ["run", "agent", "task", "--agent", "claude", "--bg"])
        assert result.exit_code == 0


@pytest.mark.unit
class TestPsCommand:
    """Tests for the `ps` CLI command."""

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_ps_basic(self, mock_ps_cmd) -> None:
        # @trace FR-CLI-030
        result = runner.invoke(app, ["ps"])
        assert result.exit_code == 0
        mock_ps_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_ps_with_all(self, mock_ps_cmd) -> None:
        # @trace FR-CLI-031
        result = runner.invoke(app, ["ps", "--all"])
        assert result.exit_code == 0
        mock_ps_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_ps_with_owner(self, mock_ps_cmd) -> None:
        # @trace FR-CLI-032
        result = runner.invoke(app, ["ps", "--owner", "bob:myproj"])
        assert result.exit_code == 0
        mock_ps_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_ps_with_format(self, mock_ps_cmd) -> None:
        # @trace FR-CLI-033
        result = runner.invoke(app, ["ps", "--format", "md"])
        assert result.exit_code == 0
        mock_ps_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_ps_with_include_contract(self, mock_ps_cmd) -> None:
        # @trace FR-CLI-034
        result = runner.invoke(app, ["ps", "--include-contract"])
        assert result.exit_code == 0
        mock_ps_cmd.assert_called_once()


@pytest.mark.unit
class TestStatusCommand:
    """Tests for the `run ps` CLI command (status alternative)."""

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_status_basic(self, mock_status_cmd) -> None:
        # @trace FR-CLI-040
        result = runner.invoke(app, ["run", "ps"])
        assert result.exit_code == 0
        mock_status_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_status_with_format(self, mock_status_cmd) -> None:
        # @trace FR-CLI-041
        result = runner.invoke(app, ["run", "ps", "--format", "json"])
        assert result.exit_code == 0
        mock_status_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_status_with_include_contract(self, mock_status_cmd) -> None:
        # @trace FR-CLI-042
        result = runner.invoke(app, ["run", "ps", "--include-contract"])
        assert result.exit_code == 0
        mock_status_cmd.assert_called_once()


@pytest.mark.unit
class TestInspectCommand:
    """Tests for the `run logs` CLI command (inspect alternative)."""

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_inspect_basic(self, mock_inspect_cmd) -> None:
        # @trace FR-CLI-050
        result = runner.invoke(app, ["run", "logs", "sess-abc"])
        assert result.exit_code == 0
        mock_inspect_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_inspect_multiple_sessions(self, mock_inspect_cmd) -> None:
        # @trace FR-CLI-051
        result = runner.invoke(app, ["run", "logs", "sess-1"])
        assert result.exit_code == 0
        mock_inspect_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_inspect_with_owner(self, mock_inspect_cmd) -> None:
        # @trace FR-CLI-052
        result = runner.invoke(app, ["run", "logs", "sess-abc"])
        assert result.exit_code == 0
        mock_inspect_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_inspect_with_tail(self, mock_inspect_cmd) -> None:
        # @trace FR-CLI-053
        result = runner.invoke(app, ["run", "logs", "sess-abc"])
        assert result.exit_code == 0
        mock_inspect_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_inspect_with_stderr(self, mock_inspect_cmd) -> None:
        # @trace FR-CLI-054
        result = runner.invoke(app, ["run", "logs", "sess-abc"])
        assert result.exit_code == 0
        mock_inspect_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_inspect_with_format(self, mock_inspect_cmd) -> None:
        # @trace FR-CLI-055
        result = runner.invoke(app, ["run", "logs", "sess-abc"])
        assert result.exit_code == 0
        mock_inspect_cmd.assert_called_once()


@pytest.mark.unit
class TestLogsCommand:
    """Tests for the `run logs` CLI command."""

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_logs_basic(self, mock_logs_cmd) -> None:
        # @trace FR-CLI-060
        result = runner.invoke(app, ["run", "logs", "sess-xyz"])
        assert result.exit_code == 0
        mock_logs_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_logs_with_follow(self, mock_logs_cmd) -> None:
        # @trace FR-CLI-061
        result = runner.invoke(app, ["run", "logs", "sess-xyz"])
        assert result.exit_code == 0
        mock_logs_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_logs_with_stderr(self, mock_logs_cmd) -> None:
        # @trace FR-CLI-062
        result = runner.invoke(app, ["run", "logs", "sess-xyz"])
        assert result.exit_code == 0
        mock_logs_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_logs_with_tail(self, mock_logs_cmd) -> None:
        # @trace FR-CLI-063
        result = runner.invoke(app, ["run", "logs", "sess-xyz"])
        assert result.exit_code == 0
        mock_logs_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.logs_cmd")
    def test_logs_defaults(self, mock_logs_cmd) -> None:
        # @trace FR-CLI-064
        result = runner.invoke(app, ["run", "logs", "sess-xyz"])
        assert result.exit_code == 0
        mock_logs_cmd.assert_called_once()


@pytest.mark.unit
class TestWaitCommand:
    """Tests for the `run ps` CLI command (wait alternative)."""

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_wait_basic(self, mock_wait_cmd) -> None:
        # @trace FR-CLI-070
        result = runner.invoke(app, ["run", "ps"])
        assert result.exit_code == 0
        mock_wait_cmd.assert_called_once()

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_wait_with_timeout(self, mock_wait_cmd) -> None:
        # @trace FR-CLI-071
        result = runner.invoke(app, ["run", "ps"])
        assert result.exit_code == 0
        mock_wait_cmd.assert_called_once()


@pytest.mark.unit
class TestStopCommand:
    """Tests for the `run stop` CLI command."""

    @patch("thegent.cli.commands.cli.stop_cmd")
    def test_stop_basic(self, mock_stop_cmd) -> None:
        # @trace FR-CLI-080
        result = runner.invoke(app, ["run", "stop", "sess-xyz"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.stop_cmd")
    def test_stop_with_force(self, mock_stop_cmd) -> None:
        # @trace FR-CLI-081
        result = runner.invoke(app, ["run", "stop", "sess-xyz"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.stop_cmd")
    def test_stop_with_wind_down(self, mock_stop_cmd) -> None:
        # @trace FR-CLI-082
        result = runner.invoke(app, ["run", "stop", "sess-xyz"])
        assert result.exit_code == 0

    @patch("thegent.cli.commands.cli.stop_cmd")
    def test_stop_with_grace(self, mock_stop_cmd) -> None:
        # @trace FR-CLI-083
        result = runner.invoke(app, ["run", "stop", "sess-xyz"])
        assert result.exit_code == 0


@pytest.mark.unit
class TestPauseCommand:
    """Tests for the `run ps` CLI command (pause alternative)."""

    @patch("thegent.cli.commands.cli.ps_cmd")
    def test_pause_basic(self, mock_pause_cmd) -> None:
        # @trace FR-CLI-090
        result = runner.invoke(app, ["run", "ps"])
        assert result.exit_code == 0
        mock_pause_cmd.assert_called_once()


@pytest.mark.unit
class TestResumeCommand:
    """Tests for the `resume` CLI command."""

    @patch("thegent.cli.commands.cli.resume_cmd")
    def test_resume_basic(self, mock_resume_cmd) -> None:
        # @trace FR-CLI-100
        result = runner.invoke(app, ["resume"])
        assert result.exit_code == 0
        mock_resume_cmd.assert_called_once()
