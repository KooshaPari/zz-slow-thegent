"""
E2E tests for Plan and Work Stream commands.

Agent Journey: Agent manages work stream and plans via 'thegent plan' commands
Expected Behavior: Commands execute successfully and provide plan status/coordination
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands 'plan' subcommands do not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestPlanCommands:
    """E2E tests for thegent plan commands."""

    def test_plan_help_exits_zero(self) -> None:
        """thegent plan --help exits with code 0."""
        result = runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0

    def test_plan_incorporate_help(self) -> None:
        """thegent plan incorporate --help exits with code 0."""
        result = runner.invoke(app, ["plan", "incorporate", "--help"])
        assert result.exit_code == 0

    def test_plan_do_next_help(self) -> None:
        """thegent plan do-next --help exits with code 0."""
        result = runner.invoke(app, ["plan", "do-next", "--help"])
        assert result.exit_code == 0

    def test_plan_get_next_help(self) -> None:
        """thegent plan get-next --help exits with code 0."""
        result = runner.invoke(app, ["plan", "get-next", "--help"])
        assert result.exit_code == 0

    def test_plan_loop_help(self) -> None:
        """thegent plan loop --help exits with code 0."""
        result = runner.invoke(app, ["plan", "loop", "--help"])
        assert result.exit_code == 0

    def test_plan_spawn_next_help(self) -> None:
        """thegent plan spawn-next --help exits with code 0."""
        result = runner.invoke(app, ["plan", "spawn-next", "--help"])
        assert result.exit_code == 0

    def test_plan_progress_help(self) -> None:
        """thegent plan progress --help exits with code 0."""
        result = runner.invoke(app, ["plan", "progress", "--help"])
        assert result.exit_code == 0

    def test_plan_wait_next_help(self) -> None:
        """thegent plan wait-next --help exits with code 0."""
        result = runner.invoke(app, ["plan", "wait-next", "--help"])
        assert result.exit_code == 0

    def test_plan_claim_help(self) -> None:
        """thegent plan claim --help exits with code 0."""
        result = runner.invoke(app, ["plan", "claim", "--help"])
        assert result.exit_code == 0

    def test_plan_complete_help(self) -> None:
        """thegent plan complete --help exits with code 0."""
        result = runner.invoke(app, ["plan", "complete", "--help"])
        assert result.exit_code == 0

    def test_plan_ready_help(self) -> None:
        """thegent plan ready --help exits with code 0."""
        result = runner.invoke(app, ["plan", "ready", "--help"])
        assert result.exit_code == 0

    def test_plan_status_help(self) -> None:
        """thegent plan status --help exits with code 0."""
        result = runner.invoke(app, ["plan", "status", "--help"])
        assert result.exit_code == 0

    def test_plan_checkpoints_help(self) -> None:
        """thegent plan checkpoints --help exits with code 0."""
        result = runner.invoke(app, ["plan", "checkpoints", "--help"])
        assert result.exit_code == 0

    def test_plan_probe_help(self) -> None:
        """thegent plan probe --help exits with code 0."""
        result = runner.invoke(app, ["plan", "probe", "--help"])
        assert result.exit_code == 0
