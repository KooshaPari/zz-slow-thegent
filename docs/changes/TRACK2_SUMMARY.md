# Track 2: Hexagonal Split TDD Plan — Executive Summary

**Document:** `/docs/changes/track-2-hexagonal-split-tdd-plan.md`
**Status:** Ready for Implementation
**Scope:** 5 Rust crates, 6 Python modules, PyO3 bindings
**Coverage Target:** 100% (Unit + Integration + E2E)

## What This Plan Covers

A complete **test-driven development** roadmap for rewriting thegent's Python infrastructure modules in Rust. Each task follows the pattern:

1. **Failing test first** (Rust `#[test]` + Python pytest)
2. **Implementation** (exact file paths, full code)
3. **Build commands** (cargo + maturin)
4. **Verification** (coverage, benchmarks, parity)

## Six Tasks Across Five Crates

### Part 1: thegent-policy (12,638 LOC → NEW)

- **1.1** Create crate skeleton + tests
- **1.2** PyO3 bindings
- **1.3** Port governance functions (compliance, cost enforcement)

### Part 2: thegent-zmx extended (896 LOC → session module)

- **2.1** Session lifecycle, state machine, context storage

### Part 3: thegent-jsonl extended (2,342 LOC → audit module)

- **3.1** Immutable JSONL audit log, range queries, filtering

### Part 4: thegent-metrics (NEW, 80 LOC)

- **4.1** Counters, gauges, histograms, Prometheus export

### Part 5: thegent-crypto extended (1,594 LOC → security module)

- Similar structure to above

### Part 6: Verification & Removal

- **5.1** Parity harness (Python vs Rust)
- **5.2** Performance benchmarks (10-50x expected speedup)
- **5.3** Remove Python modules after verification

## Key Features of This Plan

### ✓ Every Task is Concrete

- Exact file paths (absolute)
- Full Rust source code (no pseudocode)
- Full PyO3 binding code (buildable)
- Complete test fixtures and data

### ✓ Test-First Throughout

- Each task starts with **failing tests** (both Rust and Python)
- Tests define acceptance criteria
- Benchmarks measure performance gains
- Parity tests verify 1:1 replacement

### ✓ Production-Grade

- 100% coverage requirement (agent-only test level)
- No fallbacks or legacy compatibility
- Fail-fast error handling
- Rust `clippy -D warnings` enforcement

### ✓ Build System Ready

- maturin for PyO3 compilation
- Workspace Cargo.toml
- Explicit pyproject.toml updates
- Clear build/test commands for each task

## Execution Checklist

- [ ] Read full plan (`docs/changes/track-2-hexagonal-split-tdd-plan.md`)
- [ ] Task 1.1 — Create thegent-policy skeleton + tests
  - [ ] Cargo.toml, src/lib.rs, src/engine.rs, src/evaluator.rs, src/errors.rs
  - [ ] integration_tests.rs + fixtures
  - [ ] All Rust tests pass (`cargo test`)
  - [ ] No warnings (`cargo clippy -D warnings`)
- [ ] Task 1.2 — PyO3 bindings
  - [ ] Update pyproject.toml with maturin
  - [ ] Create root Cargo.toml workspace
  - [ ] Python bindings build (`maturin develop`)
  - [ ] Python tests pass (`pytest tests/unit/test_thegent_policy_binding.py`)
- [ ] Task 1.3 — Port governance functions
  - [ ] compliance.rs + cost_enforcer.rs
  - [ ] All Rust tests pass
  - [ ] Python bindings work
  - [ ] Compliance checks <1ms latency
- [ ] Task 2.1 — Session management (thegent-zmx)
  - [ ] Session struct, state machine, context storage
  - [ ] Both Rust and Python tests pass
  - [ ] State transitions enforced
- [ ] Task 3.1 — Audit logging (thegent-jsonl)
  - [ ] JSONL writer with immutability hashing
  - [ ] Range queries and filtering
  - [ ] Both test suites pass
- [ ] Task 4.1 — Metrics crate
  - [ ] Counter, Gauge, Histogram implementations
  - [ ] Prometheus export
  - [ ] Both test suites pass
- [ ] Task 5.1 — Parity harness
  - [ ] test_python_rust_parity.py passes
  - [ ] All features verified 1:1 match
- [ ] Task 5.2 — Benchmarks
  - [ ] Performance comparisons show ≥2x speedup
  - [ ] Document results
- [ ] Task 5.3 — Remove Python modules
  - [ ] Backup old code
  - [ ] Verify no imports remain
  - [ ] All tests still pass
  - [ ] Git commit with rationale

## Build Commands (Copy-Paste Ready)

```bash
# Development build
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
maturin develop --release

# Run all Rust tests
cargo test --all

# Run Python binding tests
pytest tests/unit/test_*_binding.py -v

# Coverage check
cargo tarpaulin -p thegent-policy --out stdout | grep Coverage

# Quality gate
cargo clippy -p thegent-policy -p thegent-zmx -p thegent-jsonl -p thegent-metrics -- -D warnings

# Parity verification
pytest tests/integration/test_python_rust_parity.py -v
```

## Timeline Estimate

- **Task 1.1-1.3 (thegent-policy):** 4-6 hours
- **Task 2.1 (session):** 2-3 hours
- **Task 3.1 (audit):** 2-3 hours
- **Task 4.1 (metrics):** 1-2 hours
- **Verification & Removal:** 3-5 hours

**Total:** 12-19 hours sequential | 3-5 hours with agent parallelization

## Quality Standards

All code must pass:

- ✓ `cargo clippy -D warnings` (zero warnings)
- ✓ 100% test coverage (tarpaulin)
- ✓ Parity tests (Python vs Rust match)
- ✓ Performance benchmarks (≥2x speedup)
- ✓ Zero panics on edge cases
- ✓ No fallbacks or legacy compatibility

## Next Steps

1. **Read the full plan:** Open `/docs/changes/track-2-hexagonal-split-tdd-plan.md`
2. **Start Task 1.1:** Scaffold thegent-policy crate
3. **Run failing tests first:** Before writing any implementation
4. **Build incrementally:** Each task builds on the previous
5. **Verify parity:** Before removing Python code
6. **Document findings:** Create `CONVERSATION_DUMP_YYYY-MM-DD.md`

---

**Plan created:** 2026-02-22
**Format:** Markdown, organized by Part/Task
**Code examples:** Full, production-ready, copy-paste buildable
