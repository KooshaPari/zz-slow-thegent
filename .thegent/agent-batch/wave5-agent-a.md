# Wave 5 Agent A Report

## Scope Completed

### WL-102: Async streamed API surface parity docs/examples + integration fixture

- Added async client surface parity in SDK:
  - `AsyncThegentClient.run(...)`
  - `AsyncThegentClient.list_sessions()`
  - `AsyncThegentClient.resume(...)`
  - `AsyncThegentClient.run_stream(...)`
- Exported async client in SDK package exports.
- Added streamed parity docs/examples (sync + async) in SDK README.
- Added fixture-backed stream contract test fixture:
  - `packages/thegent-sdk/tests/fixtures/run_stream_success.jsonl`
- Added tests for sync + async fixture stream parsing.

### WL-103: Emit `context_usage_ratio` in JSON run output path

- Updated run payload helper so JSON run payloads now include top-level `context_usage_ratio` whenever available.
- Preserved existing `context_usage` object shape and ensured ratio consistency.
- Added test for ratio-only path (ratio present even without used/max fields).

### WL-105: Complete `dynamic_tool_complete` roundtrip (success + failure)

- Extended dynamic tool completion model to carry optional `error` payload.
- Added failure payload validation for `dynamic_tool_complete`:
  - If `success=false`, completion now requires `error` or `output`.
- Completion events now include `error` when supplied.
- Added roundtrip tests for failure payload and validation error path.

### WL-101: Skill list/select UX docs + unknown skill error tests

- Added docs/examples for `skill list` + `skill select` UX and explicit unknown skill behavior in:
  - `README.md`
  - `docs/site/guide/cli-reference.md`
  - `docs/site/guide/getting-started.md`
- Added unknown skill handling test for `skills_select("missing-skill")`.

### WL-078: Baseline refresh guardrails + tests

- Added overwrite guardrail to benchmark suite script:
  - Existing output file now fails unless `--overwrite` is passed.
- Updated refresh task to pass explicit overwrite:
  - `bench:baseline:refresh` now uses `--overwrite`.
- Added tests for guarded and forced overwrite paths.

## Files Changed

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/src/thegent_sdk/__init__.py`
- `packages/thegent-sdk/README.md`
- `packages/thegent-sdk/tests/test_client.py`
- `packages/thegent-sdk/tests/fixtures/run_stream_success.jsonl`
- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`
- `src/thegent/mcp/dynamic_tools.py`
- `src/thegent/mcp/server/tools_sessions.py`
- `tests/mcp/test_tools_sessions_dynamic_registry.py`
- `tests/test_wl101_skill_selection_cli.py`
- `README.md`
- `docs/site/guide/cli-reference.md`
- `docs/site/guide/getting-started.md`
- `scripts/benchmark_python_suite.py`
- `Taskfile.yml`
- `tests/test_wl078_benchmark_baseline_guardrails.py`

## Focused Validation

- `uv run pytest -q packages/thegent-sdk/tests/test_client.py`
  - Result: `19 passed`
- `uv run pytest -q tests/mcp/test_tools_sessions_dynamic_registry.py tests/test_wl108_wl114_slices.py tests/test_wl101_skill_selection_cli.py tests/test_wl078_benchmark_baseline_guardrails.py`
  - Result: `23 passed`
- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/dynamic_tools.py src/thegent/mcp/server/tools_sessions.py scripts/benchmark_python_suite.py`
  - Result: success

## Notes

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept changes scoped to requested wave-5 work items only.
