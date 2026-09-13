"""Routing tests for memory snapshot/dump Typer commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from thegent.cli.apps.memory import app

runner = CliRunner()


def test_memory_snapshot_export_forwards_snapshot_project_out_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_snapshot_export_cmd(
        *,
        snapshot_path: Path,
        project: Path | None,
        out_path: Path | None,
        format: str | None,
    ) -> None:
        captured["snapshot_path"] = snapshot_path
        captured["project"] = project
        captured["out_path"] = out_path
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.snapshot_export_cmd",
        fake_snapshot_export_cmd,
    )

    snapshot_path = tmp_path / "snapshot.json"
    project = tmp_path / "project"
    out_path = tmp_path / "snapshot.md"

    result = runner.invoke(
        app,
        [
            "snapshot",
            "export",
            str(snapshot_path),
            "--project",
            str(project),
            "--out",
            str(out_path),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "snapshot_path": snapshot_path,
        "project": project,
        "out_path": out_path,
        "format": "json",
    }


def test_memory_snapshot_daily_export_forwards_project_out_dir_limit_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_snapshot_daily_export_cmd(
        *,
        project: Path | None,
        out_dir: Path | None,
        limit: int,
        format: str | None,
    ) -> None:
        captured["project"] = project
        captured["out_dir"] = out_dir
        captured["limit"] = limit
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.snapshot_daily_export_cmd",
        fake_snapshot_daily_export_cmd,
    )

    project = tmp_path / "project"
    out_dir = tmp_path / "exports"

    result = runner.invoke(
        app,
        [
            "snapshot",
            "daily-export",
            "--project",
            str(project),
            "--out-dir",
            str(out_dir),
            "--limit",
            "12",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "out_dir": out_dir,
        "limit": 12,
        "format": "json",
    }


def test_memory_snapshot_list_forwards_since_trigger_tag_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_snapshot_list_cmd(
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
        "thegent.cli.commands.team_cmds.snapshot_list_cmd",
        fake_snapshot_list_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "snapshot",
            "list",
            "--project",
            str(project),
            "--since",
            "2026-02-01T00:00:00Z",
            "--trigger",
            "manual",
            "--tag",
            "release",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "limit": 50,
        "trigger": "manual",
        "tag": "release",
        "since": "2026-02-01T00:00:00Z",
        "format": "json",
    }


def test_memory_dump_latest_forwards_category_json_only_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_dump_latest_cmd(
        *,
        project: Path | None,
        category: str | None,
        json_only: bool,
        format: str | None,
    ) -> None:
        captured["project"] = project
        captured["category"] = category
        captured["json_only"] = json_only
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.dump_latest_cmd",
        fake_dump_latest_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "dump",
            "latest",
            "--project",
            str(project),
            "--category",
            "sessions",
            "--json-only",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "project": project,
        "category": "sessions",
        "json_only": True,
        "format": "json",
    }


def test_memory_dump_index_forwards_project_and_format(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_dump_index_cmd(*, project: Path | None, format: str | None) -> None:
        captured["project"] = project
        captured["format"] = format

    monkeypatch.setattr(
        "thegent.cli.commands.team_cmds.dump_index_cmd",
        fake_dump_index_cmd,
    )

    project = tmp_path / "project"

    result = runner.invoke(
        app,
        [
            "dump",
            "index",
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
