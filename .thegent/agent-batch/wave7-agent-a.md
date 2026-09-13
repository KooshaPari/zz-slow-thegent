# Wave 7 Agent A Report

## Completed slices

### WL-102: SDK error detail extraction hardening

- Improved SDK HTTP error parsing to extract nested `error.message` when present in non-2xx JSON payloads.
- Added coverage for nested error payload mapping so typed exceptions preserve actionable detail.

### WL-105: Dynamic tool input/timeout validation hardening

- Strengthened `DynamicToolRegistry` validation:
  - `default_timeout_seconds` must be finite and `> 0`.
  - per-call `timeout_seconds` must be finite and `> 0`.
  - `create_tool_call(...)` now requires non-empty `session_id`, non-empty `name`, and object-shaped `arguments`.
- Added focused tests for non-finite timeouts and invalid call payload shapes.

### WL-103: Context usage ratio serialization safety

- Updated run-event detail helper to only emit `context_usage_ratio` when it is finite.
- Added focused tests for NaN omission and finite rounding behavior.

### WL-101: Deterministic skill list JSON output

- `thegent skill list --json` now emits skills in deterministic name-sorted order.
- Added test ensuring sorted output ordering in JSON mode.

### WL-078: Optional strict benchmark completeness gate

- Extended benchmark regression checker with `--require-complete-baseline`.
- In strict mode, missing labels from current benchmark payload are treated as regressions (`reason: missing_from_current`).
- Added tests for complete-baseline enforcement path.
- Updated docs with strict completeness command examples/guidance.

## Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/mcp/dynamic_tools.py src/thegent/cli/services/run_event_helpers.py src/thegent/cli/apps/skills.py scripts/check_python_benchmark_regression.py`
  - Result: success
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/mcp/test_dynamic_tools.py tests/cli/services/test_run_event_helpers.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py`
  - Result: `61 passed`

## Blockers

- None.

## Exact files touched

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/tests/test_client.py`
- `packages/thegent-sdk/README.md`
- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`
- `src/thegent/cli/services/run_event_helpers.py`
- `tests/cli/services/test_run_event_helpers.py`
- `src/thegent/cli/apps/skills.py`
- `tests/test_wl101_skill_selection_cli.py`
- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`
- `docs/site/guide/cli-reference.md`
- `docs/guides/QUALITY_ASSURANCE.md`
- `.thegent/agent-batch/wave7-agent-a.md`

## Constraints check

- Did not edit `docs/reference/WORK_STREAM.md`.
