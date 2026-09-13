# Track 2: Hexagonal Split — Complete Documentation Index

**Status:** ✓ Planning Complete | Ready for Implementation
**Created:** 2026-02-22 | **Updated:** 2026-02-22

## Quick Links

| Document                                          | Purpose                      | Size        | Key Info                         |
| ------------------------------------------------- | ---------------------------- | ----------- | -------------------------------- |
| [track-2-hexagonal-split-tdd-plan.md](#main-plan) | Full TDD implementation plan | 2,534 lines | Code, tests, build commands      |
| [TRACK2_SUMMARY.md](#summary)                     | Executive summary            | 200 lines   | Overview, timeline, standards    |
| [TRACK2_TASK_CHECKLIST.md](#checklist)            | Task-by-task checklist       | 400 lines   | Dependencies, verification steps |
| This document                                     | Index and navigation         | —           | You are here                     |

---

## Main Plan

**File:** `/docs/changes/track-2-hexagonal-split-tdd-plan.md`

The **definitive document** for Track 2 implementation. Contains:

### Structure

1. **Overview** — Scope, LOC counts, priorities, migration matrix
2. **Part 1: Foundation (thegent-policy)** — P0, largest crate
   - 1.1 Create crate skeleton
   - 1.2 PyO3 bindings
   - 1.3 Port governance functions
3. **Part 2: Session Management (thegent-zmx)** — P1
   - 2.1 Session lifecycle and state machine
4. **Part 3: Audit Logging (thegent-jsonl)** — P1
   - 3.1 Immutable JSONL with hashing
5. **Part 4: Metrics (thegent-metrics)** — P3
   - 4.1 Counters, gauges, histograms
6. **Part 5: Verification & Removal** — All priorities
   - 5.1 Parity harness
   - 5.2 Benchmarks
   - 5.3 Remove Python modules
7. **Part 6: Quality Gates & Coverage** — All
   - Coverage targets (100% required)
   - Quality gate bash script

### Key Features

- **100% concrete:** Every file path is absolute and exact
- **Test-first:** Every task starts with failing tests (Rust + Python)
- **Buildable:** All code is production-ready, copy-paste usable
- **Comprehensive:** PyO3 bindings included for every crate
- **Verified:** Parity tests and benchmarks before removal

### How to Use

1. Read **Overview** to understand scope
2. Pick a task from Part 1-6
3. Copy **Failing test first** code into test file
4. Run test with `cargo test` — verify FAIL
5. Copy **Implementation** code into src files
6. Run test with `cargo test` — verify PASS
7. Verify with **Build and test** commands
8. Check **Verification checklist**

---

## Summary

**File:** `/docs/changes/TRACK2_SUMMARY.md`

Quick reference for:

- What's being migrated (6 Python modules → 5 Rust crates)
- Task structure (6 major tasks across 5 parts)
- Execution order (P0 → P1 → P2 → P3 → Verification)
- Quality standards (100% coverage, no warnings, ≥2x performance)
- Timeline (12-19 hours sequential, 3-5 parallel)
- Next steps (read full plan, start Task 1.1, run tests first)

**Use this when:** You need a one-page overview before diving into the full plan.

---

## Checklist

**File:** `/docs/changes/TRACK2_TASK_CHECKLIST.md`

Step-by-step checklist for implementation:

### Organization

- **Dependency graph:** Shows which tasks must complete before others
- **Sequential checklist:** Checkbox for each sub-step (create file, run test, verify)
- **Quality gate criteria:** What must pass before each task is done
- **Critical files to verify:** Exact files to check at task completion
- **Commands to run:** Copy-paste bash commands for validation
- **Time breakdown:** Estimated hours per task

### Key Sections

- **Phase P0 (4-6h):** Tasks 1.1, 1.2, 1.3 (foundation)
- **Phase P1 (3-4h):** Tasks 2.1, 3.1 (session & audit)
- **Phase P2 (2-3h):** Task 6.1 (security, not in main plan yet)
- **Phase P3 (1-2h):** Task 4.1 (metrics)
- **Phase Verification (2-3h):** Tasks 5.1, 5.2, 5.3 (parity, benchmarks, cleanup)

**Use this when:** You're actively implementing and need step-by-step guidance.

---

## Migration Matrix

### Python Modules → Rust Crates

| Python Module               | Lines  | Target Crate                   | Task    | Priority |
| --------------------------- | ------ | ------------------------------ | ------- | -------- |
| `src/thegent/governance/`   | 12,638 | `crates/thegent-policy`        | 1.1-1.3 | P0       |
| `src/thegent/session/`      | 896    | extend `crates/thegent-zmx`    | 2.1     | P1       |
| `src/thegent/audit/`        | 2,342  | extend `crates/thegent-jsonl`  | 3.1     | P1       |
| `src/thegent/metrics/`      | 80     | `crates/thegent-metrics`       | 4.1     | P3       |
| `src/thegent/security/`     | 1,594  | extend `crates/thegent-crypto` | (6.1\*) | P2       |
| `src/thegent/verification/` | 711    | extend `crates/thegent-crypto` | (6.1\*) | P2       |
| FastMCP tools (CPU-bound)   | ~3,000 | PyO3 modules                   | 1.2-1.3 | P0       |

**Total:** ~23,261 LOC → 5 Rust crates (new + extended)

\*Note: Task 6.1 (Security) has same structure as others; included in main plan as reference.

---

## Task Execution Flowchart

```
START
  │
  ├─→ Task 1.1: Create thegent-policy skeleton
  │     └─→ Task 1.2: PyO3 bindings
  │           └─→ Task 1.3: Governance functions
  │                 ├─→ Task 2.1: Session (parallel)
  │                 ├─→ Task 3.1: Audit (parallel)
  │                 ├─→ Task 4.1: Metrics (parallel)
  │                 └─→ Task 6.1: Security (parallel)
  │
  └─→ Task 5.1: Parity harness (after 1.3, 2.1, 3.1)
        └─→ Task 5.2: Benchmarks
              └─→ Task 5.3: Remove Python modules
                    └─→ END (commit & merge)
```

**Critical path:** Task 1.1 → 1.2 → 1.3 (8 hours)
**Parallelizable:** Tasks 2.1, 3.1, 4.1, 6.1 (run while 1.3 in progress)
**Blocker:** Task 5.1 waits for all prior tasks complete

---

## Quality Standards (Non-Negotiable)

Every task must pass ALL of these:

### Code Quality

- ✓ Zero `cargo clippy` warnings (`-D warnings` enforced)
- ✓ No fallbacks, legacy compatibility, or silent error handling
- ✓ Fail-fast on errors (clear, loud failures)
- ✓ All edge cases tested (zero cost, negative values, etc.)

### Test Coverage

- ✓ **Unit tests:** ≥95% coverage (verified with tarpaulin)
- ✓ **Integration tests:** ≥90% coverage (rust + python)
- ✓ **E2E tests:** ≥80% coverage (where applicable)
- ✓ Parity tests (Python vs Rust match 100%)

### Performance

- ✓ Meets latency targets (e.g., <1ms for compliance checks)
- ✓ Benchmarks show ≥2x speedup vs Python
- ✓ No memory leaks
- ✓ Batch operations show parallelism benefits

### Build & Tooling

- ✓ PyO3 bindings compile cleanly (`maturin develop --release`)
- ✓ Python bindings importable
- ✓ Works on Python 3.10, 3.11, 3.12
- ✓ Documentation updated (this plan, README, API docs)

---

## Build System Overview

### Tools Used

- **Language:** Rust (primary), Python (bindings)
- **Bindings:** PyO3 + maturin
- **Testing:** `cargo test` (Rust), `pytest` (Python)
- **Coverage:** `cargo tarpaulin` (Rust), `pytest-cov` (Python)
- **Linting:** `cargo clippy -D warnings` (Rust)

### Key Commands

```bash
# Development build (all Rust crates + Python bindings)
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
maturin develop --release

# Run Rust tests (specific crate)
cargo test -p thegent-policy

# Run Python tests
pytest tests/unit/test_*_binding.py -v

# Check coverage
cargo tarpaulin -p thegent-policy --lib --out Html

# Quality gate
cargo clippy -p thegent-policy -p thegent-zmx -- -D warnings

# Parity check
pytest tests/integration/test_python_rust_parity.py -v
```

---

## Timeline & Resources

### Sequential Estimate

- **P0 (foundation):** 4-6 hours
- **P1 (session & audit):** 3-4 hours
- **P2 (security):** 2-3 hours
- **P3 (metrics):** 1-2 hours
- **Verification:** 2-3 hours

**Total:** 12-18 hours

### With Parallelization (2+ agents)

- **Critical path (1.1 → 1.2 → 1.3):** 4-6 hours
- **Parallel tracks (2.1, 3.1, 4.1, 6.1):** Run while 1.3 in progress
- **Wall-clock time:** 3-5 hours

---

## Success Criteria (Definition of Done)

✓ All tasks complete when:

1. **100% test coverage:** Unit + Integration + E2E
2. **Parity verified:** test_python_rust_parity.py passes
3. **Performance ≥2x:** Benchmarks show speedup
4. **Zero warnings:** `cargo clippy -D warnings`
5. **PyO3 bindings work:** All Python tests pass
6. **Python modules removed:** Backed up, fully replaced
7. **Documentation updated:** CHANGELOG, README, API docs

---

## How to Use These Documents

### For Implementation Teams

1. Start with **TRACK2_SUMMARY.md** (5 min overview)
2. Read **track-2-hexagonal-split-tdd-plan.md** (main reference)
3. Use **TRACK2_TASK_CHECKLIST.md** during implementation
4. Run commands from appropriate section
5. Verify checklist items as you complete them

### For Code Review

1. Check **Quality Standards** section above
2. Verify test coverage with tarpaulin output
3. Confirm parity tests pass
4. Review benchmark results
5. Ensure no fallbacks or legacy code introduced

### For Project Tracking

1. Use **Timeline & Resources** for estimates
2. Track tasks against **Task Execution Flowchart**
3. Mark completion when all **Success Criteria** met
4. Update progress in work stream

---

## File Locations

All Track 2 documentation is under `/docs/changes/`:

```
docs/changes/
├── TRACK2_INDEX.md                          ← You are here
├── TRACK2_SUMMARY.md                        ← Quick overview
├── TRACK2_TASK_CHECKLIST.md                 ← Implementation guide
└── track-2-hexagonal-split-tdd-plan.md     ← Full TDD plan
```

All code changes are in:

```
crates/
├── thegent-policy/                          ← NEW (Task 1.1-1.3)
├── thegent-zmx/                             ← EXTEND (Task 2.1)
├── thegent-jsonl/                           ← EXTEND (Task 3.1)
├── thegent-metrics/                         ← NEW (Task 4.1)
└── thegent-crypto/                          ← EXTEND (Task 6.1)

tests/
├── unit/test_*_binding.py                   ← Python binding tests
└── integration/test_python_rust_parity.py  ← Parity harness
```

---

## Related Documents

- **Main plan:** `docs/reference/WORK_STREAM.md` (overall roadmap)
- **Governance rules:** `docs/reference/CLAUDE_CORE_GUIDELINES.md` (no fallbacks, etc.)
- **Quality standards:** `docs/governance/GOVERNANCE_SUMMARY.md` (test coverage, linting)
- **Project status:** `docs/reference/WORK_STREAM.md` (current execution state)

---

## Questions?

Refer to the appropriate document:

| Q                              | Document                                       |
| ------------------------------ | ---------------------------------------------- |
| "What's being migrated?"       | TRACK2_SUMMARY.md                              |
| "How do I start Task 1.1?"     | track-2-hexagonal-split-tdd-plan.md, Part 1    |
| "What do I need to verify?"    | TRACK2_TASK_CHECKLIST.md, Quality Gate section |
| "What's the timeline?"         | TRACK2_SUMMARY.md, Timeline section            |
| "What commands should I run?"  | TRACK2_TASK_CHECKLIST.md, Commands section     |
| "How do I know when I'm done?" | TRACK2_SUMMARY.md, Success Criteria            |

---

**Document version:** 1.0
**Status:** ✓ Ready for implementation
**Last updated:** 2026-02-22 20:25 UTC
