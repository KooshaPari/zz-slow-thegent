# Wave 9 Agent A Report

## Objective

Add one additional reliability/edge-case/doc/test slice for each work item: `WL-102`, `WL-103`, `WL-105`, `WL-101`, `WL-078`.

## Completed slices

### WL-102: SDK list-style error detail extraction

- Hardened HTTP error detail extraction to handle list payloads under `detail`/`error` (for example validation errors like `[{"msg": "..."}]`).
- Added coverage verifying list-based `detail` maps to `ThegentRequestError.detail`.
- Updated SDK README error-detail note for list-style validation payloads.

Files:

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/tests/test_client.py`
- `packages/thegent-sdk/README.md`

### WL-103: Context usage ratio range validation

- Tightened normalization so `context_usage_ratio` is only serialized when finite and within `[0.0, 1.0]`.
- Added regression tests proving out-of-range values are omitted.

Files:

- `src/thegent/cli/services/run_event_helpers.py`
- `tests/cli/services/test_run_event_helpers.py`

### WL-105: Strict boolean contract for dynamic tool completion

- Enforced that `resolve_tool_call(..., success=...)` requires a real boolean, rejecting truthy/falsy non-bool values.
- Added test coverage for non-boolean `success` rejection.

Files:

- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`

### WL-101: Shell-safe `skill select` usage hint

- Updated `thegent skill select` command hint to shell-quote selected skill names.
- Added test for names containing spaces to ensure generated command remains copy-safe.

Files:

- `src/thegent/cli/apps/skills.py`
- `tests/test_wl101_skill_selection_cli.py`

### WL-078: Regression threshold input validation

- Added core guard in `find_regressions` to reject invalid `max_regression_pct` values (must be finite and `>= 0`).
- Added CLI argument validation for invalid `--max-regression-pct` before file processing.
- Added tests for `NaN`, `inf`, and negative threshold inputs.

Files:

- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`

## Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/cli/services/run_event_helpers.py src/thegent/mcp/dynamic_tools.py src/thegent/cli/apps/skills.py scripts/check_python_benchmark_regression.py`
  - Result: success
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/cli/services/test_run_event_helpers.py tests/mcp/test_dynamic_tools.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py`
  - Result: `76 passed`

## Constraints check

- Did not edit `docs/reference/WORK_STREAM.md`.
