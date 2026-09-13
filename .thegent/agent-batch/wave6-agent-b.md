# Wave 6 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21

## Scope Completed

### WL-107: add CI-friendly `thegent review` nonzero behavior documentation/tests

- Added CI-focused review exit-code documentation in `docs/guides/THGENT_CLI_REFERENCE.md`:
  - `0` no issues
  - `1` issues found
  - `2` review output contract violation
  - passthrough of other non-zero runner failures
- Extended `tests/test_wl107_review_output.py`:
  - verifies `--format json` still exits `1` when issues exist.
  - verifies non-zero runner exit codes are propagated by `thegent review`.

### WL-108: add one helper API consolidating status/json context usage payload creation

- Added shared helper `build_context_usage_payload(...)` in `src/thegent/cli/services/run_input_helpers.py`.
- Refactored `append_context_usage(...)` to use the shared helper for JSON payload path.
- Updated `_format_context_usage_line(...)` in `src/thegent/cli/commands/cli.py` to use the same shared helper for status-line display path.
- Added focused helper/usage tests in `tests/test_wl108_wl114_slices.py`.

### WL-109: add LSP diagnostics output shape normalization tests

- Added normalization in `src/thegent/mcp/lsp_tools.py` for each diagnostic entry:
  - normalized keys/shape (`source`, `severity`, `message`, `line`, `character`, `file_path`)
  - severity alias normalization (e.g., `high` -> `error`, `low` -> `info`)
  - line/character bounds clamping
  - validation for malformed entries
- Added tests in `tests/test_wl109_mcp_lsp_tools.py`:
  - mixed-shape diagnostic normalization
  - rejection of non-object diagnostics
  - assertions for normalized defaults in payload shape

### WL-110: add `thegent resume --prompt` smoke test path

- Added run-subcommand smoke coverage in `tests/test_wl110_resume_contract.py`:
  - `thegent run resume <session> --prompt ...` passthrough to `resume_cmd` with expected args.

### WL-114: add model capability matrix note for image support and guard tests

- Added docs note in `docs/guides/THGENT_CLI_REFERENCE.md` clarifying `--image` guard behavior is driven by model capability matrix (`model_indices.json`, `vision` flags).
- Added guard tests in `tests/test_wl108_wl114_slices.py`:
  - unsupported agent rejection
  - accepted path for vision-capable model
  - existing non-vision rejection retained

## Files Changed

- `docs/guides/THGENT_CLI_REFERENCE.md`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/cli/services/run_input_helpers.py`
- `src/thegent/mcp/lsp_tools.py`
- `tests/test_wl107_review_output.py`
- `tests/test_wl108_wl114_slices.py`
- `tests/test_wl109_mcp_lsp_tools.py`
- `tests/test_wl110_resume_contract.py`
- `.thegent/agent-batch/wave6-agent-b.md`

## Focused Validation

- `python -m py_compile src/thegent/cli/services/run_input_helpers.py src/thegent/cli/commands/cli.py src/thegent/mcp/lsp_tools.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
  - Result: success.
- `uv run pytest -q tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py`
  - Result: `27 passed`.
- `uv run pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
  - Result: blocked during collection by existing app import issue in `src/thegent/cli/apps/main.py` (`AttributeError: 'function' object has no attribute 'command'` at module import); not introduced by this wave's edits.

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept edits scoped to WL-107/108/109/110/114 surfaces and wave report path.
