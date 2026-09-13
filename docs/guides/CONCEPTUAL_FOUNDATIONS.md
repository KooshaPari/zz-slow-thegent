# Conceptual Foundations of thegent

**Purpose:** Explain the core domain concepts so a newcomer can read any thegent document and understand the vocabulary.
**Audience:** Developers, AI agents, and contributors new to the project.

---

## The Big Picture

thegent is an **agent orchestration and governance platform**. It solves a specific problem: when you have multiple AI coding agents (Claude, Codex, Gemini, Copilot, Cursor, and others), each with different CLIs, APIs, output formats, and failure modes, you need a unified layer that:

- Routes tasks to the right provider
- Normalizes their outputs into a common format
- Enforces quality and safety policies
- Coordinates multiple concurrent agents
- Maintains an auditable record of everything that happened

The name "thegent" is short for "the agent" -- it is the single entry point for all agent operations.

---

## Core Concepts

### 1. Agents and Runners

An **agent** is any AI coding assistant that can accept a prompt and produce output. thegent supports:

| Agent                                         | Runner Type       | How It Works                            |
| --------------------------------------------- | ----------------- | --------------------------------------- |
| Claude                                        | DirectAgentRunner | Invokes `claude` CLI binary directly    |
| Codex                                         | CodexProxyRunner  | Routes through CLIProxyAPIPlus proxy    |
| Gemini                                        | DirectAgentRunner | Invokes `gemini` CLI binary directly    |
| Copilot                                       | DirectAgentRunner | Invokes `copilot` CLI binary directly   |
| Cursor                                        | CursorApiRunner   | Calls cursor-api HTTP backend           |
| Others (antigravity, minimax, glm, roo, kilo) | CodexProxyRunner  | Routes through proxy with model mapping |

A **runner** implements the strategy pattern: each agent type has a runner class that knows how to invoke it, capture output, and handle errors. All runners implement `AgentRunner.run()` returning a `RunResult` with exit code, stdout, stderr, and timeout status.

The **Agent Registry** maps agent names to runners, resolves aliases (e.g., "cursor" resolves to "cursor-agent"), and provides `get_runner()` for any registered agent.

### 2. Providers and Routing

A **provider** is the upstream AI service. Routing decides which provider handles a given task based on:

- **Cost**: estimated $/1k tokens (input and output)
- **Quality**: historical success rate and confidence scores
- **Speed**: latency characteristics
- **Availability**: whether the provider is up and within rate limits

The routing system uses a **Pareto frontier** approach, selecting providers that are not dominated on cost-quality-speed dimensions. LiteLLM integration handles the actual routing resolution.

When a provider hits a rate limit or usage cap, the **fallback chain** kicks in. Each provider has an ordered list of alternatives. The **FallbackStateMachine** iterates through this chain, retrying with exponential backoff per provider before falling back to the next.

### 3. Contracts and Canonical Structured Messages (CSM)

Every agent produces output in a different format. thegent normalizes all output into a **Canonical Structured Message (CSM)**, the lingua franca of the system.

A CSM contains:

| Field Group    | Fields                                                               | Purpose                     |
| -------------- | -------------------------------------------------------------------- | --------------------------- |
| **Identity**   | task_id, run_id, chunk_id                                            | Uniquely identify the work  |
| **Lifecycle**  | status (PENDING/RUNNING/COMPLETED/FAILED), phase, progress (0.0-1.0) | Track where the work stands |
| **Content**    | objective, summary, actions_completed, issues, next_steps            | What happened               |
| **Governance** | evidence_set_hash, policy_gate_id, decision_reason_code              | Audit and compliance        |
| **Metadata**   | schema_version, source_contract, raw_payload                         | Versioning and traceability |

**Output adapters** convert provider-specific formats (XML tags, plain text, structured JSON) into CSMs. Each provider has a registered adapter. When an adapter fails, the system falls back to a generic plain-text extractor with reduced confidence.

**Contract versions** are tracked in a registry (csm-v1, task-tool-18, zen-rich-v1) with compatibility matrices and deprecation windows.

### 4. Governance

Governance is the set of rules and policies that constrain what agents can do. It operates at multiple levels:

#### Input Guardrails (Before Execution)

Checks applied before any agent runs:

- **Prompt length** -- rejects prompts exceeding 64K characters
- **Prompt blocklist** -- rejects prompts matching forbidden regex patterns
- **Agent allowlist** -- restricts which agents may be used
- **Model allowlist** -- restricts which models may be used
- **CWD restriction** -- limits which directories agents can operate in

All guardrails are configurable via environment variables (`THGENT_PROMPT_MAX_CHARS`, `THGENT_AGENT_ALLOWLIST`, etc.).

#### Cost Governance (During/After Execution)

- **Cost estimation** per run using a pricing table ($/1k tokens by model)
- **Daily cost aggregation** by owner
- Budget enforcement to prevent runaway spending

#### Policy Engine

The policy engine evaluates governance contracts stored in `contracts/`. These are JSON policy definitions that specify allowed behaviors, required evidence, and decision criteria. The `qa-policy-engine.sh` hook evaluates policies at runtime.

#### Audit Trail

Every run is recorded in `run_registry.jsonl` with SHA-256 hash chaining. Each record includes the hash of the previous record, creating a tamper-evident audit log. This covers:

- Run start/end timestamps
- Provider used, model selected
- Cost incurred
- Policy decisions (allow/deny/warn)
- Evidence artifacts with hash values

### 5. Hooks and Lifecycle

thegent uses a **lifecycle hook system** to inject quality gates at every stage of agent operation:

| Event                  | When It Fires         | Example Hooks                                  |
| ---------------------- | --------------------- | ---------------------------------------------- |
| SessionStart           | Agent session begins  | spec-preflight, qa-preflight                   |
| PreToolUse:Write       | Before writing a file | doc-location-guard, suppression-blocker        |
| PreToolUse:Edit        | Before editing a file | pre-write-validator, suppression-blocker       |
| PostToolUse:Edit/Write | After a file change   | change-doc-tracker, async-test-runner          |
| Stop                   | Session ending        | quality-gate, spec-verifier, security-pipeline |

Hooks live in `hooks/<event>-<name>.sh` and are registered in `hooks/hook-config.yaml`. Shared hook utilities live in `hooks/lib/` and are sourced (never called directly).

The **HookDispatcher** routes lifecycle events to the appropriate hooks. Hooks can block operations (pre-hooks returning non-zero) or run asynchronously (post-hooks).

### 6. Work Streams and Plans

A **work stream** is a sequence of tasks organized in a backlog. The canonical work stream lives at `docs/reference/WORK_STREAM.md`. Agents claim items, execute them, and mark them complete.

Key work stream commands:

- `thegent plan do-next` -- claim and execute the next backlog item
- `thegent plan loop` -- continuously process backlog items
- `thegent plan incorporate` -- merge fragments from research/specs into the plan

**Plans** follow a phased WBS (Work Breakdown Structure) with DAG dependencies:

- **Phases**: Discovery, Design, Build, Test/Validate, Deploy/Handoff
- **Tasks**: Each has an ID, description, and explicit predecessors
- No human checkpoints -- all timescales assume agent-driven execution

### 7. The Agent Mesh (Coordination)

When multiple agents work concurrently, the **agent mesh** prevents collisions:

- **Mesh discovery** (`thegent mesh discover`) -- finds running agents
- **Mesh status** (`thegent mesh status`) -- shows who is doing what
- **Task sync** -- prevents two agents from editing the same file
- **Voting and broadcast** -- multi-agent consensus protocols

The mesh builds on the **Multi-Tenant Agent Civilization Framework**, which defines:

- **Agent identity**: `{project}:{uuid}:L{tier}:{role-slug}`
- **Tiers**: L1 (supervisors), L2 (workers), L3 (specialists)
- **Communication patterns**: Task dispatch, peer negotiation, status broadcast, resource contention, escalation

### 8. MCP (Model Context Protocol)

thegent runs as an **MCP server** (port 3847), exposing tools that AI agents can call. This is how agents running inside Claude Code, Cursor, or other harnesses interact with thegent capabilities:

- Queue management tools
- Memory tools (add, scrape, synthesize)
- Work stream tools
- Coordination tools

The MCP server uses the **FastMCP** framework for tool registration and lifecycle management.

### 9. Memory and the Gardener

**Memory** is thegent's knowledge persistence layer, backed by Supermemory.ai for cloud-scale graph memory. Agents use memory tools to:

- `thegent_memory_add` -- log discoveries, lessons, friction points
- `thegent_memory_scrape_session` -- ingest user prompts and intents
- `thegent_memory_synthesize` -- generate summaries before finishing major tasks

The **Gardener** is an automated background agent that synthesizes audit logs and session history into governance documents (CLAUDE.md, ADR.md, PRD.md), reducing documentation debt over time.

### 10. Execution Modes

thegent supports several multi-agent execution patterns:

| Mode                  | Description                                         | Min Agents |
| --------------------- | --------------------------------------------------- | ---------- |
| SOLO                  | Single agent, no coordination                       | 1          |
| SEQUENTIAL_DELEGATION | Chain of agents, each building on prior output      | 2          |
| PARALLEL_CONSENSUS    | Multiple agents work simultaneously, results merged | 2          |
| REVIEW_LOOP           | Worker produces, reviewer validates, iterate        | 2          |
| ARBITRATION_QUORUM    | Multiple agents vote on the best approach           | 3          |

---

## How It All Fits Together

A typical thegent run flows through these layers:

```
User/Agent prompt
       |
  Input Guardrails (governance check)
       |
  Routing Engine (select provider)
       |
  Agent Runner (invoke provider CLI/API)
       |
  Output Adapter (normalize to CSM)
       |
  Semantic Validation (check CSM invariants)
       |
  Policy Engine (evaluate governance contracts)
       |
  Audit Trail (hash-chained registry entry)
       |
  Result returned to caller
```

If the provider fails, the fallback state machine retries and falls back through the provider chain. If governance blocks the run, the caller gets a clear rejection with remediation instructions.

---

## Glossary

| Term               | Definition                                                           |
| ------------------ | -------------------------------------------------------------------- |
| **Agent**          | An AI coding assistant (Claude, Codex, Gemini, etc.)                 |
| **Runner**         | Strategy-pattern implementation that invokes a specific agent type   |
| **Provider**       | The upstream AI service backing an agent                             |
| **CSM**            | Canonical Structured Message -- normalized output format             |
| **Contract**       | A governance policy definition (JSON)                                |
| **Hook**           | A lifecycle callback that enforces quality/policy at specific events |
| **Mesh**           | The coordination layer for multi-agent work                          |
| **Gardener**       | Automated agent for documentation synthesis                          |
| **Work stream**    | Ordered backlog of tasks for agents to execute                       |
| **Harness**        | The agent layer/environment (e.g., Claude Code CLI, Cursor IDE)      |
| **MCP**            | Model Context Protocol -- how agents call thegent tools              |
| **Fallback chain** | Ordered list of alternative providers when primary fails             |
| **Guardrail**      | Pre-execution policy check (prompt length, blocklist, etc.)          |

---

## Further Reading

| Topic                          | Document                                                             |
| ------------------------------ | -------------------------------------------------------------------- |
| Full product requirements      | [PRD.md](../../PRD.md)                                               |
| Formal functional requirements | [FUNCTIONAL_REQUIREMENTS.md](../../FUNCTIONAL_REQUIREMENTS.md)       |
| Architecture decisions         | [ADR.md](../../ADR.md)                                               |
| Civilization architecture      | [docs/architecture/civilization.md](../architecture/civilization.md) |
| Coordination patterns          | [docs/concepts/coordination.md](../concepts/coordination.md)         |
| Anti-patterns to avoid         | [anti-patterns.md](./anti-patterns.md)                               |
| Learning progression           | [LEARNING_PATHS.md](./LEARNING_PATHS.md)                             |
