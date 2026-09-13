from __future__ import annotations

import contextlib
from pathlib import Path

import orjson as json
import pytest

from thegent.orchestration.state.session_scraper import SessionScraper


class _Pane:
    def __init__(self, pane_id: str) -> None:
        self.pane_id = pane_id


def test_collect_snapshot_extracts_structured_fields(monkeypatch, tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)

    sample_capture = """
> add force flag to dex
$ rg --files
fact: dex should always include --search
decision: map continue to resume
edited src/thegent/cli/apps/main.py
tracking #wl155 #session-memory
"""

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.list_tmux_panes",
        lambda: [_Pane("%1")],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.is_claude_code_pane",
        lambda pane: True,
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.capture_tmux_pane",
        lambda pane_id, last_lines=150: sample_capture,
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_claude_history",
        lambda self: [],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_ante_history",
        lambda self: [],
    )

    snapshot = scraper.collect_snapshot(trigger="tool_use")

    assert snapshot.trigger == "tool_use"
    assert "add force flag to dex" in snapshot.prompts
    assert "rg --files" in snapshot.commands
    assert "src/thegent/cli/apps/main.py" in snapshot.files
    assert "dex should always include --search" in snapshot.facts
    assert "map continue to resume" in snapshot.decisions
    assert "wl155" in snapshot.tags
    assert "session-memory" in snapshot.tags
    assert "tmux:%1" in snapshot.sources


def test_persist_snapshot_writes_json(monkeypatch, tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.list_tmux_panes", list)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_claude_history",
        lambda self: ["p1"],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_ante_history",
        lambda self: ["p2"],
    )

    out_dir = tmp_path / "snapshots"
    path = scraper.persist_snapshot(trigger="periodic", out_dir=out_dir)

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["trigger"] == "periodic"
    assert data["prompts"] == ["p1", "p2"]
    assert data["sources"] == ["claude-history", "ante-history"]


def test_persist_snapshot_emits_created_event(monkeypatch, tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    event_log = tmp_path / "events.jsonl"

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.list_tmux_panes", list)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_claude_history",
        lambda self: ["p1"],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_ante_history",
        lambda self: [],
    )

    request_id = "req-123"
    snapshot_path = scraper.persist_snapshot(
        trigger="hook:pre-commit",
        out_dir=tmp_path / "snapshots",
        request_event_id=request_id,
        event_log=event_log,
    )

    assert snapshot_path.exists()
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) == 1
    event = events[0]
    assert event["event_name"] == "session.scraper.snapshot.created"
    assert event["request_event_id"] == request_id
    assert event["snapshot_path"] == str(snapshot_path)
    assert event["summary"]["prompts"] == 1
    assert event["summary"]["commands"] == 0


def test_persist_snapshot_emits_failed_event(monkeypatch, tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    event_log = tmp_path / "events.jsonl"

    def _raise_collect(self, trigger: str = "manual"):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.collect_snapshot",
        _raise_collect,
    )

    request_id = "req-fail-1"
    with pytest.raises(RuntimeError, match="boom"):
        scraper.persist_snapshot(
            trigger="timer:15m",
            out_dir=tmp_path / "snapshots",
            request_event_id=request_id,
            event_log=event_log,
        )

    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) == 1
    event = events[0]
    assert event["event_name"] == "session.scraper.snapshot.failed"
    assert event["request_event_id"] == request_id
    assert event["error_code"] == "SCRAPER_RUNTIME"
    assert "boom" in event["error_message"]


def test_list_snapshots_filters_by_trigger_and_tag(monkeypatch, tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    payload_a = {
        "snapshot_id": "snapshot-a",
        "trigger": "tool_use",
        "captured_at": "2026-02-22T00:00:00+00:00",
        "project_root": str(tmp_path),
        "prompts": [],
        "commands": [],
        "files": [],
        "facts": [],
        "decisions": [],
        "tags": ["wl155"],
        "sources": [],
    }
    payload_b = {
        **payload_a,
        "snapshot_id": "snapshot-b",
        "trigger": "error",
        "tags": ["wl156"],
    }

    path_a = snapshots_dir / "snapshot-a.json"
    path_b = snapshots_dir / "snapshot-b.json"
    path_a.write_text(json.dumps(payload_a).decode(), encoding="utf-8")
    path_b.write_text(json.dumps(payload_b).decode(), encoding="utf-8")

    tool_use = scraper.list_snapshots(trigger="tool_use", root_dir=snapshots_dir)
    assert len(tool_use) == 1
    assert tool_use[0].name == "snapshot-a.json"

    wl156 = scraper.list_snapshots(tag="wl156", root_dir=snapshots_dir)
    assert len(wl156) == 1
    assert wl156[0].name == "snapshot-b.json"


def test_latest_snapshot_and_markdown_export(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    payload = {
        "snapshot_id": "snapshot-z",
        "trigger": "session_change",
        "captured_at": "2026-02-22T00:00:00+00:00",
        "project_root": str(tmp_path),
        "prompts": ["p"],
        "commands": ["rg --files"],
        "files": ["src/app.py"],
        "facts": ["f"],
        "decisions": ["d"],
        "tags": ["wl156"],
        "sources": ["tmux:%1"],
    }
    json_path = snapshots_dir / "snapshot-z.json"
    json_path.write_text(json.dumps(payload).decode(), encoding="utf-8")

    loaded = scraper.latest_snapshot(root_dir=snapshots_dir)
    assert loaded is not None
    assert loaded.snapshot_id == "snapshot-z"
    assert loaded.trigger == "session_change"

    md_path = scraper.export_snapshot_markdown(json_path)
    content = md_path.read_text(encoding="utf-8")
    assert "# Session Snapshot: snapshot-z" in content
    assert "## Commands" in content
    assert "`rg --files`" in content


def test_summarize_snapshots_and_index_exports(tmp_path: Path) -> None:
    scraper = SessionScraper(project_root=tmp_path)
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    payload_a = {
        "snapshot_id": "snapshot-1",
        "trigger": "tool_use",
        "captured_at": "2026-02-22T00:00:00+00:00",
        "project_root": str(tmp_path),
        "prompts": ["p1", "p2"],
        "commands": ["c1"],
        "files": ["f1.py"],
        "facts": [],
        "decisions": [],
        "tags": ["wl155", "memory"],
        "sources": [],
    }
    payload_b = {
        "snapshot_id": "snapshot-2",
        "trigger": "error",
        "captured_at": "2026-02-22T01:00:00+00:00",
        "project_root": str(tmp_path),
        "prompts": ["p3"],
        "commands": ["c2", "c3"],
        "files": ["f2.py", "f3.py"],
        "facts": [],
        "decisions": [],
        "tags": ["wl156"],
        "sources": [],
    }
    (snapshots_dir / "snapshot-1.json").write_text(json.dumps(payload_a).decode(), encoding="utf-8")
    (snapshots_dir / "snapshot-2.json").write_text(json.dumps(payload_b).decode(), encoding="utf-8")

    summary = scraper.summarize_snapshots(root_dir=snapshots_dir)
    assert summary["total_snapshots"] == 2
    assert summary["total_prompts"] == 3
    assert summary["total_commands"] == 3
    assert summary["total_files"] == 3
    assert summary["trigger_counts"]["tool_use"] == 1
    assert summary["trigger_counts"]["error"] == 1
    assert summary["tag_counts"]["wl155"] == 1
    assert summary["tag_counts"]["wl156"] == 1

    index_json = scraper.persist_snapshot_index(root_dir=snapshots_dir, out_path=tmp_path / "snapshot-index.json")
    assert index_json.exists()
    index_data = json.loads(index_json.read_text(encoding="utf-8"))
    assert index_data["total_snapshots"] == 2

    index_md = scraper.export_snapshot_index_markdown(root_dir=snapshots_dir, out_path=tmp_path / "snapshot-index.md")
    assert index_md.exists()
    md_content = index_md.read_text(encoding="utf-8")
    assert "# Snapshot Index" in md_content
    assert "## Trigger Counts" in md_content
    assert "tool_use: 1" in md_content


def test_snapshot_created_event_payload_schema_validation(monkeypatch, tmp_path: Path) -> None:
    """Validate that emitted snapshot.created event conforms to the schema."""
    scraper = SessionScraper(project_root=tmp_path)
    event_log = tmp_path / "events.jsonl"

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.list_tmux_panes", list)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_claude_history",
        lambda self: ["prompt1"],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_ante_history",
        lambda self: [],
    )

    request_id = "req-evt-001"
    scraper.persist_snapshot(
        trigger="hook:post-test",
        out_dir=tmp_path / "snapshots",
        request_event_id=request_id,
        event_log=event_log,
    )

    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) == 1
    event = events[0]

    # Validate required fields from spec
    assert event["event_name"] == "session.scraper.snapshot.created"
    assert event["version"] == "v1"
    assert "event_id" in event and isinstance(event["event_id"], str)
    assert event["request_event_id"] == request_id
    assert "occurred_at" in event and isinstance(event["occurred_at"], str)
    assert "snapshot_id" in event and event["snapshot_id"].startswith("snapshot-")
    assert "snapshot_path" in event and isinstance(event["snapshot_path"], str)

    # Validate summary structure
    summary = event["summary"]
    assert isinstance(summary["prompts"], int) and summary["prompts"] == 1
    assert isinstance(summary["commands"], int)
    assert isinstance(summary["files"], int)
    assert isinstance(summary["facts"], int)
    assert isinstance(summary["decisions"], int)
    assert isinstance(summary["tags"], int)
    assert isinstance(summary["sources"], list)


def test_snapshot_failed_event_payload_schema_validation(monkeypatch, tmp_path: Path) -> None:
    """Validate that emitted snapshot.failed event conforms to the schema."""
    scraper = SessionScraper(project_root=tmp_path)
    event_log = tmp_path / "events.jsonl"

    def _raise_runtime(self, trigger: str = "manual"):
        raise RuntimeError("test failure message")

    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.collect_snapshot",
        _raise_runtime,
    )

    request_id = "req-evt-fail-001"
    with contextlib.suppress(RuntimeError):
        scraper.persist_snapshot(
            trigger="timer:15m",
            out_dir=tmp_path / "snapshots",
            request_event_id=request_id,
            event_log=event_log,
        )

    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) == 1
    event = events[0]

    # Validate required fields from spec
    assert event["event_name"] == "session.scraper.snapshot.failed"
    assert event["version"] == "v1"
    assert "event_id" in event and isinstance(event["event_id"], str)
    assert event["request_event_id"] == request_id
    assert "occurred_at" in event and isinstance(event["occurred_at"], str)
    assert event["error_code"] in ("SCRAPER_IO", "SCRAPER_PARSE", "SCRAPER_RUNTIME")
    assert isinstance(event["error_message"], str) and "test failure message" in event["error_message"]


def test_trigger_normalization_applied_to_persisted_snapshot(monkeypatch, tmp_path: Path) -> None:
    """Validate that trigger values are normalized in collect_snapshot."""
    scraper = SessionScraper(project_root=tmp_path)
    out_dir = tmp_path / "snapshots"

    monkeypatch.setattr("thegent.orchestration.state.session_scraper.list_tmux_panes", list)
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_claude_history",
        lambda self: [],
    )
    monkeypatch.setattr(
        "thegent.orchestration.state.session_scraper.SessionScraper.scrape_ante_history",
        lambda self: [],
    )

    # Test valid triggers per schema
    for trigger in [
        "manual",
        "hook:pre-commit",
        "hook:post-test",
        "timer:15m",
        "session:end",
    ]:
        path = scraper.persist_snapshot(trigger=trigger, out_dir=out_dir)
        snapshot = scraper.load_snapshot(path)
        assert snapshot is not None
        assert snapshot.trigger == trigger, f"Expected {trigger}, got {snapshot.trigger}"


# noqa: PT018
