"""Tests for thegent.integrations.dead_letter_replay — Dead-Letter Replay Engine.

@trace WL-214
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from thegent.integrations.dead_letter_queue import DeadLetterEntry, DeadLetterQueue
from thegent.integrations.dead_letter_replay import (
    DeadLetterReplayEngine,
    ReplayResult,
)


class TestReplayResultCreation:
    """Test ReplayResult dataclass creation."""

    @pytest.mark.requirement("WL-214")
    def test_create_success_result(self) -> None:
        """Can create a successful ReplayResult."""
        result = ReplayResult(
            entry_id="DLQ-001",
            success=True,
            error=None,
        )

        assert result.entry_id == "DLQ-001"
        assert result.success is True
        assert result.error is None

    @pytest.mark.requirement("WL-214")
    def test_create_failure_result(self) -> None:
        """Can create a failed ReplayResult."""
        result = ReplayResult(
            entry_id="DLQ-002",
            success=False,
            error="Connection refused",
        )

        assert result.success is False
        assert result.error == "Connection refused"


class TestDeadLetterReplayEngineInit:
    """Test DeadLetterReplayEngine initialization."""

    @pytest.mark.requirement("WL-214")
    def test_init_with_dlq(self) -> None:
        """DeadLetterReplayEngine initializes with DLQ."""
        with TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "queue.jsonl"
            dlq = DeadLetterQueue(store_path)
            engine = DeadLetterReplayEngine(dlq)

            assert engine.dlq is dlq


class TestDeadLetterReplayEngineReplayOne:
    """Test DeadLetterReplayEngine.replay_one operations."""

    @pytest.fixture
    def engine_with_entry(
        self,
    ) -> Generator[tuple[DeadLetterReplayEngine, DeadLetterQueue, Path]]:
        """Provide engine with pre-loaded entry."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        dlq = DeadLetterQueue(store_path)

        now = datetime.now(UTC)
        dlq.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-replay-1",
                wl_id="WL-100",
                connector="github",
                operation="write_item",
                payload={"title": "Updated Title"},
                error="Original error",
                created_at=now,
                retry_count=0,
            )
        )

        engine = DeadLetterReplayEngine(dlq)
        yield engine, dlq, store_path
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-214")
    def test_replay_one_success(
        self,
        engine_with_entry: tuple[DeadLetterReplayEngine, DeadLetterQueue, Path],
    ) -> None:
        """replay_one with successful handler returns success."""
        engine, _dlq, _ = engine_with_entry

        def always_succeeds(entry: DeadLetterEntry) -> bool:
            return True

        result = engine.replay_one("DLQ-replay-1", always_succeeds)

        assert result.success is True
        assert result.error is None
        assert result.entry_id == "DLQ-replay-1"

    @pytest.mark.requirement("WL-214")
    def test_replay_one_handler_returns_false(
        self,
        engine_with_entry: tuple[DeadLetterReplayEngine, DeadLetterQueue, Path],
    ) -> None:
        """replay_one with False-returning handler returns failure."""
        engine, _, _ = engine_with_entry

        def always_fails(entry: DeadLetterEntry) -> bool:
            return False

        result = engine.replay_one("DLQ-replay-1", always_fails)

        assert result.success is False
        assert result.error == "Handler returned False"

    @pytest.mark.requirement("WL-214")
    def test_replay_one_handler_raises(
        self,
        engine_with_entry: tuple[DeadLetterReplayEngine, DeadLetterQueue, Path],
    ) -> None:
        """replay_one catches exception from handler."""
        engine, _, _ = engine_with_entry

        def always_raises(entry: DeadLetterEntry) -> bool:
            raise RuntimeError("Handler error")

        result = engine.replay_one("DLQ-replay-1", always_raises)

        assert result.success is False
        assert result.error is not None
        assert "Handler error" in result.error

    @pytest.mark.requirement("WL-214")
    def test_replay_one_entry_not_found(
        self,
        engine_with_entry: tuple[DeadLetterReplayEngine, DeadLetterQueue, Path],
    ) -> None:
        """replay_one with non-existent entry_id returns failure."""
        engine, _, _ = engine_with_entry

        def dummy_handler(entry: DeadLetterEntry) -> bool:
            return True

        result = engine.replay_one("DLQ-nonexistent", dummy_handler)

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error

    @pytest.mark.requirement("WL-214")
    def test_replay_one_marks_retried_on_success(
        self,
        engine_with_entry: tuple[DeadLetterReplayEngine, DeadLetterQueue, Path],
    ) -> None:
        """replay_one increments retry_count on success."""
        engine, dlq, _ = engine_with_entry

        def always_succeeds(entry: DeadLetterEntry) -> bool:
            return True

        engine.replay_one("DLQ-replay-1", always_succeeds)

        reloaded = dlq.read_all()
        assert reloaded[0].retry_count == 1


class TestDeadLetterReplayEngineReplayAll:
    """Test DeadLetterReplayEngine.replay_all operations."""

    @pytest.fixture
    def engine_with_multiple(
        self,
    ) -> Generator[tuple[DeadLetterReplayEngine, DeadLetterQueue]]:
        """Provide engine with multiple pending entries."""
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "queue.jsonl"
        dlq = DeadLetterQueue(store_path, max_retries=3)

        now = datetime.now(UTC)

        # Add 2 pending and 1 resolved
        dlq.enqueue(
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

        dlq.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-p2",
                wl_id="WL-2",
                connector="linear",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=1,
            )
        )

        dlq.enqueue(
            DeadLetterEntry(
                entry_id="DLQ-resolved",
                wl_id="WL-3",
                connector="github",
                operation="write_item",
                payload={},
                error="Error",
                created_at=now,
                retry_count=3,
            )
        )

        engine = DeadLetterReplayEngine(dlq)
        yield engine, dlq
        tmpdir.cleanup()

    @pytest.mark.requirement("WL-214")
    def test_replay_all_processes_pending_only(
        self,
        engine_with_multiple: tuple[DeadLetterReplayEngine, DeadLetterQueue],
    ) -> None:
        """replay_all processes only pending entries."""
        engine, _ = engine_with_multiple

        def always_succeeds(entry: DeadLetterEntry) -> bool:
            return True

        results = engine.replay_all(always_succeeds)

        # Only 2 pending entries should be replayed
        assert len(results) == 2
        entry_ids = {r.entry_id for r in results}
        assert "DLQ-p1" in entry_ids
        assert "DLQ-p2" in entry_ids
        assert "DLQ-resolved" not in entry_ids

    @pytest.mark.requirement("WL-214")
    def test_replay_all_with_mixed_results(
        self,
        engine_with_multiple: tuple[DeadLetterReplayEngine, DeadLetterQueue],
    ) -> None:
        """replay_all handles mixed success/failure results."""
        engine, _ = engine_with_multiple

        success_ids = {"DLQ-p1"}

        def selective_handler(entry: DeadLetterEntry) -> bool:
            return entry.entry_id in success_ids

        results = engine.replay_all(selective_handler)

        assert len(results) == 2
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(successful) == 1
        assert len(failed) == 1


class TestDeadLetterReplayEngineSummary:
    """Test DeadLetterReplayEngine.replay_summary operations."""

    @pytest.mark.requirement("WL-214")
    def test_summary_all_success(self) -> None:
        """replay_summary calculates counts correctly for all success."""
        results = [
            ReplayResult("DLQ-1", success=True),
            ReplayResult("DLQ-2", success=True),
            ReplayResult("DLQ-3", success=True),
        ]

        engine = DeadLetterReplayEngine(DeadLetterQueue(Path("/tmp/test.jsonl")))
        summary = engine.replay_summary(results)

        assert summary["total"] == 3
        assert summary["succeeded"] == 3
        assert summary["failed"] == 0

    @pytest.mark.requirement("WL-214")
    def test_summary_all_failure(self) -> None:
        """replay_summary calculates counts correctly for all failure."""
        results = [
            ReplayResult("DLQ-1", success=False, error="Error 1"),
            ReplayResult("DLQ-2", success=False, error="Error 2"),
        ]

        engine = DeadLetterReplayEngine(DeadLetterQueue(Path("/tmp/test.jsonl")))
        summary = engine.replay_summary(results)

        assert summary["total"] == 2
        assert summary["succeeded"] == 0
        assert summary["failed"] == 2

    @pytest.mark.requirement("WL-214")
    def test_summary_mixed_results(self) -> None:
        """replay_summary handles mixed results."""
        results = [
            ReplayResult("DLQ-1", success=True),
            ReplayResult("DLQ-2", success=False, error="Error"),
            ReplayResult("DLQ-3", success=True),
            ReplayResult("DLQ-4", success=False, error="Error"),
            ReplayResult("DLQ-5", success=True),
        ]

        engine = DeadLetterReplayEngine(DeadLetterQueue(Path("/tmp/test.jsonl")))
        summary = engine.replay_summary(results)

        assert summary["total"] == 5
        assert summary["succeeded"] == 3
        assert summary["failed"] == 2

    @pytest.mark.requirement("WL-214")
    def test_summary_empty_results(self) -> None:
        """replay_summary handles empty results list."""
        results: list[ReplayResult] = []

        engine = DeadLetterReplayEngine(DeadLetterQueue(Path("/tmp/test.jsonl")))
        summary = engine.replay_summary(results)

        assert summary["total"] == 0
        assert summary["succeeded"] == 0
        assert summary["failed"] == 0
