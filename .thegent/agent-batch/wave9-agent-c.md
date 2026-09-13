# Wave 9 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench output-format normalization and validation hardening

- Code changes:
  - Normalized `bench run/compare --output-format` parsing to accept case/whitespace variants.
  - Added `table` alias normalization to `rich` output.
  - Added strict failure for unknown output formats (instead of silent rich fallback).
- Test changes:
  - Added coverage for normalized JSON option input (`"  JSON  "`).
  - Added coverage for unknown compare output format rejection.
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `tests/test_wl115_bench_cli.py`

### WL-116: transcript summary metadata normalization

- Code changes:
  - Added invalid-metadata guards for negative transcript length/source count.
  - Added thousands separator formatting for transcript character counts in human output.
- Test changes:
  - Added coverage for grouped numeric formatting and negative metadata rejection.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-118: doctor actionable-hint normalization

- Code changes:
  - Normalized actionable hint dedupe in doctor output by collapsing whitespace and case differences.
- Test changes:
  - Added regression test confirming normalized duplicate hints are emitted once.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`

### WL-119: grounding-source output de-duplication

- Code changes:
  - De-duplicated repeated grounding source URLs while preserving first-seen order in human-facing output.
- Test changes:
  - Added regression coverage for duplicate URL suppression and normalized output count.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-120: checkpoint docs update for wave-9

- Docs changes:
  - Updated current checkpoint table state descriptions to include wave-9 normalization/usability slices.
  - Expanded checkpoint ledger section from wave-4/5/6/7/8 to wave-4/5/6/7/8/9 and added wave-9 rows.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation Commands

1. Compile checks

- `python -m py_compile src/thegent/cli/apps/bench.py src/thegent/cli/commands/run_output_helpers.py src/thegent/doctor.py`

2. WL-focused tests

- `./.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py`

## Constraints Check

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-115, WL-116, WL-118, WL-119, WL-120 slices and related tests/docs only.
