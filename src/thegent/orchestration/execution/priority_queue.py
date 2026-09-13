"""Run priority queue + queued run dataclass (FR-ORC-PQ-001..013).

@trace AUDIT-N+34 dormant-core hardening.
@trace FR-ORC-PQ-001..013 -- Full RunPriorityQueue contract (swarm-priority-queue).

SOTA pass-18 hardening of the dormant-core ``RunPriorityQueue`` +
``QueuedRun`` + ``make_priority_queue`` factory. See
``tests/test_unit_audit_n34_lanes_priority_queue_hardening.py`` for the
NEW-10..NEW-15 contracts; see ``tests/test_unit_orchestration_lanes.py``
+ ``tests/orchestration/test_priority_queue.py`` for the prior dormant
contracts that this surface also satisfies.

The hardened contract:
* ``QueuedRun(run_id, lane, priority_score, metadata=..., enqueued_at=...)``
  with a fresh per-instance ``metadata`` dict and monotonic
  ``enqueued_at`` default.
* ``QueuedRun.from_lane(run_id, lane, metadata=None)`` derives the
  ``priority_score`` from ``LANE_PRIORITIES`` (falling back to
  ``LaneModel.get_priority(lane)`` for unknown lanes).
* ``RunPriorityQueue(maxsize=0)`` -- ``maxsize=0`` means unbounded,
  ``maxsize>0`` means bounded with ``Full`` raised via ``put_nowait``,
  ``put(block=False)``, or ``put(block=True, timeout=...)``.
* Full ``put``/``get``/``put_nowait``/``get_nowait`` / ``qsize`` /
  ``empty`` / ``full`` / ``cancel`` / ``drain`` / ``peek`` API.
* ``RLock``-backed thread safety for concurrent put/get/cancel/drain.
* ``make_priority_queue(maxsize=...)`` factory.

The legacy ``PriorityQueue`` (heap-based, ``push``/``pop`` on
``(priority, item)`` dict tuples) is preserved for backwards
compatibility.
"""

from __future__ import annotations

import contextlib
import heapq
import threading
import time
from dataclasses import dataclass, field
from queue import Empty, Full
from typing import Any

from thegent.orchestration.execution.lanes import LANE_PRIORITIES, LaneModel

# ---------------------------------------------------------------------------
# Legacy PriorityQueue (heap-based, push(priority, item) -> pop() -> item)
# ---------------------------------------------------------------------------


class PriorityQueue:
    """Legacy priority queue (heap-based, preserved for backwards compatibility).

    ``push(priority, item)`` adds an item; ``pop()`` returns the lowest-
    priority item or ``None`` when empty. New code should prefer
    ``RunPriorityQueue`` + ``QueuedRun``.
    """

    def __init__(self) -> None:
        self._heap: list[tuple[int, dict[str, Any]]] = []

    def push(self, priority: int, item: dict[str, Any]) -> None:
        heapq.heappush(self._heap, (priority, item))

    def pop(self) -> dict[str, Any] | None:
        if self._heap:
            _, item = heapq.heappop(self._heap)
            return item
        return None


# ---------------------------------------------------------------------------
# QueuedRun dataclass (FR-ORC-PQ-001..002, NEW-10..NEW-11)
# ---------------------------------------------------------------------------


@dataclass
class QueuedRun:
    """A queued execution run.

    Carries:
    * ``run_id`` -- unique identifier (used by ``cancel``).
    * ``lane`` -- lane name (``"critical"``/``"standard"``/...).
    * ``priority_score`` -- lower = earlier dequeue. For lanes this is
      derived from ``LANE_PRIORITIES`` via ``from_lane``.
    * ``metadata`` -- per-instance dict (default-factory so no shared
      state bug; NEW-10). Callers may freely mutate without affecting
      siblings.
    * ``enqueued_at`` -- monotonic clock value set at construction
      (NEW-10); can be used as a stable secondary sort key.
    """

    run_id: str
    lane: str
    priority_score: int
    metadata: dict[str, Any] = field(default_factory=dict)
    enqueued_at: float = field(default_factory=time.monotonic)

    @classmethod
    def from_lane(
        cls,
        run_id: str,
        lane: str,
        metadata: dict[str, Any] | None = None,
    ) -> QueuedRun:
        """Build a ``QueuedRun`` with ``priority_score`` derived from ``lane``.

        Priority is sourced from ``LANE_PRIORITIES[lane]`` when known;
        otherwise it falls back to ``LaneModel.get_priority(lane)``
        (which itself returns the default ``50`` for unknown lanes).
        ``Lane.CRITICAL`` / other enum-style attrs are accepted (their
        string values land in ``LANE_PRIORITIES``).
        """
        if lane in LANE_PRIORITIES:
            score = LANE_PRIORITIES[lane]
        else:
            score = LaneModel.get_priority(lane)
        return cls(
            run_id=run_id,
            lane=lane,
            priority_score=score,
            metadata=dict(metadata) if metadata is not None else {},
        )


# ---------------------------------------------------------------------------
# RunPriorityQueue (FR-ORC-PQ-003..013, NEW-12..NEW-15)
# ---------------------------------------------------------------------------


class RunPriorityQueue:
    """Priority queue specifically for execution runs.

    Order: lower ``priority_score`` dequeues first; FIFO within the same
    ``priority_score`` (heap entries carry a monotonic counter to break
    ties). Bounded by ``maxsize`` (``maxsize=0`` means unbounded). All
    public mutators are guarded by a single per-instance ``RLock`` so
    concurrent producers/consumers/cancellers/drainers do not corrupt
    internal state (NEW-14).

    Mirrors the standard ``queue.Queue`` / ``queue.PriorityQueue`` API
    surface (``put`` / ``get`` / ``put_nowait`` / ``get_nowait`` /
    ``qsize`` / ``empty`` / ``full``) plus the swarm-specific extensions
    ``cancel`` (remove by ``run_id``), ``drain`` (return all in priority
    order and empty the queue), and ``peek`` (return next without
    removing).
    """

    def __init__(self, maxsize: int = 0) -> None:
        # NEW-12: maxsize=0 means unbounded; maxsize>0 means bounded.
        if maxsize < 0:
            raise ValueError("maxsize must be >= 0 (0 means unbounded)")
        self._maxsize = maxsize
        # Heap entries are (priority_score, fifo_counter, QueuedRun).
        self._heap: list[tuple[int, int, QueuedRun]] = []
        # run_id -> heap entry (lazy cleanup on drain).
        self._index: dict[str, tuple[int, int, QueuedRun]] = {}
        # Monotonic counter for FIFO-within-same-score ordering.
        self._counter = 0
        # NEW-14: RLock so a single thread can re-enter safely (e.g.
        # ``drain`` calling ``put`` internally); concurrent producers
        # and consumers serialize on the same lock.
        self._lock = threading.RLock()
        # Condition for blocking put/get with timeouts.
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

    # ------------------------------------------------------------------
    # Predicates
    # ------------------------------------------------------------------

    def empty(self) -> bool:
        with self._lock:
            return not self._heap

    def qsize(self) -> int:
        with self._lock:
            return len(self._heap)

    def full(self) -> bool:
        """``True`` iff bounded (``maxsize > 0``) and at capacity."""
        with self._lock:
            return self._maxsize > 0 and len(self._heap) >= self._maxsize

    # ------------------------------------------------------------------
    # put / put_nowait (FR-ORC-PQ-009, NEW-12)
    # ------------------------------------------------------------------

    def put(
        self,
        item: QueuedRun,
        block: bool = True,
        timeout: float | None = None,
    ) -> None:
        """Add ``item`` to the queue.

        * ``block=True`` + ``timeout=None`` blocks until space is available.
        * ``block=True`` + ``timeout=N`` blocks up to ``N`` seconds.
        * ``block=False`` raises ``Full`` immediately if no space.
        """
        if block and timeout is not None and timeout < 0:
            raise ValueError("timeout must be >= 0")
        with self._not_full:
            if self._maxsize > 0:
                # Bounded: respect block + timeout.
                if block:
                    deadline = None if timeout is None else (time.monotonic() + timeout)
                    while len(self._heap) >= self._maxsize:
                        if deadline is None:
                            self._not_full.wait()
                        else:
                            remaining = deadline - time.monotonic()
                            if remaining <= 0:
                                raise Full
                            self._not_full.wait(remaining)
                elif len(self._heap) >= self._maxsize:
                    raise Full
            self._enqueue_locked(item)
            self._not_empty.notify()

    def put_nowait(self, item: QueuedRun) -> None:
        """Equivalent to ``put(item, block=False)``."""
        self.put(item, block=False)

    # ------------------------------------------------------------------
    # get / get_nowait (FR-ORC-PQ-010, FR-ORC-PQ-012, NEW-13)
    # ------------------------------------------------------------------

    def get(self, block: bool = True, timeout: float | None = None) -> QueuedRun:
        """Remove and return the next item.

        * ``block=True`` + ``timeout=None`` blocks until an item is available.
        * ``block=True`` + ``timeout=N`` blocks up to ``N`` seconds.
        * ``block=False`` raises ``Empty`` immediately if no item.
        """
        if block and timeout is not None and timeout < 0:
            raise ValueError("timeout must be >= 0")
        with self._not_empty:
            if not self._heap:
                if not block:
                    raise Empty
                deadline = None if timeout is None else (time.monotonic() + timeout)
                while not self._heap:
                    if deadline is None:
                        self._not_empty.wait()
                    else:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise Empty
                        self._not_empty.wait(remaining)
            return self._dequeue_locked()

    def get_nowait(self) -> QueuedRun:
        """Equivalent to ``get(block=False)``."""
        return self.get(block=False)

    # ------------------------------------------------------------------
    # cancel (FR-ORC-PQ-005, NEW-13)
    # ------------------------------------------------------------------

    def cancel(self, run_id: str) -> bool:
        """Remove the item with ``run_id`` from the queue.

        Returns ``True`` if an item was removed, ``False`` otherwise.
        Lazy cleanup: stale heap entries are skipped when they surface
        during ``get``/``drain``.
        """
        with self._lock:
            entry = self._index.pop(run_id, None)
            if entry is None:
                return False
            # Mark for lazy removal; the heap entry stays until
            # _dequeue_locked / drain surfaces and skips it.
            with contextlib.suppress(ValueError):
                self._heap.remove(entry)
            heapq.heapify(self._heap)
            self._not_full.notify()
            return True

    # ------------------------------------------------------------------
    # drain (FR-ORC-PQ-006, NEW-13)
    # ------------------------------------------------------------------

    def drain(self) -> list[QueuedRun]:
        """Return all items in priority order and empty the queue."""
        with self._lock:
            items = [entry[2] for entry in sorted(self._heap)]
            self._heap.clear()
            self._index.clear()
            self._not_full.notify_all()
            return items

    # ------------------------------------------------------------------
    # peek (FR-ORC-PQ-007, NEW-13)
    # ------------------------------------------------------------------

    def peek(self) -> QueuedRun | None:
        """Return the next item without removing it (or ``None`` if empty)."""
        with self._lock:
            return self._peek_locked()

    # ------------------------------------------------------------------
    # Internal helpers (must be called with ``self._lock`` held).
    # ------------------------------------------------------------------

    def _enqueue_locked(self, item: QueuedRun) -> None:
        self._counter += 1
        entry = (item.priority_score, self._counter, item)
        heapq.heappush(self._heap, entry)
        self._index[item.run_id] = entry

    def _dequeue_locked(self) -> QueuedRun:
        while self._heap:
            entry = heapq.heappop(self._heap)
            # Lazy skip: stale entry (was cancel()ed earlier).
            if self._index.get(entry[2].run_id) is not entry:
                continue
            self._index.pop(entry[2].run_id, None)
            return entry[2]
        raise Empty

    def _peek_locked(self) -> QueuedRun | None:
        # Skip stale entries lazily.
        while self._heap:
            entry = self._heap[0]
            if self._index.get(entry[2].run_id) is not entry:
                heapq.heappop(self._heap)
                continue
            return entry[2]
        return None


# ---------------------------------------------------------------------------
# Factory (FR-ORC-PQ-013, NEW-15)
# ---------------------------------------------------------------------------


def make_priority_queue(maxsize: int = 0) -> RunPriorityQueue:
    """Construct a fresh ``RunPriorityQueue``.

    ``maxsize=0`` (the default) means unbounded; ``maxsize > 0`` means
    bounded with ``Full`` raised on overflow.
    """
    return RunPriorityQueue(maxsize=maxsize)


__all__ = [
    "PriorityQueue",
    "QueuedRun",
    "RunPriorityQueue",
    "make_priority_queue",
    "Empty",
    "Full",
]
