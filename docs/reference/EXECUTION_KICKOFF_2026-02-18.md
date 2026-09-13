# Execution Kickoff: Multi-Level Agent Coordination

**Date:** 2026-02-18 | **Status:** ACTIVE | **L1 Lead:** Claude Code
**Work Stream:** `docs/reference/WORK_STREAM.md` (canonical source of truth)

---

## Overview

This document activates the **3-level agent hierarchy** for parallel work execution:

```
┌─────────────────────────────┐
│  L1: Claude Code (Main)     │  ← Strategic decisions, blockers, dependencies
├─────────────────────────────┤
│  L2: Named Teammates (3)    │  ← Task claiming, component ownership, L3 delegation
├─────────────────────────────┤
│  L3: Thegent Agents (free)  │  ← Sub-task execution, exploration, implementation
└─────────────────────────────┘
```

---

## L2 Teammate Agents (Named)

### researcher-1

- **Role:** Discovery, analysis, research tasks
- **Component:** Phase 2 (Async State & Snapshots)
- **Capabilities:** Code exploration, file analysis, pattern discovery
- **Work Items:** TGNT-P2.1 → TGNT-P2.4
- **Cycle Time Target:** 5-15 min per item
- **Status:** IDLE → Ready to claim

**Claim Protocol:**

1. Read WORK_STREAM.md PENDING section for Phase 2
2. Pick highest-priority unclaimed item with met dependencies
3. Add to CLAIMED table: `| researcher-1 | TGNT-P2.X | In Progress | 2026-02-18 13:XX |`
4. Execute via `thegent free "Implement TGNT-P2.X: <description>"`
5. On completion, update WORK_STREAM.md: move from PENDING → COMPLETED
6. Return to step 1 until Phase 2 exhausted or blocker encountered

### builder-1

- **Role:** Feature implementation, core system building
- **Component:** Phase 3 (Caching & Metrics)
- **Capabilities:** System design, implementation, testing
- **Work Items:** TGNT-P3.1 → TGNT-P3.5
- **Cycle Time Target:** 8-20 min per item
- **Status:** IDLE → Ready to claim

**Claim Protocol:** (Same as researcher-1, but Phase 3 items)

### integrator-1

- **Role:** Integration, testing, coordination
- **Component:** Phase 4-5 (Intelligence & Context)
- **Capabilities:** Integration testing, E2E scenarios, validation
- **Work Items:** TGNT-P4._ → TGNT-P5._
- **Cycle Time Target:** 5-15 min per item
- **Status:** IDLE → Standby (unblock after Phase 2-3 complete)

**Trigger:** Activate when **both** Phase 2 AND Phase 3 have **≥50% completion**

---

## First Batch: Phase 2-3 Parallelization (NOW)

### Batch Summary

- **Duration:** ~25-40 min (both workers in parallel)
- **Goal:** Complete Phase 2 (Discovery) + Phase 3 (Building)
- **Independent:** Yes (no Phase 2 → Phase 3 dependencies)
- **Next Gate:** Check Phase 4 prerequisites before integrator-1 activation

### Phase 2: Async State & Snapshots (researcher-1)

| ID        | Title                                             | Depends On | Effort | Notes                                     |
| --------- | ------------------------------------------------- | ---------- | ------ | ----------------------------------------- |
| TGNT-P2.1 | Async state snapshots (jq serialization)          | TGNT-P0.4  | ~5min  | Use jq for JSON extraction + timestamps   |
| TGNT-P2.2 | State diff calculation (recursive, null handling) | TGNT-P2.1  | ~8min  | Detect changed fields, preserve structure |
| TGNT-P2.3 | State versioning (SHA256 hash per snapshot)       | TGNT-P2.1  | ~5min  | Unique version ID per state change        |
| TGNT-P2.4 | Timeline aggregation (reverse chronological)      | TGNT-P2.3  | ~5min  | Query capabilities: `state at <time>`     |

**Researcher Execution Flow:**

```
1. thegent free --do-next  # Auto-claim TGNT-P2.1
2. Implement async snapshots
3. Mark COMPLETED in WORK_STREAM
4. thegent free --do-next  # Auto-claim TGNT-P2.2
5. ... repeat for P2.3, P2.4
6. Check Phase 2 status: all COMPLETED? → Signal integrator-1 to standby
```

### Phase 3: Caching & Metrics (builder-1)

| ID        | Title                                              | Depends On            | Effort | Notes                                       |
| --------- | -------------------------------------------------- | --------------------- | ------ | ------------------------------------------- |
| TGNT-P3.1 | Rebuild strategy (invalidation heuristics)         | TGNT-P0.4             | ~8min  | When to invalidate entire cache vs partial  |
| TGNT-P3.2 | Partial rebuild (diff-aware re-execution)          | TGNT-P3.1             | ~10min | Only re-run affected downstream items       |
| TGNT-P3.3 | Preload optimization (predict hot keys)            | TGNT-P0.4             | ~8min  | Load likely-accessed entries at startup     |
| TGNT-P3.4 | Build timing (profile hot paths, cutoff threshold) | TGNT-P3.1, TGNT-P3.2  | ~5min  | Measure rebuild cost, skip if <10ms gain    |
| TGNT-P3.5 | Cache integration test (end-to-end scenario)       | TGNT-P3.1 → TGNT-P3.4 | ~10min | Verify cache improves harness speed by ≥20% |

**Builder Execution Flow:**

```
1. thegent free --do-next  # Auto-claim TGNT-P3.1
2. Implement rebuild strategy
3. Mark COMPLETED in WORK_STREAM
4. thegent free --do-next  # Auto-claim TGNT-P3.2
5. ... repeat for P3.3 → P3.5
6. Check Phase 3 status: all COMPLETED? → Signal completion to L1
```

---

## Execution Checklist

### Pre-Execution (L1 - This Step)

- [x] WORK_STREAM.md prepared with 186 tasks (all phases)
- [x] COORDINATION.md documents L1/L2/L3 workflows
- [x] AGENTS_ACTIVE.md created with team registry
- [x] Failure recovery playbook (10 scenarios)
- [x] Phase 2-3 work items identified (independent, no blocking)
- [ ] L2 teammates notified with claims protocol

### Execution (L2 - Parallel)

- [ ] researcher-1: Claim TGNT-P2.1
- [ ] builder-1: Claim TGNT-P3.1
- [ ] Both execute in parallel via `thegent free --do-next --repeat 5` (max 5 items each batch)
- [ ] L1 monitor: Check status every 5-10 min via AGENTS_ACTIVE.md updates

### Mid-Execution Gates (L1 - Monitoring)

- [ ] At ~10 min: At least 1 item completed by each worker
- [ ] At ~20 min: ≥50% of batch complete
- [ ] At ~30 min: Phase 2 complete OR blocker detected
- [ ] At ~35 min: Phase 3 complete OR blocker detected

### Post-Batch Validation (L1)

- [ ] All Phase 2 items in COMPLETED section
- [ ] All Phase 3 items in COMPLETED section
- [ ] Cycle time metrics recorded in AGENTS_ACTIVE.md
- [ ] Zero SLO breaches (no item >150% of estimate)
- [ ] Decide: Activate integrator-1 for Phase 4-5 OR pause for review

---

## Communication Protocol

### L2 → L1 (Status Updates)

- **Frequency:** Every 5-10 min OR when blocker encountered
- **Method:** Update AGENTS_ACTIVE.md (commit immediately)
- **Content:** Current task, progress %, blockers, ETA

### L2 ↔ L2 (Coordination)

- **Method:** WORK_STREAM.md dependency columns (read-only)
- **Resolve:** Only via L1 arbitration if circular depends detected
- **Avoid:** Direct messaging (use work stream as async protocol)

### L1 → L2 (Instructions)

- **Method:** Update this document (EXECUTION_KICKOFF) or COORDINATION.md
- **Frequency:** As needed (new blockers, priority changes, phase transitions)
- **Content:** New work assignments, blocker resolutions, next phase gates

### All → L1 (Escalation)

- **Trigger:** Blocker >5 min, SLO breach, dependency cycle, unknown error
- **Method:** Add to FAILED/BLOCKED section with evidence and decision point
- **Response Time:** L1 resolves within 2 min (add note to this document)

---

## Blocker Resolution Protocol

### If researcher-1 Blocked

**Scenario:** TGNT-P2.2 blocked on TGNT-P2.1 not complete yet

1. Check WORK_STREAM.md: Is TGNT-P2.1 COMPLETED?
2. If yes: Re-read dependencies, likely config issue → Escalate to L1
3. If no: TGNT-P2.1 not finished → Wait up to 5 min for researcher-1 to complete
4. After 5 min: L1 investigates researcher-1 session status

### If builder-1 Blocked

**Scenario:** TGNT-P3.5 blocked on TGNT-P3.4 not complete

(Same protocol as researcher-1)

### If Circular Dependency Detected

**Scenario:** A → B → C → A

1. STOP: Do not continue parallel work
2. L1 reads COORDINATION.md failure scenario FRP-3 (Circular Dependencies)
3. Re-plan: Break cycle, reassign work, unblock
4. Update WORK_STREAM.md with new order
5. Resume execution

---

## Success Criteria

### Batch Complete (Phase 2-3)

- ✅ All TGNT-P2.\* items in COMPLETED
- ✅ All TGNT-P3.\* items in COMPLETED
- ✅ Cycle time avg ≤ 12 min (target)
- ✅ SLO breaches: 0
- ✅ No unresolved blockers

### Quality Gates (Validation)

- ✅ Code follows thegent patterns
- ✅ Tests added for new code
- ✅ WORK_STREAM.md entries signed off (L1 approval)
- ✅ Documentation updated (docs/reference/ links)

---

## Next Steps (After Phase 2-3 Complete)

### Batch 2: Phase 4-5 Parallelization

- **Trigger:** Phase 2-3 both 100% complete
- **Workers:** researcher-1 (continues) + integrator-1 (new)
- **Duration:** ~30-45 min
- **Items:** TGNT-P4.1 → TGNT-P5.5 (30+ tasks)

### Phase Transition Gates

- **Phase 2 → 3:** Independent (parallel)
- **Phase 3 → 4:** Depends on P3.5 (integration test) ✓
- **Phase 4 → 5:** Depends on P4.4 (context merging) ✓
- **Phase 5 → 6:** Optional: Validate all Phase 5 tests pass

---

## Key Files & References

| Document                     | Purpose                      | Location          |
| ---------------------------- | ---------------------------- | ----------------- |
| WORK_STREAM.md               | Canonical task list          | `docs/reference/` |
| COORDINATION.md              | L1/L2/L3 workflows           | `docs/reference/` |
| AGENTS_ACTIVE.md             | Team registry & status       | `docs/reference/` |
| FAILURE_RECOVERY_PLAYBOOK.md | 10 failure scenarios         | `docs/reference/` |
| This Document                | Execution kickoff & protocol | `docs/reference/` |

---

## Metrics to Track

| Metric                  | Target            | Measured At          |
| ----------------------- | ----------------- | -------------------- |
| Cycle Time (avg)        | ≤ 12 min / item   | Per batch completion |
| SLO Compliance          | 100% (0 breaches) | Per batch completion |
| Task Completion Rate    | ≥ 95%             | Per phase completion |
| Blocker Resolution Time | ≤ 5 min           | Real-time            |
| Team Utilization        | ≥ 90%             | Per batch completion |

---

## Status & Timeline

| Phase               | Start            | Target Complete  | Actual | Status  |
| ------------------- | ---------------- | ---------------- | ------ | ------- |
| Phase 2-3 (Batch 1) | 2026-02-18 13:00 | 2026-02-18 13:40 | --     | ACTIVE  |
| Phase 4-5 (Batch 2) | 2026-02-18 13:45 | 2026-02-18 14:30 | --     | Pending |
| Phase 6+ (Batch 3+) | 2026-02-18 14:35 | 2026-02-18 16:00 | --     | Pending |

---

**Maintained By:** L1 (Claude Code)
**Version:** 1.0 | **Last Updated:** 2026-02-18 13:00 UTC
**Next Review:** Every 10 min during execution
