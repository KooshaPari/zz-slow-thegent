<DONE>
# Multi-Agent Feature Parity Audit

**Purpose:** Audit all modern agent platforms — **Claude Code**, **Codex**, **Cursor-agent**, **Factory droid**, **Augment Code** — and map equivalents. Informs the Agent Orchestration Harness plan for full parity across all surfaces (interactive + headless, agents/teammates, rules, hooks).

**Scope:** Claude Code (reference), Codex, Cursor-agent (rules, skills), Factory droid (droid exec), Augment Code (auggie CLI, Context Engine MCP).

**References:** [code.claude.com/docs](https://code.claude.com/docs/llms.txt), [MULTI_PLATFORM_PARITY_MASTER_PLAN.md](../plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md), [CODEX_DONUT_HARNESS_PLAN.md](../plans/CODEX_DONUT_HARNESS_PLAN.md), [MULTI_PLATFORM_DEEP_DIVE.md](./MULTI_PLATFORM_DEEP_DIVE.md) (schemas, configs, transcripts)

---

## 1. Claude Code Feature Matrix

### 1.1 Hooks (15 events)

| Hook                   | When                 | Blocking? | Claude Code | Codex                           | thegent Strategy                                            |
| ---------------------- | -------------------- | --------- | ----------- | ------------------------------- | ----------------------------------------------------------- |
| **SessionStart**       | New session / resume | No        | ✓ Native    | ✗ None                          | Wrapper: inject handoff before spawn                        |
| **UserPromptSubmit**   | Before prompt sent   | Yes       | ✓ Native    | ✗ None                          | Exec: run_impl preprocessor; Interactive: SDK or custom TUI |
| **PreToolUse**         | Before tool call     | Yes       | ✓ Native    | ✗ None                          | Wrapper/SDK only; exec has no tool loop                     |
| **PermissionRequest**  | Permission dialog    | Yes       | ✓ Native    | ✗ None                          | Codex has different permission model                        |
| **PostToolUse**        | After tool call      | No        | ✓ Native    | AfterToolUse (not configurable) | codex-notify if AfterToolUse enabled                        |
| **PostToolUseFailure** | After tool fails     | No        | ✓ Native    | ✗ None                          | —                                                           |
| **Notification**       | Various              | No        | ✓ Native    | ✗ None                          | —                                                           |
| **SubagentStart**      | Subagent spawned     | No        | ✓ Native    | ✗ No subagents                  | thegent: spawn codex exec as "subagent"                     |
| **SubagentStop**       | Subagent done        | Yes       | ✓ Native    | ✗ None                          | Wrapper: on codex exec exit                                 |
| **Stop**               | Session ends         | Yes       | ✓ Native    | ✗ None                          | Wrapper exit hook                                           |
| **TeammateIdle**       | Teammate about idle  | Yes       | ✓ Native    | ✗ No teammates                  | thegent team: wrapper monitors                              |
| **TaskCompleted**      | Task marked done     | Yes       | ✓ Native    | ✗ None                          | thegent task list: MCP tools                                |
| **PreCompact**         | Before compaction    | No        | ✓ Native    | ✗ None                          | —                                                           |
| **SessionEnd**         | Session terminates   | No        | ✓ Native    | ✗ None                          | Wrapper exit hook                                           |

### 1.2 Execution Modes

| Mode                  | Claude Code                             | Codex                  | Parity                                   |
| --------------------- | --------------------------------------- | ---------------------- | ---------------------------------------- |
| **Interactive TUI**   | `claude`                                | `codex`                | Both have; Codex lacks hook interception |
| **Headless**          | `claude -p "prompt"` (Agent SDK CLI)    | `codex exec -` (stdin) | Both have; thegent run wraps both        |
| **Continue**          | `claude -p "..." --continue`            | —                      | Codex exec is single-turn                |
| **Resume**            | `claude -p "..." --resume SESSION_ID`   | —                      | Codex exec is stateless                  |
| **Structured output** | `--output-format json`, `--json-schema` | `--json` (exec)        | Both support JSON                        |
| **Stream**            | `--output-format stream-json`           | —                      | Codex exec streams to stdout             |
| **Allowed tools**     | `--allowedTools "Bash,Read,Edit"`       | Sandbox mode           | Different models                         |

### 1.3 Agents & Teammates

| Feature              | Claude Code                                               | Codex  | thegent Strategy                                                        |
| -------------------- | --------------------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| **Subagents**        | Task tool spawns helper; reports back                     | ✗ None | thegent_run/thegent_bg as "subagent" — Codex calls MCP                  |
| **Agent teams**      | Lead + teammates; shared task list; inter-agent messaging | ✗ None | **thegent team** wrapper: spawn N codex execs, shared task list via MCP |
| **Teammate display** | In-process or split panes (tmux/iTerm2)                   | —      | thegent: tmux splits or in-process list                                 |
| **TeammateIdle**     | Exit 2 → feedback, keep working                           | —      | Wrapper: poll teammate stdout; inject prompt                            |
| **TaskCompleted**    | Exit 2 → block completion, send feedback                  | —      | thegent_queue + MCP: task lifecycle                                     |
| **Delegate mode**    | Lead coordination-only                                    | —      | thegent team lead: skills restrict to spawn/message                     |

### 1.4 Skills & Customization

| Feature       | Claude Code                       | Codex            | Parity                               |
| ------------- | --------------------------------- | ---------------- | ------------------------------------ |
| **Skills**    | `.claude/skills/`, slash commands | `.codex/skills/` | Both have                            |
| **CLAUDE.md** | Project context                   | —                | Codex uses different project context |
| **Agents**    | Custom agent types (subagents)    | —                | Codex skills can define personas     |
| **Plugins**   | Marketplaces, hooks, MCP          | —                | Codex: MCP only                      |
| **Memory**    | user, project, local              | —                | Codex: session-scoped                |

### 1.5 MCP & Tools

| Feature            | Claude Code                                          | Codex        | Parity        |
| ------------------ | ---------------------------------------------------- | ------------ | ------------- |
| **MCP**            | Full support                                         | Full support | ✓ Both        |
| **Tool matchers**  | PreToolUse matcher: `Bash`, `Edit\|Write`, `mcp__.*` | —            | N/A for Codex |
| **MCP tool hooks** | PreToolUse on `mcp__memory__.*` etc.                 | —            | —             |

### 1.6 Permissions & Sandbox

| Feature              | Claude Code                                 | Codex              | Parity               |
| -------------------- | ------------------------------------------- | ------------------ | -------------------- |
| **Permission modes** | default, plan, acceptEdits, dontAsk, bypass | Sandbox modes      | Different            |
| **Plan approval**    | Teammates: require plan before impl         | —                  | thegent: skill + MCP |
| **Sandbox**          | Bash tool sandbox                           | codex exec sandbox | Both                 |

### 1.7 Session & Continuity

| Feature           | Claude Code                      | Codex | Parity                                   |
| ----------------- | -------------------------------- | ----- | ---------------------------------------- |
| **Checkpointing** | Rewind, summarize                | —     | thegent: run registry                    |
| **Resume**        | `--resume SESSION_ID`            | —     | Codex: new session each exec             |
| **Handoff**       | pending-handoff.md, next-session | —     | Shared: .thegent/next-session-prompts.md |

---

## 2. Parity Summary

| Category        | Claude Code             | Codex Native   | Codex + thegent Harness                                                         |
| --------------- | ----------------------- | -------------- | ------------------------------------------------------------------------------- |
| **Hooks**       | 15 events               | 1 (AfterAgent) | SessionStart/Stop/UserPromptSubmit via wrapper; PreToolUse/PostToolUse need SDK |
| **Interactive** | Full                    | Full           | Wrapper adds exit hook                                                          |
| **Headless**    | `claude -p`             | `codex exec -` | Both; thegent run unifies                                                       |
| **Subagents**   | Native                  | —              | Via thegent_run MCP (Codex calls it)                                            |
| **Agent teams** | Native                  | —              | **thegent team** wrapper: N codex execs + shared task list                      |
| **Queue**       | UserPromptSubmit + Stop | —              | run_impl preprocessor + wrapper exit                                            |
| **Skills**      | Yes                     | Yes            | Both                                                                            |
| **MCP**         | Yes                     | Yes            | Both                                                                            |

---

## 3. thegent Team Wrapper (Agent Teams Parity)

**Goal:** Provide agent teams for Codex equivalent to Claude Code's teammates.

**Architecture:**

```
User: "Create a team: UX, architecture, devil's advocate"
  → thegent team create --prompt "..." --teammates 3
  → Spawns: lead (thegent codex or codex) + 3 codex exec processes
  → Shared task list: .thegent/teams/{id}/tasks/
  → Lead coordinates via MCP: thegent_team_assign, thegent_team_message, thegent_team_task_done
  → Teammates: each runs codex exec with task prompt; report via file or MCP
```

**Components:**

- `thegent team create` — spawn lead + N teammates
- `thegent team list` — show active teammates
- `thegent team message <id> "..."` — send message to teammate
- `thegent team shutdown <id>` — graceful shutdown
- MCP tools: `thegent_team_assign`, `thegent_team_task_list`, `thegent_team_task_claim`, `thegent_team_task_done`, `thegent_team_message`, `thegent_team_broadcast`
- Display: tmux splits (like Claude) or in-process (Shift+Up/Down style via TUI)

**TeammateIdle parity:** Wrapper polls teammate stdout; when idle, can run "TeammateIdle" hook logic (e.g. exit 2 → inject feedback prompt).

---

## 4. Interactive + Headless Parity

| Surface         | Claude Code        | Codex                              | thegent                                                           |
| --------------- | ------------------ | ---------------------------------- | ----------------------------------------------------------------- |
| **Interactive** | `claude`           | `codex`                            | `thegent codex` (wrapper) or `thegent dex`                        |
| **Headless**    | `claude -p "..."`  | `codex exec -`                     | `thegent run -M codex "..."`                                      |
| **Both**        | Same binary, flags | Different: `codex` vs `codex exec` | `thegent run` unifies headless; `thegent codex` wraps interactive |

**Unified CLI:**

- `thegent run -M codex "prompt"` — headless (already exists)
- `thegent codex` or `thegent dex max` — interactive
- `thegent run -M claude "prompt"` — headless Claude (if claude -p available)
- `thegent clode` — interactive Claude

---

## 5. Hook Parity Strategy (Codex)

| Hook                   | Strategy                                                    |
| ---------------------- | ----------------------------------------------------------- |
| **SessionStart**       | Wrapper: before spawn, load handoff, inject as first prompt |
| **UserPromptSubmit**   | Exec: run_impl preprocessor. Interactive: SDK or custom TUI |
| **PreToolUse**         | SDK only (we own tool loop). Exec: N/A (single turn)        |
| **PostToolUse**        | codex-notify if AfterToolUse configurable; else —           |
| **Stop**               | Wrapper exit hook                                           |
| **SubagentStart/Stop** | thegent_run as subagent; on thegent run exit = SubagentStop |
| **TeammateIdle**       | Wrapper: poll teammate, run hook script                     |
| **TaskCompleted**      | thegent_queue + MCP task lifecycle                          |
| **SessionEnd**         | Wrapper exit hook (same as Stop)                            |

---

## 6. Cursor-Agent

### 6.1 Features

| Feature          | Cursor                                  | Description                                       | thegent Parity                            |
| ---------------- | --------------------------------------- | ------------------------------------------------- | ----------------------------------------- |
| **Rules**        | `.cursor/rules/*.mdc`                   | YAML frontmatter: description, globs, alwaysApply | Map to CLAUDE.md/.codex/skills; rule sync |
| **.cursorrules** | Project root                            | Legacy rules file                                 | Merge into rules or CLAUDE.md             |
| **AGENTS.md**    | Project root                            | Agent instructions                                | Cross-reference                           |
| **Skills**       | `.cursor/skills-cursor/*`               | Slash commands, SKILL.md                          | Sync from unified rules                   |
| **Modes**        | `/plan`, agent, background agent        | Plan mode, interactive, background                | thegent run: mode; bg for background      |
| **Hooks**        | Auto-format, gating, commit checkpoints | Similar to Claude Code                            | Harvest from Cursor transcripts           |
| **Composer**     | Multi-agent orchestration               | Cursor's agent UI                                 | thegent run via cursor-api                |

### 6.2 Rule System Parity

**Cursor rules:** `.cursor/rules/*.mdc` — description, globs, alwaysApply. File-specific or global.

**Unified rule mapping:**

- **Claude Code:** CLAUDE.md, skills
- **Codex:** .codex/skills/, config
- **Cursor:** .cursor/rules/, .cursorrules
- **thegent:** Single source → sync to all agents: `thegent rules sync` writes to .cursor/rules/, injects into CLAUDE.md, .codex/skills

### 6.3 Harvest Integration

harvest-idea-seeds.sh already pulls from `~/.cursor/projects/*/agent-transcripts/*.jsonl`. Extend for $defer/$pending/$idea.

---

## 7. Factory Droid

### 7.1 Features

| Feature        | Factory Droid                  | Description                                              | thegent Parity              |
| -------------- | ------------------------------ | -------------------------------------------------------- | --------------------------- |
| **Droids**     | `.factory/droids/*.md`         | Markdown + frontmatter (name, description, tools, model) | DroidRunner already exists  |
| **droid exec** | `droid exec -f path.md`        | Runs droid via CLI                                       | thegent run -M droid:<name> |
| **Tools**      | tools: [Read, Grep, Glob, ...] | Per-droid tool access                                    | Frontmatter parsed          |
| **Model**      | model: inherit                 | Inherit or override                                      | DroidRunner supports        |

### 7.2 Droid Integration

**Current:** `DroidRunner` in `src/thegent/agents/droid.py` — runs `droid exec -f path.md` with prompt injection.

**Parity:** Droids are headless by design. Add:

- Queue: $defer/$block in prompt before droid exec
- Harvest: on droid exit, run harvest
- MCP: thegent_run can spawn droids via `thegent run -M droid:worker "prompt"`
- Agent teams: teammates can be droids (codex exec) or Factory droids (droid exec)

### 7.3 Droid ↔ Agent Mapping

| Droid                  | Equivalent Agent         |
| ---------------------- | ------------------------ |
| worker                 | thegent run codex/claude |
| orchestrator-core      | Lead in agent team       |
| agileplus-orchestrator | Specialized workflow     |

---

## 8. Augment Code

### 8.1 Features

| Feature                | Augment                     | Description                   | thegent Parity                     |
| ---------------------- | --------------------------- | ----------------------------- | ---------------------------------- |
| **auggie CLI**         | `auggie`                    | Terminal agent                | thegent run -M augment             |
| **Headless**           | `auggie --print "task"`     | Same as claude -p             | thegent run -M augment "prompt"    |
| **Context Engine**     | Live codebase understanding | Architecture, deps, history   | MCP: Context Engine MCP            |
| **Context Engine MCP** | MCP server                  | Expose context to tools       | thegent: add augment MCP to config |
| **Intent**             | Orchestration workspace     | Specs, worktrees, multi-agent | thegent team + Intent integration  |
| **IDE agents**         | VS Code, JetBrains          | Native IDE integration        | N/A (IDE-only)                     |
| **Code Review**        | PR review agent             | —                             | —                                  |

### 8.2 Augment Integration

**CLI:** `auggie --print "prompt"` for headless. thegent run -M augment wraps it.

**Context Engine MCP:** Add to ~/.cursor/mcp.json, ~/.codex/mcp.json so Claude Code, Codex, Cursor can use Augment's context.

**Rule sync:** Augment may have project config; include in unified rule sync.

---

## 9. Unified Agent Matrix

| Platform          | Interactive | Headless         | Rules         | Skills                | Hooks     | Teams             | thegent Entry                |
| ----------------- | ----------- | ---------------- | ------------- | --------------------- | --------- | ----------------- | ---------------------------- |
| **Claude Code**   | claude      | claude -p        | CLAUDE.md     | .claude/skills        | 15 events | Native            | thegent clode, run -M claude |
| **Codex**         | codex       | codex exec -     | .codex/skills | .codex/skills         | notify    | thegent team      | thegent codex, run -M codex  |
| **Cursor**        | Composer    | cursor-agent CLI | .cursor/rules | .cursor/skills-cursor | —         | —                 | run -M cursor-agent          |
| **Factory droid** | —           | droid exec       | —             | .factory/droids       | —         | droid as teammate | run -M droid:name            |
| **Augment**       | auggie      | auggie --print   | —             | —                     | —         | Intent            | run -M augment               |
| **OpenCode**      | oc          | oc               | .codex/skills | Zen (optional)        | —         | —                 | run -M opencode              |

---

## 10. Implementation Deep Dive

### 10.1 Prompt Flag Parsing

| Flag       | Action                                                | Exit         |
| ---------- | ----------------------------------------------------- | ------------ |
| `$defer`   | Strip, append to queue, return "Queued. N pending."   | 0            |
| `$pending` | Same as $defer                                        | 0            |
| `$block`   | Escalation add, return block message                  | 1            |
| `$idea`    | Save to idea-seeds (Claude) or harvest buffer (Codex) | 0 (continue) |

**Regex:** `\$defer|\$pending|\$block|\$idea` — case-sensitive or configurable.

### 10.2 Droid Tool Sets (Full)

| Value       | Tools                                                              |
| ----------- | ------------------------------------------------------------------ |
| `all`       | Read, Grep, Glob, Create, Edit, Execute, Todo, WebSearch, FetchUrl |
| `read-only` | Read, Grep, Glob                                                   |
| `write`     | Create, Edit                                                       |
| `execute`   | Execute                                                            |
| List        | Explicit subset                                                    |

### 10.3 Cursor Rules .mdc Frontmatter

```yaml
---
description: "Short rule picker text"
globs: "**/*.ts" | ["**/*.ts", "**/*.tsx"]
alwaysApply: false
---
```

**globs:** Omit for always-apply; string or array for file-specific.

### 10.4 Teammate Spawn Command

```bash
codex exec - --cd /path --model X --json --skip-git-repo-check
# stdin: task prompt from lead
```

**Lead:** `thegent codex` or `codex`; teammates: `codex exec -` with task prompt from MCP or file.

---

## 11. References

- [Claude Code hooks](https://code.claude.com/docs/en/hooks.md)
- [Claude Code agent teams](https://code.claude.com/docs/en/agent-teams.md)
- [Claude Code headless](https://code.claude.com/docs/en/headless.md)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents.md)
- [Augment Code](https://www.augmentcode.com), [Context Engine MCP](https://www.augmentcode.com/product/context-engine-mcp)
- [CODEX_HOOKS_AND_EXTENSION_OPTIONS.md](./CODEX_HOOKS_AND_EXTENSION_OPTIONS.md)
- [CODEX_DONUT_HARNESS_PLAN.md](../plans/CODEX_DONUT_HARNESS_PLAN.md)

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added feature comparison matrix
2. Added implementation priorities
3. Enhanced cross-references

### Cross-References Added

- MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md
- CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md

### Practical Additions

- Feature gap analysis
- Implementation roadmap

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [MULTI_PLATFORM_DEEP_DIVE.md](./MULTI_PLATFORM_DEEP_DIVE.md) - Platform deep dive
- [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) - Queue design
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
