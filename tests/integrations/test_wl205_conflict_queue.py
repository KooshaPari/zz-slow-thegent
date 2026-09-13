"""Tests for thegent.integrations.conflict_queue — Manual Conflict Queue.

@trace WL-205
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.conflict_queue import (
    ConflictEntry,
    ConflictQueue,
    classify_conflict,
)


@pytest.fixture
def queue() -> ConflictQueue:
    """Provide a ConflictQueue instance."""
    return ConflictQueue()


class TestConflictEntryCreation:
    """Test ConflictEntry dataclass creation."""

    @pytest.mark.requirement("WL-205")
    def test_create_conflict_entry(self) -> None:
        """Can create a ConflictEntry with required fields."""
        now = datetime.now(UTC)
        entry = ConflictEntry(
            conflict_id="CONF-001",
            wl_id="WL-001",
            field="title",
            local_value="My Title",
            remote_value="Remote Title",
            connector="github",
            created_at=now,
        )

        assert entry.conflict_id == "CONF-001"
        assert entry.wl_id == "WL-001"
        assert entry.field == "title"
        assert entry.local_value == "My Title"
        assert entry.remote_value == "Remote Title"
        assert entry.connector == "github"
        assert entry.created_at == now
        assert entry.resolved is False

    @pytest.mark.requirement("WL-205")
    def test_create_conflict_entry_resolved(self) -> None:
        """Can create a ConflictEntry with resolved=True."""
        now = datetime.now(UTC)
        entry = ConflictEntry(
            conflict_id="CONF-001",
            wl_id="WL-001",
            field="title",
            local_value="My Title",
            remote_value="Remote Title",
            connector="github",
            created_at=now,
            resolved=True,
        )

        assert entry.resolved is True


class TestConflictQueueInit:
    """Test ConflictQueue initialization."""

    @pytest.mark.requirement("WL-205")
    def test_init_creates_empty_queue(self) -> None:
        """ConflictQueue initializes as empty."""
        queue = ConflictQueue()

        assert queue.size() == 0
        assert queue.pending() == []
        assert queue.all_entries() == []


class TestConflictQueueEnqueue:
    """Test ConflictQueue.enqueue operations."""

    @pytest.mark.requirement("WL-205")
    def test_enqueue_single_entry(self, queue: ConflictQueue) -> None:
        """enqueue adds entry to queue."""
        now = datetime.now(UTC)
        entry = ConflictEntry(
            conflict_id="CONF-001",
            wl_id="WL-001",
            field="title",
            local_value="Local",
            remote_value="Remote",
            connector="github",
            created_at=now,
        )

        queue.enqueue(entry)

        assert queue.size() == 1
        assert len(queue.all_entries()) == 1
        queued = queue.all_entries()[0]
        assert queued.category == "content_drift"
        assert queued.severity == "medium"
        assert queued.owner_domain == "source-control"

    @pytest.mark.requirement("WL-269")
    def test_enqueue_assigns_state_conflict_high_severity(self, queue: ConflictQueue) -> None:
        """enqueue classifies status/priority conflicts as high severity."""
        now = datetime.now(UTC)
        entry = ConflictEntry(
            conflict_id="CONF-STATE",
            wl_id="WL-401",
            field="status",
            local_value="BACKLOG",
            remote_value="COMPLETED",
            connector="linear",
            created_at=now,
        )
        queue.enqueue(entry)
        queued = queue.all_entries()[0]
        assert queued.category == "state_divergence"
        assert queued.severity == "high"
        assert queued.owner_domain == "planning"


class TestConflictClassification:
    """Test conflict triage classifier utility."""

    @pytest.mark.requirement("WL-269")
    def test_classify_conflict_for_schema_field(self) -> None:
        category, severity, owner = classify_conflict(field="custom_field", connector="jira", wl_id="WL-300")
        assert category == "schema_mismatch"
        assert severity == "low"
        assert owner == "operations"

    @pytest.mark.requirement("WL-205")
    def test_enqueue_multiple_entries(self, queue: ConflictQueue) -> None:
        """enqueue can add multiple entries."""
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        assert queue.size() == 3

    @pytest.mark.requirement("WL-205")
    def test_enqueue_none_raises_error(self, queue: ConflictQueue) -> None:
        """enqueue raises ValueError for None entry."""
        with pytest.raises(ValueError, match="entry cannot be None"):
            queue.enqueue(None)  # type: ignore

    @pytest.mark.requirement("WL-205")
    def test_enqueue_empty_conflict_id_raises_error(self, queue: ConflictQueue) -> None:
        """enqueue raises ValueError for empty conflict_id."""
        now = datetime.now(UTC)
        entry = ConflictEntry(
            conflict_id="",
            wl_id="WL-001",
            field="title",
            local_value="Local",
            remote_value="Remote",
            connector="github",
            created_at=now,
        )

        with pytest.raises(ValueError, match="conflict_id cannot be empty"):
            queue.enqueue(entry)


class TestConflictQueueDequeue:
    """Test ConflictQueue.dequeue operations."""

    @pytest.fixture
    def queue_with_entries(self) -> ConflictQueue:
        """Provide a ConflictQueue with entries."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        return queue

    @pytest.mark.requirement("WL-205")
    def test_dequeue_returns_first_unresolved(self, queue_with_entries: ConflictQueue) -> None:
        """dequeue returns first unresolved entry in FIFO order."""
        entry = queue_with_entries.dequeue()

        assert entry.conflict_id == "CONF-000"
        assert queue_with_entries.size() == 2

    @pytest.mark.requirement("WL-205")
    def test_dequeue_multiple_times(self, queue_with_entries: ConflictQueue) -> None:
        """dequeue can be called multiple times."""
        ids = []
        while queue_with_entries.size() > 0:
            entry = queue_with_entries.dequeue()
            ids.append(entry.conflict_id)

        assert ids == ["CONF-000", "CONF-001", "CONF-002"]

    @pytest.mark.requirement("WL-205")
    def test_dequeue_empty_raises_error(self) -> None:
        """dequeue raises IndexError when queue is empty."""
        queue = ConflictQueue()

        with pytest.raises(IndexError, match="Cannot dequeue from empty queue"):
            queue.dequeue()

    @pytest.mark.requirement("WL-205")
    def test_dequeue_skips_resolved_entries(self) -> None:
        """dequeue skips resolved entries."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        # Add two entries, mark first as resolved
        entry1 = ConflictEntry(
            conflict_id="CONF-001",
            wl_id="WL-001",
            field="title",
            local_value="Local",
            remote_value="Remote",
            connector="github",
            created_at=now,
            resolved=True,
        )
        entry2 = ConflictEntry(
            conflict_id="CONF-002",
            wl_id="WL-002",
            field="title",
            local_value="Local",
            remote_value="Remote",
            connector="github",
            created_at=now,
        )

        queue.enqueue(entry1)
        queue.enqueue(entry2)

        # Dequeue should return unresolved entry (CONF-002)
        entry = queue.dequeue()
        assert entry.conflict_id == "CONF-002"


class TestConflictQueueResolve:
    """Test ConflictQueue.resolve operations."""

    @pytest.fixture
    def queue_with_entries(self) -> ConflictQueue:
        """Provide a ConflictQueue with entries."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        return queue

    @pytest.mark.requirement("WL-205")
    def test_resolve_marks_as_resolved(self, queue_with_entries: ConflictQueue) -> None:
        """resolve marks entry as resolved."""
        queue_with_entries.resolve("CONF-001")

        # Entry should still be in all_entries but not in pending
        all_entries = queue_with_entries.all_entries()
        pending = queue_with_entries.pending()

        assert len(all_entries) == 3
        assert len(pending) == 2

        resolved_entry = next(e for e in all_entries if e.conflict_id == "CONF-001")
        assert resolved_entry.resolved is True

    @pytest.mark.requirement("WL-205")
    def test_resolve_not_found_raises_error(self, queue_with_entries: ConflictQueue) -> None:
        """resolve raises KeyError for non-existent conflict_id."""
        with pytest.raises(KeyError, match="not found"):
            queue_with_entries.resolve("CONF-999")

    @pytest.mark.requirement("WL-205")
    def test_resolve_empty_id_raises_error(self, queue_with_entries: ConflictQueue) -> None:
        """resolve raises KeyError for empty conflict_id."""
        with pytest.raises(KeyError, match="cannot be empty"):
            queue_with_entries.resolve("")

    @pytest.mark.requirement("WL-205")
    def test_resolve_decreases_size(self, queue_with_entries: ConflictQueue) -> None:
        """resolve decreases pending size."""
        initial_size = queue_with_entries.size()
        queue_with_entries.resolve("CONF-001")

        assert queue_with_entries.size() == initial_size - 1

    @pytest.mark.requirement("WL-205")
    def test_resolve_all_entries(self, queue_with_entries: ConflictQueue) -> None:
        """resolve can mark all entries as resolved."""
        queue_with_entries.resolve("CONF-000")
        queue_with_entries.resolve("CONF-001")
        queue_with_entries.resolve("CONF-002")

        assert queue_with_entries.size() == 0
        assert len(queue_with_entries.all_entries()) == 3


class TestConflictQueuePending:
    """Test ConflictQueue.pending operations."""

    @pytest.mark.requirement("WL-205")
    def test_pending_returns_unresolved_only(self) -> None:
        """pending returns only unresolved entries."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            resolved = i == 1
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
                resolved=resolved,
            )
            queue.enqueue(entry)

        pending = queue.pending()

        assert len(pending) == 2
        assert all(not e.resolved for e in pending)

    @pytest.mark.requirement("WL-205")
    def test_pending_empty_queue(self) -> None:
        """pending returns empty list for empty queue."""
        queue = ConflictQueue()

        assert queue.pending() == []

    @pytest.mark.requirement("WL-205")
    def test_pending_fifo_order(self) -> None:
        """pending returns entries in FIFO order."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        pending = queue.pending()

        ids = [e.conflict_id for e in pending]
        assert ids == ["CONF-000", "CONF-001", "CONF-002"]


class TestConflictQueueAllEntries:
    """Test ConflictQueue.all_entries operations."""

    @pytest.mark.requirement("WL-205")
    def test_all_entries_includes_resolved_and_unresolved(self) -> None:
        """all_entries includes both resolved and unresolved."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            resolved = i == 1
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
                resolved=resolved,
            )
            queue.enqueue(entry)

        all_entries = queue.all_entries()

        assert len(all_entries) == 3

    @pytest.mark.requirement("WL-205")
    def test_all_entries_order(self) -> None:
        """all_entries maintains insertion order."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        all_entries = queue.all_entries()

        ids = [e.conflict_id for e in all_entries]
        assert ids == ["CONF-000", "CONF-001", "CONF-002"]


class TestConflictQueueSize:
    """Test ConflictQueue.size operations."""

    @pytest.mark.requirement("WL-205")
    def test_size_empty_queue(self) -> None:
        """size returns 0 for empty queue."""
        queue = ConflictQueue()

        assert queue.size() == 0

    @pytest.mark.requirement("WL-205")
    def test_size_after_enqueue(self) -> None:
        """size increases with enqueue."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        assert queue.size() == 3

    @pytest.mark.requirement("WL-205")
    def test_size_after_resolve(self) -> None:
        """size decreases with resolve."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        for i in range(3):
            entry = ConflictEntry(
                conflict_id=f"CONF-{i:03d}",
                wl_id=f"WL-{i:03d}",
                field="title",
                local_value="Local",
                remote_value="Remote",
                connector="github",
                created_at=now,
            )
            queue.enqueue(entry)

        queue.resolve("CONF-001")

        assert queue.size() == 2

    @pytest.mark.requirement("WL-205")
    def test_size_ignores_resolved_on_enqueue(self) -> None:
        """size only counts unresolved entries even if added resolved."""
        queue = ConflictQueue()
        now = datetime.now(UTC)

        entry = ConflictEntry(
            conflict_id="CONF-001",
            wl_id="WL-001",
            field="title",
            local_value="Local",
            remote_value="Remote",
            connector="github",
            created_at=now,
            resolved=True,
        )

        queue.enqueue(entry)

        assert queue.size() == 0
