<DONE>
# Claude Code Plan & Delegate Modes — Deep Research for thegent Tooling

**Purpose:** In-depth research on Claude Code's Plan and Delegate modes to inform thegent tooling for structured agent work, effective looping, and CLI/MCP integration.

**References:** [code.claude.com/docs](https://code.claude.com/docs/llms.txt), [CLAUDE_CODE_FEATURE_PARITY_AUDIT.md](./CLAUDE_CODE_FEATURE_PARITY_AUDIT.md), [CODEX_DONUT_HARNESS_PLAN.md](../plans/CODEX_DONUT_HARNESS_PLAN.md)

---

## 1. Executive Summary

Claude Code exposes distinct modes that heavily structure agent work. thegent extends this with **Discussion**, **Research**, and **Validation** modes, all guided by structured protocols and supporting teams of thegents.

### Claude-Native Modes

| Mode              | Purpose                                                     | Key Mechanism                                                                            | CLI/MCP Surface                             |
| ----------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------- |
| **Plan Mode**     | Read-only exploration → user-approved plan → implementation | `EnterPlanMode` → explore → write plan file → `ExitPlanMode` → user approves → implement | `--permission-mode plan`, `Shift+Tab` cycle |
| **Delegate Mode** | Lead coordinates only; no direct implementation             | Restricts lead to team-management tools (spawn, message, task list)                      | `Shift+Tab` (when agent team active)        |

### thegent-Extended Modes (Design)

| Mode           | Stage          | Purpose                                          | Protocol-Driven            |
| -------------- | -------------- | ------------------------------------------------ | -------------------------- |
| **Discussion** | Elicitation    | Clarify idea, scope, constraints before research | Yes — elicitation brief    |
| **Research**   | Pre-plan       | Explore codebase/docs without changes            | Yes — research report      |
| **Validation** | Post-implement | Verify, review, quality gate                     | Yes — validation checklist |

All modes support **teams of thegents**: agents can spawn and manage teammates, each in a mode-appropriate role, with protocols enforcing structure.

---

## 2. Plan Mode — Deep Dive

### 2.1 What It Is

Plan Mode instructs Claude to **analyze the codebase with read-only operations**, create a plan, and **get user approval** before making any edits. It prevents wasted effort and ensures alignment.

### 2.2 Tools

| Tool                | Role                                                                                                                              |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **EnterPlanMode**   | Transitions into plan mode. Use proactively for non-trivial implementation tasks. Requires user approval.                         |
| **ExitPlanMode**    | Signals plan is complete and ready for user review. Reads plan from file (does NOT take plan as parameter). Triggers approval UI. |
| **AskUserQuestion** | Clarify requirements/approach BEFORE finalizing plan. Do NOT use to ask "Is my plan ready?" — that's ExitPlanMode's job.          |

### 2.3 When to Use Plan Mode

**Use EnterPlanMode when:**

- New feature implementation (e.g., "Add logout button", "Add form validation")
- Multiple valid approaches (e.g., caching: Redis vs in-memory vs file-based)
- Code modifications affecting existing behavior
- Architectural decisions (WebSockets vs SSE, Redux vs Context)
- Multi-file changes (likely >2–3 files)
- Unclear requirements (need to explore first)
- User preferences matter (would use AskUserQuestion to clarify)

**Skip Plan Mode for:**

- Single-line or few-line fixes (typos, obvious bugs)
- Single function with clear requirements
- Very specific, detailed user instructions
- Pure research (use Task tool with Explore agent instead)

### 2.4 Plan Mode Flow

```
1. EnterPlanMode (user approves)
   ↓
2. Explore codebase (Glob, Grep, Read)
   ↓
3. Design implementation approach
   ↓
4. Write plan to plan file (path in plan mode system message)
   ↓
5. ExitPlanMode (request approval)
   ↓
6. User approves → begin implementation
```

### 2.5 CLI & Configuration

```bash
# Start session in Plan Mode
claude --permission-mode plan

# Headless query in Plan Mode
claude --permission-mode plan -p "Analyze auth system and suggest improvements"
```

**Permission modes (Shift+Tab cycle):** Normal → Auto-Accept → Plan → (Delegate if team active)

**Default in settings:**

```json
// .claude/settings.json
{
  "permissions": {
    "defaultMode": "plan"
  }
}
```

### 2.6 Built-in Plan Subagent

Claude Code includes a **Plan** subagent used during plan mode:

- **Purpose:** Codebase research for planning
- **Tools:** Read-only (no Write, Edit)
- **Model:** Inherits from main
- When in plan mode and Claude needs to understand the codebase, it delegates research to the Plan subagent to avoid infinite nesting.

### 2.7 ExitPlanMode Input Schema (from p0/claude-code-prompts)

```json
{
  "allowedPrompts": [
    { "tool": "Bash", "prompt": "run tests" },
    { "tool": "Bash", "prompt": "install dependencies" }
  ],
  "pushToRemote": false,
  "remoteSessionId": null,
  "remoteSessionUrl": null,
  "remoteSessionTitle": null
}
```

`allowedPrompts` describes **prompt-based permissions** needed to implement the plan (semantic categories, not specific commands).

---

## 3. Delegate Mode — Deep Dive

### 3.1 What It Is

Delegate Mode restricts the **team lead** to **coordination-only tools**. The lead cannot implement tasks directly—only spawn teammates, message them, manage the task list, and shut them down.

### 3.2 When It Applies

Delegate Mode is **only available when an agent team is active**. It is part of the permission mode cycle: Normal → Auto-Accept → Plan → **Delegate**.

### 3.3 Lead Restrictions in Delegate Mode

| Allowed             | Blocked                                   |
| ------------------- | ----------------------------------------- |
| Spawn teammates     | Edit, Write, Bash (direct implementation) |
| Message teammates   |                                           |
| Manage task list    |                                           |
| Shut down teammates |                                           |
| Clean up team       |                                           |

### 3.4 Subagent Permission Mode: `delegate`

In subagent configuration, `permissionMode: "delegate"` is for **agent team leads**:

- Coordination-only
- Restricts to team management tools

### 3.5 Use Case

> "Without delegate mode, the lead sometimes starts implementing tasks itself instead of waiting for teammates. Delegate mode prevents this by restricting the lead to coordination-only tools."

---

## 4. Agent Teams vs Subagents

|                   | Subagents                             | Agent Teams                                |
| ----------------- | ------------------------------------- | ------------------------------------------ |
| **Context**       | Own context; results return to caller | Own context; fully independent             |
| **Communication** | Report to main agent only             | Teammates message each other directly      |
| **Coordination**  | Main agent manages all work           | Shared task list, self-coordination        |
| **Best for**      | Focused tasks, result matters         | Complex work, discussion, collaboration    |
| **Token cost**    | Lower                                 | Higher (each teammate = separate instance) |

**Plan Mode + Teammates:** You can require teammates to plan before implementing:

> "Spawn an architect teammate to refactor the authentication module. Require plan approval before they make any changes."

---

## 5. CLI/MCP Tooling Recommendations for thegent

### 5.1 Plan Mode Tooling

| Tool                      | Description                                   | Implementation                                            |
| ------------------------- | --------------------------------------------- | --------------------------------------------------------- |
| `thegent plan start`      | Start Claude Code in plan mode                | `claude --permission-mode plan` (or equivalent for Codex) |
| `thegent plan analyze`    | Headless plan-only analysis                   | `claude --permission-mode plan -p "..."`                  |
| `thegent plan approve`    | Programmatic plan approval (if API supports)  | TBD — may require MCP or hook                             |
| MCP `thegent_plan_status` | Return current plan file path, status         | Read `.claude/` or session state                          |
| MCP `thegent_plan_save`   | Save plan to `docs/plans/` after ExitPlanMode | PostToolUse on ExitPlanMode                               |

### 5.2 Delegate Mode Tooling

| Tool                                   | Description                             | Implementation                           |
| -------------------------------------- | --------------------------------------- | ---------------------------------------- |
| `thegent team create --delegate`       | Create team with lead in delegate mode  | Spawn `claude` with team + delegate mode |
| MCP `thegent_team_assign`              | Assign task to teammate                 | Already in parity audit                  |
| MCP `thegent_team_message`             | Send message to teammate                | Already in parity audit                  |
| MCP `thegent_team_task_done`           | Mark task complete                      | Already in parity audit                  |
| Hook: `SubagentStart` / `SubagentStop` | Log, notify, or gate subagent lifecycle | thegent wrapper                          |

### 5.3 Structured Work Loop (Plan → Delegate → Execute)

Proposed flow for thegent to "heavily structure" agent work:

```
1. User: thegent plan "Refactor auth to OAuth2"
   → claude --permission-mode plan -p "..."
   → Plan written to plan file

2. User reviews plan (or MCP auto-saves to docs/plans/)

3. User: thegent execute-plan
   → claude -p "Implement the plan in docs/plans/PLAN_xxx.md"
   → Or: thegent team create --plan docs/plans/PLAN_xxx.md
   → Teammates get plan as spawn prompt; lead in delegate mode
```

### 5.4 MCP Tools for Plan/Delegate Integration

| MCP Tool                 | Purpose                                        |
| ------------------------ | ---------------------------------------------- |
| `thegent_plan_create`    | Create plan from prompt, return plan ID/path   |
| `thegent_plan_get`       | Get plan content by ID                         |
| `thegent_plan_approve`   | Mark plan approved (for downstream automation) |
| `thegent_team_create`    | Create agent team with optional delegate mode  |
| `thegent_team_lead_mode` | Get/set lead mode (normal, delegate)           |
| `thegent_subagent_spawn` | Spawn subagent with Task tool (Codex parity)   |

### 5.5 Hooks for Looping

| Hook                            | Use Case                                                      |
| ------------------------------- | ------------------------------------------------------------- |
| `UserPromptSubmit`              | Inject plan file path, WORK_STREAM.md, or next-session prompt |
| `PostToolUse` on `ExitPlanMode` | Save plan to `docs/plans/`, emit event for MCP                |
| `SubagentStop`                  | Harvest subagent result, update task list, trigger next step  |
| `TaskCompleted`                 | Exit 2 to block completion + send feedback (quality gate)     |
| `TeammateIdle`                  | Exit 2 to inject feedback, keep teammate working              |

---

## 6. Permission Modes Reference

| Mode                | Behavior                                        |
| ------------------- | ----------------------------------------------- |
| `default`           | Standard permission prompts                     |
| `acceptEdits`       | Auto-accept file edits                          |
| `plan`              | Read-only exploration; plan before implement    |
| `delegate`          | Coordination-only (agent team lead)             |
| `dontAsk`           | Auto-deny (explicitly allowed tools still work) |
| `bypassPermissions` | Skip all checks (use with caution)              |

---

## 7. Key Documentation URLs

- [Common workflows — Plan Mode](https://code.claude.com/docs/en/common-workflows#use-plan-mode-for-safe-code-analysis)
- [Agent teams — Delegate Mode](https://code.claude.com/docs/en/agent-teams#use-delegate-mode)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Agent SDK — Subagents](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Hooks reference](https://code.claude.com/docs/en/hooks)
- [CLI reference](https://code.claude.com/en/cli-reference)

---

## 8. Implementation Priorities for thegent

### Claude-Native Parity

1. **P1 — Plan Mode CLI:** `thegent plan start`, `thegent plan analyze` wrapping `claude --permission-mode plan`
2. **P2 — Plan persistence:** Hook or MCP to save plans to `docs/plans/` after ExitPlanMode
3. **P3 — Delegate Mode:** Integrate with `thegent team` when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
4. **P4 — MCP plan tools:** `thegent_plan_create`, `thegent_plan_get`, `thegent_plan_approve` for automation
5. **P5 — software-planning-mcp alignment:** Ensure `start_planning`, `add_todo`, `save_plan` work with Claude's plan file format

### Extended Modes (Discussion, Research, Validation)

6. **P6 — Protocol schema:** Define YAML/JSON schema for structured protocols (phases, steps, outputs, tool allow/deny)
7. **P7 — Discussion mode:** `thegent discuss` / `thegent elicit`; AskUserQuestion-heavy; brief output
8. **P8 — Research mode:** `thegent research`; read-only + Explore; report output
9. **P9 — Validation mode:** `thegent validate`; checklist-driven; gate on failure
10. **P10 — Mode-aware teams:** `thegent team create --mode {discussion|research|plan|validation}`; protocol injection

---

## 9. Open Questions

- Does Claude Code expose an API for programmatic plan approval (without user interaction)?
- Can thegent wrap Codex in a "plan mode" equivalent (read-only phase + approval + execute)?
- How does `software-planning-mcp`'s plan format align with Claude's plan file format?

---

## 10. Extended Modes: Discussion, Research, Validation

**Purpose:** Design Research, Discussion (Elicitation), and Validation modes to heavily structure agent work via protocols, and support agents calling/managing teams of thegents.

### 10.1 Mode Pipeline Overview

```
Idea → Discussion (Elicitation) → Research → Plan → Execute → Validation
  │           │                      │         │        │          │
  │           │                      │         │        │          └─ Validation mode
  │           │                      │         │        └─ Normal / Delegate (teams)
  │           │                      │         └─ Plan mode
  │           │                      └─ Research mode
  │           └─ Discussion mode
  └─ Raw user input
```

| Mode           | Stage           | Purpose                                               | Output                                             |
| -------------- | --------------- | ----------------------------------------------------- | -------------------------------------------------- |
| **Discussion** | Elicitation     | Clarify idea, scope, constraints before any deep work | Elicited brief, decision points, success criteria  |
| **Research**   | Pre-plan        | Explore codebase, docs, options without commitment    | Research report, options analysis, recommendations |
| **Plan**       | Pre-implement   | Design approach, get approval                         | Approved plan file                                 |
| **Delegate**   | Execute (teams) | Lead orchestrates; teammates implement                | Completed work                                     |
| **Validation** | Post-implement  | Verify, review, quality gate                          | Pass/fail, findings, recommendations               |

### 10.2 Discussion Mode (Elicitation)

**When:** Idea stage — before research. User has a rough idea; agent must elicit requirements, constraints, and success criteria before proceeding.

**Structured protocol:**

1. **Capture the idea** — Paraphrase and confirm understanding
2. **Elicit scope** — What's in? What's out? Boundaries?
3. **Elicit constraints** — Tech stack, timeline, team, compliance
4. **Elicit success criteria** — How do we know we're done?
5. **Identify decision points** — Choices that need user input before research
6. **Produce elicitation brief** — Structured artifact (e.g. `docs/briefs/ELICIT_xxx.md`)

**Tool restrictions:**

- **Allowed:** AskUserQuestion, Write (brief only), Read (existing briefs/specs)
- **Blocked:** Edit (codebase), Bash, Glob/Grep (codebase exploration)
- **Rationale:** No codebase diving yet — pure elicitation

**Team management:**

- **Elicitation team:** Multiple agents with different lenses (user advocate, technical skeptic, domain expert) can run in parallel to elicit from different angles; lead synthesizes into single brief
- **MCP:** `thegent_discussion_start`, `thegent_discussion_add_question`, `thegent_discussion_finalize` → produces brief

**CLI surface:**

```bash
thegent discuss "Add OAuth2 to our app"
thegent elicit --prompt "..." --output docs/briefs/
```

### 10.3 Research Mode

**When:** After elicitation (or when idea is clear). Deep exploration without making changes.

**Structured protocol:**

1. **Research plan** — What questions to answer? What to explore?
2. **Execute research** — Read, Grep, Glob, WebSearch, WebFetch, Task(Explore)
3. **Synthesize** — Options, trade-offs, recommendations
4. **Produce research report** — `docs/research/RESEARCH_xxx.md`

**Tool restrictions:**

- **Allowed:** Read, Grep, Glob, WebSearch, WebFetch, Task(Explore), Write (report only)
- **Blocked:** Edit (codebase), Bash (except read-only queries if needed)
- **Rationale:** Exploration only; no modifications

**Team management:**

- **Research team:** Parallel researchers (e.g. "auth patterns", "OAuth2 libs", "migration risks") each produce findings; lead synthesizes
- **MCP:** `thegent_research_start`, `thegent_research_assign`, `thegent_research_harvest`, `thegent_research_finalize`

**CLI surface:**

```bash
thegent research "OAuth2 migration options for our stack"
thegent research --brief docs/briefs/ELICIT_xxx.md
```

### 10.4 Validation Mode

**When:** After implementation. Verify work, run tests, check compliance, review before merge.

**Structured protocol:**

1. **Validation checklist** — Load from protocol (e.g. `.thegent/protocols/validation.md`) or MCP
2. **Execute checks** — Tests, lint, security scan, coverage, manual review
3. **Report** — Pass/fail per item, findings, recommendations
4. **Gate** — Block merge/complete if critical failures (configurable)

**Tool restrictions:**

- **Allowed:** Read, Grep, Glob, Bash (tests, lint, scripts), Write (report only)
- **Blocked:** Edit (codebase) — validation is read-only + execute tests
- **Rationale:** Verify, don't change (unless "fix and re-validate" is explicit)

**Team management:**

- **Validation team:** Parallel validators (security, perf, tests, UX review) each run checks; lead aggregates report
- **Hooks:** `TaskCompleted` exit 2 → block completion until validation passes
- **MCP:** `thegent_validation_start`, `thegent_validation_run`, `thegent_validation_report`, `thegent_validation_gate`

**CLI surface:**

```bash
thegent validate
thegent validate --protocol .thegent/protocols/pr-review.md
```

### 10.5 Structured Protocols

Each mode is **heavily guided** by a protocol — a defined sequence of steps, required outputs, and tool constraints.

**Protocol format (proposed):**

```yaml
# .thegent/protocols/discussion.md or discussion.yaml
name: elicitation
mode: discussion
phases:
  - id: capture
    steps: [paraphrase, confirm]
    output: understanding_summary
  - id: scope
    steps: [in_scope, out_of_scope, boundaries]
    output: scope_section
  - id: constraints
    steps: [tech, timeline, team, compliance]
    output: constraints_section
  - id: success
    steps: [done_criteria, acceptance]
    output: success_criteria
  - id: decisions
    steps: [identify_choices]
    output: decision_points
required_output: docs/briefs/ELICIT_{id}.md
tool_allowlist: [AskUserQuestion, Write]
tool_denylist: [Edit, Bash, Glob, Grep]
```

**Protocol loading:**

- MCP: `thegent_protocol_get(mode)` → returns protocol for agent to follow
- CLI: `thegent discuss --protocol .thegent/protocols/elicitation.yaml`
- System prompt injection: Protocol steps injected when mode is active

### 10.6 Teams of Thegents — Mode-Aware Orchestration

**Principle:** Agents can **call and manage teams of thegents**; each teammate can be in a different mode.

| Scenario                         | Lead mode  | Teammate modes                           | Flow                                  |
| -------------------------------- | ---------- | ---------------------------------------- | ------------------------------------- |
| Elicitation from multiple angles | Discussion | Discussion (3x: user, tech, domain)      | Lead synthesizes brief                |
| Parallel research                | Research   | Research (Nx: each owns a question)      | Lead synthesizes report               |
| Plan + implement                 | Delegate   | Plan (architect) + Normal (implementers) | Architect plans; implementers execute |
| Parallel validation              | Validation | Validation (Nx: security, perf, tests)   | Lead aggregates report                |

**MCP tools for team + mode:**
| Tool | Purpose |
|------|---------|
| `thegent_team_create` | Create team; `mode` param: discussion, research, plan, delegate, validation |
| `thegent_team_set_mode` | Set mode for lead or specific teammate |
| `thegent_team_spawn` | Spawn teammate with mode + protocol |
| `thegent_protocol_list` | List available protocols |
| `thegent_protocol_get` | Get protocol by mode/name |

**CLI:**

```bash
# Elicitation team
thegent team create --mode discussion --teammates 3 --prompt "Elicit requirements for OAuth2"

# Research team
thegent team create --mode research --teammates 4 --prompt "Research OAuth2 options" --brief docs/briefs/ELICIT_xxx.md

# Validation team
thegent team create --mode validation --teammates 3 --protocol .thegent/protocols/pr-review.md
```

### 10.7 Implementation Priorities (Extended Modes)

See **§8** for the full priority list. For Discussion, Research, and Validation modes specifically:

| Order | Item                         | Notes                                                  |
| ----- | ---------------------------- | ------------------------------------------------------ |
| 1     | Protocol schema + loader     | YAML/JSON; phases, steps, outputs, tool allow/deny     |
| 2     | Discussion mode              | AskUserQuestion-heavy; brief output; tool restrictions |
| 3     | Research mode                | Read-only + Explore; report output                     |
| 4     | Validation mode              | Checklist-driven; gate on failure                      |
| 5     | `thegent team create --mode` | Mode-aware team spawning                               |
| 6     | MCP protocol tools           | `thegent_protocol_get`, `thegent_team_set_mode`        |
| 7     | Protocol injection           | System prompt or skill that enforces protocol steps    |

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added delegation patterns
2. Added mode configurations
3. Enhanced cross-references

### Cross-References Added

- CLAUDE_CODE_FEATURE_PARITY_AUDIT.md
- SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md

### Practical Additions

- Delegation templates
- Mode configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [CLAUDE_CODE_FEATURE_PARITY_AUDIT.md](./CLAUDE_CODE_FEATURE_PARITY_AUDIT.md) - Feature parity
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
