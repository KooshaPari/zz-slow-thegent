# Track 2: Task Checklist & Dependency Graph

**Plan Document:** `/docs/changes/track-2-hexagonal-split-tdd-plan.md`
**Last Updated:** 2026-02-22

## Task Dependency Graph

```
TASK 1.1 (thegent-policy skeleton)
  ↓
TASK 1.2 (PyO3 bindings)
  ├─→ TASK 1.3 (Compliance functions)
  │    ├─→ TASK 5.1 (Parity tests)
  │    │    ├─→ TASK 5.2 (Benchmarks)
  │    │    └─→ TASK 5.3 (Remove Python module)
  │
  ├─→ TASK 2.1 (Session mgmt) ────→ TASK 5.1
  │
  ├─→ TASK 3.1 (Audit logging) ────→ TASK 5.1
  │
  ├─→ TASK 4.1 (Metrics) ────→ TASK 5.1
  │
  └─→ TASK 6.1 (Security extended) → TASK 5.1
```

## Sequential Task Completion

### Phase P0: Foundation (4-6 hours)

- [ ] **TASK 1.1** — Create thegent-policy crate skeleton
  - [ ] Create Cargo.toml with dependencies
  - [ ] Create src/lib.rs, src/engine.rs, src/evaluator.rs, src/errors.rs
  - [ ] Create tests/integration_tests.rs with 3 failing tests
  - [ ] Create tests/fixtures/test-policy.toml
  - [ ] Run `cargo test` — verify all 3 tests FAIL
  - [ ] Implement PolicyEngine, ComplianceRule, EvaluationContext
  - [ ] Run `cargo test` — verify all 3 tests PASS
  - [ ] Run `cargo clippy -D warnings` — zero warnings
  - [ ] Run `cargo tarpaulin --lib` — ≥95% coverage

- [ ] **TASK 1.2** — Create PyO3 bindings for thegent-policy
  - [ ] Update /pyproject.toml with maturin build backend
  - [ ] Create root /Cargo.toml workspace
  - [ ] Add PyO3 to thegent-policy/Cargo.toml
  - [ ] Update src/lib.rs with #[pymodule] macro
  - [ ] Create src/lib.rs with PolicyEngineBinding, EvaluationResultBinding
  - [ ] Create tests/unit/test_thegent_policy_binding.py with 3 failing tests
  - [ ] Run `maturin develop --release`
  - [ ] Run `pytest tests/unit/test_thegent_policy_binding.py -v` — verify PASS
  - [ ] Verify bindings can be imported as `from thegent import policy_engine`

- [ ] **TASK 1.3** — Port governance compliance functions
  - [ ] Create src/compliance.rs with ComplianceChecker
  - [ ] Create src/cost_enforcer.rs with CostEnforcer
  - [ ] Create tests/compliance_tests.rs with 3 failing tests
  - [ ] Run `cargo test` — verify all tests PASS
  - [ ] Update PyO3 bindings with ComplianceCheckerBinding, CostEnforcerBinding
  - [ ] Create tests/unit/test_compliance_checker.py with 3 failing tests
  - [ ] Run `maturin develop --release`
  - [ ] Run `pytest tests/unit/test_compliance_checker.py -v` — verify PASS
  - [ ] Run compliance check latency benchmark — must be <1ms
  - [ ] Verify 100% coverage: `cargo tarpaulin -p thegent-policy --lib`

### Phase P1: Session & Audit (3-4 hours)

- [ ] **TASK 2.1** — Extend thegent-zmx for session management
  - [ ] Create src/session.rs with Session struct, SessionState enum
  - [ ] Implement state machine (Created → Active → Suspended/Resumed → Closed)
  - [ ] Create tests/session_tests.rs with 4 failing tests
  - [ ] Run `cargo test` — verify all tests PASS
  - [ ] Update Cargo.toml with PyO3 dependency
  - [ ] Create PyO3 bindings for SessionBinding
  - [ ] Create tests/unit/test_zmx_session_binding.py with 4 failing tests
  - [ ] Run `maturin develop --release`
  - [ ] Run `pytest tests/unit/test_zmx_session_binding.py -v` — verify PASS
  - [ ] Verify elapsed time tracking accurate (±10ms)
  - [ ] Verify 100% coverage: `cargo tarpaulin -p thegent-zmx --lib`

- [ ] **TASK 3.1** — Extend thegent-jsonl for immutable audit
  - [ ] Create src/audit.rs with AuditEntry, AuditLogger
  - [ ] Implement JSONL writing with append-only semantics
  - [ ] Implement immutability via blake3 hashing
  - [ ] Create tests/audit_tests.rs with 3 failing tests
  - [ ] Run `cargo test` — verify all tests PASS
  - [ ] Update Cargo.toml with blake3 dependency
  - [ ] Create PyO3 bindings for AuditLoggerBinding
  - [ ] Create tests/unit/test_audit_logger.py with 4 failing tests
  - [ ] Run `maturin develop --release`
  - [ ] Run `pytest tests/unit/test_audit_logger.py -v` — verify PASS
  - [ ] Verify JSONL format is valid (each line is JSON)
  - [ ] Verify file hash changes with new entries
  - [ ] Verify 100% coverage: `cargo tarpaulin -p thegent-jsonl --lib`

### Phase P2: Security & Crypto (2-3 hours)

- [ ] **TASK 6.1** — Extend thegent-crypto for security
  - [ ] Port `src/thegent/security/` functions to Rust
  - [ ] Create src/security.rs with key types, hashing, signing
  - [ ] Create tests/security_tests.rs with failing tests
  - [ ] Run `cargo test` — verify all tests PASS
  - [ ] Create PyO3 bindings
  - [ ] Create tests/unit/test_crypto_binding.py with failing tests
  - [ ] Run `maturin develop --release` && `pytest` — verify PASS
  - [ ] Verify 100% coverage: `cargo tarpaulin -p thegent-crypto --lib`

### Phase P3: Metrics (1-2 hours)

- [ ] **TASK 4.1** — Create thegent-metrics crate
  - [ ] Create Cargo.toml for new crate
  - [ ] Create src/lib.rs with Counter, Gauge, Histogram, MetricsRegistry
  - [ ] Create tests/metrics_tests.rs with 4 failing tests
  - [ ] Run `cargo test` — verify all tests PASS
  - [ ] Create PyO3 bindings for all types
  - [ ] Create tests/unit/test_metrics_binding.py with 4 failing tests
  - [ ] Run `maturin develop --release`
  - [ ] Run `pytest tests/unit/test_metrics_binding.py -v` — verify PASS
  - [ ] Verify Prometheus export format valid
  - [ ] Verify 100% coverage: `cargo tarpaulin -p thegent-metrics --lib`

### Phase Verification (2-3 hours)

- [ ] **TASK 5.1** — Parity harness
  - [ ] Create tests/integration/test_python_rust_parity.py
  - [ ] Write parametrized parity tests for all migrated functions
  - [ ] Run parity tests: `pytest tests/integration/test_python_rust_parity.py -v`
  - [ ] Verify 100% feature parity (all tests PASS)
  - [ ] Document any differences found

- [ ] **TASK 5.2** — Performance benchmarks
  - [ ] Create benchmarks/bench_governance.py
  - [ ] Run Python implementation benchmarks
  - [ ] Run Rust implementation benchmarks
  - [ ] Compare latencies
  - [ ] Document performance improvements (target: ≥2x speedup)
  - [ ] Create perf report in docs/reports/

- [ ] **TASK 5.3** — Remove Python modules
  - [ ] Verify parity tests pass (TASK 5.1)
  - [ ] Verify performance acceptable (TASK 5.2)
  - [ ] Backup Python modules: `mv src/thegent/governance/ .deleted-modules-backup/`
  - [ ] Search codebase for remaining Python imports:
    ```bash
    grep -r "from thegent.governance import" --include="*.py"
    grep -r "from thegent.compliance import" --include="*.py"
    grep -r "from thegent.session import" --include="*.py"
    grep -r "from thegent.audit import" --include="*.py"
    ```
  - [ ] Update all imports to use Rust bindings
  - [ ] Run full test suite: `pytest tests/ -v`
  - [ ] Verify no test failures
  - [ ] Run quality gate: `cargo clippy -D warnings`
  - [ ] Git commit with removal + rationale

## Quality Gate Criteria (Before Commit)

Every task must pass ALL of these before code review:

### Coverage (Checked with Tarpaulin)

- [ ] Unit test coverage ≥95%
- [ ] Integration test coverage ≥90%
- [ ] E2E test coverage ≥80% (where applicable)
- [ ] No untested code paths

### Correctness

- [ ] All Rust tests pass: `cargo test --all`
- [ ] All Python tests pass: `pytest tests/ -v`
- [ ] Parity tests pass: `pytest tests/integration/test_python_rust_parity.py -v`
- [ ] Clippy clean: `cargo clippy -D warnings` (zero warnings)
- [ ] No panics on edge cases (zero cost, negative values, etc.)

### Performance

- [ ] Latency meets target (e.g., compliance checks <1ms)
- [ ] Benchmarks show ≥2x speedup vs Python
- [ ] No memory leaks (test with valgrind for critical paths)
- [ ] Batch operations show parallelism benefits

### Build System

- [ ] PyO3 bindings compile: `maturin develop --release`
- [ ] Python bindings importable
- [ ] No warnings from maturin
- [ ] Works with multiple Python versions (3.10, 3.11, 3.12)

## Critical Files to Verify

Before marking each task complete:

### TASK 1.1

- [ ] `/crates/thegent-policy/Cargo.toml` — exists, has all deps
- [ ] `/crates/thegent-policy/src/lib.rs` — compiles, pub exports
- [ ] `/crates/thegent-policy/src/engine.rs` — PolicyEngine::load(), evaluate()
- [ ] `/crates/thegent-policy/tests/integration_tests.rs` — all tests pass
- [ ] `/crates/thegent-policy/tests/fixtures/test-policy.toml` — valid TOML

### TASK 1.2

- [ ] `/pyproject.toml` — has `maturin` build backend
- [ ] `/Cargo.toml` — workspace root, lists all members
- [ ] `/crates/thegent-policy/src/lib.rs` — has `#[pymodule]` macro
- [ ] `/tests/unit/test_thegent_policy_binding.py` — imports work
- [ ] Bindings importable as `from thegent import policy_engine`

### TASK 1.3

- [ ] `/crates/thegent-policy/src/compliance.rs` — ComplianceChecker
- [ ] `/crates/thegent-policy/src/cost_enforcer.rs` — CostEnforcer
- [ ] `/tests/unit/test_compliance_checker.py` — all tests pass
- [ ] Compliance checks execute in <1ms

### [Similar verification for TASK 2.1, 3.1, 4.1, 6.1]

### TASK 5.1

- [ ] `/tests/integration/test_python_rust_parity.py` — exists, passes
- [ ] All parametrized tests pass
- [ ] Parity report generated

### TASK 5.2

- [ ] `/benchmarks/bench_governance.py` — runnable
- [ ] Perf report in `/docs/reports/bench-results-2026-02-22.md`
- [ ] Shows ≥2x speedup for all operations

### TASK 5.3

- [ ] Python modules backed up in `.deleted-modules-backup/`
- [ ] No remaining imports of deleted modules
- [ ] Full test suite passes
- [ ] Git commit message references this plan + WL ticket

## Commands to Run at Task Completion

### After completing Task 1.1

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy
cargo test --lib
cargo clippy -D warnings
cargo tarpaulin --lib --out Html --output-dir target/coverage
```

### After completing Task 1.2

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
maturin develop --release
pytest tests/unit/test_thegent_policy_binding.py -v
```

### After completing Task 1.3

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
cargo test -p thegent-policy compliance
maturin develop --release
pytest tests/unit/test_compliance_checker.py -v
cargo bench -p thegent-policy compliance
```

### Before TASK 5.1 (Parity Check)

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
pytest tests/integration/test_python_rust_parity.py -v
```

### Before TASK 5.3 (Final Quality Gate)

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
cargo test --all
pytest tests/ -v
cargo clippy -p thegent-policy -p thegent-zmx -p thegent-jsonl -p thegent-metrics -- -D warnings
cargo tarpaulin --out stdout | grep Coverage
```

---

## Estimated Time Breakdown

| Task      | Time    | Status  |
| --------- | ------- | ------- |
| 1.1       | 1.5h    | Pending |
| 1.2       | 1h      | Pending |
| 1.3       | 1.5h    | Pending |
| 2.1       | 1.5h    | Pending |
| 3.1       | 1.5h    | Pending |
| 4.1       | 0.5h    | Pending |
| 6.1       | 1.5h    | Pending |
| 5.1       | 1h      | Pending |
| 5.2       | 1h      | Pending |
| 5.3       | 1h      | Pending |
| **TOTAL** | **13h** | Pending |

With agent parallelization (2+ agents on independent tasks): **3-5 hours wall-clock**.

---

**Checklist created:** 2026-02-22
**Format:** Markdown checklist with per-task verification steps
**Status:** Ready for implementation
