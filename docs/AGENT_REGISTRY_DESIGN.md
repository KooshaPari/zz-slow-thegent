# Agent Registry & Interactive Session Management — Holistic Design

> **Status**: Implemented (Phases P0-P5 complete)
> **Scope**: Unified agent registry, session lifecycle, interaction modes, UX, security, observability
> **Related**: [AGENT_REGISTRY_RESEARCH.md](./AGENT_REGISTRY_RESEARCH.md) (research, IPC, prior art)

---

## Harmonization with Adjacent Systems

This design aligns with existing thegent plans, features, and governance.

| Adjacent System                 | Alignment                                                                                                                                                           |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Lifecycle Loops** (AGENTS.md) | `thegent orchestrate loop`, `loop-send`, `takeover` — Agent Registry extends these with unified list/view/send/attach; `session send` = `loop-send` for any session |
| **Unified Work Stream**         | Sessions may be tied to work items (WP-XXX, FR-XXX); registry does not own work stream; optional `task_id` / `run_id` links                                         |
| **Gardener**                    | Gardener spawns agents; registry discovers them; hunger `agent_failure` can surface session status                                                                  |
| **FR-AGT-007**                  | Existing "Agent Registry" = agent name resolution; this design = **Session Registry** (running processes); distinct but complementary                               |
| **Library-First**               | Prefer `watchdog` over polling for message/chat file changes; `tenacity` for retries; `structlog` for audit                                                         |
| **Docs Organization**           | Design in `docs/`; implementation tasks → `docs/changes/agent-registry/`; ADR when decisions lock                                                                   |
| **Spec Traceability**           | New FRs (FR-REG-XXX) for registry features; tests reference FR IDs                                                                                                  |
| **Debug/Metrics**               | Reuse `--debug`, `THGENT_DEBUG`; add `thegent_sessions_*` metrics alongside existing                                                                                |

**Terminology**: Use **Session Registry** when distinguishing from FR-AGT-007's agent name registry. Use **Agent Registry** when referring to the holistic "all agent processes" vision.

**Docs location**: Per project docs org, research → `docs/research/`, plans → `docs/plans/`, reference → `docs/reference/`. Consider moving `AGENT_REGISTRY_RESEARCH.md` → `docs/research/`, this design → `docs/reference/` or `docs/plans/` when finalizing. Implementation tasks → `docs/changes/agent-registry/`.

---

## Quick Reference

| Section | Contents                                             |
| ------- | ---------------------------------------------------- |
| §1      | Vision, principles, non-goals                        |
| §2      | Unified agent model (sources, interactivity, schema) |
| §3      | Lifecycle & state machine                            |
| §4      | Capability matrix (action × transport)               |
| §5      | Data model & storage layout                          |
| §6      | Security & authorization                             |
| §7      | Observability (metrics, logs, audit)                 |
| §8      | UX flows (CLI, TUI, MCP)                             |
| §9      | Extensibility (plugins)                              |
| §10     | Failure modes & mitigations                          |
| §11     | Migration & rollout                                  |
| §12     | Testing strategy                                     |
| §13     | Glossary                                             |
| §14     | Decision records                                     |
| §15     | Implementation roadmap                               |
| §16     | References                                           |

---

## 1. Vision & Principles

### 1.1 North Star

**Every agent process — whether thegent-managed, IDE-spawned, or externally discovered — is discoverable, inspectable, and interactable through a single registry.**

A user can:

- See all running agents in one place
- Open any session to view chat history, logs, and audit trail
- Send messages or reprompts to running agents
- Attach interactively when the process supports it
- Resume or patch sessions when direct interaction is not possible

### 1.2 Design Principles

| Principle                   | Meaning                                                                    |
| --------------------------- | -------------------------------------------------------------------------- |
| **Unified over fragmented** | One registry, one data model, one UX — not separate systems per agent type |
| **Graceful degradation**    | Full interactivity when possible; view-only or patch-resume when not       |
| **Composability**           | Works with tmux, holdpty, reptyr — does not require them                   |
| **Observability first**     | Every interaction is auditable; metrics and traces built in                |
| **Security by default**     | Trust boundaries, least privilege, explicit authorization                  |
| **Incremental adoption**    | Works with existing agents; enhancements are additive                      |

### 1.3 Non-Goals (Explicit)

- **Not a process manager** — No lifecycle orchestration beyond thegent’s existing run/bg
- **Not a replacement for tmux/screen** — Complements them; uses them when available
- **Not real-time collaboration** — Single-writer for interactive attach; multi-reader for view
- **Not a chat platform** — Focus is agent sessions, not general messaging

---

## 2. Unified Agent Model

### 2.1 Agent Source Types

All agents are classified by **source** and **interactivity**:

| Source               | Description                                     | Examples                       |
| -------------------- | ----------------------------------------------- | ------------------------------ |
| **thegent-run**      | Spawned by `thegent run` or `thegent free --bg` | claude, codex, copilot, gemini |
| **thegent-droid**    | Factory droid / opencode                        | `.factory/droids/*.md`         |
| **thegent-subagent** | Internal sub-task (e.g. cc task, plan step)     | Orchestration workers          |
| **ide-managed**      | Spawned by IDE (Cursor, Claude Code)            | Cursor agent, Claude Code pane |
| **user-spawned**     | User ran agent CLI directly                     | `claude -p "..."` in terminal  |
| **discovered**       | Detected via heliosShield / process tree        | External codex, copilot        |
| **mcp-proxy**        | Running behind MCP / CLIProxyAPIPlus            | Codex via proxy                |

### 2.2 Interactivity Modes

| Mode                   | stdin          | stdout/stderr   | Attach | View | Message        |
| ---------------------- | -------------- | --------------- | ------ | ---- | -------------- |
| **Interactive (PTY)**  | TTY            | TTY             | ✅     | ✅   | ✅ (keys)      |
| **Interactive (tmux)** | tmux pane      | tmux pane       | ✅     | ✅   | ✅ (send-keys) |
| **Headless (logs)**    | /dev/null      | files           | ❌     | ✅   | ⚠️ (queue)     |
| **Headless (holdpty)** | PTY via holder | socket + buffer | ✅     | ✅   | ✅             |
| **Read-only**          | N/A            | stream only     | ❌     | ✅   | ❌             |

### 2.3 Canonical Agent Record Schema

```yaml
AgentRecord:
  id: string # Unique, stable (e.g. session_id or correlation_id)
  source: enum # thegent-run | thegent-droid | thegent-subagent | ide-managed | user-spawned | discovered | mcp-proxy
  interactivity: enum # pty | tmux | headless-logs | headless-holdpty | read-only

  # Identity
  agent_name: string # claude, codex, copilot, etc.
  model: string | null
  owner: string # owner tag (user@host, etc.)
  cwd: string
  started_at: datetime

  # Process
  pid: int | null
  ppid: int | null
  status: enum # running | paused | exited | failed | unknown

  # Attachment
  attach_target: object | null # tmux pane, holdpty session, etc.
  message_endpoint: string | null # fifo path, socket path, or "tmux:{pane}"

  # Paths (thegent-managed only)
  meta_path: string | null
  stdout_path: string | null
  stderr_path: string | null
  chat_path: string | null
  messages_path: string | null

  # Metadata
  prompt_preview: string
  run_id: string | null
  task_id: string | null
  domain_tag: string | null
```

---

## 3. Lifecycle & State Machine

### 3.1 Session States

```
                    ┌─────────────┐
                    │   created   │
                    └──────┬──────┘
                           │ spawn
                           ▼
                    ┌─────────────┐
         ┌──────────│   running   │──────────┐
         │          └──────┬──────┘          │
         │ pause           │                 │ stop
         ▼                 │ exit             ▼
   ┌──────────┐            │           ┌──────────┐
   │  paused  │            │           │  stopped │
   └────┬─────┘            │           └──────────┘
        │ resume           │
        └──────────────────┼──────────────────┘
                           ▼
                    ┌─────────────┐
                    │   exited    │
                    │ (success or │
                    │   failure)  │
                    └─────────────┘
```

### 3.2 State Transitions

| From    | To      | Trigger                                    |
| ------- | ------- | ------------------------------------------ |
| created | running | Process spawned, meta written              |
| running | paused  | HITL checkpoint, policy, or explicit pause |
| running | stopped | SIGTERM/SIGKILL, user stop                 |
| running | exited  | Process exits (code 0 or non-zero)         |
| paused  | running | Resume                                     |
| stopped | exited  | Process reaped                             |

### 3.3 Staleness & Cleanup

- **Stale**: No activity for `max_idle_seconds`; process may be hung
- **Orphan**: Parent (thegent, Cursor, etc.) no longer running
- **Zombie**: Process exited but not reaped
- **Cleanup policy**: Configurable retention; prune orphans by PPID when enabled

---

## 4. Interaction Modes — Capability Matrix

### 4.1 By Action

| Action                   | tmux         | holdpty     | headless (FIFO) | headless (file) | read-only |
| ------------------------ | ------------ | ----------- | --------------- | --------------- | --------- |
| **List**                 | ✅           | ✅          | ✅              | ✅              | ✅        |
| **View logs**            | ✅           | ✅          | ✅              | ✅              | ✅        |
| **View chat**            | ✅           | ✅          | ✅              | ✅              | ✅        |
| **Send message**         | ✅ send-keys | ✅ write    | ✅ write        | ✅ append       | ❌        |
| **Attach (interactive)** | ✅           | ✅          | ❌              | ❌              | ❌        |
| **Stop**                 | ✅ kill pane | ✅ stop     | ✅ SIGTERM      | ✅ SIGTERM      | ❌        |
| **Pause/Resume**         | ⚠️ registry  | ⚠️ registry | ⚠️ registry     | ⚠️ registry     | ❌        |

### 4.2 By Agent Source

| Source           | Default interactivity | Upgrade path                |
| ---------------- | --------------------- | --------------------------- |
| thegent-run (bg) | headless-logs         | holdpty wrapper             |
| thegent-run (fg) | pty (terminal)        | tmux if in tmux             |
| ide-managed      | tmux or pty           | Depends on IDE              |
| user-spawned     | tmux if in tmux       | holdpty if launched with it |
| discovered       | read-only or headless | N/A                         |
| mcp-proxy        | headless-logs         | MCP session API             |

---

## 5. Data Model & Storage

### 5.1 Directory Layout

```
session_dir/
├── {owner}/
│   ├── {session_id}.meta.json      # AgentRecord snapshot
│   ├── {session_id}.stdout.log
│   ├── {session_id}.stderr.log
│   ├── {session_id}.chat.jsonl     # Structured conversation
│   ├── {session_id}.messages.jsonl # Pending messages (queue)
│   ├── {session_id}.in             # FIFO (optional)
│   └── {session_id}.audit.jsonl    # Audit trail
├── discovered/
│   └── ppid_{ppid}.json
├── run_registry.jsonl
└── agent_index.json                # Optional: cached list for fast listing
```

### 5.2 Chat Entry Schema

```json
{
  "ts": "2025-02-18T12:00:00Z",
  "role": "user|assistant|system|tool",
  "content": "...",
  "tool_name": null,
  "tool_input": null,
  "metadata": {}
}
```

### 5.3 Message (Queue) Schema

```json
{
  "id": "uuid",
  "ts": "2025-02-18T12:00:00Z",
  "type": "reprompt|command|system|interrupt",
  "sender": "user|agent|system",
  "content": "...",
  "status": "pending|delivered|processed|failed",
  "metadata": {}
}
```

### 5.4 Audit Entry Schema

```json
{
  "ts": "2025-02-18T12:00:00Z",
  "action": "view|send|attach|stop|pause|resume",
  "actor": "user@host",
  "session_id": "...",
  "details": {},
  "result": "success|denied|error"
}
```

---

## 6. Security & Authorization

### 6.1 Trust Boundaries

| Boundary         | Rule                                                   |
| ---------------- | ------------------------------------------------------ |
| **Owner**        | Sessions are scoped by owner tag; list/filter by owner |
| **Cross-owner**  | `--all` or admin role required to see other owners     |
| **Message send** | Only owner (or delegated) can send messages            |
| **Stop/Kill**    | Owner or explicit override                             |
| **Audit**        | All actions logged; no bypass                          |

### 6.2 Threat Model

| Threat              | Mitigation                                        |
| ------------------- | ------------------------------------------------- |
| Unauthorized view   | Owner-scoped listing; no cross-owner by default   |
| Message injection   | Validate message format; rate limit               |
| FIFO abuse          | Create with restricted perms; session-scoped path |
| Audit tampering     | Append-only; optional integrity hash chain        |
| DoS (many sessions) | Concurrency limit; retention policy               |

### 6.3 Configuration

```yaml
agent_registry:
  allow_cross_owner: false
  require_owner_for_send: true
  audit_enabled: true
  audit_retention_days: 90
  max_message_rate_per_session: 10 # per minute
```

---

## 7. Observability

### 7.1 Metrics

| Metric                                   | Type      | Labels               |
| ---------------------------------------- | --------- | -------------------- |
| `thegent_sessions_total`                 | gauge     | owner, agent, status |
| `thegent_sessions_created_total`         | counter   | owner, agent         |
| `thegent_messages_sent_total`            | counter   | session_id, type     |
| `thegent_attach_attempts_total`          | counter   | session_id, result   |
| `thegent_registry_list_duration_seconds` | histogram | —                    |

### 7.2 Logging

- **Structured logs** (JSON) for registry actions
- **Correlation ID** (session_id) on every log line
- **Log levels**: DEBUG for message delivery, INFO for actions, WARN for fallbacks

### 7.3 Tracing

- **OTel spans** for: list, view, send, attach
- **Span attributes**: session_id, agent, owner, interactivity

### 7.4 Audit Trail

- **Append-only** `{session_id}.audit.jsonl`
- **Immutable** — no deletion, only retention-based pruning
- **Queryable** — for compliance, debugging, forensics

---

## 8. UX Flows

### 8.1 User Journeys

**Journey A: Inspect running agent**

1. Run `thegent session list` or open TUI
2. See all sessions (owner-filtered)
3. Select session → view chat + logs
4. Optionally send reprompt or attach

**Journey B: Reprompt headless agent**

1. Session is headless (no tmux)
2. User sends message via TUI or `thegent session send <id> "new prompt"`
3. Message queued to `messages.jsonl` or FIFO
4. Agent polls or reads FIFO; processes when ready
5. Response appears in chat + logs

**Journey C: Attach to tmux session**

1. Session has `attach_target.tmux_pane`
2. User runs `thegent session attach <id>` or TUI "Attach"
3. CLI prints: `tmux attach-session -t {session}` or equivalent
4. User attaches; interacts directly

**Journey D: Patch-resume (fallback)**

1. Session is headless and does not support message queue
2. User selects "Resume with context"
3. System builds continuation prompt from chat + logs (tail)
4. New run started with `--continue-from <session_id>`
5. Old session marked superseded

### 8.2 CLI Surface

**New commands** (extends existing surface):

```
thegent session list [--all] [--owner X] [--agent Y] [--status running]
thegent session show <id>
thegent session logs <id> [--stdout|--stderr] [--follow]
thegent session send <id> <message>
thegent session attach <id>
thegent session stop <id>
thegent session pause <id>
thegent session resume <id>
```

**Mapping to existing commands**:

| New              | Existing                                      | Notes                                                                |
| ---------------- | --------------------------------------------- | -------------------------------------------------------------------- |
| `session list`   | `thegent ps`                                  | `ps` = list; `session list` = same data + discovery, richer filters  |
| `session send`   | `thegent orchestrate loop-send <id> <prompt>` | loop-send is loop-specific; session send = any session               |
| `session attach` | `thegent takeover <session>`                  | takeover = tmux attach; session attach = unified (tmux/holdpty hint) |
| —                | `thegent orchestrate loop`                    | Loop spawns sessions; registry lists them                            |
| —                | `thegent bg`                                  | bg spawns sessions; registry lists them                              |

**Backward compatibility**: `thegent ps` unchanged. `thegent session` is additive. Consider `ps` as alias for `session list` in future.

### 8.3 TUI Layout (opentui/react)

```
┌─────────────────────────────────────────────────────────────┐
│ Agent Registry                                    [r]efresh │
├─────────────────────────────────────────────────────────────┤
│ Sessions (12)          │ Chat / Logs                         │
│ ───────────────────── │ ────────────────────────────────── │
│ ● claude-abc1  running │ [Chat] [Logs] [Audit]               │
│   codex-def2   running │                                     │
│   copilot-ghi3 exited  │  user: Fix the bug in utils.py      │
│   ...                  │  assistant: I'll analyze...         │
│                        │  tool: read_file utils.py           │
│                        │  ...                                │
├─────────────────────────────────────────────────────────────┤
│ [Type message...]                              [Send] [Attach]│
└─────────────────────────────────────────────────────────────┘
```

### 8.4 MCP Tools

| Tool                          | Purpose                        |
| ----------------------------- | ------------------------------ |
| `thegent_session_list`        | List sessions (filterable)     |
| `thegent_session_show`        | Get session details            |
| `thegent_session_logs`        | Read stdout/stderr             |
| `thegent_session_send`        | Send message to session        |
| `thegent_session_attach_hint` | Return attach command for user |

---

## 9. Extensibility

### 9.1 Agent Source Plugins

- **Discovery plugins**: Register custom discovery logic (e.g. Kubernetes pods, Docker)
- **Attachment plugins**: Custom attach logic (e.g. VS Code debug, custom IDE)
- **Message transport plugins**: Custom delivery (e.g. WebSocket, gRPC)

### 9.2 Configuration Hooks

```yaml
agent_registry:
  discovery_plugins: ["heliosShield", "k8s"]
  attachment_handlers:
    tmux: "thegent.tools.terminal"
    holdpty: "thegent.tools.holdpty"
  message_transports:
    default: "file"
    fifo: "thegent.messaging.fifo"
```

---

## 10. Failure Modes & Mitigations

| Failure               | Impact                         | Mitigation                         |
| --------------------- | ------------------------------ | ---------------------------------- |
| FIFO creation fails   | No message delivery            | Fallback to file queue             |
| Agent doesn't poll    | Messages never processed       | Document; optional agent-side hook |
| Tmux not installed    | No attach for tmux sessions    | Show "Install tmux" hint           |
| holdpty not installed | No attach for holdpty sessions | Fallback to view-only              |
| Session dir full      | Write failures                 | Retention policy; alert            |
| Stale session         | Confusion                      | Status "stale"; idle detection     |
| Orphan session        | Resource leak                  | Prune by PPID; configurable        |
| Cross-owner leak      | Privacy                        | Strict owner filtering; audit      |

---

## 11. Migration & Rollout

### 11.1 Phases

| Phase | Scope                                              | Risk   |
| ----- | -------------------------------------------------- | ------ |
| **0** | Add chat.jsonl, messages.jsonl; no behavior change | Low    |
| **1** | MessageRegistry + ChatHistory; TUI read-only       | Low    |
| **2** | Send message (file + tmux); TUI send               | Medium |
| **3** | FIFO for headless; holdpty wrapper option          | Medium |
| **4** | MCP tools; discovery plugins                       | Low    |

### 11.2 Backward Compatibility

- **Existing sessions**: Continue to work; new files created on first interaction
- **Old CLI**: `thegent ps` unchanged; `thegent session` is additive
- **Config**: New keys under `agent_registry`; defaults preserve current behavior

### 11.3 Feature Flags

```yaml
agent_registry:
  enabled: true
  chat_logging: true
  message_queue: true
  fifo_transport: false # Opt-in initially
  holdpty_wrapper: false # Opt-in
```

---

## 12. Testing Strategy

| Layer           | Scope                                            | Tools               |
| --------------- | ------------------------------------------------ | ------------------- |
| **Unit**        | MessageRegistry, ChatHistory, schema validation  | pytest              |
| **Integration** | List/send with real session dir; FIFO round-trip | pytest + temp dir   |
| **E2E**         | Full flow: run bg → list → send → view           | pytest + subprocess |
| **Manual**      | TUI, attach, holdpty                             | Checklist           |

---

## 13. Glossary

| Term              | Definition                                                      |
| ----------------- | --------------------------------------------------------------- |
| **Session**       | A single agent run; has id, meta, logs, chat                    |
| **Registry**      | Central index of all sessions                                   |
| **Attach**        | Interactive takeover of a session's stdin/stdout                |
| **View**          | Read-only access to logs/chat                                   |
| **Message**       | User or system input sent to a running agent                    |
| **Reprompt**      | A message that continues or redirects the conversation          |
| **Patch-resume**  | Starting a new run with prior context when attach is impossible |
| **Owner**         | Tag identifying who "owns" a session (user@host, etc.)          |
| **Interactivity** | Whether a session supports attach and/or message delivery       |

---

## 14. Decision Records

### DR-1: File-first messaging

**Decision**: Use file-based message queue as default; FIFO as opt-in enhancement.
**Rationale**: Works everywhere; no special setup; easy to debug. FIFO adds complexity and platform considerations.

### DR-2: Single-writer for attach

**Decision**: Only one interactive attach at a time per session.
**Rationale**: Avoids conflicting input; matches tmux/holdpty semantics.

### DR-3: Owner-scoped by default

**Decision**: List and actions are owner-scoped unless `--all` or admin.
**Rationale**: Privacy; least privilege; multi-tenant safety.

### DR-4: holdpty as optional wrapper

**Decision**: holdpty is an opt-in launch wrapper, not required.
**Rationale**: External dependency; not all users need attach for headless.

### DR-5: Ghostty not a mux

**Decision**: No Ghostty-specific attach API; use tmux/holdpty inside Ghostty.
**Rationale**: Ghostty is a terminal emulator; it does not provide session multiplexing.

---

## 15. Implementation Roadmap

| Phase  | Focus      | Deliverables                                               | Est.   | Status |
| ------ | ---------- | ---------------------------------------------------------- | ------ | ------ |
| **P0** | Foundation | Schema, ChatHistory, MessageRegistry (file), audit stub    | 1 wk   | ✅     |
| **P1** | Read UX    | `session list`/`show`/`logs`, TUI read-only, MCP list/show | 1 wk   | ✅     |
| **P2** | Send       | `session send`, tmux delivery, TUI input                   | 1 wk   | ✅     |
| **P3** | Attach     | `session attach`, tmux/holdpty hints, TUI attach button    | 1 wk   | ✅     |
| **P4** | Headless   | FIFO transport, agent polling hook, holdpty wrapper opt-in | 1–2 wk | ✅     |
| **P5** | Polish     | Metrics, retention, discovery plugins, docs                | 1 wk   | ✅     |

**Spec traceability**: Add FR-REG-XXX to FUNCTIONAL_REQUIREMENTS.md for each deliverable; tests reference FR IDs per project QA governance.

---

## 16. References

### Internal

| Doc                                                                           | Purpose                                 |
| ----------------------------------------------------------------------------- | --------------------------------------- |
| [AGENT_REGISTRY_RESEARCH.md](./AGENT_REGISTRY_RESEARCH.md)                    | IPC options, prior art, web research    |
| [UNIFIED_WORK_STREAM_DESIGN.md](./reference/UNIFIED_WORK_STREAM_DESIGN.md)    | Work stream, backlog, CLAIMED/COMPLETED |
| [GARDENER_ARCHITECTURE.md](./reference/GARDENER_ARCHITECTURE.md)              | Hunger states, scan→execute loop        |
| [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./research/LIBRARY_FIRST_AUDIT_AND_PLAN.md) | Library preferences, watchdog, tenacity |
| [DEBUG_TAGS_AND_METRICS.md](./plans/DEBUG_TAGS_AND_METRICS.md)                | Debug flag, response tags               |
| [FUNCTIONAL_REQUIREMENTS.md](../FUNCTIONAL_REQUIREMENTS.md)                   | FR-AGT-007 (agent name registry)        |
| [AGENTS.md](../AGENTS.md)                                                     | Lifecycle loops, takeover, orchestrate  |

### External

- [Baeldung: Attach Terminal to Detached Process](https://www.baeldung.com/linux/attach-terminal-detached-process)
- [reptyr](https://github.com/nelhage/reptyr)
- [holdpty](https://github.com/marcfargas/holdpty)
- [mcp-interactive-terminal](https://github.com/amol21p/mcp-interactive-terminal)
