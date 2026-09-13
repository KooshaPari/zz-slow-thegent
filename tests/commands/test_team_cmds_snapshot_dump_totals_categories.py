"""Tests for snapshot daily totals and dump categories team commands."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.cli.commands import team_cmds


class FakeSessionScraper:
    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path


def test_snapshot_daily_totals_cmd_json_emits_totals(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {
        "total_days": 2,
        "total_snapshots": 7,
        "total_prompts": 11,
        "total_commands": 13,
        "total_files": 5,
        "generated_at": "2026-02-22T10:00:00+00:00",
    }

    def fake_snapshot_daily_totals_payload(scraper, limit: int = 1000, trigger=None, tag=None, since=None):
        assert isinstance(scraper, FakeSessionScraper)
        assert scraper.project_path == tmp_path
        assert limit == 1000
        assert trigger is None
        assert tag is None
        assert since is None
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_totals_payload",
        fake_snapshot_daily_totals_payload,
    )

    team_cmds.snapshot_daily_totals_cmd(project=tmp_path, format="json")

    out = capsys.readouterr().out.strip()
    assert json.loads(out) == payload


def test_snapshot_daily_totals_cmd_rich_contains_total_snapshots_and_days(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {
        "total_days": 3,
        "total_snapshots": 9,
        "total_prompts": 0,
        "total_commands": 0,
        "total_files": 0,
        "generated_at": "2026-02-22T10:00:00+00:00",
    }

    def fake_snapshot_daily_totals_payload(scraper, limit: int = 1000, trigger=None, tag=None, since=None):
        assert isinstance(scraper, FakeSessionScraper)
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_totals_payload",
        fake_snapshot_daily_totals_payload,
    )

    team_cmds.snapshot_daily_totals_cmd(project=tmp_path)

    out = capsys.readouterr().out.lower()
    assert "snapshots" in out
    assert "days" in out
    assert "9" in out
    assert "3" in out


def test_dump_categories_cmd_json_emits_categories_list(monkeypatch, capsys, tmp_path: Path) -> None:
    categories = ["alpha", "beta"]

    class FakeConversationDumper:
        def __init__(self, docs_dir: Path) -> None:
            assert docs_dir == tmp_path / "docs" / "dumps"

        def list_dump_categories(self) -> list[str]:
            return categories

    monkeypatch.setattr("thegent.research.always_write_dumps.ConversationDumper", FakeConversationDumper)

    team_cmds.dump_categories_cmd(project=tmp_path, format="json")

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["categories"] == categories


def test_dump_categories_cmd_rich_prints_categories_or_none(monkeypatch, capsys, tmp_path: Path) -> None:
    state = {"categories": ["research", "ops"]}

    class FakeConversationDumper:
        def __init__(self, docs_dir: Path) -> None:
            assert docs_dir == tmp_path / "docs" / "dumps"

        def list_dump_categories(self) -> list[str]:
            return list(state["categories"])

    monkeypatch.setattr("thegent.research.always_write_dumps.ConversationDumper", FakeConversationDumper)

    team_cmds.dump_categories_cmd(project=tmp_path)
    out_nonempty = capsys.readouterr().out.lower()
    assert "research" in out_nonempty
    assert "ops" in out_nonempty

    state["categories"] = []
    team_cmds.dump_categories_cmd(project=tmp_path)
    out_empty = capsys.readouterr().out.lower()
    assert "(none)" in out_empty


def test_team_cmds_all_includes_snapshot_daily_totals_and_dump_categories() -> None:
    exported = set(team_cmds.__all__)
    assert "snapshot_daily_totals_cmd" in exported
    assert "dump_categories_cmd" in exported
