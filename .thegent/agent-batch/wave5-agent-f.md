# Wave 5 — Agent F Status

## WL-079: CI checklist snippet for audit bench smoke verification

- status: completed
- changes:
  - `docs/guides/QUALITY_ASSURANCE.md`
    - Added explicit pre-review checklist snippet to verify CI benchmark smoke step and the audit bench smoke command wrapper.
  - `tests/test_wl079_audit_bench.py`
    - Expanded assertions to require the new checklist snippet text.
- validation:
  - `uv run pytest -q tests/test_wl079_audit_bench.py`
    - `6 passed in 1.80s`

## WL-093: Assert escalation event includes lane/status fields in list path

- status: completed
- changes:
  - `tests/test_wl093_vetter_hitl_escalation.py`
    - In govern-list-path regression test, added explicit assertions that returned pending event includes `lane` and `status` fields and expected values.
- validation:
  - `uv run pytest -q tests/test_wl093_vetter_hitl_escalation.py -k govern_list_pending_path`
    - `1 passed, 32 deselected in 32.09s`

## WL-094: Expand evidence tests for duration_ms/verdict payloads

- status: completed
- changes:
  - `tests/test_wl094_vetter_evidence.py`
    - Added parameterized coverage for all four verdicts (`approved`, `rejected`, `escalated`, `revision_requested`) asserting payload `verdict` and non-negative integer `duration_ms`.
- validation:
  - `uv run pytest -q tests/test_wl094_vetter_evidence.py -k verdict_and_duration_for_all_verdicts`
    - `4 passed, 24 deselected in 27.17s`

## WL-095: Fallback selection tests when CapabilityIndex returns empty/None

- status: completed
- changes:
  - `tests/test_wl095_quality_score_vetter_check.py`
    - Added tests for `judge_model="auto"` with context-provided `CapabilityIndex` returning:
      - empty list recommendations
      - `None` recommendations
    - Both assert `VetterConfigError` and verify no LLM call is made (`litellm.acompletion` not called).
- validation:
  - `uv run pytest -q tests/test_wl095_quality_score_vetter_check.py -k "context_index_empty_recommendations or context_index_none_recommendations"`
    - `2 passed, 46 deselected in 35.27s`

## WL-096: Regression test for repeated revision_requested with no round increment guard

- status: completed
- changes:
  - `tests/test_wl096_vetter_revision_queue.py`
    - Added regression test confirming repeat evaluation for same `run_id` with stale round does not keep returning `REVISION_REQUESTED`; second call is guarded to `REJECTED` and queue enqueue count stays at 1.
- validation:
  - `uv run pytest -q tests/test_wl096_vetter_revision_queue.py -k repeated_revision_requested_for_same_run_is_guarded_by_tracker_round`
    - `1 passed, 30 deselected in 32.14s`

## Notes

- Did not modify `docs/reference/WORK_STREAM.md`.
- Kept scope limited to requested wave-5 WL items.
