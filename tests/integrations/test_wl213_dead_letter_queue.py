"""Tests for thegent.integrations.dead_letter_queue — Dead-Letter Queue.

@trace WL-213
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from thegent.integrations.dead_letter_queue import DeadLetterEntry, DeadLetterQueue


class TestDeadLetterEntryCreation:
    """Test DeadLetterEntry dataclass creation."""

    @pytest.mark.requirement("WL-213")
    def test_create_entry_minimal(self) -> None:
        """Can create a DeadLetterEntry with required fields."""
        now = datetime.now(UTC)
        entry = DeadLetterEntry(
            entry_id="DLQ-001",
            wl_id="WL-042",
            connector="github",
            operation="write_item",
            payload={"title": "Updated Title"},
            error="Connection timeout",
            created_at=now,
        )

        assert entry.entry_id == "DLQ-001"
        assert entry.wl_id == "WL-042"
        assert entry.connector == "github"
        assert entry.operation == "write_item"
        assert entry.payload == {"title": "Updated Title"}
        assert entry.error == "Connection timeout"
        assert entry.created_at == now
        assert entry.retry_count == 0

    @pytest.mark.requirement("WL-213")
    def test_create_entry_with_retry_count(self) -> None:
        """Can create a DeadLetterEntry with explicit retry_count."""
        now = datetime.now(UTC)
        entry = DeadLetterEntry(
            entry_id="DLQ-002",
            wl_id="WL-043",
            connector="linear",
            operation="sync_field",
            payload={"status": "DONE"},
            error="Authentication failed",
            created_at=now,
            retry_count=2,
        )

        assert entry.retry_count == 2


class TestDeadLetterQueueInit:
    """Test DeadLetterQueue initialization."""

    @pytest.mark.requirement("WL-213")
    def test_init_creates_store_path(self) -> None:
        """DeadLetterQueue init creates parent directories."""
        with TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "subdir" / "queue.jsonl"
            dlq = DeadLetterQueue(store_path)

            assert dlq.store_path == store_path
            assert store_path.parent.exists()

    @pytest.mark.requirement("WL-213")
    def test_init_with_custom_max_retries(self) -> None:
        """DeadLetterQueue respects custom max_retries."""
        with TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "queue.jsonl"
            dlq = DeadLetterQueue(store_path, max_retries=5)

            assert dlq.max_retries == 5


class TestDeadLetterQueueEnqueue:
    """Test DeadLetterQueue.enqueue operations."""

    @pytest.fixture
    def dlq(self) -> Generator[tuple[DeadLetterQueue, Path]]:
        """Provide a DeadLetterQueue and temp store path."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        yield DeadLetterQueue(store_path), store_path
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-213")
    def test_enqueue_single_entry(self, dlq: tuple[DeadLetterQueue, Path]) -> None:
        """enqueue persists entry to JSONL file."""
        queue, store_path = dlq
        now = datetime.now(UTC)
        entry = DeadLetterEntry(
            entry_id="DLQ-003",
            wl_id="WL-044",
            connector="github",
            operation="write_item",
            payload={"title": "Test"},
            error="Timeout",
            created_at=now,
        )

        queue.enqueue(entry)

        assert store_path.exists()
        content = store_path.read_text()
        assert "DLQ-003" in content
        assert "WL-044" in content

    @pytest.mark.requirement("WL-213")
    def test_enqueue_multiple_entries(self, dlq: tuple[DeadLetterQueue, Path]) -> None:
        """enqueue appends multiple entries."""
        queue, store_path = dlq
        now = datetime.now(UTC)

        for i in range(3):
            entry = DeadLetterEntry(
                entry_id=f"DLQ-{i}",
                wl_id=f"WL-{100 + i}",
                connector="linear",
                operation="sync_field",
                payload={"field": f"value_{i}"},
                error=f"Error {i}",
                created_at=now,
            )
            queue.enqueue(entry)

        lines = store_path.read_text().strip().split("\n")
        assert len(lines) == 3


class TestDeadLetterQueueRead:
    """Test DeadLetterQueue.read_all operations."""

    @pytest.fixture
    def dlq_with_entries(self) -> Generator[tuple[DeadLetterQueue, Path]]:
        """Provide a DeadLetterQueue with pre-loaded entries."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        queue = DeadLetterQueue(store_path)

        now = datetime.now(UTC)
        for i in range(3):
            entry = DeadLetterEntry(
                entry_id=f"DLQ-{i}",
                wl_id=f"WL-{i}",
                connector="github" if i % 2 == 0 else "linear",
                operation="write_item",
                payload={"id": i},
                error=f"Error {i}",
                created_at=now,
                retry_count=i % 2,
            )
            queue.enqueue(entry)

        yield queue, store_path
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-213")
    def test_read_all_returns_all_entries(
        self,
        dlq_with_entries: tuple[DeadLetterQueue, Path],
    ) -> None:
        """read_all returns all persisted entries."""
        queue, _ = dlq_with_entries
        all_entries = queue.read_all()

        assert len(all_entries) == 3
        assert all_entries[0].entry_id == "DLQ-0"
        assert all_entries[2].entry_id == "DLQ-2"

    @pytest.mark.requirement("WL-213")
    def test_read_all_empty_queue(self) -> None:
        """read_all returns empty list for non-existent file."""
        with TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "nonexistent.jsonl"
            queue = DeadLetterQueue(store_path)

            all_entries = queue.read_all()

            assert all_entries == []


class TestDeadLetterQueuePending:
    """Test DeadLetterQueue.pending operations."""

    @pytest.fixture
    def dlq_with_mixed_retries(self) -> Generator[tuple[DeadLetterQueue, Path]]:
        """Provide DLQ with both pending and resolved entries."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        queue = DeadLetterQueue(store_path, max_retries=3)

        now = datetime.now(UTC)

        # Entry with 0 retries (pending)
        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-pending-1",
                wl_id="WL-1",
                connector="github",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=0,
            )
        )

        # Entry with 2 retries (pending)
        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-pending-2",
                wl_id="WL-2",
                connector="github",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=2,
            )
        )

        # Entry with 3 retries (resolved)
        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-resolved-1",
                wl_id="WL-3",
                connector="linear",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=3,
            )
        )

        yield queue, store_path
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-213")
    def test_pending_filters_by_retry_count(
        self,
        dlq_with_mixed_retries: tuple[DeadLetterQueue, Path],
    ) -> None:
        """pending returns only entries with retry_count < max_retries."""
        queue, _ = dlq_with_mixed_retries
        pending = queue.pending()

        assert len(pending) == 2
        pending_ids = {e.entry_id for e in pending}
        assert "DLQ-pending-1" in pending_ids
        assert "DLQ-pending-2" in pending_ids
        assert "DLQ-resolved-1" not in pending_ids


class TestDeadLetterQueueMarkRetried:
    """Test DeadLetterQueue.mark_retried operations."""

    @pytest.fixture
    def dlq_single_entry(self) -> Generator[tuple[DeadLetterQueue, Path]]:
        """Provide DLQ with single entry."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        queue = DeadLetterQueue(store_path)

        now = datetime.now(UTC)
        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-test",
                wl_id="WL-1",
                connector="github",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=0,
            )
        )

        yield queue, store_path
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-213")
    def test_mark_retried_increments_count(
        self,
        dlq_single_entry: tuple[DeadLetterQueue, Path],
    ) -> None:
        """mark_retried increments retry_count and persists."""
        queue, _store_path = dlq_single_entry

        queue.mark_retried("DLQ-test")

        # Re-read from disk to verify persistence
        reloaded = queue.read_all()
        assert len(reloaded) == 1
        assert reloaded[0].retry_count == 1

    @pytest.mark.requirement("WL-213")
    def test_mark_retried_not_found(
        self,
        dlq_single_entry: tuple[DeadLetterQueue, Path],
    ) -> None:
        """mark_retried raises ValueError for missing entry."""
        queue, _ = dlq_single_entry

        with pytest.raises(ValueError, match="not found"):
            queue.mark_retried("DLQ-nonexistent")


class TestDeadLetterQueuePurgeResolved:
    """Test DeadLetterQueue.purge_resolved operations."""

    @pytest.fixture
    def dlq_with_resolved(self) -> Generator[tuple[DeadLetterQueue, Path]]:
        """Provide DLQ with mix of pending and resolved entries."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        queue = DeadLetterQueue(store_path, max_retries=2)

        now = datetime.now(UTC)

        # Pending
        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-p1",
                wl_id="WL-1",
                connector="github",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=0,
            )
        )

        # Resolved (retry_count >= max_retries)
        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-r1",
                wl_id="WL-2",
                connector="github",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=2,
            )
        )

        queue.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-r2",
                wl_id="WL-3",
                connector="linear",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=3,
            )
        )

        yield queue, store_path
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-213")
    def test_purge_resolved_removes_entries(
        self,
        dlq_with_resolved: tuple[DeadLetterQueue, Path],
    ) -> None:
        """purge_resolved removes and returns count of resolved entries."""
        queue, _ = dlq_with_resolved

        count_removed = queue.purge_resolved()

        assert count_removed == 2
        remaining = queue.read_all()
        assert len(remaining) == 1
        assert remaining[0].entry_id == "DLQ-p1"

    @pytest.mark.requirement("WL-213")
    def test_purge_resolved_empty_queue(self) -> None:
        """purge_resolved on empty queue returns 0."""
        with TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "queue.jsonl"
            queue = DeadLetterQueue(store_path)

            count_removed = queue.purge_resolved()

            assert count_removed == 0
