from __future__ import annotations

from pathlib import Path

import orjson as json

import thegent.orchestration.state.session_snapshot_cli_helpers as helpers
from thegent.orchestration.state.session_scraper import SessionScraper


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


def test_daily_index_payload_contains_days_sorted_desc(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-20",
        name="snapshot-20260220T010000000000Z-a.json",
        trigger="tool_use",
        tags=["t1"],
        captured_at="2026-02-20T01:00:00+00:00",
    )
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T020000000000Z-b.json",
        trigger="tool_use",
        tags=["t2"],
        captured_at="2026-02-22T02:00:00+00:00",
    )
    _write_snapshot(
        scraper,
        day="2026-02-21",
        name="snapshot-20260221T030000000000Z-c.json",
        trigger="tool_use",
        tags=["t3"],
        captured_at="2026-02-21T03:00:00+00:00",
    )

    payload = helpers.snapshot_daily_index_payload(scraper, limit=1000)

    assert [item["day"] for item in payload["days"]] == [
        "2026-02-22",
        "2026-02-21",
        "2026-02-20",
    ]


def test_daily_export_payload_returns_json_and_markdown_paths(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T040000000000Z-export.json",
        trigger="session_change",
        tags=["daily"],
        captured_at="2026-02-22T04:00:00+00:00",
    )
    out_dir = tmp_path / "daily-exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = helpers.snapshot_daily_export_payload(
        scraper, out_path=str(out_dir), limit=1000
    )

    assert payload["source_json"]
    assert payload["source_md"]
    assert Path(payload["source_json"]).exists()
    assert Path(payload["source_md"]).exists()


def test_list_payload_since_integration_with_real_snapshots(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    older = _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T000000000000Z-old.json",
        trigger="tool_use",
        tags=["wl"],
        captured_at="2026-02-22T00:00:00+00:00",
    )
    newer = _write_snapshot(
        scraper,
        day="2026-02-22",
        name="snapshot-20260222T010000000000Z-new.json",
        trigger="tool_use",
        tags=["wl"],
        captured_at="2026-02-22T01:00:00+00:00",
    )

    payload = helpers.snapshot_list_payload(
        scraper, since="2026-02-22T00:30:00Z", limit=50
    )

    assert payload["count"] == 1
    assert payload["items"][0]["path"] == str(newer)
    assert payload["items"][0]["path"] != str(older)


def test_prune_payload_delegates_to_scraper_prune_snapshots() -> None:
    class _DelegatingScraper:
        def __init__(self) -> None:
            self.calls: list[int] = []

        def prune_snapshots(self, max_keep: int = 500) -> int:
            self.calls.append(max_keep)
            return 7

        def list_snapshots(self, limit: int = 50) -> list[Path]:
            raise AssertionError(
                "snapshot_prune_payload should delegate to prune_snapshots"
            )

    scraper = _DelegatingScraper()
    payload = helpers.snapshot_prune_payload(scraper, max_keep=3)

    assert scraper.calls == [3]
    assert payload == {"deleted": 7}


def test_helpers_handle_missing_optional_methods_gracefully(tmp_path: Path) -> None:
    class _MinimalScraper:
        def __init__(self, default_snapshot_dir: Path) -> None:
            self.default_snapshot_dir = default_snapshot_dir

        def summarize_snapshots(self, limit: int = 200) -> dict[str, object]:
            return {"tag_counts": {}}

        def list_snapshots(
            self, limit: int = 50, trigger: str | None = None, tag: str | None = None
        ) -> list[Path]:
            return []

        def load_snapshot(self, path: Path) -> None:
            return None

        def export_snapshot_markdown(
            self, snapshot_path: Path, out_path: Path | None = None
        ) -> Path:
            raise FileNotFoundError(str(snapshot_path))

    scraper = _MinimalScraper(default_snapshot_dir=tmp_path)

    list_payload = helpers.snapshot_list_payload(scraper, limit=5)
    index_payload = helpers.snapshot_index_payload(scraper, limit=5)
    export_payload = helpers.snapshot_export_payload(
        scraper, snapshot_path="missing.json"
    )
    prune_payload = helpers.snapshot_prune_payload(scraper, max_keep=5)
    tags_payload = helpers.snapshot_triggers_tags_payload(scraper, limit=5)
    daily_index_payload = helpers.snapshot_daily_index_payload(scraper, limit=5)
    daily_export_payload = helpers.snapshot_daily_export_payload(
        scraper, out_path=None, limit=5
    )

    assert list_payload == {"count": 0, "items": []}
    assert index_payload.get("top_tags") == []
    assert export_payload == {"source": "missing.json", "output": None}
    assert prune_payload == {"deleted": 0}
    assert tags_payload == {"triggers": [], "tags": []}
    assert daily_index_payload.get("days") == []
    assert isinstance(daily_export_payload, dict)
    assert "source_json" in daily_export_payload
    assert "source_md" in daily_export_payload
