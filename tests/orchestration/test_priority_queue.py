"""Tests for RunPriorityQueue (swarm-priority-queue).

@trace FR-ORC-PQ-001 -- QueuedRun dataclass fields and defaults.
@trace FR-ORC-PQ-002 -- QueuedRun.from_lane sets priority_score from LaneModel.
@trace FR-ORC-PQ-003 -- put/get ordering respects priority_score (lower first).
@trace FR-ORC-PQ-004 -- FIFO within the same priority_score.
@trace FR-ORC-PQ-005 -- cancel removes a specific run; returns True/False.
@trace FR-ORC-PQ-006 -- drain returns all items in priority order and empties queue.
@trace FR-ORC-PQ-007 -- peek returns next item without removing it.
@trace FR-ORC-PQ-008 -- empty/full/qsize reflect queue state accurately.
@trace FR-ORC-PQ-009 -- maxsize=0 is unbounded; maxsize>0 raises Full.
@trace FR-ORC-PQ-010 -- get_nowait raises Empty; put_nowait raises Full.
@trace FR-ORC-PQ-011 -- Thread safety: concurrent put/get from multiple threads.
@trace FR-ORC-PQ-012 -- Timeout raises Empty when no item arrives in time.
@trace FR-ORC-PQ-013 -- make_priority_queue factory returns RunPriorityQueue.
"""

from __future__ import annotations

import threading
import time
from queue import Empty, Full

import pytest

from thegent.orchestration.execution.lanes import LANE_PRIORITIES, Lane, LaneModel
from thegent.orchestration.execution.priority_queue import (
    QueuedRun,
    RunPriorityQueue,
    make_priority_queue,
)

# ---------------------------------------------------------------------------
# QueuedRun dataclass
# ---------------------------------------------------------------------------


class TestQueuedRun:
    """Unit tests for QueuedRun. @trace FR-ORC-PQ-001"""

    def test_fields_stored(self) -> None:  # @trace FR-ORC-PQ-001
        run = QueuedRun(run_id="r1", lane="standard", priority_score=10)
        assert run.run_id == "r1"
        assert run.lane == "standard"
        assert run.priority_score == 10

    def test_enqueued_at_default_monotonic(self) -> None:  # @trace FR-ORC-PQ-001
        before = time.monotonic()
        run = QueuedRun(run_id="r2", lane="standard", priority_score=10)
        after = time.monotonic()
        assert before <= run.enqueued_at <= after

    def test_metadata_default_empty_dict(self) -> None:  # @trace FR-ORC-PQ-001
        run = QueuedRun(run_id="r3", lane="standard", priority_score=10)
        assert run.metadata == {}

    def test_metadata_independent_instances(self) -> None:  # @trace FR-ORC-PQ-001
        """Each instance gets its own default dict (no shared-state bug)."""
        r1 = QueuedRun(run_id="a", lane="standard", priority_score=0)
        r2 = QueuedRun(run_id="b", lane="standard", priority_score=0)
        r1.metadata["key"] = "val"
        assert "key" not in r2.metadata

    def test_custom_metadata(self) -> None:  # @trace FR-ORC-PQ-001
        meta = {"owner": "svc-a", "retries": 2}
        run = QueuedRun(run_id="r4", lane="critical", priority_score=0, metadata=meta)
        assert run.metadata == meta


class TestQueuedRunFromLane:
    """Unit tests for QueuedRun.from_lane. @trace FR-ORC-PQ-002"""

    def test_critical_lane_priority(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r1", "critical")
        assert run.priority_score == LANE_PRIORITIES["critical"]  # 0

    def test_standard_lane_priority(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r2", "standard")
        assert run.priority_score == LANE_PRIORITIES["standard"]  # 10

    def test_recovery_lane_priority(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r3", "recovery")
        assert run.priority_score == LANE_PRIORITIES["recovery"]  # 20

    def test_background_lane_priority(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r4", "background")
        assert run.priority_score == LANE_PRIORITIES["background"]  # 100

    def test_unknown_lane_uses_lanemodel_default(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r5", "unknown-lane")
        assert run.priority_score == LaneModel.get_priority("unknown-lane")  # 50

    def test_lane_name_stored(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r6", "background")
        assert run.lane == "background"

    def test_metadata_passed_through(self) -> None:  # @trace FR-ORC-PQ-002
        meta = {"tag": "v1"}
        run = QueuedRun.from_lane("r7", "standard", metadata=meta)
        assert run.metadata == meta

    def test_metadata_none_gives_empty_dict(self) -> None:  # @trace FR-ORC-PQ-002
        run = QueuedRun.from_lane("r8", "standard", metadata=None)
        assert run.metadata == {}

    def test_lane_enum_value_works(self) -> None:  # @trace FR-ORC-PQ-002
        """Lane enum string value is accepted by from_lane."""
        run = QueuedRun.from_lane("r9", Lane.CRITICAL)
        assert run.priority_score == 0


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------


class TestPriorityOrdering:
    """put/get ordering respects priority_score. @trace FR-ORC-PQ-003"""

    def test_lower_score_dequeued_first(self) -> None:  # @trace FR-ORC-PQ-003
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="bg", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="crit", lane="critical", priority_score=0))
        q.put(QueuedRun(run_id="std", lane="standard", priority_score=10))
        assert q.get_nowait().run_id == "crit"
        assert q.get_nowait().run_id == "std"
        assert q.get_nowait().run_id == "bg"

    def test_from_lane_ordering_matches_lanes(self) -> None:  # @trace FR-ORC-PQ-003
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun.from_lane("b", "background"))
        q.put(QueuedRun.from_lane("r", "recovery"))
        q.put(QueuedRun.from_lane("c", "critical"))
        q.put(QueuedRun.from_lane("s", "standard"))
        assert q.get_nowait().run_id == "c"
        assert q.get_nowait().run_id == "s"
        assert q.get_nowait().run_id == "r"
        assert q.get_nowait().run_id == "b"

    def test_single_item_returned_immediately(self) -> None:  # @trace FR-ORC-PQ-003
        q: RunPriorityQueue = RunPriorityQueue()
        run = QueuedRun(run_id="solo", lane="standard", priority_score=10)
        q.put(run)
        assert q.get_nowait().run_id == "solo"

    def test_many_items_sorted(self) -> None:  # @trace FR-ORC-PQ-003
        q: RunPriorityQueue = RunPriorityQueue()
        scores = [50, 1, 99, 10, 3]
        for i, score in enumerate(scores):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=score))
        dequeued_scores = [q.get_nowait().priority_score for _ in scores]
        assert dequeued_scores == sorted(scores)


# ---------------------------------------------------------------------------
# FIFO within same priority
# ---------------------------------------------------------------------------


class TestFIFOSamePriority:
    """FIFO ordering within the same priority_score. @trace FR-ORC-PQ-004"""

    def test_fifo_same_score(self) -> None:  # @trace FR-ORC-PQ-004
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(5):
            q.put(QueuedRun(run_id=f"r{i}", lane="standard", priority_score=10))
        ids = [q.get_nowait().run_id for _ in range(5)]
        assert ids == ["r0", "r1", "r2", "r3", "r4"]

    def test_fifo_across_groups(self) -> None:  # @trace FR-ORC-PQ-004
        """Within each group, insertion order is preserved."""
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="std-1", lane="standard", priority_score=10))
        q.put(QueuedRun(run_id="std-2", lane="standard", priority_score=10))
        q.put(QueuedRun(run_id="bg-1", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="bg-2", lane="background", priority_score=100))
        assert q.get_nowait().run_id == "std-1"
        assert q.get_nowait().run_id == "std-2"
        assert q.get_nowait().run_id == "bg-1"
        assert q.get_nowait().run_id == "bg-2"


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------


class TestCancel:
    """cancel removes a specific run by run_id. @trace FR-ORC-PQ-005"""

    def test_cancel_existing_returns_true(self) -> None:  # @trace FR-ORC-PQ-005
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=10))
        assert q.cancel("a") is True

    def test_cancel_nonexistent_returns_false(self) -> None:  # @trace FR-ORC-PQ-005
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.cancel("ghost") is False

    def test_cancel_removes_item_from_queue(self) -> None:  # @trace FR-ORC-PQ-005
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="keep", lane="standard", priority_score=10))
        q.put(QueuedRun(run_id="drop", lane="standard", priority_score=10))
        q.cancel("drop")
        assert q.qsize() == 1
        assert q.get_nowait().run_id == "keep"

    def test_cancel_middle_item_preserves_order(self) -> None:  # @trace FR-ORC-PQ-005
        q: RunPriorityQueue = RunPriorityQueue()
        for rid in ["a", "b", "c"]:
            q.put(QueuedRun(run_id=rid, lane="standard", priority_score=10))
        q.cancel("b")
        remaining = q.qsize()
        ids = [q.get_nowait().run_id for _ in range(remaining)]
        assert ids == ["a", "c"]

    def test_cancel_only_first_match(self) -> None:  # @trace FR-ORC-PQ-005
        """If run_id is unique (as required), cancel removes exactly one item."""
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="dup", lane="standard", priority_score=10))
        q.put(QueuedRun(run_id="other", lane="standard", priority_score=10))
        result = q.cancel("dup")
        assert result is True
        assert q.qsize() == 1

    def test_cancel_decreases_qsize(self) -> None:  # @trace FR-ORC-PQ-005
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(3):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        q.cancel("1")
        assert q.qsize() == 2


# ---------------------------------------------------------------------------
# drain
# ---------------------------------------------------------------------------


class TestDrain:
    """drain returns all items in priority order. @trace FR-ORC-PQ-006"""

    def test_drain_returns_all_in_priority_order(self) -> None:  # @trace FR-ORC-PQ-006
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="bg", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="crit", lane="critical", priority_score=0))
        q.put(QueuedRun(run_id="std", lane="standard", priority_score=10))
        drained = q.drain()
        assert [r.run_id for r in drained] == ["crit", "std", "bg"]

    def test_drain_empties_queue(self) -> None:  # @trace FR-ORC-PQ-006
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(5):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=10))
        q.drain()
        assert q.empty()
        assert q.qsize() == 0

    def test_drain_empty_queue_returns_empty_list(self) -> None:  # @trace FR-ORC-PQ-006
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.drain() == []

    def test_drain_fifo_within_same_score(self) -> None:  # @trace FR-ORC-PQ-006
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(3):
            q.put(QueuedRun(run_id=f"r{i}", lane="standard", priority_score=10))
        drained = q.drain()
        assert [r.run_id for r in drained] == ["r0", "r1", "r2"]


# ---------------------------------------------------------------------------
# peek
# ---------------------------------------------------------------------------


class TestPeek:
    """peek returns next item without removing it. @trace FR-ORC-PQ-007"""

    def test_peek_returns_highest_priority(self) -> None:  # @trace FR-ORC-PQ-007
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="bg", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="crit", lane="critical", priority_score=0))
        peeked = q.peek()
        assert peeked is not None
        assert peeked.run_id == "crit"

    def test_peek_does_not_remove_item(self) -> None:  # @trace FR-ORC-PQ-007
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="r1", lane="standard", priority_score=10))
        _ = q.peek()
        assert q.qsize() == 1
        assert q.get_nowait().run_id == "r1"

    def test_peek_empty_queue_returns_none(self) -> None:  # @trace FR-ORC-PQ-007
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.peek() is None

    def test_peek_consistent_with_get(self) -> None:  # @trace FR-ORC-PQ-007
        q: RunPriorityQueue = RunPriorityQueue()
        run = QueuedRun(run_id="x", lane="critical", priority_score=0)
        q.put(run)
        peeked = q.peek()
        gotten = q.get_nowait()
        assert peeked is not None
        assert peeked.run_id == gotten.run_id


# ---------------------------------------------------------------------------
# empty / full / qsize
# ---------------------------------------------------------------------------


class TestStatePredicates:
    """empty/full/qsize reflect queue state. @trace FR-ORC-PQ-008"""

    def test_new_queue_is_empty(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.empty() is True

    def test_queue_not_empty_after_put(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="r", lane="standard", priority_score=10))
        assert q.empty() is False

    def test_qsize_zero_initially(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.qsize() == 0

    def test_qsize_increments_on_put(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(4):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.qsize() == 4

    def test_qsize_decrements_on_get(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="r", lane="standard", priority_score=0))
        q.get_nowait()
        assert q.qsize() == 0

    def test_full_false_unbounded(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue(maxsize=0)
        for i in range(1000):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.full() is False

    def test_full_true_when_at_maxsize(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue(maxsize=3)
        for i in range(3):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.full() is True

    def test_full_false_when_below_maxsize(self) -> None:  # @trace FR-ORC-PQ-008
        q: RunPriorityQueue = RunPriorityQueue(maxsize=5)
        q.put(QueuedRun(run_id="r", lane="standard", priority_score=0))
        assert q.full() is False


# ---------------------------------------------------------------------------
# maxsize / bounded queue
# ---------------------------------------------------------------------------


class TestBoundedQueue:
    """maxsize=0 unbounded; maxsize>0 raises Full. @trace FR-ORC-PQ-009"""

    def test_maxsize_zero_is_unbounded(self) -> None:  # @trace FR-ORC-PQ-009
        q: RunPriorityQueue = RunPriorityQueue(maxsize=0)
        for i in range(500):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.qsize() == 500

    def test_put_nowait_raises_full(self) -> None:  # @trace FR-ORC-PQ-009
        q: RunPriorityQueue = RunPriorityQueue(maxsize=2)
        q.put_nowait(QueuedRun(run_id="a", lane="standard", priority_score=0))
        q.put_nowait(QueuedRun(run_id="b", lane="standard", priority_score=0))
        with pytest.raises(Full):
            q.put_nowait(QueuedRun(run_id="c", lane="standard", priority_score=0))

    def test_put_nonblocking_raises_full(self) -> None:  # @trace FR-ORC-PQ-009
        q: RunPriorityQueue = RunPriorityQueue(maxsize=1)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        with pytest.raises(Full):
            q.put(QueuedRun(run_id="b", lane="standard", priority_score=0), block=False)

    def test_put_blocking_timeout_raises_full(self) -> None:  # @trace FR-ORC-PQ-009
        q: RunPriorityQueue = RunPriorityQueue(maxsize=1)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        start = time.monotonic()
        with pytest.raises(Full):
            q.put(
                QueuedRun(run_id="b", lane="standard", priority_score=0),
                block=True,
                timeout=0.1,
            )
        elapsed = time.monotonic() - start
        assert elapsed >= 0.08  # waited approximately the timeout

    def test_space_freed_after_get_allows_put(self) -> None:  # @trace FR-ORC-PQ-009
        q: RunPriorityQueue = RunPriorityQueue(maxsize=1)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        q.get_nowait()
        # Should not raise
        q.put(QueuedRun(run_id="b", lane="standard", priority_score=0))
        assert q.qsize() == 1


# ---------------------------------------------------------------------------
# get_nowait / put_nowait edge cases
# ---------------------------------------------------------------------------


class TestNowait:
    """get_nowait raises Empty; put_nowait raises Full. @trace FR-ORC-PQ-010"""

    def test_get_nowait_empty_raises(self) -> None:  # @trace FR-ORC-PQ-010
        q: RunPriorityQueue = RunPriorityQueue()
        with pytest.raises(Empty):
            q.get_nowait()

    def test_get_nowait_returns_item_when_available(
        self,
    ) -> None:  # @trace FR-ORC-PQ-010
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="r", lane="standard", priority_score=0))
        run = q.get_nowait()
        assert run.run_id == "r"


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """Concurrent put/get from multiple threads. @trace FR-ORC-PQ-011"""

    def test_concurrent_put_get_no_item_lost(self) -> None:  # @trace FR-ORC-PQ-011
        n = 200
        q: RunPriorityQueue = RunPriorityQueue()
        consumed: list[str] = []
        lock = threading.Lock()

        def producer(start: int) -> None:
            for i in range(start, start + 20):
                q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=10))

        def consumer() -> None:
            for _ in range(20):
                run = q.get(timeout=5.0)
                with lock:
                    consumed.append(run.run_id)

        producers = [
            threading.Thread(target=producer, args=(i * 20,)) for i in range(10)
        ]
        consumers = [threading.Thread(target=consumer) for _ in range(10)]

        for t in producers + consumers:
            t.start()
        for t in producers + consumers:
            t.join(timeout=10.0)

        assert len(consumed) == n
        assert len(set(consumed)) == n  # no duplicates

    def test_concurrent_cancel_safe(self) -> None:  # @trace FR-ORC-PQ-011
        """Concurrent cancel from one thread while another puts items."""
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(50):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))

        results: list[bool] = []
        lock = threading.Lock()

        def canceller(run_id: str) -> None:
            r = q.cancel(run_id)
            with lock:
                results.append(r)

        threads = [
            threading.Thread(target=canceller, args=(str(i),)) for i in range(50)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert len(results) == 50
        # Each ID should have been found exactly once
        assert sum(results) == 50

    def test_concurrent_drain_empties_completely(self) -> None:  # @trace FR-ORC-PQ-011
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(100):
            q.put(QueuedRun(run_id=str(i), lane="background", priority_score=100))

        all_drained: list[QueuedRun] = []
        lock = threading.Lock()

        def drainer() -> None:
            items = q.drain()
            with lock:
                all_drained.extend(items)

        threads = [threading.Thread(target=drainer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # Total drained must equal total inserted (each item removed exactly once)
        assert len(all_drained) == 100
        assert q.empty()


# ---------------------------------------------------------------------------
# Timeout behaviour
# ---------------------------------------------------------------------------


class TestTimeout:
    """Timeout raises Empty when no item arrives in time. @trace FR-ORC-PQ-012"""

    def test_get_timeout_raises_empty(self) -> None:  # @trace FR-ORC-PQ-012
        q: RunPriorityQueue = RunPriorityQueue()
        start = time.monotonic()
        with pytest.raises(Empty):
            q.get(timeout=0.1)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.08  # waited approximately the timeout

    def test_get_unblocks_when_item_arrives(self) -> None:  # @trace FR-ORC-PQ-012
        q: RunPriorityQueue = RunPriorityQueue()
        result: list[str] = []

        def producer() -> None:
            time.sleep(0.05)
            q.put(QueuedRun(run_id="late", lane="standard", priority_score=10))

        t = threading.Thread(target=producer)
        t.start()
        run = q.get(timeout=2.0)
        result.append(run.run_id)
        t.join()
        assert result == ["late"]

    def test_get_blocking_no_timeout_unblocks_on_put(
        self,
    ) -> None:  # @trace FR-ORC-PQ-012
        """A blocking get with timeout=None unblocks when an item is added."""
        q: RunPriorityQueue = RunPriorityQueue()
        received: list[str] = []

        def consumer() -> None:
            run = q.get(block=True, timeout=None)
            received.append(run.run_id)

        t = threading.Thread(target=consumer)
        t.start()
        time.sleep(0.05)
        q.put(QueuedRun(run_id="hello", lane="critical", priority_score=0))
        t.join(timeout=2.0)
        assert received == ["hello"]


# ---------------------------------------------------------------------------
# make_priority_queue factory
# ---------------------------------------------------------------------------


class TestMakePriorityQueue:
    """make_priority_queue factory. @trace FR-ORC-PQ-013"""

    def test_returns_run_priority_queue(self) -> None:  # @trace FR-ORC-PQ-013
        q = make_priority_queue()
        assert isinstance(q, RunPriorityQueue)

    def test_default_unbounded(self) -> None:  # @trace FR-ORC-PQ-013
        q = make_priority_queue()
        assert q.full() is False
        for i in range(100):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.qsize() == 100

    def test_maxsize_forwarded(self) -> None:  # @trace FR-ORC-PQ-013
        q = make_priority_queue(maxsize=2)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        q.put(QueuedRun(run_id="b", lane="standard", priority_score=0))
        with pytest.raises(Full):
            q.put_nowait(QueuedRun(run_id="c", lane="standard", priority_score=0))
