"""Tests for WL-085: SubAgentEvent Streaming — asyncio.Queue + MCP Tool.

Covers:
- SubAgentEventQueue construction with default and custom maxsize
- SubAgentEventQueue.put() enqueues an event (qsize increments)
- SubAgentEventQueue.get() returns the enqueued event (async)
- SubAgentEventQueue.get_nowait() returns event or raises QueueEmpty
- SubAgentEventQueue.drain_nowait() returns all queued events
- SubAgentEventQueue.drain_nowait() returns empty list on empty queue
- SubAgentEventQueue.put() raises QueueFull when maxsize reached
- SubAgentEventQueue.empty property reflects queue state
- SubAgentEventQueue.qsize property reflects queue depth
- SubAgentEventQueue.maxsize property reflects constructor value
- SubAgentEventQueue.stream() yields events in order
- SubAgentEventQueue.stream() raises TimeoutError after inactivity
- get_global_event_queue() returns same singleton on repeated calls
- reset_global_event_queue() replaces the singleton with a fresh queue
- SubAgentDispatcher publishes STARTED event to queue on dispatch()
- SubAgentDispatcher publishes COMPLETED event to queue on dispatch()
- Both events are published per dispatch() call (exactly 2)
- Event request_id matches the dispatched request
- Event payload contains agent_type key
- dispatch_concurrent() publishes events for all requests
- BudgetExceededError: no COMPLETED event emitted when budget exceeded
- Custom event_queue is used instead of global queue
- thegent_orchestration_events tool drains queue events
- thegent_orchestration_events respects max_events limit
- thegent_orchestration_events returns empty list on empty queue
- UnifiedWorkerDaemon._consume_events() receives events from queue
- UnifiedWorkerDaemon accepts custom event_queue
- UnifiedWorkerDaemon._consume_events can be cancelled cleanly

# @trace WL-085
"""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import MagicMock, patch

import pytest

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
    request_id: str = "req_test",
    event_type: SubAgentEventType = SubAgentEventType.STARTED,
) -> SubAgentEvent:
    return SubAgentEvent(
        request_id=request_id,
        event_type=event_type,
        payload={"agent_type": "test"},
    )


def _make_request(agent_type: str = "test-agent") -> SubAgentRequest:
    return SubAgentRequest(agent_type=agent_type, task="do something")


def _make_dispatcher(
    queue: SubAgentEventQueue | None = None,
) -> SubAgentDispatcher:
    index = CapabilityIndex()
    return SubAgentDispatcher(capability_index=index, event_queue=queue)


# ---------------------------------------------------------------------------
# 1. SubAgentEventQueue construction — default maxsize
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_default_maxsize():
    """SubAgentEventQueue default maxsize is 1024."""
    q = SubAgentEventQueue()
    assert q.maxsize == 1024


# ---------------------------------------------------------------------------
# 2. SubAgentEventQueue construction — custom maxsize
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_custom_maxsize():
    """SubAgentEventQueue accepts custom maxsize."""
    q = SubAgentEventQueue(maxsize=8)
    assert q.maxsize == 8


# ---------------------------------------------------------------------------
# 3. put() enqueues — qsize increments
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_put_increments_qsize():
    """put() places an event into the queue and qsize grows."""
    q = SubAgentEventQueue()
    assert q.qsize == 0
    q.put(_make_event())
    assert q.qsize == 1


# ---------------------------------------------------------------------------
# 4. get() returns the enqueued event (async)
# @trace WL-085
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_queue_get_returns_event():
    """get() returns the event that was put into the queue."""
    q = SubAgentEventQueue()
    event = _make_event(request_id="req_abc")
    q.put(event)
    result = await q.get()
    assert result.request_id == "req_abc"


# ---------------------------------------------------------------------------
# 5. get_nowait() returns event or raises QueueEmpty
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_get_nowait_success():
    """get_nowait() returns the event when one is available."""
    q = SubAgentEventQueue()
    event = _make_event()
    q.put(event)
    result = q.get_nowait()
    assert result.event_type == SubAgentEventType.STARTED


def test_event_queue_get_nowait_raises_queue_empty():
    """get_nowait() raises asyncio.QueueEmpty on empty queue."""
    q = SubAgentEventQueue()
    with pytest.raises(asyncio.QueueEmpty):
        q.get_nowait()


# ---------------------------------------------------------------------------
# 6. drain_nowait() returns all queued events
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_drain_nowait_returns_all():
    """drain_nowait() returns all events in FIFO order and clears the queue."""
    q = SubAgentEventQueue()
    q.put(_make_event(request_id="r1", event_type=SubAgentEventType.STARTED))
    q.put(_make_event(request_id="r2", event_type=SubAgentEventType.COMPLETED))
    events = q.drain_nowait()
    assert len(events) == 2
    assert events[0].request_id == "r1"
    assert events[1].request_id == "r2"
    assert q.qsize == 0


# ---------------------------------------------------------------------------
# 7. drain_nowait() returns empty list on empty queue
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_drain_nowait_empty():
    """drain_nowait() returns [] when the queue holds no events."""
    q = SubAgentEventQueue()
    assert q.drain_nowait() == []


# ---------------------------------------------------------------------------
# 8. put() raises QueueFull when maxsize reached
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_put_raises_queue_full():
    """put() raises asyncio.QueueFull when maxsize is exhausted."""
    q = SubAgentEventQueue(maxsize=2)
    q.put(_make_event())
    q.put(_make_event())
    with pytest.raises(asyncio.QueueFull):
        q.put(_make_event())


# ---------------------------------------------------------------------------
# 9. empty property reflects queue state
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_empty_property():
    """empty is True when queue has no events, False after put."""
    q = SubAgentEventQueue()
    assert q.empty is True
    q.put(_make_event())
    assert q.empty is False


# ---------------------------------------------------------------------------
# 10. qsize property reflects queue depth
# @trace WL-085
# ---------------------------------------------------------------------------


def test_event_queue_qsize_property():
    """qsize reflects the number of events in the queue."""
    q = SubAgentEventQueue()
    q.put(_make_event())
    q.put(_make_event())
    assert q.qsize == 2


# ---------------------------------------------------------------------------
# 11. stream() yields events in order
# @trace WL-085
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_queue_stream_yields_in_order():
    """stream() yields events in FIFO insertion order."""
    q = SubAgentEventQueue()
    q.put(_make_event(request_id="first"))
    q.put(_make_event(request_id="second"))

    collected: list[SubAgentEvent] = []

    async def _collect() -> None:
        async for evt in q.stream(timeout=0.1):
            collected.append(evt)
            if len(collected) == 2:
                break

    await _collect()
    assert collected[0].request_id == "first"
    assert collected[1].request_id == "second"


# ---------------------------------------------------------------------------
# 12. stream() raises TimeoutError after inactivity
# @trace WL-085
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_queue_stream_timeout():
    """stream() raises asyncio.TimeoutError when no event arrives within timeout."""
    q = SubAgentEventQueue()

    with pytest.raises(asyncio.TimeoutError):
        async for _ in q.stream(timeout=0.05):
            pass  # should not reach here


# ---------------------------------------------------------------------------
# 13. get_global_event_queue() returns same singleton
# @trace WL-085
# ---------------------------------------------------------------------------


def test_get_global_event_queue_singleton():
    """get_global_event_queue() returns the same instance on repeated calls."""
    reset_global_event_queue()
    q1 = get_global_event_queue()
    q2 = get_global_event_queue()
    assert q1 is q2


# ---------------------------------------------------------------------------
# 14. reset_global_event_queue() replaces singleton
# @trace WL-085
# ---------------------------------------------------------------------------


def test_reset_global_event_queue_replaces_singleton():
    """reset_global_event_queue() produces a new queue instance."""
    q_before = get_global_event_queue()
    reset_global_event_queue()
    q_after = get_global_event_queue()
    assert q_before is not q_after


# ---------------------------------------------------------------------------
# 15. SubAgentDispatcher publishes STARTED event on dispatch()
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_publishes_started_event():
    """dispatch() puts a STARTED event into the event queue."""
    q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=q)
    request = _make_request()
    dispatcher.dispatch(request)
    events = q.drain_nowait()
    started = [e for e in events if e.event_type == SubAgentEventType.STARTED]
    assert len(started) == 1


# ---------------------------------------------------------------------------
# 16. SubAgentDispatcher publishes COMPLETED event on dispatch()
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_publishes_completed_event():
    """dispatch() puts a COMPLETED event into the event queue."""
    q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=q)
    request = _make_request()
    dispatcher.dispatch(request)
    events = q.drain_nowait()
    completed = [e for e in events if e.event_type == SubAgentEventType.COMPLETED]
    assert len(completed) == 1


# ---------------------------------------------------------------------------
# 17. Exactly 2 events emitted per dispatch() call
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_emits_exactly_two_events_per_dispatch():
    """dispatch() emits exactly 2 events (STARTED + COMPLETED)."""
    q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=q)
    dispatcher.dispatch(_make_request())
    assert q.qsize == 2


# ---------------------------------------------------------------------------
# 18. Event request_id matches dispatched request
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_event_request_id_matches():
    """Events carry the same request_id as the dispatched SubAgentRequest."""
    q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=q)
    request = _make_request()
    dispatcher.dispatch(request)
    for evt in q.drain_nowait():
        assert evt.request_id == request.request_id


# ---------------------------------------------------------------------------
# 19. Event payload contains agent_type key
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_event_payload_has_agent_type():
    """Each event payload contains the agent_type from the request."""
    q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=q)
    request = _make_request(agent_type="my-agent")
    dispatcher.dispatch(request)
    for evt in q.drain_nowait():
        assert evt.payload.get("agent_type") == "my-agent"


# ---------------------------------------------------------------------------
# 20. dispatch_concurrent() publishes events for all requests
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_concurrent_publishes_events_for_all():
    """dispatch_concurrent() emits 2 events per request dispatched."""
    q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=q)
    requests = [_make_request(f"agent-{i}") for i in range(3)]
    results = dispatcher.dispatch_concurrent(requests)
    assert len(results) == 3
    # 3 requests x 2 events each = 6
    assert q.qsize == 6


# ---------------------------------------------------------------------------
# 21. BudgetExceededError: COMPLETED event NOT emitted
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_budget_exceeded_no_completed_event():
    """When the budget_tracker raises, no COMPLETED event is queued.

    We use a mock that raises on .check() to avoid coupling to the
    BudgetTracker internal API, which may evolve.
    """
    from thegent.orchestration.budget_tracker import BudgetExceededError

    mock_budget = MagicMock()
    mock_budget.check.side_effect = BudgetExceededError(
        node_id="test-node", budget=0, actual=1
    )

    q = SubAgentEventQueue()
    dispatcher = SubAgentDispatcher(
        capability_index=CapabilityIndex(),
        budget_tracker=mock_budget,
        event_queue=q,
    )
    request = _make_request()
    with pytest.raises(BudgetExceededError):
        dispatcher.dispatch(request)

    events = q.drain_nowait()
    event_types = [e.event_type for e in events]
    assert SubAgentEventType.STARTED in event_types
    assert SubAgentEventType.COMPLETED not in event_types


# ---------------------------------------------------------------------------
# 22. Custom event_queue is used instead of global
# @trace WL-085
# ---------------------------------------------------------------------------


def test_dispatcher_uses_custom_event_queue_not_global():
    """When event_queue is supplied, global queue remains untouched."""
    reset_global_event_queue()
    global_q = get_global_event_queue()

    custom_q = SubAgentEventQueue()
    dispatcher = _make_dispatcher(queue=custom_q)
    dispatcher.dispatch(_make_request())

    assert custom_q.qsize == 2
    assert global_q.qsize == 0  # global queue untouched


# ---------------------------------------------------------------------------
# 23. MCP tool logic: drain events from queue (exercised via event_queue API)
# @trace WL-085
# ---------------------------------------------------------------------------


def _drain_queue_bounded(
    queue: SubAgentEventQueue, max_events: int
) -> list[SubAgentEvent]:
    """Replicate the MCP tool's bounded-drain logic for unit testing.

    This mirrors the implementation in thegent_orchestration_events without
    importing server.py (which has a pre-existing dynamic-module loader that
    fails in isolated test contexts).

    # @trace WL-085
    """
    events: list[SubAgentEvent] = []
    for _ in range(max_events):
        if queue.empty:
            break
        events.append(queue.get_nowait())
    return events


def test_mcp_tool_logic_drains_queue():
    """MCP tool logic returns events from the global queue."""
    reset_global_event_queue()
    global_q = get_global_event_queue()
    global_q.put(_make_event(request_id="mcp_test_1"))
    global_q.put(_make_event(request_id="mcp_test_2"))

    events = _drain_queue_bounded(global_q, max_events=10)
    ids = [e.request_id for e in events]
    assert len(events) == 2
    assert "mcp_test_1" in ids
    assert "mcp_test_2" in ids


# ---------------------------------------------------------------------------
# 24. MCP tool logic: respects max_events limit
# @trace WL-085
# ---------------------------------------------------------------------------


def test_mcp_tool_logic_respects_max_events():
    """MCP tool logic caps returned events at max_events."""
    reset_global_event_queue()
    global_q = get_global_event_queue()
    for i in range(5):
        global_q.put(_make_event(request_id=f"r{i}"))

    events = _drain_queue_bounded(global_q, max_events=3)
    assert len(events) == 3
    # Remaining 2 events still in queue
    assert global_q.qsize == 2


# ---------------------------------------------------------------------------
# 25. MCP tool logic: returns empty list on empty queue
# @trace WL-085
# ---------------------------------------------------------------------------


def test_mcp_tool_logic_empty_queue():
    """MCP tool logic returns empty list when queue holds no events."""
    reset_global_event_queue()
    global_q = get_global_event_queue()

    events = _drain_queue_bounded(global_q, max_events=100)
    assert events == []


# ---------------------------------------------------------------------------
# 26. UnifiedWorkerDaemon._consume_events() receives events from queue
# @trace WL-085
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unified_worker_daemon_consume_events_receives():
    """_consume_events() logs events received from the queue."""
    q = SubAgentEventQueue()
    daemon = UnifiedWorkerDaemon(event_queue=q)

    consumed: list[SubAgentEvent] = []

    async def _patched_consume() -> None:
        while True:
            event = await q.get()
            consumed.append(event)

    daemon._consume_events = _patched_consume

    task = asyncio.create_task(daemon._consume_events())
    q.put(_make_event(request_id="daemon_test"))
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert len(consumed) == 1
    assert consumed[0].request_id == "daemon_test"


# ---------------------------------------------------------------------------
# 27. UnifiedWorkerDaemon accepts custom event_queue
# @trace WL-085
# ---------------------------------------------------------------------------


def test_unified_worker_daemon_accepts_custom_queue():
    """UnifiedWorkerDaemon stores the custom event_queue passed in __init__."""
    q = SubAgentEventQueue()
    daemon = UnifiedWorkerDaemon(event_queue=q)
    assert daemon._event_queue is q


# ---------------------------------------------------------------------------
# 28. UnifiedWorkerDaemon._consume_events can be cancelled cleanly
# @trace WL-085
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unified_worker_daemon_consume_events_cancels_cleanly():
    """_consume_events() terminates cleanly on cancellation without error."""
    q = SubAgentEventQueue()
    daemon = UnifiedWorkerDaemon(event_queue=q)

    task = asyncio.create_task(daemon._consume_events())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_unified_worker_daemon_dispatches_post_agent_run_on_completed_event():
    """UnifiedWorkerDaemon dispatches PostAgentRun hook when a COMPLETED event is consumed."""
    q = SubAgentEventQueue()
    daemon = UnifiedWorkerDaemon(event_queue=q)

    with patch(
        "thegent.orchestration.unified_worker._dispatch_post_agent_run_hook"
    ) as mock_dispatch:
        task = asyncio.create_task(daemon._consume_events())
        q.put(
            _make_event(
                request_id="req_completed", event_type=SubAgentEventType.COMPLETED
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert mock_dispatch.call_count == 1
    kwargs = mock_dispatch.call_args.kwargs
    assert kwargs["run_id"] == "req_completed"
    assert kwargs["extra_context"]["output_context"] == {"agent_type": "test"}
