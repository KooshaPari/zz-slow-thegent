---
task_id: research-economic-governance
status: in_progress
---

# Economic Governance Implementation Tasks

**Status**: Phase 2.1 Complete ✅ | Phase 2.2-2.5 Ready for Implementation
**Work Item**: WP-5003
**Phase**: Phase 2 (Weeks 3-4)
**Created**: 2026-02-18
**Phase 2.1 Completion**: 2026-02-18 - All scoring tasks complete

---

## Work Breakdown Structure

### Phase 2.1: Provider Scoring System (Week 3, Days 1-2)

#### Task 2.1.1: Implement DefaultProviderScorer ✅ COMPLETE

- **Objective**: Create provider scoring with reliability/latency/cost normalization
- **Inputs**: ProviderMetrics (reliability, latency_p99, cost)
- **Outputs**: ProviderScore (0-10 composite score)
- **Dependencies**: None
- **Acceptance Criteria**:
  - [x] Composite score correctly weighted (0.4/0.2/0.4)
  - [x] Latency normalization produces 0-10 range
  - [x] Cost normalization produces 0-10 range
  - [x] Score inversely weighted (higher cost/latency = lower score)
  - [x] Unit tests passing (>95% coverage)
- **Estimated Work**: 4-6 tool calls (Actual: 3)
- **Owner**: Backend team
- **File**: `governance/scoring.py` (moved from thegent/src/thegent/governance/)
- **Completion Date**: 2026-02-18

#### Task 2.1.2: Implement ProviderRegistry ✅ COMPLETE

- **Objective**: Create extensible provider registry with configuration
- **Inputs**: Built-in provider configs (gemini-flash, claude-haiku, gpt-4o-mini, etc.)
- **Outputs**: Queryable registry with lookup, fallback chain methods
- **Dependencies**: Task 2.1.1 (scorer reference)
- **Acceptance Criteria**:
  - [x] Registry initialized with 4+ providers (6 built-in)
  - [x] Each provider has: cost, reliability, latency, fallback chain
  - [x] `get()`, `list_providers()`, `get_fallback_order()` work
  - [x] Fallback chains prioritize cost-efficiency
  - [x] Integration tests with mock providers (25+ tests)
- **Estimated Work**: 3-5 tool calls (Actual: 2)
- **Owner**: Backend team
- **File**: `governance/providers.py`
- **Completion Date**: 2026-02-18

#### Task 2.1.3: Create Provider Metrics Collection ✅ COMPLETE

- **Objective**: Infrastructure to collect/update provider performance metrics
- **Inputs**: Execution results (success/error, latency, tokens used)
- **Outputs**: Metrics stored in local cache (JSONL format)
- **Dependencies**: Task 2.1.2 (registry), WP-5001-SM (Supermemory - fallback)
- **Acceptance Criteria**:
  - [x] Metrics collection for each provider
  - [x] Latency p99 calculation from samples
  - [x] Success rate calculation
  - [x] Storage in local cache (var/provider_metrics/)
  - [x] Metrics queryable within <50ms
- **Estimated Work**: 4-6 tool calls (Actual: 3)
- **Owner**: Observability team
- **File**: `governance/metrics.py`
- **Completion Date**: 2026-02-18

---

### Phase 2.2: Value & Cost Estimation (Week 3, Days 3-4)

#### Task 2.2.1: Implement ValueEstimator

- **Objective**: Estimate task value (complexity, business impact, priority)
- **Inputs**: Task object with type, category, priority hints
- **Outputs**: TaskValue with estimated value (0-10 scale) and confidence (0-1)
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] Complexity estimation: trivial (1) → very_complex (10)
  - [ ] Business impact estimation: internal (2) → security (10)
  - [ ] User priority estimation: standard (1) → blocking (10)
  - [ ] Value calculation: 0.3×complexity + 0.5×impact + 0.2×priority
  - [ ] Confidence reflects estimation method (explicit hints = 0.9, inferred = 0.6)
  - [ ] Unit tests with 5+ scenarios
- **Estimated Work**: 4-6 tool calls
- **Owner**: Backend team
- **File**: `thegent/src/thegent/governance/value.py`

#### Task 2.2.2: Implement CostEstimator

- **Objective**: Estimate task cost for given provider
- **Inputs**: Task object, provider_id
- **Outputs**: CostEstimate (USD, token estimate, confidence)
- **Dependencies**: Task 2.1.2 (registry), Task 2.2.1 (value)
- **Acceptance Criteria**:
  - [ ] Token estimation by task type (trivial=100, feature=1000)
  - [ ] Cost calculation: (tokens / 1M) × provider_rate
  - [ ] Size multipliers applied from task hints
  - [ ] Confidence scoring (0.75 for typical, range 0.6-0.9)
  - [ ] Unit tests with 5+ provider/task combinations
- **Estimated Work**: 3-5 tool calls
- **Owner**: Backend team
- **File**: `thegent/src/thegent/governance/cost.py`

#### Task 2.2.3: Build Token Estimation Database

- **Objective**: Create historical token estimate database for task types
- **Inputs**: Task type → (input_tokens, output_tokens) mapping
- **Outputs**: Configuration file with estimates for 20+ task categories
- **Dependencies**: Task 2.2.2 (estimator)
- **Acceptance Criteria**:
  - [ ] 20+ task types with token estimates
  - [ ] Estimates based on actual production data
  - [ ] Config file: `config/governance.yaml`
  - [ ] Adjustable multipliers for size hints
  - [ ] Documentation of estimation methodology
- **Estimated Work**: 3-4 tool calls
- **Owner**: Data team
- **File**: `config/governance.yaml`

---

### Phase 2.3: Cost-Aware Router (Week 4, Days 1-2)

#### Task 2.3.1: Implement CostAwareRouter

- **Objective**: Route tasks to providers based on cost-to-value ratio
- **Inputs**: Task object, list of available providers
- **Outputs**: RoutingDecision with selected provider, ratios, rationale
- **Dependencies**: Task 2.2.1 (value), Task 2.2.2 (cost), Task 2.1.2 (registry)
- **Acceptance Criteria**:
  - [ ] Route selection logic: min(cost/value) across providers
  - [ ] Fallback to score-based if cost estimation fails
  - [ ] Decision record includes: provider, ratios, rationale, timestamp
  - [ ] Audit log appends decision
  - [ ] Error handling: graceful fallback on exceptions
  - [ ] Unit tests covering happy path + 5 failure scenarios
- **Estimated Work**: 6-8 tool calls
- **Owner**: Backend team
- **File**: `thegent/src/thegent/governance/router.py`

#### Task 2.3.2: Implement Fallback Chain Execution

- **Objective**: Execute task with provider fallback
- **Inputs**: RoutingDecision, task, execution context
- **Outputs**: Result or error after trying fallback chain
- **Dependencies**: Task 2.3.1 (router), Task 2.1.2 (fallback order)
- **Acceptance Criteria**:
  - [ ] Try primary provider first
  - [ ] On failure, try fallbacks in order
  - [ ] Circuit breaker on repeated provider failures
  - [ ] Retry with exponential backoff (max 3 retries)
  - [ ] Logging of all provider attempts
  - [ ] Integration tests with mock providers
- **Estimated Work**: 5-7 tool calls
- **Owner**: Backend team
- **File**: `thegent/src/thegent/governance/executor.py`

#### Task 2.3.3: Create Audit Log Storage

- **Objective**: Persist routing decisions for compliance & analysis
- **Inputs**: RoutingDecision objects
- **Outputs**: Immutable audit log (JSON/JSONL format)
- **Dependencies**: Task 2.3.1 (decision format)
- **Acceptance Criteria**:
  - [ ] Async append-only writes (<1ms latency)
  - [ ] Log includes: timestamp, task_id, provider, ratios, actual_cost
  - [ ] Rotation by date (daily files)
  - [ ] Query interface to retrieve decisions by date/provider/task
  - [ ] Tests: write latency <1ms, read accuracy 100%
- **Estimated Work**: 3-5 tool calls
- **Owner**: DevOps team
- **File**: `thegent/src/thegent/governance/audit.py`

---

### Phase 2.4: Integration & Testing (Week 4, Days 3-5)

#### Task 2.4.1: Integrate with Pareto Router

- **Objective**: Wire economic governance into Pareto routing
- **Inputs**: Pareto router, economic router
- **Outputs**: Task → Pareto (risk) + Economic (cost-aware) → Route decision
- **Dependencies**: Task 2.3.1 (router), WP-1004 (Pareto router)
- **Acceptance Criteria**:
  - [ ] Pareto router calls economic router for cost-aware route
  - [ ] Risk score + cost ratio both available in final decision
  - [ ] Existing tests still pass (backward compatibility)
  - [ ] Integration test: task → risk + cost → provider selection
  - [ ] End-to-end happy path working
- **Estimated Work**: 4-6 tool calls
- **Owner**: Backend team
- **File**: `thegent/src/thegent/orchestration/pareto_router.py`

#### Task 2.4.2: Performance Testing

- **Objective**: Validate performance against SLO targets
- **Inputs**: Router, load test scenario (100 concurrent tasks)
- **Outputs**: Performance report (latency p99, throughput, cost)
- **Dependencies**: Task 2.4.1 (integration)
- **Acceptance Criteria**:
  - [ ] Provider selection latency: <5ms (p99)
  - [ ] Cost estimation: <10ms per provider (p99)
  - [ ] Audit log write: <1ms (p99)
  - [ ] Throughput: >1000 tasks/sec
  - [ ] No memory leaks under sustained load
  - [ ] Report: latencies, throughput, cost-savings achieved
- **Estimated Work**: 5-7 tool calls
- **Owner**: Performance team
- **File**: `tests/performance/test_economic_governance.py`

#### Task 2.4.3: Cost Accuracy Validation

- **Objective**: Verify cost predictions vs. actual billed costs
- **Inputs**: 1000 task executions across providers
- **Outputs**: Cost prediction report (error rates, calibration)
- **Dependencies**: Task 2.4.1 (integration), actual provider bills
- **Acceptance Criteria**:
  - [ ] Cost prediction accuracy: >90% within 1 week
  - [ ] Calibration spreadsheet: estimated vs actual per task type
  - [ ] Variance <20% for 95% of tasks
  - [ ] Outlier analysis: identify tasks needing adjustment
  - [ ] Recommendations for token estimate refinement
- **Estimated Work**: 4-6 tool calls
- **Owner**: Finance team
- **File**: `docs/reports/cost_prediction_validation.md`

#### Task 2.4.4: Comprehensive Integration Tests

- **Objective**: Test all components end-to-end
- **Inputs**: Value estimator, cost estimator, router, executor, audit log
- **Outputs**: Integration test suite (>20 tests, >90% path coverage)
- **Dependencies**: All tasks 2.1-2.4.3
- **Acceptance Criteria**:
  - [ ] Happy path: task → value → cost → route → execute → audit ✓
  - [ ] Failure modes: 5+ scenarios (cost estimation fails, provider down, etc.)
  - [ ] Fallback chain: all providers tested
  - [ ] Audit log: all routing decisions recorded
  - [ ] Performance: all tests complete in <30 seconds
  - [ ] Tests use fixtures, not live APIs
- **Estimated Work**: 6-8 tool calls
- **Owner**: QA team
- **File**: `tests/integration/test_economic_governance_e2e.py`

---

### Phase 2.5: Documentation & Deployment (Week 4, Days 5)

#### Task 2.5.1: Create Operator Runbook

- **Objective**: Documentation for configuring & operating economic governance
- **Inputs**: Configuration schema, audit log queries, troubleshooting
- **Outputs**: Runbook: setup, monitoring, troubleshooting
- **Dependencies**: Task 2.4.1 (integration)
- **Acceptance Criteria**:
  - [ ] Section: Provider setup (adding new providers)
  - [ ] Section: Configuration tuning (weights, multipliers)
  - [ ] Section: Monitoring (metrics, alerts)
  - [ ] Section: Troubleshooting (cost discrepancies, routing issues)
  - [ ] Examples: cost queries, audit log analysis
- **Estimated Work**: 2-3 tool calls
- **Owner**: Documentation team
- **File**: `docs/guides/ECONOMIC_GOVERNANCE_RUNBOOK.md`

#### Task 2.5.2: Create Cost Analysis Report

- **Objective**: Baseline cost analysis & savings projection
- **Inputs**: Provider pricing, estimated task distribution, current routing
- **Outputs**: Report: current costs, savings projections, ROI
- **Dependencies**: Task 2.4.3 (validation)
- **Acceptance Criteria**:
  - [ ] Current spending breakdown by provider
  - [ ] Projected savings with cost-aware routing (30-50%)
  - [ ] Break-even analysis
  - [ ] Recommendations for provider mix
  - [ ] Quarterly cost tracking plan
- **Estimated Work**: 2-3 tool calls
- **Owner**: Finance team
- **File**: `docs/reports/COST_ANALYSIS_BASELINE.md`

#### Task 2.5.3: Create Deployment Plan

- **Objective**: Staged rollout strategy & rollback plan
- **Inputs**: Integration test results, cost validation report
- **Outputs**: Deployment plan: stages, metrics, rollback triggers
- **Dependencies**: Task 2.4.1 (integration)
- **Acceptance Criteria**:
  - [ ] Stage 1: 10% of low-risk tasks (week 5)
  - [ ] Stage 2: 50% of low-risk tasks (week 6)
  - [ ] Stage 3: 100% rollout (week 7)
  - [ ] Rollback trigger: cost overrun >20%
  - [ ] Monitoring dashboard: cost, latency, error rate
  - [ ] Kill switch: disable economic governance if needed
- **Estimated Work**: 2-3 tool calls
- **Owner**: DevOps team
- **File**: `docs/plans/ECONOMIC_GOVERNANCE_DEPLOYMENT.md`

---

## Dependency Graph

```
2.1.1 (Scorer)
  ├─ 2.1.2 (Registry) ←─┬─ 2.1.3 (Metrics)
  │                     │
  │                     ├─ 2.2.2 (CostEstimator)
  │                     └─ 2.3.1 (Router)
  │
  ├─ 2.2.1 (ValueEstimator)
  │   └─ 2.3.1 (Router)
  │       ├─ 2.3.2 (Executor)
  │       │   └─ 2.4.1 (Pareto Integration)
  │       │       ├─ 2.4.2 (Performance Test)
  │       │       ├─ 2.4.4 (E2E Test)
  │       │       └─ 2.5.3 (Deployment)
  │       │
  │       └─ 2.3.3 (Audit)
  │           ├─ 2.4.3 (Cost Validation)
  │           └─ 2.5.2 (Cost Report)
  │
  └─ 2.2.3 (Token Database)

Parallel tracks:
- 2.1: Scoring (days 1-2)
- 2.2: Value/Cost (days 3-4)
- 2.3: Router/Fallback (days 1-2 of week 4)
- 2.4: Testing (days 3-5 of week 4)
- 2.5: Documentation (day 5 of week 4)
```

---

## Risk Assessment

| Risk                       | Mitigation                             | Task       |
| -------------------------- | -------------------------------------- | ---------- |
| Cost estimation inaccuracy | Validation task (2.4.3), learning loop | Task 2.4.3 |
| Provider unavailable       | Fallback chain (2.3.2)                 | Task 2.3.2 |
| Performance regression     | Performance testing (2.4.2)            | Task 2.4.2 |
| Integration complexity     | Staged integration (2.4.1)             | Task 2.4.1 |

---

## Success Criteria Summary

### By End of Week 3

- [x] Provider scoring working ✅ (2.1.1 complete)
- [x] Metrics collection functional ✅ (2.1.3 complete)
- [ ] Value & cost estimation functional (2.2.1-2.2.3)
- [ ] Token database populated (2.2.3)
- [x] All unit tests passing (>90% coverage) ✅ (65+ Phase 2.1 tests)

### By End of Week 4

- [ ] Router integrated with Pareto (2.3.1 + 2.4.1)
- [ ] Performance tests passing (2.4.2)
- [ ] Cost prediction validated (>90% accuracy) (2.4.3)
- [ ] Deployment plan ready (2.5.3)
- [ ] Runbook complete (2.5.1)

### By End of Phase 2

- [ ] 30-50% cost savings projected
- [ ] Ready for staged rollout
- [ ] Zero production incidents in testing

---

## Quality Gates

- All new code: >90% coverage, ruff check passing
- All tests: passing, <30s runtime
- Performance: meeting SLO targets
- Documentation: complete, reviewed

---

## See Also

- [Proposal](./proposal.md) — Business case
- [Design](./design.md) — Technical architecture
- [WORK_STREAM.md](../../reference/WORK_STREAM.md) — Project tracking
- [02-UNIFIED-WBS.md](../../plans/02-UNIFIED-WBS.md) — Overall plan

---

**Created**: 2026-02-18
**Status**: Ready for assignment
**Next Action**: Assign tasks to team members, begin Week 3
