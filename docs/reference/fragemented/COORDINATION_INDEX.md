# Phase 6: Coordination Setup - Complete Index

**Status:** Complete | **Last Updated:** 2026-02-18 | **Total Documents:** 5

---

## Overview

This index documents the complete coordination framework for Phase 6, enabling multi-agent teams to work safely and efficiently on shared codebases.

### Documents Created

| Document                         | Size      | Purpose                                    | Status     |
| -------------------------------- | --------- | ------------------------------------------ | ---------- |
| **COORDINATION.md**              | 24 KB     | Three-level hierarchy, workflows, recovery | ✓ Complete |
| **AGENTS_ACTIVE.md**             | 8.5 KB    | Agent registry, team management            | ✓ Complete |
| **TUI_DASHBOARD_DESIGN.md**      | 34 KB     | Dashboard mockup, implementation plan      | ✓ Complete |
| **FAILURE_RECOVERY_PLAYBOOK.md** | 27 KB     | 10 FRP scenarios, decision tree            | ✓ Complete |
| **COORDINATION_INDEX.md**        | This file | Cross-reference and navigation             | ✓ Complete |

**Total:** 93.5 KB of coordination documentation

---

## Quick Navigation

### For Claude Code (L1 Coordinators)

**Getting Started:**

1. Read: [COORDINATION.md - Level 1 Section](COORDINATION.md#level-1-coordinator-claude-code)
2. Review: [AGENTS_ACTIVE.md - Team Composition Patterns](AGENTS_ACTIVE.md#team-composition-patterns)
3. Understand: [TUI_DASHBOARD_DESIGN.md - Overview](TUI_DASHBOARD_DESIGN.md#overview)

**Operational Tasks:**

- Creating a team → [COORDINATION.md - Team Coordination](COORDINATION.md#team-coordination)
- Assigning work → [AGENTS_ACTIVE.md - Commands](AGENTS_ACTIVE.md#commands-for-registry-management)
- Monitoring progress → [TUI_DASHBOARD_DESIGN.md - Full Dashboard](TUI_DASHBOARD_DESIGN.md#full-dashboard-layout-160x40-minimum)
- Resolving failures → [FAILURE_RECOVERY_PLAYBOOK.md - Decision Tree](FAILURE_RECOVERY_PLAYBOOK.md#recovery-decision-tree)

### For L2 Teammates (Named Agents)

**Getting Started:**

1. Read: [COORDINATION.md - Level 2 Section](COORDINATION.md#level-2-teammates-named-agents)
2. Learn: [COORDINATION.md - CLAIMED Workflow](COORDINATION.md#claimed-workflow)
3. Practice: [COORDINATION.md - COMPLETED Workflow](COORDINATION.md#completed-workflow)

**During Execution:**

- Finding work → `thegent plan do-next`
- Claiming task → [COORDINATION.md - CLAIMED Step 3](COORDINATION.md#3-agent-claims-item)
- Updating status → [COORDINATION.md - COMPLETED Step 4](COORDINATION.md#4-unblock-downstream-tasks)
- Reporting blockers → [COORDINATION.md - CLAIMED Workflow - Step 5](COORDINATION.md#5-commit--push)
- When stuck → [FAILURE_RECOVERY_PLAYBOOK.md - FRP-6](FAILURE_RECOVERY_PLAYBOOK.md#frp-6-slo-breach-task-running-10x-estimate)

### For L3 Thegent Agents

**Getting Started:**

1. Read: [COORDINATION.md - Level 3 Section](COORDINATION.md#level-3-thegent-agents-freepremium)
2. Understand: [AGENTS_ACTIVE.md - Agent Lifecycle States](AGENTS_ACTIVE.md#agent-lifecycle-states)

**During Execution:**

- Follow L2 instructions exactly
- Report results via file writes or stdout
- If stuck, escalate to L2 (don't make decisions)
- No independent work claiming

---

## Workflow Quick Reference

### CLAIMED Workflow (L2)

```
1. Read WORK_STREAM.md
2. Find task with Status=PENDING, Dependencies=met
3. Add to CLAIMED section with agent_id + timestamp
4. Change task Status from PENDING → CLAIMED
5. Commit & push immediately
6. Start work on task
```

📄 **Full details:** [COORDINATION.md - CLAIMED Workflow](COORDINATION.md#claimed-workflow)

### COMPLETED Workflow (L2)

```
1. Finish implementation, tests, docs
2. Remove from CLAIMED, add to COMPLETED
3. Update original task Status → COMPLETED
4. Update related trackers (PLAN_STATUS, CODE_ENTITY_MAP)
5. Commit & push
6. Move dependent tasks to available queue
```

📄 **Full details:** [COORDINATION.md - COMPLETED Workflow](COORDINATION.md#completed-workflow)

### Recovery Workflows (L1)

| Failure                     | Handler                            | Reference                                                                                     |
| --------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------- |
| Agent timeout               | Release task, force kill if needed | [FRP-1](FAILURE_RECOVERY_PLAYBOOK.md#frp-1-agent-crashtimeout-during-execution)               |
| Race condition              | Break tie, lock WORK_STREAM.md     | [FRP-2](FAILURE_RECOVERY_PLAYBOOK.md#frp-2-duplicate-task-claims-race-condition)              |
| Circular dependency         | Break cycle by redesign            | [FRP-3](FAILURE_RECOVERY_PLAYBOOK.md#frp-3-circular-dependencies)                             |
| File merge conflict         | Manual merge + verify              | [FRP-4](FAILURE_RECOVERY_PLAYBOOK.md#frp-4-file-conflict-multiple-agents-editing-same-file)   |
| Regression after completion | Reopen task, fix, test             | [FRP-5](FAILURE_RECOVERY_PLAYBOOK.md#frp-5-regression-after-completion)                       |
| SLO breach (10x estimate)   | Investigate, split, adjust         | [FRP-6](FAILURE_RECOVERY_PLAYBOOK.md#frp-6-slo-breach-task-running-10x-estimate)              |
| Git conflict in WORK_STREAM | Manual merge, prevent future       | [FRP-7](FAILURE_RECOVERY_PLAYBOOK.md#frp-7-git-conflict-in-work_streammd)                     |
| Blocker 30+ min             | Escalate dependency                | [FRP-8](FAILURE_RECOVERY_PLAYBOOK.md#frp-8-blocker-slo-breach-task-waiting-30-minutes)        |
| Permission/file lock error  | Fix perms, remove lock             | [FRP-9](FAILURE_RECOVERY_PLAYBOOK.md#frp-9-permissionfile-locking-issues)                     |
| No more work                | Verify complete, next phase        | [FRP-10](FAILURE_RECOVERY_PLAYBOOK.md#frp-10-work-stream-depletion-all-tasks-claimedcomplete) |

---

## File Locations

### Primary Coordination Files

```
docs/reference/
├── COORDINATION.md ..................... Three-level hierarchy & workflows
├── AGENTS_ACTIVE.md .................... Agent registry & team management
├── TUI_DASHBOARD_DESIGN.md ............. Dashboard mockup & implementation
├── FAILURE_RECOVERY_PLAYBOOK.md ........ 10 failure scenarios + recovery
├── COORDINATION_INDEX.md ............... This file (navigation)
└── WORK_STREAM.md ...................... Canonical work queue (read existing)
```

### Related Files (Reference)

```
docs/
├── reports/
│   └── PHASE_6_COMPLETION_SUMMARY.md .. (created when phase complete)
├── research/
│   └── CONVERSATION_DUMP_YYYY-MM-DD.md .. Key decisions & findings
└── reference/
    └── PLAN_STATUS.md .................. Phase tracking (update per task)
```

---

## Key Concepts

### Three-Level Coordination Model

```
Level 1 (L1)          Level 2 (L2)           Level 3 (L3)
Claude Code        Named Agents          Thegent Agents
└─ Strategy       └─ Component Owner   └─ Task Execution
└─ Decision Gates └─ Task Claiming     └─ Parallel Work
└─ Monitoring     └─ Quality Gates     └─ Background Work
└─ Escalation     └─ Delegation
```

**Read:** [COORDINATION.md - Overview](COORDINATION.md#overview)

### CLAIMED vs COMPLETED

- **CLAIMED:** Agent has registered intent to work (prevents duplicate effort)
- **COMPLETED:** Agent has finished, moved work product to COMPLETED section

**Read:** [COORDINATION.md - Workflows](COORDINATION.md#claimed-workflow)

### Dependency Management

- Tasks list `Depends On` column
- Circular dependencies detected & broken (FRP-3)
- Blockers auto-tracked and escalated if >15 min

**Read:** [FAILURE_RECOVERY_PLAYBOOK.md - FRP-8](FAILURE_RECOVERY_PLAYBOOK.md#frp-8-blocker-slo-breach-task-waiting-30-minutes)

---

## Operational Commands

### Work Stream Management

```bash
# Read current work
thegent plan do-next

# Claim a task (L2)
TaskUpdate taskId="TGNT-P6.1" status="in_progress" owner="dev-agent-1"

# Complete a task (L2)
TaskUpdate taskId="TGNT-P6.1" status="completed"

# Create new team (L1)
TeamCreate team_name="phase-6-team" description="Git Parallelism Phase"

# Message teammate (L1)
SendMessage type="message" recipient="dev-agent-1" \
  content="Task complete. Ready for next?"
```

### Monitoring

```bash
# Check agent status (L1)
thegent ps
thegent status {session_id}

# View full work stream
cat docs/reference/WORK_STREAM.md

# Check for blockers
grep "BLOCKED" docs/reference/WORK_STREAM.md

# Launch dashboard (when implemented)
thegent dashboard
```

### Troubleshooting

```bash
# Find stale agents
grep -E "CLAIMED|IN_PROGRESS" docs/reference/WORK_STREAM.md | awk '{print $(NF-1)}' | while read ts; do
  age=$(($(date +%s) - $(date -d "$ts" +%s)))
  if [ $age -gt 600 ]; then echo "STALE: $ts ($age sec)"; fi
done

# Check for race conditions (duplicate tasks)
grep "TGNT-P6.1" docs/reference/WORK_STREAM.md | wc -l

# Verify no circular dependencies
# (See FRP-3 for automated check)
```

---

## Dashboard Status

**Current Status:** Design Phase (Ready for MVP Implementation)

### Implementation Roadmap

| Phase             | Timeframe | Deliverable                                  | Owner |
| ----------------- | --------- | -------------------------------------------- | ----- |
| **Phase 1 (MVP)** | Week 1    | Basic dashboard (header + agents + blockers) | TBD   |
| **Phase 2**       | Week 2    | Extended views (workstream, blockers, stats) | TBD   |
| **Phase 3**       | Week 3    | Interactive features (claim, message, edit)  | TBD   |
| **Phase 4**       | Week 4    | Predictions & automation (ETA, auto-unblock) | TBD   |

📄 **Full details:** [TUI_DASHBOARD_DESIGN.md - Implementation Roadmap](TUI_DASHBOARD_DESIGN.md#implementation-roadmap)

---

## Decision Matrix

### When to Create a Team

| Scenario                              | Decision      | Effort     |
| ------------------------------------- | ------------- | ---------- |
| Single agent, simple task (1-2 files) | ❌ No team    | 5-15 min   |
| 2-3 agents, feature                   | ✓ Small team  | 30-45 min  |
| 4-6 agents, sprint                    | ✓ Medium team | 60-120 min |
| 7+ agents, major refactor             | ✓ Large team  | 120+ min   |

### When to Escalate to L1

| Issue                   | Escalate? | When?                     |
| ----------------------- | --------- | ------------------------- |
| Task estimate seems low | ⚠ Maybe  | If >100% and persistent   |
| Need another agent      | ✓ Always  | Ask L1 to allocate        |
| Change scope            | ✓ Always  | Don't unilaterally change |
| Circular dependency     | ✓ Always  | Can't break on own        |
| File conflict           | ⚠ Maybe  | Try manual merge first    |
| Blocker >15 min         | ✓ Always  | Report immediately        |

---

## Checklists

### Pre-Sprint (L1)

- [ ] Team created via `TeamCreate`
- [ ] Agents roster defined (names, roles, components)
- [ ] WORK_STREAM.md updated with phase tasks
- [ ] Dependencies verified (no cycles)
- [ ] Estimates reviewed (sanity check)
- [ ] Dashboard ready (or manual monitoring plan)

### Pre-Task (L2)

- [ ] Task dependencies are satisfied
- [ ] Task description is clear
- [ ] No other agent has claimed task
- [ ] Estimate seems reasonable
- [ ] Ready to commit first claim

### During Task (L2)

- [ ] Update CLAIMED section with timestamp
- [ ] Change task status to CLAIMED
- [ ] Commit & push immediately
- [ ] Send progress update every 10-15 min (for long tasks)
- [ ] Report blockers immediately

### Post-Task (L2)

- [ ] All tests passing
- [ ] Code lint clean
- [ ] Documentation updated
- [ ] Commit message references task ID
- [ ] Move to COMPLETED with duration
- [ ] Update related trackers
- [ ] Commit & push final state

### Phase Complete (L1)

- [ ] All tasks in COMPLETED section
- [ ] Quality gates passing (lint, tests, coverage)
- [ ] Phase summary document created
- [ ] Lessons learned documented
- [ ] Next phase work items created
- [ ] Commit everything and celebrate!

---

## Common Patterns & Anti-Patterns

### ✓ Good Patterns

| Pattern               | Example                          | Reference                                                                            |
| --------------------- | -------------------------------- | ------------------------------------------------------------------------------------ |
| Atomic CLAIMED update | Claim task, immediately commit   | [COORDINATION.md](COORDINATION.md#3-agent-claims-item)                               |
| Clear task ownership  | One agent per task               | [AGENTS_ACTIVE.md](AGENTS_ACTIVE.md#agent-lifecycle-states)                          |
| Explicit dependencies | All TGNT-P6.X specify Depends On | [COORDINATION.md](COORDINATION.md#overview)                                          |
| Fast recovery         | FRP procedures, auto-escalation  | [FAILURE_RECOVERY_PLAYBOOK.md](FAILURE_RECOVERY_PLAYBOOK.md)                         |
| Blocker visibility    | Dashboard shows blockers in red  | [TUI_DASHBOARD_DESIGN.md](TUI_DASHBOARD_DESIGN.md#3-blockers-section-always-visible) |

### ❌ Anti-Patterns

| Anti-Pattern               | Problem                      | Fix                               |
| -------------------------- | ---------------------------- | --------------------------------- |
| Manual WORK_STREAM updates | Race conditions              | Use TaskUpdate tool               |
| Claiming without commit    | Other agents don't see claim | Always commit immediately         |
| Hiding blockers            | Escalation delays            | Report immediately to L1          |
| Circular dependencies      | Deadlock                     | Break cycle with redesign (FRP-3) |
| No timestamps              | Can't detect staleness       | Always use ISO 8601 timestamps    |
| Soft estimates             | SLO breaches                 | +30% buffer for git/risky work    |

---

## Metrics & SLOs

### Task-Level SLOs

| Metric             | Target | Warning | Critical |
| ------------------ | ------ | ------- | -------- |
| Cycle Time         | 15 min | >20 min | >30 min  |
| SLO Adherence      | 100%   | >85%    | <70%     |
| Estimate Accuracy  | ±30%   | ±50%    | >50%     |
| Agent Utilization  | 60%+   | 30-60%  | <30%     |
| Blocker Resolution | <5 min | <15 min | >30 min  |

### Phase-Level SLOs

| Metric            | Target      | Warning | Critical |
| ----------------- | ----------- | ------- | -------- |
| Phase Completion  | On schedule | ±15%    | >±15%    |
| Test Coverage     | >=90%       | >=80%   | <80%     |
| Zero Regressions  | 0           | 1       | >1       |
| Quality Gate Pass | 100%        | >95%    | <95%     |

---

## Feedback & Improvements

### Report Issues

If you encounter a failure not covered by FRP-1 through FRP-10:

1. Document it: Create file `docs/research/UNCOVERED_FAILURE_SCENARIO.md`
2. Report it: Send message to L1 coordinator
3. Resolve it: Work with L1 to create recovery procedure
4. Update: Add new FRP section to playbook

### Suggest Improvements

Good places for improvements:

- Automation (reduce manual steps)
- Visibility (better metrics, clearer dashboards)
- Prevention (avoid failures before they happen)
- Recovery (faster MTTR for known failures)

---

## Version History

| Version | Date       | Changes                         | Status   |
| ------- | ---------- | ------------------------------- | -------- |
| 1.0     | 2026-02-18 | Initial coordination framework  | ✓ Active |
| 1.1     | TBD        | Dashboard MVP implementation    | Planned  |
| 2.0     | TBD        | Automated escalation & recovery | Planned  |

---

## Support & Escalation

**Questions about coordination?**
→ Read the relevant section in [COORDINATION.md](COORDINATION.md)

**How to handle a failure?**
→ Follow the decision tree in [FAILURE_RECOVERY_PLAYBOOK.md](FAILURE_RECOVERY_PLAYBOOK.md)

**Need to create a new team?**
→ See [AGENTS_ACTIVE.md - Team Composition Patterns](AGENTS_ACTIVE.md#team-composition-patterns)

**Want dashboard updates?**
→ Check [TUI_DASHBOARD_DESIGN.md](TUI_DASHBOARD_DESIGN.md)

**For everything else:**
→ Escalate to L1 Coordinator (Claude Code)

---

**Maintained By:** Phase 6 Coordination Leadership
**Last Updated:** 2026-02-18
**Next Review:** 2026-02-25
**Contact:** docs/reference/COORDINATION.md (L1 section)
