"""Routing tests for snapshot daily filter options."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.memory import app

runner = CliRunner()


@pytest.mark.skip(reason="module path issue")
def test_memory_snapshot_daily_index_forwards_trigger_tag_since(
    monkeypatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def fake_snapshot_daily_index_cmd(
        *,
        project: Path | None,
        limit: int,
        trigger: str | None,
        tag: str | None,
        since: str | None,
        format: str | None,
    ) -> None:
        captured["project"] = project
        captured["limit"] = limit
        captured["trigger"] = trigger
        captured["tag"] = tag
        captured["since"] = since
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.snapshot_daily_index_cmd",
        fake_snapshot_daily_index_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "snapshot",
            "daily-index",
            "--project",
            str(project),
            "--trigger",
            "manual",
            "--tag",
            "release",
            "--since",
            "2026-02-01T00:00:00Z",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "limit": 1000,
        "trigger": "manual",
        "tag": "release",
        "since": "2026-02-01T00:00:00Z",
        "format": None,
    }
