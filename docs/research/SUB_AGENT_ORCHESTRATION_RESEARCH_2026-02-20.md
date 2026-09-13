<DONE>
# Sub-Agent Orchestration Research

> **Date**: 2026-02-20
> **Scope**: Gap analysis + design for a first-class sub-agent orchestration layer in thegent
> **Author**: Research agent
> **Related WL items**: WL-080 through WL-089

---

## 1. Executive Summary

thegent currently has the building blocks for sub-agent orchestration: a DAG planner (`PlangentPlanner` + `PlangentExecutor`), a persistent worker pool (`TaskWorkerPool`), flash agents (`FlashAgent`), compute offloading (`ComputePoolManager`), and capability-based auto-selection (`CapabilityIndex`). However, these components are not wired together into a coherent orchestration layer.

Compared to Claude Code (which dispatches up to 7 parallel subagents via the `Task` tool), Codex (which forks threads via the App Server protocol with approval flows and dynamic tools), and Gemini CLI (which provides MCP-backed sub-agent dispatch), thegent lacks:

1. A **typed inter-agent message protocol** — there is no standard schema for sub-agent requests, results, and status events.
2. A **DAG dispatcher** that maps `PlanNode` objects to specific `AgentRunner` implementations selected by `CapabilityIndex`.
3. A **ResultAggregator** that merges partial outputs, propagates failures, and enforces budget caps across a sub-agent wave.
4. **Budget/cost limits** per sub-agent execution slot.
5. **Streaming results** from sub-agents back to an orchestrator in real time.
6. **HITL approval gates** integrated into the sub-agent dispatch loop (the HITL governance system exists at WL-019, but is not wired into the planner).

The proposed design layers a `SubAgentDispatcher`, `ResultAggregator`, `InterAgentProtocol`, and a budget-aware `OrchestrationPlan` on top of existing primitives without replacing them.

---

## 2. Current thegent Sub-Agent Capabilities

### 2.1 PlangentPlanner + PlangentExecutor

**File**: `src/thegent/agents/plangent.py` (WL: `borrow-plangent-subagents`)

The planner decomposes a goal into a `Plan` (a DAG of `PlanNode` objects). Each `PlanNode` has:
- `id`, `task` (natural-language description), `depends_on` (list of prerequisite node IDs)
- `status`: `pending | running | done | failed`
- `result`, `error`, `metadata` (arbitrary dict)

`PlangentExecutor.execute()` (sync) and `execute_async()` (async) iterate waves of `is_ready()` nodes, invoke a caller-supplied `runner(node) -> str` callback, and advance node status. The async path uses `asyncio.gather` to dispatch parallel-ready nodes concurrently.

**Gaps in the existing planner**:
- `_generate_sub_tasks` is a heuristic string-split by default. No LLM-backed decomposition.
- The `runner` callback is untyped and receives no budget, timeout, or model-routing hints from the plan.
- There is no mechanism to propagate a parent run ID or correlation ID through the plan to child executions.
- No streaming: each node's result is a plain `str` collected after the runner returns.

### 2.2 FlashAgent

**File**: `src/thegent/agents/flash_agent.py` (WL: `borrow-dex-flash-agents`)

`FlashAgent` fires a single `litellm.acompletion()` call with a strict `asyncio.wait_for` timeout. Designed for sub-30-second focused tasks. Returns a typed `FlashAgentResult(output, success, elapsed_s, agent_id)`.

**Gaps**: No budget cap, no retry, no result streaming, no parent correlation.

### 2.3 TaskWorkerPool

**File**: `src/thegent/orchestration/worker_pool.py` (MTSP-03)

File-based inbox/results queue. Workers poll `inbox/*.json`, rename to claim, execute via `asyncio.create_subprocess_exec`, write result to `results/<task_id>.json`. Client polls `get_result(task_id, timeout=60)`.

**Gaps**: No priority ordering between tasks, no budget enforcement, no per-task timeout at the pool level, no streaming of intermediate output.

### 2.4 ComputePoolManager + FederatedLoadBalancer

**File**: `src/thegent/compute/offload.py` (WP-5001/5004)

Dispatches `AgentTask` objects to local `PersistentWorkerPool` (overflow to remote Tailscale nodes). `FederatedLoadBalancer` uses EMA-weighted round-robin to select the lowest-latency node. `RemoteNodeClient` is an httpx async client posting to `/execute`.

**Gaps**: `AgentTask` is an opaque blob (`dataclasses.asdict(task)`). No concept of sub-agent type, model, or tool-set constraints. No streaming back to orchestrator — only final result.

### 2.5 CapabilityIndex

**File**: `src/thegent/agents/capability_index.py` (WL-034)

Builds a TF-IDF index over agent `*.md` frontmatter (`description`, `capabilities`, `model`, `runner`). `recommend(task_description, top_n=3)` returns ranked `AgentRecommendation` objects.

**Gaps**: Recommendations are not consumed by the planner or dispatcher automatically. The routing link from `PlanNode.task` text → recommended agent → `AgentRunner` instance is missing.

### 2.6 HITL Governance

**File**: `src/thegent/orchestration/oversight.py`, `PolicyEngine.await_approval()` (WL-019)

HITL approval is available but not integrated into the sub-agent dispatch loop. There is no mechanism to pause a plan wave pending human approval of high-risk sub-agent actions.

### 2.7 $defer Injection

**File**: `src/thegent/orchestration/resilience/deferral.py` (WL-038)

`AgentRunner._process_output_deferrals()` scans agent stdout/stderr for `$defer <task>` lines and appends them to the Unified Prompt Queue as new pending entries. This is a loose form of sub-agent spawning: agents can self-schedule follow-on tasks. However, it bypasses the plan DAG entirely.

---

## 3. Other Harness Patterns

### 3.1 Claude Code

**Source**: `docs/context/claude-code.md` (fetched 2026-02-20)

**Sub-agent mechanism**: Claude Code spawns up to 7 parallel subagents via the internal `Task` tool. The orchestrating Claude instance:
1. Decomposes the goal into subtasks in its reasoning.
2. Emits `Task` tool calls (up to `--max-parallel` concurrently).
3. Each `Task` invocation spawns a child Claude process, isolated to a workspace, with its own tool permissions.
4. Results stream back as JSONL events (`stream-json` output format).
5. The parent merges results and continues.

**Controlled via**:
- `--allow-subagents true/false`
- `--max-parallel N` (default 7)

**Key properties**:
- Subagent dispatch is **model-native**: the orchestrating LLM decides when to spawn.
- Each subagent is isolated (separate process, separate tool sandbox).
- Results are typed JSONL events, not raw strings.
- No explicit DAG: the orchestrating model maintains the plan in its context window.

**Approval flow**: With `permissionMode: manual`, each tool call (including spawning subagents) requires human approval. `--dangerously-skip-permissions` bypasses this.

### 3.2 Codex

**Source**: `docs/context/codex.md` (verified 2026-02-20 from codex-upstream)

**Sub-agent mechanism**: Codex provides three integration surfaces:

**a) App Server Protocol** (`codex app-server`):
The App Server is a bidirectional JSONL-over-stdio daemon. The client can:
- Create threads (`thread/start`) and fork them (`thread/fork`) for parallel subtasks.
- Submit turns (`turn/start`) concurrently on different threads.
- Register **dynamic tools** in `ThreadStartParams.dynamic_tools` — tool call routing flows back to the client for client-side execution (the ultimate sub-agent primitive).
- Receive `item/commandExecution/requestApproval` and `item/fileChange/requestApproval` from the server for HITL gates.

**b) TypeScript SDK** (`@openai/codex-sdk`):
The SDK wraps `codex exec --experimental-json` as a subprocess. `thread.run()` (blocking) or `thread.runStreamed()` (async generator over `ThreadEvent`) per thread. Multiple SDK `Thread` instances can run concurrently (each spawning a child `codex exec` process). No coordinated orchestration beyond the caller's own logic.

**c) MCP Server** (`codex mcp server`):
Exposes two tools: `codex` (start session) and `codex_thread_continue` (resume thread). These allow an LLM to invoke Codex as a tool — the ultimate sub-agent pattern from the MCP perspective.

**Key properties**:
- Thread fork/resume enables stateful multi-agent: a parent thread can fork a child thread, get results, and merge.
- Typed `ThreadItem` events (agent_message, command_execution, file_change, mcp_tool_call, etc.) give structured per-item results.
- Approval flows are client-side: the server blocks and waits for the client to respond to `requestApproval`.
- Budget/cost data is available per-turn via `turn.usage` (input_tokens, output_tokens).

### 3.3 Gemini CLI

**Source**: `docs/context/gemini-cli.md` (fetched 2026-02-20)

Gemini CLI does not have a native sub-agent protocol. Sub-agent patterns are implemented via:
- **MCP**: Gemini CLI can call tools registered on an MCP server. If that server itself invokes agents (e.g., calls `codex mcp server` tools or thegent MCP tools), Gemini CLI functions as an orchestrator.
- **YOLO mode + sandbox**: Automated, non-interactive execution with sandboxed tool calls. Suitable as a sub-agent target from a parent orchestrator.
- **No native thread fork/resume**: Each `gemini --prompt` invocation is stateless.

---

## 4. Gap Analysis

| Capability | Claude Code | Codex | Gemini CLI | thegent (current) |
|---|---|---|---|---|
| Parallel sub-agent dispatch | Yes (Task tool, up to 7) | Yes (thread fork, concurrent SDK) | Via MCP only | Partial (asyncio.gather in PlangentExecutor) |
| Typed inter-agent message protocol | JSONL events (stream-json) | ThreadItem/ThreadEvent union | None native | None — plain `str` result in PlanNode |
| DAG-based plan execution | None (model-native) | None native (client responsibility) | None | Yes (PlangentPlanner+Executor, linear default) |
| Capability-based agent selection | Model-native | None explicit | None | Yes (CapabilityIndex TF-IDF) |
| Budget/cost cap per sub-agent | --max-turns, token tracking | turn.usage per thread | None | None |
| HITL approval in dispatch loop | Yes (permissionMode) | Yes (requestApproval server→client) | None native | Exists (WL-019) but not wired to planner |
| Streaming results to orchestrator | Yes (stream-json JSONL) | Yes (ThreadEvent async gen) | None | None — blocking collect |
| Sub-agent failure isolation | Per-process isolation | Per-thread isolation | N/A | None (exception propagated) |
| Sub-agent sandboxing | Yes (separate permissions) | Yes (per-thread sandbox policy) | YOLO+sandbox | None — same process env |
| Retry per sub-agent | Adaptive retry (harness) | on-failure approval + retry | None | Yes (with_retry in runners) |
| Result aggregation | Model-native in context | Client responsibility | N/A | None — PlanNode.result is last string |
| Correlation/parent run ID | Session ID | Thread ID | None | None — PlanNode.metadata is freeform |
| Cost accounting across wave | None explicit | Per-turn usage | None | None |
| Remote node dispatch | None | None (local binary) | None | Yes (ComputePoolManager/Tailscale) |

### 4.1 Summary of Critical Gaps

1. **No typed protocol**: Sub-agent inputs and outputs are untyped strings. There is no standard schema for `SubAgentRequest` or `SubAgentResult`.
2. **No dispatcher**: `PlangentExecutor` calls a generic `runner(node) -> str` callback. There is no automatic routing from `PlanNode.task` text to a `CapabilityIndex`-recommended `AgentRunner`.
3. **No streaming**: Sub-agent results are collected after the runner returns. There is no mechanism to stream partial output back to the orchestrating layer.
4. **No budget enforcement**: Sub-agents can run unbounded; there is no per-node token or time budget.
5. **No HITL integration**: The HITL approval system (WL-019) is not wired into the plan execution loop.
6. **No result aggregation**: After a plan wave, there is no component that merges outputs, resolves conflicts, or handles partial failures gracefully.
7. **No isolation**: Sub-agents run in the same process environment as the orchestrator. Claude Code and Codex provide per-process/per-thread isolation.

---

## 5. Proposed Design

### 5.1 OrchestrationPlan

Extend `Plan` / `PlanNode` from `plangent.py` with orchestration-specific metadata. No replacement — additive metadata only.

**Extended PlanNode metadata keys** (by convention in `PlanNode.metadata`):

```
agent_hint: str           # Preferred runner name ("claude", "codex", "flash", etc.)
model_hint: str           # Preferred model alias ("gemini-3-flash", "claude-haiku-4.5")
budget_tokens: int        # Max tokens this node may consume (0 = unlimited)
budget_time_s: float      # Max wall-clock seconds (0 = use global default)
sandbox: str              # "read-only" | "workspace-write" | "full"
require_hitl: bool        # If True, pause for HITL approval before executing
output_schema: dict       # Optional JSON Schema for structured output validation
parent_run_id: str        # Correlation ID from the orchestrating run
```

**OrchestrationPlan** is a `Plan` subclass with convenience factory methods:

```python
class OrchestrationPlan(Plan):
    @classmethod
    def from_goal(
        cls,
        goal: str,
        global_budget_tokens: int = 0,
        global_timeout_s: float = 3600.0,
        default_sandbox: str = "workspace-write",
        parent_run_id: str | None = None,
    ) -> "OrchestrationPlan": ...

    def add_task(
        self,
        task: str,
        depends_on: list[str] | None = None,
        *,
        agent_hint: str = "",
        model_hint: str = "",
        budget_tokens: int = 0,
        budget_time_s: float = 0.0,
        sandbox: str = "",
        require_hitl: bool = False,
        output_schema: dict | None = None,
    ) -> PlanNode: ...

    def total_budget_used(self) -> int:
        """Sum of tokens consumed across all completed nodes."""
        ...
```

**Location**: `src/thegent/orchestration/plan.py`

### 5.2 InterAgentProtocol

A typed message schema for all agent-to-agent communication. Implemented as `pydantic` dataclasses.

```python
# src/thegent/orchestration/protocol.py


class SubAgentRequest(BaseModel):
    request_id: str  # UUID
    parent_run_id: str  # Correlation with orchestrating run
    node_id: str  # PlanNode.id
    task: str  # Natural-language task description
    agent_name: str  # Resolved agent runner name
    model: str  # Resolved model alias
    cwd: Path | None
    mode: str  # "read-only" | "write" | "full"
    sandbox: str
    budget_tokens: int  # 0 = unlimited
    timeout_s: float
    context: dict  # Freeform key/value context from parent
    output_schema: dict | None


class SubAgentResult(BaseModel):
    request_id: str
    node_id: str
    success: bool
    output: str
    error: str | None
    tokens_in: int
    tokens_out: int
    elapsed_s: float
    agent_name: str
    model: str
    exit_code: int


class SubAgentEvent(BaseModel):
    """Streaming event emitted during sub-agent execution."""

    event_id: str
    request_id: str
    node_id: str
    event_type: Literal["started", "output_delta", "completed", "failed"]
    data: str  # Delta text or final output
    timestamp: float  # monotonic
```

**Wire format**: JSONL. Events written to an async queue consumed by the orchestrator.

**Location**: `src/thegent/orchestration/protocol.py`

### 5.3 SubAgentDispatcher

The dispatcher translates an `OrchestrationPlan` + plan wave into concurrent `SubAgentRequest` executions, enforces budgets, integrates HITL, and yields `SubAgentEvent` streams.

```python
# src/thegent/orchestration/dispatcher.py


class SubAgentDispatcher:
    """Dispatches ready PlanNodes as typed SubAgentRequests to AgentRunners.

    Responsibilities:
    - Resolve agent runner via CapabilityIndex.recommend()
    - Enforce per-node budget (tokens, wall time)
    - Emit SubAgentEvents to an asyncio.Queue
    - Gate on HITL approval when PlanNode.metadata["require_hitl"] is True
    - Retry transient failures via tenacity
    - Propagate isolation: each sub-agent runs in an isolated subprocess env
    """

    def __init__(
        self,
        capability_index: CapabilityIndex | None = None,
        runner_registry: dict[str, AgentRunner] | None = None,
        event_queue: asyncio.Queue[SubAgentEvent] | None = None,
        hitl_engine: PolicyEngine | None = None,
        max_concurrent: int = 7,
    ) -> None: ...

    async def dispatch_wave(
        self,
        plan: OrchestrationPlan,
        ready_nodes: list[PlanNode],
    ) -> list[SubAgentResult]: ...

    async def _dispatch_node(
        self,
        plan: OrchestrationPlan,
        node: PlanNode,
    ) -> SubAgentResult: ...

    def _resolve_runner(self, node: PlanNode) -> tuple[AgentRunner, str]:
        """Select runner + model for a node using CapabilityIndex + metadata hints."""
        ...
```

**Key behaviors**:

- `dispatch_wave()` uses `asyncio.gather(*[_dispatch_node(n) for n in ready_nodes])` with a semaphore for `max_concurrent`.
- `_dispatch_node()` wraps execution in `asyncio.wait_for(..., timeout=node.metadata["budget_time_s"])`.
- Token budget is checked by wrapping the runner with a `BudgetTracker` that parses token metadata from JSONL output.
- HITL gates: before executing a node with `require_hitl=True`, the dispatcher calls `hitl_engine.await_approval(run_id, description)` and only proceeds on `HITLDecision.APPROVED`.
- Each sub-agent is invoked via `runner.run(prompt, cwd, mode, timeout)` with an isolated `env` dict (separate `CODEX_HOME`, etc.).

**Location**: `src/thegent/orchestration/dispatcher.py`

### 5.4 ResultAggregator

Merges `SubAgentResult` objects from a completed plan wave into a structured summary.

```python
# src/thegent/orchestration/aggregator.py


class AggregationResult(BaseModel):
    plan_id: str
    total_nodes: int
    succeeded: int
    failed: int
    total_tokens_in: int
    total_tokens_out: int
    total_elapsed_s: float
    outputs: dict[str, str]  # node_id -> output
    errors: dict[str, str]  # node_id -> error message
    partial_failure: bool
    budget_exceeded: bool


class ResultAggregator:
    """Merges SubAgentResults from a plan wave.

    Handles:
    - Collecting outputs keyed by node_id
    - Summing token and time costs
    - Detecting budget overruns (global_budget_tokens exceeded)
    - Marking failed nodes without aborting the plan (unless fail_fast)
    - Producing a structured AggregationResult for the orchestrator
    """

    def __init__(
        self,
        global_budget_tokens: int = 0,
        fail_fast: bool = False,
    ) -> None: ...

    def aggregate(
        self,
        plan: OrchestrationPlan,
        results: list[SubAgentResult],
    ) -> AggregationResult: ...
```

**Location**: `src/thegent/orchestration/aggregator.py`

### 5.5 Integration Architecture

```
OrchestrationPlan (plan.py)
    |
    v
PlangentPlanner.next_ready_tasks()
    |
    v
SubAgentDispatcher.dispatch_wave()
    |-- CapabilityIndex.recommend()  --> AgentRunner (DirectAgentRunner / CodexProxyRunner / FlashAgent)
    |-- HITL gate (PolicyEngine)     --> await_approval() if require_hitl
    |-- BudgetTracker               --> enforce budget_tokens / budget_time_s
    |-- asyncio.gather (semaphore)  --> concurrent node execution
    |-- SubAgentEvent stream        --> asyncio.Queue --> orchestrator / TUI
    |
    v
list[SubAgentResult]
    |
    v
ResultAggregator.aggregate()
    |
    v
AggregationResult (total cost, outputs, failure map)
    |
    v
PlangentPlanner.mark_done() / mark_failed() per node
    |
    v
Next wave or plan complete
```

**ASCII DAG flow**:

```
                    [OrchestrationPlan]
                           |
                    [Wave N ready nodes]
                    /     |     \
              [Node A] [Node B] [Node C]
                 |         |         |
         [Cap. Index] [Cap. Index] [Cap. Index]
                 |         |         |
         [Runner A]   [Runner B]  [Flash C]
                 \         |         /
                  [ResultAggregator]
                           |
                  [AggregationResult]
                           |
              [PlangentPlanner.mark_done/failed]
                           |
                    [Next Wave or Done]
```

---

## 6. Integration Points with Existing Components

| Existing Component | Integration Point |
|---|---|
| `PlangentPlanner` + `PlangentExecutor` | `OrchestrationPlan` extends `Plan`; `dispatch_wave()` replaces the inline `runner()` callback |
| `CapabilityIndex` | Called by `SubAgentDispatcher._resolve_runner()` to select best agent |
| `FlashAgent` | Registered in `runner_registry` as `"flash"` for short-lived sub-tasks |
| `CodexProxyRunner.run_lightweight()` | Used when `agent_hint == "codex"` and `budget_time_s < 600` |
| `ComputePoolManager` | Optional: `SubAgentDispatcher` can delegate to `ComputePoolManager.submit()` for remote node dispatch |
| `PolicyEngine.await_approval()` (WL-019) | Called for nodes with `require_hitl=True` before execution |
| `TaskWorkerPool` (MTSP-03) | Used as the local dispatch backend for non-agent subprocess tasks |
| `$defer` injection (`deferral.py`, WL-038) | `SubAgentResult.output` is scanned for `$defer` directives post-execution |
| `OTel instrumentation` | Each `_dispatch_node()` wrapped in `instrument_genai_call()` span with `parent_run_id` context |
| `PromptQueueManager` (WL-014) | Completed `OrchestrationPlan` results injected as next items when plan produces deferred tasks |
| `UnifiedWorkerDaemon` (MTSP-05) | `SubAgentDispatcher` can be hosted inside the unified daemon for persistent orchestration |

---

## 7. Proposed WL Items (WL-080 through WL-089)

### [WL-080] InterAgentProtocol: Typed Message Schema
**Status:** pending
**Priority:** P1
**Area:** orchestration
**Effort:** S (2-4h)
**Blocked by:** none
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Implement `SubAgentRequest`, `SubAgentResult`, `SubAgentEvent` pydantic models in `src/thegent/orchestration/protocol.py`. Wire JSONL serialization. 20+ unit tests.

---

### [WL-081] OrchestrationPlan: Extended PlanNode Metadata + Convenience Factory
**Status:** pending
**Priority:** P1
**Area:** orchestration
**Effort:** S (2-4h)
**Blocked by:** WL-080
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Implement `OrchestrationPlan(Plan)` subclass with `add_task()` factory, `from_goal()` classmethod, and `total_budget_used()` in `src/thegent/orchestration/plan.py`. 20+ unit tests.

---

### [WL-082] SubAgentDispatcher: CapabilityIndex-Backed Dispatch with Budget + HITL
**Status:** pending
**Priority:** P1
**Area:** orchestration
**Effort:** M (half day)
**Blocked by:** WL-080, WL-081
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Implement `SubAgentDispatcher` in `src/thegent/orchestration/dispatcher.py`. Uses `CapabilityIndex.recommend()` to select runner, `asyncio.gather` with semaphore for concurrency, `asyncio.wait_for` for per-node timeouts, `PolicyEngine.await_approval()` for HITL gates. 30+ tests including concurrency and budget enforcement.

---

### [WL-083] ResultAggregator: Merge Sub-Agent Outputs with Cost Tracking
**Status:** pending
**Priority:** P1
**Area:** orchestration
**Effort:** S (2-4h)
**Blocked by:** WL-080, WL-081
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Implement `ResultAggregator` + `AggregationResult` in `src/thegent/orchestration/aggregator.py`. Token sum, partial failure tracking, global budget check, structured output. 20+ tests.

---

### [WL-084] PlangentExecutor Integration: Wire Dispatcher into execute_async()
**Status:** pending
**Priority:** P1
**Area:** orchestration
**Effort:** S (2-4h)
**Blocked by:** WL-082, WL-083
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Add `SubAgentDispatcher`-backed execution path to `PlangentExecutor.execute_async()` when `isinstance(plan, OrchestrationPlan)`. The dispatcher replaces the inline `runner()` callback for orchestration plans. Fallback to existing callback behavior for plain `Plan`. 20+ tests.

---

### [WL-085] SubAgentEvent Streaming: asyncio.Queue + MCP Tool
**Status:** pending
**Priority:** P2
**Area:** orchestration
**Effort:** M (half day)
**Blocked by:** WL-082
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Wire `SubAgentEvent` emission from `SubAgentDispatcher` to an `asyncio.Queue`. Expose `thegent_orchestration_events` MCP tool that streams events via SSE for real-time TUI/client consumption. Wire into `UnifiedWorkerDaemon`. 25+ tests.

---

### [WL-086] BudgetTracker: Per-Node Token Budget Enforcement
**Status:** pending
**Priority:** P2
**Area:** orchestration
**Effort:** S (2-4h)
**Blocked by:** WL-080
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Implement `BudgetTracker` that wraps JSONL output from `CodexProxyRunner`/`DirectAgentRunner` to parse token usage and enforce `budget_tokens` per node. Raises `BudgetExceededError` (fail-loud, no silent continuation) when limit reached. 20+ tests.

---

### [WL-087] LLM-Backed Plan Decomposition: Override _generate_sub_tasks()
**Status:** pending
**Priority:** P2
**Area:** orchestration
**Effort:** M (half day)
**Blocked by:** WL-082
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Implement `LLMPlangentPlanner(PlangentPlanner)` that overrides `_generate_sub_tasks()` with a `FlashAgent` call to decompose the goal into structured sub-tasks with agent hints, dependencies, and budget estimates. Output validated against `OrchestrationPlan` schema. 20+ tests.

---

### [WL-088] CLI: thegent orchestrate plan + thegent orchestrate run
**Status:** pending
**Priority:** P2
**Area:** cli, orchestration
**Effort:** S (2-4h)
**Blocked by:** WL-084
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Add `thegent orchestrate plan <goal>` (decompose and print plan DAG) and `thegent orchestrate run <goal>` (decompose and execute with live sub-agent event streaming) commands. Wire into `src/thegent/cli/apps/`. 20+ tests.

---

### [WL-089] ComputePoolManager Integration: Remote Sub-Agent Dispatch
**Status:** pending
**Priority:** P3
**Area:** orchestration, compute
**Effort:** M (half day)
**Blocked by:** WL-082
**Source:** [docs/research/SUB_AGENT_ORCHESTRATION_RESEARCH_2026-02-20.md]
Wire `ComputePoolManager.submit()` into `SubAgentDispatcher` as an optional remote dispatch backend. When `agent_hint` maps to a compute node task (not a CLI agent), dispatch via the Tailscale pool with workspace sync. 20+ tests.

---

## 8. References

| Component | File |
|---|---|
| PlangentPlanner/Executor | `src/thegent/agents/plangent.py` |
| FlashAgent | `src/thegent/agents/flash_agent.py` |
| CapabilityIndex | `src/thegent/agents/capability_index.py` |
| TaskWorkerPool | `src/thegent/orchestration/worker_pool.py` |
| ComputePoolManager | `src/thegent/compute/offload.py` |
| DirectAgentRunner | `src/thegent/agents/direct_agents.py` |
| CodexProxyRunner | `src/thegent/agents/codex_proxy.py` |
| AgentRunner base | `src/thegent/agents/base.py` |
| ExecutionEngine | `src/thegent/orchestration/execution/engine.py` |
| $defer injection | `src/thegent/orchestration/resilience/deferral.py` |
| HITL governance | `src/thegent/orchestration/oversight.py` |
| Claude Code context | `docs/context/claude-code.md` |
| Codex context | `docs/context/codex.md` |
| Gemini CLI context | `docs/context/gemini-cli.md` |
| Harness Parity Matrix | `docs/reference/HARNESS_PARITY_MATRIX.md` |
