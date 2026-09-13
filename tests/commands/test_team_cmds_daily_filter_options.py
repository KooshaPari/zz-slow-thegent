"""Tests for daily snapshot command filter forwarding and output modes."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.cli.commands import team_cmds


class FakeSessionScraper:
    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path


def test_snapshot_daily_index_cmd_forwards_trigger_tag_since(
    monkeypatch, tmp_path: Path
) -> None:
    seen: dict[str, object] = {}

    def fake_snapshot_daily_index_payload(
        scraper, limit: int = 1000, trigger=None, tag=None, since=None
    ):
        seen["scraper"] = scraper
        seen["limit"] = limit
        seen["trigger"] = trigger
        seen["tag"] = tag
        seen["since"] = since
        return {"days": []}

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_index_payload",
        fake_snapshot_daily_index_payload,
    )

    team_cmds.snapshot_daily_index_cmd(
        project=tmp_path, trigger="manual", tag="ops", since="2026-02-20T00:00:00Z"
    )

    assert isinstance(seen["scraper"], FakeSessionScraper)
    assert seen["limit"] == 1000
    assert seen["trigger"] == "manual"
    assert seen["tag"] == "ops"
    assert seen["since"] == "2026-02-20T00:00:00Z"


def test_snapshot_daily_totals_cmd_forwards_trigger_tag_since(
    monkeypatch, tmp_path: Path
) -> None:
    seen: dict[str, object] = {}

    def fake_snapshot_daily_totals_payload(
        scraper, limit: int = 1000, trigger=None, tag=None, since=None
    ):
        seen["scraper"] = scraper
        seen["limit"] = limit
        seen["trigger"] = trigger
        seen["tag"] = tag
        seen["since"] = since
        return {
            "total_days": 0,
            "total_snapshots": 0,
            "total_prompts": 0,
            "total_commands": 0,
            "total_files": 0,
            "generated_at": None,
        }

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_totals_payload",
        fake_snapshot_daily_totals_payload,
    )

    team_cmds.snapshot_daily_totals_cmd(
        project=tmp_path, trigger="session_change", tag="nightly", since="2026-02-01"
    )

    assert isinstance(seen["scraper"], FakeSessionScraper)
    assert seen["limit"] == 1000
    assert seen["trigger"] == "session_change"
    assert seen["tag"] == "nightly"
    assert seen["since"] == "2026-02-01"


def test_snapshot_daily_export_cmd_forwards_trigger_tag_since(
    monkeypatch, tmp_path: Path
) -> None:
    seen: dict[str, object] = {}

    def fake_snapshot_daily_export_payload(
        scraper,
        out_path: str | None,
        limit: int = 1000,
        trigger=None,
        tag=None,
        since=None,
    ):
        seen["scraper"] = scraper
        seen["out_path"] = out_path
        seen["limit"] = limit
        seen["trigger"] = trigger
        seen["tag"] = tag
        seen["since"] = since
        return {
            "source_json": "snapshot-daily-index.json",
            "source_md": "snapshot-daily-index.md",
        }

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_export_payload",
        fake_snapshot_daily_export_payload,
    )

    team_cmds.snapshot_daily_export_cmd(
        project=tmp_path,
        out_dir=tmp_path / "out",
        trigger="manual",
        tag="release",
        since="2026-02-10T12:00:00+00:00",
    )

    assert isinstance(seen["scraper"], FakeSessionScraper)
    assert seen["out_path"] == str(tmp_path / "out")
    assert seen["limit"] == 1000
    assert seen["trigger"] == "manual"
    assert seen["tag"] == "release"
    assert seen["since"] == "2026-02-10T12:00:00+00:00"


def test_snapshot_daily_totals_cmd_rich_prints_filters_line_when_present(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    payload = {
        "total_days": 1,
        "total_snapshots": 2,
        "total_prompts": 3,
        "total_commands": 4,
        "total_files": 5,
        "generated_at": "2026-02-22T10:00:00+00:00",
        "filters": {
            "trigger": "manual",
            "tag": "ops",
            "since": "2026-02-20T00:00:00+00:00",
        },
    }

    def fake_snapshot_daily_totals_payload(
        scraper, limit: int = 1000, trigger=None, tag=None, since=None
    ):
        assert isinstance(scraper, FakeSessionScraper)
        return payload

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_totals_payload",
        fake_snapshot_daily_totals_payload,
    )

    team_cmds.snapshot_daily_totals_cmd(project=tmp_path)

    out = capsys.readouterr().out
    assert "Filters:" in out
    assert "manual" in out
    assert "ops" in out


def test_snapshot_daily_index_cmd_json_emits_payload_when_filtered(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    payload = {
        "summary": {"total_days": 1, "total_snapshots": 1},
        "days": [{"day": "2026-02-20", "count": 1}],
    }

    def fake_snapshot_daily_index_payload(
        scraper, limit: int = 1000, trigger=None, tag=None, since=None
    ):
        assert isinstance(scraper, FakeSessionScraper)
        assert trigger == "manual"
        assert tag == "ops"
        assert since == "2026-02-20T00:00:00Z"
        return payload

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_index_payload",
        fake_snapshot_daily_index_payload,
    )

    team_cmds.snapshot_daily_index_cmd(
        project=tmp_path,
        trigger="manual",
        tag="ops",
        since="2026-02-20T00:00:00Z",
        format="json",
    )

    out = capsys.readouterr().out.strip()
    assert json.loads(out) == payload
