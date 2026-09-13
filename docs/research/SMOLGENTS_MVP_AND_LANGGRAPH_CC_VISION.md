<DONE>
# SmolGents Deep Research: MVP Use Case & LangGraph-over-CC Vision

> **Date**: 2026-02-18
> **Status**: Research
> **Purpose**: Deep dive on smolgents for MVP; long-term alignment with LangGraph layered over Claude Code

---

## 1. Executive Summary

**MVP**: **Maximal MVP** (not minimal)—production-ready, fully featured orchestration layer following **Agile Plus**. Crew → Task → Agent with dependency resolution, hierarchical execution, routing, WorkflowEngine, monitoring, and extensibility. Quality gates, documentation, and test coverage from day one.

**Long-term**: Evolve toward LangGraph-style StateGraph layered over Claude Code (CC) as the execution backend. CC provides team lead + teammates, JSON inboxes, blockedBy; LangGraph provides durable state, conditional edges, human-in-the-loop, and explicit graph topology.

---

## 1.1 Agile Plus Alignment (Maximal MVP)

**Agile Plus** = Agile with structured quality gates, upfront design, and production-ready deliverables.

| Principle               | Maximal MVP Application                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| **Sprint structure**    | Defined sprints with clear deliverables; no "throwaway prototype"                         |
| **Quality gates**       | Unit tests, integration tests, type hints, lint before merge                              |
| **Documentation**       | API docs, architecture docs, runbooks from day one                                        |
| **Extensibility**       | Plugin-style agent_executor; AgentAssigner strategy pattern                               |
| **Observability**       | MonitoringEngine, metrics, health checks in MVP                                           |
| **Maximal engineering** | Optimal minimal overhead, maintainability, scalability (per thegent SYNC_UPDATE plan §26) |

**Out of scope for MVP** (defer to LangGraph phase): human-in-the-loop, conditional routing, durable checkpoints, nested teams.

---

## 2. SmolGents Deep Dive for MVP

### 2.1 Core Abstraction Stack

```
Workflow (multi-crew, stages, depends_on)
    └── Crew (agents + tasks, execution_mode)
            └── CrewExecutor
                    ├── TaskExecutor (dependency resolution, execute_all)
                    ├── AgentAssigner (round-robin, load-balanced, skill-based)
                    ├── ResultAggregator
                    └── ResultConsolidator
```

**Key insight**: SmolGents is **crew-centric**, not graph-centric. A Crew is a fixed set of agents + tasks. Execution mode (sequential, hierarchical, custom) determines how tasks map to agents.

### 2.2 MVP-Relevant Components

| Component                             | MVP Value          | Notes                                                   |
| ------------------------------------- | ------------------ | ------------------------------------------------------- |
| **Task.dependencies**                 | High               | `add_dependency(task_id)` — linear/diamond resolution   |
| **TaskExecutor.resolve_dependencies** | High               | Topological sort; `get_task_input` passes prior results |
| **CrewExecutor.execute_hierarchical** | High               | Manager/lead vs worker; priority tasks to managers      |
| **AgentAssigner**                     | Medium             | SkillBasedAssigner matches task name to agent role      |
| **Workflow + CrewStage**              | Medium             | Multi-crew with stage dependencies; parallel stages     |
| **RouterManager**                     | High (maximal MVP) | Cost/performance routing; include                       |
| **MonitoringEngine**                  | High (maximal MVP) | Include; production observability                       |

### 2.3 Execution Modes (MVP Fit)

**Sequential** (default):

- Tasks execute in dependency order
- `assign_tasks_to_agents()` uses AgentAssigner (round-robin by default)
- No hierarchy; any agent can get any task

**Hierarchical** (best for MVP with team lead):

- Sorts agents by role: `"manager"` or `"lead"` first
- Manager agents get priority tasks (first N tasks)
- Worker agents get remaining tasks
- **Limitation**: Role detection is string match on `agent.role.lower()`

**Custom**:

- Pluggable `custom_executor(crew, task_executor)` in crew.config
- Escape hatch for custom logic

### 2.4 Task Dependency Model

```python
# Task has dependencies list
task.add_dependency(other_task.id)

# TaskExecutor.resolve_dependencies(task_id) → topological order
# TaskExecutor.get_task_input(task_id) → dict of {dep_id: result}
# TaskExecutor.execute_all(task_ids) → respects deps, retries, aggregates
```

**MVP mapping to thegent**:

- `DelegationRequest` ≈ Task (with dependencies)
- `blockedBy` (Claude Code) ≈ `Task.dependencies`
- **codex/cc/droid harness** (DirectAgentRunner, CodexProxyRunner, DroidRunner) ≈ agent_executor callback

### 2.5 What SmolGents Does NOT Have (MVP Gaps)

| Gap                        | Impact                                    | Workaround                                                    |
| -------------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| **No LLM execution**       | TaskExecutor.\_run_task is mock           | Register `agent_executor` callback that invokes actual agent  |
| **No CC integration**      | Can't spawn Claude Code teammates         | MVP: use thegent **codex/cc/droid harness** as agent_executor |
| **No persistent state**    | StateManager exists but not wired to Crew | Use DelegationRequest storage                                 |
| **No human-in-the-loop**   | No interrupt/resume                       | Defer to LangGraph phase                                      |
| **No conditional routing** | Fixed assignment at start                 | Defer to LangGraph                                            |
| **Flat hierarchy**         | Only manager vs worker, no nested teams   | Accept for MVP                                                |

**MVP execution backend**: thegent already has a **codex/cc/droid harness**—DirectAgentRunner, CodexProxyRunner, DroidRunner, cursor_api_runner—with heliosShield harness wrapping when enabled. The MVP uses this existing harness, not TeammateManager.

### 2.6 MVP Use Case: thegent + SmolGents

**Scenario**: `thegent sitback` delegates to a crew (planner → researcher → coder → reviewer).

1. **Crew**: 4 agents (planner, researcher, coder, reviewer), 4 tasks with dependencies
2. **CrewExecutor**: Sequential mode; SkillBasedAssigner matches task to agent role
3. **TaskExecutor.agent_executor**: Callback that invokes thegent **codex/cc/droid harness** (DirectAgentRunner, CodexProxyRunner, DroidRunner, etc.)—the existing agent runners that wrap claude, codex, copilot, gemini, droid via CLI + heliosShield harness
4. **Result**: Linear pipeline, dependency-ordered, each step executed via codex/cc/droid

**Maximal MVP**: Include WorkflowEngine for multi-crew; single Crew per sitback is the primary path, but multi-crew stages supported.

---

## 3. Long-Term Vision: LangGraph Layered Over Claude Code

### 3.1 Why LangGraph + CC

| Layer           | Responsibility                                                                    |
| --------------- | --------------------------------------------------------------------------------- |
| **LangGraph**   | State machine, conditional edges, durable execution, human-in-the-loop, subgraphs |
| **Claude Code** | Execution backend: team lead, teammates, context windows, JSON inboxes, blockedBy |

**CC provides**:

- Team lead coordinates, spawns teammates
- Teammates in own context windows
- `~/.claude/teams/{name}/inboxes/{agent}.json` for peer messaging
- `~/.claude/tasks/{team-name}/{n}.json` with blockedBy
- TeammateTool: spawn, write, broadcast, read, list, shutdown

**LangGraph provides**:

- Explicit graph: nodes = agents/steps, edges = transitions
- State: TypedDict/dataclass with reducers
- Conditional edges: route based on state
- Durable execution: checkpoint, resume
- Human-in-the-loop: interrupt, inspect, modify state
- Subgraphs: nested agent workflows
- Command: combine state update + routing (handoffs)

### 3.2 Layering Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                       │
│  Nodes: orchestrator, planner, researcher, coder, reviewer   │
│  Edges: conditional (route by state), human-in-the-loop      │
│  State: task_list, current_phase, results, blockedBy          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │  Node execution = invoke CC
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code (Execution)                   │
│  Team lead: orchestrator node                               │
│  Teammates: planner, researcher, coder, reviewer            │
│  Tasks: ~/.claude/tasks/{team}/{n}.json + blockedBy          │
│  Inboxes: ~/.claude/teams/{name}/inboxes/{agent}.json        │
└─────────────────────────────────────────────────────────────┘
```

**Node implementation**: Each LangGraph node that represents an agent:

1. Writes task to CC task file (or uses TeammateTool.spawn)
2. Sets blockedBy from state (previous task IDs)
3. Waits for completion (poll inbox or task status)
4. Reads result, updates state
5. Returns state update; conditional edge routes to next node

### 3.3 Key LangGraph Concepts for CC Integration

**State**:

```python
class CCWorkflowState(TypedDict):
    task_list: list[dict]  # CC task format
    completed_tasks: dict  # task_id -> result
    current_phase: str  # planning, research, coding, review
    blocked_by: dict  # task_id -> list of blocking task ids
    human_input: Optional[str]  # for interrupt/resume
```

**Nodes**: Each node = one CC teammate invocation

- `planner_node(state)` → spawn planner teammate, wait, return result
- `researcher_node(state)` → spawn researcher, blockedBy planner, return result
- etc.

**Edges**:

- `add_edge("planner", "researcher")` — linear pipeline
- `add_conditional_edges("reviewer", route_by_review)` — pass/fail → redo coder or end
- `add_edge("reviewer", "__interrupt__")` — human approval before merge

**Durable execution**: LangGraph checkpointer persists state. CC has no session resumption—LangGraph fills that gap by resuming from checkpoint and re-invoking CC as needed.

### 3.4 heliosShield Mesh Interface (Alignment)

From agent-mesh research:

- Mesh treats each CLI process as **opaque**
- Unit of coordination: **process**
- Read-only monitoring of `~/.claude/teams/`, `~/.claude/tasks/`
- Mesh responsibilities: task_assignment, file_locks, heartbeat, result_synthesis

**LangGraph-over-CC** fits this: LangGraph is the mesh layer. It assigns tasks (via CC spawn), coordinates (via state + edges), synthesizes (via state aggregation). It does NOT reach into CC internals—it invokes CC via TeammateTool/CLI and reads task files.

---

## 4. Evolution Path: SmolGents MVP → LangGraph + CC

### 4.1 Phase 1: Maximal MVP (SmolGents-style, Agile Plus)

- **Orchestration**: Crew + CrewExecutor + TaskExecutor + **WorkflowEngine**
- **Agents**: thegent codex/cc/droid harness (DirectAgentRunner, CodexProxyRunner, DroidRunner, etc.)
- **Execution**: agent_executor callback → invoke codex/cc/droid harness (existing agent runners)
- **Routing**: RouterManager (cost/performance/balanced), AgentSelector, LoadBalancer
- **Monitoring**: MonitoringEngine, HealthChecker, PerformanceTracker, CostTracker
- **Scope**: Single crew primary; multi-crew via WorkflowEngine; sequential + hierarchical modes
- **Quality**: Tests, type hints, docs, extensibility hooks
- **No** (defer to LangGraph): human-in-the-loop, conditional routing, durable checkpoints, nested teams

### 4.2 Phase 2: Add CC Primitives

- **blockedBy**: Add to DelegationRequest; map to CC task format
- **Task files**: Write `~/.claude/tasks/{team}/{n}.json` when delegating
- **Inbox read**: Poll teammate inbox for completion signal
- **TeammateTool**: Use spawn, write, read if available via CC API/CLI

### 4.3 Phase 3: LangGraph Migration

- **Replace CrewExecutor** with LangGraph StateGraph
- **Nodes** = agent invocation (CC spawn)
- **State** = task list, results, phase
- **Edges** = conditional routing, human-in-the-loop
- **Checkpointer** = durable execution, resume

### 4.4 Phase 4: Full LangGraph + CC

- Subgraphs for nested teams
- Multi-crew as subgraphs
- Human-in-the-loop at review/merge
- Full state persistence, streaming

---

## 5. SmolGents vs LangGraph: Conceptual Mapping

| SmolGents                  | LangGraph                           | CC                |
| -------------------------- | ----------------------------------- | ----------------- |
| Crew                       | StateGraph (compiled)               | Team              |
| Task                       | Node (or state channel)             | Task file         |
| Task.dependencies          | State.blockedBy / edge ordering     | blockedBy in JSON |
| Agent                      | Node implementation                 | Teammate          |
| AgentAssigner              | Conditional edge / routing function | —                 |
| CrewExecutor               | graph.invoke(state)                 | —                 |
| ExecutionMode.HIERARCHICAL | Node priority / subgraph            | Team lead         |
| Workflow + CrewStage       | Subgraph                            | —                 |
| ResultAggregator           | State reducer                       | —                 |
| —                          | interrupt() / Command(resume=)      | Human escalation  |
| —                          | Checkpointer                        | —                 |

---

## 6. Recommendations

### 6.1 For Maximal MVP (Agile Plus)

1. **Use SmolGents patterns** (Crew, Task, CrewExecutor, WorkflowEngine, RouterManager, MonitoringEngine) as reference.
2. **Implement full Crew stack** in thegent: Crew + CrewExecutor + TaskExecutor + WorkflowEngine; RouterManager; MonitoringEngine.
3. **Wire codex/cc/droid harness** as agent_executor: invoke DirectAgentRunner, CodexProxyRunner, DroidRunner, etc.
4. **Task.dependencies** → map to blockedBy when adding CC integration.
5. **Hierarchical mode**: Use role "manager" or "lead" for sitback orchestrator; specialists for teammates.
6. **Quality gates**: Unit + integration tests, type hints, API docs, architecture doc.
7. **Extensibility**: Plugin-style agent_executor; AgentAssigner strategy pattern.

### 6.2 For Long-Term

1. **Design state schema now** with LangGraph in mind: TypedDict with task_list, results, phase.
2. **Keep CC interface thin**: spawn, read task, read inbox. Don't replicate CC internals.
3. **Plan for LangGraph migration**: CrewExecutor logic should be extractable into nodes + edges.
4. **Human-in-the-loop**: Reserve state channel `human_input`; add interrupt points at review/merge.

### 6.3 What to Build in thegent (Maximal MVP)

- `Crew` (or `AgentCrew`): agents + tasks + execution_mode
- `CrewExecutor`: assign_tasks_to_agents, execute (sequential/hierarchical)
- `TaskExecutor`: dependency resolution, agent_executor callback
- `Task` with dependencies (or extend DelegationRequest)
- `WorkflowEngine`: multi-crew stages, stage dependencies
- `agent_executor` that invokes thegent **codex/cc/droid harness**
- `AgentAssigner`: SkillBasedAssigner, HierarchicalAssigner (manager-first), RoundRobin, LoadBalanced
- `RouterManager`: cost/performance/balanced routing, AgentSelector, LoadBalancer
- `MonitoringEngine`: HealthChecker, PerformanceTracker, CostTracker
- Tests, type hints, API docs, architecture doc

### 6.4 What to Defer (LangGraph Phase)

- Human-in-the-loop (interrupt/resume)
- Conditional routing (dynamic edges)
- Durable execution (checkpointer)
- Nested teams
- CC task file writing (Phase 2)

---

## 7. References

- smolgents: `src/crews/crew.py`, `src/executors/crew_executor.py`, `src/executors/task_executor.py`, `src/executors/agent_assigner.py`
- thegent codex/cc/droid harness: `src/thegent/agents/direct_agents.py`, `codex_proxy.py`, `droid.py`, `cursor_api_runner.py`; heliosShield harness via `_wrap_with_harness`
- heliosShield: `agent-mesh-research-r3-consensus-escalation-2026.md` (§6 CLI Tool Coordination)
- LangGraph: StateGraph, Nodes, Edges, Command, interrupt, checkpointer
- Claude Code: TeammateTool, teams dir, tasks dir, blockedBy

---

## 8. Unified Work Stream Integration

**Work stream items** (see [WORK_STREAM.md](../reference/WORK_STREAM.md)):

| ID                                      | Title                                         | Priority |
| --------------------------------------- | --------------------------------------------- | -------- |
| research-agent-hierarchy-mvp            | Agent Hierarchy & Maximal MVP research        | P1       |
| impl-agent-crew-maximal-mvp             | Implement Agent Crew stack                    | P1       |
| impl-agent-crew-codex-harness           | Wire codex/cc/droid harness as agent_executor | P1       |
| research-agent-hierarchy-implementation | Implement AgentHierarchyManager (Phase 1)     | P2       |
