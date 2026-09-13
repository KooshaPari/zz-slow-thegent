from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.orchestration.state.session_scraper import SessionScraper


def _snapshot_payload(
    tmp_path: Path,
    snapshot_id: str,
    trigger: str,
    captured_at: str,
    tags: list[str] | None = None,
) -> dict:
    return {
        "snapshot_id": snapshot_id,
        "trigger": trigger,
        "captured_at": captured_at,
        "project_root": str(tmp_path),
        "prompts": [],
        "commands": [],
        "files": [],
        "facts": [],
        "decisions": [],
        "tags": tags or [],
        "sources": [],
    }


def _write_snapshot_json(path: Path, payload: dict, mtime: int) -> None:
    path.write_text(json.dumps(payload).decode(), encoding="utf-8")
    path.touch()
    path.chmod(0o644)
    import os

    os.utime(path, (mtime, mtime))


def test_prune_snapshots_deletes_oldest_and_returns_count(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    root.mkdir()

    p1 = _snapshot_payload(
        tmp_path, "snapshot-1", "manual", "2026-02-22T00:00:00+00:00"
    )
    p2 = _snapshot_payload(
        tmp_path, "snapshot-2", "manual", "2026-02-22T01:00:00+00:00"
    )
    p3 = _snapshot_payload(
        tmp_path, "snapshot-3", "manual", "2026-02-22T02:00:00+00:00"
    )

    f1 = root / "snapshot-1.json"
    f2 = root / "snapshot-2.json"
    f3 = root / "snapshot-3.json"

    _write_snapshot_json(f1, p1, mtime=1)
    _write_snapshot_json(f2, p2, mtime=2)
    _write_snapshot_json(f3, p3, mtime=3)

    deleted = scraper.prune_snapshots(max_keep=2, root_dir=root)

    assert deleted == 1
    assert not f1.exists()
    assert f2.exists()
    assert f3.exists()


def test_list_triggers_returns_unique_triggers(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    root.mkdir()

    snapshots = [
        ("snapshot-a.json", "tool_use", "2026-02-22T00:00:00+00:00", 1),
        ("snapshot-b.json", "manual", "2026-02-22T01:00:00+00:00", 2),
        ("snapshot-c.json", "tool_use", "2026-02-22T02:00:00+00:00", 3),
        ("snapshot-d.json", "error", "2026-02-22T03:00:00+00:00", 4),
    ]

    for filename, trigger, captured_at, mtime in snapshots:
        payload = _snapshot_payload(
            tmp_path, filename.replace(".json", ""), trigger, captured_at
        )
        _write_snapshot_json(root / filename, payload, mtime=mtime)

    assert scraper.list_triggers(root_dir=root) == ["error", "tool_use", "manual"]


def test_list_tags_returns_sorted_tags_by_frequency(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    root.mkdir()

    entries = [
        ("snapshot-1.json", ["alpha", "beta"], 1),
        ("snapshot-2.json", ["alpha", "gamma"], 2),
        ("snapshot-3.json", ["beta", "alpha"], 3),
        ("snapshot-4.json", ["beta", "delta"], 4),
    ]

    for idx, (filename, tags, mtime) in enumerate(entries, start=1):
        payload = _snapshot_payload(
            tmp_path,
            snapshot_id=f"snapshot-{idx}",
            trigger="manual",
            captured_at=f"2026-02-22T0{idx}:00:00+00:00",
            tags=tags,
        )
        _write_snapshot_json(root / filename, payload, mtime=mtime)

    # counts: alpha=3, beta=3, delta=1, gamma=1 -> ties broken by tag name
    assert scraper.list_tags(root_dir=root) == ["alpha", "beta", "delta", "gamma"]


def test_list_snapshots_since_filters_out_older_snapshots(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    root.mkdir()

    entries = [
        ("snapshot-old", "2026-02-22T00:00:00+00:00", 1),
        ("snapshot-mid", "2026-02-22T10:00:00+00:00", 2),
        ("snapshot-new", "2026-02-22T12:00:00+00:00", 3),
    ]

    for snapshot_id, captured_at, mtime in entries:
        payload = _snapshot_payload(tmp_path, snapshot_id, "manual", captured_at)
        _write_snapshot_json(root / f"{snapshot_id}.json", payload, mtime=mtime)

    paths = scraper.list_snapshots(since="2026-02-22T10:00:00+00:00", root_dir=root)

    assert [p.name for p in paths] == ["snapshot-new.json", "snapshot-mid.json"]


def test_invalid_json_files_are_ignored_by_list_and_prune_helpers(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    root.mkdir()

    valid_payload = _snapshot_payload(
        tmp_path,
        snapshot_id="snapshot-valid",
        trigger="manual",
        captured_at="2026-02-22T12:00:00+00:00",
        tags=["ok"],
    )
    valid_path = root / "snapshot-valid.json"
    _write_snapshot_json(valid_path, valid_payload, mtime=10)

    malformed_path = root / "snapshot-bad.json"
    malformed_path.write_text("{not-json", encoding="utf-8")

    list_paths = scraper.list_snapshots(root_dir=root)
    assert [p.name for p in list_paths] == ["snapshot-valid.json"]
    assert scraper.list_triggers(root_dir=root) == ["manual"]
    assert scraper.list_tags(root_dir=root) == ["ok"]

    deleted = scraper.prune_snapshots(max_keep=0, root_dir=root)
    assert deleted == 1
    assert not valid_path.exists()
    assert malformed_path.exists()
