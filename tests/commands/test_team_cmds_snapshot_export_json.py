"""Tests for snapshot export/daily index JSON and rich output behavior."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.cli.commands import team_cmds


class FakeSessionScraper:
    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path


def test_snapshot_export_cmd_json_prints_payload(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {"source": "snapshots/in.json", "output": "snapshots/out.md", "ok": True}

    def fake_snapshot_export_payload(scraper, snapshot_path: str, out_path: str | None):
        assert isinstance(scraper, FakeSessionScraper)
        assert snapshot_path == str(tmp_path / "in.json")
        assert out_path == str(tmp_path / "out.md")
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_export_payload",
        fake_snapshot_export_payload,
    )

    team_cmds.snapshot_export_cmd(
        snapshot_path=tmp_path / "in.json",
        project=tmp_path,
        out_path=tmp_path / "out.md",
        format="json",
    )

    out = capsys.readouterr().out.strip()
    assert json.loads(out) == payload


def test_snapshot_export_cmd_rich_prints_source_to_output(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {"source": "snapshots/in.json", "output": "snapshots/out.md"}

    def fake_snapshot_export_payload(scraper, snapshot_path: str, out_path: str | None):
        assert isinstance(scraper, FakeSessionScraper)
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_export_payload",
        fake_snapshot_export_payload,
    )

    team_cmds.snapshot_export_cmd(snapshot_path=tmp_path / "in.json", project=tmp_path, out_path=tmp_path / "out.md")

    out = capsys.readouterr().out
    assert f"{payload['source']} -> {payload['output']}" in out


def test_snapshot_daily_index_cmd_rich_prefers_snapshots_when_present(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {
        "days": [
            {
                "day": "2026-02-20",
                "snapshots": 7,
                "count": 2,
                "latest_captured_at": "2026-02-20T09:00:00Z",
            }
        ]
    }

    def fake_snapshot_daily_index_payload(scraper, limit: int):
        assert isinstance(scraper, FakeSessionScraper)
        assert limit == 123
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_index_payload",
        fake_snapshot_daily_index_payload,
    )

    team_cmds.snapshot_daily_index_cmd(project=tmp_path, limit=123)

    out = capsys.readouterr().out
    assert "snapshots=7" in out


def test_snapshot_daily_index_cmd_rich_falls_back_to_count_without_snapshots(
    monkeypatch, capsys, tmp_path: Path
) -> None:
    payload = {
        "days": [
            {
                "day": "2026-02-21",
                "count": 4,
                "latest_captured_at": "2026-02-21T10:00:00Z",
            }
        ]
    }

    def fake_snapshot_daily_index_payload(scraper, limit: int):
        assert isinstance(scraper, FakeSessionScraper)
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_daily_index_payload",
        fake_snapshot_daily_index_payload,
    )

    team_cmds.snapshot_daily_index_cmd(project=tmp_path)

    out = capsys.readouterr().out
    assert "snapshots=4" in out


def test_snapshot_export_cmd_json_includes_source_and_output_keys(monkeypatch, capsys, tmp_path: Path) -> None:
    payload = {"source": "snapshots/in.json", "output": "snapshots/out.md", "extra": 1}

    def fake_snapshot_export_payload(scraper, snapshot_path: str, out_path: str | None):
        assert isinstance(scraper, FakeSessionScraper)
        return payload

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.SessionScraper", FakeSessionScraper)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_snapshot_cli_helpers.snapshot_export_payload",
        fake_snapshot_export_payload,
    )

    team_cmds.snapshot_export_cmd(
        snapshot_path=tmp_path / "in.json",
        project=tmp_path,
        out_path=tmp_path / "out.md",
        format="json",
    )

    out = capsys.readouterr().out.strip()
    parsed = json.loads(out)
    assert "source" in parsed
    assert "output" in parsed
