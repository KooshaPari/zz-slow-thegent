<DONE>
# Conversation Dump — WL-085: SubAgentEvent Streaming

**Date:** 2026-02-20
**Status:** COMPLETED
**Agent:** Claude Sonnet 4.6

---

## Issues Addressed

WL-085: Wire SubAgentEvent emission from SubAgentDispatcher to an asyncio.Queue.
Expose `thegent_orchestration_events` MCP tool. Wire into UnifiedWorkerDaemon.
25+ tests.

---

## Fixes Applied

### 1. New file: `src/thegent/orchestration/event_queue.py`

- `SubAgentEventQueue`: asyncio.Queue wrapper for SubAgentEvent streaming
  - `put(event)` — enqueue without blocking; raises `asyncio.QueueFull` at capacity
  - `get()` — async await for next event
  - `get_nowait()` — non-blocking get or raises `asyncio.QueueEmpty`
  - `drain_nowait()` — drain all events non-blocking
  - `stream(timeout)` — async generator yielding events with inactivity timeout
  - Properties: `qsize`, `maxsize`, `empty`
- `get_global_event_queue()` — lazy process-global singleton
- `reset_global_event_queue()` — test utility to replace singleton

### 2. Modified: `src/thegent/orchestration/sub_agent_dispatcher.py`

- Added `event_queue: SubAgentEventQueue | None = None` parameter to `SubAgentDispatcher.__init__()`
- When `None`, falls back to `get_global_event_queue()` (process-global)
- Renamed `_emit_event()` to `_publish_event()` to reflect queue publishing
- `_publish_event()` now calls `self._event_queue.put(event)` after logging
- Both `dispatch()` and `dispatch_concurrent()` now publish STARTED + COMPLETED events

### 3. Modified: `src/thegent/mcp/server.py`

- Added `thegent_orchestration_events` MCP tool (annotations: readOnlyHint=True)
- Parameters: `max_events: int = 100`, `timeout_ms: int = 0`
- Uses bounded drain (loop of `get_nowait()`) to avoid discarding excess events
- Optional timeout_ms support for blocking-wait via `asyncio.run(_wait_one())`
- Returns `ToolResult` with `structured_content = {"events": [...], "count": N}`

### 4. Modified: `src/thegent/orchestration/unified_worker.py`

- Added `event_queue: SubAgentEventQueue | None = None` to `UnifiedWorkerDaemon.__init__()`
- Added `_event_consumer_task` field (asyncio.Task)
- `start()` creates `asyncio.create_task(self._consume_events())`
- `stop()` cancels the consumer task and awaits its CancelledError cleanly
- `_consume_events()` awaits events from the queue and logs at INFO level

### 5. New file: `tests/test_wl085_sub_agent_events.py`

29 tests, all passing. Covers:

- SubAgentEventQueue: construction, put/get/drain/stream, QueueFull/QueueEmpty
- Singleton: get_global_event_queue() returns same instance; reset replaces it
- SubAgentDispatcher: STARTED+COMPLETED events per dispatch, request_id match, payload
- Concurrent dispatch: 2 events per request across N requests
- Budget exceeded: STARTED emitted, COMPLETED not emitted
- Custom queue isolation: global queue untouched when custom queue supplied
- MCP tool logic: drain bounded, respects max_events, empty queue returns []
- UnifiedWorkerDaemon: accepts custom queue, consume loop receives events, cancels cleanly

---

## Research Findings

- `BudgetExceededError` actual signature: `__init__(self, node_id, budget, actual)` (not `used`)
- `BudgetTracker` runtime API: `track(node_id, tokens_used)` not `check()`
- `ToolResult.content` is `list[TextContent]` when called directly; use `.structured_content` for dict access in tests
- `server.py` has a pre-existing dynamic module loader (`_load_server_session_tools_module`) that
  resolves `Path(__file__).with_suffix("") / "server" / "session_tools.py"` — this resolves to
  an invalid path in isolated test contexts, so MCP tool tests were refactored to test the
  queue-drain logic directly without importing server.py

---

## Plans

None — implementation complete.

---

## Open Questions

- Should `drain_nowait()` accept an optional `max_count` parameter for callers that want bounded drain without `get_nowait()` loops? Low priority; current pattern is clean.
- The `_server_session_tools` loader path issue in `server.py` is pre-existing; should be investigated separately as a path resolution bug.

---

## Next Steps

- WL-086: BudgetTracker per-node enforcement (blocked on WL-080, now unblocked)
- WL-084: PlangentExecutor + SubAgentDispatcher integration (blocked on WL-082, WL-083)
