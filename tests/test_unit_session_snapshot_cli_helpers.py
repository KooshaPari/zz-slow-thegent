from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.orchestration.state.session_scraper import SessionScraper
from thegent.orchestration.state.session_snapshot_cli_helpers import (
    snapshot_export_payload,
    snapshot_index_payload,
    snapshot_list_payload,
    snapshot_prune_payload,
    snapshot_triggers_tags_payload,
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


def test_list_payload_shape_count(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000000000000Z-a.json",
        trigger="tool_use",
        tags=["wl155"],
        captured_at="2026-02-22T00:00:00+00:00",
    )
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000100000000Z-b.json",
        trigger="error",
        tags=["wl156", "ops"],
        captured_at="2026-02-22T00:01:00+00:00",
    )

    payload = snapshot_list_payload(scraper, limit=10)

    assert set(payload.keys()) == {"count", "items"}
    assert payload["count"] == 2
    assert isinstance(payload["items"], list)
    assert all(set(item.keys()) == {"path", "trigger", "captured_at", "tags"} for item in payload["items"])


def test_index_payload_includes_top_tags_max_10(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    for idx in range(12):
        tag = f"tag{idx:02d}"
        _write_snapshot(
            scraper,
            day="2026-02-22",
            name=f"snapshot-20260222T001{idx:02d}000000Z-{idx}.json",
            trigger="tool_use",
            tags=[tag],
            captured_at=f"2026-02-22T00:{idx:02d}:00+00:00",
        )

    payload = snapshot_index_payload(scraper, limit=50)

    assert "top_tags" in payload
    assert isinstance(payload["top_tags"], list)
    assert len(payload["top_tags"]) == 10
    assert payload["top_tags"] == [f"tag{idx:02d}" for idx in range(10)]


def test_export_payload_writes_markdown_and_returns_paths(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    source = _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T010000000000Z-export.json",
        trigger="session_change",
        tags=["handoff"],
        captured_at="2026-02-22T01:00:00+00:00",
    )
    output = tmp_path / "exports" / "snapshot-export.md"
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = snapshot_export_payload(scraper, snapshot_path=str(source), out_path=str(output))

    assert payload == {"source": str(source), "output": str(output)}
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "# Session Snapshot:" in content


def test_prune_payload_returns_deleted_count(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    for idx in range(3):
        _write_snapshot(
            scraper,
            day="2026-02-22",
            name=f"snapshot-20260222T020{idx:02d}000000Z-{idx}.json",
            trigger="tool_use",
            tags=["trim"],
            captured_at=f"2026-02-22T02:0{idx}:00+00:00",
        )

    payload = snapshot_prune_payload(scraper, max_keep=1)

    assert payload == {"deleted": 2}


def test_triggers_tags_payload_includes_both_arrays(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T030000000000Z-one.json",
        trigger="manual",
        tags=["alpha", "beta"],
        captured_at="2026-02-22T03:00:00+00:00",
    )
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T030100000000Z-two.json",
        trigger="error",
        tags=["beta", "gamma"],
        captured_at="2026-02-22T03:01:00+00:00",
    )

    payload = snapshot_triggers_tags_payload(scraper, limit=20)

    assert set(payload.keys()) == {"triggers", "tags"}
    assert payload["triggers"] == ["error", "manual"]
    assert payload["tags"] == ["alpha", "beta", "gamma"]
