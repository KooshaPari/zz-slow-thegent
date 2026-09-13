# Wave 13 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21
Owner: agent-b

## Objective

Delivered one additional contract-hardening slice per assigned item with focused tests/docs.

## WL-107: review output string canonicalization hardening

- Hardened review payload normalization to trim validated non-empty string fields before returning contract output.
- Covered `summary`, `issues[].file`, `issues[].message`, and `issues[].suggestion` in focused validation coverage.

Files:

- `src/thegent/agents/review_output.py`
- `tests/test_wl107_review_output.py`

## WL-108: context ratio consistency hardening

- Hardened context-usage payload builder to reject inconsistent externally supplied ratio values when they disagree with computed `used/max`.
- Contract now keeps computed ratio unless supplied ratio is within a small consistency tolerance.

Files:

- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`

## WL-109: symbol coordinate strictness hardening

- Hardened LSP symbol match normalization to reject fractional float coordinates (`line`/`character`) instead of silently truncating.
- Added focused failing-contract coverage for fractional coordinate input.

Files:

- `src/thegent/mcp/lsp_tools.py`
- `tests/test_wl109_mcp_lsp_tools.py`

## WL-110: session list contract normalization hardening

- Hardened `session_list_impl` to normalize/trim state and registry contract IDs (`session_id`, `run_id`) before emitting rows.
- Added focused list-path coverage for whitespace-padded contract values.

Files:

- `src/thegent/cli/commands/impl.py`
- `tests/test_wl110_resume_contract.py`

## WL-114: codex image arg canonicalization hardening

- Hardened codex `--image` argument builder to trim path values before forwarding.
- Added focused test for whitespace-trimmed image arg output.

Files:

- `src/thegent/agents/image_inputs.py`
- `tests/test_wl114_image_flag.py`

## Focused Docs Update

- Added Wave 13 contract-hardening notes for WL-107/108/109/110/114.

File:

- `docs/guides/THGENT_CLI_REFERENCE.md`

## Validation

- `python -m py_compile src/thegent/agents/review_output.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/lsp_tools.py src/thegent/cli/commands/impl.py src/thegent/agents/image_inputs.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
  - Result: pass
- `python -m pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
  - Result: `104 passed, 6 warnings`

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept edits scoped to WL-107/WL-108/WL-109/WL-110/WL-114 contract hardening, focused tests/docs, and this wave report.
