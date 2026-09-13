# Agent Forking Systems: Research and Planning Specification

## 1. Purpose

This document defines research scope, architecture options, and execution roadmap for same-agent cloning behavior in Codex-style operator workflows.

The objective is to evaluate and then implement a practical fork model that maximizes throughput and preserves decision coherence while respecting execution isolation constraints.

## 2. Problem Definition

Current multi-agent execution in this workspace has strong support for wave-based orchestration via `spawn_agent`, but each spawned worker has independent session state.

Goals:

1. Increase parallel throughput for large, context-heavy tasks.
2. Preserve semantic continuity across agents through explicit memory synchronization.
3. Keep failure domains bounded (rollback, conflict control, and auditability).
4. Provide a governance-friendly model for quality and task integrity.

## 3. Canonical Constraints

- True in-process memory cloning is not guaranteed in current tool behavior.
- A spawn is a separate agent with isolated session context and its own tool invocations.
- Shared truth must be represented as persistent coordination artifacts (ledger + contracts).
- Determinism and reproducibility are higher priority than aggressive unbounded concurrency.

## 4. Research Findings (Current Ecosystem)

### 4.1 OpenAI and tool-call parallelism

1. OpenAI function calling supports multi-turn tool-based orchestration with configurable strictness.
2. The API can emit multiple tool calls and exposes `parallel_tool_calls` behavior and strict schema mode options.
3. Parallel calls are useful for independent calls but can weaken strict schema behavior in some flows.

Source: https://platform.openai.com/docs/guides/function-calling/prompt-chaining

### 4.2 OpenAI-style handoff/swarm patterns

1. Swarm-style patterns center on handoff and shared message context at the conversation level.
2. Practical systems still require a coordinator to control turn-taking, context sharing strategy, and conflict arbitration.

Source: https://microsoft.github.io/autogen/0.7.3/user-guide/agentchat-user-guide/swarm.html

### 4.3 CrewAI/flow orchestration

1. Crew/flow style frameworks expose explicit processes, delegation, asynchronous execution, and process composition.
2. These frameworks are useful as blueprints for role decomposition, validation gates, and traceability.
3. They still converge on centralized execution control around state and task graph.

Source: https://docs.crewai.com/en/core-concepts/Tasks

### 4.4 LangGraph custom workflows

1. LangGraph style workflows give explicit control over branching, parallel steps, and deterministic graph control.
2. This maps well to mixed-mode execution where model tasks and deterministic steps need combined orchestration.

Source: https://docs.langchain.com/oss/python/langchain/multi-agent/custom-workflow

## 5. Design Alternatives

### 5.1 Alternative A — Single Agent, High-Granularity Internal Parallelization

- No forks.
- Single long context agent decomposes and executes internally.
- Best for: low branching problems with low IO concurrency.
- Weakness: limited wall-clock gains.

### 5.2 Alternative B — Parallel Specialist Agents (Heterogeneous)

- Fixed roles (planner, implementer, verifier, reporter).
- Best for: clear domain boundaries.
- Weakness: context handoff complexity and dependency management.

### 5.3 Alternative C — Same-Agent Fork (Proposed)

- Spawn N workers with the same persona and constraints.
- Every fork receives identical bootstrap snapshot.
- Shared persistent memory plane manages facts, decisions, and lock state.
- Best for: high-volume, mostly independent subproblems.
- Risk: merge and conflict management complexity.

### 5.4 Alternative D — Stateful Graph Orchestrator

- Deterministic graph engine handles task graph and state transitions.
- Workers used as execution nodes; coordinator remains deterministic.
- Best for: long-running regulated tasks with auditable transitions.

## 6. Recommended Architecture (Hybrid C + D)

The practical system should combine worker cloning semantics with graph-level deterministic control.

### 6.1 Core components

1. `orchestrator` service

- Owns task graph and state transitions.
- Enforces ownership and conflict rules.
- Routes work to forked workers.

2. `fork_controller`

- Issues worker jobs with a standardized bootstrap block.
- Tracks lifecycle states: `pending`, `running`, `blocked`, `done`, `failed`, `deferred`.

3. `shared_memory_bus`

- Immutable append log for facts and claims.
- Conflict ledger with file lock hints and last-writer metadata.
- Shared objective and invariants file.

4. `evidence_store`
   4.1 Every lane writes discovery notes.
   4.2 Every lane writes command evidence.
   4.3 Every lane writes assumptions.
   4.4 Every lane writes confidence tags.
   4.5 Every lane writes verification result.

5. `resolver`

- Performs conflict resolution by deterministic precedence.
- Merges compatible findings automatically.
- Escalates semantic conflicts to coordinator agent.

6. `quality_gates`

- Per-lane validation matrix and parent-level gate tasks.
- Runs lightweight checks first, then full gates.

### 6.2 Coordination contract

All fork workers must output JSON blocks following a fixed schema:

```json
{
  "lane_id": "string",
  "objective": "string",
  "agent_context_version": "string",
  "phase": "string",
  "findings": [
    {
      "file": "string",
      "type": "discovery|decision|claim|risk|patch|test|question",
      "summary": "string",
      "severity": "low|med|high|critical",
      "evidence": ["path:line", "command"],
      "confidence": 0.0
    }
  ],
  "proposed_actions": [],
  "conflicts": [],
  "next_actions": []
}
```

### 6.3 Memory sharing model

- Shared memory is event-sourced and append-only.
- Each worker keeps a local scratchpad for transient reasoning.
- Before each major step, worker reads a compact snapshot: objective, latest high-confidence findings, active conflicts, and unresolved dependencies.
- Optional periodic compaction: nightly or post-wave summary compresses old entries.

## 7. Research Plan for Pilot Deployment

### 7.1 Phase 0: Baseline measurement (no functional change)

1. Capture baseline across 6 representative tasks.
2. Measure time-to-first-insight, total time, conflict rate, duplicate work rate, and evidence quality score.
3. Identify which task classes are truly parallelizable.

### 7.2 Phase 1: Controlled pilot on `thegent` quality checks

1. Create 3+ lanes for task family: static checks and test analysis.
2. Use shared memory bus for claim/evidence sharing only.
3. Keep all patch writes serialized by resolver.
4. Evaluate with historical workload.

### 7.3 Phase 2: Expand pilot to cross-repo tasks

1. Add `cliproxyapi-plusplus` and `trace` lanes.
2. Add parent-orchestrated quality run behavior where possible.
3. Add cross-repo artifact references to single evidence index.

### 7.4 Phase 3: Same-agent clone hardening

1. Add fork heartbeat and inactivity timeout.
2. Add conflict policy for file ownership maps.
3. Add conflict policy for priority and lock duration.
4. Add conflict policy for stale-lock recovery.
5. Add deterministic merge for non-conflicting claims.
6. Add quality gate that fails if conflict resolution is incomplete.

### 7.5 Phase 4: Productionization

1. Introduce governance docs and onboarding pattern.
2. Add operator dashboard outputs.
3. Add incident runbook for fork exhaustion and repeated conflicting lanes.
4. Promote `agent-forking` as default for selected task categories.

## 8. Evaluation Matrix

### 8.1 Key metrics

1. Throughput

- tasks/hour
- elapsed time vs serial baseline
- parallel efficiency ratio

2. Quality

- false merge rate
- unresolved conflict ratio
- evidence completeness score
- validation pass-at-least-once success

3. Behavioral control

- context drift score
- repeated rework rate
- average lane blocker time

4. Cost and reliability

- tool call count
- duplicate findings rate
- token overhead per finished task
- incident frequency per 100 tasks

### 8.2 Stop conditions

1. If unresolved conflicts remain above threshold after 3 waves.
2. If evidence quality drops below manual baseline.
3. If context drift causes repeated semantic regressions.
4. If forking overhead exceeds 25 percent of baseline wall-clock.

## 9. Security and Governance Controls

1. Mandatory redaction of secrets in all emitted evidence.
2. Deterministic redaction policy for command output capture.
3. No auto-commit behavior in unresolved conflict state.
4. Immutable event log for accountability.
5. Every lane must have explicit scope and file ownership.

## 10. Deployment Scope Proposal (Governance Fit)

1. Pilot in non-production maintenance waves first.
2. Expand to quality gates and cross-repo validation once conflict rates are stable.
3. Apply strictness defaults:

- quality gates remain explicit and always-on
- no implicit skip behavior
- all skipped checks require governance reason with evidence id

## 11. Immediate Workpack for Next Execution

1. Draft operational runbook and worker contract schema in `governance/agent-forking/`.
2. Add one pilot playbook for `thegent` quality task.
3. Add two templates:

- `fork_plan.md`
- `fork_lane_report.md`

4. Add simple CI-style validator for lane report schema.
5. Run pilot on 3 representative tasks and publish first research note under `governance/agent-forking/observations/`.

## 12. Open Research Questions

1. Can we legally and safely persist enough state to emulate “session clone” without over-coupling privacy boundaries?
2. Which conflict resolution policy gives best precision for engineering changes (`last-writer-wins` vs `priority-first` vs `human gate`)?
3. What is the minimal snapshot depth that preserves throughput without causing duplicate discovery loops?
4. Can tool-call parallelism and fork lanes be orchestrated together without schema brittleness regressions?

## 13. Decision Log (Initial)

1. Reject fully isolated same-instance session cloning as not reliably available.
2. Accept clone approximation via deterministic bootstrap + shared evidence bus.
3. Select deterministic resolver-first hybrid architecture.
4. Pilot with quality checks only, then expand breadth once KPIs pass.
