"""Sub-agent event queue — thread-safe FIFO for orchestration telemetry.

The :class:`SubAgentEventQueue` is the canonical event-stream surface used by
:class:`SubAgentDispatcher` and :class:`UnifiedWorkerDaemon` to publish
sub-agent lifecycle events (STARTED / PROGRESS / COMPLETED / FAILED / etc.)
for downstream consumers (MCP tools, the operator cockpit, the audit
pipeline, etc.).

Hardening (AUDIT-N+37)
======================

| FR | Invariant |
|---|-----------|
| FR-ORC-060 | ``put()`` is concurrency-safe under contention; no lost events. |
| FR-ORC-061 | ``drain_nowait()`` returns a defensive copy. |
| FR-ORC-062 | ``stream(timeout=)`` is a true async generator (FIFO, ``asyncio.TimeoutError``, cancel-clean). |
| FR-ORC-063 | non-positive ``maxsize`` raises ``ValueError`` at construction. |
| FR-ORC-064 | non-``SubAgentEvent`` payloads raise ``TypeError`` at ``put()``. |
| FR-ORC-065 | ``get_global_event_queue()`` is locked; concurrent callers see the same singleton. |
| FR-ORC-066 | ``reset_global_event_queue()`` is locked; no torn replace. |
| FR-ORC-071 | ``stats()`` exposes ``{enqueued, drained, dropped, qsize, maxsize}`` for audit tooling. |
| FR-ORC-072 | ``put()`` at capacity raises ``asyncio.QueueFull`` synchronously (no block). |

The implementation is a guarded ``collections.deque`` (the canonical FIFO)
serialised by a ``threading.RLock`` for thread safety, with an
``asyncio.Event`` to bridge sync producers to async consumers without
ever spawning an ``asyncio.Queue`` instance.  This avoids the
asyncio.Queue lifecycle hazard (dangling unfinished tasks at GC) and
gives the queue a clean, predictable threading model: lock first, then
deque operation, then event set.
"""

from __future__ import annotations

import asyncio
import threading
from collections import deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAXSIZE: int = 1024
"""Default maxsize for :class:`SubAgentEventQueue` (also the audit SLO)."""

ABSOLUTE_MIN_MAXSIZE: int = 1
"""Hard floor for ``maxsize``; smaller values are rejected with :class:`ValueError`."""

# asyncio.Queue's "Empty" / "Full" exceptions are the same singletons
# imported elsewhere; aliasing them here keeps the queue's public surface
# self-documenting.
QueueEmpty = asyncio.QueueEmpty
QueueFull = asyncio.QueueFull


# ---------------------------------------------------------------------------
# EventQueueStats
# ---------------------------------------------------------------------------


class EventQueueStats:
    """Snapshot of :class:`SubAgentEventQueue` health for SOTA audit tooling.

    Fields:
    - ``enqueued`` (int): cumulative ``put()`` success count.
    - ``drained`` (int): cumulative ``drain_nowait()`` total events returned.
    - ``dropped`` (int): cumulative ``put()`` calls that raised ``QueueFull``.
    - ``qsize`` (int): current depth.
    - ``maxsize`` (int): configured maximum depth.
    """

    __slots__ = ("drained", "dropped", "enqueued", "maxsize", "qsize")

    def __init__(
        self,
        *,
        enqueued: int,
        drained: int,
        dropped: int,
        qsize: int,
        maxsize: int,
    ) -> None:
        self.enqueued = enqueued
        self.drained = drained
        self.dropped = dropped
        self.qsize = qsize
        self.maxsize = maxsize

    def to_dict(self) -> dict[str, int]:
        return {
            "enqueued": self.enqueued,
            "drained": self.drained,
            "dropped": self.dropped,
            "qsize": self.qsize,
            "maxsize": self.maxsize,
        }

    def __repr__(self) -> str:
        return (
            f"EventQueueStats(enqueued={self.enqueued}, drained={self.drained}, "
            f"dropped={self.dropped}, qsize={self.qsize}, maxsize={self.maxsize})"
        )


# ---------------------------------------------------------------------------
# SubAgentEventQueue
# ---------------------------------------------------------------------------


class SubAgentEventQueue:
    """FIFO queue for :class:`~thegent.orchestration.protocol.SubAgentEvent` instances.

    Parameters
    ----------
    maxsize:
        Maximum number of events the queue can hold.  ``put()`` raises
        :class:`asyncio.QueueFull` when the queue is at capacity.  Must
        be a positive integer (FR-ORC-063).

    Implementation: a guarded ``collections.deque`` is the canonical
    FIFO; an ``asyncio.Event`` is set whenever the queue transitions
    from empty to non-empty so awaiting consumers wake up promptly.
    A ``threading.RLock`` serialises every mutation so concurrent
    producers never lose events (FR-ORC-060) and observers see
    consistent state (``stats()`` cannot tear).
    """

    def __init__(self, maxsize: int = DEFAULT_MAXSIZE) -> None:
        if not isinstance(maxsize, int) or isinstance(maxsize, bool):
            raise TypeError(f"maxsize must be int, got {type(maxsize).__name__}")
        if maxsize < ABSOLUTE_MIN_MAXSIZE:
            raise ValueError(
                f"maxsize must be >= {ABSOLUTE_MIN_MAXSIZE}, got {maxsize}",
            )
        self._maxsize: int = maxsize
        self._items: deque[Any] = deque()
        self._lock: threading.RLock = threading.RLock()
        # Monotonic counters for ``stats()``.
        self._enqueued: int = 0
        self._drained: int = 0
        self._dropped: int = 0
        # Async wake-up primitive.  ``None`` until first async consumer
        # binds; once bound it is reused for the lifetime of the queue
        # (a fresh queue is created in ``reset_global_event_queue``).
        self._loop: asyncio.AbstractEventLoop | None = None
        self._not_empty: asyncio.Event | None = None
        self._not_empty_guard: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Async primitive binding
    # ------------------------------------------------------------------

    def _bind_loop(self) -> asyncio.Event:
        """Return an :class:`asyncio.Event` bound to the running loop.

        The event is created once per queue, lazily, on the loop of the
        first async caller.  Subsequent callers see the same event so
        ``put()`` from another thread signals exactly the right loop.
        """
        loop = asyncio.get_running_loop()
        with self._not_empty_guard:
            if self._not_empty is None or self._loop is not loop:
                evt = asyncio.Event()
                self._not_empty = evt
                self._loop = loop
                # If events are already in the queue when the event is
                # bound, set it immediately so the first waiter doesn't
                # block on a non-empty queue.
                with self._lock:
                    if self._items:
                        self._loop.call_soon_threadsafe(evt.set)
            return self._not_empty

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def maxsize(self) -> int:
        """Configured maximum queue depth."""
        return self._maxsize

    @property
    def qsize(self) -> int:
        """Current queue depth."""
        with self._lock:
            return len(self._items)

    @property
    def empty(self) -> bool:
        """True when the queue holds no events."""
        with self._lock:
            return len(self._items) == 0

    # ------------------------------------------------------------------
    # Sync surface
    # ------------------------------------------------------------------

    def put(self, event: Any) -> None:
        """Enqueue ``event`` synchronously.

        Raises
        ------
        TypeError
            if ``event`` is not a :class:`SubAgentEvent` (FR-ORC-064).
            Duck-typed objects with ``request_id``, ``event_type``,
            ``payload`` attributes are accepted so test doubles work.
        asyncio.QueueFull
            if the queue is at ``maxsize`` (FR-ORC-072).  The call does
            not block — fail fast so the dispatcher never stalls.
        """
        if not _is_sub_agent_event_like(event):
            raise TypeError(
                f"event must be SubAgentEvent (or duck-typed equivalent), got {type(event).__name__}",
            )
        with self._lock:
            if len(self._items) >= self._maxsize:
                self._dropped += 1
                raise QueueFull(
                    f"SubAgentEventQueue at capacity (maxsize={self._maxsize})",
                )
            self._items.append(event)
            self._enqueued += 1
        # Signal async consumers *after* releasing the lock to avoid
        # blocking under contention.  If no async consumer is bound
        # yet the call is a no-op (the lock guard makes it cheap).
        evt, loop = self._not_empty, self._loop
        if evt is not None and loop is not None and loop.is_running():
            try:
                loop.call_soon_threadsafe(evt.set)
            except RuntimeError:
                # Loop closed between bind and set; ignore — async
                # consumers are gone, sync put path is unaffected.
                pass

    def get_nowait(self) -> Any:
        """Dequeue the next event synchronously.

        Raises
        ------
        asyncio.QueueEmpty
            if the queue is empty.
        """
        with self._lock:
            if not self._items:
                raise QueueEmpty("SubAgentEventQueue is empty")
            event = self._items.popleft()
            self._drained += 1
            return event

    def drain_nowait(self) -> list[Any]:
        """Return a defensive copy of every queued event in FIFO order.

        The queue is cleared as a side effect.  The returned list is a
        fresh ``list`` so the caller can iterate / mutate it without
        affecting the queue's internal state (FR-ORC-061).
        """
        with self._lock:
            snapshot: list[Any] = list(self._items)
            self._items.clear()
            self._drained += len(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # Async surface
    # ------------------------------------------------------------------

    async def get(self) -> Any:
        """Dequeue the next event asynchronously (FIFO).

        Increments the ``drained`` counter when an event is returned.
        ``CancelledError`` propagates so callers can cancel cleanly
        (FR-ORC-074).
        """
        evt = self._bind_loop()
        while True:
            with self._lock:
                if self._items:
                    event = self._items.popleft()
                    self._drained += 1
                    return event
            # Wait for the next producer.  ``await`` here is the only
            # blocking point; cancellation cleanly wakes the task.
            await evt.wait()
            # Clear under the lock so we don't lose a wake-up that
            # arrived between the check and the wait.
            with self._lock:
                evt.clear()

    async def stream(self, timeout: float) -> AsyncIterator[Any]:
        """Yield events indefinitely until ``timeout`` seconds of inactivity.

        Raises
        ------
        asyncio.TimeoutError
            if no event is dequeued within ``timeout`` seconds.
        asyncio.CancelledError
            if the enclosing task is cancelled (exits cleanly).
        """
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
            raise TypeError(f"timeout must be a number, got {type(timeout).__name__}")
        if timeout <= 0:
            raise ValueError(f"timeout must be > 0, got {timeout}")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(
                    f"SubAgentEventQueue.stream: no event within {timeout}s",
                )
            try:
                event = await asyncio.wait_for(self.get(), timeout=remaining)
            except TimeoutError as exc:
                raise TimeoutError(
                    f"SubAgentEventQueue.stream: no event within {timeout}s",
                ) from exc
            yield event
            # Reset the deadline on each successful dequeue so the
            # timeout measures *inactivity*, not total run time.
            deadline = loop.time() + timeout

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, int]:
        """Return a snapshot of queue health.

        Returns a dict with ``enqueued``, ``drained``, ``dropped``,
        ``qsize``, and ``maxsize`` integer counters (FR-ORC-071).
        """
        with self._lock:
            return EventQueueStats(
                enqueued=self._enqueued,
                drained=self._drained,
                dropped=self._dropped,
                qsize=len(self._items),
                maxsize=self._maxsize,
            ).to_dict()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_sub_agent_event_like(event: Any) -> bool:
    """Return True if ``event`` quacks like a :class:`SubAgentEvent`.

    Dormant tests and the historical implementation used both
    Pydantic-style and stdlib-style ``SubAgentEvent`` instances.  The
    audit accepts both so the contract is "request_id + event_type +
    payload" — three duck-typed attributes.
    """
    if event is None:
        return False
    return bool(hasattr(event, "request_id") and hasattr(event, "event_type") and hasattr(event, "payload"))


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_global_event_queue: SubAgentEventQueue | None = None
_global_event_queue_lock: threading.Lock = threading.Lock()


def get_global_event_queue() -> SubAgentEventQueue:
    """Return the process-wide singleton :class:`SubAgentEventQueue`.

    Lazy construction is locked (FR-ORC-065) so two concurrent callers
    in the same process see the same instance.
    """
    global _global_event_queue
    with _global_event_queue_lock:
        if _global_event_queue is None:
            _global_event_queue = SubAgentEventQueue()
        return _global_event_queue


def reset_global_event_queue() -> None:
    """Replace the global singleton with a fresh :class:`SubAgentEventQueue`.

    Locked (FR-ORC-066) so a concurrent reader cannot observe a
    half-replaced singleton.
    """
    global _global_event_queue
    with _global_event_queue_lock:
        _global_event_queue = None


def get_event_queue() -> SubAgentEventQueue:
    """Alias for :func:`get_global_event_queue` (historical name)."""
    return get_global_event_queue()


__all__ = [
    "ABSOLUTE_MIN_MAXSIZE",
    "DEFAULT_MAXSIZE",
    "EventQueueStats",
    "QueueEmpty",
    "QueueFull",
    "SubAgentEventQueue",
    "get_event_queue",
    "get_global_event_queue",
    "reset_global_event_queue",
]
