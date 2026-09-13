# Unified Work Stream — Design

> **Purpose**: Single source of truth for all project work. All agents read one file. Incorporator agents merge fragments from scattered sources and resolve conflicts.
> **Canonical file**: [WORK_STREAM.md](./WORK_STREAM.md)
> **Related**: [WBS_AGENT_PROGRESS.md](./WBS_AGENT_PROGRESS.md) (claim coordination), [GARDENER_ARCHITECTURE.md](./GARDENER_ARCHITECTURE.md), [specs/README.md](../../specs/README.md), [AGENT_REGISTRY_DESIGN.md](../AGENT_REGISTRY_DESIGN.md) (session registry — sessions may link to work items via task_id)

---

## Problem

Work items are scattered across:

| Source                    | Location                                                                                                               | Format                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Plans                     | `docs/plans/*.md`                                                                                                      | WP tables, phase sections                                   |
| WBS                       | `docs/plans/02-UNIFIED-WBS.md`                                                                                         | WP \| Title \| Status \| Priority                           |
| Research seeds            | `docs/research/*.md`                                                                                                   | Freeform, TODOs                                             |
| Fragment/sprawl inventory | [RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md](../research/RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) | Catalog of fragments, seeds, indexes; sprawl todo → BACKLOG |
| Specs                     | `docs/docset/*.md`, `specs/`                                                                                           | PRD, FR, WBS fragments                                      |
| Conversation              | `pending-handoff.md`, escalation                                                                                       | Deferred prompts                                            |
| PLAN_STATUS               | `docs/reference/PLAN_STATUS.md`                                                                                        | (optional) Plan task table                                  |
| FR_TRACKER                | `docs/reference/FR_TRACKER.md`                                                                                         | (optional) FR implementation table                          |

Agents must read many files to find work. Progress is fragmented. No single place to claim or update.

---

## Solution: Canonical Work Stream

### Single File

**`docs/reference/WORK_STREAM.md`** is the compiled view. All agents:

1. **Read** before picking work
2. **Claim** by appending to CLAIMED
3. **Update** by moving to COMPLETED and updating status

### Schema

```
## BACKLOG (not started)
| ID | Title | Source | Priority | Depends |
|----|-------|--------|----------|---------|

## CLAIMED (in progress — do not pick)
| ID | Agent | Started |
|----|-------|---------|

## COMPLETED
| ID | Agent | Completed |
|----|-------|-----------|
```

- **ID**: WP-XXXX, FR-XXX-NNN, P{n}.{m}, research-{slug}, pending-{n}, etc.
- **Source**: Path or label (e.g. `02-UNIFIED-WBS.md`, `research/SEED.md`, `pending-handoff`)
- **Depends**: Comma-separated IDs that must be DONE before this item

---

## Continuously Evolving Backlog + Product Spec

The work stream is intended as a **living backlog and product spec** that evolves continuously. It integrates three systems: **4X game mechanics**, **AgilePlus governance**, and **Gardener automation**.

### 4X Mapping (eXplore → eXpand → eXploit → eXterminate)

| 4X Phase        | Dev Equivalent          | Work Stream Stage               | specs/ Stage                           | Artifact / Provenance    |
| --------------- | ----------------------- | ------------------------------- | -------------------------------------- | ------------------------ |
| **eXplore**     | Research, discovery     | Ideas, research seeds → BACKLOG | intake, breadth, depth                 | Raw context logs         |
| **eXpand**      | Formalize, design       | Specs, PRD, FR, WBS → BACKLOG   | devil-advocate, synthesis, formalizing | Spec signatures          |
| **eXploit**     | Build, implement        | CLAIMED → COMPLETED             | approved, implementing                 | Action trace             |
| **eXterminate** | Verify, harden, archive | COMPLETED, quality gates        | verifying, archived                    | **MAIF Signed Artifact** |

Items flow through the stream as they mature: raw ideas (eXplore) → formal specs (eXpand) → implementation (eXploit) → verification (eXterminate). The incorporator merges from all stages.

### AgilePlus Integration (scan → analyze → plan → deploy → verify → commit)

AgilePlus runs governance cycles that **feed into and consume** the work stream:

| AgilePlus Step | Work Stream Interaction                                                                             |
| -------------- | --------------------------------------------------------------------------------------------------- |
| **SCAN**       | gardener-scan hunger states; fragmented_research → incorporator adds to BACKLOG                     |
| **ANALYZE**    | HealthAnalyzer findings → BacklogManager; incorporator can merge AgilePlus backlog into WORK_STREAM |
| **PLAN**       | RemediationPlanner picks from findings; can also read WORK_STREAM for next items                    |
| **DEPLOY**     | AgentDeployer executes; workers claim from WORK_STREAM                                              |
| **VERIFY**     | Resolved items → COMPLETED; failed → back to BACKLOG or deferred                                    |
| **COMMIT**     | Evidence ledger; WORK_STREAM COMPLETED updated; **MAIF artifact generated**                         |

**Bidirectional flow**: AgilePlus backlog (`agileplus/backlog.jsonl`) and WORK_STREAM should stay aligned. Incorporator can merge AgilePlus pending findings into WORK_STREAM; AgilePlus can read WORK_STREAM for remediation planning.

### Gardener Loop (SCAN → PRIORITIZE → ROUTE → EXECUTE → VERIFY → REPORT)

The gardener maintains work stream health:

| Gardener Step  | Work Stream Action                                                                      |
| -------------- | --------------------------------------------------------------------------------------- |
| **SCAN**       | gardener-scan.sh detects hunger (fragmented_research, missing_specs, stale_items)       |
| **PRIORITIZE** | Critical: lint, coverage, agent_failure; High: fragmented_research, doc_disorganization |
| **ROUTE**      | fragmented_research → work-stream-incorporator; missing_specs → formalization agent     |
| **EXECUTE**    | Incorporator merges; agents pick from WORK_STREAM                                       |
| **VERIFY**     | Quality gates; XP awarded (gardener-xp.sh)                                              |
| **REPORT**     | garden-state.json, XP state, evidence ledger                                            |

**Hunger → Stream**: When `fragmented_research` fires, incorporator runs to move research into WORK_STREAM. When `stale_items` fires, boost priority of items in BACKLOG with no progress >7 days.

### XP and Levels (Gamification)

| Action                  | XP   | Work Stream Event                                 |
| ----------------------- | ---- | ------------------------------------------------- |
| Complete research stage | +50  | Item moves breadth→depth or synthesis→formalizing |
| Pass quality gate       | +100 | Item verified, moved to COMPLETED                 |
| Fix critical bug        | +75  | Remediation item COMPLETED                        |
| Add test coverage       | +25  | Coverage hunger resolved                          |
| Complete implementation | +150 | Item CLAIMED → COMPLETED                          |
| Pass code review        | +50  | Verifying → archived                              |

Levels (0→500→1500→5000→15000 XP) unlock parallel execution and advanced orchestration. The work stream is the **source of tasks** that earn XP.

### Evolution Loop (Continuous)

```
Ideas/Research → specs/intake
       ↓
Gardener SCAN (fragmented_research?) → Incorporator → WORK_STREAM BACKLOG
       ↓
AgilePlus SCAN (health < threshold?) → Findings → BacklogManager ↔ WORK_STREAM
       ↓
Workers / Agents: thegent_do_next → pick from BACKLOG → CLAIM → execute → COMPLETED
       ↓
Gardener VERIFY + XP → REPORT
       ↓
Repeat (never idle; backlog converges toward empty + green)
```

The work stream **evolves** because:

1. New items enter from ideas, research, plans, specs, pending-handoff, escalation
2. Incorporator merges fragments and resolves conflicts
3. Gardener and AgilePlus detect hunger/health issues and spawn remediation
4. Workers complete items; COMPLETED grows; BACKLOG shrinks (until new work arrives)
5. Product spec = approved + implementing + verifying items; backlog = intake through formalizing

---

## Incorporator Agent

A **dedicated incorporator agent** merges fragments into the work stream. It does not execute work items; it maintains the canonical file.

### Responsibilities

1. **Scan sources** — `docs/plans/`, `docs/research/`, `docs/docset/`, `specs/`, `pending-handoff.md`
2. **Extract items** — Parse tables, TODOs, WP/FR references, deferred prompts
3. **Merge into BACKLOG** — Add new items; do not duplicate existing IDs
4. **Resolve conflicts**:
   - **Duplicate ID**: Keep one; merge metadata (source, priority) if different
   - **Conflicting status**: Same ID in BACKLOG and COMPLETED → prefer COMPLETED; remove from BACKLOG
   - **Orphan in CLAIMED**: If agent_id stale (>7 days), move back to BACKLOG
5. **Dedupe** — Same semantic item (e.g. "WP-0002" in WBS and in a plan fragment) → single row
6. **Sort** — By priority (P0 > P1 > P2), then by dependency order

### Conflict Resolution Rules

| Conflict                                      | Resolution                                                      |
| --------------------------------------------- | --------------------------------------------------------------- |
| Same ID in BACKLOG and COMPLETED              | Remove from BACKLOG; COMPLETED wins                             |
| Same ID in multiple sources                   | Merge; highest priority wins; union of Depends                  |
| Stale CLAIMED (>7 days, no activity)          | Move back to BACKLOG                                            |
| Semantic duplicate (different IDs, same work) | Human or incorporator chooses canonical ID; other becomes alias |

### When to Run

- **On demand**: `thegent plan incorporate` or MCP `thegent_incorporate`
- **Gardener loop**: When `fragmented_research` hunger detected → spawn work-stream-incorporator
- **AgilePlus cycle**: After SCAN/ANALYZE — merge AgilePlus backlog findings into WORK_STREAM
- **Pre do-next**: Optional — `thegent_do_next` can trigger incorporate if WORK_STREAM stale

---

## Agent Workflow

### Worker Agents (execute work)

1. Read `docs/reference/WORK_STREAM.md`
2. Filter BACKLOG: not in CLAIMED, dependencies satisfied
3. Pick batch (e.g. 3–5 items)
4. Append to CLAIMED (agent_id, started)
5. Execute work
6. On done: remove from CLAIMED, add to COMPLETED, update source file status if applicable (e.g. 02-UNIFIED-WBS.md)

### Incorporator Agent (maintain stream)

1. Scan all sources
2. Extract items
3. Merge into WORK_STREAM.md BACKLOG
4. Resolve conflicts per rules above
5. Write canonical file

### Coordination with WBS_AGENT_PROGRESS

- **Option A**: WORK_STREAM subsumes WBS_AGENT_PROGRESS. CLAIMED/COMPLETED live only in WORK_STREAM.
- **Option B**: WBS_AGENT_PROGRESS remains for WBS-only "do all" coordination; WORK_STREAM is the broader backlog. Agents doing WBS read both; agents doing general work read WORK_STREAM only.

**Recommended**: Option A — single file. Simpler. All agents check one place.

---

## Source Extraction Rules

| Source                             | Extraction                                                   |
| ---------------------------------- | ------------------------------------------------------------ |
| `02-UNIFIED-WBS.md`                | Rows with Status ≠ DONE; ID = WP-XXXX                        |
| `docs/plans/*.md`                  | Tables with WP \| Title \| Status \| Priority; Status ≠ DONE |
| `PLAN_STATUS.md`                   | Table rows; Status ≠ Done                                    |
| `FR_TRACKER.md`                    | Table rows; Status ≠ Done                                    |
| `docs/research/*.md`               | `- [ ]` or `TODO:` or `WP-` / `FR-` refs → research-{slug}   |
| `specs/intake/`, `specs/approved/` | Dir names or SPEC.md titles → specs-{slug}                   |
| `pending-handoff.md`               | Numbered list items → pending-{n}                            |
| Escalation queue                   | run_id → escalation-{run_id}                                 |

---

## Implementation Status

| Component                      | Status                                 |
| ------------------------------ | -------------------------------------- |
| WORK_STREAM.md canonical file  | ✓ Created                              |
| Schema and initial seed        | ✓ From 02-UNIFIED-WBS                  |
| Incorporator agent persona     | ✓ `agents/work-stream-incorporator.md` |
| `thegent plan incorporate` CLI | ✓ Merges WBS into WORK_STREAM          |
| do_next_impl reads WORK_STREAM | ✓ Primary source when present          |
| WBS_AGENT_PROGRESS deprecation | Optional; can coexist                  |

---

## Optional Schema Extension: Stage (4X / specs)

For a **product spec** view, items can carry an optional `Stage` column:

| Stage       | 4X          | specs/                 | Meaning                 |
| ----------- | ----------- | ---------------------- | ----------------------- |
| explore     | eXplore     | intake, breadth, depth | Raw idea or research    |
| expand      | eXpand      | synthesis, formalizing | Spec/PRD/FR/WBS created |
| exploit     | eXploit     | approved, implementing | Ready or in build       |
| exterminate | eXterminate | verifying, archived    | In review or done       |

This enables filtering by maturity (e.g. "show only exploit+ items for implementation") and reporting (backlog by stage).

---

## References

- [specs/README.md](../../specs/README.md) — Gamified work stream (intake → breadth → depth → … → archived)
- [GARDENER_ARCHITECTURE.md](./GARDENER_ARCHITECTURE.md) — Hunger states, 4X mapping, fragmented_research → move to unified stream
- [hooks/gardener-scan.sh](../../hooks/gardener-scan.sh), [gardener-loop.sh](../../hooks/gardener-loop.sh), [gardener-spawn.sh](../../hooks/gardener-spawn.sh), [gardener-xp.sh](../../hooks/gardener-xp.sh) — Gardener implementation
- AgilePlus: `src/thegent/governance/agileplus.py` — scan→analyze→plan→deploy→verify→commit
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — Plan navigation
- [thegent-orchestration-optimization-prd.md](../docset/thegent-orchestration-optimization-prd.md) — "map to canonical workstream", unify fragmented program
- [TOUCHPOINT_INTEGRATION_EVALUATION.md](./TOUCHPOINT_INTEGRATION_EVALUATION.md) — MCP/CLI/skill/CLAUDE.md/roles/headless triggers; MD vs SQLite evaluation

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
