# Wave 12 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21
Owner: agent-b

## Objective

Delivered one additional contract-hardening slice per assigned item with focused tests/docs.

## WL-107: review issue-line contract hardening

- Hardened `issues[].line` validation to explicitly reject boolean values (prevent Python bool-as-int acceptance).
- Added focused validator test for boolean line rejection.

Files:

- `src/thegent/agents/review_output.py`
- `tests/test_wl107_review_output.py`

## WL-108: context usage bounds contract hardening

- Hardened context usage payload builder to reject invalid states where `used > max`.
- Added focused test for over-capacity reject path.

Files:

- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`

## WL-109: symbol file-path normalization hardening

- Hardened symbol match normalization to trim whitespace from `file_path` before contract validation/output.
- Added focused test asserting whitespace-stripped `file_path` in lookup results.

Files:

- `src/thegent/mcp/lsp_tools.py`
- `tests/test_wl109_mcp_lsp_tools.py`

## WL-110: resume contract string normalization hardening

- Added shared contract-string normalization helper.
- Hardened latest-session selection + resume flow to trim `session_id`/`run_id` contract strings before resolution and registry registration.
- Added focused resume test covering whitespace-padded contract strings.

Files:

- `src/thegent/cli/commands/impl.py`
- `tests/test_wl110_resume_contract.py`

## WL-114: codex image-arg input contract hardening

- Hardened `build_codex_image_args` to reject empty/non-string image path values.
- Added focused test for both blank-string and non-string reject cases.

Files:

- `src/thegent/agents/image_inputs.py`
- `tests/test_wl114_image_flag.py`

## Focused Docs Update

- Added Wave 12 contract-hardening notes for WL-107/108/109/110/114.

File:

- `docs/guides/THGENT_CLI_REFERENCE.md`

## Validation

- `python -m py_compile src/thegent/agents/review_output.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/lsp_tools.py src/thegent/cli/commands/impl.py src/thegent/agents/image_inputs.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
  - Result: pass
- `python -m pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
  - Result: `99 passed, 6 warnings`

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept edits scoped to WL-107/WL-108/WL-109/WL-110/WL-114 contract hardening, focused tests/docs, and this wave report.
