# Wave 2 Agent F Report

## Completed Slices

### WL-079

- Added offline-safe verification tests for benchmark wiring:
  - `tests/test_wl079_audit_bench.py`
  - Asserts `crates/thegent-router/Cargo.toml` declares `[[bench]] name = "audit_bench"` with `harness = false`.
  - Asserts workspace-level `criterion` dependency exists in `crates/Cargo.toml`.
- Verified benchmark target compiles with `cargo bench --no-run`.

### WL-093

- Validated escalation slice behavior remains correct with focused tests:
  - escalated verdict emits `vetter_escalation`
  - HITL `await_approval` call path executes
- No additional code changes required for this wave slice.

### WL-094

- Validated evidence append slice behavior remains correct with focused tests:
  - evidence appended on approved verdict
  - evidence appended on revision-requested verdict
- No additional code changes required for this wave slice.

### WL-095

- Implemented `QualityScoreVetterCheck` in `src/thegent/govern/vetter/checks.py`.
- Added strict configuration + scoring contract:
  - rubric normalization/validation
  - threshold validation (`pass_threshold`, `min_criterion_score` in `[0,1]`)
  - deterministic JSON parsing via typed payload model
  - pass/fail requires both aggregate and per-criterion thresholds + judge pass verdict
  - rich metadata payload in `VetterCheckResult`
- Exported new check in `src/thegent/govern/vetter/__init__.py`.
- Added focused tests in `tests/govern/test_vetter_models.py`:
  - protocol conformance
  - pass path
  - aggregate-threshold fail path
  - min-criterion fail path
  - malformed JSON failure
  - auto-model without resolver failure

### WL-096

- Extended queue schema and enqueue API in `src/thegent/core/prompt_queue.py`:
  - added `QueueItem.metadata: dict[str, Any]`
  - persisted metadata in JSONL serialization
  - backward-compatible read path for entries missing/invalid metadata
  - extended `PromptQueueManager.enqueue(..., metadata=...)`
- Wired orchestrator revision metadata in `src/thegent/govern/vetter/orchestrator.py`:
  - revision enqueue now includes metadata:
    - `vetter_revision: true`
    - `original_run_id`
    - `round` (next round)
- Added/updated tests:
  - `tests/test_prompt_queue.py` metadata persistence + legacy-line compatibility
  - `tests/test_wl092_vetter_orchestrator.py` asserts revision enqueue metadata fields

## Validation

- `python -m py_compile src/thegent/govern/vetter/checks.py src/thegent/govern/vetter/orchestrator.py src/thegent/core/prompt_queue.py tests/govern/test_vetter_models.py tests/test_wl092_vetter_orchestrator.py tests/test_prompt_queue.py tests/test_wl079_audit_bench.py` (pass)
- `uv run pytest -q tests/govern/test_vetter_models.py -k "quality_score_check"` (pass: 6 passed)
- `uv run pytest -q tests/test_prompt_queue.py -k "metadata"` (pass: 2 passed)
- `uv run pytest -q tests/test_wl092_vetter_orchestrator.py -k "revision_requested_enqueues_prompt or revision_round_cap_falls_back_to_rejected"` (pass: 2 passed)
- `uv run pytest -q tests/test_wl093_vetter_hitl_escalation.py -k "test_escalated_verdict_emits_vetter_escalation_event or test_hitl_await_approval_called_on_escalation"` (pass: 2 passed)
- `uv run pytest -q tests/test_wl094_vetter_evidence.py -k "test_evidence_appended_on_approved_verdict or test_evidence_appended_for_revision_requested_verdict"` (pass: 2 passed)
- `uv run pytest -q tests/test_wl079_audit_bench.py` (pass: 2 passed)
- `cargo bench --manifest-path crates/Cargo.toml -p thegent-router --bench audit_bench --no-run` (pass; bench executable built)

## Blockers

- None for this wave slice.

## Exact Files Touched

- `src/thegent/govern/vetter/checks.py`
- `src/thegent/govern/vetter/__init__.py`
- `src/thegent/core/prompt_queue.py`
- `src/thegent/govern/vetter/orchestrator.py`
- `tests/govern/test_vetter_models.py`
- `tests/test_prompt_queue.py`
- `tests/test_wl092_vetter_orchestrator.py`
- `tests/test_wl079_audit_bench.py`
- `.thegent/agent-batch/wave2-agent-f.md`
