# Wave 13 Agent C Report (WL-115, WL-116, WL-118, WL-119, WL-120)

Date: 2026-02-21

## Scope Completed

### WL-115: bench rich compare winner-margin visibility

- Code changes:
  - Added explicit `Winner Margin` row in rich `bench compare` table output, showing both seconds and percent.
  - Keeps existing delta row and JSON payload fields; adds a direct operator-readable summary row.
- Test changes:
  - Extended rich-table rendering test to assert `Winner Margin` is present.
- Files changed:
  - `src/thegent/cli/apps/bench.py`
  - `tests/test_wl115_bench_cli.py`

### WL-116: transcript empty-payload wording clarity

- Code changes:
  - `format_transcript_summary_line` now renders `Transcript input: empty transcript ...` when `transcript_length_chars == 0` with valid positive `source_count`.
  - Avoids ambiguous `0 chars` phrasing in human-facing output.
- Test changes:
  - Added focused coverage for empty transcript wording.
- Files changed:
  - `src/thegent/cli/commands/run_output_helpers.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-118: doctor actionable-hint index tags for checkpoint/readback

- Code changes:
  - Actionable hints now include deterministic displayed index tags (`[1/3]`, `[2/3]`, `[3/3]`) for the shown subset.
  - Overflow line remains unchanged for hidden hints.
- Test changes:
  - Updated ordering assertion to indexed format.
  - Added explicit assertions for indexed actionable-hint lines in overflow scenario.
- Files changed:
  - `src/thegent/doctor.py`
  - `tests/test_wl118_ollama_doctor_slice.py`

### WL-119: root trailing-slash grounding URL normalization

- Code changes:
  - `normalize_grounding_source_url` now collapses root-only trailing slash variants (`https://a.example/` -> `https://a.example`) when no query/fragment is present.
  - Preserves non-root paths like `/path/`.
- Test changes:
  - Added normalization tests for root slash collapsing and path preservation.
  - Added human-output dedupe test for root slash variants.
- Files changed:
  - `src/thegent/routing/grounding.py`
  - `tests/test_wl119_grounding_sources.py`
  - `tests/test_wl119_run_cli_output.py`

### WL-120: checkpoint ledger update for wave-13 slices

- Docs changes:
  - Updated current checkpoint table states to wave-13 descriptions for WL-115/116/118/119/120.
  - Extended modernization checkpoint ledger section to include wave-13 rows.
- Files changed:
  - `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`

## Focused Validation Commands

1. Compile checks

- `python -m py_compile src/thegent/cli/apps/bench.py src/thegent/cli/commands/run_output_helpers.py src/thegent/doctor.py src/thegent/routing/grounding.py`

2. WL-focused tests

- `./.venv/bin/pytest -q tests/test_wl115_bench_cli.py tests/test_wl119_run_cli_output.py tests/test_wl118_ollama_doctor_slice.py tests/test_wl119_grounding_sources.py`
- Result: `41 passed in 4.86s`

## Constraints Check

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-115, WL-116, WL-118, WL-119, WL-120 slices and focused tests/docs.
