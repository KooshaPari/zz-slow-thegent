# Wave 9 — Agent F Report

## Scope

- Work items: WL-079, WL-093, WL-094, WL-095, WL-096.
- Objective: one additional vetter/evidence/benchmark hardening slice with tests/docs.
- Constraint honored: did not edit `docs/reference/WORK_STREAM.md`.

## Hardening Slice Delivered

### WL-095 — strict judge-score contract hardening

- File: `src/thegent/govern/vetter/checks.py`
- Strengthened `QualityScoreVetterCheck` input contract:
  - Judge payload scores now require strict integers (`StrictInt`) instead of permissive numeric coercion.
  - Unexpected rubric criteria in judge output now fail loudly with explicit `VetterConfigError`.
  - Removed score rounding/coercion path; scores are validated as-is and then range-checked in `[1, 5]`.

### WL-095 — regression tests added

- File: `tests/test_wl095_quality_score_vetter_check.py`
- Added focused tests:
  - `test_unexpected_criterion_score_raises_config_error`
  - `test_float_score_raises_config_error`
  - `test_bool_score_raises_config_error`

### WL-095 — plan doc contract update

- File: `docs/plans/WL-095_QUALITY_SCORE_VETTER_CHECK_IMPLEMENTATION_PLAN.md`
- Documented strict score typing and rubric-key parity requirements (no missing/no extra criteria).

## Validation Evidence

- `python -m py_compile src/thegent/govern/vetter/checks.py` -> pass
- `pytest -q tests/test_wl095_quality_score_vetter_check.py` -> blocked in host env (`pytest_asyncio` missing)
- `uv run pytest -q tests/test_wl095_quality_score_vetter_check.py` -> **53 passed**
- `uv run pytest -q tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/test_wl096_vetter_revision_queue.py` -> **107 passed**

## WL Status Snapshot (Wave 9)

- WL-079: revalidated via focused benchmark-governance tests (pass)
- WL-093: revalidated escalation path tests (pass)
- WL-094: revalidated evidence append/integrity tests (pass)
- WL-095: hardened strict judge contract + new regressions (pass)
- WL-096: revalidated revision queue tests (pass)
