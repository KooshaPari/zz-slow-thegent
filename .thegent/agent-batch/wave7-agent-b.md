# Wave 7 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21

## Scope Completed

### WL-107: enforce strict review output contract (no legacy alias)

- Tightened `validate_review_output(...)` in `src/thegent/agents/review_output.py`:
  - requires exact top-level keys: `summary`, `overall_rating`, `issues`
  - rejects unsupported top-level keys (including legacy `rating`)
  - keeps strict issue field validation unchanged
- Updated tests in `tests/test_wl107_review_output.py`:
  - now asserts legacy `rating` alias is rejected
  - now asserts unsupported top-level key handling is explicit
- Updated docs in `docs/guides/THGENT_CLI_REFERENCE.md` to state strict key requirements for review JSON.

### WL-108: guard invalid context window payloads

- Hardened `build_context_usage_payload(...)` in `src/thegent/cli/services/run_input_helpers.py`:
  - returns `None` when `max_tokens <= 0` to avoid emitting invalid context window contracts
- Added test coverage in `tests/test_wl108_wl114_slices.py` for non-positive window handling.

### WL-109: clearer malformed diagnostics coordinate errors

- Hardened diagnostics normalization in `src/thegent/mcp/lsp_tools.py`:
  - added explicit coercion helper for `line`/`character`
  - malformed string coordinates (e.g. `"x1"`) now fail with precise contract error messages
- Added focused test in `tests/test_wl109_mcp_lsp_tools.py` for non-integer-like line value failure.

### WL-110: reject whitespace-only resume prompts

- Hardened `resume_impl(...)` in `src/thegent/cli/commands/impl.py`:
  - `--prompt` values that are empty/whitespace-only now fail fast with actionable error
  - non-empty prompts are trimmed before send/skill augmentation
- Added focused contract test in `tests/test_wl110_resume_contract.py`.

### WL-114: normalize duplicate image inputs

- Hardened image normalization in `src/thegent/cli/services/run_input_helpers.py`:
  - de-duplicates normalized image inputs while preserving order
  - applies to both HTTPS URLs and resolved local paths
  - preserves strict HTTPS + extension + existence validation
- Added focused dedupe test in `tests/test_wl108_wl114_slices.py`.
- Updated docs in `docs/guides/THGENT_CLI_REFERENCE.md` to document duplicate normalization behavior.

## Files Changed

- `src/thegent/agents/review_output.py`
- `src/thegent/cli/services/run_input_helpers.py`
- `src/thegent/mcp/lsp_tools.py`
- `src/thegent/cli/commands/impl.py`
- `tests/test_wl107_review_output.py`
- `tests/test_wl108_wl114_slices.py`
- `tests/test_wl109_mcp_lsp_tools.py`
- `tests/test_wl110_resume_contract.py`
- `docs/guides/THGENT_CLI_REFERENCE.md`
- `.thegent/agent-batch/wave7-agent-b.md`

## Focused Validation

- `python -m py_compile src/thegent/agents/review_output.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/lsp_tools.py src/thegent/cli/commands/impl.py tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
  - Result: success
- `uv run pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py tests/test_wl114_image_flag.py`
  - Result: `74 passed` (warnings only)
- `uv run pytest -q tests/test_wl107_review_cmd.py tests/test_wl108_context_budget.py tests/test_wl109_lsp_tools.py tests/test_wl110_resume.py`
  - Result: `104 passed` (warnings only)

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept edits scoped to WL-107/WL-108/WL-109/WL-110/WL-114 surfaces and wave report path.
