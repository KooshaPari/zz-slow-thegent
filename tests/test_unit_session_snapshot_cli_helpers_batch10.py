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


def test_daily_index_payload_exposes_applied_filters_alias(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-20",
        name="snapshot-a.json",
        trigger="tool_use",
        tags=["x"],
        captured_at="2026-02-20T00:00:00+00:00",
    )

    payload = snapshot_daily_index_payload(
        scraper, trigger="tool_use", tag="x", since="2026-02-20T00:00:00Z"
    )

    assert payload["applied_filters"] == payload["summary"]["filters"]


def test_daily_index_payload_preserves_since_input_in_filters(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-21",
        name="snapshot-b.json",
        trigger="tool_use",
        tags=["x"],
        captured_at="2026-02-21T00:00:00+00:00",
    )

    payload = snapshot_daily_index_payload(scraper, since="2026-02-21T00:00:00Z")

    assert payload["summary"]["filters"]["since"] == "2026-02-21T00:00:00Z"


def test_daily_totals_payload_exposes_applied_filters_alias(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-c.json",
        trigger="tool_use",
        tags=["x"],
        captured_at="2026-02-22T00:00:00+00:00",
    )

    totals = snapshot_daily_totals_payload(scraper, trigger="tool_use")

    assert totals["applied_filters"] == totals["filters"]


def test_daily_export_payload_includes_applied_filters_when_filtered(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-23",
        name="snapshot-d.json",
        trigger="tool_use",
        tags=["x"],
        captured_at="2026-02-23T00:00:00+00:00",
    )

    exported = snapshot_daily_export_payload(
        scraper, out_path=str(tmp_path / "daily"), trigger="tool_use"
    )

    assert exported["applied_filters"]["trigger"] == "tool_use"


def test_daily_export_payload_omits_applied_filters_without_filter_args(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-24",
        name="snapshot-e.json",
        trigger="tool_use",
        tags=["x"],
        captured_at="2026-02-24T00:00:00+00:00",
    )

    exported = snapshot_daily_export_payload(scraper, out_path=str(tmp_path / "daily2"))

    assert "applied_filters" not in exported
