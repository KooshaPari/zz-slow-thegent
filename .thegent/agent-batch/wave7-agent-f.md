# Wave 7 — Agent F Status

## Scope

- Work items: WL-079, WL-093, WL-094, WL-095, WL-096
- Goal: complete do-next slices and harden vetter flow guarantees without touching `docs/reference/WORK_STREAM.md`.

## Completed Edits

### WL-079: CI benchmark smoke enforcement

- status: completed
- file: `.github/workflows/ci.yml`
- changes:
  - Added quality job step named `Deterministic benchmark smoke`.
  - Step runs `task bench:smoke:ci` to enforce the deterministic offline benchmark smoke lane expected by WL-079 tests/docs.

### WL-093 / WL-094 / WL-095 / WL-096: vetter hardening validation + WL-096 fail-loud guarantee

- status: completed
- file: `src/thegent/govern/vetter/orchestrator.py`
- changes:
  - Hardened revision queue path: `_enqueue_revision_prompt(...)` now raises `RuntimeError` when `run_id` is empty.
  - This prevents enqueueing anonymous vetter revisions and guarantees metadata includes a valid `original_run_id`.

- file: `tests/test_wl096_vetter_revision_queue.py`
- changes:
  - Added `test_revision_enabled_requires_non_empty_run_id`.
  - Verifies revision-enabled vetter flows fail loudly without `run_id` and do not call `prompt_queue.enqueue`.

- file: `docs/plans/WL-096_REVISION_QUEUE_METADATA_PLAN.md`
- changes:
  - Added acceptance criterion that orchestrator must fail loudly (no enqueue) when revision queue is enabled without `run_id`.

## Validation Commands

- `python -m py_compile src/thegent/govern/vetter/orchestrator.py src/thegent/core/prompt_queue.py`
  - passed
- `uv run pytest -q tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/test_wl095_quality_score_vetter_check.py tests/test_wl096_vetter_revision_queue.py`
  - `152 passed in 7.77s`

## Notes

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept scope limited to wave-7 deliverables in a dirty multi-agent tree.
