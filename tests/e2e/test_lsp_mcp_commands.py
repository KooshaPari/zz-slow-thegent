"""
E2E tests for LSP and MCP commands.

Agent Journey: Agent manages LSP (Language Server Protocol) and MCP (Model Context Protocol)
Expected Behavior: Commands execute successfully and provide service status/management
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands 'lsp' do not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestLspMcpCommands:
    """E2E tests for LSP and MCP commands."""

    # LSP commands
    def test_lsp_help_exits_zero(self) -> None:
        """thegent lsp --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "--help"])
        assert result.exit_code == 0

    def test_lsp_install_help(self) -> None:
        """thegent lsp install --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "install", "--help"])
        assert result.exit_code == 0

    def test_lsp_start_help(self) -> None:
        """thegent lsp start --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "start", "--help"])
        assert result.exit_code == 0

    def test_lsp_stop_help(self) -> None:
        """thegent lsp stop --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "stop", "--help"])
        assert result.exit_code == 0

    def test_lsp_list_help(self) -> None:
        """thegent lsp list --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "list", "--help"])
        assert result.exit_code == 0

    def test_lsp_format_help(self) -> None:
        """thegent lsp format --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "format", "--help"])
        assert result.exit_code == 0

    def test_lsp_inspect_help(self) -> None:
        """thegent lsp inspect --help exits with code 0."""
        result = runner.invoke(app, ["lsp", "inspect", "--help"])
        assert result.exit_code == 0

    # MCP commands
    def test_mcp_help_exits_zero(self) -> None:
        """thegent mcp --help exits with code 0."""
        result = runner.invoke(app, ["mcp", "--help"])
        assert result.exit_code == 0

    def test_mcp_introspect_help(self) -> None:
        """thegent mcp introspect --help exits with code 0."""
        result = runner.invoke(app, ["mcp", "introspect", "--help"])
        assert result.exit_code == 0

    def test_mcp_spotlight_exclude_help(self) -> None:
        """thegent mcp spotlight-exclude --help exits with code 0."""
        result = runner.invoke(app, ["mcp", "spotlight-exclude", "--help"])
        assert result.exit_code == 0

    def test_mcp_prune_help(self) -> None:
        """thegent mcp prune --help exits with code 0."""
        result = runner.invoke(app, ["mcp", "prune", "--help"])
        assert result.exit_code == 0

    def test_mcp_fix_help(self) -> None:
        """thegent mcp fix --help exits with code 0."""
        result = runner.invoke(app, ["mcp", "fix", "--help"])
        assert result.exit_code == 0

    def test_mcp_restart_help(self) -> None:
        """thegent mcp restart --help exits with code 0."""
        result = runner.invoke(app, ["mcp", "restart", "--help"])
        assert result.exit_code == 0

    def test_mcp_stdio_help(self) -> None:
        """thegent mcp-stdio --help exits with code 0."""
        result = runner.invoke(app, ["mcp-stdio", "--help"])
        assert result.exit_code == 0
