# Wave 6 — Agent F Status

## WL-079: Explicit benchmark smoke command snippet in CI docs

- status: completed
- changes:
  - `docs/guides/QUALITY_ASSURANCE.md`
    - Added explicit CI benchmark smoke command snippet showing `task bench:smoke:ci` and its deterministic offline cargo expansion.
  - `tests/test_wl079_audit_bench.py`
    - Added assertions for the new WL-079 snippet heading and explicit offline cargo command string.

## WL-093: Escalation event serialization shape test for audit-log payload

- status: completed
- changes:
  - `tests/test_wl093_vetter_hitl_escalation.py`
    - Added test `test_escalation_event_payload_shape_is_json_serializable_for_audit_log`.
    - Verifies forwarded `vetter_escalation` event has exact key set and JSON-serializable payload with expected field values.

## WL-094: Evidence append ordering across multiple evaluations

- status: completed
- changes:
  - `tests/test_wl094_vetter_evidence.py`
    - Added test `test_evidence_append_order_matches_evaluate_order_across_runs`.
    - Confirms append order in `EvidenceStore` tracks evaluation call order across mixed pass/fail policies.

## WL-095: Judge timeout/error propagation tests

- status: completed
- changes:
  - `tests/test_wl095_quality_score_vetter_check.py`
    - Added `test_judge_timeout_error_propagates_without_fallback`.
    - Added `test_judge_runtime_error_propagates_without_wrapping`.
    - Both enforce fail-loud propagation from `litellm.acompletion` with no fallback/silent handling.

## WL-096: Exhausted revision path non-requeue regression

- status: completed
- changes:
  - `tests/test_wl096_vetter_revision_queue.py`
    - Added `test_exhausted_revision_path_does_not_requeue_without_new_round`.
    - Verifies repeated calls at exhausted round stay `REJECTED` and never enqueue without a new round.

## Validation

- `uv run pytest -q tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/test_wl095_quality_score_vetter_check.py tests/test_wl096_vetter_revision_queue.py`
  - `151 passed in 7.76s`

## Notes

- Did not modify `docs/reference/WORK_STREAM.md`.
- Kept scope focused to wave-6 WL items only.
