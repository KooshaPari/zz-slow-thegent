<DONE>
# User Queue + TUI: Editable Prompts While Agent Runs

**Goal:** User queues prompts in a separate TUI while the agent runs other work. Agent periodically checks the queue, picks up items, and processes them. User can add, edit, and view state (queued → in_progress → done) of each item.

**Context:** [OpenAI Codex](https://github.com/openai/codex) runs in terminal. User wants to type queued messages freely in another TUI without interrupting the agent.

---

## 1. Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  User TUI           │     │  prompt_queue.jsonl   │     │  Agent (Codex)   │
│  - Add prompt       │────▶│  - id, prompt, status │◀────│  - Polls queue  │
│  - Edit prompt      │     │  - queued|in_progress │     │  - Claims item   │
│  - View state       │     │    |done               │     │  - Marks done   │
└─────────────────────┘     └──────────────────────┘     └─────────────────┘
```

**Flow:**
1. User runs `thegent queue tui` (or similar) in a separate terminal — TUI for add/edit/list
2. Agent runs in Codex; agent instructions tell it to check `thegent_queue_list` between tasks
3. Agent calls `thegent_queue_list` → sees queued items
4. Agent calls `thegent_queue_claim <id>` → marks in_progress, returns prompt
5. Agent processes prompt
6. Agent calls `thegent_queue_done <id>` → marks done

---

## 2. Queue Schema

**File:** `PROJECT_DIR/.thegent/prompt_queue.jsonl` (or `~/.thegent/prompt_queue.jsonl` for global)

```jsonl
{"id":"q_abc123","prompt":"Add tests for auth.py","status":"queued","created_at":"2026-02-16T12:00:00Z","updated_at":"2026-02-16T12:00:00Z","project":"/path/to/repo"}
{"id":"q_def456","prompt":"Refactor login flow","status":"in_progress","created_at":"2026-02-16T12:01:00Z","updated_at":"2026-02-16T12:05:00Z","claimed_at":"2026-02-16T12:05:00Z","claimed_by":"codex:session_xyz","lease_expires_at":"2026-02-16T12:35:00Z","project":"/path/to/repo"}
{"id":"q_ghi789","prompt":"Update README","status":"done","created_at":"2026-02-16T12:02:00Z","updated_at":"2026-02-16T12:10:00Z","done_at":"2026-02-16T12:10:00Z","done_by":"codex:session_xyz","project":"/path/to/repo"}
```

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique ID (e.g. q_<uuid8>) |
| prompt | str | User's prompt (editable) |
| status | enum | queued, in_progress, done |
| created_at | ISO8601 | When added |
| updated_at | ISO8601 | Last modification |
| claimed_at | ISO8601? | When agent claimed (in_progress) |
| claimed_by | str? | **Agent identity** (see §2.1) |
| lease_expires_at | ISO8601? | Lock expiry; stale items can be reclaimed |
| done_at | ISO8601? | When agent marked done |
| done_by | str? | Agent that completed |
| project | str? | Project path for scoping |

### 2.1 Agent Identity (`claimed_by` / `done_by`)

Format: `{client}:{session_id}` or `{client}:{session_id}:{agent_name}`

| Client | Example |
|--------|---------|
| Codex | `codex:5bc6858a-f775-4ed5-b757-bbc684c8af0d` |
| Claude Code | `claude-code:abc123` |
| Cursor | `cursor:067bf5cb0b14a175fea2065139a899df` |
| Sitback | `sitback:session_xyz` |

**Source:** MCP context `session_id`, or `SESSION_ID` env, or client-provided `--agent-id` when claiming. TUI and `thegent_queue_list` display `claimed_by` so user sees who is working on each item.

---

## 3. Components

### 3.1 MCP Tools (for Agent)

| Tool | Purpose |
|------|---------|
| `thegent_queue_list` | List items; filter by status. Shows `claimed_by`, `lease_expires_at`. |
| `thegent_queue_claim` | Claim next queued (or stale) item. Requires `agent_id` (from context or arg). Sets `claimed_by`, `lease_expires_at`. |
| `thegent_queue_done` | Mark item done. Only `claimed_by` can complete (else error or `--force`). |
| `thegent_queue_release` | Release item back to queued. Only `claimed_by` or `--force`. |
| `thegent_queue_extend_lease` | Extend lease_expires_at (optional; agent calls if long-running). |
| `thegent_queue_add` | Add item (agent or user via CLI). |
| `thegent_queue_edit` | Edit prompt (only if queued). |

### 3.2 CLI Commands (for User)

| Command | Purpose |
|---------|---------|
| `thegent queue tui` | TUI: add, edit, list with state + claimed_by. Release stuck items. |
| `thegent queue add "prompt"` | Add from CLI. |
| `thegent queue list [--status queued\|in_progress\|done]` | List items (shows claimed_by). |
| `thegent queue edit <id> "new prompt"` | Edit queued item. |
| `thegent queue release <id> [--force]` | Release in_progress back to queued (--force to override ownership). |
| `thegent queue status` | Summary (N queued, N in progress, N done). |

### 3.3 TUI (User-Facing)

**Tech:** Textual (Python) or Rich + simple input loop.

**Features:**
- **Add** — Type prompt, Enter to add
- **Edit** — Select queued item, edit prompt (only queued)
- **List** — Table: id, prompt (truncated), status, created_at
- **Refresh** — Auto-refresh every N seconds or on keypress
- **State** — Color: queued (yellow), in_progress (blue), done (green)

**Layout:**
```
┌─ Prompt Queue ───────────────────────────────────────────────────────────────┐
│ [A]dd  [E]dit  [X] release (stuck)  [R]efresh  [Q]uit                         │
├───────────────────────────────────────────────────────────────────────────────┤
│ id       │ prompt              │ status     │ claimed_by      │ created      │
│ q_abc123 │ Add tests for...     │ queued     │ —               │ 12:00        │
│ q_def456 │ Refactor login...    │ in_progress│ codex:sess_xyz  │ 12:01        │
│ q_ghi789 │ Update README        │ done       │ codex:sess_xyz  │ 12:02        │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Instruction

Agent (Codex, Claude Code, Cursor) needs to know to check the queue. Options:

### 4.1 System / Skill Instruction

Add to agent instructions (e.g. Codex skill, Claude Code project instructions):

```
Between tasks or when idle, check the prompt queue: call thegent_queue_list with status=queued.
If items exist, claim one with thegent_queue_claim, process it, then call thegent_queue_done.
```

### 4.2 MCP Resource

Expose `thegent://queue` resource — agent can read it. But tools are better for mutating state (claim, done).

### 4.3 Never-Idle Loop (Sitback Pattern)

Thegent Sitback Agent already has a "never-idle" loop. Extend it:

1. Check queue
2. If queued items, claim and process
3. Else, run other idle tasks (health, governance, etc.)

---

## 5. Multi-Agent Locking & Concurrency

**Requirement:** Multiple agents (Codex, Claude Code, Cursor, Sitback) can pull from the same queue. Must be clear who owns each item and prevent double-claim.

### 5.1 Lock Systems

| Mechanism | Purpose |
|-----------|---------|
| **Claim ownership** | `claimed_by` records which agent/session holds the item |
| **Lease (TTL)** | `lease_expires_at` = claimed_at + lease_duration (default 30 min). Stale locks can be reclaimed. |
| **Atomic claim** | Single read-modify-write under file lock; only one agent succeeds per item |
| **Done ownership** | Only `claimed_by` can call `thegent_queue_done` for that item (or allow override with flag) |

### 5.2 Claim Protocol

```text
1. Agent calls thegent_queue_claim (optional: --agent-id or from MCP context)
2. Server acquires file lock (fcntl.flock or filelock)
3. Read queue, find first status=queued (or oldest lease-expired in_progress)
4. If found:
   - Set status=in_progress
   - Set claimed_by=agent_id
   - Set claimed_at=now
   - Set lease_expires_at=now + 30min
   - Write queue
5. Release lock
6. Return item to agent
```

**Race:** Two agents claim simultaneously → file lock serializes; second agent gets next queued item (or none).

### 5.3 Stale Lock Recovery

Items in `in_progress` with `lease_expires_at` in the past are **stale** (agent crashed or left). Options:

| Option | Behavior |
|-------|----------|
| **Reclaim** | `thegent_queue_claim` can return stale items; new claim overwrites `claimed_by` |
| **Release** | `thegent_queue_release <id>` — agent or user explicitly releases; reverts to queued |
| **Auto-release** | Background job or on-next-claim: reset stale items to queued |

**Recommendation:** `thegent_queue_claim` considers stale items (lease_expired) as eligible for reclaim. New claimer becomes `claimed_by`.

### 5.4 Done, Release & Lease Extension Ownership

| Action | Rule |
|--------|------|
| `thegent_queue_done <id>` | Only `claimed_by` can mark done. Else: error "Item claimed by X; you are Y". |
| `thegent_queue_release <id>` | Only `claimed_by` can release. Or: `--force` for user/admin override. |
| `thegent_queue_extend_lease <id>` | Only `claimed_by` can extend; resets lease_expires_at by +30min. |
| Override | `thegent_queue_done <id> --force` — user can force completion (e.g. agent crashed) |

### 5.5 Edit & User Lock Interaction

- **Edit** only when status=queued (no agent holds it)
- User cannot edit in_progress (agent owns it)
- User can `thegent_queue_release <id> --force` to reclaim stuck items

### 5.6 File Locking

**Implementation:** Use `fcntl.flock(LOCK_EX)` on the queue file for any mutation (claim, done, release, add, edit). Read-only list can use `LOCK_SH` or no lock (eventual consistency acceptable for display).

**Alternative:** `filelock` (pip) or `portalocker` for cross-platform file locking.

### 5.7 Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `THGENT_QUEUE_LEASE_MINUTES` | 30 | Lease TTL for claimed items |
| `THGENT_QUEUE_PATH` | `.thegent/prompt_queue.jsonl` | Queue file path (relative to project or ~/.thegent) |

---

## 6. Implementation Plan

| Phase | Task | Effort |
|-------|------|--------|
| 1 | Queue storage: `PromptQueue` class, JSONL read/write | Small |
| 2 | MCP tools: list, claim, done, add, edit | Small |
| 3 | CLI: queue add, list, edit, status | Small |
| 4 | TUI: Textual app for add/edit/list with live state | Medium |
| 5 | Agent instruction: add to Codex skill / thegent docs | Small |
| 6 | Sitback integration: queue check in never-idle loop | Small |

---

## 7. Codex Integration

**Codex** (OpenAI) supports:
- MCP servers (thegent serve)
- Skills (`.codex/skills/`)
- Terminal TUI

**Skill for Codex:** Create `.codex/skills/thegent-queue/` (or add to existing thegent skill) with instructions to check thegent queue.

**TUI:** User runs `thegent queue tui` in a separate terminal — works with any agent (Codex, Claude Code, Cursor).

---

## 8. File Locations

| Path | Purpose |
|------|---------|
| `PROJECT_DIR/.thegent/prompt_queue.jsonl` | Project-scoped queue |
| `~/.thegent/prompt_queue.jsonl` | Global fallback when not in project |
| `PROJECT_DIR/.codex/skills/thegent-queue/` | Codex skill (optional) |

---

## 9. Summary

| Component | Purpose |
|-----------|---------|
| **Queue file** | JSONL with id, prompt, status, timestamps |
| **MCP tools** | Agent: list, claim, done, add, edit |
| **CLI** | User: add, list, edit, status |
| **TUI** | User: add/edit/list with live state view |
| **Agent instruction** | "Check queue between tasks" |

**Next step:** Implement Phase 1–3 (storage + MCP tools + CLI), then TUI.

---

## 10. Queue Design Patterns

### 10.1 Priority Queue Pattern

For tasks with different priority levels:

```jsonl
{"id":"q_prio_001","prompt":"Fix critical security vulnerability","priority":"critical","status":"queued","created_at":"2026-02-16T12:00:00Z"}
{"id":"q_prio_002","prompt":"Add feature X","priority":"high","status":"queued","created_at":"2026-02-16T12:01:00Z"}
{"id":"q_prio_003","prompt":"Update documentation","priority":"low","status":"queued","created_at":"2026-02-16T12:02:00Z"}
```

**Agent Claim Logic:**
```python
def claim_next(agent_id, min_priority=None):
    items = queue.list(status="queued")
    if min_priority:
        items = [i for i in items if PRIORITY_ORDER[i.priority] >= PRIORITY_ORDER[min_priority]]
    return items[0] if items else None
```

### 10.2 Work Stealing Pattern

Multiple agents can steal work from a shared queue:

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ Agent A (primary)  │     │ Agent B (stealer)   │     │ Agent C (stealer)   │
│ Claims: q_a001     │     │ Claims: q_b001      │     │ Claims: q_c001      │
│ Owned: q_a002      │     │ Owned: q_b002       │     │ Owned: q_c002       │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         │                           │                          │
         └───────────────────────────┴──────────────────────────┘
                                    │
                           ┌────────▼────────┐
                           │  Shared Queue   │
                           │ q_a001:claimed  │
                           │ q_a002:claimed  │
                           │ q_b001:claimed  │
                           │ q_b002:claimed  │
                           │ q_c001:claimed  │
                           │ q_c002:claimed  │
                           │ q_shared001    │◀── Can be stolen
                           │ q_shared002    │◀── Can be stolen
                           └────────────────┘
```

### 10.3 Batching Pattern

Process multiple items in a single session:

```python
def claim_batch(agent_id, batch_size=5):
    """Claim up to batch_size items for bulk processing."""
    batch = []
    for _ in range(batch_size):
        item = queue.claim(agent_id)
        if item:
            batch.append(item)
        else:
            break
    return batch


# Usage in agent:
batch = claim_batch(agent_id, batch_size=3)
for item in batch:
    process(item)
    queue.done(item.id)
```

### 10.4 Circuit Breaker Integration

Prevent queue flooding during system issues:

```python
class QueueCircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure = None

    def can_claim(self):
        if self.failure_count >= self.failure_threshold:
            if time() - self.last_failure > self.reset_timeout:
                self.failure_count = 0  # Reset
                return True
            return False
        return True

    def record_failure(self):
        self.failure_count += 1
        self.last_failure = time()

    def record_success(self):
        self.failure_count = 0
```

### 10.5 Dead Letter Queue (DLQ)

Handle failed items that cannot be processed:

```jsonl
{"id":"dlq_001","original_id":"q_failed123","prompt":"Complex refactor task","reason":"timeout","status":"dead_letter","failed_at":"2026-02-16T14:00:00Z","retry_count":3}
```

**DLQ Management:**
- Items moved to DLQ after `max_retries` failures
- DLQ reviewed weekly
- Items either: requeued with adjusted timeout, ignored, or escalated

### 10.6 Idempotent Claim Pattern

Ensure safe retry of claim operations:

```python
def claim_idempotent(queue_path, agent_id, item_id=None):
    """Claim with idempotency - safe to retry."""
    with file_lock(queue_path):
        queue = read_queue(queue_path)

        # Find item (by ID or first queued)
        item = find_item(queue, item_id) if item_id else find_first_queued(queue)

        if not item:
            return None

        # Check if already claimed by this agent (idempotent)
        if item.status == "in_progress" and item.claimed_by == agent_id:
            return item  # Already claimed, return existing

        if item.status == "in_progress" and item.claimed_by != agent_id:
            return None  # Claimed by another agent

        # Claim it
        item.status = "in_progress"
        item.claimed_by = agent_id
        item.claimed_at = now()
        item.lease_expires_at = now() + LEASE_DURATION

        write_queue(queue_path, queue)
        return item
```

---

## 11. Cross-References

| Topic | Reference |
|-------|-----------|
| Agent Orchestration | `docs/reference/AGENT_NEGOTIATION_ACL_DEPTH.md` |
| MCP Tools | `src/thegent/mcp_tools_modes.py` |
| Session Management | `src/thegent/orchestration/session.py` |
| Governance | `docs/governance/` |
| Planning Loop | `skills/sitback-agent/SKILL.md` |

---

## 12. Extension Summary

### Added in This Extension

| Section | Description |
|---------|-------------|
| **10. Queue Design Patterns** | Added priority queue, work stealing, batching, circuit breaker, DLQ, idempotent claim patterns |
| **11. Cross-References** | Added links to related documentation |

### Related Extensions

| File | Extension |
|------|-----------|
| `docs/architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md` | Compute offloading examples |
| `docs/research/API_CLI_DEVOPS_TOOLING.md` | CLI patterns for queue tools |
| `docs/research/CI_CD_DEVX_TOOLING.md` | CI/CD integration patterns |

---

## Appendix: Quick Reference

### MCP Tool Reference

| Tool | Parameters | Returns |
|------|------------|---------|
| `thegent_queue_list` | `[--status queued\|in_progress\|done]` | Array of queue items |
| `thegent_queue_claim` | `[--id <item_id>]` | Claimed item |
| `thegent_queue_done` | `<item_id>` | Success/failure |
| `thegent_queue_release` | `<item_id>` | Released item |
| `thegent_queue_add` | `"<prompt>"` | Created item |
| `thegent_queue_edit` | `<item_id> "<new_prompt>"` | Updated item |

### CLI Command Reference

| Command | Purpose |
|---------|---------|
| `thegent queue tui` | Launch TUI interface |
| `thegent queue add "task"` | Add task to queue |
| `thegent queue list` | List all items |
| `thegent queue status` | Show queue summary |
| `thegent queue purge --force` | Clear completed items |

---

**Document Version:** 1.1
**Last Updated:** 2026-02-17
**Extension:** Queue Design Patterns, Cross-References, Extension Summary

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added
- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions
- Implementation templates
- Configuration examples
- Best practices

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) - Queue design
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
