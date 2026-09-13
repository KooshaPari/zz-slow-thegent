# WL Wave 110-119 - Lane F

Date: 2026-02-23
Lane: F
Scope: WL-110..119 (targeted high-confidence hardening slices)

## Summary

Implemented 2 high-confidence items with code, tests, and validation evidence:

- WL-118: Doctor actionable-hint dedupe now normalizes leading list markers (`-`, `*`, `1.`/`1)`) to avoid duplicate operator guidance lines.
- WL-119: Grounding URL normalization now unwraps common wrapped literals (`<url>`, `(url)`, `[url]`) before canonicalization/dedupe.

## Item 1 - WL-118

Status: Completed

### Change

- Updated `src/thegent/doctor.py` hint-normalization logic in `_display_results` to strip leading list markers before dedupe key generation.

### Why

- Different checks can emit the same hint with minor formatting variations (`1. ...` vs `- ...`). These should collapse into one actionable hint.

### Tests

- Added `test_display_results_deduplicates_actionable_hints_with_leading_list_markers` in `tests/test_wl118_ollama_doctor_slice.py`.

## Item 2 - WL-119

Status: Completed

### Change

- Updated `src/thegent/routing/grounding.py` in `normalize_grounding_source_url` to unwrap enclosing `< >`, `( )`, and `[ ]` wrappers before URL normalization.

### Why

- Provider metadata and human-authored payloads frequently include wrapped URL literals; these should normalize to the same canonical source value.

### Tests

- Added `test_normalize_grounding_source_url_unwraps_wrapped_literals` in `tests/test_wl119_grounding_sources.py`.

## Evidence

Commands run:

- `./.venv/bin/python -m pytest tests/test_wl118_ollama_doctor_slice.py -q`
  - Result: `10 passed in 89.13s`
- `./.venv/bin/python -m pytest tests/test_wl119_grounding_sources.py -q`
  - Result: `11 passed in 93.25s`

Touched files:

- `src/thegent/doctor.py`
- `src/thegent/routing/grounding.py`
- `tests/test_wl118_ollama_doctor_slice.py`
- `tests/test_wl119_grounding_sources.py`
- `docs/reports/wl-wave-110-119-lane-f.md`

## Notes

- Workspace contained unrelated in-flight changes at start; lane-F work was limited strictly to files above.
- No commits created.
