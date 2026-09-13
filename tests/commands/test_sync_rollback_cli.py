from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.sync import app
from thegent.integrations.reflection_rollback import ReflectionRollbackManager


@pytest.mark.unit
def test_sync_rollback_create_snapshot() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ws_path = Path("docs/reference/WORK_STREAM.md")
        ws_path.parent.mkdir(parents=True, exist_ok=True)
        ws_path.write_text("# Work Stream\n\nbody", encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "rollback",
                "--create",
                "--cycle-id",
                "cycle-a",
                "--work-stream",
                str(ws_path),
            ],
        )

        assert result.exit_code == 0
        assert "Created snapshot" in result.stdout
        snapshot_dir = Path("docs/reference/rollback_snapshots")
        assert snapshot_dir.exists()
        assert list(snapshot_dir.glob("*.json"))


@pytest.mark.unit
def test_sync_rollback_latest_restores_newest_snapshot() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ws_path = Path("docs/reference/WORK_STREAM.md")
        ws_path.parent.mkdir(parents=True, exist_ok=True)
        ws_path.write_text("v1", encoding="utf-8")

        manager = ReflectionRollbackManager()
        manager.take_snapshot(ws_path, cycle_id="c1")
        ws_path.write_text("v2", encoding="utf-8")
        manager.take_snapshot(ws_path, cycle_id="c2")
        ws_path.write_text("broken", encoding="utf-8")

        result = runner.invoke(
            app, ["rollback", "--latest", "--work-stream", str(ws_path)]
        )

        assert result.exit_code == 0
        assert "Restored snapshot" in result.stdout
        assert ws_path.read_text(encoding="utf-8") == "v2"


@pytest.mark.unit
def test_sync_rollback_latest_without_snapshots_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ws_path = Path("docs/reference/WORK_STREAM.md")
        ws_path.parent.mkdir(parents=True, exist_ok=True)
        ws_path.write_text("# empty", encoding="utf-8")

        result = runner.invoke(
            app, ["rollback", "--latest", "--work-stream", str(ws_path)]
        )

        assert result.exit_code == 1
        assert "No snapshots available to restore" in result.stdout
