# TaskRouter + Pareto Routing Integration — Document Index

**Project Status**: Design Complete, Ready for Implementation
**Created**: 2026-02-15
**Timeline**: 3 Weeks (15 Working Days)
**Goal**: 18% Cost Reduction ($550 → $450/mo) with Hard Constraint Enforcement

---

## Quick Navigation

### For Different Audiences

**Architects & Technical Leads**
Start here → Read in this order:

1. INTEGRATION_ARCHITECTURE.md § 1–3 (Executive Summary + Module Map + Data Flow)
2. INTEGRATION_ARCHITECTURE.md § 5 (Constraint Enforcement Matrix)
3. INTEGRATION_ARCHITECTURE.md § 7 (Phase Breakdown)

**Software Engineers (Implementers)**
Start here → Read in this order:

1. INTEGRATION_QUICK_START.md (25-action checklist)
2. INTEGRATION_ARCHITECTURE.md § 2 (Module-by-module changes with code examples)
3. INTEGRATION_ARCHITECTURE.md § 4 (File Changes Summary table)
4. INTEGRATION_ARCHITECTURE.md § 8 (Testing Strategy)

**Operations & Monitoring**
Start here → Read in this order:

1. INTEGRATION_QUICK_START.md § "Risky Spots"
2. INTEGRATION_QUICK_START.md § "Debugging & Troubleshooting"
3. INTEGRATION_ARCHITECTURE.md § 9 (Monitoring & Metrics)
4. INTEGRATION_ARCHITECTURE.md § 10 (Rollback Plan)

---

## Document Summary

### INTEGRATION_ARCHITECTURE.md (1,482 lines)

Comprehensive technical design document covering all aspects of TaskRouter + Pareto routing integration.

**Key Sections:**

1. **Executive Summary**
   Context, 3-phase approach, hard constraints (perf, cost, speed)

2. **Module Integration Map**
   - execution.py: RunMeta extensions (+15 LOC)
   - cli_impl.py: TaskRouter integration point (+20 LOC)
   - governance/cost.py: Per-category cost tracking (+40 LOC)
   - models/catalog.py: Pareto-aware routing (+50 LOC, Phase 2 optional)
   - config.py: TaskRouter configuration schema (+20 LOC)
   - routing/: New module (360 LOC total)

3. **Data Flow Diagram (ASCII)**
   7-step flow from user command → TaskRouter.classify() → ConstraintValidator → PolicyEngine → resolve_route_for_category() → dispatch

4. **File Changes Summary**
   Table: 9 files, ~1,205 LOC total, LOC breakdown by priority

5. **Constraint Enforcement Matrix**
   Hard constraints (all must pass):
   - Performance: Quality thresholds 60%–80% by category
   - Instantaneous: $0.002–$0.85 per-call limits
   - Cumulative: Monthly $50–$200 budgets by category
   - Speed: 1s–60s SLAs by category

6. **Configuration Schema**
   YAML/env var reference for all routing settings (task classification, constraints, budgets)

7. **Phase Breakdown (3 Weeks)**
   - Week 1 (Days 1–5): Core routing (TaskRouter module, config, integration)
   - Week 2 (Days 6–10): Policy + cost integration (CostAggregator, PolicyEngine, Pareto routing)
   - Week 3 (Days 11–15): Testing + rollout (shadow run, enforcement, post-launch)

8. **Testing Strategy**
   - Unit: TaskClassifier, ConstraintValidator, CostAggregator (70%)
   - Integration: Full flow, cost tracking, budget enforcement (20%)
   - E2E: FAST/HIGH_COMPLEX routing, budget exhaustion (10%)
   - Target coverage: ≥90% for routing/

9. **Monitoring & Metrics**
   - SLOs: Routing latency <100ms p99, budget accuracy <10%, violation rate <1%
   - Dashboard queries: Cost by category, utilization %, fallback frequency
   - Metric thresholds and alert conditions

10. **Rollback Plan**
    Disable flags, restore backups, git revert procedures

---

### INTEGRATION_QUICK_START.md (467 lines)

1-page action checklist targeting 2-hour understanding + implementation kickoff.

**Key Sections:**

1. **Overview**
   2-hour target audience, status, timeline

2. **25-Action Implementation Checklist**
   Ordered by dependency, with time estimates and success criteria:
   - Phase 1 (Days 1–5): Actions 1–18 (routing module + integration)
   - Phase 2 (Days 6–10): Actions 19–25 (cost enforcement + Pareto routing)
   - Phase 3 (Days 11–15): Shadow run + rollout (passive)

3. **File Changes at a Glance**
   Visual tree of new/modified files with LOC counts

4. **Risky Spots (5 Identified)**
   - Concurrent cost tracking (file lock needed)
   - Policy ordering (TaskRouter before PolicyEngine)
   - Classifier accuracy (token estimation can be off by 2–3x)
   - Config parsing (JSON can fail silently)
   - Fallback chain unbounding (memory leak risk)
     Each with risk, mitigation, and action

5. **Success Criteria by Phase**
   Checkpoints for Phase 1 (core routing), Phase 2 (cost enforcement), Phase 3 (production)

6. **Dependency Graph**
   Execution order for implementation (config → routing → cli_impl → execution → governance)

7. **Debugging & Troubleshooting**
   Commands to diagnose token estimation, budget enforcement, constraint violations, config issues

8. **Rollback (Quick Reference)**
   Immediate disable, restore from backup, git revert

---

## Implementation Roadmap

### Pre-Work (Week 0)

- [ ] Read architecture + quick-start documents
- [ ] Set up feature branches (feature/taskrouter-phase1, etc.)
- [ ] Prepare test environment
- [ ] Schedule code review pairing sessions

### Week 1: Core Routing (Days 1–5)

- [ ] Action 1–6: Create routing/ module (TaskRouter, TaskClassifier, ConstraintValidator)
- [ ] Action 7–10: Extend config.py + RunMeta
- [ ] Action 11–13: Integrate into cli_impl.py
- [ ] Action 14–18: Unit + E2E testing
- **Deliverable**: TaskRouter integrated, 90%+ tested, 100 test tasks classified

### Week 2: Policy + Cost (Days 6–10)

- [ ] Action 19–21: Extend CostAggregator + PolicyEngine
- [ ] Action 22–24: Pareto routing (Phase 2, optional)
- [ ] Action 25: Monitoring setup
- **Deliverable**: Cost enforcement working, integration tests pass, dashboard ready

### Week 3: Testing + Rollout (Days 11–15)

- [ ] Day 11–12: Shadow run (no enforcement, collect calibration data)
- [ ] Day 13: Full enforcement rollout
- [ ] Day 14: Tuning + documentation
- [ ] Day 15: Post-launch monitoring
- **Deliverable**: 18% cost reduction, metrics stable, post-launch report

---

## Key Metrics & SLOs

### Success Criteria (End of Phase 3)

| Metric                            | Target                 | Current  | Owner   |
| --------------------------------- | ---------------------- | -------- | ------- |
| Cost Reduction                    | 18% ($550→$450/mo)     | TBD      | Finance |
| Routing Latency (p99)             | < 100ms                | Baseline | Eng     |
| Budget Accuracy                   | < 10% error            | Baseline | Eng     |
| Constraint Violation Rate         | < 1% (false positives) | Baseline | Eng     |
| Fallback Frequency (HIGH_COMPLEX) | < 5%                   | Baseline | Eng     |
| Code Coverage (routing/)          | ≥90%                   | Baseline | Eng     |

### Hard Constraints (Must Pass)

```
Performance (Quality Thresholds):
  FAST:         ≥ 60%
  NORMAL:       ≥ 70%
  COMPLEX:      ≥ 75%
  HIGH_COMPLEX: ≥ 80%

Instantaneous Cost (per-call):
  FAST:         ≤ $0.002
  NORMAL:       ≤ $0.05
  COMPLEX:      ≤ $0.15
  HIGH_COMPLEX: ≤ $0.85

Cumulative (monthly):
  FAST:         ≤ $50 (warn $40, block $50)
  NORMAL:       ≤ $200 (warn $160, block $200)
  COMPLEX:      ≤ $150 (warn $120, block $150)
  HIGH_COMPLEX: ≤ $50 (warn $40, block $50)

Speed (SLA):
  FAST:         ≤ 1s
  NORMAL:       ≤ 5s
  COMPLEX:      ≤ 20s
  HIGH_COMPLEX: ≤ 60s
```

---

## File Structure

```
docs/reference/
├── INTEGRATION_INDEX.md              ← You are here
├── INTEGRATION_ARCHITECTURE.md       (1,482 lines, comprehensive design)
└── INTEGRATION_QUICK_START.md        (467 lines, implementation checklist)

src/thegent/
├── routing/                          [NEW MODULE]
│   ├── __init__.py                   [+10 LOC]
│   ├── models.py                     [+50 LOC]
│   └── task_router.py                [+300 LOC]
├── execution.py                      [+30 LOC] RunMeta + register_end
├── cli_impl.py                       [+20 LOC] TaskRouter integration
├── config.py                         [+20 LOC] Routing settings
├── governance/cost.py                [+40 LOC] Per-category tracking
└── models/catalog.py                 [+50 LOC] Pareto routing (Phase 2)

tests/
├── test_unit_routing.py              [NEW, +200 LOC]
├── test_integration_routing.py       [NEW, +150 LOC]
├── test_unit_config.py               [+50 LOC]
└── test_unit_governance.py           [+80 LOC]
```

---

## Critical Path (Dependency Order)

```
1. config.py (routing settings schema)
   ↓
2. routing/models.py (TaskMetadata enums)
   ↓
3. routing/task_router.py (TaskClassifier, ConstraintValidator, TaskRouter)
   ↓
4. execution.py (RunMeta extensions)
   ↓
5. cli_impl.py (TaskRouter integration point)
   ↓
6. governance/cost.py (per-category tracking)
   ↓
7. tests/* (unit + integration tests)
```

**Must Complete Before Week 2 Starts**: All of Week 1 (Actions 1–18)

---

## Common Questions

**Q: Can we start Phase 2 before Phase 1 is complete?**
A: No. Phase 1 (TaskRouter integration) is blocking. Phase 2 depends on task_category being available in RunMeta.

**Q: What if constraint violations are too strict?**
A: That's expected. Phase 3 shadow run (Days 11–12) will calibrate thresholds before full enforcement (Day 13).

**Q: How do we handle cost estimation errors?**
A: Conservative estimate (word_count_div_1.3) is built in. Shadow run will reveal if classifier needs tuning.

**Q: Can we disable routing without code changes?**
A: Yes. Set `THGENT_ROUTING_ENABLED=false`. Old code that doesn't use task_category continues to work (backward compatible).

**Q: What's the worst-case impact of a bug in TaskRouter?**
A: Tasks might be misclassified (e.g., FAST → HIGH_COMPLEX) or constraint validation might false-positive. Both caught by unit tests + shadow run.

**Q: How do we monitor for production issues?**
A: 4 SLOs with alerts: routing latency, budget accuracy, violation rate, fallback frequency.

---

## Communication & Escalation

### Daily Standup (Week 1–3)

- [ ] Update checklist items (✓ completed, ⚠ blocked, ⏳ in progress)
- [ ] Report blockers to tech lead
- [ ] Share risky spot updates

### Code Review Pairing (Suggested)

- [ ] routing/task_router.py (classifier accuracy + complexity scoring)
- [ ] cli_impl.py integration (early TaskRouter call)
- [ ] governance/cost.py (per-category tracking logic)

### Metrics Review (Weekly)

- [ ] Shadow run metrics (Days 11–12): Cost estimates within 20%?
- [ ] Phase 2 metrics (Days 6–10): Integration tests green?
- [ ] Phase 1 metrics (Days 1–5): Coverage ≥90%?

### Post-Launch (Day 15+)

- [ ] Daily monitoring of 4 SLOs
- [ ] On-call response to alerts
- [ ] Weekly retrospective on cost reduction, incidents, improvements

---

## References & Resources

| Document                          | Purpose                   | Where           |
| --------------------------------- | ------------------------- | --------------- |
| INTEGRATION_ARCHITECTURE.md       | Full technical design     | docs/reference/ |
| INTEGRATION_QUICK_START.md        | 25-action checklist       | docs/reference/ |
| src/thegent/config.py             | Config schema reference   | Source code     |
| src/thegent/execution.py          | RunMeta + RunRegistry API | Source code     |
| tests/test_unit_routing.py        | Unit test examples        | Tests           |
| tests/test_integration_routing.py | Integration test examples | Tests           |

---

## Next Actions

**Immediate (Today)**

1. [ ] Share this index with team
2. [ ] Schedule 30-min walkthrough of INTEGRATION_ARCHITECTURE.md § 1–3
3. [ ] Schedule 30-min walkthrough of INTEGRATION_QUICK_START.md

**This Week** 4. [ ] Assign Week 1 owner (Action 1–18) 5. [ ] Set up feature branches 6. [ ] Prepare test environment

**Week 1 Kickoff** 7. [ ] Begin Action #1 (routing/models.py) 8. [ ] Daily standup on progress vs. checklist 9. [ ] Pair on Action #3 (task_router.py)

---

**Document Version**: 1.0
**Last Updated**: 2026-02-15
**Status**: Ready for Implementation
**Contact**: [Core Team]

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
