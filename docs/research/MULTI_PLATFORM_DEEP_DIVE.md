<DONE>
# Multi-Platform Agent Deep Dive

**Purpose:** Extreme-depth reference for Claude Code, Codex, Cursor-agent, Factory droid, and Augment Code. Schemas, configs, transcript formats, hook payloads, and integration points.

**Companion:** [MULTI_PLATFORM_PARITY_MASTER_PLAN.md](../plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md), [CLAUDE_CODE_FEATURE_PARITY_AUDIT.md](./CLAUDE_CODE_FEATURE_PARITY_AUDIT.md), [CODEX_DONUT_HARNESS_PLAN.md](../plans/CODEX_DONUT_HARNESS_PLAN.md)

---

## Part I: Claude Code

### 1.1 Hook System (15 Events)

| Event                  | When                                | Blocking | Input Schema (key fields)                                                                      | Output / Decision                                              |
| ---------------------- | ----------------------------------- | -------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **SessionStart**       | New session, resume, clear, compact | No       | session_id, transcript_path, cwd, source (startup\|resume\|clear\|compact), model, agent_type? | additionalContext                                              |
| **UserPromptSubmit**   | Before prompt sent                  | Yes      | prompt, session_id, cwd                                                                        | decision: block, reason; additionalContext                     |
| **PreToolUse**         | Before tool call                    | Yes      | tool_name, tool_input, session_id                                                              | permissionDecision: allow\|deny\|ask, permissionDecisionReason |
| **PermissionRequest**  | Permission dialog                   | Yes      | tool_name, tool_input                                                                          | decision.behavior: allow\|deny                                 |
| **PostToolUse**        | After tool call                     | No       | tool_name, tool_input, result                                                                  | decision: block (rare)                                         |
| **PostToolUseFailure** | After tool fails                    | No       | tool_name, tool_input, error                                                                   | —                                                              |
| **Notification**       | Various                             | No       | notification type                                                                              | —                                                              |
| **SubagentStart**      | Subagent spawned                    | No       | agent_type (Bash, Explore, Plan, custom)                                                       | —                                                              |
| **SubagentStop**       | Subagent done                       | Yes      | agent_type                                                                                     | decision: block                                                |
| **Stop**               | Session ends                        | Yes      | session_id, cwd                                                                                | decision: block (force continue)                               |
| **TeammateIdle**       | Teammate about idle                 | Yes      | teammate_id                                                                                    | exit 2 → feedback, keep working                                |
| **TaskCompleted**      | Task marked done                    | Yes      | task_id                                                                                        | exit 2 → block, send feedback                                  |
| **PreCompact**         | Before compaction                   | No       | trigger: manual\|auto                                                                          | —                                                              |
| **SessionEnd**         | Session terminates                  | No       | reason: clear\|logout\|prompt_input_exit\|...                                                  | —                                                              |

**Matcher patterns:** PreToolUse/PostToolUse match on `tool_name` (regex: `Bash`, `Edit|Write`, `mcp__.*`). UserPromptSubmit, Stop, TeammateIdle, TaskCompleted have no matcher.

**Hook config locations:** ~/.claude/settings.json, .claude/settings.json, .claude/settings.local.json, plugin hooks/hooks.json, skill/agent frontmatter.

### 1.2 Agent SDK (Headless)

```bash
claude -p "prompt" [--continue] [--resume SESSION_ID] [--output-format json|stream-json|text] [--allowedTools "Bash,Read,Edit"] [--append-system-prompt "..."] [--json-schema '...']
```

**Continue:** `--continue` uses most recent session; `--resume SESSION_ID` uses specific session.

**Structured output:** `--output-format json` returns `{result, session_id, ...}`; `--json-schema` returns `structured_output` field.

### 1.3 Subagents

- **Task tool:** Spawns helper; reports back to main agent.
- **Locations:** `.cursor/agents/` (project), `~/.cursor/agents/` (user).
- **Format:** `.md` with frontmatter: name, description. Body = system prompt.
- **Skills frontmatter:** `skills:` for auto-load; `agent:` for agent type.

### 1.4 Agent Teams

- **Config:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **Storage:** `~/.claude/teams/{team-name}/config.json`, `~/.claude/tasks/{team-name}/`
- **Display:** in-process (Shift+Up/Down) or split panes (tmux/iTerm2)
- **TeammateIdle:** Exit 2 → feedback, teammate continues
- **TaskCompleted:** Exit 2 → block completion, send feedback

---

## Part II: Codex

### 2.1 Config (config.toml)

**Locations:** `~/.codex/config.toml`, `.codex/config.toml` (project, trusted only).

**Key keys:**

```toml
notify = ["cmd", "arg1"]           # Receives JSON as last argv
model_instructions_file = "path"  # Override AGENTS.md
developer_instructions = "..."    # Injected instructions
project_root_markers = ["..."]     # Project root detection
project_doc_max_bytes = 50000     # AGENTS.md limit
skills.config = [{path="...", enabled=true}]
mcp_servers = [{command="...", args=[...], url="...", enabled_tools=[...]}]
web_search = "disabled"|"cached"|"live"
sandbox_mode = "workspace-write"|"danger-full-access"|...
personality = "none"|"friendly"|"pragmatic"
history.persistence = "save-all"|"none"
tui.notifications = true|[...]
```

**Notify payload (AfterAgent):**

```json
{
  "type": "agent-turn-complete",
  "thread-id": "uuid",
  "turn-id": "turn-1",
  "cwd": "/path",
  "input-messages": ["..."],
  "last-assistant-message": "..."
}
```

### 2.2 Skills

**Location:** `.codex/skills/{skill-name}/SKILL.md`

**Config override:** `skills.config` in config.toml: `{path=".codex/skills/name", enabled=true}`

### 2.3 Exec Flow

```bash
codex exec - [--model X] [--cd PATH] [--json] [--skip-git-repo-check] [--full-auto] [--sandbox workspace-write]
```

- **Stdin:** Prompt (or combined droid+prompt for CodexRunner)
- **Stdout:** Streamed response; `--json` for JSONL events

### 2.4 State & History

- **Threads:** `~/.codex/state_5.sqlite` — `threads` table: id, cwd
- **History:** `~/.codex/history.jsonl` — `text` field for harvest
- **Session end:** `session_log::log_session_end()` — no hook

---

## Part III: Cursor-Agent

### 3.1 Rules (.cursor/rules/\*.mdc)

**Format:**

```yaml
---
description: Brief description (rule picker)
globs: "**/*.ts" # File pattern; omit for always-apply
alwaysApply: false # true = every session
---
# Rule content (markdown)
```

**Best practices:** Under 50 lines, one concern per rule, concrete examples.

### 3.2 .cursorrules (Legacy)

Project root; plain text or markdown. Being superseded by .cursor/rules/.

### 3.3 Subagents (.cursor/agents/)

**Format:** `.md` with frontmatter:

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
---
# System prompt body
```

**Priority:** `.cursor/agents/` (project) over `~/.cursor/agents/` (user).

### 3.4 Skills (.cursor/skills-cursor/)

**Structure:** `{skill-name}/SKILL.md` — similar to Claude Code skills. Slash commands.

### 3.5 Transcript Format (Harvest)

**Path:** `~/.cursor/projects/Users-{user}-{path-slug}/agent-transcripts/{session-id}.jsonl`

**Line format:**

```json
{
  "role": "user",
  "message": {
    "content": [{ "type": "text", "text": "prompt with $idea or $defer" }]
  }
}
```

**Harvest logic:** Filter `role==user`, extract `message.content[].text`, check for $idea/$defer/$pending.

**Project path resolution:** Folder name = path segments joined by `-`; or grep agent-tools/agent-transcripts for workspace path.

### 3.6 Modes

- **Plan:** `/plan` — design before impl
- **Agent:** Interactive, default
- **Background agent:** Isolated VM, separate branch, can open PR

---

## Part IV: Factory Droid

### 4.1 Droid Format (.factory/droids/\*.md)

**Frontmatter:**

```yaml
---
name: worker
description: General-purpose worker for delegating tasks
tools: [Read, Grep, Glob, Create, Edit, Execute, Todo, WebSearch, FetchUrl]
# or tools: all | read-only | write | execute
version: v1
model: inherit # or specific model
---
# System prompt body
```

**Tools values:** `all`, `read-only`, `write`, `execute`, or list: Read, Grep, Glob, Create, Edit, Execute, Todo, WebSearch, FetchUrl.

### 4.2 droid exec

```bash
droid exec -f path/to/droid.md [--model X] [--cwd PATH] [--output-format stream-json] [--auto low|high]
```

**Prompt injection:** DroidRunner concatenates `droid_content + "\n\n---\nUser request: " + prompt` to temp file.

### 4.3 DroidRunner (thegent)

**Cmd:** `[droid, exec, -f, tmp_path, --model, model, --cwd, cwd, --output-format, stream-json, --auto, low|high]`

**Mode mapping:** `write` → `--auto low`; `full` → `--auto high`

**Resolve:** `~/.local/bin/droid`, `~/.factory/bin/droid`

### 4.4 CodexRunner (Droid Backend)

Uses `codex exec -` with combined droid+prompt on stdin. `--cd`, `--json`, `--sandbox workspace-write`, `--full-auto`.

### 4.5 Factory Hooks

**Config:** `.factory/hooks/hooks.json` — can import Claude hooks.

**Hook events (Factory/droid):** PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, SessionEnd, Stop, SubagentStop, Notification, PreCompact.

**Hook script pattern:** Python or shell; stdin = JSON; block via `{"decision":"block","reason":"..."}` or exit 2.

---

## Part V: Augment Code

### 5.1 auggie CLI

```bash
auggie                    # Interactive
auggie --print "task"     # Headless (same as claude -p)
```

### 5.2 Context Engine

- Live codebase understanding: architecture, deps, history
- Powers IDE agents, CLI, Code Review

### 5.3 Context Engine MCP

- MCP server exposing context to tools
- Add to ~/.cursor/mcp.json, ~/.codex/mcp.json for cross-platform use

### 5.4 Intent

- Orchestration workspace: specs, worktrees, multi-agent
- Parallel agents without conflicts
- Comparable to thegent team + git worktrees

### 5.5 Products

- **Agent:** IDE agents (VS Code, JetBrains)
- **Next Edit:** Step-by-step guidance
- **Code Completions:** Inline suggestions
- **Code Review:** PR review agent
- **Slack:** Delegate from Slack
- **Remote Agents:** Cloud execution

---

## Part VI: Harvest Integration

### 6.1 Claude History

**Path:** `~/.claude/history.jsonl`

**Line format:** `{display, project, timestamp, sessionId}` — `display` has prompt text.

**Offset:** `~/.claude/.idea-harvest-claude-offset` — line number.

### 6.2 Codex History

**Path:** `~/.codex/history.jsonl`

**Line format:** `{text, ...}` — `text` has prompt/response.

**CWD resolution:** `state_5.sqlite` threads table: `SELECT cwd FROM threads WHERE id=?`

**Offset:** `~/.claude/.idea-harvest-codex-offset`

### 6.3 Cursor Transcripts

**Path:** `~/.cursor/projects/Users-*/agent-transcripts/*.jsonl`

**Line format:** `{role, message: {content: [{type, text}]}}` — role=user, extract text.

**Offset:** `~/.claude/.idea-harvest-cursor-done` — `file:line_num` per transcript.

### 6.4 Output

- **$idea:** `docs/research/idea-seeds/seed_{source}_{ts}_{id}.md`
- **$defer/$pending:** Append to `docs/research/pending-handoff.md` (or `~/.claude/pending-handoff.md`)

---

## Part VII: Unified Rules Sync (Design)

### 7.1 Canonical Source

**Option A:** `.cursor/rules/` as source (Cursor-native)
**Option B:** `.thegent/rules/` as source (thegent-owned)
**Option C:** `docs/reference/agent-rules/` (docs-first)

### 7.2 Mapping

| Source      | Claude Code                | Codex                         | Cursor                   |
| ----------- | -------------------------- | ----------------------------- | ------------------------ |
| Rule .mdc   | CLAUDE.md section or skill | .codex/skills/{name}/SKILL.md | .cursor/rules/{name}.mdc |
| alwaysApply | Injected at SessionStart   | model_instructions or skill   | alwaysApply: true        |
| globs       | N/A (no file-scoped)       | N/A                           | globs field              |

### 7.3 Sync Algorithm

1. Read canonical rules
2. For each rule: emit .mdc (Cursor), append to CLAUDE.md or create skill (Claude/Codex)
3. Handle conflicts: last-write-wins or merge strategy

---

## Part VIII: Queue & Escalation

### 8.1 Queue Schema (.thegent/prompt_queue.jsonl)

```json
{
  "ts": "2025-02-15T12:00:00Z",
  "prompt": "...",
  "project": "/path",
  "claimed_by": null,
  "lease_expires_at": null
}
```

### 8.2 Escalation ($block)

`thegent govern escalate add RUN_ID "reason" --sla-minutes=60`

Resolve: `thegent govern escalate resolve RUN_ID`

### 8.3 Handoff Output

`docs/research/pending-handoff.md` or `.thegent/next-session-prompts.md`

---

## Part IX: MCP Tool Registry (thegent)

**Queue:** thegent_queue_list, thegent_queue_claim, thegent_queue_done, thegent_queue_add, thegent_queue_edit, thegent_queue_release, thegent_queue_extend_lease

**Team:** thegent_team_create, thegent_team_task_list, thegent_team_task_assign, thegent_team_task_claim, thegent_team_task_done, thegent_team_message, thegent_team_broadcast, thegent_team_shutdown

**Run:** thegent_run, thegent_bg, thegent_do_next

---

## Part X: Cross-Platform Invocation Matrix

| Platform      | Interactive | Headless       | thegent run         |
| ------------- | ----------- | -------------- | ------------------- |
| Claude Code   | claude      | claude -p      | run -M claude       |
| Codex         | codex       | codex exec -   | run -M codex        |
| Cursor        | Composer    | cursor-agent   | run -M cursor-agent |
| Factory droid | —           | droid exec     | run -M droid:name   |
| Augment       | auggie      | auggie --print | run -M augment      |

---

## Part XI: Factory Hooks (Deep Dive)

### 11.1 Hook Categories

**Security:** prevent-hardcoded-secrets.py, prevent-force-push.py
**Quality:** (imported from Claude hooks)
**Global:** session-welcome.sh, session-summary.sh, inject-git-context.sh

### 11.2 Hook Config (hooks.json)

Factory can import Claude hooks: `claudeHooksImported: true`, `importedClaudeHooks: ["$HOME/.claude/hooks/..."]`

### 11.3 Hook Input (PreToolUse)

```json
{
  "tool_name": "Write",
  "tool_input": { "file_path": "...", "content": "..." },
  "session_id": "...",
  "cwd": "...",
  "hook_event_name": "PreToolUse"
}
```

### 11.4 Block Pattern

```python
output = {"decision": "block", "reason": "..."}
# or
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "...",
    }
}
print(json.dumps(output))
sys.exit(0)  # or exit 2 for simple block
```

---

## Part XII: Cursor Skills (Deep Dive)

### 12.1 Skill Structure

```
.cursor/skills-cursor/{skill-name}/
  SKILL.md    # Main content + frontmatter
```

### 12.2 create-rule Skill

Frontmatter: name, description. Guides creation of .cursor/rules/\*.mdc with description, globs, alwaysApply.

### 12.3 create-subagent Skill

Frontmatter: name, description, disable-model-invocation. Guides creation of .cursor/agents/_.md or ~/.cursor/agents/_.md.

### 12.4 AGENTS.md

Project root; agent instructions. Cross-referenced by CLAUDE.md, Cursor, Factory.

---

## Part XIII: Codex Config (Extended)

### 13.1 notify Array

```toml
notify = ["thegent", "codex-notify"]
# or ["notify-send", "Codex"] for desktop notifications
```

Command receives JSON as last argv. Fire-and-forget (async spawn).

### 13.2 MCP Server Config

```toml
[mcp_servers.thegent]
command = "thegent"
args = ["serve", "--stdio"]
# or
url = "http://localhost:3847/sse"
```

### 13.3 skills.config

```toml
[[skills.config]]
path = ".codex/skills/thegent-queue"
enabled = true
```

---

## Part XIV: thegent Agent Registry

**Direct agents:** cursor, claude, codex, gemini, copilot — via CLI (cursor-agent, claude, codex exec, etc.)

**Proxy agents:** antigravity, minimax, glm, cliproxy, kilo — via CodexProxyRunner (codex exec → CLIProxyAPIPlus)

**Droid backends:** droid (Factory), codex (CodexRunner), custom (CustomCliRunner)

**Discovery:** `_is_triggered_by_agent_process()` checks parent for cursor-agent, claude-code, codex.

---

## Part XV: MCP Tool Parameters (Full)

### 15.1 Queue Tools

| Tool                       | Params             | Returns |
| -------------------------- | ------------------ | ------- |
| thegent_queue_list         | project?, limit?   | items[] |
| thegent_queue_claim        | id, lease_minutes? | item    |
| thegent_queue_done         | id                 | ok      |
| thegent_queue_add          | prompt, project?   | id      |
| thegent_queue_edit         | id, prompt         | ok      |
| thegent_queue_release      | id                 | ok      |
| thegent_queue_extend_lease | id, minutes        | ok      |

### 15.2 Team Tools

| Tool                     | Params               | Returns |
| ------------------------ | -------------------- | ------- |
| thegent_team_create      | name, teammates[]    | team_id |
| thegent_team_task_list   | team_id              | tasks[] |
| thegent_team_task_assign | team_id, task        | task_id |
| thegent_team_task_claim  | team_id, task_id     | ok      |
| thegent_team_task_done   | team_id, task_id     | ok      |
| thegent_team_message     | team_id, to, message | ok      |
| thegent_team_broadcast   | team_id, message     | ok      |
| thegent_team_shutdown    | team_id              | ok      |

### 15.3 Run Tools

| Tool            | Params                | Returns                     |
| --------------- | --------------------- | --------------------------- |
| thegent_run     | prompt, mode?, model? | run_id, output              |
| thegent_bg      | prompt, mode?         | run_id                      |
| thegent_do_next | —                     | run_id, output (from queue) |

---

## Part XVI: Claude Code Hook Payload Examples

### 16.1 UserPromptSubmit (block)

**Input:** `{prompt: "...", session_id: "...", cwd: "/path"}`

**Block output:** `{"decision": "block", "reason": "Contains $block; escalated."}`

### 16.2 PreToolUse (deny)

**Input:** `{tool_name: "Bash", tool_input: {command: "rm -rf /"}, session_id: "..."}`

**Output:** `{"permissionDecision": "deny", "permissionDecisionReason": "Dangerous command"}`

### 16.3 TeammateIdle (feedback)

**Input:** `{teammate_id: "t1", task_id: "task-1", ...}`

**Output (exit 2):** `{"feedback": "Check tests before marking done"}`

---

## Part XVII: Run Registry & Telemetry

### 17.1 run_registry.jsonl

**Path:** `.thegent/sessions/run_registry.jsonl`

**Line format:** `{run_id, mode, model, cwd, started_at, ended_at?, status, agent_type?}`

### 17.2 contract_telemetry.jsonl

**Path:** `.thegent/sessions/contract_telemetry.jsonl`

**Line format:** `{run_id, contract_id, verdict, timestamp}`

### 17.3 escalation_queue.jsonl

**Path:** `.thegent/sessions/escalation_queue.jsonl`

**Line format:** `{run_id, reason, sla_minutes, created_at, resolved_at?}`

---

## Part XVIII: Augment CLI (Extended)

```bash
auggie                           # Interactive TUI
auggie --print "task"            # Headless, returns output
auggie --help                    # Full flags
```

**Context Engine:** Indexes repo; MCP exposes `augment_context_search`, `augment_get_architecture`, etc.

**Intent:** `intent start`, `intent add-agent`, `intent run` — multi-agent orchestration.

---

## Part XIX: Droid Backend Resolution

| Backend | Resolve order                                  | Fallback |
| ------- | ---------------------------------------------- | -------- |
| droid   | ~/.local/bin/droid, ~/.factory/bin/droid, PATH | —        |
| codex   | PATH codex                                     | —        |
| custom  | CLI from droid frontmatter `cli:`              | —        |

**CodexRunner stdin:** `{droid_content}\n\n---\nUser request: {prompt}`

---

## Part XX: Harvest Line Formats (Exact)

### Claude history.jsonl

```json
{
  "display": "prompt text",
  "project": "/path",
  "timestamp": "ISO8601",
  "sessionId": "uuid"
}
```

### Codex history.jsonl

```json
{
  "text": "prompt or response",
  "role": "user|assistant",
  "thread_id": "uuid",
  "turn_id": "...",
  "timestamp": "..."
}
```

### Cursor transcript (per line)

```json
{
  "role": "user",
  "message": { "content": [{ "type": "text", "text": "prompt" }] },
  "timestamp": "..."
}
```

---

## Part XXI: Error Handling & Edge Cases

### 21.1 Queue

- **Corruption:** Append-only; on read error, truncate to last valid line, log.
- **Concurrent claim:** Atomic rename or lock file; `claimed_by` + `lease_expires_at`; extend_lease before expiry.
- **Empty project:** Fallback to `~/.thegent/prompt_queue.jsonl`.

### 21.2 Harvest

- **Missing offset file:** Start from line 0.
- **Cursor project path:** Folder name may not map 1:1 to path; use `workspace_path` from transcript metadata if present.
- **Large history:** Stream; don't load full file.

### 21.3 codex-notify

- **Invalid JSON:** Log, exit 0 (don't fail Codex).
- **Missing type:** Ignore; only process `agent-turn-complete`.

### 21.4 Rules Sync

- **Conflict:** Last-write-wins; or merge strategy (configurable).
- **Missing target dir:** Create `.cursor/rules`, `.codex/skills` as needed.

---

## Part XXII: Migration Paths

### 22.1 Queue Migration (.claude → .thegent)

1. If `PROJECT/.claude/pending-queue.jsonl` exists and `PROJECT/.thegent/prompt_queue.jsonl` empty: copy lines, clear source.
2. If `~/.claude/pending-queue.jsonl` exists and `~/.thegent/prompt_queue.jsonl` empty: same.
3. Update prompt-submit-guard, harvest-pending-queue to use `.thegent/prompt_queue.jsonl`.

### 22.2 Config Merge (Codex notify)

```python
# Pseudocode
config = read_toml("~/.codex/config.toml")
if "notify" not in config or "thegent" not in str(config.get("notify", [])):
    config.setdefault("notify", []).append("thegent")
    config.setdefault("notify", []).append("codex-notify")
    write_toml(config)
```

### 22.3 Backward Compatibility

- **prompt-submit-guard:** Read from both `.claude/pending-queue.jsonl` and `.thegent/prompt_queue.jsonl` during transition; write only to `.thegent`.
- **harvest:** Same dual-read during migration window.

---

## Part XXIII: Codex Source Locations (Exact)

| Symbol                       | File                                | Approx Line |
| ---------------------------- | ----------------------------------- | ----------- |
| notify_hook spawn            | codex-rs/core/src/codex.rs          | ~4536       |
| AgentTurnComplete struct     | codex-rs/core/src/                  | —           |
| after_tool_use (empty)       | codex-rs/core/src/tools/registry.rs | ~347        |
| session_log::log_session_end | codex-rs/tui/src/lib.rs             | —           |
| config.toml parse            | codex-rs/core/src/config/           | —           |
| exec stdin read              | codex-rs/cli/ or exec path          | —           |

---

## Part XXIV: thegent run Dispatch (Full)

```
run -M claude     → direct_agents.run_claude() or claude -p
run -M codex      → codex_proxy.run_codex_exec()
run -M cursor-agent → direct_agents.run_cursor_agent()
run -M droid:name → DroidRunner(droid_path).run()
run -M augment    → direct_agents.run_augment() or auggie --print
run -M cliproxy   → CodexProxyRunner (codex exec → CLIProxyAPIPlus)
```

**Registry:** `src/thegent/agents/registry.py` — `AGENT_REGISTRY`, `get_runner(mode)`.

---

## Part XXV: MCP Architecture & Infrastructure (Deep Dive)

### 25.1 Model Context Protocol (MCP) Overview

**MCP** = protocol for AI clients to discover and invoke tools, resources, and prompts from servers. JSON-RPC 2.0 over STDIO or HTTP.

**thegent:** FastMCP server (`src/thegent/mcp_server.py`) — 30+ tools, 20+ resources, 6+ prompts. Transports: STDIO (Claude Code), Streamable HTTP (Cursor, Codex, remote).

### 25.2 Transport Stack

| Transport           | Spec   | Use Case              | Config                                                                    |
| ------------------- | ------ | --------------------- | ------------------------------------------------------------------------- |
| **STDIO**           | Core   | Local, single-process | `thegent mcp-stdio` or `python -m thegent.main mcp-stdio`                 |
| **Streamable HTTP** | Core   | Remote, multi-client  | `thegent serve` → uvicorn on `mcp_host:mcp_port` (default 127.0.0.1:3847) |
| **SSE**             | Legacy | Long-polling          | EventStore + `Last-Event-ID` for reconnect                                |

### 25.3 EventStore & Session State

- **Default:** In-memory (`EventStore()`)
- **Distributed:** `FASTMCP_EVENT_STORE_URL` → Redis URL for multi-worker, horizontal scaling
- **Session TTL:** 1 day; keyed by `mcp-session-id`
- **Stateless HTTP:** `stateless_http=True` — per-request JSON-RPC, no persistent session (CI, verification)

### 25.4 Lifespan (Startup/Shutdown)

```
Startup:
  1. validate_setup()
  2. Optional: mount flyto-core or @playwright/mcp at namespace "browser"
  3. Optional: prewarm catalog + git index (parallel)
  4. Optional: THGENT_BUNDLE_PROXY=1 → start CLIProxyAPIPlus

Shutdown:
  1. shutdown_wait_s (drain in-flight)
  2. shutdown_wait_active_s (poll ps_impl until no running sessions or timeout)
  3. Terminate bundled proxy if started
```

### 25.5 HTTP Endpoints

| Path      | Method | Purpose                        |
| --------- | ------ | ------------------------------ |
| `/health` | GET    | Health check; no auth          |
| `/mcp`    | POST   | MCP JSON-RPC (Streamable HTTP) |

---

## Part XXVI: Full MCP Tool Registry

### 26.1 Execution & Orchestration

| Tool                  | Params                                                                                                    | Annotations                                | Purpose                               |
| --------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------- |
| thegent_run           | prompt, agent?, model?, cd?, mode, timeout, full, include_contract, confidence, arbitration               | readOnly: F, destructive: F, idempotent: F | Sync agent run; blocks until complete |
| thegent_bg            | agent, prompt, cd?, mode, timeout, owner?, model?, provider?, routing?, failover, confidence, arbitration | same                                       | Fire-and-forget; returns session_id   |
| thegent_loop          | prompt, todo_spec, agent?, checker, mode, cd?                                                             | same                                       | Lifecycle loop with Checker oversight |
| thegent_loop_takeover | session_id, prompt                                                                                        | same                                       | Inject human input into running loop  |
| thegent_loop_stop     | session_id                                                                                                | same                                       | Send STOP signal to loop              |
| thegent_stop          | session_id, force?                                                                                        | destructive: T                             | Stop background session               |
| thegent_wait          | session_id, timeout?                                                                                      | readOnly: T                                | Block until session completes         |
| thegent_do_next       | cd?, limit                                                                                                | readOnly: T                                | Find next actionable work items       |

### 26.2 Discovery & Status

| Tool                        | Params                                                 | Purpose                              |
| --------------------------- | ------------------------------------------------------ | ------------------------------------ |
| thegent_ps                  | owner?, all?, include_contract?                        | List background sessions             |
| thegent_status              | session_id, include_contract?                          | Session status                       |
| thegent_logs                | session_id, tail?, stderr?                             | Read session logs                    |
| thegent_inspect             | session_ids?, owner?, tail, stderr?, include_contract? | Multi-session status + logs          |
| thegent_list_agents         | —                                                      | List available agents                |
| thegent_list_droids         | cd?                                                    | List available droids                |
| thegent_list_models         | provider?, include_contract?, by_model?                | List models (optionally by provider) |
| thegent_resolve_model_route | model, provider?, policy                               | Resolve model to routing target      |

### 26.3 Contract & Governance

| Tool                                   | Params                                                                                                     | Purpose                       |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------- |
| thegent_negotiate_contract             | contract_id, supported_versions                                                                            | Version negotiation (WP-7001) |
| thegent_session_contracts              | owner?, all?, missing_only?, summary_only?, strict?                                                        | Contract audit                |
| thegent_session_contract_health_gate   | owner?, all?, strict?, min_healthy_ratio?, policy_profile?, no_worse_than_baseline?, regression_tolerance? | Health gate for CI            |
| thegent_session_contract_health_report | owner?, all?, strict?, top_blocked?, policy_profile?, no_worse_than_baseline?, regression_tolerance?       | Health report with taxonomy   |
| thegent_session_contract_health_trend  | payload_type?, owner?, all?, strict?, policy_profile?, min_healthy_ratio?, top_blocked?, limit?            | Trend snapshots               |

### 26.4 Observability & Inbox

| Tool                    | Params                                                                                                           | Purpose                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------- |
| thegent_observe_summary | limit?, drift_window?, structural_budget_pct?, semantic_budget_pct?, provider?, trend_samples?, top_escalations? | KPIs, drift, escalations  |
| thegent_inbox_list      | owner?, agent?, event_type?, status?, sources?, limit?                                                           | List inbox events         |
| thegent_inbox_wait      | owner?, agent?, event_type?, status?, sources?, poll_interval?, timeout?                                         | Wait for next inbox event |

### 26.5 Planning & Workflow

| Tool                    | Params     | Purpose                                                                      |
| ----------------------- | ---------- | ---------------------------------------------------------------------------- |
| thegent_dag_list        | cd?        | List DAG tasks from .factory/dag-session.md                                  |
| thegent_list_operations | operation? | Universal operation taxonomy                                                 |
| thegent_list_modes      | mode?      | Orchestration modes (sequential_delegation, parallel_consensus, review_loop) |

### 26.6 Terminal & Sitback

| Tool                        | Params                | Purpose                        |
| --------------------------- | --------------------- | ------------------------------ |
| thegent_terminal_list       | all?                  | List tmux panes                |
| thegent_terminal_inspect    | pane_id, last_lines?  | Capture pane content           |
| thegent_terminal_send       | pane_id, text, enter? | Send text to pane              |
| thegent_terminal_attach     | pane_id               | Get tmux attach command        |
| thegent_heliosShield_status | —                     | heliosShield harness status    |
| thegent_sitback_dashboard   | —                     | Sitback dashboard (cached 30s) |

### 26.7 Research & Sampling

| Tool                   | Params              | Purpose                        |
| ---------------------- | ------------------- | ------------------------------ |
| thegent_ddg_search     | query, num_results? | DuckDuckGo search              |
| thegent_suggest_prompt | raw_prompt          | Refine prompt via ctx.sample() |

---

## Part XXVII: MCP Resources & Prompts

### 27.1 Resources (URI-addressable)

| URI                                 | Params                                                                                                           | MIME             | Purpose                          |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------- | -------------------------------- |
| thegent://sessions                  | include_contract?                                                                                                | application/json | List sessions                    |
| thegent://session/{id}/meta         | include_contract?                                                                                                | application/json | Session metadata                 |
| thegent://session/{id}/logs         | stderr?, tail?                                                                                                   | text/plain       | Session logs                     |
| thegent://dag                       | —                                                                                                                | application/json | DAG from .factory/dag-session.md |
| thegent://agents                    | —                                                                                                                | application/json | List agents                      |
| thegent://models                    | provider?, include_contract?                                                                                     | application/json | List models                      |
| thegent://models/contract           | —                                                                                                                | application/json | Model routing contract schema    |
| thegent://sessions/contracts        | owner?, all?, missing_only?, summary_only?, strict?                                                              | application/json | Contract audit                   |
| thegent://sessions/contracts/health | owner?, all?, strict?, min_healthy_ratio?, policy_profile?, no_worse_than_baseline?, regression_tolerance?       | application/json | Health gate                      |
| thegent://sessions/contracts/report | owner?, all?, strict?, top_blocked?, policy_profile?, no_worse_than_baseline?, regression_tolerance?             | application/json | Health report                    |
| thegent://sessions/contracts/trend  | payload_type?, owner?, all?, strict?, policy_profile?, min_healthy_ratio?, top_blocked?, limit?                  | application/json | Health trend                     |
| thegent://observe/summary           | limit?, drift_window?, structural_budget_pct?, semantic_budget_pct?, provider?, trend_samples?, top_escalations? | application/json | Observe summary                  |
| thegent://meta                      | —                                                                                                                | application/json | Server metadata                  |
| thegent://operations                | operation?                                                                                                       | application/json | Operation taxonomy               |
| thegent://modes                     | mode?                                                                                                            | application/json | Orchestration modes              |
| thegent://workflow/triggers         | —                                                                                                                | text/markdown    | Workflow instructions            |
| thegent://workflow/gardening        | —                                                                                                                | text/markdown    | Gardening workflow               |

### 27.2 Prompts (Template-based)

| Prompt                         | Params                   | Purpose                         |
| ------------------------------ | ------------------------ | ------------------------------- |
| thegent_workflow_idea          | idea                     | Idea/task workflow instructions |
| thegent_workflow_quality_green | —                        | Quality pipeline instructions   |
| thegent_workflow_next_item     | —                        | Next work item instructions     |
| thegent_workflow_gardening     | —                        | Gardening workflow              |
| thegent_run_agent              | agent, prompt, cd?, mode | Generate run prompt             |
| thegent_create_wbs             | feature, scope?          | WBS creation prompt             |
| thegent_bg_task                | agent, prompt, owner?    | Background task prompt          |

### 27.3 Transforms

- **ResourcesAsTools:** Exposes all resources as tools for tool-only clients
- **PromptsAsTools:** Exposes all prompts as tools for tool-only clients

---

## Part XXVIII: Middleware & Transport Stack

### 28.1 Middleware Order (outermost → innermost)

1. **ErrorHandlingMiddleware** — Centralized error handling
2. **RateLimitingMiddleware** — 10 req/s, burst 20
3. **TimingMiddleware** — Execution duration
4. **ResponseCachingMiddleware** — TTL 30s for: thegent_ps, thegent_list_agents, thegent_list_droids, thegent_list_models, thegent_session_contract_health_trend, thegent_sitback_dashboard
5. **ResponseLimitingMiddleware** — Max 500KB response
6. **LoggingMiddleware** — Request/response logging
7. **BearerAuthMiddleware** (HTTP only) — G-FM-01: Bearer token when mcp_auth_mode=bearer

### 28.2 Auth

| Mode   | Config                                                  | Behavior                                        |
| ------ | ------------------------------------------------------- | ----------------------------------------------- |
| none   | mcp_auth_mode=none                                      | No auth                                         |
| bearer | mcp_auth_mode=bearer, mcp_bearer_tokens=comma-separated | `Authorization: Bearer <token>`; /health exempt |

### 28.3 Context Injection

- **meta.cwd** — Client sends in request meta; `get_default_cwd()` injects into tools
- **meta.owner** — Client sends owner tag; `get_default_owner()` injects
- **ctx.elicit()** — Request cwd/owner when ambiguous (ELICIT_CWD_MSG, ELICIT_OWNER_MSG)

---

## Part XXIX: Client Config & Install Paths

### 29.1 MCP Client Config Paths

| Client         | Path(s)                                                         |
| -------------- | --------------------------------------------------------------- |
| Cursor         | ~/.cursor/mcp.json, .cursor/mcp.json (workspace)                |
| Claude Code    | ~/.claude.json                                                  |
| Codex          | ~/.codex/mcp.json, ~/.config/codex/mcp.json                     |
| Claude Desktop | ~/Library/Application Support/Claude/claude_desktop_config.json |
| Droid          | .factory/mcp.json (project)                                     |

### 29.2 Install Modes

| Client                               | Transport | Config Entry                                                                          |
| ------------------------------------ | --------- | ------------------------------------------------------------------------------------- |
| Claude Code                          | STDIO     | `command: python`, `args: ["-m", "thegent.main", "mcp-stdio"]`, `cwd: <project_root>` |
| Cursor, Codex, Claude Desktop, Droid | HTTP      | `url: http://host:port/mcp`, `transport: http`                                        |

### 29.3 Config Keys

```json
{
  "mcpServers": {
    "thegent": {
      "url": "http://127.0.0.1:3847/mcp",
      "transport": "http",
      "description": "Thegent agent orchestration (run, bg, ps, logs, dag, etc.)"
    }
  }
}
```

---

## Part XXX: FastMCP Features & MCP Spec Alignment

### 30.1 FastMCP Feature Matrix

| Feature              | FastMCP | MCP/SEP  | thegent                                       |
| -------------------- | ------- | -------- | --------------------------------------------- |
| Tools                | ✓       | Core     | 30+                                           |
| Resources            | ✓       | Core     | 20+                                           |
| Prompts              | ✓       | Core     | 7                                             |
| Elicitation          | ✓       | SEP-1330 | cwd/owner in run, bg, dag_list                |
| Progress             | ✓       | Core     | thegent_run every 10s                         |
| Sampling             | ✓       | SEP-1577 | thegent_suggest_prompt                        |
| Background Tasks     | ✓       | SEP-1686 | TaskConfig(mode=optional) on run              |
| Notifications        | ✓       | Core     | tools/list_changed (not yet used)             |
| SSE Polling          | ✓       | SEP-1699 | ctx.close_sse_stream() every 30s in long runs |
| Bearer Auth          | ✓       | —        | G-FM-01                                       |
| Dependency Injection | ✓       | —        | Depends(get_default_cwd), CurrentContext      |

### 30.2 Client Verification (Elicitation, Progress, Sampling)

| Client      | Elicitation | Progress | Sampling |
| ----------- | ----------- | -------- | -------- |
| Claude Code | ?           | ?        | ?        |
| Cursor      | ?           | ?        | ?        |
| Codex       | ?           | ?        | ?        |

**Workaround:** Queue/blocking uses hooks, not MCP elicitation.

---

## Part XXXI: External Tooling & Bundles

### 31.1 Browser Tools (Optional Mount)

| Provider        | Config                                 | URL/Command                   | Namespace |
| --------------- | -------------------------------------- | ----------------------------- | --------- |
| flyto-core      | mcp_mount_flyto=True, THGENT_FLYTO_URL | http://localhost:8333/mcp     | browser   |
| @playwright/mcp | mcp_mount_playwright=True              | npx -y @playwright/mcp@latest | browser   |

**Mutually exclusive:** Only one browser provider at a time.

### 31.2 Bundled Proxy

- **THGENT_BUNDLE_PROXY=1** — Start CLIProxyAPIPlus on lifespan; stop on shutdown
- **Purpose:** Antigravity, Kilo, NIM, etc. — free model routing
- **cliproxy_manager.start_proxy_managed()**

### 31.3 Prewarm (Lifespan)

- **prewarm_catalog** — Model catalog, routes
- **prewarm_git_index** — Git index for common commands
- **Parallel:** asyncio.to_thread for both

### 31.4 Tool Icons (G-FM-04)

| Tool                      | Icon     |
| ------------------------- | -------- |
| thegent_run               | ▶       |
| thegent_bg                | ⏸       |
| thegent_stop              | ⏹       |
| thegent_logs              | ▤        |
| thegent_ps                | ≡        |
| thegent_status            | ℹ       |
| thegent_wait              | ⏳       |
| thegent_inbox_list        | ↓        |
| thegent_inbox_wait        | 📬       |
| thegent_inspect           | ⌕        |
| thegent_list_agents       | ⊕        |
| thegent_list_droids       | ◉        |
| thegent_list_models       | ⊞        |
| thegent_dag_list          | ▣        |
| thegent_observe_summary   | ↑        |
| thegent_sitback_dashboard | ⊞        |
| thegent*terminal*\*       | ⊞ ◉ ⌨ ⎘ |
| thegent_ddg_search        | ⌕        |
| thegent_do_next           | →        |

---

## Part XXXII: Queue & Team MCP Tools (Planned)

### 32.1 Queue Tools (Phase 1)

| Tool                       | Params             | Purpose              |
| -------------------------- | ------------------ | -------------------- |
| thegent_queue_list         | project?, limit?   | List pending         |
| thegent_queue_claim        | id, lease_minutes? | Claim for processing |
| thegent_queue_done         | id                 | Mark done            |
| thegent_queue_add          | prompt, project?   | Add to queue         |
| thegent_queue_edit         | id, prompt         | Edit prompt          |
| thegent_queue_release      | id                 | Release claim        |
| thegent_queue_extend_lease | id, minutes        | Extend lease         |

### 32.2 Team Tools (Phase 6)

| Tool                     | Params               | Purpose                      |
| ------------------------ | -------------------- | ---------------------------- |
| thegent_team_create      | name, teammates[]    | Create team, spawn teammates |
| thegent_team_task_list   | team_id              | List tasks                   |
| thegent_team_task_assign | team_id, task        | Assign task                  |
| thegent_team_task_claim  | team_id, task_id     | Teammate self-claim          |
| thegent_team_task_done   | team_id, task_id     | Mark done                    |
| thegent_team_message     | team_id, to, message | Send to teammate             |
| thegent_team_broadcast   | team_id, message     | Broadcast                    |
| thegent_team_shutdown    | team_id              | Graceful shutdown            |

---

## References

- [Claude Code hooks](https://code.claude.com/docs/en/hooks.md)
- [Claude Code agent teams](https://code.claude.com/docs/en/agent-teams.md)
- [Codex config reference](https://developers.openai.com/codex/config-reference)
- [Augment Code](https://www.augmentcode.com)
- harvest-idea-seeds.sh, prompt-submit-guard.sh, harvest-pending-queue.sh
- src/thegent/agents/droid.py, codex_proxy.py, direct_agents.py, registry.py
- .factory/hooks/hooks.json, .factory/settings.json

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added platform patterns
2. Added deep dive configurations
3. Enhanced cross-references

### Cross-References Added

- CROSS_PLATFORM_RESEARCH_INDEX.md
- CROSS_PLATFORM_ADVANCED_PATTERNS.md

### Practical Additions

- Platform templates
- Configuration examples

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](./CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md) - Consolidated guide
- [CLAUDE_CODE_FEATURE_PARITY_AUDIT.md](./CLAUDE_CODE_FEATURE_PARITY_AUDIT.md) - Feature parity
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
