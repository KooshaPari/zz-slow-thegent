<DONE>
# Conversation Dump: WL-080 InterAgentProtocol Implementation

**Date:** 2026-02-20
**Task:** WL-080 — InterAgentProtocol: Typed Message Schema
**Status:** COMPLETED

---

## Issues Addressed

- WL-080 was pending with no implementation for `InterAgentMessage` and `MessageBus`.
- Several downstream WL items (WL-081, WL-082, WL-083, WL-085) were blocked on WL-080.

---

## Fixes Applied

### New file: `src/thegent/orchestration/inter_agent_protocol.py`

- `InterAgentMessage` — Pydantic v2 BaseModel with:
  - `id: str` — UUID4, auto-generated via `default_factory=lambda: str(uuid.uuid4())`
  - `sender_id: str`
  - `recipient_id: str`
  - `message_type: Literal["task_request", "status_update", "result", "error", "heartbeat"]`
  - `payload: dict[str, Any]`
  - `correlation_id: str | None = None`
  - `created_at: datetime` — UTC auto-default via `default_factory=lambda: datetime.now(timezone.utc)`
  - `ttl_s: int = 300`

- `MessageBus` — in-memory bus using `asyncio.Queue` per subscriber:
  - `subscribe(agent_id)` — creates or returns existing queue; idempotent
  - `unsubscribe(agent_id)` — removes queue; raises `KeyError` if not subscribed (fail-fast)
  - `publish(msg)` — puts msg into recipient's queue; raises `KeyError` if recipient not subscribed (fail-fast)
  - `drain(agent_id, timeout_s=1.0)` — non-blocking FIFO drain; raises `KeyError` if not subscribed

### New file: `tests/test_wl080_inter_agent_protocol.py`

32 tests across 6 test classes:

- `TestInterAgentMessageDefaults` — id format, UUID4, created_at UTC, uniqueness, correlation_id=None, ttl_s=300
- `TestInterAgentMessageTypes` — all 5 literals accepted, invalid type raises
- `TestInterAgentMessageFields` — explicit field overrides
- `TestMessageBusSubscription` — subscribe returns Queue, idempotent, unsubscribe, unsubscribe unknown raises
- `TestMessageBusPublish` — delivery to recipient, isolation from others, unknown recipient raises, FIFO, identity preservation
- `TestMessageBusDrain` — returns all pending, empty list, clears queue, unknown agent raises, FIFO order, timeout_s param accepted

All 32 tests pass.

---

## Decisions

- Placed in `src/thegent/orchestration/inter_agent_protocol.py` (new file, not modifying existing `protocol.py` which handles a different concern — SubAgentRequest/SubAgentResult JSONL models).
- `unsubscribe` and `publish` to unknown agents raise `KeyError` immediately — fail-fast, no silent swallowing.
- `drain` is synchronous/non-blocking (`get_nowait` loop); `timeout_s` is accepted for future async callers but not used in this implementation.
- `subscribe` is idempotent (returns same queue if already subscribed) — prevents duplicate queue creation bugs.

---

## Open Questions

- None. WL-080 is fully self-contained.
- Downstream items (WL-082 MessageRouter, WL-083 AgentRegistry) can now unblock.

---

## Test Results

```
32 passed in 16.60s
```

All tests have `# @trace WL-080` comments for FR traceability.
