# B90 Wave-3 Retrospective

<!-- @trace WL-138 B90-W3-C5 -->

**Date:** 2026-02-21
**Author:** B90-W3-C5 agent
**Status:** Complete

---

## Executive Summary

The B90 plan comprised 90 implementation items distributed across three waves and six
parallel agents per wave. Each wave built on the artifacts of the prior wave, following
a foundation-then-implementation-then-hardening progression.

- **Wave-1 (B90-W1):** 30 items — Foundation artifacts: contracts, schemas, governance
  strategies, test scaffolding, metric baseline contracts.
- **Wave-2 (B90-W2):** 30 items — Implementation: approximately 258 tests passing across
  six agents. Key artifacts included `cli_dag.py`, `slo_metrics.py`, the Rust PyO3 wrapper
  (`thegent-router`), and the Zig CI job integration.
- **Wave-3 (B90-W3, current):** 30 items — Hardening and validation: dedup cleanup,
  documentation, promotion reports, boundary compliance, and retrospective notes.

---

## Wave-1 Outcome (Foundation)

Wave-1 established the invariant contracts and schemas that Waves 2 and 3 build against.

Key deliverables:

- Governance contracts (`contracts/metric-contracts.json`, `contracts/max_lines.json`)
- Quality DAG schema and strategy definitions
- Test pyramid validator scaffolding
- SLO threshold baseline and Zig ABI contract specification (`contracts/runtime/zig_abi_contract_v1.json`)
- Core boundary spec (`config/thegent_core_boundary.toml`)

Agent reports: `docs/reports/2026-02-21-B90-W1-agent-a.md` through `-agent-f.md`

---

## Wave-2 Outcome (Implementation)

Wave-2 implemented the items defined by Wave-1 contracts, producing approximately 258
passing tests across the six parallel agents.

Key artifacts:

- `src/thegent/cli/commands/cli_dag.py` — CLI task DAG execution engine
- `src/thegent/governance/slo_metrics.py` — SLO metric definitions and evaluation
- `crates/thegent-router/` — Rust PyO3 router crate with Python bindings
- Zig CI job integration in `.github/workflows/ci.yml`
- `scripts/collect_loc_metrics.py` — LOC/complexity collector
- `scripts/render_slo_dashboard.py` — SLO dashboard renderer
- `pytest-fast.ini` — Fast lane test configuration
- `scripts/check_deprecated_quality_aliases.py` — Alias inventory and enforcement

Agent reports: `docs/reports/2026-02-21-B90-W2-agent-a.md` through `-agent-f.md`

---

## Wave-3 Outcome (Hardening and Validation)

Wave-3 hardened the Wave-2 implementation with dedup cleanup, documentation, boundary
audits, and retrospective notes.

Key deliverables (this wave):

- `tests/test_wl128_final_dedup.py` — Taskfile/pyproject dedup validation
- `docs/guides/FAST_DEEP_LANE.md` — Fast/Deep/Gate lane documentation
- `tests/test_wl134_lane_docs.py` — Lane documentation validation
- `scripts/check_dashboard_freshness.py` — Dashboard freshness validator
- `tests/test_wl135_dashboard_freshness.py` — Dashboard freshness tests
- `scripts/audit_boundary_compliance.py` — Core-to-tooling boundary auditor
- `tests/test_wl136_boundary_compliance.py` — Boundary compliance tests
- `docs/reports/2026-02-21-B90-W3-C5-wave-retrospective.md` (this document)
- `tests/test_wl138_retrospective.py` — Retrospective document validation

---

## Anti-Patterns Encountered

The following anti-patterns were observed across B90 wave agents and should be
avoided in future work:

1. **Unused stdlib imports**: Agents commonly imported `sys`, `inspect`, and `pytest`
   without using them, triggering ruff `F401` violations.

2. **Unused `field` from dataclasses**: `from dataclasses import dataclass, field`
   followed by using only `dataclass`, leaving `field` unused.

3. **`**overrides: float`type mismatch**: Using`\*\*overrides: float`in function
signatures when the actual values passed were`str` or mixed types, causing mypy
   and basedpyright errors.

4. **`assert` not narrowing compound types**: Using `assert isinstance(x, (A, B))`
   and then accessing attributes only available on `A`, without a subsequent
   `isinstance(x, A)` narrowing. Type checkers could not narrow compound `assert`
   forms in all positions.

5. **Test files importing from `conftest` explicitly**: Some agents wrote
   `from tests.conftest import fixture_name` instead of relying on pytest's
   automatic fixture injection, causing import errors in isolation.

---

## Go-Forward Recommendations (Wave-4 Scope)

The following items are recommended for a hypothetical Wave-4 hardening pass:

1. **Maturin build automation**: Integrate `maturin build --release` into CI for
   the `thegent-router` and `thegent-shm` crates, producing wheel artifacts.

2. **`cli_session.py` extraction**: The `cli.py` monolith (5665 LOC) should have
   session-management commands extracted to `cli_session.py` per WL-124/WL-125.

3. **SLO CI integration**: Wire `scripts/render_slo_dashboard.py` and
   `scripts/check_dashboard_freshness.py` into the CI pipeline so dashboard
   staleness becomes a blocking CI gate.

4. **Tach boundary enforcement in CI**: Enable `uv run tach check` as a hard CI
   gate (currently advisory) to prevent boundary regressions from merging.

5. **Mutation testing baseline**: Establish a mutmut or cosmic-ray baseline for
   the core routing and governance modules to quantify test quality beyond coverage.
