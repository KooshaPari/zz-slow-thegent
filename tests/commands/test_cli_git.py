"""Tests for `thegent git` command options."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app

runner = CliRunner()


@pytest.mark.skip(reason="GitParallelismManager mock location issue")
def test_git_lock_status_reports_clear_state() -> None:
    fake_manager = MagicMock()
    fake_manager.index_lock_status.return_value = {
        "exists": False,
        "path": "/tmp/repo/.git/index.lock",
        "age_seconds": None,
        "stale_after_seconds": 90.0,
        "is_stale": False,
        "open_holder_detected": False,
    }

    with patch("thegent.cli.commands.cli_git.GitParallelismManager", return_value=fake_manager):
        result = runner.invoke(app, ["git", "lock-status"])

    assert result.exit_code == 0
    assert "No index.lock present." in result.stdout
    fake_manager.index_lock_status.assert_called_once_with(stale_after_s=90.0)


@pytest.mark.skip(reason="GitParallelismManager mock location issue")
def test_git_lock_status_outputs_json() -> None:
    fake_manager = MagicMock()
    fake_manager.index_lock_status.return_value = {
        "exists": True,
        "path": "/tmp/repo/.git/index.lock",
        "age_seconds": 123.4,
        "stale_after_seconds": 120.0,
        "is_stale": True,
        "open_holder_detected": False,
    }

    with patch("thegent.cli.commands.cli_git.GitParallelismManager", return_value=fake_manager):
        result = runner.invoke(app, ["git", "lock-status", "--json", "--stale-after", "120"])

    assert result.exit_code == 0
    assert '"exists": true' in result.stdout
    assert '"is_stale": true' in result.stdout
    fake_manager.index_lock_status.assert_called_once_with(stale_after_s=120.0)


@pytest.mark.skip(reason="GitParallelismManager mock location issue")
def test_git_commit_respects_lock_options() -> None:
    fake_manager = MagicMock()
    fake_manager.wait_for_index_lock.return_value = True
    fake_manager.create_commit_from_index.return_value = "new-hash"
    fake_manager.update_ref_cas.return_value = True

    with (
        patch("thegent.cli.commands.cli_git.GitParallelismManager", return_value=fake_manager),
        patch("thegent.cli.commands.cli_git.subprocess.check_output", return_value="old-hash\n"),
    ):
        result = runner.invoke(
            app,
            [
                "git",
                "commit",
                "msg",
                "--agent",
                "agent-1",
                "--ref",
                "refs/heads/main",
                "--lock-timeout",
                "5",
                "--stale-after",
                "15",
                "--no-allow-stale-cleanup",
            ],
        )

    assert result.exit_code == 0
    fake_manager.wait_for_index_lock.assert_called_once_with(
        timeout_s=5.0,
        stale_after_s=15.0,
        allow_stale_cleanup=False,
    )
    fake_manager.create_commit_from_index.assert_called_once_with(
        "msg",
        parent_ref="refs/heads/main",
    )
