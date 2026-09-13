# Wave 4 Agent F Report

## Scope

Completed wave-4 ownership for:

- WL-079
- WL-093
- WL-094
- WL-095
- WL-096

## Concrete Changes

### WL-079: Deterministic benchmark smoke in CI docs/checklist

- Added Task targets in `Taskfile.yml`:
  - `bench:rust:audit` (offline + locked deterministic audit benchmark command)
  - `bench:smoke:ci` (deterministic smoke using WL-079 wiring assertions)
- Added CI quality job smoke step in `.github/workflows/ci.yml`:
  - `Deterministic benchmark smoke` running `task bench:smoke:ci`
- Updated QA checklist doc in `docs/guides/QUALITY_ASSURANCE.md`:
  - Pre-review checkbox now explicitly requires `task bench:smoke:ci`
- Extended WL-079 tests in `tests/test_wl079_audit_bench.py` to assert:
  - checklist entry exists
  - CI step exists and runs `task bench:smoke:ci`

### WL-093: Escalated decisions queryable by existing govern list path

- Added integration test in `tests/test_wl093_vetter_hitl_escalation.py`:
  - uses real `HITLApprovalWorkflow`
  - verifies escalation produces pending `await_approval`
  - verifies `thegent.cli.services.governance.govern_list_pending_impl()` returns the escalated run
- This validates queryability through existing govern list pending path (no CLI path rewrite needed).

### WL-094: Evidence payload failed/passed check detail coverage

- Added tests in `tests/test_wl094_vetter_evidence.py`:
  - exact failed/passed check-name detail coverage for mixed outcomes
  - explicit empty-side behavior (`failed_checks == []` for all-pass)

### WL-095: Quality scorer fallback semantics + error messaging tests

- Improved `QualityScoreVetterCheck` error semantics in `src/thegent/govern/vetter/checks.py`:
  - wraps malformed JSON judge responses in `VetterConfigError` with explicit model context
  - wraps invalid payload shape in `VetterConfigError` with explicit model context
  - preserves deterministic fallback failure message when critique is blank
- Added/updated tests in `tests/govern/test_vetter_models.py`:
  - malformed JSON -> `VetterConfigError` message assertion
  - invalid payload shape -> `VetterConfigError` message assertion
  - deterministic non-empty fallback message when critique is blank

### WL-096: max_revision_rounds never loops infinitely across repeated calls

- Hardened orchestrator in `src/thegent/govern/vetter/orchestrator.py`:
  - added per-run internal revision round tracker
  - prevents perpetual `revision_requested` on repeated calls with unchanged run_context round
- Added tests in `tests/test_wl092_vetter_orchestrator.py`:
  - repeated calls without round bump stop at cap and become rejected
  - repeated calls without round bump escalate after cap when `on_fail="escalate"`

## Focused Validation

- `python -m py_compile src/thegent/govern/vetter/orchestrator.py src/thegent/govern/vetter/checks.py tests/test_wl079_audit_bench.py tests/test_wl093_vetter_hitl_escalation.py tests/test_wl094_vetter_evidence.py tests/govern/test_vetter_models.py tests/test_wl092_vetter_orchestrator.py`
- `uv run pytest -q tests/test_wl079_audit_bench.py`
  - pass: `6 passed`
- `uv run pytest -q tests/test_wl093_vetter_hitl_escalation.py -k "govern_list_pending_path"`
  - pass: `1 passed`
- `uv run pytest -q tests/test_wl094_vetter_evidence.py -k "failed_passed_checks_capture_exact_details or failed_passed_checks_empty_side_is_explicit"`
  - pass: `2 passed`
- `uv run pytest -q tests/govern/test_vetter_models.py -k "quality_score_check_raises_on_malformed_json or quality_score_check_raises_on_invalid_payload_shape or quality_score_check_builds_deterministic_failure_message_without_critique"`
  - pass: `3 passed`
- `uv run pytest -q tests/test_wl092_vetter_orchestrator.py -k "repeated_calls_without_round_bump"`
  - pass: `2 passed`

## Files Touched

- `.github/workflows/ci.yml`
- `Taskfile.yml`
- `docs/guides/QUALITY_ASSURANCE.md`
- `src/thegent/govern/vetter/checks.py`
- `src/thegent/govern/vetter/orchestrator.py`
- `tests/govern/test_vetter_models.py`
- `tests/test_wl079_audit_bench.py`
- `tests/test_wl092_vetter_orchestrator.py`
- `tests/test_wl093_vetter_hitl_escalation.py`
- `tests/test_wl094_vetter_evidence.py`
- `.thegent/agent-batch/wave4-agent-f.md`
