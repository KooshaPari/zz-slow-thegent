"""Tests for `thegent git worktree` lifecycle commands."""

import importlib.util

import pytest

# Skip entire test module if thegent_git native extension is not available
if importlib.util.find_spec("thegent_git") is None:
    import pytest

    pytest.skip("thegent-git native extension not installed", allow_module_level=True)

from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
from typer.testing import CliRunner

from thegent.cli.commands.cli_git import app

runner = CliRunner()


def test_git_worktree_status_shows_active_agents(tmp_path: Path) -> None:
    """`thegent git worktree status` prints active pooled agents."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.active_agents.return_value = ["agent-1", "agent-2"]
        result = runner.invoke(
            app,
            ["worktree", "status", "--root", str(tmp_path), "--target-branch", "main"],
        )

    assert result.exit_code == 0
    assert "Active pooled agents (2):" in result.output
    assert "agent-1" in result.output
    assert "agent-2" in result.output


def test_git_worktree_status_empty_when_no_agents() -> None:
    """`thegent git worktree status` handles empty pool state."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.active_agents.return_value = []
        result = runner.invoke(app, ["worktree", "status"])

    assert result.exit_code == 0
    assert "No active pooled worktrees." in result.output


def test_git_worktree_acquire_prints_path_and_branch(tmp_path: Path) -> None:
    """`thegent git worktree acquire` returns worktree path and branch."""
    context = MagicMock(path=tmp_path / "agent-1", branch="agent/agent-1")
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.acquire_worktree.return_value = context
        result = runner.invoke(app, ["worktree", "acquire", "agent-1", "--root", str(tmp_path)])

    assert result.exit_code == 0
    normalized_output = result.output.replace("\n", "")
    assert f"path={tmp_path / 'agent-1'}" in normalized_output
    assert "branch=agent/agent-1" in result.output


def test_git_worktree_acquire_reports_failure(tmp_path: Path) -> None:
    """`thegent git worktree acquire` exits non-zero on runtime error."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.acquire_worktree.side_effect = RuntimeError("boom")
        result = runner.invoke(app, ["worktree", "acquire", "agent-x", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "Failed to acquire worktree for agent-x" in result.output


def test_git_worktree_release_failure_returns_non_zero(tmp_path: Path) -> None:
    """`thegent git worktree release` exits non-zero when no active lease exists."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.release_worktree.return_value = False
        result = runner.invoke(app, ["worktree", "release", "agent-9", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "No active worktree for agent agent-9" in result.output


def test_git_worktree_cleanup_stale_reports_count(tmp_path: Path) -> None:
    """`thegent git worktree cleanup-stale` prints removed count."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.cleanup_stale.return_value = 3
        result = runner.invoke(app, ["worktree", "cleanup-stale", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Removed 3 stale pool entry(ies)." in result.output


def test_git_worktree_list_prints_agent_and_branch(tmp_path: Path) -> None:
    """`thegent git worktree list` prints known active agents and branch aliases."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.active_agents.return_value = ["agent-1", "agent-2"]
        result = runner.invoke(app, ["worktree", "list", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Active pooled worktrees:" in result.output
    assert "agent: agent-1" in result.output
    assert "branch: agent/agent-1" in result.output


def test_git_worktree_status_supports_json_output(tmp_path: Path) -> None:
    """`thegent git worktree status --json` emits machine-readable agent state."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.active_agents.return_value = ["alpha", "beta"]
        result = runner.invoke(
            app,
            ["worktree", "status", "--root", str(tmp_path), "--json"],
        )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == [
        {"agent_id": "alpha", "branch": "agent/alpha"},
        {"agent_id": "beta", "branch": "agent/beta"},
    ]


def test_git_worktree_claim_aliases_acquire(tmp_path: Path) -> None:
    """`thegent git worktree claim` reuses acquire logic for terminology alignment."""
    with patch("thegent.cli.commands.cli_git_log_ops.worktree_acquire") as mock_worktree_acquire:
        result = runner.invoke(app, ["worktree", "claim", "agent-x", "--root", str(tmp_path)])

    assert result.exit_code == 0
    mock_worktree_acquire.assert_called_once_with(
        agent_id="agent-x",
        project_root=tmp_path,
        target_branch="HEAD",
        pool_root=None,
        json_output=False,
    )


def test_git_worktree_list_supports_json_output(tmp_path: Path) -> None:
    """`thegent git worktree list --json` emits machine-readable list rows."""
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.active_agents.return_value = ["alpha", "beta"]
        result = runner.invoke(app, ["worktree", "list", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == [
        {"agent_id": "alpha", "branch": "agent/alpha"},
        {"agent_id": "beta", "branch": "agent/beta"},
    ]


def test_git_worktree_acquire_supports_json_output(tmp_path: Path) -> None:
    """`thegent git worktree acquire --json` returns structured context."""
    context = MagicMock(path=tmp_path / "agent-1", branch="agent/agent-1")
    with patch("thegent.cli.commands.cli_git_log_ops.WorktreePool") as mock_pool:
        mock_pool.return_value.acquire_worktree.return_value = context
        result = runner.invoke(app, ["worktree", "acquire", "agent-1", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output.replace("\n", ""))
    assert payload == {
        "agent_id": "agent-1",
        "path": str(tmp_path / "agent-1"),
        "branch": "agent/agent-1",
    }
