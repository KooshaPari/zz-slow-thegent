# Wave 11 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench compare same-harness guardrail for clearer output

- Code changes:
  - Added explicit validation in `bench compare` to reject `--baseline-harness` and `--candidate-harness` when they normalize to the same harness key.
  - Emits clear operator-facing error instead of producing an ambiguous self-compare payload.
- Test changes:
  - Added coverage for normalized same-harness rejection (`codeX` vs `CODEx`).
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `tests/test_wl115_bench_cli.py`

### WL-116: transcript summary adds per-file average chars for multi-input runs

- Code changes:
  - Enhanced transcript summary line to include approximate average characters per file when multiple transcript inputs are present.
  - Preserves existing singular-file output format.
- Test changes:
  - Updated transcript summary expectations to validate the new avg-per-file output.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-118: deterministic actionable-hint ordering in doctor output

- Code changes:
  - After dedupe normalization, actionable hints are now sorted by normalized form before rendering.
  - Makes doctor output stable across run order variation.
- Test changes:
  - Added coverage asserting stable sorted hint order in rendered output.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`

### WL-119: grounding domain rollup normalizes `www.` variants

- Code changes:
  - Domain summary in grounding output now collapses `www.`-prefixed hosts into the same domain bucket as bare hosts.
  - Reduces noisy duplicate domain entries in human-facing output.
- Test changes:
  - Added coverage for `www.`/bare-host rollup normalization.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-120: checkpoint ledger update for wave-11 slices

- Docs changes:
  - Updated current checkpoint table to wave-11 state descriptions for WL-115/116/118/119/120.
  - Extended checkpoint ledger table with wave-11 rows.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation Commands

1. Compile checks

- `python -m py_compile src/thegent/cli/apps/bench.py src/thegent/cli/commands/run_output_helpers.py src/thegent/doctor.py`

2. WL-focused tests

- `./.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py`
- Result: `27 passed in 47.99s`

## Constraints Check

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-115, WL-116, WL-118, WL-119, WL-120 slices and focused tests/docs.
