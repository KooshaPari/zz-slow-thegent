"""Unit tests for AUDIT-N+34 dormant-core hardening: LaneModel + RunPriorityQueue.

@trace FR-019 -- Adaptive load controls with critical lane protection.
@trace FR-ORC-PQ-001..013 -- Full RunPriorityQueue contract.

SOTA pass over the dormant-core `execution/lanes/__init__.py`
(`LaneModel` + `Lane` enum-style attrs + `LANE_PRIORITIES` canonical map)
plus `execution/priority_queue.py` (`QueuedRun` + `RunPriorityQueue` +
`make_priority_queue`). Audit carried forward from AUDIT-N+33 (dormant-core
chain: N+9 -> N+27 -> N+28 -> N+29 -> N+30 -> N+31 -> N+32 -> N+33).

Hardening contracts (NEW-1..NEW-14):

LaneModel (lanes/__init__.py):
- NEW-1  LANE_PRIORITIES has critical=0, standard=10, recovery=20, background=100
- NEW-2  LANE_URGENCY has critical=URGENCY_CRITICAL, standard=URGENCY_NORMAL,
         recovery=URGENCY_HIGH, background=URGENCY_LOW
- NEW-3  LaneModel.get_priority(name) integer; case-insensitive; default 50
         for unknown/empty inputs; critical=0, background=100
- NEW-4  LaneModel.get_urgency(name) float in (0, 1]; case-insensitive;
         unknown lanes fall back to URGENCY_NORMAL
- NEW-5  LaneModel.is_protected("critical") is True; all others False
- NEW-6  LaneModel.sort_tasks(tasks) returns list sorted by (priority asc,
         started_at_utc asc); tasks missing "lane" default to "standard";
         return is a fresh list (not in-place)
- NEW-7  LaneModel.check_capacity("critical", *, active_count, total_capacity)
         is True regardless of active_count (critical bypasses overload)
         For non-critical: True iff active_count < total_capacity - 2
         (2 reserved slots for critical); total_capacity < 2 floor at
         max(active_count, 1) -- never below critical allotment
- NEW-8  Lane has enum-style attrs CRITICAL/STANDARD/RECOVERY/BACKGROUND
         that string-equal their lane names
- NEW-9  LaneModel does NOT mutate input dicts in sort_tasks (defensive)

RunPriorityQueue + QueuedRun (priority_queue.py):
- NEW-10 QueuedRun carries (run_id, lane, priority_score, metadata=...,
         enqueued_at=...). Default metadata is a fresh empty dict per
         instance (no shared-state bug). enqueued_at defaults to
         time.monotonic() at construction.
- NEW-11 QueuedRun.from_lane(run_id, lane, metadata=None) -> QueuedRun with
         priority_score=LANE_PRIORITIES.get(lane, LaneModel.get_priority(lane))
         (so unknown lanes fall back to the LaneModel default of 50)
- NEW-12 RunPriorityQueue(maxsize=0). maxsize=0 is unbounded; maxsize>0 is
         bounded. put(item, block=True, timeout=...) honors blocking; raises
         Full when full + block=False or timeout expires.
- NEW-13 RunPriorityQueue ordering: lower priority_score first; FIFO within
         same score. cancel(run_id) removes by run_id, returns True/False.
         drain() returns all items in priority order and empties the queue.
         peek() returns next item without removing it. empty()/qsize()/full()
         are predicates.
- NEW-14 RunPriorityQueue is thread-safe: concurrent put/get from multiple
         threads loses no items; concurrent cancel is safe; concurrent drain
         returns each item exactly once.
- NEW-15 make_priority_queue() factory returns RunPriorityQueue; honors maxsize.
"""

from __future__ import annotations

import threading
import time
from queue import Empty, Full

import pytest

from thegent.orchestration.execution.lanes import (
    LANE_PRIORITIES,
    Lane,
    LaneModel,
)
from thegent.orchestration.execution.priority_queue import (
    PriorityQueue,
    QueuedRun,
    RunPriorityQueue,
    make_priority_queue,
)

# ---------------------------------------------------------------------------
# LaneModel + canonical map
# ---------------------------------------------------------------------------


class TestLanePriorityMap:
    """NEW-1: LANE_PRIORITIES canonical values."""

    def test_critical_zero(self) -> None:
        assert LANE_PRIORITIES["critical"] == 0

    def test_standard_ten(self) -> None:
        assert LANE_PRIORITIES["standard"] == 10

    def test_recovery_twenty(self) -> None:
        assert LANE_PRIORITIES["recovery"] == 20

    def test_background_hundred(self) -> None:
        assert LANE_PRIORITIES["background"] == 100


class TestLaneGetPriority:
    """NEW-3: LaneModel.get_priority() with case-insensitivity + default."""

    def test_critical(self) -> None:
        assert LaneModel.get_priority("critical") == 0

    def test_standard(self) -> None:
        assert LaneModel.get_priority("standard") == 10

    def test_recovery(self) -> None:
        assert LaneModel.get_priority("recovery") == 20

    def test_background(self) -> None:
        assert LaneModel.get_priority("background") == 100

    def test_unknown_default_fifty(self) -> None:
        assert LaneModel.get_priority("nonsense") == 50

    def test_empty_default_fifty(self) -> None:
        assert LaneModel.get_priority("") == 50

    def test_case_insensitive(self) -> None:
        assert LaneModel.get_priority("CRITICAL") == 0
        assert LaneModel.get_priority("Standard") == 10

    def test_returns_int(self) -> None:
        assert isinstance(LaneModel.get_priority("critical"), int)
        assert not isinstance(LaneModel.get_priority("standard"), bool)


class TestLaneGetUrgency:
    """NEW-4: LaneModel.get_urgency() with case-insensitivity + fallback."""

    def test_critical_urgency(self) -> None:
        assert LaneModel.get_urgency("critical") == pytest.approx(1.0)

    def test_standard_urgency(self) -> None:
        assert LaneModel.get_urgency("standard") == pytest.approx(0.5)

    def test_recovery_urgency(self) -> None:
        assert LaneModel.get_urgency("recovery") == pytest.approx(0.8)

    def test_background_urgency(self) -> None:
        assert LaneModel.get_urgency("background") == pytest.approx(0.3)

    def test_unknown_falls_back_to_normal(self) -> None:
        assert LaneModel.get_urgency("nonsense") == pytest.approx(0.5)

    def test_returns_float(self) -> None:
        assert isinstance(LaneModel.get_urgency("critical"), float)


class TestLaneIsProtected:
    """NEW-5: only critical is protected."""

    def test_critical_true(self) -> None:
        assert LaneModel.is_protected("critical") is True

    def test_standard_false(self) -> None:
        assert LaneModel.is_protected("standard") is False

    def test_recovery_false(self) -> None:
        assert LaneModel.is_protected("recovery") is False

    def test_background_false(self) -> None:
        assert LaneModel.is_protected("background") is False

    def test_unknown_false(self) -> None:
        assert LaneModel.is_protected("nonsense") is False


class TestLaneEnumAttrs:
    """NEW-8: Lane has enum-style attributes."""

    def test_critical_attr(self) -> None:
        assert Lane.CRITICAL == "critical"

    def test_standard_attr(self) -> None:
        assert Lane.STANDARD == "standard"

    def test_recovery_attr(self) -> None:
        assert Lane.RECOVERY == "recovery"

    def test_background_attr(self) -> None:
        assert Lane.BACKGROUND == "background"


# ---------------------------------------------------------------------------
# sort_tasks + check_capacity (FR-019 critical-lane protection)
# ---------------------------------------------------------------------------


class TestSortTasks:
    """NEW-6/NEW-9: sort_tasks stable ordering + defensive non-mutation."""

    def test_critical_before_standard(self) -> None:
        tasks = [
            {"lane": "standard", "started_at_utc": "2026-01-01T00:00:00Z"},
            {"lane": "critical", "started_at_utc": "2026-01-01T00:01:00Z"},
        ]
        out = LaneModel.sort_tasks(tasks)
        assert out[0]["lane"] == "critical"

    def test_standard_before_background(self) -> None:
        tasks = [
            {"lane": "background", "started_at_utc": "2026-01-01T00:00:00Z"},
            {"lane": "standard", "started_at_utc": "2026-01-01T00:01:00Z"},
        ]
        out = LaneModel.sort_tasks(tasks)
        assert out[0]["lane"] == "standard"

    def test_recovery_before_background(self) -> None:
        tasks = [
            {"lane": "background", "started_at_utc": "2026-01-01T00:00:00Z"},
            {"lane": "recovery", "started_at_utc": "2026-01-01T00:01:00Z"},
        ]
        out = LaneModel.sort_tasks(tasks)
        assert out[0]["lane"] == "recovery"

    def test_same_lane_sorted_by_time_asc(self) -> None:
        tasks = [
            {"lane": "standard", "started_at_utc": "2026-01-01T00:01:00Z"},
            {"lane": "standard", "started_at_utc": "2026-01-01T00:00:00Z"},
        ]
        out = LaneModel.sort_tasks(tasks)
        assert out[0]["started_at_utc"] == "2026-01-01T00:00:00Z"

    def test_missing_lane_defaults_standard(self) -> None:
        tasks = [{"started_at_utc": "2026-01-01T00:00:00Z"}]
        out = LaneModel.sort_tasks(tasks)
        assert len(out) == 1

    def test_returns_fresh_list(self) -> None:
        tasks = [
            {"lane": "background", "started_at_utc": "2026-01-01T00:00:00Z"},
            {"lane": "critical", "started_at_utc": "2026-01-01T00:01:00Z"},
        ]
        original = list(tasks)
        _ = LaneModel.sort_tasks(tasks)
        # input should not be mutated
        assert tasks == original

    def test_empty_input_returns_empty(self) -> None:
        assert LaneModel.sort_tasks([]) == []


class TestCheckCapacity:
    """NEW-7: FR-019 critical bypass + reserved slots."""

    def test_critical_bypasses_active_count(self) -> None:
        assert LaneModel.check_capacity("critical", active_count=99, total_capacity=10) is True
        assert LaneModel.check_capacity("critical", active_count=0, total_capacity=1) is True

    def test_standard_has_capacity_when_under_limit(self) -> None:
        # 10 total, 2 reserved -> 8 available for non-critical; 5 active -> ok
        assert LaneModel.check_capacity("standard", active_count=5, total_capacity=10) is True
        assert LaneModel.check_capacity("standard", active_count=7, total_capacity=10) is True

    def test_standard_full_rejects(self) -> None:
        # 8 active of 8 available -> at limit; 9 active -> rejected
        assert LaneModel.check_capacity("standard", active_count=9, total_capacity=10) is False

    def test_recovery_rejects_over_limit(self) -> None:
        assert LaneModel.check_capacity("recovery", active_count=8, total_capacity=10) is False

    def test_background_rejects_over_limit(self) -> None:
        assert LaneModel.check_capacity("background", active_count=8, total_capacity=10) is False

    def test_small_capacity_floor(self) -> None:
        # total_capacity < 2: floor at 1, so active=0 -> ok
        assert LaneModel.check_capacity("standard", active_count=0, total_capacity=1) is True

    def test_check_capacity_only_critical_unbounded_for_active99(self) -> None:
        # Even at 100 active, critical still gets a slot
        assert LaneModel.check_capacity("critical", active_count=100, total_capacity=1) is True


# ---------------------------------------------------------------------------
# QueuedRun dataclass + from_lane factory
# ---------------------------------------------------------------------------


class TestQueuedRunFields:
    """NEW-10: QueuedRun fields + independent metadata dicts."""

    def test_basic_fields(self) -> None:
        run = QueuedRun(run_id="r1", lane="standard", priority_score=10)
        assert run.run_id == "r1"
        assert run.lane == "standard"
        assert run.priority_score == 10

    def test_metadata_defaults_to_empty_dict(self) -> None:
        run = QueuedRun(run_id="r1", lane="standard", priority_score=10)
        assert run.metadata == {}

    def test_metadata_independent_per_instance(self) -> None:
        """The default-factory dict must not be shared between instances."""
        r1 = QueuedRun(run_id="a", lane="standard", priority_score=0)
        r2 = QueuedRun(run_id="b", lane="standard", priority_score=0)
        r1.metadata["x"] = 1
        assert r2.metadata == {}

    def test_custom_metadata(self) -> None:
        meta = {"owner": "svc-a"}
        run = QueuedRun(run_id="r1", lane="critical", priority_score=0, metadata=meta)
        assert run.metadata == meta

    def test_enqueued_at_monotonic_default(self) -> None:
        before = time.monotonic()
        run = QueuedRun(run_id="r1", lane="standard", priority_score=10)
        after = time.monotonic()
        assert before <= run.enqueued_at <= after


class TestQueuedRunFromLane:
    """NEW-11: from_lane derives priority_score from LANE_PRIORITIES."""

    def test_critical_priority(self) -> None:
        run = QueuedRun.from_lane("r1", "critical")
        assert run.priority_score == 0

    def test_standard_priority(self) -> None:
        run = QueuedRun.from_lane("r2", "standard")
        assert run.priority_score == 10

    def test_recovery_priority(self) -> None:
        run = QueuedRun.from_lane("r3", "recovery")
        assert run.priority_score == 20

    def test_background_priority(self) -> None:
        run = QueuedRun.from_lane("r4", "background")
        assert run.priority_score == 100

    def test_unknown_lane_falls_back(self) -> None:
        run = QueuedRun.from_lane("r5", "made-up")
        assert run.priority_score == LaneModel.get_priority("made-up")  # 50

    def test_lane_value_stored(self) -> None:
        run = QueuedRun.from_lane("r6", "background")
        assert run.lane == "background"

    def test_metadata_none_gives_empty_dict(self) -> None:
        run = QueuedRun.from_lane("r7", "standard", metadata=None)
        assert run.metadata == {}

    def test_metadata_passed_through(self) -> None:
        meta = {"tag": "v1"}
        run = QueuedRun.from_lane("r8", "standard", metadata=meta)
        assert run.metadata == meta

    def test_lane_enum_accepted(self) -> None:
        run = QueuedRun.from_lane("r9", Lane.CRITICAL)
        assert run.priority_score == 0


# ---------------------------------------------------------------------------
# RunPriorityQueue -- ordering, predicates, drain, peek, cancel
# ---------------------------------------------------------------------------


class TestPriorityOrdering:
    """NEW-13: lower priority_score first; FIFO within same score."""

    def test_lower_score_first(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="bg", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="crit", lane="critical", priority_score=0))
        q.put(QueuedRun(run_id="std", lane="standard", priority_score=10))
        assert q.get_nowait().run_id == "crit"
        assert q.get_nowait().run_id == "std"
        assert q.get_nowait().run_id == "bg"

    def test_fifo_within_same_score(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(5):
            q.put(QueuedRun(run_id=f"r{i}", lane="standard", priority_score=10))
        ids = [q.get_nowait().run_id for _ in range(5)]
        assert ids == ["r0", "r1", "r2", "r3", "r4"]


class TestCancel:
    """NEW-13: cancel removes by run_id, returns True/False."""

    def test_existing_returns_true(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=10))
        assert q.cancel("a") is True

    def test_nonexistent_returns_false(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.cancel("ghost") is False

    def test_removes_specific_run(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="keep", lane="standard", priority_score=10))
        q.put(QueuedRun(run_id="drop", lane="standard", priority_score=10))
        q.cancel("drop")
        assert q.qsize() == 1
        assert q.get_nowait().run_id == "keep"


class TestDrain:
    """NEW-13: drain returns all in priority order, empties queue."""

    def test_drain_priority_order(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="bg", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="crit", lane="critical", priority_score=0))
        q.put(QueuedRun(run_id="std", lane="standard", priority_score=10))
        drained = q.drain()
        assert [r.run_id for r in drained] == ["crit", "std", "bg"]

    def test_drain_empties(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(5):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=10))
        q.drain()
        assert q.empty()
        assert q.qsize() == 0


class TestPeek:
    """NEW-13: peek returns next without removing."""

    def test_peek_highest_priority(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="bg", lane="background", priority_score=100))
        q.put(QueuedRun(run_id="crit", lane="critical", priority_score=0))
        peeked = q.peek()
        assert peeked is not None
        assert peeked.run_id == "crit"

    def test_peek_does_not_remove(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="r1", lane="standard", priority_score=10))
        _ = q.peek()
        assert q.qsize() == 1

    def test_peek_empty_returns_none(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.peek() is None


class TestPredicates:
    """NEW-13: empty/full/qsize."""

    def test_new_queue_empty(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        assert q.empty() is True

    def test_qsize_increments(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        for i in range(4):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.qsize() == 4

    def test_full_bounded_when_at_maxsize(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue(maxsize=3)
        for i in range(3):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.full() is True

    def test_full_unbounded_false(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue(maxsize=0)
        for i in range(100):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.full() is False


class TestBounded:
    """NEW-12: maxsize=0 unbounded; maxsize>0 raises Full."""

    def test_maxsize_zero_unbounded(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue(maxsize=0)
        for i in range(500):
            q.put(QueuedRun(run_id=str(i), lane="standard", priority_score=0))
        assert q.qsize() == 500

    def test_put_nowait_raises_full(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue(maxsize=2)
        q.put_nowait(QueuedRun(run_id="a", lane="standard", priority_score=0))
        q.put_nowait(QueuedRun(run_id="b", lane="standard", priority_score=0))
        with pytest.raises(Full):
            q.put_nowait(QueuedRun(run_id="c", lane="standard", priority_score=0))

    def test_put_block_false_raises_full(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue(maxsize=1)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        with pytest.raises(Full):
            q.put(QueuedRun(run_id="b", lane="standard", priority_score=0), block=False)

    def test_put_blocking_timeout_raises_full(self) -> None:
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
        assert elapsed >= 0.08

    def test_space_freed_after_get_allows_put(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue(maxsize=1)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        q.get_nowait()
        q.put(QueuedRun(run_id="b", lane="standard", priority_score=0))
        assert q.qsize() == 1


class TestNowait:
    """NEW-13: get_nowait raises Empty when empty."""

    def test_get_nowait_empty_raises(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        with pytest.raises(Empty):
            q.get_nowait()

    def test_get_nowait_returns_item(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        q.put(QueuedRun(run_id="r", lane="standard", priority_score=0))
        run = q.get_nowait()
        assert run.run_id == "r"


class TestTimeouts:
    """NEW-13/NEW-12: get(timeout=...) raises Empty on timeout."""

    def test_get_timeout_raises_empty(self) -> None:
        q: RunPriorityQueue = RunPriorityQueue()
        start = time.monotonic()
        with pytest.raises(Empty):
            q.get(timeout=0.1)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.08

    def test_get_unblocks_when_item_arrives(self) -> None:
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


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """NEW-14: concurrent put/get loses no items."""

    def test_concurrent_put_get_no_loss(self) -> None:
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

        producers = [threading.Thread(target=producer, args=(i * 20,)) for i in range(10)]
        consumers = [threading.Thread(target=consumer) for _ in range(10)]

        for t in producers + consumers:
            t.start()
        for t in producers + consumers:
            t.join(timeout=10.0)

        assert len(consumed) == n
        assert len(set(consumed)) == n


# ---------------------------------------------------------------------------
# Factory + module-level surface
# ---------------------------------------------------------------------------


class TestFactoryAndSurface:
    """NEW-15: factory + module-level PriorityQueue still exists."""

    def test_make_priority_queue_returns_run_priority_queue(self) -> None:
        q = make_priority_queue()
        assert isinstance(q, RunPriorityQueue)

    def test_make_priority_queue_maxsize_forwarded(self) -> None:
        q = make_priority_queue(maxsize=2)
        q.put(QueuedRun(run_id="a", lane="standard", priority_score=0))
        q.put(QueuedRun(run_id="b", lane="standard", priority_score=0))
        with pytest.raises(Full):
            q.put_nowait(QueuedRun(run_id="c", lane="standard", priority_score=0))

    def test_priority_queue_class_still_exported(self) -> None:
        """The original (heap-based) PriorityQueue is preserved as legacy."""
        pq = PriorityQueue()
        pq.push(0, {"run_id": "a"})
        assert pq.pop() == {"run_id": "a"}
