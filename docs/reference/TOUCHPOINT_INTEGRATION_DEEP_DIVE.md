# Touchpoint Integration — Deep Dive

> **Purpose**: Heavy breadth and depth on MCP, CLI, skills, CLAUDE.md, roles, and headless triggers — covering all related conversations, research, plans, **web research**, and **thegent copilot/sitback agents** for research tasks. Companion to [TOUCHPOINT_INTEGRATION_EVALUATION.md](./TOUCHPOINT_INTEGRATION_EVALUATION.md).
> **Scope**: thegent project (`/thegent`), docs, research, plans, cross-referenced sibling projects (tray-app worktree), `~`, `../`, and external web sources.

---

## 1. Related Conversations & Research Index

All documents that bear on touchpoint integration, unified work stream, and civilizational systems:

### 1.1 Work Stream & Backlog

| Doc                        | Path                                                                                           | Summary                                                                          |
| -------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Unified Work Stream Design | [UNIFIED_WORK_STREAM_DESIGN.md](./UNIFIED_WORK_STREAM_DESIGN.md)                               | Canonical WORK_STREAM.md, incorporator agent, 4X/AgilePlus/gardening integration |
| Touchpoint Evaluation      | [TOUCHPOINT_INTEGRATION_EVALUATION.md](./TOUCHPOINT_INTEGRATION_EVALUATION.md)                 | MD vs SQLite, touchpoint matrix, integration rules                               |
| Robustness & Depth         | [ROBUSTNESS_AND_FUTURE_DEPTH.md](./ROBUSTNESS_AND_FUTURE_DEPTH.md)                             | Phase 0–6 evolution, rule sync v2, atomic stream, cockpit design                 |
| Agent Debugging            | [AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md](../guides/AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md) | Error taxonomy, automated remediation, poison pill detection                     |
| Gardener Architecture      | [GARDENER_ARCHITECTURE.md](./GARDENER_ARCHITECTURE.md)                                         | Hunger states, 4X mapping, SCAN→PRIORITIZE→ROUTE→EXECUTE→VERIFY→REPORT           |
| Specs README               | [specs/README.md](../../specs/README.md)                                                       | Gamified flow: intake→breadth→depth→…→archived                                   |
| Work Stream Incorporator   | [agents/work-stream-incorporator.md](../../agents/work-stream-incorporator.md)                 | Agent persona for merging fragments into WORK_STREAM                             |

### 1.2 Queue, Harvest, Handoff

| Doc                                | Path                                                                                       | Summary                                                                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| User Queue + TUI                   | [USER_QUEUE_TUI_AND_AGENT_POLL.md](../research/USER_QUEUE_TUI_AND_AGENT_POLL.md)           | Editable prompts while agent runs; `thegent_queue_list`, `thegent_queue_claim`, `thegent_queue_done`; `prompt_queue.jsonl`        |
| Claude Code Queue Pending Blocking | [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](../research/CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) | $defer/$pending→queue; $block→escalation; UserPromptSubmit intercept; harvest from Cursor transcripts                             |
| Idea Seeds & Session Storage       | [IDEA_SEEDS_SESSION_STORAGE.md](../research/IDEA_SEEDS_SESSION_STORAGE.md)                 | $idea→idea-seeds; $defer/$pending→pending-handoff; Claude/Codex/Cursor paths; harvest-idea-seeds.sh                               |
| Codex Donut Harness                | [CODEX_DONUT_HARNESS_PLAN.md](../plans/CODEX_DONUT_HARNESS_PLAN.md)                        | Unified queue, harvest, rules sync across Claude Code + Codex + Cursor + Factory + Augment; `.thegent/prompt_queue.jsonl` as SSOT |

### 1.3 Multi-Platform & Parity

| Doc                               | Path                                                                                   | Summary                                                                                |
| --------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Multi-Platform Deep Dive          | [MULTI_PLATFORM_DEEP_DIVE.md](../research/MULTI_PLATFORM_DEEP_DIVE.md)                 | 15 Claude hooks, Codex config/history/sqlite, Cursor rules/transcripts, headless modes |
| Multi-Platform Parity Master Plan | [MULTI_PLATFORM_PARITY_MASTER_PLAN.md](../plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md)  | Capability×Platform matrix; unified queue, rules, harvest; hook-by-hook strategy       |
| Claude Code Feature Parity Audit  | [CLAUDE_CODE_FEATURE_PARITY_AUDIT.md](../research/CLAUDE_CODE_FEATURE_PARITY_AUDIT.md) | Full feature audit vs Codex/Cursor                                                     |
| MCP Tool Optimization Plan        | [MCP_TOOL_OPTIMIZATION_PLAN.md](../plans/MCP_TOOL_OPTIMIZATION_PLAN.md)                | MCP tool polish, OPT/ROB/UX mapping                                                    |

### 1.4 Sitback, Skills, CLI

| Doc                              | Path                                                                                                                       | Summary                                                                |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Sitback Design                   | [2026-02-15-thegent-sitback-design.md](../plans/2026-02-15-thegent-sitback-design.md)                                      | `thegent sitback`, startup protocol, skill system, MCP integration     |
| CLI Single Source of Truth Audit | [thegent-cli-single-source-of-truth-audit-2026-02-14.md](../docset/thegent-cli-single-source-of-truth-audit-2026-02-14.md) | All capabilities via `thegent <subcommand>`; no Makefile/script bypass |
| Hook Optimization Strategy       | [HOOK_OPTIMIZATION_STRATEGY.md](./HOOK_OPTIMIZATION_STRATEGY.md)                                                           | Smart skip, prewarm, parallel stages, learning-based skip, daemon mode |

### 1.5 Governance, Triggers, Tooling

| Doc                     | Path                                                                                     | Summary                                                    |
| ----------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| In-Depth Tooling Audit  | [IN_DEPTH_TOOLING_AUDIT_2026.md](../research/IN_DEPTH_TOOLING_AUDIT_2026.md)             | CLI gaps, OPT/ROB items, teammates, run-diff, trace replay |
| Governance Policy Audit | [GOVERNANCE_POLICY_AUDIT_RESEARCH.md](../research/GOVERNANCE_POLICY_AUDIT_RESEARCH.md)   | OPA/Rego, human-as-tool, conflict resolution               |
| Codex Hooks & Extension | [CODEX_HOOKS_AND_EXTENSION_OPTIONS.md](../research/CODEX_HOOKS_AND_EXTENSION_OPTIONS.md) | Codex notify, AfterAgent, session end behavior             |

### 1.6 Project Path Coverage (~, ../, project)

| Scope            | Paths                                                                              | Contents                                                                                                     |
| ---------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **~ (home)**     | `~/.claude/`, `~/.thegent/`                                                        | Pending queue, skills override, session cache; `THGENT_OWNER_TAG` for orchestration                          |
| **../ (parent)** | `../temp-PRODVERCEL/`, `../kush/`                                                  | Sibling projects, tray-app worktree; shared templates                                                        |
| **Project root** | `/thegent` or `$THEGENT_ROOT`                                                      | CLAUDE.md, AGENTS.md, 00_START_HERE.md, agents/, skills/, hooks/, contracts/                                 |
| **docs/**        | `docs/plans/`, `docs/research/`, `docs/reference/`, `docs/docset/`, `docs/guides/` | 270+ MD files; plans (WBS, DAG, ARCH), research (parity, hooks, queue), reference (WORK_STREAM, touchpoints) |
| **specs/**       | `specs/`                                                                           | Intake→breadth→depth→formalizing→approved→archived                                                           |
| **.thegent/**    | `.thegent/sessions/`                                                               | run_registry.jsonl, handoff_registry.jsonl, agileplus/backlog.jsonl                                          |

**Related docs (extended index)**:

- FastMCP: FASTMCP_SPEC_DEEP_DIVE, FASTMCP_FEATURES_AND_TRANSPORT_GAPS, FASTMCP_IMPLEMENTATION_GUIDE, THGENT_FASTMCP_IMPLEMENTATION_PLAN
- Providers: PROVIDER_SETUP_GUIDE, PROVIDER_MODEL_REFERENCE, COMPLETE_PROVIDER_ROUTING_MAP, LITELLM_CLIPROXY_BIFROST_HARMONY
- Cycleloop: 12-LIFECYCLE-LOOP-DESIGN
- Teammates: TEAMMATES_RESEARCH_AND_PLAN
- Phases: PHASE*\*\_PROGRESS_REPORT, PHASE*_\_GUIDE, docset/thegent-phase_-\*

---

## 2. Touchpoint Deep Dive

### 2.1 MCP

**Location**: `src/thegent/mcp_server.py`

**Tools (work-stream relevant)**:

- `thegent_do_next` — reads WORK_STREAM, PLAN_STATUS, FR_TRACKER, docs/plans/, pending-handoff, escalation
- `thegent_run`, `thegent_bg` — execute with prompt_suggestion from do_next
- `thegent_queue_list`, `thegent_queue_claim`, `thegent_queue_done` (planned per USER_QUEUE_TUI)
- `thegent_incorporate` (planned) — run incorporator

**Resources (URI-addressable)**:

- `thegent://workflow/triggers` — workflow instructions
- `thegent://workflow/gardening` — gardening workflow
- `thegent://sitback/dashboard` — unified dashboard
- `thegent://sessions`, `thegent://observe/summary` — run state, contracts
- `thegent://workstream` (recommended) — WORK_STREAM.md or summary

**Prompts**:

- `thegent_workflow_idea` — idea→research→spec→work stream
- `thegent_workflow_quality_green` — task quality-a-r
- `thegent_workflow_next_item` — find next from stream
- `thegent_workflow_gardening` — garden: gov, traceability, dispatch

**Integration**: MCP is primary for agents. All tools/resources should read WORK_STREAM or its derived views. No duplication of workflow logic in prompts vs resources.

### 2.2 CLI

**Location**: `src/thegent/main.py`, `cli.py`, `cli_impl.py`

**Work-stream commands**:

- `thegent plan next` — same as thegent_do_next
- `thegent plan incorporate` — merge WBS into WORK_STREAM
- `thegent govern go health` — 8-dimension gardener scan
- `thegent govern go cycle` — AgilePlus scan→analyze→plan→deploy→verify→commit
- `thegent govern escalate list` — past-SLA escalations

**Single source of truth**: CLI audit (2026-02-14) confirmed all capabilities via CLI. No Makefile or script bypass. Prompt-first syntax canonical.

**Integration**: CLI and MCP share `do_next_impl`, `incorporate_impl`. Skills and CLAUDE.md reference CLI as fallback when MCP unavailable.

### 2.3 Skills

**Location**: `skills/sitback-agent/SKILL.md`, `skills/agent-orchestra/SKILL.md`

**Sitback-agent**:

- Never-idle loop: govern go health, task quality, FR traceability, PLAN_STATUS/FR_TRACKER, escalate list, dispatch, go cycle
- Gardening: converge to empty backlog + green
- References: `thegent_do_next`, WORK_STREAM (via do_next), `thegent://workflow/gardening`

**Agent-orchestra**:

- Add work items to unified stream: docs/reference/, contracts/, docs/plans/
- `thegent_do_next` for next items
- Governance cycle (AgilePlus)

**Integration**: Skills are read-only MD. They should explicitly reference WORK_STREAM and thegent_do_next. No workflow logic duplication — point to CLAUDE.md or MCP resources.

### 2.4 CLAUDE.md

**Location**: Project root `CLAUDE.md`

**Sections (work-stream relevant)**:

- Workflow Triggers table — Hook, Skill, MCP resource, MCP prompts, CLI
- Unified work stream — WORK_STREAM.md as SSOT, incorporator agent
- WBS Agent Coordination — claim in WORK_STREAM, avoid overlap
- Where to Add New Functionality — agents/, hooks/, MCP, CLI, contracts/

**Integration**: CLAUDE.md is the project instruction layer. All agents load it. Trigger table should include `thegent://workstream`. Single place for "read WORK_STREAM before picking work."

### 2.5 Roles (Agents)

**Location**: `agents/*.md`

**Work-stream relevant**:

- `work-stream-incorporator.md` — merges fragments, resolves conflicts
- `backlog-gardener.md` — curates intake (zen-mcp context)
- `wbs-task-executor.md` — executes WBS tasks
- `plan-orchestrator.md` — WBS/PERT, parallel workstreams

**Integration**: Roles are persona definitions. They reference CLAUDE.md, skills, and (when executing) WORK_STREAM. No runtime mutation of roles — MD is correct.

### 2.6 Headless Triggers

**Location**: `src/thegent/governance/triggers.py`, `hooks/gardener-*.sh`

**AgilePlus triggers**:

- **Watchdog** — FS watcher on src/, tests/, hooks/; debounce 30s
- **Timer** — periodic (default 300s)
- **Manual** — `thegent govern go cycle`

**Gardener loop**:

- **Stop** — gardener-loop.sh on session stop
- **Timer** — GARDENER_TIMER env
- **Scan** — gardener-scan.sh (8 hunger states)
- **Spawn** — gardener-spawn.sh (bounded context → agent)

**Integration**: Triggers fire AgilePlusLoop or gardener. Both should consume/produce WORK_STREAM. When `fragmented_research` hunger detected → spawn work-stream-incorporator. AgilePlus backlog.jsonl ↔ WORK_STREAM alignment.

---

## 3. Cross-Cutting Flows

### 3.1 Queue → Handoff → Do-Next

```
$defer / $pending  →  pending-queue.jsonl  →  (Stop) harvest  →  pending-handoff.md
                                                                    ↓
thegent_do_next  ←  WORK_STREAM + pending-handoff + escalation + PLAN_STATUS + FR_TRACKER
```

**Unification (CODEX_DONUT)**: Migrate to `.thegent/prompt_queue.jsonl` as SSOT. Today: `~/.claude/pending-queue.jsonl` or `PROJECT_DIR/.claude/pending-queue.jsonl`. Incorporator can merge pending-handoff items into WORK_STREAM BACKLOG.

### 3.2 Idea → Research → Spec → Work Stream

```
$idea  →  idea-seeds/  →  (optional) breadth/depth  →  specs/formalizing  →  approved
                                                                              ↓
Incorporator  ←  specs/approved, docs/plans/, docs/research/  →  WORK_STREAM BACKLOG
```

**4X mapping**: eXplore (idea, research) → eXpand (spec, formalizing) → eXploit (implementing) → eXterminate (verifying, archived).

### 3.3 Gardener → Incorporator → WORK_STREAM

```
gardener-scan  →  fragmented_research?  →  spawn work-stream-incorporator
                                              ↓
Incorporator  →  scan docs/plans, research, specs  →  merge  →  WORK_STREAM.md
```

### 3.4 AgilePlus → Backlog ↔ WORK_STREAM

```
AgilePlus SCAN  →  findings  →  BacklogManager (backlog.jsonl)
                                    ↓
ANALYZE  →  get_pending()  →  PLANNING  →  DEPLOY  →  agents claim from WORK_STREAM?
                                    ↓
VERIFY  →  resolve/defer  →  backlog.jsonl updated
```

**Bidirectional**: Incorporator merges AgilePlus pending into WORK_STREAM. AgilePlus planner can read WORK_STREAM for remediation tasks.

---

## 4. Multi-Platform Considerations

### 4.1 Hook Availability by Platform

| Hook             | Claude Code | Codex | Cursor | Strategy                                                         |
| ---------------- | :---------: | :---: | :----: | ---------------------------------------------------------------- |
| UserPromptSubmit |      ✓      |   ✗   |   ✗    | prompt-submit-guard (Claude); run_impl preprocessor (Codex exec) |
| Stop             |      ✓      |   ✗   |   ✗    | Wrapper exit + harvest (Codex)                                   |
| SessionStart     |      ✓      |   ✗   |   ✗    | Inject handoff before spawn                                      |
| Harvest          |      ✓      |   ✓   |   ✓    | harvest-idea-seeds from all transcripts                          |

**Implication**: Queue ($defer/$pending) and $block work fully only in Claude Code. Codex/Cursor rely on harvest and run_impl preprocessor. WORK_STREAM and do_next are platform-agnostic (MCP/CLI).

### 4.2 Rules/Skills by Platform

| Platform    | Location             | Format    |
| ----------- | -------------------- | --------- |
| Claude Code | CLAUDE.md, skills/   | MD        |
| Codex       | .codex/skills/       | MD        |
| Cursor      | .cursor/rules/\*.mdc | YAML + MD |
| Factory     | .factory/droids/     | MD        |

**Unification**: `thegent rules sync` (planned) → canonical source to all. WORK_STREAM and workflow instructions should be in a platform-agnostic location (docs/reference/) and referenced by all.

### 4.3 Headless Modes

| Platform    | Headless Entry       | thegent                                           |
| ----------- | -------------------- | ------------------------------------------------- |
| Claude Code | `claude -p "prompt"` | `thegent run agent "prompt" --agent claude`       |
| Codex       | `codex exec -`       | `thegent run agent "prompt" --agent codex`        |
| Cursor      | cursor-agent CLI     | `thegent run agent "prompt" --agent cursor-agent` |

**Implication**: Headless triggers (timer, watchdog) run outside IDE. They use AgilePlusLoop and gardener. No UserPromptSubmit — queue/harvest apply at session boundaries. WORK_STREAM is the primary source for "what to do next" in headless.

---

## 5. Storage & Integration Patterns

### 5.1 File Layout (Canonical)

```
PROJECT/
├── CLAUDE.md                    # Project instructions (read-only for workflow)
├── agents/*.md                  # Roles (read-only)
├── skills/*/SKILL.md            # Skills (read-only)
├── docs/
│   ├── plans/                   # Plans, WBS (source for incorporator)
│   ├── research/                # Research, idea-seeds, pending-handoff
│   ├── docset/                  # Specs, PRD, FR
│   └── reference/
│       ├── WORK_STREAM.md       # Canonical backlog (short-throw)
│       ├── UNIFIED_WORK_STREAM_DESIGN.md
│       └── TOUCHPOINT_*.md
├── specs/                       # intake→archived (unified stream stages)
├── contracts/                   # garden-state, health-targets
└── .thegent/
    └── sessions/
        ├── run_registry.jsonl
        ├── handoff_registry.jsonl
        └── agileplus/
            ├── backlog.jsonl
            └── evidence_ledger.jsonl
```

### 5.2 Read vs Write by Touchpoint

| Touchpoint              | Reads                                           | Writes                         |
| ----------------------- | ----------------------------------------------- | ------------------------------ |
| MCP thegent_do_next     | WORK_STREAM, pending-handoff, escalation, plans | —                              |
| MCP thegent_incorporate | WBS, plans, research, specs                     | WORK_STREAM                    |
| CLI plan next           | Same as do_next                                 | —                              |
| CLI plan incorporate    | WBS                                             | WORK_STREAM                    |
| Skills                  | CLAUDE.md, WORK_STREAM (via do_next)            | —                              |
| Agents (workers)        | WORK_STREAM                                     | WORK_STREAM (claim, complete)  |
| Gardener                | garden-state, specs/                            | garden-state, spawn agents     |
| AgilePlus               | backlog.jsonl, health-targets                   | backlog.jsonl, evidence_ledger |

### 5.3 Conflict Avoidance

- **Single writer for merge**: Incorporator is the only process that merges fragments into BACKLOG. Workers only claim/complete.
- **Claim before edit**: Workers append to CLAIMED before starting; remove and add to COMPLETED when done.
- **Atomic writes**: Use write-to-temp-then-rename for WORK_STREAM.
- **Stale claim recovery**: Incorporator or gardener moves CLAIMED items >7 days back to BACKLOG.

---

## 6. Implementation Roadmap

### Phase 1: Harmonize (Current)

- [x] WORK_STREAM.md canonical
- [x] do_next_impl reads WORK_STREAM first
- [x] plan incorporate CLI
- [x] work-stream-incorporator agent
- [ ] Add `thegent://workstream` MCP resource
- [ ] Skills: explicit WORK_STREAM reference
- [ ] CLAUDE.md: add thegent://workstream to trigger table

### Phase 2: Trigger Wiring

- [ ] Gardener fragmented_research → spawn incorporator
- [ ] AgilePlus ANALYZE → optional merge backlog.jsonl into WORK_STREAM
- [ ] Queue unification: `.thegent/prompt_queue.jsonl` (from CODEX_DONUT)

### Phase 3: Multi-Platform

- [ ] thegent rules sync → all platforms
- [ ] Harvest $defer from Cursor transcripts → pending-handoff
- [ ] Headless: WORK_STREAM as primary next-item source

---

## 7. References (Full Paths)

| Doc                                      | Full Path                                                          |
| ---------------------------------------- | ------------------------------------------------------------------ |
| UNIFIED_WORK_STREAM_DESIGN               | docs/reference/UNIFIED_WORK_STREAM_DESIGN.md                       |
| TOUCHPOINT_INTEGRATION_EVALUATION        | docs/reference/TOUCHPOINT_INTEGRATION_EVALUATION.md                |
| GARDENER_ARCHITECTURE                    | docs/reference/GARDENER_ARCHITECTURE.md                            |
| USER_QUEUE_TUI_AND_AGENT_POLL            | docs/research/USER_QUEUE_TUI_AND_AGENT_POLL.md                     |
| CLAUDE_CODE_QUEUE_PENDING_BLOCKING       | docs/research/CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md                |
| IDEA_SEEDS_SESSION_STORAGE               | docs/research/IDEA_SEEDS_SESSION_STORAGE.md                        |
| CODEX_DONUT_HARNESS_PLAN                 | docs/plans/CODEX_DONUT_HARNESS_PLAN.md                             |
| MULTI_PLATFORM_DEEP_DIVE                 | docs/research/MULTI_PLATFORM_DEEP_DIVE.md                          |
| MULTI_PLATFORM_PARITY_MASTER_PLAN        | docs/plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md                    |
| 2026-02-15-thegent-sitback-design        | docs/plans/2026-02-15-thegent-sitback-design.md                    |
| thegent-cli-single-source-of-truth-audit | docs/docset/thegent-cli-single-source-of-truth-audit-2026-02-14.md |
| HOOK_OPTIMIZATION_STRATEGY               | docs/reference/HOOK_OPTIMIZATION_STRATEGY.md                       |
| IN_DEPTH_TOOLING_AUDIT_2026              | docs/research/IN_DEPTH_TOOLING_AUDIT_2026.md                       |

---

## 8. Web Research (External Landscape)

Findings from web research (DuckDuckGo, MCP spec, coding-with-ai.dev) relevant to touchpoint integration:

### 8.1 MCP Adoption & Ecosystem (2025–2026)

| Source                                    | Finding                                                                                                                                             |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **modelcontextprotocol.io**               | MCP is open protocol (Anthropic Nov 2024); JSON-RPC 2.0; Tools, Prompts, Resources; LSP-inspired; security: user consent, data privacy, tool safety |
| **Microsoft Learn MCP Server**            | GitHub Copilot and agents need trusted docs; MCP servers expose context for grounding                                                               |
| **Enterprise adoption (guptadeepak.com)** | 97M+ monthly SDK downloads; Anthropic, OpenAI, Google, Microsoft backing; auth strategies, implementation paths                                     |
| **arXiv 2504.21030**                      | Multi-agent systems via MCP: context management, coordination, scalable operation                                                                   |
| **Windows 11 MCP**                        | Securing MCP for agentic computing; trust & safety at OS layer                                                                                      |

**Implication for thegent**: `thegent://workstream` as MCP resource aligns with ecosystem. Tools (thegent_do_next, thegent_run) and Resources (workflow/triggers, sitback/dashboard) follow spec. Consider readOnlyHint/idempotentHint annotations.

### 8.2 Claude Code vs Codex vs Cursor Parity

| Source                 | Finding                                                                                                                                                                                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Builder.io**         | Codex vs Claude Code: agents, model choices, costs, workflows                                                                                                                                                                                                    |
| **DoltHub**            | Cursor Agent vs Claude Code; Cursor Agent strong challenger                                                                                                                                                                                                      |
| **coding-with-ai.dev** | **Memory sync**: Claude Code reads `.claude/CLAUDE.md`; Codex/Cursor read `AGENTS.md`. Same instruction drifts across files. Fix: (1) `@AGENTS.md` in CLAUDE.md (Claude inline), (2) pointer "READ AGENTS.md FIRST!!!", (3) symlink `ln -sf AGENTS.md CLAUDE.md` |
| **nxcode.io 2026**     | Codex vs Claude Code vs Cursor: 1M+ developers choose Codex for multi-agent                                                                                                                                                                                      |
| **labs.adaline.ai**    | Autonomous sessions spanning weeks; Cursor agents 3+ weeks, 1M+ lines; migration 266k add, 193k del without human checkpoints                                                                                                                                    |

**Implication for thegent**: `thegent rules sync` (planned) addresses memory sync. WORK_STREAM in docs/reference/ is platform-agnostic. Single source of truth: one file, references everywhere.

### 8.3 Agent Orchestration & Work Stream

| Source                  | Finding                                                                        |
| ----------------------- | ------------------------------------------------------------------------------ |
| **OneReach.ai**         | MCP reduces integration costs, scales multi-agent, powers autonomous workflows |
| **Omnitech**            | MCP for AI agent integration; lunch-and-learn adoption                         |
| **Medium (agentic AI)** | MCP in agentic architecture; industrial applications                           |

**Implication**: Unified work stream (WORK_STREAM.md) + incorporator agent pattern is aligned with industry direction. MCP + CLI + skills as touchpoints is standard.

---

## 9. Using thegent Copilot/Sitback Agents for Breadth & Depth

How to invoke thegent agents for heavy research, coverage, and incorporation tasks.

### 9.1 Agent Types

| Agent                        | Role                               | Invocation                                                      | Best for                                 |
| ---------------------------- | ---------------------------------- | --------------------------------------------------------------- | ---------------------------------------- |
| **copilot**                  | GitHub Copilot (DirectAgentRunner) | `thegent run agent "..." --agent copilot`                       | Quick tasks, fallback                    |
| **gemini**                   | Google Gemini                      | `thegent run agent "..." --agent gemini`                        | Broad research, stable                   |
| **sitback**                  | Dashboard + orchestrator           | `thegent sitback`                                               | Multi-session, gardening, routing        |
| **agent-orchestra**          | Unified orchestration              | `thegent sitback --skill agent-orchestra`                       | Multi-agent coordination                 |
| **work-stream-incorporator** | Merge fragments                    | `thegent run agent "..." --agent gemini` + incorporator persona | Merge docs/plans, research → WORK_STREAM |

### 9.2 Workflow: Breadth & Depth Research

**1. Web research (MCP/CLI)**:

```text
thegent_ddg_search("MCP agent integration 2025")  # MCP tool
thegent run agent "Search DDG for..." --agent gemini  # CLI fallback
```

**2. Parallel sub-agent dispatch:**

```bash
# Spawn 3 agents for parallel research
thegent run agent "Research MCP adoption trends 2025" --agent gemini --bg --cd .
thegent run agent "Research Claude Code vs Codex parity" --agent copilot --bg --cd .
thegent run agent "Research unified backlog patterns" --agent gemini --bg --cd .
```

**3. Sitback orchestration:**

```bash
thegent sitback -a minimax  # or kilo, glm
# In Sitback: thegent_do_next → pick next; thegent run ... --bg for dispatch
# thegent_ddg_search for web research
```

**4. Incorporation:**

```bash
thegent plan incorporate  # Merge WBS → WORK_STREAM
# Or spawn work-stream-incorporator with prompt
```

### 9.3 Skill References for Research

| Skill               | Research-related tools                                                    |
| ------------------- | ------------------------------------------------------------------------- |
| **sitback-agent**   | thegent_ddg_search, thegent_do_next, thegent_run, thegent_observe_summary |
| **agent-orchestra** | Same + workflow triggers (idea→research→spec→work stream)                 |

**Skills**: `skills/sitback-agent/SKILL.md`, `skills/agent-orchestra/SKILL.md`. Both reference `thegent_do_next` and WORK_STREAM. Add explicit `thegent_ddg_search` for research tasks.

### 9.4 Checklist: Heavy Breadth & Depth

- [ ] **Web research**: `thegent_ddg_search` or `mcp_web_fetch` (MCP resource); document in docs/research/
- [ ] **Project paths**: Scan ~, ../, project root; index in docs/reference/ or TOUCHPOINT_INTEGRATION_DEEP_DIVE
- [ ] **Copilot agents**: Use `thegent run agent "..." --agent copilot` or `thegent run agent "..." --agent gemini` for parallel research
- [ ] **Sitback**: `thegent sitback` for dashboard + never-idle gardening; route tasks via thegent_run with `--bg`
- [ ] **Incorporation**: Merge findings into WORK_STREAM via `thegent plan incorporate` or work-stream-incorporator

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
