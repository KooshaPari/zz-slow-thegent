"""CLI tests for lane-7 sync commands.

# @trace WL-204 WL-206 WL-209 WL-240
"""

from __future__ import annotations

from typer.testing import CliRunner

from thegent.cli.apps.main import app
from thegent.sync.conflicts import SyncConflict
from thegent.sync.queue import ConflictQueueStore

runner = CliRunner()


def test_sync_conflicts_prints_unresolved_lines(tmp_path):
    queue_file = tmp_path / "conflicts.json"
    store = ConflictQueueStore(queue_file)
    store.add(
        SyncConflict(
            conflict_id="c1",
            wl_id="WL-204",
            field="status",
            local_value="BACKLOG",
            remote_value="IN PROGRESS",
            connector="github",
        )
    )

    result = runner.invoke(app, ["sync", "conflicts", "--queue-file", str(queue_file)])
    assert result.exit_code == 0
    assert "c1" in result.stdout
    assert "action=manual_review" in result.stdout


def test_sync_freeze_and_unfreeze_commands(tmp_path):
    state_file = tmp_path / "freeze.json"

    freeze_result = runner.invoke(
        app,
        [
            "sync",
            "freeze",
            "--reason",
            "maintenance",
            "--actor",
            "lane7",
            "--state-file",
            str(state_file),
        ],
    )
    assert freeze_result.exit_code == 0
    assert "frozen" in freeze_result.stdout.lower()

    unfreeze_result = runner.invoke(
        app,
        ["sync", "unfreeze", "--actor", "lane7", "--state-file", str(state_file)],
    )
    assert unfreeze_result.exit_code == 0
    assert "unfrozen" in unfreeze_result.stdout.lower()


def test_sync_health_outputs_scoreboard_lines():
    result = runner.invoke(
        app,
        ["sync", "health", "--entry", "github,0.95,0", "--entry", "linear,0.8,1"],
    )
    assert result.exit_code == 0
    assert "github score=" in result.stdout
    assert "linear score=" in result.stdout


def test_sync_ga_readiness_returns_nonzero_when_not_ready(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["sync", "ga-readiness", "--format", "json"])
    assert result.exit_code == 1
    assert '"ready": false' in result.stdout
