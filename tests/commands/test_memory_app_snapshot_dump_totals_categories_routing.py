"""Routing tests for memory snapshot daily-totals and dump categories commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from thegent.cli.apps.memory import app

runner = CliRunner()


def test_memory_snapshot_daily_totals_forwards_project_limit_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_snapshot_daily_totals_cmd(*, project: Path | None, limit: int, format: str | None) -> None:
        captured["project"] = project
        captured["limit"] = limit
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.snapshot_daily_totals_cmd",
        fake_snapshot_daily_totals_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "snapshot",
            "daily-totals",
            "--project",
            str(project),
            "--limit",
            "9",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "limit": 9,
        "format": "json",
    }


def test_memory_dump_categories_forwards_project_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_dump_categories_cmd(*, project: Path | None, format: str | None) -> None:
        captured["project"] = project
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.dump_categories_cmd",
        fake_dump_categories_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "dump",
            "categories",
            "--project",
            str(project),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "format": "json",
    }


def test_memory_snapshot_daily_totals_help_exits_zero() -> None:
    result = runner.invoke(app, ["snapshot", "daily-totals", "--help"])
    assert result.exit_code == 0


def test_memory_dump_categories_help_exits_zero() -> None:
    result = runner.invoke(app, ["dump", "categories", "--help"])
    assert result.exit_code == 0


def test_memory_dump_categories_omitted_format_passes_none(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_dump_categories_cmd(*, project: Path | None, format: str | None) -> None:
        captured["project"] = project
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.dump_categories_cmd",
        fake_dump_categories_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "dump",
            "categories",
            "--project",
            str(project),
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "format": None,
    }
