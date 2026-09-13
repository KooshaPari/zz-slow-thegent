# Wave 8 — Agent F Report

## Scope

- Work items: WL-079, WL-093, WL-094, WL-095, WL-096
- Objective: strengthen vetter/evidence/revision guarantees and benchmark governance docs/tests.
- Constraint honored: did not edit `docs/reference/WORK_STREAM.md`.

## Changes Delivered

### WL-094 / WL-096 — fail-loud guarantee hardening in vetter orchestrator

- File: `src/thegent/govern/vetter/orchestrator.py`
- Added strict revision-round validation:
  - `vetter_revision_round` must be an integer and `>= 0`.
  - Invalid types (including strings/bools) and negative values now raise `RuntimeError` with explicit message.
- Added strict evidence append preconditions when `evidence_store` is configured:
  - `run_id` must be non-empty.
  - `session_id` must be non-empty.
  - Missing values now fail loudly before append.

### WL-094 — evidence contract tests strengthened

- File: `tests/test_wl094_vetter_evidence.py`
- Added coverage for fail-loud evidence invariants:
  - raises on missing `run_id`.
  - raises on missing `session_id`.
  - confirms `evidence_store.append` is not called in both failure paths.

### WL-096 — revision round guard tests strengthened

- File: `tests/test_wl096_vetter_revision_queue.py`
- Added coverage for revision-round input contract:
  - non-integer `vetter_revision_round` raises.
  - negative `vetter_revision_round` raises.
  - confirms no queue enqueue on invalid round metadata.

### WL-079 — benchmark governance docs/tests hardened

- File: `docs/governance/GOVERNANCE_SUMMARY.md`
- Added `Deterministic Benchmark Governance (WL-079)` section requiring:
  - `task bench:smoke:ci` in CI,
  - offline + locked benchmark command contract,
  - required CI step name `Deterministic benchmark smoke`.

- File: `tests/test_wl079_audit_bench.py`
- Added test asserting governance summary contains the WL-079 benchmark governance contract.

- File: `.github/workflows/ci.yml`
- Restored/added quality-lane step:
  - `Deterministic benchmark smoke`
  - runs `task bench:smoke:ci`.

## Validation Evidence

- `python -m py_compile src/thegent/govern/vetter/orchestrator.py` -> pass
- `uv run pytest -q tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/test_wl095_quality_score_vetter_check.py tests/test_wl096_vetter_revision_queue.py` -> **157 passed**

## Notes

- First targeted test run surfaced a real regression: CI workflow lacked the `Deterministic benchmark smoke` step expected by WL-079 assertions.
- Fixed by adding the explicit step back to `.github/workflows/ci.yml`; re-run passed fully.
