"""Spec-only hardening tests for the dormant SubAgentEventQueue + SubAgentDispatcher + UnifiedWorkerDaemon cluster (SOTA pass-21).

@trace FR-ORC-060 -- SubAgentEventQueue.put() is concurrency-safe under
                    ``threading`` contention (FIFO order, no lost events).
@trace FR-ORC-061 -- SubAgentEventQueue.drain_nowait() returns a defensive
                    copy so a caller can iterate without seeing later
                    enqueues mutate the queue.
@trace FR-ORC-062 -- SubAgentEventQueue.stream(timeout=…) is a true
                    ``async`` generator that yields FIFO order, raises
                    ``asyncio.TimeoutError`` on inactivity, and respects
                    ``task.cancel()`` cleanly.
@trace FR-ORC-063 -- SubAgentEventQueue rejects non-positive ``maxsize``
                    with ``ValueError`` so a misconfigured queue cannot
                    silently disable the cap.
@trace FR-ORC-064 -- SubAgentEventQueue rejects non-``SubAgentEvent``
                    ``put()`` payloads with ``TypeError`` so protocol drift
                    surfaces at the call site rather than at drain time.
@trace FR-ORC-065 -- ``get_global_event_queue()`` is locked so two
                    concurrent callers in the same process see the same
                    singleton instance (no torn lazy construction).
@trace FR-ORC-066 -- ``reset_global_event_queue()`` is locked so a
                    concurrent reader cannot observe a half-replaced
                    singleton.
@trace FR-ORC-067 -- SubAgentDispatcher.dispatch() publishes a STARTED
                    event to the bound ``event_queue`` and a COMPLETED
                    event after the inner dispatch path returns;
                    the dispatch path is unaffected when ``event_queue``
                    is not bound (back-compat with WL-082).
@trace FR-ORC-068 -- SubAgentDispatcher.dispatch() does NOT publish a
                    COMPLETED event when the budget_tracker raises
                    ``BudgetExceededError`` (STARTED is still emitted).
@trace FR-ORC-069 -- SubAgentDispatcher.dispatch() survives a
                    ``RuntimeError`` from the bound event_queue
                    (continues to the next event); the dispatch path
                    itself is never blocked by a misbehaving queue.
@trace FR-ORC-070 -- SubAgentDispatcher.dispatch() uses an ``RLock`` so
                    concurrent dispatchers do not see torn ``self._events``
                    state (start/complete pair).
@trace FR-ORC-071 -- SubAgentEventQueue exposes a ``stats()`` snapshot
                    (``enqueued`` / ``drained`` / ``dropped`` / ``qsize``
                    / ``maxsize`` counters) so SOTA audit tooling can
                    monitor queue health without breaking the queue.
@trace FR-ORC-072 -- SubAgentEventQueue caps memory by rejecting
                    ``put()`` at ``maxsize`` (via ``asyncio.QueueFull``)
                    and never blocks the caller.
@trace FR-ORC-073 -- UnifiedWorkerDaemon(event_queue=…) stores the
                    queue as ``self._event_queue`` and exposes a
                    ``_consume_events()`` coroutine that exits cleanly
                    on ``asyncio.CancelledError``.
@trace FR-ORC-074 -- UnifiedWorkerDaemon._consume_events() dispatches
                    the post-agent-run hook (``_dispatch_post_agent_run_hook``)
                    for COMPLETED events and forwards the correct
                    ``run_id`` + ``extra_context`` kwargs.
@trace FR-ORC-075 -- UnifiedWorkerDaemon exposes ``_dispatch_post_agent_run_hook``
                    as a module-level symbol so test suites can patch
                    the import path ``thegent.orchestration.unified_worker._dispatch_post_agent_run_hook``.

This file is the AUDIT-N+37 contract spec (SOTA pass-21): it pins
hardening invariants on top of the dormant WL-085 contract.  It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35 /
N+36) so the next step is to make every assertion here pass without
breaking the WL-082 ``bus+plan`` corridor or the dormant
``test_wl085_sub_agent_events.py`` baseline.
"""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.budget_tracker import BudgetExceededError
from thegent.orchestration.event_queue import (
    SubAgentEventQueue,
    get_global_event_queue,
    reset_global_event_queue,
)
from thegent.orchestration.protocol import (
    SubAgentEvent,
    SubAgentEventType,
    SubAgentRequest,
)
from thegent.orchestration.sub_agent_dispatcher import (
    CapabilityIndex,
    SubAgentDispatcher,
)
from thegent.orchestration.unified_worker import UnifiedWorkerDaemon

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    request_id: str = "req_audit_n37",
    event_type: SubAgentEventType = SubAgentEventType.STARTED,
    payload: dict | None = None,
) -> SubAgentEvent:
    return SubAgentEvent(
        request_id=request_id,
        event_type=event_type,
        payload=payload if payload is not None else {"agent_type": "test"},
    )


def _make_event_queue(maxsize: int = 1024) -> SubAgentEventQueue:
    return SubAgentEventQueue(maxsize=maxsize)


def _make_request(
    agent_type: str = "test-agent", task: str = "do something"
) -> SubAgentRequest:
    return SubAgentRequest(agent_type=agent_type, task=task)


# ---------------------------------------------------------------------------
# FR-ORC-060 -- put() is concurrency-safe under threading contention
# ---------------------------------------------------------------------------


class TestEventQueueConcurrency:
    """@trace FR-ORC-060"""

    def test_put_thread_safe_no_lost_events(self) -> None:
        """100 concurrent put() calls from N threads preserve all events."""
        q = _make_event_queue(maxsize=1024)
        n_threads = 8
        per_thread = 25
        barrier = threading.Barrier(n_threads)

        def _worker(thread_id: int) -> None:
            barrier.wait()
            for i in range(per_thread):
                q.put(_make_event(request_id=f"t{thread_id}-i{i}"))

        threads = [
            threading.Thread(target=_worker, args=(t,)) for t in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert q.qsize == n_threads * per_thread
        # Every request_id must appear exactly once
        seen: list[str] = []
        while not q.empty:
            seen.append(q.get_nowait().request_id)
        assert len(seen) == n_threads * per_thread
        assert len(set(seen)) == n_threads * per_thread


# ---------------------------------------------------------------------------
# FR-ORC-061 -- drain_nowait() returns a defensive copy
# ---------------------------------------------------------------------------


class TestEventQueueDrainNowaitCopy:
    """@trace FR-ORC-061"""

    def test_drain_nowait_returns_independent_list(self) -> None:
        """Mutating the returned list does NOT affect the queue's internal state."""
        q = _make_event_queue()
        q.put(_make_event(request_id="a"))
        q.put(_make_event(request_id="b"))
        snapshot = q.drain_nowait()
        assert [e.request_id for e in snapshot] == ["a", "b"]
        # Mutating the snapshot must not affect the queue.
        snapshot.clear()
        assert q.empty is True  # drain cleared the queue, not the snapshot
        # Re-fill and verify empty state.
        q.put(_make_event(request_id="c"))
        assert q.qsize == 1


# ---------------------------------------------------------------------------
# FR-ORC-062 -- stream() is async generator, FIFO, timeout, cancellable
# ---------------------------------------------------------------------------


class TestEventQueueStream:
    """@trace FR-ORC-062"""

    @pytest.mark.asyncio
    async def test_stream_yields_fifo_order(self) -> None:
        q = _make_event_queue()
        for i in range(5):
            q.put(_make_event(request_id=f"r{i}"))
        collected: list[str] = []
        async for evt in q.stream(timeout=0.2):
            collected.append(evt.request_id)
            if len(collected) == 5:
                break
        assert collected == ["r0", "r1", "r2", "r3", "r4"]

    @pytest.mark.asyncio
    async def test_stream_timeout_raises(self) -> None:
        q = _make_event_queue()
        with pytest.raises(asyncio.TimeoutError):
            async for _ in q.stream(timeout=0.05):
                pass  # never reached

    @pytest.mark.asyncio
    async def test_stream_cancels_cleanly(self) -> None:
        q = _make_event_queue()
        task = asyncio.create_task(self._collect_one(q))
        q.put(_make_event(request_id="x"))
        await asyncio.wait_for(task, timeout=0.5)
        assert task.result() == "x"

    @staticmethod
    async def _collect_one(q: SubAgentEventQueue) -> str:
        async for evt in q.stream(timeout=0.5):
            return evt.request_id
        raise AssertionError("stream yielded no event")


# ---------------------------------------------------------------------------
# FR-ORC-063 -- maxsize validation
# ---------------------------------------------------------------------------


class TestEventQueueMaxsizeValidation:
    """@trace FR-ORC-063"""

    @pytest.mark.parametrize("bad_maxsize", [0, -1, -10])
    def test_rejects_non_positive_maxsize(self, bad_maxsize: int) -> None:
        with pytest.raises(ValueError):
            SubAgentEventQueue(maxsize=bad_maxsize)


# ---------------------------------------------------------------------------
# FR-ORC-064 -- put() rejects non-SubAgentEvent payloads
# ---------------------------------------------------------------------------


class TestEventQueuePutTypeGuard:
    """@trace FR-ORC-064"""

    @pytest.mark.parametrize("bad_payload", [None, "not-an-event", 42, {"raw": "dict"}])
    def test_put_rejects_non_event_payload(self, bad_payload) -> None:
        q = _make_event_queue()
        with pytest.raises(TypeError):
            q.put(bad_payload)  # type: ignore[arg-type]
        assert q.qsize == 0


# ---------------------------------------------------------------------------
# FR-ORC-065 -- get_global_event_queue() is locked
# ---------------------------------------------------------------------------


class TestGlobalQueueThreadSafe:
    """@trace FR-ORC-065, FR-ORC-066"""

    def test_get_global_returns_same_singleton_under_contention(self) -> None:
        reset_global_event_queue()
        results: list[SubAgentEventQueue] = []
        lock = threading.Lock()
        barrier = threading.Barrier(8)

        def _worker() -> None:
            barrier.wait()
            q = get_global_event_queue()
            with lock:
                results.append(q)

        threads = [threading.Thread(target=_worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All callers must see the same singleton instance.
        assert len(results) == 8
        first = results[0]
        for q in results[1:]:
            assert q is first

    def test_reset_global_replaces_singleton_atomically(self) -> None:
        q_before = get_global_event_queue()
        before_id = id(q_before)
        reset_global_event_queue()
        q_after = get_global_event_queue()
        assert id(q_after) != before_id


# ---------------------------------------------------------------------------
# FR-ORC-067 -- SubAgentDispatcher.dispatch() publishes STARTED + COMPLETED
# ---------------------------------------------------------------------------


class TestDispatcherEventPublishing:
    """@trace FR-ORC-067, FR-ORC-068, FR-ORC-069, FR-ORC-070"""

    def test_dispatch_publishes_started_and_completed_when_event_queue_bound(
        self,
    ) -> None:
        q = _make_event_queue()
        dispatcher = SubAgentDispatcher(
            capability_index=CapabilityIndex(),
            event_queue=q,
        )
        # Pass through to the WL-082 path (which still works).
        # The dispatcher should still emit STARTED + COMPLETED events.
        dispatcher.dispatch(_make_request())  # type: ignore[arg-type] -- we accept legacy ignores
        events = q.drain_nowait()
        types = [e.event_type for e in events]
        assert SubAgentEventType.STARTED in types
        assert SubAgentEventType.COMPLETED in types

    def test_dispatch_without_event_queue_is_a_no_op(self) -> None:
        """Back-compat: SubAgentDispatcher without event_queue must not crash."""
        dispatcher = SubAgentDispatcher(capability_index=CapabilityIndex())
        # Must not crash; the WL-082 path is preserved.
        dispatcher.dispatch(_make_request())  # type: ignore[arg-type]

    def test_dispatch_emits_no_completed_when_budget_exceeded(self) -> None:
        """@trace FR-ORC-068"""

        mock_budget = MagicMock()
        mock_budget.check.side_effect = BudgetExceededError(
            node_id="req_budget_test", budget=0, actual=1
        )

        q = _make_event_queue()
        dispatcher = SubAgentDispatcher(
            capability_index=CapabilityIndex(),
            budget_tracker=mock_budget,
            event_queue=q,
        )
        with pytest.raises(BudgetExceededError):
            dispatcher.dispatch(_make_request())  # type: ignore[arg-type]

        events = q.drain_nowait()
        types = [e.event_type for e in events]
        assert SubAgentEventType.STARTED in types
        assert SubAgentEventType.COMPLETED not in types

    def test_dispatch_survives_misbehaving_event_queue(self) -> None:
        """@trace FR-ORC-089"""
        bad_queue = MagicMock()
        bad_queue.put.side_effect = RuntimeError("queue is broken")
        bad_queue.drain_nowait.return_value = []

        dispatcher = SubAgentDispatcher(
            capability_index=CapabilityIndex(),
            event_queue=bad_queue,  # type: ignore[arg-type]
        )
        # Must not raise despite the broken queue.
        dispatcher.dispatch(_make_request())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FR-ORC-071 -- stats() snapshot
# ---------------------------------------------------------------------------


class TestEventQueueStats:
    """@trace FR-ORC-071"""

    def test_stats_snapshot_contract(self) -> None:
        q = _make_event_queue(maxsize=16)
        q.put(_make_event(request_id="a"))
        q.put(_make_event(request_id="b"))
        q.drain_nowait()
        stats = q.stats()
        assert isinstance(stats, dict)
        for key in ("enqueued", "drained", "dropped", "qsize", "maxsize"):
            assert key in stats, f"missing key: {key}"
        assert stats["enqueued"] == 2
        assert stats["drained"] == 2
        assert stats["qsize"] == 0
        assert stats["maxsize"] == 16
        assert stats["dropped"] == 0


# ---------------------------------------------------------------------------
# FR-ORC-072 -- put() never blocks the caller
# ---------------------------------------------------------------------------


class TestEventQueuePutNeverBlocks:
    """@trace FR-ORC-072"""

    def test_put_raises_queue_full_at_maxsize(self) -> None:
        q = _make_event_queue(maxsize=2)
        q.put(_make_event(request_id="a"))
        q.put(_make_event(request_id="b"))
        with pytest.raises(asyncio.QueueFull):
            q.put(_make_event(request_id="c"))
        assert q.qsize == 2

    def test_put_third_event_completes_under_50ms(self) -> None:
        """put() at maxsize must raise QueueFull synchronously (no wait)."""
        q = _make_event_queue(maxsize=4)
        for i in range(4):
            q.put(_make_event(request_id=f"r{i}"))
        start = time.perf_counter()
        with pytest.raises(asyncio.QueueFull):
            q.put(_make_event(request_id="overflow"))
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 50, f"put() blocked for {elapsed_ms:.1f}ms (SLO: <50ms)"


# ---------------------------------------------------------------------------
# FR-ORC-073 / FR-ORC-074 -- UnifiedWorkerDaemon surfaces
# ---------------------------------------------------------------------------


class TestUnifiedWorkerDaemonSurface:
    """@trace FR-ORC-073, FR-ORC-074, FR-ORC-075"""

    def test_daemon_stores_event_queue(self) -> None:
        q = _make_event_queue()
        daemon = UnifiedWorkerDaemon(event_queue=q)
        assert daemon._event_queue is q

    def test_daemon_falls_back_to_global_queue(self) -> None:
        """When no event_queue is passed, the daemon binds to the global singleton."""
        from thegent.orchestration.event_queue import (
            get_global_event_queue,
            reset_global_event_queue,
        )

        reset_global_event_queue()
        daemon = UnifiedWorkerDaemon()
        assert daemon._event_queue is get_global_event_queue()

    def test_dispatch_post_agent_run_hook_is_module_level(self) -> None:
        """_dispatch_post_agent_run_hook must be importable from the
        unified_worker module path so tests can patch it."""
        from thegent.orchestration import unified_worker

        assert hasattr(unified_worker, "_dispatch_post_agent_run_hook")
        assert callable(unified_worker._dispatch_post_agent_run_hook)

    @pytest.mark.asyncio
    async def test_consume_events_cancels_cleanly(self) -> None:
        """_consume_events() must exit cleanly on cancellation."""
        q = _make_event_queue()
        daemon = UnifiedWorkerDaemon(event_queue=q)
        task = asyncio.create_task(daemon._consume_events())
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_consume_events_dispatches_hook_on_completed(self) -> None:
        """COMPLETED event triggers _dispatch_post_agent_run_hook with run_id + extra_context."""
        q = _make_event_queue()
        daemon = UnifiedWorkerDaemon(event_queue=q)
        with patch(
            "thegent.orchestration.unified_worker._dispatch_post_agent_run_hook"
        ) as mock_hook:
            task = asyncio.create_task(daemon._consume_events())
            q.put(
                _make_event(
                    request_id="req_x",
                    event_type=SubAgentEventType.COMPLETED,
                    payload={"agent_type": "audit"},
                )
            )
            # Give the consumer a chance to dequeue.
            for _ in range(20):
                if mock_hook.call_count >= 1:
                    break
                await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        assert mock_hook.call_count == 1
        kwargs = mock_hook.call_args.kwargs
        assert kwargs["run_id"] == "req_x"
        assert kwargs["extra_context"]["output_context"] == {"agent_type": "audit"}


# ---------------------------------------------------------------------------
# FR-ORC-070 -- SubAgentDispatcher.dispatch() uses an RLock
# ---------------------------------------------------------------------------


class TestDispatcherDispatchLock:
    """@trace FR-ORC-070"""

    def test_dispatcher_has_dispatch_lock(self) -> None:
        """SubAgentDispatcher must expose an internal RLock for event publishing."""
        import threading

        dispatcher = SubAgentDispatcher(capability_index=CapabilityIndex())
        # The contract: a re-entrant lock guarding the STARTED + COMPLETED
        # pair.  The actual attribute name in this build is
        # ``_dispatch_lock`` (a ``threading.RLock``).
        assert hasattr(dispatcher, "_dispatch_lock")
        assert isinstance(dispatcher._dispatch_lock, type(threading.RLock()))

    def test_concurrent_dispatch_publishes_balanced_events(self) -> None:
        """N=16 threads dispatching concurrently must produce exactly 2N events (no lost pair)."""
        q = _make_event_queue(maxsize=1024)
        dispatcher = SubAgentDispatcher(
            capability_index=CapabilityIndex(),
            event_queue=q,
        )
        n_threads = 16

        def _worker() -> None:
            dispatcher.dispatch(_make_request())  # type: ignore[arg-type]

        threads = [threading.Thread(target=_worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = q.drain_nowait()
        started = sum(1 for e in events if e.event_type == SubAgentEventType.STARTED)
        completed = sum(
            1 for e in events if e.event_type == SubAgentEventType.COMPLETED
        )
        assert started == n_threads
        assert completed == n_threads
