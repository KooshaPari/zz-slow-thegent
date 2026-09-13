## <DONE>

title: WL-082 SubAgentDispatcher Implementation
date: 2026-02-20
status: completed
owner: claude-sonnet-4-6
tags: [orchestration, wl-082, sub-agent-dispatcher, message-bus]

---

# WL-082: SubAgentDispatcher Implementation

## Issues Addressed

- WL-082 was pending, blocked by WL-080 (InterAgentProtocol) and WL-081 (OrchestrationPlan), both of which are COMPLETED.
- Task required creating `src/thegent/orchestration/sub_agent_dispatcher.py` with `SubAgentDispatcher` class.
- 30+ tests required with `# @trace WL-082` annotation.

## Research Findings

### Existing Interface Review

**`InterAgentMessage` (WL-080)** — `src/thegent/orchestration/inter_agent_protocol.py`:

- Pydantic v2 model with fields: `id` (UUID4 auto), `sender_id`, `recipient_id`, `message_type` (Literal), `payload` (dict), `correlation_id` (optional), `created_at`, `ttl_s`
- `message_type` accepts: `"task_request"`, `"status_update"`, `"result"`, `"error"`, `"heartbeat"`

**`MessageBus` (WL-080)**:

- `subscribe(agent_id)` — auto-idempotent, returns queue
- `unsubscribe(agent_id)` — raises `KeyError` if not subscribed
- `publish(msg)` — raises `KeyError` if recipient not subscribed (puts to queue)
- `drain(agent_id, timeout_s)` — non-blocking synchronous drain; `timeout_s` accepted for API compat

**`PlanNode` (base: plangent.py)**:

- Fields: `id`, `task`, `depends_on` (list of node ids), `status`, `result`, `error`, `metadata` (dict)
- `metadata` dict stores orchestration keys via string constants

**`OrchestrationPlan` (WL-081)** — `src/thegent/orchestration/plan.py`:

- Extends `Plan` (dataclass) with `add_task()`, `from_goal()`, `total_budget_used()`
- Node metadata key `AGENT_HINT = "agent_hint"` — identifies the target agent for a node

### Key Design Decisions

1. **Recipient resolution**: `agent_hint` metadata key used when present; falls back to `node.id` as recipient. This makes every node dispatchable without requiring agent_hint.

2. **Auto-subscribe**: `MessageBus.publish()` raises `KeyError` if recipient not subscribed. The dispatcher calls `bus.subscribe(recipient_id)` before every `bus.publish()` — this is idempotent (existing subscription is returned unchanged). This eliminates the need for callers to pre-register agents.

3. **`dispatch_all` ordering**: Kahn's BFS topological sort algorithm. Builds in-degree counts and adjacency (dependent) lists; drains from a queue of zero-in-degree nodes. Guarantees parents are dispatched before children in any DAG (linear chain, diamond, fan-out, multiple roots).

4. **`correlation_id`**: Set to `self.plan.id` on every dispatched message, linking messages back to their originating plan.

5. **`sender_id`**: Auto-generated as `f"dispatcher-{uuid4()}"` at construction time; consistent across all messages from the same dispatcher instance.

6. **`collect_results`**: Thin wrapper around `bus.drain()` with auto-subscribe; `timeout_s` parameter accepted for API symmetry (not used in synchronous implementation, consistent with `MessageBus.drain` pattern).

7. **No fallbacks**: All errors propagate immediately. `KeyError` from unsubscribed bus operations surface without suppression. `ValueError` from invalid inputs propagate directly.

## Fixes Applied

None — this was a net-new implementation.

## Implementation Summary

### Files Created

**`src/thegent/orchestration/sub_agent_dispatcher.py`**

- `SubAgentDispatcher` class with:
  - Constructor: `__init__(self, *, bus: MessageBus, plan: OrchestrationPlan)`
  - Attributes: `bus`, `plan`, `sender_id`
  - `dispatch(plan_node: PlanNode) -> str`
  - `dispatch_all(plan: OrchestrationPlan) -> list[str]`
  - `collect_results(agent_id: str, timeout_s: float = 5.0) -> list[InterAgentMessage]`
- Uses Kahn's BFS topological sort for dependency ordering in `dispatch_all`
- Uses `AGENT_HINT` constant from `thegent.orchestration.plan` for recipient resolution
- No fallbacks, no silent errors, fail-fast design

**`tests/test_wl082_sub_agent_dispatcher.py`**

- 32 tests (exceeds 30+ requirement)
- All tests carry `# @trace WL-082`
- Coverage domains:
  - Constructor attribute storage (2 tests)
  - `dispatch()`: return type, UUID4, message_type, bus publish, payload contents, correlation_id, sender_id, recipient routing, uniqueness, auto-subscribe, fallback to node.id (13 tests)
  - `dispatch_all()`: return type, empty plan, single node, count per node, id uniqueness, linear chain ordering, diamond DAG, multiple roots, parallel leaves (9 tests)
  - `collect_results()`: return type, empty queue, messages returned, type checking, zero timeout, auto-subscribe (5 tests)
  - Integration / edge cases: multi-agent routing, plan correlation_id across all messages, consistent sender_id (3 tests)

## Plans

WL-082 is COMPLETED. Downstream items now unblocked:

- WL-084: PlangentExecutor Integration (Blocked by WL-082, WL-083)
- WL-085: SubAgentEvent Streaming (Blocked by WL-082)
- WL-087: LLM-Backed Plan Decomposition (Blocked by WL-082)
- WL-089: ComputePoolManager Integration (Blocked by WL-082)

## Open Questions

- WL-082 work stream description referenced `CapabilityIndex.recommend()`, `asyncio.gather` with semaphore (concurrency), `asyncio.wait_for` for per-node timeouts, and `PolicyEngine.await_approval()` for HITL gates. The task specification provided to this session did not include those components. The implementation is scoped to exactly what the task specification requested. These features may be layered in via WL-084 or a follow-up WL.

## Validation Commands

```bash
uv run pytest tests/test_wl082_sub_agent_dispatcher.py -v
# Expected: 32 passed
```

## Residual Risks

None identified. Implementation is minimal and direct, with no cross-cutting concerns beyond what WL-080 and WL-081 already provide.

## Follow-up Review Date

2026-03-20 (30 days)
