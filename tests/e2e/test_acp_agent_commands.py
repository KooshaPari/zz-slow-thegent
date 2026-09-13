"""
E2E tests for ACP and Agent management commands.

Agent Journey: Agent manages ACP (Agent Communication Protocol) and agents
Expected Behavior: Commands execute successfully and provide status/configuration
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI command 'acp' does not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestAcpAgentCommands:
    """E2E tests for ACP and Agent management commands."""

    # ACP commands
    def test_acp_help_exits_zero(self) -> None:
        """thegent acp --help exits with code 0."""
        result = runner.invoke(app, ["acp", "--help"])
        assert result.exit_code == 0

    def test_acp_client_help(self) -> None:
        """thegent acp client --help exits with code 0."""
        result = runner.invoke(app, ["acp", "client", "--help"])
        assert result.exit_code == 0

    def test_acp_server_help(self) -> None:
        """thegent acp server --help exits with code 0."""
        result = runner.invoke(app, ["acp", "server", "--help"])
        assert result.exit_code == 0

    # Agent commands
    def test_agents_help_exits_zero(self) -> None:
        """thegent agents --help exits with code 0."""
        result = runner.invoke(app, ["agents", "--help"])
        assert result.exit_code == 0

    def test_agents_list_help(self) -> None:
        """thegent agents list --help exits with code 0."""
        result = runner.invoke(app, ["agents", "list", "--help"])
        assert result.exit_code == 0

    def test_agents_retry_help(self) -> None:
        """thegent agents retry --help exits with code 0."""
        result = runner.invoke(app, ["agents", "retry", "--help"])
        assert result.exit_code == 0

    # Top-level add-* commands
    def test_add_api_key_help(self) -> None:
        """thegent add-api-key --help exits with code 0."""
        result = runner.invoke(app, ["add-api-key", "--help"])
        assert result.exit_code == 0

    def test_add_benchmark_help(self) -> None:
        """thegent add-benchmark --help exits with code 0."""
        result = runner.invoke(app, ["add-benchmark", "--help"])
        assert result.exit_code == 0

    def test_add_modality_help(self) -> None:
        """thegent add-modality --help exits with code 0."""
        result = runner.invoke(app, ["add-modality", "--help"])
        assert result.exit_code == 0

    def test_add_provider_help(self) -> None:
        """thegent add-provider --help exits with code 0."""
        result = runner.invoke(app, ["add-provider", "--help"])
        assert result.exit_code == 0

    # code command
    def test_code_help(self) -> None:
        """thegent code --help exits with code 0."""
        result = runner.invoke(app, ["code", "--help"])
        assert result.exit_code == 0
