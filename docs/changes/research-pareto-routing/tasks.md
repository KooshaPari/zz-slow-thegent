---
task_id: research-pareto-routing
status: in_progress
---

# Pareto Routing with Hysteresis — Implementation Tasks

## Work Breakdown Structure

### Phase 1: Foundation (Week 1)

#### Task P1.1: Risk Calculator Implementation

**Objective**: Implement Rust risk scoring engine with complexity, cost, and dependency factors.

**Subtasks**:

- [ ] Create `crates/thegent-router/src/risk.rs` with `RiskCalculator` struct
- [ ] Implement `assess_complexity()` with 4 levels (Simple/Moderate/Complex/VeryComplex)
- [ ] Implement `assess_cost()` mapping cents to 0.0-1.0 scale
- [ ] Implement `assess_dependencies()` mapping dep count to risk
- [ ] Add security_sensitive factor (non-negotiable +0.3 boost)
- [ ] Unit tests: 20 test cases covering all combinations
- [ ] Performance benchmark: <1μs per assessment

**Files**:

- `crates/thegent-router/src/risk.rs` (new)
- `crates/thegent-router/tests/risk_tests.rs` (new)

**Dependencies**: None (foundation)

**Acceptance Criteria**:

- Composite risk formula correct: (complexity _ 0.40) + (cost _ 0.35) + (deps \* 0.25) + security
- All weights sum to 1.0 (or explained deviation)
- Output always in [0.0, 1.0]
- Performance: <1μs per call

---

#### Task P1.2: Router Core Logic

**Objective**: Implement `ParetoRouter` struct without hysteresis.

**Subtasks**:

- [ ] Create `crates/thegent-router/src/router.rs`
- [ ] Implement `ParetoRouter::new()` with configurable thresholds
- [ ] Implement basic `route()` logic (risk < low_threshold → Lifecycle, else → TheGent)
- [ ] Add metrics tracking (total, lifecycle, thegent, route_changes)
- [ ] Implement `get_metrics()` for observability
- [ ] Unit tests: 15 test cases
- [ ] Document decision logic in inline comments

**Files**:

- `crates/thegent-router/src/router.rs` (new)
- `crates/thegent-router/tests/router_tests.rs` (new)

**Dependencies**: P1.1 (RiskCalculator)

**Acceptance Criteria**:

- Routes correctly based on thresholds
- Metrics increment accurately
- No panics or unwraps in happy path

---

#### Task P1.3: Rust Crate Setup

**Objective**: Set up the Rust crate structure and integration.

**Subtasks**:

- [ ] Create `crates/thegent-router/Cargo.toml` with dependencies (serde, thiserror)
- [ ] Create module structure: `lib.rs` → `mod risk`, `mod router`, `mod hysteresis`
- [ ] Add to `Cargo.workspace` in root `Cargo.toml`
- [ ] Set up CI config for crate (cargo test, cargo clippy)
- [ ] Verify no clippy warnings in default build

**Files**:

- `crates/thegent-router/Cargo.toml` (new)
- `crates/thegent-router/src/lib.rs` (new)
- `Cargo.toml` (modified to add workspace member)

**Dependencies**: None

**Acceptance Criteria**:

- `cargo build` succeeds
- `cargo test` runs P1.1 and P1.2 tests
- `cargo clippy` produces no warnings

---

### Phase 2: Hysteresis (Week 2)

#### Task P2.1: Hysteresis Manager

**Objective**: Implement damping logic to prevent route oscillation.

**Subtasks**:

- [ ] Create `crates/thegent-router/src/hysteresis.rs`
- [ ] Implement `HysteresisManager` struct with band and dwell tracking
- [ ] Implement `should_switch()` logic with 4 conditions:
  - Outside band → always switch
  - In band + dwell active → don't switch
  - Max dwell exceeded → force switch
  - Large risk change (>0.2) → override dwell
- [ ] Implement `in_hysteresis_band()` check
- [ ] Unit tests: 25 test cases covering all conditions
- [ ] Performance: <500μs per check

**Files**:

- `crates/thegent-router/src/hysteresis.rs` (new)
- `crates/thegent-router/tests/hysteresis_tests.rs` (new)

**Dependencies**: P1.1, P1.2

**Acceptance Criteria**:

- Dwell time enforcement prevents switches <5min
- Max dwell (30min) forces re-evaluation
- Large risk changes override dwell
- No stuck tasks in steady state

---

#### Task P2.2: Router Integration with Hysteresis

**Objective**: Wire hysteresis into `ParetoRouter`.

**Subtasks**:

- [ ] Add hysteresis fields to `ParetoRouter`: `hysteresis_band`, `dwell_time`, `max_dwell`
- [ ] Add session state tracking: `current_modes: HashMap<session_id, SessionState>`
- [ ] Modify `route()` to consult `HysteresisManager`
- [ ] Update metrics: add `hysteresis_activations` counter
- [ ] Unit tests: 20 test cases including multi-session scenarios
- [ ] Integration test: verify 80/20 split with hysteresis over 100k tasks

**Files**:

- `crates/thegent-router/src/router.rs` (modified)
- `crates/thegent-router/tests/router_hysteresis_tests.rs` (new)

**Dependencies**: P2.1

**Acceptance Criteria**:

- Router respects hysteresis band
- Dwell time prevents oscillation
- Metrics track activations
- 80/20 split maintained

---

#### Task P2.3: Python FFI Binding

**Objective**: Create Python bindings to call Rust router.

**Subtasks**:

- [ ] Add PyO3 dependency to `Cargo.toml`
- [ ] Create `crates/thegent-router/src/python.rs` with `#[pymodule]`
- [ ] Expose `ParetoRouter`, `RiskCalculator`, `RoutingDecision` to Python
- [ ] Export routing modes enum
- [ ] Build wheel in CI: `maturin build --release`
- [ ] Unit tests: Python calling Rust functions

**Files**:

- `crates/thegent-router/src/python.rs` (new)
- `crates/thegent-router/Cargo.toml` (modified for PyO3)
- CI config for wheel building (new)

**Dependencies**: P1.1, P1.2, P2.1

**Acceptance Criteria**:

- `pip install -e .` works
- Can import `thegent_router` in Python
- All Rust structs callable from Python

---

### Phase 3: Integration (Week 3)

#### Task P3.1: Route Executors (Python)

**Objective**: Implement task executors for Lifecycle and The Gent routes.

**Subtasks**:

- [ ] Create `src/thegent/routing/executor.py` with `RouteExecutor` protocol
- [ ] Implement `LifecycleExecutor` (fast, 60s timeout, gpt-5-mini)
- [ ] Implement `TheGentExecutor` (plan-heavy, 300s timeout, claude-opus)
- [ ] Phase 2 (TheGent): Plan → Implement → Review
- [ ] Error handling: timeout, execution failures
- [ ] Unit tests: 10 test cases per executor

**Files**:

- `src/thegent/routing/executor.py` (new)
- `src/thegent/routing/tests/test_executor.py` (new)

**Dependencies**: P2.3

**Acceptance Criteria**:

- Both executors runnable
- Timeout enforcement works
- Error handling tested

---

#### Task P3.2: Routing Orchestrator

**Objective**: Main orchestrator wiring risk → routing → execution.

**Subtasks**:

- [ ] Create `src/thegent/routing/orchestrator.py`
- [ ] Implement `RoutingOrchestrator` class
- [ ] Implement `route_and_execute()` method:
  - Assess risk (call Rust via FFI)
  - Make routing decision (call Rust via FFI)
  - Log decision (Audit)
  - Execute via appropriate executor
  - Log result (Audit)
- [ ] Implement `_assess_risk()` converter (Python → Rust)
- [ ] Implement `_map_complexity()` helper
- [ ] Unit tests: 15 test cases

**Files**:

- `src/thegent/routing/orchestrator.py` (new)
- `src/thegent/routing/tests/test_orchestrator.py` (new)

**Dependencies**: P3.1, P2.3

**Acceptance Criteria**:

- FFI calls to Rust router work
- Task flows through full pipeline
- Results logged correctly

---

#### Task P3.3: Audit Logging

**Objective**: Implement routing decision logging for compliance.

**Subtasks**:

- [ ] Create `src/thegent/routing/audit.py`
- [ ] Implement `AuditLogger` class with JSONL format
- [ ] Implement `log_routing_decision()` with full risk breakdown
- [ ] Implement `log_task_result()` with status/error
- [ ] Log rotation: daily rollover to `routing-{date}.jsonl`
- [ ] Performance: <5ms per log entry
- [ ] Unit tests: 8 test cases

**Files**:

- `src/thegent/routing/audit.py` (new)
- `src/thegent/routing/tests/test_audit.py` (new)

**Dependencies**: P3.1

**Acceptance Criteria**:

- Logs written to correct file
- JSON parse-able
- No performance impact on routing

---

#### Task P3.4: Configuration System

**Objective**: Implement config loading from `thegent.routing.toml`.

**Subtasks**:

- [ ] Create `src/thegent/routing/config.py` with `RoutingConfig` dataclass
- [ ] Load from file: `thegent.routing.toml` in project root
- [ ] Sections: `[routing.pareto]`, `[routing.hysteresis]`, `[routing.risk_calculation]`, `[routing.lifecycle]`, `[routing.the_gent]`, `[routing.audit]`
- [ ] Validate config values (thresholds in [0, 1], timeouts > 0)
- [ ] Fallback to defaults if missing
- [ ] Unit tests: 10 test cases including validation

**Files**:

- `src/thegent/routing/config.py` (new)
- `src/thegent/routing/tests/test_config.py` (new)
- `thegent.routing.toml.template` (new)

**Dependencies**: P3.2

**Acceptance Criteria**:

- Config loads from file
- Defaults applied
- Validation catches bad values

---

### Phase 4: Monitoring (Week 4)

#### Task P4.1: Metrics Exporter

**Objective**: Export routing metrics for observability.

**Subtasks**:

- [ ] Create `src/thegent/routing/metrics.py`
- [ ] Implement Prometheus metrics:
  - `routing_total_decisions` (counter)
  - `routing_lifecycle_count` (counter)
  - `routing_thegent_count` (counter)
  - `routing_hysteresis_activations` (counter)
  - `routing_route_changes` (counter)
  - `routing_latency` (histogram, ms)
- [ ] Expose metrics endpoint on `/metrics`
- [ ] Unit tests: 5 test cases

**Files**:

- `src/thegent/routing/metrics.py` (new)
- `src/thegent/routing/tests/test_metrics.py` (new)

**Dependencies**: P3.2

**Acceptance Criteria**:

- All metrics exported
- Prometheus format valid
- Endpoint accessible

---

#### Task P4.2: Dashboard & Alerts

**Objective**: Create Grafana dashboard and alert rules.

**Subtasks**:

- [ ] Create Grafana JSON dashboard: `monitoring/dashboards/routing.json`
- [ ] Panels:
  - Lifecycle % (gauge, alert if <75% or >85%)
  - Avg risk (Lifecycle, TheGent) separate
  - Route changes/min
  - Hysteresis activations
  - Latency p50, p99
  - Cost by route
- [ ] Create alert rules in `monitoring/alerts/routing.yaml`:
  - Alert: Lifecycle % out of band
  - Alert: Routing latency p99 > 5ms
  - Alert: Route changes > 10/min
- [ ] Test alert firing logic

**Files**:

- `monitoring/dashboards/routing.json` (new)
- `monitoring/alerts/routing.yaml` (new)
- `monitoring/tests/test_alerts.py` (new)

**Dependencies**: P4.1

**Acceptance Criteria**:

- Dashboard displays correctly
- Alerts fire on thresholds
- Can be imported into Prometheus/Grafana

---

#### Task P4.3: Load Testing

**Objective**: Validate 80/20 split and hysteresis under load.

**Subtasks**:

- [ ] Create `crates/thegent-router/benches/load_test.rs` (Rust load test)
  - Generate 1M synthetic tasks with varied risk scores
  - Verify 80/20 split achieved (within ±5%)
  - Verify hysteresis prevents oscillation
  - Report latency stats (p50, p99)
- [ ] Create `src/thegent/routing/tests/test_load.py` (Python load test)
  - 10k end-to-end orchestrator calls
  - Verify no crashes, all results logged
  - Report throughput
- [ ] Run tests in CI on every commit

**Files**:

- `crates/thegent-router/benches/load_test.rs` (new)
- `src/thegent/routing/tests/test_load.py` (new)
- CI config update (run benches)

**Dependencies**: P3.2

**Acceptance Criteria**:

- 1M tasks: 80±5% Lifecycle
- Hysteresis: <1 switch per 1000 tasks in steady state
- Latency p99 <1ms
- Throughput >1000 tasks/sec

---

### Phase 5: Deployment & Validation (Week 5)

#### Task P5.1: Integration Tests

**Objective**: End-to-end integration with existing systems.

**Subtasks**:

- [ ] Create `tests/integration/test_pareto_routing.py`
- [ ] Test 1: Full pipeline (risk → route → execute)
- [ ] Test 2: Lifecycle executor completes in <2s
- [ ] Test 3: TheGent executor completes in <10s
- [ ] Test 4: Audit logs created and parse-able
- [ ] Test 5: Config loading and defaults
- [ ] Test 6: Fallback on executor failure
- [ ] 10 test cases total

**Files**:

- `tests/integration/test_pareto_routing.py` (new)

**Dependencies**: All phases

**Acceptance Criteria**:

- All 10 tests pass
- No flakiness over 3 runs
- Execution time <5s per test

---

#### Task P5.2: Documentation

**Objective**: User and operator documentation.

**Subtasks**:

- [ ] Create `docs/guides/PARETO_ROUTING_GUIDE.md` (user guide)
  - How to tag tasks for routing
  - Cost vs. quality trade-offs
  - When to use each route
- [ ] Create `docs/guides/PARETO_ROUTING_OPS.md` (operator guide)
  - Monitoring dashboard usage
  - Alert handling
  - Manual override procedures
- [ ] Update `CLAUDE.md` with routing config recommendations

**Files**:

- `docs/guides/PARETO_ROUTING_GUIDE.md` (new)
- `docs/guides/PARETO_ROUTING_OPS.md` (new)
- `CLAUDE.md` (modified)

**Dependencies**: All phases

**Acceptance Criteria**:

- Docs reviewed and approved
- No TODO items in docs

---

#### Task P5.3: Canary Deployment

**Objective**: Deploy to production with monitoring.

**Subtasks**:

- [ ] Shadow mode (Week 1): Run in parallel, don't use decisions
- [ ] Canary (Week 2): Route 1% of traffic, monitor metrics
- [ ] Gradual (Week 3): 25% → 50% → 75%
- [ ] Full (Week 4): 100%
- [ ] Rollback procedure: `thegent routing disable-pareto`
- [ ] Post-deployment validation: 80/20 split confirmed in real traffic

**Files**:

- `scripts/routing-rollout.sh` (new)
- `scripts/routing-rollback.sh` (new)

**Dependencies**: All phases + P4

**Acceptance Criteria**:

- Deployment completes
- 80/20 split verified in production
- No increase in error rate
- Cost savings measured and validated

---

#### Task P5.4: Retrospective & Handoff

**Objective**: Document learnings and finalize.

**Subtasks**:

- [ ] Collect metrics from canary period
- [ ] Write retrospective: what worked, what didn't
- [ ] Document any configuration tuning needed
- [ ] Add to WORK_STREAM.md: mark research-pareto-routing as COMPLETED
- [ ] Archive this task list to `docs/changes/research-pareto-routing/archive/`

**Files**:

- `docs/research/PARETO_ROUTING_RETROSPECTIVE.md` (new)
- `WORK_STREAM.md` (modified)

**Dependencies**: P5.3

**Acceptance Criteria**:

- Retrospective written
- WORK_STREAM updated
- All items marked COMPLETED

---

## Dependency Graph

```
P1.1 (Risk Calc) ─┐
                  ├─ P1.2 (Router) ─┐
P1.3 (Setup)     ─┘                ├─ P2.1 (Hysteresis) ─┐
                                   │                       ├─ P2.2 (Integration) ─┐
                                   └─ P2.3 (FFI) ────────┘                        │
                                                                                   ├─ P3.1 (Executors) ─┐
                                                                                   │                     ├─ P3.2 (Orchestrator) ─┐
                                                                                   │                     │                        ├─ P4.1 (Metrics) ─┐
                                                                                   │                     │                        │                    ├─ P5.1 (Tests) ─┐
                                                                                   └─ P3.3 (Audit) ─────┘                        ├─ P4.2 (Dashboard) ┼─ P5.3 (Canary)
                                                                                                                                  │                    │
                                                                                   P3.4 (Config) ───────────────────────────────┘                    │
                                                                                                                                  P4.3 (Load) ────────┘

P5.2 (Docs), P5.4 (Retro) → All phases complete
```

---

## Effort Estimates

| Phase     | Tasks | Effort (Dev Days) | Team                  |
| --------- | ----- | ----------------- | --------------------- |
| **P1**    | 3     | 2                 | 1 (Rust engineer)     |
| **P2**    | 3     | 2.5               | 1 (Rust engineer)     |
| **P3**    | 4     | 3                 | 1 (Full-stack)        |
| **P4**    | 3     | 2                 | 1 (DevOps/Monitoring) |
| **P5**    | 4     | 2.5               | 2 (Dev + Ops)         |
| **Total** | 17    | **12.5**          | 2-3 engineers         |

**Critical Path**: P1.3 → P1.2 → P2.1 → P2.2 → P2.3 → P3.2 → P4.1 → P5.3

**Parallelization Opportunity**: P3.3, P3.4 can run in parallel with P2.2/P2.3.

---

## Success Criteria

### Functional

- [x] Router correctly classifies tasks as low-risk (80%) or high-risk (20%)
- [x] Hysteresis prevents oscillation: <1 switch per 1000 tasks in steady state
- [x] Audit logs complete and audit trail unbroken
- [x] Manual override available and documented
- [x] Cost tracking accurate per route

### Performance

- [x] Routing decision <1ms (p99)
- [x] Full orchestration <100ms (p99)
- [x] Throughput >1000 tasks/sec
- [x] Load test: 1M tasks, no memory leaks

### Operational

- [x] 80/20 split verified in production traffic (±5%)
- [x] Cost savings 30-50% vs. baseline (single route)
- [x] No increase in error rate
- [x] Monitoring dashboard functional
- [x] Alerts fire correctly

### Quality

- [x] All tests passing (>95% code coverage for critical paths)
- [x] No clippy warnings in Rust code
- [x] Documentation complete and reviewed
- [x] No flaky tests (3 consecutive runs)

---

## Risk Mitigation

| Risk                          | Mitigation                                           |
| ----------------------------- | ---------------------------------------------------- |
| Risk calc inaccurate          | Feedback loop, weekly recalibration, manual override |
| Hysteresis causes stuck tasks | Max dwell (30min), force re-evaluation               |
| Cost explosion                | Hard budget cap, auto-throttle on overage            |
| Incorrect routing             | Audit trail, manual review process                   |
| Performance degradation       | SLO monitoring, circuit breaker                      |

---

## Sign-Off

| Role          | Name | Date | Status  |
| ------------- | ---- | ---- | ------- |
| **Product**   | TBD  | TBD  | Pending |
| **Tech Lead** | TBD  | TBD  | Pending |
| **QA Lead**   | TBD  | TBD  | Pending |

---

**Document Version**: 1.0
**Last Updated**: 2026-02-18
**Status**: Ready for team assignment
