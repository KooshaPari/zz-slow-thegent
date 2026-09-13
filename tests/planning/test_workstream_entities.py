"""Tests for canonical workstream entity operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.planning.workstream_entities import entity_operation


@pytest.mark.requirement("FR-ENT-001")
def test_entity_operation_roundtrip_with_metadata(tmp_path: Path) -> None:
    """Traces to: FR-ENT-001."""
    db_path = tmp_path / "workstream.db"

    created = entity_operation(
        "upsert",
        "workstream_items",
        entity_id="WL-100",
        properties={
            "title": "Past task",
            "source": "manual",
            "priority": "P1",
            "status": "pending",
            "metadata": {"phase": "past", "kind": "spec"},
        },
        db_path=db_path,
    )

    assert created["entity_type"] == "workstream_items"
    assert created["item"]["item_id"] == "WL-100"
    assert created["item"]["metadata"]["phase"] == "past"

    listed = entity_operation("list", "workstream_items", limit=10, db_path=db_path)
    assert listed["count"] == 1
    assert listed["items"][0]["title"] == "Past task"

    searched = entity_operation(
        "search", "workstream_items", query="Past", limit=10, db_path=db_path
    )
    assert searched["count"] == 1
    assert searched["items"][0]["item_id"] == "WL-100"

    imported = entity_operation(
        "import",
        "workstream_items",
        records=[
            {
                "entity_id": "WL-101",
                "title": "Future task",
                "source": "manual",
                "priority": "P2",
                "status": "backlog",
            }
        ],
        db_path=db_path,
    )
    assert imported["count"] == 1
    assert imported["items"][0]["item_id"] == "WL-101"

    deleted = entity_operation(
        "delete", "workstream_items", entity_id="WL-100", db_path=db_path
    )
    assert deleted["deleted"] is True

    remaining = entity_operation("list", "workstream_items", limit=10, db_path=db_path)
    assert remaining["count"] == 1
    assert remaining["items"][0]["item_id"] == "WL-101"


@pytest.mark.requirement("FR-ENT-002")
def test_entity_operation_sync_dispatches_source_batches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Traces to: FR-ENT-002."""
    db_path = tmp_path / "workstream.db"
    work_stream_path = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    work_stream_path.parent.mkdir(parents=True, exist_ok=True)
    work_stream_path.write_text("# Unified Work Stream\n", encoding="utf-8")
    calls: list[str] = []

    class _FakeDB:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.db_path = db_path

        def sync_workstream(self, data: dict[str, object]) -> None:
            calls.append("markdown")

        def sync_from_agileplus(self, session_dir: Path) -> int:
            calls.append("agileplus")
            return 2

        def sync_from_queues(self, session_dir: Path) -> int:
            calls.append("queues")
            return 3

        def close(self) -> None:
            pass

    monkeypatch.setattr("thegent.planning.workstream_entities.WorkstreamDB", _FakeDB)
    monkeypatch.setattr(
        "thegent.planning.workstream_entities.ThegentSettings",
        lambda: type("S", (), {"session_dir": tmp_path})(),
    )
    monkeypatch.setattr(
        "thegent.cli.services.run_workstream_helpers.parse_work_stream_md",
        lambda path: {"backlog": []},
    )

    result = entity_operation(
        "sync", "sessions", source="all", cd=tmp_path, db_path=db_path
    )

    assert result["total"] == 5
    assert calls == ["markdown", "agileplus", "queues"]
