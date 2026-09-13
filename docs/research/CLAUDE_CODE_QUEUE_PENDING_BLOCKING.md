<DONE>
# Claude Code: Queue Pending & Blocking Messages (Research & Plan)

**Goal:** Replicate Codex/Cursor-agent behavior in Claude Code:

1. **Queue messages pending session stop** — add messages that are saved and processed when the session stops
2. **Blocking messages** — messages that block until the user resolves them

**Scope:** Claude Code (primary), with **pull from Cursor agent CLI sessions** so $defer/$pending in Cursor transcripts are harvested like $idea.

---

## 1. Codex/Cursor-Agent Behavior (Inferred)

From user description and common agent UX patterns:

| Feature           | Likely behavior                                                                                                                                                                                           |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pending queue** | User adds messages (e.g. `$defer`, `$later`) that are not sent immediately. They are stored and either: (a) dumped to a handoff file for the next session, or (b) shown/processed when the session stops. |
| **Blocking**      | User sends a message that requires human input before the agent continues. The agent pauses; user must acknowledge/resolve (e.g. approve, reject, add context) before work resumes.                       |

**Note:** Codex and Cursor-agent are proprietary. Exact APIs/schemas are not publicly documented. This plan infers behavior from UX patterns.

### 1.1 Parity with $idea Flow

The existing **$idea** flow (see [IDEA_SEEDS_SESSION_STORAGE.md](./IDEA_SEEDS_SESSION_STORAGE.md)) provides a precedent:

| Aspect             | $idea                                                   | $defer / $pending                                 |
| ------------------ | ------------------------------------------------------- | ------------------------------------------------- |
| **Immediate save** | UserPromptSubmit saves to `docs/research/idea-seeds/`   | UserPromptSubmit appends to pending queue         |
| **Harvest**        | harvest-idea-seeds.sh scans Claude/Codex/Cursor history | Same script extended to scan for $defer/$pending  |
| **Block prompt?**  | No (advisory only)                                      | Yes (exit 1)                                      |
| **On Stop**        | harvest-idea-seeds-stop.sh runs harvest                 | harvest-pending-queue.sh flushes queue to handoff |
| **Output**         | Per-prompt seed file                                    | Consolidated handoff file                         |

**Design principle:** Reuse harvest-idea-seeds.sh pattern for Cursor/Claude/Codex session pull. Add $defer/$pending to the harvest filter; write to pending-handoff instead of idea-seeds when flag is $defer/$pending.

---

## 1.2 Cursor Agent CLI Sessions Pull

**User ask:** "pull from cursor-agent cli sessions too?"

Cursor agent transcripts live at `~/.cursor/projects/<project-id>/agent-transcripts/<session>.jsonl`. The harvest-idea-seeds.sh already pulls $idea from:

- Claude: `~/.claude/history.jsonl`
- Codex: `~/.codex/history.jsonl`
- Cursor: `~/.cursor/projects/Users-*/agent-transcripts/*.jsonl`

**Extension:** Add $defer and $pending to the harvest filter. When found:

- **$idea** → write to `docs/research/idea-seeds/` (unchanged)
- **$defer** / **$pending** → append to project-scoped pending queue or write directly to `docs/research/pending-handoff.md` (append section)

**Path resolution:** Reuse `cursor_project_path()` from harvest-idea-seeds.sh (decode folder name or grep agent-tools for workspace path).

**State:** Use offset file `~/.claude/.idea-harvest-cursor-done` (already exists) — extend schema to track last line per transcript for both $idea and $defer. Or: single pass, write $defer entries to pending-handoff during harvest.

**Performance:** Cursor harvest scans 270+ transcript files; can take 1–2 min. Use `CURSOR_PROJECTS=` to skip. For $defer harvest, same cost — one pass, two filters ($idea vs $defer).

---

## 2. Claude Code Hook Surface

Claude Code exposes these lifecycle hooks (from `hooks/hook-dispatcher`):

| Event                | When                           | Blocking?       | Use for queue                              |
| -------------------- | ------------------------------ | --------------- | ------------------------------------------ |
| **UserPromptSubmit** | Before prompt is sent to model | Yes (fail-fast) | Intercept prompts with `$defer` / `$block` |
| **Stop**             | When user ends session         | No (parallel)   | Process pending queue, write handoff       |
| **SessionStart**     | When new session begins        | No              | Load pending queue from previous session   |
| **SessionEnd**       | When session ends (cleanup)    | No              | Alternative to Stop for queue flush        |
| **PreToolUse**       | Before each tool call          | Yes             | Could block tool use until resolution      |
| **PostToolUse**      | After each tool call           | No              | Advisory                                   |

**Key insight:** UserPromptSubmit is the only hook that runs _before_ the prompt is sent. It can:

- Return non-zero → block the prompt (Claude Code will not send it)
- Return zero → allow the prompt through

---

## 3. Design: Pending Queue

### 3.1 Prompt flags

| Flag                   | Meaning                                                 |
| ---------------------- | ------------------------------------------------------- |
| `$defer` or `$pending` | Do not send now; add to pending queue. Process on Stop. |
| `$block`               | Block until user resolves (see §4).                     |

### 3.2 Flow

```
User types: "Add tests for auth.py $defer"
    → UserPromptSubmit hook fires
    → prompt-submit-guard (or new queue hook) detects $defer
    → Append to ~/.claude/pending-queue.jsonl (or project .claude/pending-queue.jsonl)
    → Return exit 1 (block prompt from being sent)
    → User sees: "Queued for session stop. 3 pending."

On Stop:
    → stop-reconcile or new harvest-pending-queue hook
    → Read pending-queue.jsonl
    → Write to project docs/research/pending-handoff.md or .claude/next-session-prompts.md
    → Clear or archive queue
```

### 3.3 Sequence Diagram: Pending Queue (Claude Code)

```
User                Claude Code         prompt-submit-guard      pending-queue.jsonl
  |                       |                        |                        |
  | "Add tests $defer"    |                        |                        |
  |---------------------->|                        |                        |
  |                       | UserPromptSubmit       |                        |
  |                       |----------------------->|                        |
  |                       |                        | detect $defer           |
  |                       |                        | append entry            |
  |                       |                        |------------------------>|
  |                       |                        | exit 1                  |
  |                       |<-----------------------|                        |
  |  "Queued. 3 pending." |                        |                        |
  |<----------------------|                        |                        |
  |  (prompt NOT sent)    |                        |                        |

--- Session Stop ---

  |                       | Stop hook              | harvest-pending-queue   |
  |                       |----------------------->|                        |
  |                       |                        | read queue             |
  |                       |                        |<------------------------|
  |                       |                        | write handoff.md       |
  |                       |                        | clear queue            |
  |                       |<-----------------------|                        |
```

### 3.4 Sequence Diagram: Harvest from Cursor (Pull)

```
harvest-idea-seeds.sh    Cursor transcripts       pending-handoff.md
         |                        |                        |
         | scan */*.jsonl         |                        |
         |---------------------->|                        |
         |                        |                        |
         | for each line:         |                        |
         |   if $defer in text    |                        |
         |   resolve project path |                        |
         |   append to handoff    |                        |
         |----------------------------------------------->|
         |                        |                        |
```

### 3.5 Handoff format

```markdown
# Pending prompts (from session stop 2026-02-16T12:00:00Z)

1. Add tests for auth.py
2. Refactor the login flow to use OAuth
3. Update README with new setup steps
```

Or structured JSON for programmatic consumption:

```json
{ "session_stopped_at": "...", "prompts": ["Add tests for auth.py", "..."] }
```

---

## 4. Design: Blocking Messages

### 4.1 Challenge

Claude Code hooks are synchronous. A "blocking" message in Codex/Cursor-agent typically means:

- Agent pauses
- User sees a modal or inline prompt
- User must respond (approve, reject, add context)
- Agent continues with that response

Claude Code does not expose a "pause/resume" API to hooks. The only blocking we can do is:

- **UserPromptSubmit returns non-zero** → prompt is rejected and never sent

So we cannot "pause and wait for user input" in the traditional sense. We can only:

1. Block the prompt (reject it)
2. Show the user where to resolve (file, CLI command)
3. User resolves manually (e.g. edits a file, runs a command)
4. User resubmits the prompt (or a "resume" command picks it up)

### 4.2 Blocking flow (practical)

```
User types: "Deploy to prod $block"
    → UserPromptSubmit detects $block
    → Block prompt (exit 1)
    → Write to .claude/blocked-prompts.jsonl with status: "pending"
    → Print: "Blocked. Resolve with: thegent queue resolve <id>"
    → User runs: thegent queue resolve abc123 --approve
    → Blocked prompt is marked resolved
    → User can then resubmit prompt (without $block) or a "resume" flow picks it up
```

**Alternative:** Blocking could mean "add to escalation queue" (WP-3008) — thegent already has `EscalationQueue` and `thegent govern escalate add`. A `$block` prompt could be routed there.

### 4.3 State Machine: Pending vs Blocked

```
                    User types prompt
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    [no flag]         [$defer]          [$block]
         │                 │                 │
         │                 │                 │
    prompt sent       append to          escalate add
    to model          queue              + exit 1
         │                 │                 │
         │                 │                 │
         ▼                 ▼                 ▼
    [agent runs]    [queued]           [blocked]
                           │                 │
                           │                 │
                    On Stop:            User: govern
                    flush to            escalate resolve
                    handoff             │
                           │                 │
                           ▼                 ▼
                    [handoff file]     [resolved]
                    for next session   (resubmit or
                                       next-item picks up)
```

### 4.4 Blocking as escalation

```
User: "Deploy to prod $block"
    → Hook blocks prompt
    → thegent govern escalate add --run-id=block-<ts> --reason="User requested blocking approval"
    → User runs: thegent govern escalate resolve <id>
    → Next session or "next thing to do" picks up the resolved item
```

---

## 5. Alternatives Considered

| Alternative                                              | Pros                                             | Cons                                                    |
| -------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------- |
| **MCP tool** (`thegent_queue_add`, `thegent_queue_list`) | Agent can queue via tool; no prompt interception | Requires agent to call tool; user must type differently |
| **Native Claude Code support**                           | Ideal UX if Claude adds it                       | Not available; out of our control                       |
| **Separate queue CLI only**                              | `thegent queue add "prompt"` — no hook           | User must leave Claude Code to queue; friction          |
| **Hook + handoff file (chosen)**                         | Works with current Claude Code; no API needed    | Blocking is "reject + escalate", not true pause         |

---

## 6. Edge Cases & Error Handling

| Edge case                                              | Handling                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Concurrent sessions** (multiple Claude Code windows) | Project-scoped queue: `PROJECT_DIR/.claude/pending-queue.jsonl`. Each session writes to same file; append is atomic at line level. Stop hook runs per session; last one to stop flushes. Risk: duplicate handoff if two sessions stop close together. Mitigation: handoff file append with session_id; or lock file. |
| **Multi-project**                                      | Queue keyed by `PROJECT_DIR` (git root). Handoff written to `$PROJECT_DIR/docs/research/pending-handoff.md`.                                                                                                                                                                                                         |
| **Queue file missing/corrupt**                         | On read: if not exists, treat as empty. On write: mkdir -p parent; append. Corrupt line: skip, log to stderr.                                                                                                                                                                                                        |
| **PROJECT_DIR unset**                                  | Fallback: `~/.claude/pending-queue.jsonl` and `~/.claude/pending-handoff.md`. User can set PROJECT_DIR in env.                                                                                                                                                                                                       |
| **Harvest script timeout**                             | Cursor harvest can take 1–2 min. Run in background on Stop? Or accept; user can `CURSOR_PROJECTS=` to skip.                                                                                                                                                                                                          |
| **$defer and $block in same prompt**                   | Precedence: $block wins (blocking is stricter). Block prompt, add to escalation.                                                                                                                                                                                                                                     |
| **Empty prompt with only $defer**                      | Reject; do not add empty string to queue.                                                                                                                                                                                                                                                                            |

---

## 7. Configuration

| Env / config               | Default                                                                       | Purpose                                        |
| -------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------- |
| `PENDING_QUEUE_FILE`       | `$PROJECT_DIR/.claude/pending-queue.jsonl` or `~/.claude/pending-queue.jsonl` | Queue storage                                  |
| `PENDING_HANDOFF_FILE`     | `$PROJECT_DIR/docs/research/pending-handoff.md`                               | Output on Stop                                 |
| `PENDING_QUEUE_ENABLED`    | `1`                                                                           | Set to `0` to disable $defer/$pending handling |
| `BLOCK_ESCALATION_ENABLED` | `1`                                                                           | Set to `0` to disable $block → escalation      |
| `CURSOR_PROJECTS`          | `~/.cursor/projects`                                                          | Cursor harvest root; `=` to skip               |

---

## 8. Integration with Existing Workflows

| Workflow             | Integration                                                                                                                                                                                                       |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Next thing to do** | `thegent_do_next` / `thegent plan do-next` should include items from pending-handoff.md and escalation queue. Add handoff path to "read from" list.                                                               |
| **Gardening**        | `thegent govern escalate list --past-sla` already shows escalations. Pending handoff can be a "pre-escalation" — items not yet escalated but queued for next session.                                             |
| **Skills**           | Update agent-orchestra and sitback-agent: "Use $defer to queue for session stop; use $block to require approval before proceeding."                                                                               |
| **Stop hook order**  | harvest-idea-seeds-stop runs; harvest-pending-queue (new) runs. Order: harvest-idea-seeds (captures $idea from history), then harvest-pending-queue (flushes Claude Code queue + any Cursor $defer from harvest). |

---

## 9. Implementation Plan

### Phase 1: Pending queue (MVP)

| Task                                                                                                                       | Location                       | Effort |
| -------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------ |
| Add `$defer` / `$pending` detection in prompt-submit-guard                                                                 | `hooks/prompt-submit-guard.sh` | Small  |
| Add pending queue file: `~/.claude/pending-queue.jsonl` or `PROJECT_DIR/.claude/pending-queue.jsonl`                       | New                            | Small  |
| On `$defer`: append to queue, exit 1, print friendly message                                                               | prompt-submit-guard            | Small  |
| Add Stop hook: `harvest-pending-queue.sh`                                                                                  | `hooks/`                       | Small  |
| On Stop: read queue, write handoff to `docs/research/pending-handoff.md` or `.claude/next-session-prompts.md`, clear queue | harvest-pending-queue          | Small  |
| Add SessionStart hook: optionally inject "You have N pending prompts from last session"                                    | Optional                       | Small  |

### Phase 1b: Cursor pull (harvest $defer/$pending)

| Task                                                                            | Location                        | Effort |
| ------------------------------------------------------------------------------- | ------------------------------- | ------ |
| Extend harvest-idea-seeds.sh to filter for $defer/$pending in addition to $idea | `scripts/harvest-idea-seeds.sh` | Small  |
| For $defer/$pending: append to pending-handoff or project pending queue         | Same script                     | Small  |
| Reuse cursor_project_path() and offset tracking                                 | Same script                     | —      |

### Phase 2: Blocking (as escalation)

| Task                                                                          | Location                        | Effort |
| ----------------------------------------------------------------------------- | ------------------------------- | ------ |
| Add `$block` detection in prompt-submit-guard                                 | prompt-submit-guard             | Small  |
| On `$block`: call `thegent govern escalate add` with prompt as reason, exit 1 | prompt-submit-guard or new hook | Medium |
| Ensure escalation queue is visible in "next thing to do" / handoff            | Already exists                  | —      |
| Add `thegent queue resolve` or use existing `thegent govern escalate resolve` | CLI                             | Small  |

### Phase 3: SessionStart integration (optional)

| Task                                                             | Location        | Effort |
| ---------------------------------------------------------------- | --------------- | ------ |
| SessionStart hook reads `next-session-prompts.md`                | New hook        | Small  |
| Inject summary into session context (if Claude Code supports it) | Research needed | —      |

**Note:** Claude Code may not support injecting text into the session on start. If not, the handoff file is purely for human/agent reference.

### Phase 4: Skills and docs

| Task                                                           | Location       | Effort |
| -------------------------------------------------------------- | -------------- | ------ |
| Update agent-orchestra, sitback-agent with $defer/$block usage | `skills/`      | Small  |
| Add thegent_do_next to read pending-handoff                    | MCP / cli_impl | Small  |
| Document in IDEA_SEEDS_SESSION_STORAGE.md                      | docs/research  | Small  |

---

## 10. Schema: Pending Queue

```jsonl
{"ts": "2026-02-16T12:00:00Z", "prompt": "Add tests for auth.py", "project": "/path/to/repo"}

{"ts": "2026-02-16T12:01:00Z", "prompt": "Refactor login flow", "project": "/path/to/repo"}
```

### Blocked prompts (or use escalation queue)

```jsonl
{
  "id": "block-1739...",
  "ts": "...",
  "prompt": "Deploy to prod",
  "status": "pending",
  "project": "..."
}
```

---

## 11. Testing Strategy

| Test type                            | Approach                                                                               | Status                                |
| ------------------------------------ | -------------------------------------------------------------------------------------- | ------------------------------------- |
| **Unit (prompt-submit-guard)**       | Invoke hook with mock stdin containing `$defer`; assert exit 1, queue file appended    | ✓ `tests/test_hooks_pending_queue.py` |
| **Unit (harvest-pending-queue)**     | Create temp queue file; run hook; assert handoff written, queue cleared                | ✓ `tests/test_hooks_pending_queue.py` |
| **Integration (harvest-idea-seeds)** | Add $defer line to temp Claude history; run harvest; assert pending-handoff updated    | ✓ `tests/test_hooks_pending_queue.py` |
| **E2E**                              | Manual: type "test $defer" in Claude Code; verify queued; stop session; verify handoff | Manual                                |

---

## 12. Gaps & Risks

| Gap                                                        | Mitigation                                                                                    |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Claude Code may not support SessionStart context injection | Handoff file is sufficient; user opens next session and says "process pending handoff"        |
| Blocking is not true "pause until user responds"           | Use escalation + manual resolve; document as "blocking = requires approval before proceeding" |
| Multiple projects sharing same queue                       | Use project-scoped queue: `PROJECT_DIR/.claude/pending-queue.jsonl`                           |
| Queue file grows unbounded                                 | Stop hook clears after processing; add retention for archived handoffs                        |

---

## 13. Summary

| Feature           | Approach                                                                                                              |
| ----------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Pending queue** | `$defer` / `$pending` → prompt-submit-guard blocks, appends to queue → Stop hook flushes to handoff file              |
| **Blocking**      | `$block` → prompt-submit-guard blocks, adds to escalation queue → user resolves via `thegent govern escalate resolve` |
| **Cursor pull**   | harvest-idea-seeds.sh extended to filter $defer/$pending from Cursor transcripts; append to handoff                   |

### Implementation DAG

```
P1.1: prompt-submit-guard $defer detection     ──┐
P1.2: pending queue append + exit 1            ──┼──> P1.4: harvest-pending-queue Stop hook
P1.3: queue file + handoff path logic          ──┘
                                                      │
P1b: harvest-idea-seeds $defer/$pending filter ───────┘
                                                      │
P2.1: prompt-submit-guard $block detection     ───────┼──> P2.2: escalate add integration
                                                      │
P3: SessionStart (optional)                    ───────┘
P4: Skills + thegent_do_next                   ───────┘
```

**Next step:** Implement Phase 1 (pending queue) in prompt-submit-guard + new Stop hook; then Phase 1b (Cursor pull).

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added queue implementation patterns
2. Added blocking/deferral workflow diagrams
3. Enhanced cross-references to related docs

### Cross-References Added

- USER_QUEUE_TUI_AND_AGENT_POLL.md
- CLAUDE_CODE_FEATURE_PARITY_AUDIT.md

### Practical Additions

- Queue storage patterns
- Blocking workflow implementation

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [USER_QUEUE_TUI_AND_AGENT_POLL.md](./USER_QUEUE_TUI_AND_AGENT_POLL.md) - Queue TUI
- [IDEA_SEEDS_SESSION_STORAGE.md](./IDEA_SEEDS_SESSION_STORAGE.md) - Session storage
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
