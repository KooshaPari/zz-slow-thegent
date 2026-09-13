# Wave 6 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: add `bench run --output-format json` test coverage

- Test changes:
  - Added explicit coverage for `thegent bench run --output-format json` and JSON payload assertions.
- Files changed:
  - `tests/test_wl115_bench_cli.py`
- Coverage added:
  - `test_bench_run_supports_output_format_json`

### WL-116: add audio transcript metadata to structured output schema docs

- Docs changes:
  - Added a dedicated structured-output schema section documenting:
    - `audio_transcript`
    - `audio_sources`
    - `audio_metadata.transcript_length_chars`
    - `audio_metadata.source_count`
    - `audio_metadata.sources`
  - Included JSON example and emission rules.
- Files changed:
  - `docs/plans/WL-116-AGENT-C-AUDIO-PASSTHROUGH-PLAN.md`

### WL-118: add doctor check severity levels for ollama statuses

- Code changes:
  - Added `severity` field to `CheckResult` (`info|warning|error|critical`).
  - Added explicit severity assignment for Ollama runtime checks (missing binary, no models, HTTP failure, timeout, connect error, unexpected exception).
- Test changes:
  - Extended Ollama doctor slice tests to assert severity values.
  - Added timeout severity test.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`
- Coverage added:
  - `test_runtime_infrastructure_ollama_timeout_sets_error_severity`

### WL-119: add grounding source dedupe/normalization helper tests

- Code changes:
  - Added `normalize_grounding_source_url()` helper.
  - Updated `extract_grounding_sources()` to normalize URLs before dedupe.
- Test changes:
  - Added normalization-focused tests for URL canonicalization + dedupe behavior.
- Files changed:
  - `src/thegent/routing/grounding.py`
  - `tests/test_wl119_grounding_sources.py`
- Coverage added:
  - `test_extract_grounding_sources_normalizes_and_dedupes_urls`
  - `test_normalize_grounding_source_url_trims_and_lowercases_host`

### WL-120: update modernization plan with wave-4/5 checkpoint rows

- Docs changes:
  - Added Wave-4 and Wave-5 executed checkpoint entries in the main checkpoint list.
  - Added explicit `Wave-4/5 Checkpoint Rows` table with WL item evidence mappings.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation

1. Compile checks:

- `python -m py_compile src/thegent/routing/grounding.py src/thegent/doctor.py`
- Result: pass.

2. Focused WL tests:

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl116_audio_inputs.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py`
- Result: `24 passed in 4.79s`.

## Constraints Check

- `docs/reference/WORK_STREAM.md` not modified.
- Changes scoped to requested WL-115/116/118/119/120 items only.
