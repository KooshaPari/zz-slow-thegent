# TaskRouter Integration Quick Start

**Target Audience**: Software engineers (2 hours to understand + begin implementation)
**Status**: Ready for implementation
**Last Updated**: 2026-02-15

---

## Overview

This is a **1-page** action checklist for integrating TaskRouter + Pareto routing into thegent. It assumes you've read `INTEGRATION_ARCHITECTURE.md` or can reference it for details.

**Timeline**: 3 weeks (W1: core routing, W2: policy + cost, W3: testing + rollout)
**Critical Path**: execution.py → cli_impl.py → routing/task_router.py → tests

---

## 25-Action Implementation Checklist

### Phase 1: Core Routing (Week 1, Days 1–5)

**Day 1–2: Implement TaskRouter Module**

- [ ] **1. Create routing/models.py** (50 LOC)
  - Define TaskCategory enum (FAST, NORMAL, COMPLEX, HIGH_COMPLEX)
  - Define TaskMetadata dataclass (category, complexity_score, estimated_tokens, cost, duration)
  - Define ConstraintViolation dataclass
  - **Verify**: Enum values match config keys
  - **Time**: 20 min

- [ ] **2. Create routing/**init**.py** (10 LOC)
  - Export TaskRouter, TaskClassifier, ConstraintValidator, TaskMetadata
  - **Verify**: `from thegent.routing import TaskRouter` works
  - **Time**: 5 min

- [ ] **3. Create routing/task_router.py — TaskClassifier** (120 LOC)
  - Implement `_estimate_tokens()` (word_count_div_1.3 method)
  - Implement `_score_complexity()` (keyword + token + structure scoring)
  - Implement `_categorize()` (map complexity → FAST/NORMAL/COMPLEX/HIGH_COMPLEX)
  - Implement `_estimate_cost()` and `_estimate_duration()`
  - Implement `classify()` orchestrator
  - **Verify**: Unit tests pass (token estimation, complexity scoring)
  - **Time**: 2 hours

- [ ] **4. Create routing/task_router.py — ConstraintValidator** (80 LOC)
  - Implement `validate()` checking all 4 constraints (performance, cost inst., cost cum., speed)
  - Return list of violation strings (empty if all pass)
  - **Verify**: Each constraint violation tested in isolation
  - **Time**: 1 hour

- [ ] **5. Create routing/task_router.py — TaskRouter** (20 LOC)
  - Implement `route()` orchestrator (classify + validate)
  - **Verify**: E2E test classifies and validates
  - **Time**: 20 min

- [ ] **6. Create tests/test_unit_routing.py** (200 LOC)
  - TaskClassifier: token estimation, complexity scoring, categorization (50 LOC)
  - ConstraintValidator: each constraint in isolation (100 LOC)
  - TaskRouter: full routing (50 LOC)
  - **Success Criteria**: ≥95% code coverage for routing/
  - **Time**: 2 hours

**Day 2–3: Extend Config + RunMeta**

- [ ] **7. Update config.py — Add routing settings** (20 LOC)
  - Add routing_enabled, routing_classifier_method
  - Add routing_performance_thresholds, routing_instantaneous_budget, routing_cumulative_budget, routing_speed_sla_ms
  - Add routing_budget_warning_threshold
  - Add cost_budget_by_category (replaces/augments global cost_budget_mtd)
  - Add field validators for JSON parsing (complexity_keywords)
  - **Verify**: `from thegent.config import ThegentSettings; s = ThegentSettings(); s.routing_enabled` works
  - **Time**: 45 min

- [ ] **8. Update tests/test_unit_config.py** (50 LOC)
  - Test routing settings parsing (env vars, JSON strings)
  - Test defaults
  - **Success Criteria**: All routing config tests pass
  - **Time**: 45 min

- [ ] **9. Update execution.py — Extend RunMeta** (15 LOC)
  - Add task_category: str | None
  - Add task_complexity_score: float | None
  - Add estimated_cost_usd: float | None
  - Add estimated_duration_s: float | None
  - Add constraint_violations: list[str]
  - Add fallback_reason: str | None
  - Add fallback_chain: list[str]
  - **Verify**: RunMeta can be instantiated with all fields
  - **Time**: 20 min

- [ ] **10. Update execution.py — Modify register_start/register_end** (15 LOC)
  - register_start(): Include task_category, complexity_score, estimated_cost in JSON output
  - register_end(): Accept actual_cost_usd, actual_duration_s (for calibration)
  - **Verify**: Registry JSONL includes new fields
  - **Time**: 30 min

**Day 3–4: Integrate into cli_impl.py**

- [ ] **11. Update cli_impl.py — Add TaskRouter.classify() call** (20 LOC)
  - Import TaskRouter from routing
  - Create TaskRouter(config) instance
  - Call task_metadata = router.classify(run.prompt) early in run_impl()
  - Populate run.task_category, run.task_complexity_score, run.estimated_cost_usd, run.estimated_duration_s
  - **Verify**: Smoke test: 10 tasks classified successfully
  - **Time**: 1 hour

- [ ] **12. Update cli_impl.py — Add ConstraintValidator.validate() call** (20 LOC)
  - Create ConstraintValidator(config) instance
  - Call violations = validator.validate(task_metadata, registry, model)
  - Store violations in run.constraint_violations
  - Log violations (warning level, not error yet)
  - **Verify**: Smoke test: violations logged when hard constraints violated
  - **Time**: 1 hour

- [ ] **13. Update execution.py — Modify PolicyEngine.evaluate()** (5 LOC)
  - Accept RunMeta with task_category field
  - (No logic changes; policy evaluation happens later in Phase 2)
  - **Verify**: PolicyEngine.evaluate(run) doesn't crash
  - **Time**: 15 min

- [ ] **14. Create tests/test_integration_routing.py** (150 LOC)
  - Full flow: classify + validate + policy + dispatch
  - Test FAST task (cheap model, <1s)
  - Test HIGH_COMPLEX task (quality model)
  - Test budget checks (Phase 2 integration)
  - **Success Criteria**: All E2E flows pass
  - **Time**: 2 hours

**Day 5: Comprehensive Testing**

- [ ] **15. Run all routing unit tests** (20 min)
  - `pytest tests/test_unit_routing.py -v`
  - Target: ≥90% coverage for routing/
  - **Success Criteria**: All tests pass, coverage ≥90%

- [ ] **16. Run all integration tests** (20 min)
  - `pytest tests/test_integration_routing.py -v`
  - **Success Criteria**: All tests pass

- [ ] **17. E2E smoke test: 100 tasks** (30 min)
  - Run 100 varied prompts through TaskRouter
  - Verify categories distributed (roughly 50% FAST/NORMAL, 25% COMPLEX, 25% HIGH_COMPLEX)
  - Verify no crashes
  - **Success Criteria**: 100/100 tasks classified successfully

- [ ] **18. Week 1 checkpoint: Manual code review** (30 min)
  - Verify: TaskRouter module is clean, testable, documented
  - Verify: Config schema makes sense
  - Verify: cli_impl integration is non-invasive
  - **Success Criteria**: Code review passes, no major issues

---

### Phase 2: Policy + Cost Integration (Week 2, Days 6–10)

**Day 6–7: Extend CostAggregator + PolicyEngine**

- [ ] **19. Update governance/cost.py — Add per-category methods** (40 LOC)
  - Add add_to_category(category, cost_usd, owner, timestamp)
  - Add get_category_mtd_total(category)
  - Add get_category_daily_total(category)
  - Add get_all_categories_mtd()
  - Add is_budget_exhausted(category, config) → (bool, reason)
  - **Verify**: Cost correctly bucketed by category in registry
  - **Time**: 1 hour

- [ ] **20. Update execution.py — PolicyEngine.evaluate() adds task-aware rules** (30 LOC)
  - NEW: Check per-category MTD budget before allow
  - NEW: Log category budget utilization warnings (at 80%)
  - NEW: Access run.task_category to select appropriate budget
  - **Verify**: Budget enforcement working (deny when exhausted, warn at 80%)
  - **Time**: 1 hour

- [ ] **21. Update execution.py — register_end() calls CostAggregator** (10 LOC)
  - After run completes, call `agg.add_to_category(run.task_category, cost_usd)`
  - Requires cost_usd from run metadata or API call result
  - **Verify**: Cost events written to registry
  - **Time**: 30 min

- [ ] **22. Update tests/test_unit_governance.py** (80 LOC)
  - Test per-category cost tracking (add_to_category, queries)
  - Test budget exhaustion detection
  - Test warning threshold (80%)
  - **Success Criteria**: All cost tests pass
  - **Time**: 1.5 hours

**Day 8–9: Pareto Routing (Phase 2 – Optional, can skip if time-constrained)**

- [ ] **23. Update models/catalog.py — Add resolve_route_for_category()** (50 LOC)
  - Implement Pareto-aware route selection (quality > cost for COMPLEX tasks, cost > quality for FAST)
  - Add helper: \_get_route_quality_score(route) (hardcoded quality map)
  - Add fallback: \_fallback_cheapest_route(routes)
  - **Verify**: Route selection honors task category constraints
  - **Time**: 1.5 hours

- [ ] **24. Update cli_impl.py — Use resolve_route_for_category()** (10 LOC)
  - Replace resolve_route() call with resolve_route_for_category(model, category, policy, config)
  - **Verify**: Routes chosen match category requirements
  - **Time**: 30 min

**Day 9–10: Integration + Monitoring**

- [ ] **25. Create monitoring queries + dashboard setup** (40 LOC)
  - SQL queries: cost by category (daily), budget utilization (%), constraint violations, fallback frequency
  - SLO targets: routing latency <100ms p99, budget accuracy <10%, violation rate <1%
  - **Verify**: Queries return expected results from test registry
  - **Time**: 1 hour

---

### Phase 3: Testing + Rollout (Week 3, Days 11–15)

**Day 11–12: Shadow Run (No Enforcement)**

- [ ] **Set routing_constraints_enabled=false** (5 min)
  - Tasks classified and validated, but violations don't block
  - Cost tracked but budgets not enforced

- [ ] **Run production traffic through TaskRouter for 2 days** (passive monitoring)
  - Collect metrics: classification accuracy, cost estimates vs actual, SLA adherence
  - **Success Criteria**: Cost estimates within 20% of actual, no crashes

**Day 13: Full Enforcement Rollout**

- [ ] **Set routing_constraints_enabled=true** (5 min)
  - Hard constraints now enforced (violations block/escalate)
  - Budget warnings at 80%, blocks at 100%

- [ ] **Monitor for 2 hours: violations + budget alerts** (real-time)
  - Verify no false positives (no legitimate tasks rejected)
  - Verify budget enforcement working
  - **Success Criteria**: No unexpected task rejections

**Day 14: Tuning + Documentation**

- [ ] **Adjust thresholds based on shadow run data** (30 min)
  - If cost estimates off by >20%, adjust classifier thresholds
  - If violation rate >1%, adjust SLAs or complexity scoring
  - **Success Criteria**: Metrics within SLO targets

- [ ] **Finalize documentation** (1 hour)
  - INTEGRATION_ARCHITECTURE.md (already done in design phase)
  - INTEGRATION_QUICK_START.md (this document)
  - Runbooks: How to investigate cost overages, disable routing, adjust budgets
  - **Deliverable**: Runbooks in docs/guides/

**Day 15: Post-Launch Monitoring**

- [ ] **Monitor SLOs for 24 hours** (real-time during business hours)
  - Routing latency < 100ms p99, budget accuracy <10%, violation rate <1%
  - Respond to any issues (paging on-call if needed)

- [ ] **Post-launch report** (1 hour)
  - Cost reduction achieved (goal: 18%, $550 → $450/mo)
  - Constraint compliance rate
  - Incident summary (if any)
  - Recommendations for Phase 2 enhancements

---

## File Changes at a Glance

```
├─ src/thegent/
│  ├─ execution.py              [+15 lines] RunMeta extensions, register_end cost tracking
│  ├─ cli_impl.py               [+20 lines] TaskRouter.classify() + ConstraintValidator.validate() calls
│  ├─ config.py                 [+20 lines] Routing config schema + validators
│  ├─ governance/cost.py         [+40 lines] Per-category cost tracking
│  ├─ models/catalog.py          [+50 lines] Pareto-aware routing (Phase 2, optional)
│  └─ routing/                   [NEW]
│     ├─ __init__.py            [+10 lines] Module exports
│     ├─ models.py              [+50 lines] TaskCategory, TaskMetadata, ConstraintViolation
│     └─ task_router.py          [+300 lines] TaskClassifier, ConstraintValidator, TaskRouter
│
├─ tests/
│  ├─ test_unit_routing.py       [NEW, +200 LOC]
│  ├─ test_integration_routing.py [NEW, +150 LOC]
│  ├─ test_unit_config.py        [+50 lines] Routing config tests
│  └─ test_unit_governance.py    [+80 lines] Per-category cost tests
│
└─ docs/reference/
   ├─ INTEGRATION_ARCHITECTURE.md [NEW, comprehensive design]
   └─ INTEGRATION_QUICK_START.md  [THIS FILE]
```

**Total**: ~1,205 LOC (including tests)

---

## Risky Spots (Watch Out)

### Concurrent Cost Tracking

**Risk**: Multiple processes writing to run_registry.jsonl simultaneously can corrupt entries or lose events.
**Mitigation**: Use file locks (fcntl on Unix) or atomic append-only writes (already in RunRegistry).
**Action**: Test with concurrent task dispatch during Week 3 shadow run.

### Policy Ordering

**Risk**: TaskRouter runs BEFORE PolicyEngine. If policy denies based on missing task_category, task dies with confusing error.
**Mitigation**: PolicyEngine gracefully handles missing task_category (defaults to NORMAL budget).
**Action**: Add unit test for "missing task_category" scenario.

### Classifier Accuracy

**Risk**: Token estimation can be off by 2–3x, leading to bad routing decisions (e.g., FAST task routed as HIGH_COMPLEX).
**Mitigation**: Use word_count_div_1.3 (conservative estimate), shadow run for 2 days to collect calibration data.
**Action**: If estimates off by >20%, retrain classifier or adjust thresholds in Week 3.

### Config Parsing

**Risk**: JSON parsing in config validators can fail silently if malformed (e.g., `THGENT_ROUTING_INSTANTANEOUS_BUDGET="invalid json"`).
**Mitigation**: Use strict JSON parsing with explicit error messages.
**Action**: Add config validation tests (Action #8).

### Fallback Chain Management

**Risk**: If route selection keeps failing, fallback_chain grows unbounded (memory leak).
**Mitigation**: Limit fallback_chain to 10 entries; log warning if exceeded.
**Action**: Add safeguard in cli_impl.py.

---

## Success Criteria by Phase

### Phase 1 (Core Routing — Week 1)

- [ ] TaskRouter module 100% tested (≥90% coverage)
- [ ] 100 test tasks classified with ≤5% misclassification
- [ ] All constraints validated with 100% accuracy (no false positives)
- [ ] config.py supports all routing settings
- [ ] RunMeta extended with task metadata
- [ ] E2E smoke tests pass
- **Exit Criteria**: All checkboxes above checked; code review passed

### Phase 2 (Policy + Cost Integration — Week 2)

- [ ] Per-category cost tracking working (verified in tests)
- [ ] PolicyEngine enforces per-category budgets (block at 100%, warn at 80%)
- [ ] Integration tests pass (policy + cost + routing full flow)
- [ ] Pareto routing working (optional; can skip)
- [ ] Monitoring queries production-ready
- **Exit Criteria**: All integration tests pass; shadow run ready

### Phase 3 (Testing + Rollout — Week 3)

- [ ] Shadow run: cost estimates within 20% of actual
- [ ] Zero false-positive constraint blocks during shadow run
- [ ] Full enforcement: legitimate blocks only
- [ ] Cost reduction: achieved 18% goal or better
- [ ] SLOs met: routing <100ms p99, budget accuracy <10%, violation rate <1%
- [ ] Post-launch report complete
- **Exit Criteria**: All metrics within SLO; no critical incidents; ready for production

---

## Dependency Graph (Execution Order)

```
config.py (routing settings)
    ↓
routing/models.py (TaskMetadata, enums)
    ↓
routing/task_router.py (TaskClassifier, ConstraintValidator)
    ↓
execution.py (RunMeta extensions)
    ↓
cli_impl.py (TaskRouter integration)
    ↓
governance/cost.py (per-category tracking)
    ↓
tests/* (unit + integration tests)
```

**Critical Path**: config.py → routing/task_router.py → cli_impl.py
**Must Complete Before Week 2 Starts**: All of Week 1 checklist (actions 1–18)

---

## Debugging & Troubleshooting

### TaskRouter Produces Wrong Category

```bash
# Check token estimation
python -c "
from thegent.routing.task_router import TaskClassifier
from thegent.config import ThegentSettings
cfg = ThegentSettings()
c = TaskClassifier(cfg)
result = c.classify('Your prompt here')
print(f'Category: {result.category}')
print(f'Complexity: {result.complexity_score}')
print(f'Tokens: {result.estimated_tokens}')
"

# If tokens off by 2x, adjust config:
export THGENT_ROUTING_CLASSIFIER_METHOD=model_specific  # Use better tokenizer (Phase 2)
```

### Budget Enforcement Not Working

```bash
# Check cost events in registry
grep '"event":"cost"' ~/.cache/thegent/sessions/run_registry.jsonl | head -5

# Verify budget config
python -c "
from thegent.config import ThegentSettings
cfg = ThegentSettings()
print(cfg.routing_cumulative_budget)
print(cfg.cost_budget_by_category)
"

# If missing, set env vars:
export THGENT_ROUTING_CUMULATIVE_BUDGET='{"FAST":50,"NORMAL":200,"COMPLEX":150,"HIGH_COMPLEX":50}'
```

### Constraint Violations Not Blocking

```bash
# Check if constraints are enabled
export THGENT_ROUTING_CONSTRAINTS_ENABLED=true

# Check policy evaluation
export THGENT_DEBUG=true  # Enables detailed logging
	thegent run agent "Your task" --agent claude

# Look for policy_result in registry
grep '"policy_result":"deny"' ~/.cache/thegent/sessions/run_registry.jsonl
```

---

## Rollback (Quick Reference)

**Immediate Disable**:

```bash
export THGENT_ROUTING_ENABLED=false
export THGENT_ROUTING_CONSTRAINTS_ENABLED=false
export THGENT_COST_TRACKING_ENABLED=false
```

**Restore from Backup**:

```bash
cp ~/.cache/thegent/sessions/run_registry.jsonl.backup ~/.cache/thegent/sessions/run_registry.jsonl
```

**Revert Code**:

```bash
git revert <commit-hash>  # If all changes in one commit
# OR
git checkout HEAD~1 src/thegent/routing/  # If just routing module broke
```

---

## References

| Document                       | Purpose                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| INTEGRATION_ARCHITECTURE.md    | Full design, data flows, constraint matrix, monitoring queries |
| src/thegent/config.py          | Config schema reference                                        |
| src/thegent/execution.py       | RunMeta fields, RunRegistry API                                |
| tests/test_unit_routing.py     | Unit test examples                                             |
| docs/guides/TROUBLESHOOTING.md | Troubleshooting guide (create after rollout)                   |

---

## Quick Links to Sections in Architecture Doc

- **Constraint Matrix**: INTEGRATION_ARCHITECTURE.md § 5 — Hard constraints (perf, cost, speed)
- **Config Schema**: INTEGRATION_ARCHITECTURE.md § 6 — Full configuration reference
- **Data Flow**: INTEGRATION_ARCHITECTURE.md § 3 — ASCII diagram of full flow
- **Phase Breakdown**: INTEGRATION_ARCHITECTURE.md § 7 — Detailed timeline and deliverables
- **Testing Strategy**: INTEGRATION_ARCHITECTURE.md § 8 — Unit, integration, E2E tests
- **Monitoring**: INTEGRATION_ARCHITECTURE.md § 9 — Dashboard queries and SLOs

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
