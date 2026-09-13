# Wave 12 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench compare winner-margin output fields

- Code changes:
  - Added explicit winner-margin fields in JSON compare payload:
    - `winner_margin_sec`
    - `winner_margin_pct`
  - Keeps existing signed delta fields while adding a direct magnitude surface for operator readability.
- Test changes:
  - Extended compare JSON assertions to validate new margin fields and non-negative values.
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `tests/test_wl115_bench_cli.py`

### WL-116: transcript summary sanity guard for zero-source metadata

- Code changes:
  - `_format_transcript_summary_line` now returns `None` when metadata reports `source_count == 0`.
  - Prevents rendering misleading output like "from 0 files".
- Test changes:
  - Added focused coverage for zero-source metadata rejection.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-118: doctor actionable-hints overflow indicator

- Code changes:
  - Preserved top-3 actionable hint display limit.
  - Added explicit overflow line when additional hints are present.
- Test changes:
  - Added coverage verifying overflow indicator text when four hints exist.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`

### WL-119: grounding URL default-port normalization

- Code changes:
  - `normalize_grounding_source_url` now strips default ports (`:80` for `http`, `:443` for `https`).
  - Improves URL-equivalence dedupe for grounding sources.
- Test changes:
  - Added focused normalization tests for both default port cases.
- Files changed:
  - `src/thegent/routing/grounding.py`
  - `tests/test_wl119_grounding_sources.py`

### WL-120: checkpoint ledger update for wave-12 slices

- Docs changes:
  - Updated current checkpoint table to wave-12 state descriptions for WL-115/116/118/119/120.
  - Extended modernization checkpoint ledger table with wave-12 rows.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation Commands

1. Compile checks

- `python -m py_compile src/thegent/cli/apps/bench.py src/thegent/cli/commands/run_output_helpers.py src/thegent/doctor.py src/thegent/routing/grounding.py`

2. WL-focused tests

- `./.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py`

## Constraints Check

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-115, WL-116, WL-118, WL-119, WL-120 slices and focused tests/docs.
