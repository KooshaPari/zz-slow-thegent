from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.orchestration.state.session_scraper import SessionScraper
from thegent.orchestration.state.session_snapshot_cli_helpers import (
    snapshot_daily_export_payload,
    snapshot_daily_index_payload,
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


def test_snapshot_daily_index_payload_includes_summary_and_days_list_shape(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000000000000Z-one.json",
        trigger="tool_use",
        tags=["wave7"],
        captured_at="2026-02-22T00:00:00+00:00",
    )

    payload = snapshot_daily_index_payload(scraper, limit=1000)

    assert "summary" in payload
    assert "days" in payload
    assert isinstance(payload["summary"], dict)
    assert isinstance(payload["days"], list)


def test_snapshot_daily_index_day_items_include_required_keys(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000100000000Z-two.json",
        trigger="error",
        tags=["wave7", "compat"],
        captured_at="2026-02-22T00:01:00+00:00",
    )

    payload = snapshot_daily_index_payload(scraper, limit=1000)
    day_item = payload["days"][0]

    required = {"day", "count", "trigger_counts", "tag_counts", "latest_captured_at"}
    assert required.issubset(set(day_item.keys()))


def test_snapshot_daily_export_payload_returns_source_json_and_source_md(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000200000000Z-three.json",
        trigger="session_change",
        tags=["daily-export"],
        captured_at="2026-02-22T00:02:00+00:00",
    )

    payload = snapshot_daily_export_payload(scraper, out_path=str(tmp_path / "daily-export"), limit=1000)

    assert "source_json" in payload
    assert "source_md" in payload


def test_snapshot_daily_export_payload_returns_alias_paths_matching_source_keys(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000300000000Z-four.json",
        trigger="manual",
        tags=["compat"],
        captured_at="2026-02-22T00:03:00+00:00",
    )

    payload = snapshot_daily_export_payload(scraper, out_path=str(tmp_path / "daily-export-aliases"), limit=1000)

    assert payload["json_path"] == payload["source_json"]
    assert payload["markdown_path"] == payload["source_md"]


def test_snapshot_daily_export_json_contains_generated_at_in_summary(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000400000000Z-five.json",
        trigger="tool_use",
        tags=["generated-at"],
        captured_at="2026-02-22T00:04:00+00:00",
    )

    payload = snapshot_daily_export_payload(scraper, out_path=str(tmp_path / "daily-export-json"), limit=1000)
    exported = json.loads(Path(payload["source_json"]).read_text(encoding="utf-8"))

    assert "summary" in exported
    assert exported["summary"].get("generated_at")
