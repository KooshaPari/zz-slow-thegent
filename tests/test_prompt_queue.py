"""Unit tests for PromptQueue (WP-7001) and PromptQueueManager (FR-HAX-001)."""

# @trace FR-HAX-001

from pathlib import Path

import pytest

from thegent.core.prompt_queue import PromptQueueManager
from thegent.queue.storage import PromptQueue


@pytest.fixture
def queue_dir(tmp_path: Path) -> Path:
    return tmp_path / "sessions"


@pytest.fixture
def queue(queue_dir: Path) -> PromptQueue:
    return PromptQueue(queue_dir)


@pytest.fixture
def pqm(tmp_path: Path) -> PromptQueueManager:
    """PromptQueueManager with an isolated queue file."""
    queue_file = tmp_path / "prompt_queue.jsonl"
    return PromptQueueManager(queue_path=queue_file)


def test_append_and_list_pending(queue: PromptQueue) -> None:
    queue.append("First task", "proj1")
    queue.append("Second task", "proj1")
    pending = queue.list_pending()
    assert len(pending) == 2
    assert pending[0]["prompt"] == "First task"
    assert pending[1]["prompt"] == "Second task"


def test_list_all_includes_ids(queue: PromptQueue) -> None:
    queue.append("A", "p1")
    queue.append("B", "p1")
    items = queue.list_all(include_done=True)
    assert len(items) == 2
    assert items[0]["id"] == 0
    assert items[1]["id"] == 1


def test_claim_returns_first_pending(queue: PromptQueue) -> None:
    queue.append("Task 1", "proj")
    queue.append("Task 2", "proj")
    claimed = queue.claim("worker-1", project="proj")
    assert claimed is not None
    assert claimed["prompt"] == "Task 1"
    assert claimed["claimed_by"] == "worker-1"
    assert claimed["status"] == "claimed"
    assert claimed["id"] == 0


def test_claim_filters_by_project(queue: PromptQueue) -> None:
    queue.append("P1 task", "proj1")
    queue.append("P2 task", "proj2")
    claimed = queue.claim("w", project="proj2")
    assert claimed is not None
    assert claimed["prompt"] == "P2 task"


def test_claim_empty_returns_none(queue: PromptQueue) -> None:
    assert queue.claim("w") is None


def test_done_marks_item(queue: PromptQueue) -> None:
    queue.append("X", "p")
    claimed = queue.claim("w")
    assert claimed is not None
    assert queue.done(claimed["id"]) is True
    items = queue.list_all(include_done=True)
    assert items[0]["status"] == "done"


def test_release_returns_to_pending(queue: PromptQueue) -> None:
    queue.append("Y", "p")
    claimed = queue.claim("w")
    assert claimed is not None
    assert queue.release(claimed["id"]) is True
    pending = queue.list_pending()
    assert len(pending) == 1
    assert pending[0]["prompt"] == "Y"


def test_extend_lease(queue: PromptQueue) -> None:
    queue.append("Z", "p")
    claimed = queue.claim("w", lease_seconds=60)
    assert claimed is not None
    assert queue.extend_lease(claimed["id"], lease_seconds=120) is True
    items = queue.list_all(include_done=True)
    assert "lease_expires_at" in items[0]


def test_edit_pending(queue: PromptQueue) -> None:
    queue.append("Original", "p")
    assert queue.edit(0, "Updated") is True
    pending = queue.list_pending()
    assert pending[0]["prompt"] == "Updated"


def test_edit_claimed(queue: PromptQueue) -> None:
    queue.append("Original", "p")
    queue.claim("w")
    assert queue.edit(0, "Updated") is True
    items = queue.list_all(include_done=True)
    assert items[0]["prompt"] == "Updated"


def test_edit_done_fails(queue: PromptQueue) -> None:
    queue.append("X", "p")
    queue.claim("w")
    queue.done(0)
    assert queue.edit(0, "Y") is False


def test_get_pending_count(queue: PromptQueue) -> None:
    assert queue.get_pending_count() == 0
    queue.append("A", "p")
    assert queue.get_pending_count() == 1
    queue.claim("w")
    assert queue.get_pending_count() == 0


# ---------------------------------------------------------------------------
# PromptQueueManager tests (FR-HAX-001)
# ---------------------------------------------------------------------------


def test_pqm_enqueue_and_list_pending(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: enqueue creates a pending item."""
    # @trace FR-HAX-001
    item = pqm.enqueue("First task", project_path="/proj/alpha")
    assert item.status == "pending"
    assert item.prompt == "First task"
    assert item.project_path == "/proj/alpha"
    assert len(item.id) == 26  # ULID length

    pending = pqm.list_pending()
    assert len(pending) == 1
    assert pending[0].prompt == "First task"


def test_pqm_enqueue_multiple_items(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: multiple items accumulate in order."""
    # @trace FR-HAX-001
    pqm.enqueue("Task A", project_path="/proj/a")
    pqm.enqueue("Task B", project_path="/proj/b")
    pending = pqm.list_pending()
    assert len(pending) == 2
    assert pending[0].prompt == "Task A"
    assert pending[1].prompt == "Task B"


def test_pqm_claim_returns_first_pending(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: claim() returns the oldest pending item and marks it claimed."""
    # @trace FR-HAX-001
    pqm.enqueue("Alpha", project_path="/proj")
    pqm.enqueue("Beta", project_path="/proj")

    claimed = pqm.claim()
    assert claimed is not None
    assert claimed.prompt == "Alpha"
    assert claimed.status == "claimed"

    pending = pqm.list_pending()
    assert len(pending) == 1
    assert pending[0].prompt == "Beta"


def test_pqm_claim_empty_returns_none(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: claim() on empty queue returns None."""
    # @trace FR-HAX-001
    assert pqm.claim() is None


def test_pqm_complete_marks_done(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: complete() marks item as done."""
    # @trace FR-HAX-001
    pqm.enqueue("Task X", project_path="/proj")
    claimed = pqm.claim()
    assert claimed is not None

    result = pqm.complete(claimed.id)
    assert result is True

    all_items = pqm.list_all(include_done=True)
    assert len(all_items) == 1
    assert all_items[0].status == "done"


def test_pqm_complete_unknown_id_returns_false(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: complete() with unknown id returns False."""
    # @trace FR-HAX-001
    assert pqm.complete("NONEXISTENT00000000000000") is False


def test_pqm_id_is_ulid_format(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: item IDs are ULID-compatible (26 chars, uppercase alphanumeric)."""
    # @trace FR-HAX-001
    item = pqm.enqueue("Test prompt", project_path="/proj")
    assert len(item.id) == 26
    assert item.id.upper() == item.id
    assert item.id.isalnum()


def test_pqm_ids_are_unique(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: each enqueued item receives a unique ID."""
    # @trace FR-HAX-001
    items = [pqm.enqueue(f"Task {i}", project_path="/proj") for i in range(5)]
    ids = [item.id for item in items]
    assert len(set(ids)) == 5


def test_pqm_list_all_excludes_done_by_default(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: list_all() excludes done items unless include_done=True."""
    # @trace FR-HAX-001
    pqm.enqueue("Keep", project_path="/proj")
    claimed = pqm.claim()
    assert claimed is not None
    pqm.complete(claimed.id)

    visible = pqm.list_all(include_done=False)
    assert len(visible) == 0

    all_items = pqm.list_all(include_done=True)
    assert len(all_items) == 1


def test_pqm_timestamp_is_iso8601(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: timestamp field is an ISO-8601 UTC string."""
    # @trace FR-HAX-001
    from datetime import datetime

    item = pqm.enqueue("Timestamp test", project_path="/proj")
    # Should parse without error
    dt = datetime.fromisoformat(item.timestamp)
    assert dt is not None


def test_pqm_enqueue_persists_metadata(pqm: PromptQueueManager) -> None:
    """FR-HAX-001: enqueue() stores structured metadata fields."""
    # @trace WL-096
    item = pqm.enqueue(
        "Revise output",
        project_path="/proj/revision",
        metadata={"vetter_revision": True, "original_run_id": "run-1", "round": 2},
    )
    assert item.metadata["vetter_revision"] is True
    assert item.metadata["original_run_id"] == "run-1"
    assert item.metadata["round"] == 2

    claimed = pqm.claim()
    assert claimed is not None
    assert claimed.metadata["vetter_revision"] is True
    assert claimed.metadata["original_run_id"] == "run-1"
    assert claimed.metadata["round"] == 2


def test_pqm_from_dict_defaults_missing_metadata(tmp_path: Path) -> None:
    """FR-HAX-001: queue lines without metadata remain readable."""
    # @trace WL-096
    queue_file = tmp_path / "prompt_queue.jsonl"
    queue_file.write_text(
        '{"id":"A","timestamp":"2026-02-21T00:00:00+00:00","prompt":"x","project_path":"/p","status":"pending"}\n',
        encoding="utf-8",
    )
    pqm = PromptQueueManager(queue_path=queue_file)
    items = pqm.list_pending()
    assert len(items) == 1
    assert items[0].metadata == {}
