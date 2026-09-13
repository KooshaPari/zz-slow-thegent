# Wave 12 — Agent F Report

## Scope

- Work items: WL-079, WL-093, WL-094, WL-095, WL-096.
- Objective: one additional vetter/evidence/benchmark hardening slice per item with focused tests/docs.
- Constraint honored: did not edit `docs/reference/WORK_STREAM.md`.

## Hardening Slices Delivered

### WL-079 — benchmark smoke docs/contract consistency hardening

- Files:
  - `docs/guides/QUALITY_ASSURANCE.md`
  - `tests/test_wl079_audit_bench.py`
- Updated the WL-079 benchmark smoke snippet to reflect current wrapper contract:
  - `task bench:smoke:ci` currently runs `uv run pytest -q tests/test_wl079_audit_bench.py`
  - WL-079 guard still verifies offline+locked benchmark command contract.
- Added assertion locking this snippet to avoid future docs drift.

### WL-093 — escalation reason explicit-empty canonicalization

- Files:
  - `src/thegent/govern/vetter/orchestrator.py`
  - `tests/test_wl093_vetter_hitl_escalation.py`
- Hardened escalation reason generation:
  - `policy_escalate_on` now renders as `<none>` when empty (instead of ambiguous blank value).
- Added regression `test_escalation_reason_uses_explicit_none_when_policy_escalate_on_empty`.

### WL-094 — evidence canonical resource-id normalization proof

- File: `tests/test_wl094_vetter_evidence.py`
- Added regression `test_append_normalizes_resource_ids_before_write` to lock canonical resource behavior:
  - trims `run_id` and `session_id` before evidence resource key creation.

### WL-095 — rubric list duplicate normalization fail-loud

- Files:
  - `src/thegent/govern/vetter/checks.py`
  - `tests/test_wl095_quality_score_vetter_check.py`
- Hardened `QualityScoreVetterCheck` rubric-list normalization to reject duplicate criteria after trimming.
- Added focused tests:
  - `test_rubric_list_strips_whitespace_around_keys`
  - `test_rubric_list_duplicate_entries_after_strip_raises`

### WL-096 — revision tracker run_id canonicalization

- Files:
  - `src/thegent/govern/vetter/orchestrator.py`
  - `tests/test_wl096_vetter_revision_queue.py`
- Hardened orchestrator to normalize `run_id` at evaluation entry (trim) so round tracking keys are canonical.
- Added regression `test_revision_round_tracker_uses_normalized_run_id` to prove whitespace variants share revision history.

## Validation Evidence

- `python -m py_compile src/thegent/govern/vetter/orchestrator.py src/thegent/govern/vetter/checks.py` -> pass
- `uv run pytest -q tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/test_wl095_quality_score_vetter_check.py tests/test_wl096_vetter_revision_queue.py` -> **176 passed in 61.59s**

## WL Status Snapshot (Wave 12)

- WL-079: benchmark smoke docs+test contract now reflects wrapper-first CI reality.
- WL-093: escalation reason now explicitly encodes empty escalate set as `<none>`.
- WL-094: canonical evidence resource-id trimming is locked by regression coverage.
- WL-095: rubric list duplicate-after-normalization is fail-loud and regression-tested.
- WL-096: revision round tracking is canonical for whitespace-variant run IDs and regression-tested.
