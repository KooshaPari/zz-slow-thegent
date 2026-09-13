# Wave 11 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21
Owner: agent-b

## Objective

Delivered one additional contract-hardening slice per assigned item with focused tests/docs.

## WL-107: review output contract hardening

- Hardened `overall_rating` validation to reject boolean values (bool is no longer accepted as integer).
- Added focused test for boolean-rating rejection path.

Files:

- `src/thegent/agents/review_output.py`
- `tests/test_wl107_review_cmd.py`

## WL-108: context usage payload contract hardening

- Hardened context payload builder to reject invalid `used/max` types and negative usage.
- Hardened ratio handling to ignore invalid ratio values (`NaN`, bool, non-numeric) and use computed `used/max` ratio.

Files:

- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`

## WL-109: MCP LSP symbol contract hardening

- Added strict normalization/validation for symbol lookup matches.
- Enforced object shape and required non-empty fields (`name`, `kind`, `file_path`) with normalized coordinates.

Files:

- `src/thegent/mcp/lsp_tools.py`
- `tests/test_wl109_mcp_lsp_tools.py`

## WL-110: resume timestamp ordering contract hardening

- Added normalized timestamp parsing for state/meta selection.
- Auto-selection now safely handles mixed naive and timezone-aware ISO timestamps by normalizing to UTC.

Files:

- `src/thegent/cli/commands/impl.py`
- `tests/test_wl110_resume_contract.py`

## WL-114: image input contract hardening

- Hardened image path normalization to reject non-string image inputs with clear error.
- Added focused rejection test.

Files:

- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`

## Focused Docs Update

- Added Wave 11 contract-hardening notes for WL-107/108/109/110/114.

Files:

- `docs/guides/THGENT_CLI_REFERENCE.md`

## Additional compatibility fix discovered during validation

- Re-exported review constants from `impl` to satisfy existing import contract tests.

File:

- `src/thegent/cli/commands/impl.py`

## Validation

- `python -m py_compile src/thegent/agents/review_output.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/lsp_tools.py src/thegent/cli/commands/impl.py tests/test_wl107_review_cmd.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
  - Result: pass
- `python -m py_compile src/thegent/cli/commands/impl.py`
  - Result: pass
- `python -m pytest -q tests/test_wl107_review_cmd.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
  - Result: `108 passed, 6 warnings`

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept edits scoped to assigned WL contract-hardening surfaces, focused tests/docs, and this wave report.
