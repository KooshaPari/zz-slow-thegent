# Wave 11 — Agent F Report

## Scope

- Work items: WL-079, WL-093, WL-094, WL-095, WL-096.
- Objective: one additional vetter/evidence/benchmark hardening slice per item with focused tests/docs.
- Constraint honored: did not edit `docs/reference/WORK_STREAM.md`.

## Hardening Slices Delivered

### WL-079 — benchmark smoke gate contract hardening

- File: `tests/test_wl079_audit_bench.py`
- Added regression `test_taskfile_bench_smoke_ci_remains_test_wrapper_gate` to lock the CI smoke lane contract:
  - `bench:smoke:ci` must execute `uv run pytest -q tests/test_wl079_audit_bench.py`
  - `bench:smoke:ci` must not inline `cargo bench`

### WL-093 — escalation reason determinism hardening

- Files:
  - `src/thegent/govern/vetter/orchestrator.py`
  - `tests/test_wl093_vetter_hitl_escalation.py`
- Hardened escalation reason generation so `policy_escalate_on` is canonicalized as sorted+deduplicated for stable audit output.
- Added regression `test_escalation_reason_deduplicates_policy_escalate_on_for_audit_stability`.
- Updated existing deterministic-reason assertion to enforce canonical ordering.

### WL-094 — evidence run_id fail-loud hardening

- Files:
  - `src/thegent/govern/vetter/orchestrator.py`
  - `tests/test_wl094_vetter_evidence.py`
- Hardened evidence append path to reject whitespace-only `run_id` (trim + fail loudly).
- Added regression `test_append_raises_with_whitespace_run_id`.

### WL-095 — rubric normalization contract hardening

- Files:
  - `src/thegent/govern/vetter/checks.py`
  - `tests/test_wl095_quality_score_vetter_check.py`
  - `docs/plans/WL-095_QUALITY_SCORE_VETTER_CHECK_IMPLEMENTATION_PLAN.md`
- Hardened rubric dict normalization in `QualityScoreVetterCheck`:
  - trims rubric keys/descriptions deterministically
  - rejects duplicate criteria after normalization
- Added focused tests:
  - `test_rubric_dict_strips_keys_and_descriptions`
  - `test_rubric_dict_duplicate_keys_after_strip_raises`
- Updated WL-095 plan acceptance/implementation notes for duplicate-normalized-key rejection.

### WL-096 — revision queue run_id fail-loud hardening

- Files:
  - `src/thegent/govern/vetter/orchestrator.py`
  - `tests/test_wl096_vetter_revision_queue.py`
  - `docs/plans/WL-096_REVISION_QUEUE_METADATA_PLAN.md`
- Hardened revision enqueue path to reject whitespace-only `run_id` (trim + fail loudly) and write normalized `original_run_id` metadata.
- Added regression `test_revision_enabled_rejects_whitespace_run_id`.
- Updated WL-096 plan with explicit whitespace-`run_id` rejection contract.

## Validation Evidence

- `python -m py_compile src/thegent/govern/vetter/orchestrator.py src/thegent/govern/vetter/checks.py` -> pass
- `uv run pytest -q tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/test_wl095_quality_score_vetter_check.py tests/test_wl096_vetter_revision_queue.py` -> **171 passed in 111.05s**

## WL Status Snapshot (Wave 11)

- WL-079: benchmark smoke task-wrapper gate regression added and passing.
- WL-093: escalation reason canonicalization hardened with deterministic tests passing.
- WL-094: evidence append now rejects blank/whitespace `run_id`; regression passing.
- WL-095: rubric normalization hardened for whitespace+duplicate-key edge cases; tests/docs updated and passing.
- WL-096: revision enqueue now rejects whitespace `run_id`; regression + plan updates passing.
