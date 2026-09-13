# Wave 7 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench CLI contract alignment for compare/json options

- Code changes:
  - Updated bench run output flag to `--output-format`.
  - Updated bench compare to accept explicit `--baseline-harness` and `--candidate-harness`.
  - Added validation error when only one harness flag is provided.
- Test/docs changes:
  - Existing bench CLI WL tests now pass against current command surface.
  - Updated WL-115 plan command examples to the explicit harness flag contract.
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `docs/plans/WL-115-AGENT-C-BENCH-SLICE-PLAN.md`

### WL-116: BOM-safe transcript ingestion

- Code changes:
  - Added UTF-8 BOM normalization for text transcript reads.
  - Added BOM-safe SRT parsing path.
- Test changes:
  - Added regression test for BOM-prefixed transcript files.
- Files changed:
  - `src/thegent/agents/audio_inputs.py`
  - `tests/test_wl116_audio_inputs.py`

### WL-118: doctor severity visibility in human output

- Code changes:
  - Added `Severity` column in doctor results table rendering.
  - Rendered severity labels (`info|warning|error|critical`) alongside status.
- Test changes:
  - Added output-rendering test to verify severity column and value emission.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`

### WL-119: structured grounding metadata key hardening

- Code changes:
  - Expanded payload URL extraction to include keys ending in `url|uri|link` (for example `sourceUrl`).
- Test changes:
  - Added regression test for `sourceUrl` extraction + dedupe behavior.
- Files changed:
  - `src/thegent/routing/grounding.py`
  - `tests/test_wl119_grounding_sources.py`

### WL-120: modernization checkpoint ledger update

- Docs changes:
  - Expanded checkpoint table section to include wave-6 and wave-7 rows.
  - Added explicit evidence rows for WL-115/116/118/119/120 wave-7 slices.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation Commands

1. Compile checks

- `python -m py_compile src/thegent/cli/apps/bench.py src/thegent/agents/audio_inputs.py src/thegent/doctor.py src/thegent/routing/grounding.py`
- Result: pass.

2. WL-focused tests (primary)

- `./.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl116_audio_inputs.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py`
- Result: `27 passed in 38.84s`.

3. WL follow-up regression tests (supporting)

- `./.venv/bin/pytest -q tests/test_wl116_audio_transcript.py tests/test_wl119_google_grounding.py`
- Result: `46 passed in 15.77s`.

## Constraints Check

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were limited to WL-115, WL-116, WL-118, WL-119, WL-120 slices and their associated docs/tests.
