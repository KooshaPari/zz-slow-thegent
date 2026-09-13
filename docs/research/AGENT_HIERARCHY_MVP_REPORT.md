<DONE>
# Agent Hierarchy MVP Report

**Date**: 2026-02-19
**Task**: research-agent-hierarchy-mvp
**Status**: COMPLETE

---

## 1. Research Findings

### Existing Infrastructure

The codebase already has two distinct agent hierarchy layers:

| Layer | Location | Purpose |
|-------|----------|---------|
| Governance hierarchy | `src/thegent/governance/agent_hierarchy.py` | Persistence-backed (JSON files), role-based (EXECUTIVE / TEAM_LEAD / SPECIALIST), team management, delegation policy enforcement |
| Research stub | `src/thegent/research/agent_hierarchy.py` | Minimal 60-line prototype — register + get_children + get_hierarchy_path |
| Crew executor | `src/thegent/crew/executor.py` | TaskExecutor with topological DAG resolution; AgentAssigner strategies (RoundRobin, SkillBased, Hierarchical) |
| Harness | `src/thegent/crew/harness.py` | Bridges crew tasks to CLI agents (codex/claude/copilot/gemini) via DirectAgentRunner |

### SmolAgents v1.24.0 Integration Points

SmolAgents `ManagedAgent` was renamed in v1.x; the current API (v1.24.0) uses:
- `MultiStepAgent` (base class) with `managed_agents: list[Agent]` parameter — the orchestrator loads sub-agents as callable tools automatically via `_setup_managed_agents`.
- `CodeAgent` — writes and executes Python code as its action space.
- `ToolCallingAgent` — uses JSON tool-call format (OpenAI-style).
- Models: `InferenceClientModel`, `LiteLLMModel`, `OpenAIServerModel` (no API keys needed in tests).

Key discovery: When `managed_agents` are set on a `MultiStepAgent`, SmolAgents wraps each sub-agent as a tool callable — the orchestrator can invoke specialists by name in its generated code/tool calls. This is the primary SmolAgents hierarchy pattern.

### Design Decision: New Module vs. Extending Governance

The governance `AgentHierarchyManager` is tightly coupled to persistence (JSON files), role enums, and governance policy. The MVP needs:
- In-memory operation (for speed and testability)
- Capability-based routing (domain skills, not hierarchical roles)
- SmolAgents smolagent attachment per node
- Parallel async execution

**Decision**: New module `src/thegent/agents/hierarchy.py`. The governance module remains for operational governance; this module is the live-execution hierarchy.

---

## 2. Implementation Notes

### File: `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/agents/hierarchy.py`

#### AgentCapability Enum (10 members)
```
CODE, RESEARCH, REVIEW, TEST, DEPLOY, PLAN, SECURITY, DATA, DOCUMENTATION, ORCHESTRATE
```
Uses `auto()` for values; extensible by adding new enum members.

#### AgentState Enum (5 members)
```
IDLE, RUNNING, COMPLETED, FAILED, CANCELLED
```

#### RoutingStrategy Enum (3 members)
```
CAPABILITY_MATCH  — exact set match preferred, partial match fallback
ROUND_ROBIN       — cycles through capable agents per capability bucket
LEAST_LOADED      — picks agent with lowest active_task_count
```

#### AgentNode Dataclass
Key fields:
- `capabilities: set[AgentCapability]` — set operations for O(1) matching
- `smolagent: Any | None` — live SmolAgents agent instance; excluded from `to_dict()` serialisation
- `active_task_count: int` — live counter used by LEAST_LOADED routing
- `total_tasks_completed: int` — historical counter
- `children: list[str]` — child IDs (maintained by manager)
- `parent_id: str | None` — parent ID (maintained by manager)

Helper methods: `has_capability()`, `has_any_capability()`, `to_dict()`

#### AgentHierarchyManager

Constructor parameters:
- `routing_strategy: RoutingStrategy` — defaults to `CAPABILITY_MATCH`
- `task_executor: Callable[[AgentNode, str, dict], TaskResult] | None` — injectable callback for testing/simulation without real LLM calls

**spawn_agent()**: Creates and registers an `AgentNode`. Wires parent↔child links. First registered node becomes root. Raises `ValueError` on duplicate ID or missing parent.

**route_task()**: Selects agent from candidates matching required capabilities. Supports `exclude_ids` to skip busy or failed agents. Returns `None` if no match.

**execute_task()**: Runs a task synchronously. Execution priority:
1. `node.smolagent.run(task_description)` — real SmolAgents integration
2. `self.task_executor(node, task, context)` — injectable mock/simulator
3. `RuntimeError` — explicit failure (not swallowed as task failure)

`RuntimeError` (programming errors) is raised before the `try/except` block so it propagates to the caller rather than being silently converted to `TaskResult(success=False)`.

**execute_parallel()**: Wraps `execute_task` calls in `asyncio.gather`. Handles both sync and async calling contexts (detects running event loop, spawns ThreadPoolExecutor when needed). Preserves input order in returned results.

**collect_results()**: Filters the internal ledger by `agent_id` and/or `success_only`. Returns copies of stored `TaskResult` objects.

**Tree helpers**: `get_children()`, `get_ancestors()`, `get_descendants()`, `get_hierarchy_tree()` (nested dict for serialisation/display).

**summary()**: Returns agent count, task counts, routing strategy, and per-agent dicts.

### File: `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/test_agent_hierarchy_mvp.py`

---

## 3. Test Results

```
59 passed in 29.94s
```

### Test Coverage by Category

| Category | Tests | All Pass |
|----------|-------|----------|
| AgentCapability enum | 2 | Yes |
| AgentState enum | 1 | Yes |
| AgentNode creation/capability/serialisation | 8 | Yes |
| spawn_agent (registration, wiring, validation) | 6 | Yes |
| Agent registry (list/get/root) | 3 | Yes |
| route_task (3 strategies + no-match + exclude) | 6 | Yes |
| execute_task (success, failure, smolagent, state, counters) | 10 | Yes |
| execute_parallel (ordering, concurrency, mixed success) | 3 | Yes |
| collect_results (all, filtered, success-only, clear) | 4 | Yes |
| Tree traversal (children, ancestors, descendants, tree dict) | 9 | Yes |
| remove_agent | 3 | Yes |
| summary | 2 | Yes |
| End-to-end (orchestrator→specialist, parallel) | 2 | Yes |

---

## 4. SmolAgents Integration Pattern

### Attaching a SmolAgents Agent to a Node

```python
from smolagents import ToolCallingAgent, InferenceClientModel
from thegent.agents.hierarchy import AgentHierarchyManager, AgentCapability

model = InferenceClientModel("Qwen/Qwen2.5-72B-Instruct")
sa = ToolCallingAgent(tools=[], model=model, name="coder", description="Writes code")

manager = AgentHierarchyManager()
manager.spawn_agent(
    {AgentCapability.CODE},
    agent_id="coder",
    name="coder",
    smolagent=sa,
)
result = manager.execute_task("coder", "Write a fibonacci function in Python")
```

### Orchestrator with Managed Sub-agents (SmolAgents native pattern)

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel

model = InferenceClientModel("meta-llama/Meta-Llama-3.1-70B-Instruct")

researcher = ToolCallingAgent(tools=[...], model=model, name="researcher", description="Searches the web")
coder = CodeAgent(tools=[], model=model, name="coder", description="Writes and runs code")

# Orchestrator automatically wraps sub-agents as callable tools
orchestrator = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[researcher, coder],
)

# Orchestrator can call researcher("find X") and coder("implement Y")
orchestrator.run("Research best sorting algorithms then implement the fastest one")
```

### Combining Both Patterns

The `AgentHierarchyManager` can wrap the above orchestrator as the root node, while each specialist (with its SmolAgents instance) is a child node. The manager then provides:
- Capability-based routing (which specialist for which task type)
- Parallel dispatch (`execute_parallel`)
- Result collection and summary
- Tree traversal for monitoring

---

## 5. Design Decisions

| Decision | Rationale |
|----------|-----------|
| `set[AgentCapability]` for capabilities | O(1) intersection/subset checks; clean enum namespace |
| Separate from governance hierarchy | Governance needs persistence + policy; this needs speed + SmolAgents attachment |
| `RuntimeError` propagates, `Exception` creates TaskResult | Programming errors (no executor configured) should crash loudly; task execution errors should be handled gracefully |
| `asyncio.gather` in thread when event loop running | Allows `execute_parallel` to be called from both sync and async contexts without forcing the caller to manage loops |
| `task_executor` callback parameter | 100% test coverage without LLM API keys; production code swaps in real SmolAgents calls |
| First spawned node is root | Minimal friction: single-orchestrator pattern is the common case |
| ROUND_ROBIN bucketed per capability | Prevents one capability from monopolising a single index counter |

---

## 6. Open Questions / Next Steps

1. **Persistence**: Add optional JSON/SQLite backend (pattern from `governance/agent_hierarchy.py`) for durable hierarchy state across process restarts.
2. **SmolAgents managed_agents wiring**: Auto-wire child SmolAgents instances as `managed_agents` of the root orchestrator's SmolAgents instance when `spawn_agent` is called.
3. **Capability inference**: Auto-detect capabilities from SmolAgents tool list (e.g., `WebSearchTool` → `RESEARCH`).
4. **Timeout per task**: Add `timeout_seconds` to `execute_task`; wrap `smolagent.run` in `asyncio.wait_for`.
5. **Cost/token tracking**: SmolAgents `MultiStepAgent` exposes `monitor` attribute with token counts — surface these in `TaskResult`.
6. **Dead-letter queue**: When `execute_task` fails, enqueue in `governance.dlq_integration` for retry/escalation.
