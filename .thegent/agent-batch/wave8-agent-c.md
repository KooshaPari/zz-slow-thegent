# Wave 8 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench compare winner metadata for output usability

- Code changes:
  - Added `winner_harness` and `winner_reason` to `bench compare --output-format json` payload.
  - Added a `Winner` row to rich table output so operators can scan result direction quickly.
- Test changes:
  - Extended bench CLI tests for winner fields and rich-table winner row visibility.
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `tests/test_wl115_bench_cli.py`

### WL-116: transcript summary readability in human output

- Code changes:
  - Updated transcript summary formatter to use singular/plural file wording (`1 file` vs `N files`).
- Test changes:
  - Added singular-file transcript summary coverage.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-118: doctor triage usability summary

- Code changes:
  - Added compact doctor summary line with status counts and severity counts.
  - Added top actionable hints block (deduped) for warn/fail checks.
- Test changes:
  - Added assertions for summary rendering and actionable hints emission.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`

### WL-119: grounding output usability improvements

- Code changes:
  - Grounding summary now renders `showing X/Y` at the header.
  - Added domains rollup line (with truncation marker) to improve source scanability.
- Test changes:
  - Updated grounding output format assertions for new header and domain rollup.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-120: checkpoint docs update for wave-8

- Docs changes:
  - Updated current checkpoint table state descriptions to include wave-8 usability slices.
  - Expanded checkpoint ledger section from wave-4/5/6/7 to wave-4/5/6/7/8 and added wave-8 rows.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation Commands

1. Compile checks

- `python -m py_compile src/thegent/cli/apps/bench.py src/thegent/cli/commands/run_output_helpers.py src/thegent/doctor.py`
- Result: pass.

2. WL-focused tests

- `./.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py`
- Result: `14 passed in 53.34s`.

## Constraints Check

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-115, WL-116, WL-118, WL-119, WL-120 slices and related tests/docs only.
