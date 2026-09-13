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
    prompts: list[str] | None = None,
    commands: list[str] | None = None,
    files: list[str] | None = None,
) -> Path:
    target_dir = scraper.default_snapshot_dir / day
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / name
    payload = {
        "snapshot_id": name.removesuffix(".json"),
        "trigger": trigger,
        "captured_at": captured_at,
        "project_root": str(scraper.project_root),
        "prompts": prompts or [],
        "commands": commands or [],
        "files": files or [],
        "facts": [],
        "decisions": [],
        "tags": tags,
        "sources": [],
    }
    path.write_text(json.dumps(payload).decode(), encoding="utf-8")
    return path


def test_daily_index_summary_contains_prompt_command_file_totals(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-a.json",
        trigger="tool_use",
        tags=["a"],
        captured_at="2026-02-22T01:00:00+00:00",
        prompts=["p1", "p2"],
        commands=["c1"],
        files=["f1"],
    )
    _write_snapshot(
        scraper,
        day="2026-02-23",
        name="snapshot-b.json",
        trigger="tool_use",
        tags=["b"],
        captured_at="2026-02-23T01:00:00+00:00",
        prompts=["p3"],
        commands=["c2", "c3"],
        files=["f2", "f3"],
    )

    payload = snapshot_daily_index_payload(scraper, limit=1000)

    assert payload["summary"]["total_prompts"] == 3
    assert payload["summary"]["total_commands"] == 3
    assert payload["summary"]["total_files"] == 3


def test_daily_index_summary_has_days_count_alias(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-24",
        name="snapshot-c.json",
        trigger="manual",
        tags=[],
        captured_at="2026-02-24T00:00:00+00:00",
    )

    payload = snapshot_daily_index_payload(scraper, limit=1000)

    assert payload["summary"]["days_count"] == payload["summary"]["total_days"]


def test_snapshot_daily_totals_payload_returns_compact_totals(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-25",
        name="snapshot-d.json",
        trigger="manual",
        tags=[],
        captured_at="2026-02-25T00:00:00+00:00",
        prompts=["p1"],
        commands=["c1"],
        files=["f1"],
    )

    totals = snapshot_daily_totals_payload(scraper, limit=1000)

    assert totals["total_days"] == 1
    assert totals["total_snapshots"] == 1
    assert totals["total_prompts"] == 1
    assert totals["total_commands"] == 1
    assert totals["total_files"] == 1
    assert totals["generated_at"]


def test_daily_export_markdown_includes_total_prompts_commands_files(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-26",
        name="snapshot-e.json",
        trigger="manual",
        tags=[],
        captured_at="2026-02-26T00:00:00+00:00",
        prompts=["p1"],
        commands=["c1", "c2"],
        files=["f1"],
    )

    payload = snapshot_daily_export_payload(
        scraper, out_path=str(tmp_path / "daily-index"), limit=1000
    )
    markdown_text = Path(payload["source_md"]).read_text(encoding="utf-8")

    assert "- Total prompts:" in markdown_text
    assert "- Total commands:" in markdown_text
    assert "- Total files:" in markdown_text


def test_snapshot_daily_totals_payload_empty_snapshots_returns_zeroes(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)

    totals = snapshot_daily_totals_payload(scraper, limit=1000)

    assert totals["total_days"] == 0
    assert totals["total_snapshots"] == 0
    assert totals["total_prompts"] == 0
    assert totals["total_commands"] == 0
    assert totals["total_files"] == 0
