"""Tests for team_cmds snapshot/dump exports and JSON output behavior."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.cli.commands import team_cmds


def test_team_cmds_all_contains_snapshot_core_commands() -> None:
    exported = set(team_cmds.__all__)
    expected = {
        "snapshot_list_cmd",
        "snapshot_index_cmd",
        "snapshot_export_cmd",
        "snapshot_prune_cmd",
        "snapshot_meta_cmd",
    }
    assert expected.issubset(exported)


def test_team_cmds_all_contains_snapshot_daily_and_dump_commands() -> None:
    exported = set(team_cmds.__all__)
    expected = {
        "snapshot_daily_index_cmd",
        "snapshot_daily_export_cmd",
        "dump_index_cmd",
        "dump_latest_cmd",
    }
    assert expected.issubset(exported)


def test_snapshot_daily_export_cmd_json_writes_payload(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {
        "source_json": str(tmp_path / "snapshot_daily_index.json"),
        "source_md": str(tmp_path / "snapshot_daily_index.md"),
        "count": 2,
    }

    class FakeSessionScraper:
        def __init__(self, project_path: Path) -> None:
            self.project_path = project_path

    def fake_snapshot_daily_export_payload(scraper, out_path: str | None, limit: int):
        assert isinstance(scraper, FakeSessionScraper)
        assert out_path == str(tmp_path)
        assert limit == 123
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_export_payload",
        fake_snapshot_daily_export_payload,
    )

    team_cmds.snapshot_daily_export_cmd(project=tmp_path, out_dir=tmp_path, limit=123, format="json")

    out = capsys.readouterr().out.strip()
    assert json.loads(out) == payload


def test_dump_latest_cmd_blank_category_treated_as_none(monkeypatch, capsys, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class FakeConversationDumper:
        def __init__(self, docs_dir: Path) -> None:
            captured["docs_dir"] = docs_dir

        def latest_dump(self, category=None, json_only: bool = False):
            captured["category"] = category
            captured["json_only"] = json_only

    monkeypatch.setattr(
        "thegent.research.always_write_dumps.ConversationDumper",
        FakeConversationDumper,
    )

    team_cmds.dump_latest_cmd(project=tmp_path, category="   ", json_only=True, format="json")

    assert captured["docs_dir"] == tmp_path / "docs" / "dumps"
    assert captured["category"] is None
    assert captured["json_only"] is True
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == {"latest": None}


def test_dump_index_cmd_json_writes_index_and_markdown_paths(monkeypatch, capsys, tmp_path: Path) -> None:
    index_path = tmp_path / "docs" / "dumps" / "dump_index.json"
    markdown_path = tmp_path / "docs" / "dumps" / "dump_index.md"

    class FakeConversationDumper:
        def __init__(self, docs_dir: Path) -> None:
            assert docs_dir == tmp_path / "docs" / "dumps"

        def persist_dump_index(self) -> Path:
            return index_path

        def export_dump_index_markdown(self) -> Path:
            return markdown_path

    monkeypatch.setattr(
        "thegent.research.always_write_dumps.ConversationDumper",
        FakeConversationDumper,
    )

    team_cmds.dump_index_cmd(project=tmp_path, format="json")

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["index_path"] == str(index_path)
    assert payload["markdown_path"] == str(markdown_path)
