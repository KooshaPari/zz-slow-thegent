"""Structured worktree governance MCP export smoke.

# @trace FR-MCP-001
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.unit
@pytest.mark.requirement("FR-MCP-001")
def test_mcp_server_exports_structured_worktree_governance_tool() -> None:
    """The MCP server should export the consolidated structured worktree tool."""
    from thegent.mcp import server

    assert hasattr(server, "thegent_worktree")


@pytest.mark.asyncio
@pytest.mark.requirement("FR-MCP-001")
async def test_mcp_server_forwards_legacy_migration_action(monkeypatch, tmp_path) -> None:
    """The consolidated MCP worktree tool should forward legacy migration requests."""
    from thegent.cli.commands import cli_git_worktree_governance as cli_module
    from thegent.mcp import server

    def _fake_run(project_root, *args):  # noqa: ANN001
        assert project_root == tmp_path
        assert args[0] == "migrate-legacy"
        return SimpleNamespace(returncode=0, stdout="[OK] migrated legacy worktree\n", stderr="")

    monkeypatch.setattr(cli_module, "run_worktree_governance_script", _fake_run)

    result = await server.thegent_worktree(
        action="migrate-legacy",
        legacy_path="/tmp/legacy-cache",
        domain="infra",
        scale="m",
        change_anchor="migrate-cache",
        state="blocked",
        root=str(tmp_path),
    )

    assert "migrated legacy worktree" in result.content[0].text
    assert result.structured_content["action"] == "migrate-legacy"
