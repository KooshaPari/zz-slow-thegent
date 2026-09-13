# Wave 5 Agent B Report (WL-107, WL-108, WL-109, WL-110, WL-114)

Date: 2026-02-21

## Scope Completed

### WL-107: strengthen structured schema validation for review findings list

- Tightened `review_output` issue-object validation:
  - Rejects missing required keys in each `issues[]` entry.
  - Rejects unsupported/extra keys in each `issues[]` entry.
  - Enforces alias consistency when both `overall_rating` and legacy `rating` are present.
- Added focused tests:
  - Missing issue fields rejection.
  - Extra issue fields rejection.
  - Conflicting rating alias rejection.

### WL-108: ensure CLI status bar and JSON use same threshold logic path

- Updated `_format_context_usage_line()` to prefer recomputing display via shared `compute_context_usage_display(used, max)` whenever numeric values are present.
- This keeps CLI text output aligned with status-bar/JSON threshold mapping path.
- Added focused test to ensure stale precomputed `display` values are ignored when `used/max` are provided.

### WL-109: richer LSP backend unavailable remediation hints

- Improved MCP LSP remediation messaging:
  - Distinguishes unsupported `THGENT_LSP_ADAPTER` values with direct corrective action.
  - Provides richer unavailable-backend hints for non-Python/file-type cases.
- Fixed normalization gap in `lsp_tools` so adapter-resolution failures (including unsupported adapter config) also map through `LSP_BACKEND_UNAVAILABLE` contract.
- Added focused test for unsupported-adapter remediation path.

### WL-110: improve resume command UX messages for no sessions found

- `resume_impl()` now returns explicit actionable error payload when no resumable sessions exist:
  - Includes target session directory path.
  - Suggests `thegent run agent --bg "<prompt>"` and `--session-id` usage.
- Top-level `resume` passthrough now only forwards `skills` when provided, restoring compatibility for direct resume command passthrough behavior.
- Added focused test for no-session actionable messaging.

### WL-114: fix/advance failing bg image forwarding test path (`OptionInfo` issue)

- Fixed direct Python invocation path in `run_agent()` by unwrapping Typer `OptionInfo`/`ArgumentInfo` defaults to concrete default values.
- Prevents accidental truthy `OptionInfo` values from triggering wrong execution branches (e.g., remote path) and breaking bg image forwarding tests.
- Keeps `--image` forwarding to `bg_cmd` intact in test/direct-call flows.

## Files Changed

- `src/thegent/agents/review_output.py`
- `src/thegent/cli/apps/main.py`
- `src/thegent/cli/apps/run.py`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/cli/commands/impl.py`
- `src/thegent/mcp/lsp_tools.py`
- `src/thegent/mcp/server/tools_workstream_lsp.py`
- `tests/test_wl107_review_output.py`
- `tests/test_wl108_wl114_slices.py`
- `tests/test_wl109_mcp_lsp_tools.py`
- `tests/test_wl110_resume_contract.py`
- `.thegent/agent-batch/wave5-agent-b.md`

## Focused Validation

- `uv run pytest -q tests/test_wl107_review_output.py tests/test_wl108_wl114_slices.py tests/test_wl109_mcp_lsp_tools.py tests/test_wl110_resume_contract.py`
  - Result: `38 passed`.
- `python -m py_compile src/thegent/agents/review_output.py src/thegent/cli/apps/run.py src/thegent/cli/apps/main.py src/thegent/cli/commands/impl.py src/thegent/cli/commands/cli.py src/thegent/mcp/lsp_tools.py src/thegent/mcp/server/tools_workstream_lsp.py`
  - Result: success.

## Constraints Check

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept changes scoped to assigned WL-107/108/109/110/114 surfaces.
