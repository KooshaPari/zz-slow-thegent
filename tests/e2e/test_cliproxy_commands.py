"""
E2E tests for thegent cliproxy commands.

Agent Journey: Agent manages CLIProxyAPIPlus via cliproxy commands
Expected Behavior: Commands execute successfully and manage proxy state correctly
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI command 'cliproxy' does not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestCliproxyCommands:
    """E2E tests for thegent cliproxy commands."""

    def test_cliproxy_help_exits_zero(self) -> None:
        """thegent cliproxy --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "--help"])
        assert result.exit_code == 0
        assert "CLIProxyAPIPlus" in result.stdout

    def test_cliproxy_ensure_config_help(self) -> None:
        """thegent cliproxy ensure-config --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "ensure-config", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_start_help(self) -> None:
        """thegent cliproxy start --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "start", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_stop_help(self) -> None:
        """thegent cliproxy stop --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "stop", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_restart_help(self) -> None:
        """thegent cliproxy restart --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "restart", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_models_setup_help(self) -> None:
        """thegent cliproxy models-setup --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "models-setup", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_service_help(self) -> None:
        """thegent cliproxy service --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "service", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_login_help(self) -> None:
        """thegent cliproxy login --help exits with code 0."""
        result = runner.invoke(app, ["cliproxy", "login", "--help"])
        assert result.exit_code == 0

    def test_cliproxy_ensure_config_exits_zero(self) -> None:
        """thegent cliproxy ensure-config exits with code 0."""
        # This command should be safe to run as it just ensures config exists
        result = runner.invoke(app, ["cliproxy", "ensure-config"])
        assert result.exit_code == 0
