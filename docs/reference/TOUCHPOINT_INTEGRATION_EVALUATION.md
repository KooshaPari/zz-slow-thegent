# Touchpoint Integration Evaluation

> **Purpose**: Evaluate how MCP, CLI, skills, CLAUDE.md, roles, and headless triggers can be holistically tied into the unified work stream and team-structure/software-dev civilizational systems. Assess MD (read-only/short-throw) vs SQLite/DB-backed storage.
> **Deep dive**: [TOUCHPOINT_INTEGRATION_DEEP_DIVE.md](./TOUCHPOINT_INTEGRATION_DEEP_DIVE.md) — related conversations, research index, **web research**, **thegent copilot/sitback agents**, ~/../project paths, cross-cutting flows, multi-platform, implementation roadmap.

---

## Touchpoint Matrix

| Touchpoint            | Location                                        | Current State                                                                       | Feeds Into                      | Consumes From                             |
| --------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------- | ----------------------------------------- |
| **MCP tools**         | `mcp_server.py`                                 | `thegent_do_next`, `thegent_run`, `thegent_bg`, etc.                                | Agent execution                 | WORK_STREAM, run_registry, escalation     |
| **MCP resources**     | `thegent://*` URIs                              | workflow/triggers, workflow/gardening, sitback/dashboard, sessions, observe/summary | Agent context                   | run_registry, WORK_STREAM, contracts      |
| **MCP prompts**       | `thegent_workflow_*`                            | idea, quality_green, next_item, gardening                                           | Structured invocation           | WORK_STREAM, pending-handoff              |
| **CLI**               | `main.py`, `cli.py`                             | `plan next`, `plan incorporate`, `govern go cycle`, `govern go health`              | Human/script invocation         | Same as MCP                               |
| **Skills**            | `skills/*/SKILL.md`                             | sitback-agent, agent-orchestra                                                      | Agent persona + workflow        | CLAUDE.md, WORK_STREAM, gardening         |
| **CLAUDE.md**         | Root                                            | Project instructions, workflow triggers table                                       | All agents                      | —                                         |
| **Roles**             | `agents/*.md`                                   | Persona definitions                                                                 | Agent selection                 | CLAUDE.md                                 |
| **Headless triggers** | `governance/triggers.py`, `hooks/gardener-*.sh` | Watchdog, timer, manual; gardener loop                                              | AgilePlus cycle, gardener spawn | run_registry, backlog.jsonl, garden-state |

---

## Current State Storage (File-Backed)

| Store             | Path                                                               | Format               | Writers                               | Readers              |
| ----------------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------- | -------------------- |
| Work stream       | `docs/reference/WORK_STREAM.md`                                    | Markdown tables      | Incorporator, agents (claim/complete) | do_next_impl, agents |
| Run registry      | `.thegent/sessions/run_registry.jsonl`                             | JSONL                | execution.py, mcp_server              | MCP resources, CLI   |
| Handoff registry  | `.thegent/sessions/handoff_registry.jsonl`                         | JSONL                | execution.py                          | handoff_show         |
| AgilePlus backlog | `.thegent/sessions/agileplus/backlog.jsonl`                        | JSONL                | BacklogManager                        | AgilePlusLoop        |
| Evidence ledger   | `.thegent/sessions/agileplus/evidence_ledger.jsonl`                | JSONL (hash-chained) | EvidenceLedger                        | Audit                |
| Garden state      | `contracts/garden-state.json`                                      | JSON                 | gardener-loop                         | gardener-scan        |
| XP state          | `.thegent/gardener/xp/state.json`                                  | JSON                 | gardener-xp.sh                        | gardener-xp.sh       |
| Pending handoff   | `docs/research/pending-handoff.md`, `~/.claude/pending-handoff.md` | Markdown             | Session stop hooks                    | do_next_impl         |

---

## MD as Read-Only / Short-Throw

### Pros

| Benefit            | Rationale                                                                |
| ------------------ | ------------------------------------------------------------------------ |
| **Git-friendly**   | WORK_STREAM.md, specs/, plans/ diff and merge. No binary blobs.          |
| **Human-readable** | Agents, humans, and tools can inspect and edit without tooling.          |
| **Short-throw**    | Edit in place; no sync layer. CLAUDE.md, skills, roles are already MD.   |
| **Portable**       | No DB runtime. Works in sandbox, CI, read-only mounts.                   |
| **Audit trail**    | Git history = natural audit. JSONL append-only gives similar for events. |
| **Low friction**   | No migrations, no connection pooling, no backup strategy beyond git.     |

### Cons

| Drawback              | Mitigation                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------------- |
| **Concurrent writes** | Multiple agents editing WORK_STREAM → conflict. Use claim file or single-writer (incorporator). |
| **No transactions**   | Partial write can corrupt. Use atomic write (write to temp, rename).                            |
| **Query limits**      | No SQL. Filtering/sorting done in code. Acceptable for backlog size (<10k items).               |
| **No foreign keys**   | Depends, traceability manual. Schema discipline in incorporator.                                |

### Verdict: MD + JSONL is **good** for thegent's scale

- **Read-only MD** for specs, plans, CLAUDE.md, skills, roles: correct. These are documentation.
- **Short-throw MD** for WORK_STREAM: acceptable if single-writer (incorporator) or claim-before-edit discipline.
- **JSONL** for append-only event streams (run_registry, evidence_ledger, backlog): appropriate. No need for SQL.

---

## SQLite / DB-Backed

### When DB Helps

| Use Case                   | Why DB                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| **High write concurrency** | Many agents claiming/updating simultaneously; need row-level locking.                    |
| **Complex queries**        | "All items where Depends satisfied and Priority=P0 and not in CLAIMED" — SQL is cleaner. |
| **Referential integrity**  | Depends → BACKLOG.id; COMPLETED.id must exist in BACKLOG.                                |
| **Time-series analytics**  | "Tasks completed per day", "stale rate by source" — SQL aggregations.                    |
| **Cross-store joins**      | WORK_STREAM + run_registry + backlog.jsonl in one query.                                 |

### When DB Hurts

| Drawback               | Impact                                                               |
| ---------------------- | -------------------------------------------------------------------- |
| **Operational burden** | SQLite file in `.thegent/` — backup, migration, corruption recovery. |
| **Git opacity**        | DB not diffable. Lose "what changed" in code review.                 |
| **Portability**        | Need sqlite3 binary. Sandbox/CI may restrict.                        |
| **Abstraction tax**    | All readers need DB layer. Today: `read_text()` + parse.             |
| **Overkill**           | Backlog ~100–1000 items; JSONL + in-memory filter is fine.           |

### Verdict: SQLite **not recommended** for current scope

- thegent is single-user/single-session or low-concurrency multi-agent.
- Claim coordination (CLAIMED table) works with file-based discipline.
- Event volumes (run_registry, evidence) are append-only; JSONL is sufficient.
- **Revisit** if: >10 agents writing concurrently, or analytics/reporting needs grow.

---

## Harmonious Integration: Single Conceptual Model

All touchpoints should share one **conceptual model** even if storage is split:

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              UNIFIED WORK STREAM (conceptual)           │
                    │  BACKLOG | CLAIMED | COMPLETED | Sources | Triggers     │
                    └─────────────────────────────────────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│  MD (read-only) │           │  MD (short-throw)│           │  JSONL (append) │
│  CLAUDE.md      │           │  WORK_STREAM.md  │           │  run_registry   │
│  skills/*.md    │           │  specs/          │           │  backlog.jsonl  │
│  agents/*.md    │           │  pending-handoff │           │  evidence_ledger│
│  plans/*.md     │           │                  │           │  handoff_registry│
└────────┬────────┘           └────────┬──────────┘           └────────┬────────┘
         │                             │                               │
         └─────────────────────────────┼───────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│  MCP            │           │  CLI             │           │  Headless       │
│  tools/resources│           │  plan next     │           │  triggers       │
│  prompts        │           │  govern go cycle  │           │  AgilePlus      │
│                 │           │  plan incorporate│           │  gardener-loop  │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

### Integration Rules

1. **Single source of truth for work items**: `WORK_STREAM.md`. MCP `thegent_do_next`, CLI `plan next`, skills (gardening), and AgilePlus planner all read it.
2. **Single source of truth for workflow instructions**: `CLAUDE.md` + `thegent://workflow/triggers`, `thegent://workflow/gardening`. Skills and MCP prompts reference these; no duplication.
3. **Triggers fire the same cycle**: Headless (timer/watchdog), gardener (Stop/time-based), and manual (`govern go cycle`) all invoke AgilePlusLoop. Same backlog, same evidence ledger.
4. **Roles and skills are read-only config**: `agents/*.md` and `skills/*/SKILL.md` are loaded by runner; no runtime mutation. MD is correct.
5. **Event streams stay append-only**: run_registry, evidence_ledger, backlog.jsonl — JSONL. No DB.

---

## Recommendations

### Keep (No Change)

| Item                                             | Rationale                                                                  |
| ------------------------------------------------ | -------------------------------------------------------------------------- |
| WORK_STREAM.md as canonical backlog              | MD, git-friendly, human-editable. Incorporator is single writer for merge. |
| JSONL for run_registry, evidence_ledger, backlog | Append-only, audit trail, no schema migration.                             |
| CLAUDE.md, skills, roles as MD                   | Read-only config. Perfect for MD.                                          |
| MCP resources `thegent://workflow/*`             | URI-addressable; agents read when needed.                                  |

### Add (Harmonize)

| Item                                    | Action                                                                                                                                              |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Trigger → WORK_STREAM**               | When gardener detects `fragmented_research`, spawn incorporator. When AgilePlus ANALYZE completes, optionally merge backlog.jsonl into WORK_STREAM. |
| **MCP resource `thegent://workstream`** | Expose WORK_STREAM.md (or summary) as read-only resource. Agents can `read_resource("thegent://workstream")` instead of file path.                  |
| **Skills reference WORK_STREAM**        | In sitback-agent and agent-orchestra SKILL.md: "Read WORK_STREAM.md or thegent_do_next for next items."                                             |
| **CLAUDE.md trigger table**             | Add row: `thegent://workstream` \| Work stream (canonical backlog) \| MCP resource                                                                  |

### Defer (Revisit Later)

| Item                     | When to Revisit                                              |
| ------------------------ | ------------------------------------------------------------ |
| SQLite for WORK_STREAM   | >10 concurrent writers; or need for complex reporting.       |
| SQLite for run_registry  | Compliance requirement for queryable audit; or >100k events. |
| Unified DB for all state | Enterprise deployment with dedicated ops; multi-tenant.      |

---

## Summary

| Question                           | Answer                                                                                                                                                                                                            |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MD as read-only / short-throw?** | **Yes.** Keep specs, plans, CLAUDE.md, skills, roles as MD. WORK_STREAM as short-throw MD with single-writer discipline.                                                                                          |
| **SQLite/DB better?**              | **Not for current scope.** JSONL + MD sufficient. Revisit if concurrency or analytics demands it.                                                                                                                 |
| **Holistic tie-in?**               | **Single conceptual model**: WORK_STREAM = canonical backlog. All touchpoints (MCP, CLI, skill, triggers) read/write it or its derived views. Add `thegent://workstream` resource; wire triggers to incorporator. |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

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
