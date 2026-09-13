from __future__ import annotations

import contextlib
from pathlib import Path

import orjson as json

from thegent.orchestration.state.session_scraper import SessionScraper


def _snapshot_payload(
    tmp_path: Path,
    snapshot_id: str,
    captured_at: str,
    prompts: list[str],
    commands: list[str],
    files: list[str],
) -> dict:
    return {
        "snapshot_id": snapshot_id,
        "trigger": "manual",
        "captured_at": captured_at,
        "project_root": str(tmp_path),
        "prompts": prompts,
        "commands": commands,
        "files": files,
        "facts": [],
        "decisions": [],
        "tags": [],
        "sources": [],
    }


def _write_snapshot(path: Path, payload: dict, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload).decode(), encoding="utf-8")
    import os

    os.utime(path, (mtime, mtime))


def test_summarize_snapshots_by_day_aggregates_counts_across_two_dates(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"

    _write_snapshot(
        root / "2026-02-20" / "snapshot-1.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-1",
            captured_at="2026-02-20T01:00:00+00:00",
            prompts=["p1", "p2"],
            commands=["c1"],
            files=["a.py"],
        ),
        mtime=1,
    )
    _write_snapshot(
        root / "2026-02-20" / "snapshot-2.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-2",
            captured_at="2026-02-20T09:00:00+00:00",
            prompts=["p3"],
            commands=["c2", "c3"],
            files=["b.py", "c.py"],
        ),
        mtime=2,
    )
    _write_snapshot(
        root / "2026-02-21" / "snapshot-3.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-3",
            captured_at="2026-02-21T12:00:00+00:00",
            prompts=[],
            commands=["c4"],
            files=[],
        ),
        mtime=3,
    )

    summary = scraper.summarize_snapshots_by_day(root_dir=root)

    assert summary == {
        "2026-02-20": {"snapshots": 2, "prompts": 3, "commands": 3, "files": 3},
        "2026-02-21": {"snapshots": 1, "prompts": 0, "commands": 1, "files": 0},
    }


def test_daily_summary_skips_malformed_snapshot_json(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"

    _write_snapshot(
        root / "2026-02-22" / "snapshot-valid.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-valid",
            captured_at="2026-02-22T10:00:00+00:00",
            prompts=["p1"],
            commands=["c1"],
            files=["ok.py"],
        ),
        mtime=10,
    )
    malformed = root / "2026-02-22" / "snapshot-bad.json"
    malformed.write_text("{not-json", encoding="utf-8")

    summary = scraper.summarize_snapshots_by_day(root_dir=root)

    assert summary == {
        "2026-02-22": {"snapshots": 1, "prompts": 1, "commands": 1, "files": 1},
    }


def test_persist_snapshot_daily_index_writes_expected_json_structure(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    out_path = tmp_path / "snapshot-daily-index.json"

    _write_snapshot(
        root / "2026-02-23" / "snapshot-1.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-1",
            captured_at="2026-02-23T08:00:00+00:00",
            prompts=["p1", "p2"],
            commands=["c1"],
            files=["x.py", "y.py"],
        ),
        mtime=20,
    )

    json_path = scraper.persist_snapshot_daily_index(root_dir=root, out_path=out_path)

    assert json_path == out_path
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data == {
        "2026-02-23": {"snapshots": 1, "prompts": 2, "commands": 1, "files": 2},
    }


def test_export_snapshot_daily_index_markdown_writes_file_with_daily_headers_and_metrics(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "snapshots"
    out_path = tmp_path / "snapshot-daily-index.md"

    _write_snapshot(
        root / "2026-02-24" / "snapshot-a.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-a",
            captured_at="2026-02-24T07:00:00+00:00",
            prompts=["p1"],
            commands=["c1", "c2"],
            files=["a.py"],
        ),
        mtime=30,
    )
    _write_snapshot(
        root / "2026-02-25" / "snapshot-b.json",
        _snapshot_payload(
            tmp_path,
            snapshot_id="snapshot-b",
            captured_at="2026-02-25T07:00:00+00:00",
            prompts=["p2", "p3"],
            commands=["c3"],
            files=["b.py", "c.py"],
        ),
        mtime=31,
    )

    md_path = scraper.export_snapshot_daily_index_markdown(root_dir=root, out_path=out_path)
    content = md_path.read_text(encoding="utf-8")

    assert md_path == out_path
    assert "# Snapshot Daily Index" in content
    assert "- `2026-02-25 | 1 | 2 | 1 | 2`" in content
    assert "- `2026-02-24 | 1 | 1 | 2 | 1`" in content


def test_empty_directory_returns_empty_daily_summary_and_exports_valid_markdown(
    tmp_path: Path,
) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    root = tmp_path / "empty-snapshots"
    root.mkdir()
    out_path = tmp_path / "empty-daily-index.md"

    summary = scraper.summarize_snapshots_by_day(root_dir=root)
    md_path = scraper.export_snapshot_daily_index_markdown(root_dir=root, out_path=out_path)
    content = md_path.read_text(encoding="utf-8")

    assert summary == {}
    assert md_path.exists()
    assert "# Snapshot Daily Index" in content
    assert "- (none)" in content


def test_request_event_id_propagation_from_request_to_created_and_failed_events(monkeypatch, tmp_path: Path) -> None:
    """
    WL-156 Regression: Validate request_event_id propagates from persist_snapshot request
    through to both snapshot.created and snapshot.failed events.
    """
    scraper = SessionScraper(project_root=tmp_path)
    event_log_created = tmp_path / "events-created.jsonl"
    event_log_failed = tmp_path / "events-failed.jsonl"

    # Test 1: request_event_id propagation on SUCCESS
    monkeypatch.setattr("thegent.orchestration.state.session_scraper.list_tmux_panes", list)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_claude_history",
        lambda self: ["p1"],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_ante_history",
        lambda self: [],
    )

    request_id_success = "req-propagation-success-001"
    scraper.persist_snapshot(
        trigger="manual",
        out_dir=tmp_path / "snapshots-success",
        request_event_id=request_id_success,
        event_log=event_log_created,
    )

    events_created = [
        json.loads(line) for line in event_log_created.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(events_created) == 1
    assert events_created[0]["event_name"] == "session.scraper.snapshot.created"
    assert events_created[0]["request_event_id"] == request_id_success
    assert events_created[0]["event_id"] != request_id_success, "event_id should be distinct from request_event_id"

    # Test 2: request_event_id propagation on FAILURE
    def _raise_on_collect(self, trigger: str = "manual"):
        raise OSError("simulated IO error")

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.collect_snapshot",
        _raise_on_collect,
    )

    request_id_fail = "req-propagation-fail-001"
    with contextlib.suppress(OSError):
        scraper.persist_snapshot(
            trigger="hook:pre-commit",
            out_dir=tmp_path / "snapshots-failed",
            request_event_id=request_id_fail,
            event_log=event_log_failed,
        )

    events_failed = [
        json.loads(line) for line in event_log_failed.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(events_failed) == 1
    assert events_failed[0]["event_name"] == "session.scraper.snapshot.failed"
    assert events_failed[0]["request_event_id"] == request_id_fail
    assert events_failed[0]["event_id"] != request_id_fail, "event_id should be distinct from request_event_id"
