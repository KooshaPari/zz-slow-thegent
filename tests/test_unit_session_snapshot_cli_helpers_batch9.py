from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.orchestration.state.session_scraper import SessionScraper
from thegent.orchestration.state.session_snapshot_cli_helpers import (
    snapshot_daily_export_payload,
    snapshot_daily_index_payload,
    snapshot_daily_totals_payload,
)


def _write_snapshot(
    scraper: SessionScraper,
    *,
    day: str,
    name: str,
    trigger: str,
    tags: list[str],
    captured_at: str,
) -> Path:
    target_dir = scraper.default_snapshot_dir / day
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / name
    payload = {
        "snapshot_id": name.removesuffix(".json"),
        "trigger": trigger,
        "captured_at": captured_at,
        "project_root": str(scraper.project_root),
        "prompts": [],
        "commands": [],
        "files": [],
        "facts": [],
        "decisions": [],
        "tags": tags,
        "sources": [],
    }
    path.write_text(json.dumps(payload).decode(), encoding="utf-8")
    return path


def test_daily_index_payload_filters_by_trigger(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-a.json",
        trigger="tool_use",
        tags=["x"],
        captured_at="2026-02-22T00:00:00+00:00",
    )
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-b.json",
        trigger="session_change",
        tags=["x"],
        captured_at="2026-02-22T01:00:00+00:00",
    )

    payload = snapshot_daily_index_payload(scraper, trigger="tool_use")

    assert payload["summary"]["total_snapshots"] == 1
    assert payload["summary"]["filters"]["trigger"] == "tool_use"


def test_daily_index_payload_filters_by_tag(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-23",
        name="snapshot-a.json",
        trigger="tool_use",
        tags=["keep"],
        captured_at="2026-02-23T00:00:00+00:00",
    )
    _write_snapshot(
        scraper,
        day="2026-02-23",
        name="snapshot-b.json",
        trigger="tool_use",
        tags=["skip"],
        captured_at="2026-02-23T01:00:00+00:00",
    )

    payload = snapshot_daily_index_payload(scraper, tag="keep")

    assert payload["summary"]["total_snapshots"] == 1
    assert payload["summary"]["filters"]["tag"] == "keep"


def test_daily_totals_payload_includes_filters_when_provided(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-24",
        name="snapshot-a.json",
        trigger="tool_use",
        tags=["t"],
        captured_at="2026-02-24T02:00:00+00:00",
    )

    totals = snapshot_daily_totals_payload(
        scraper, trigger="tool_use", tag="t", since="2026-02-24T00:00:00Z"
    )

    assert totals["total_snapshots"] == 1
    assert totals["filters"] == {
        "trigger": "tool_use",
        "tag": "t",
        "since": "2026-02-24T00:00:00Z",
    }


def test_daily_export_payload_forwards_filters_to_summary(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-25",
        name="snapshot-a.json",
        trigger="tool_use",
        tags=["t1"],
        captured_at="2026-02-25T02:00:00+00:00",
    )

    exported = snapshot_daily_export_payload(
        scraper,
        out_path=str(tmp_path / "daily"),
        trigger="tool_use",
        tag="t1",
        since="2026-02-25T00:00:00Z",
    )
    payload = json.loads(Path(exported["source_json"]).read_text(encoding="utf-8"))

    assert payload["summary"]["filters"] == {
        "trigger": "tool_use",
        "tag": "t1",
        "since": "2026-02-25T00:00:00Z",
    }


def test_daily_totals_payload_without_filters_has_no_filters_key(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)

    totals = snapshot_daily_totals_payload(scraper)

    assert "filters" not in totals
