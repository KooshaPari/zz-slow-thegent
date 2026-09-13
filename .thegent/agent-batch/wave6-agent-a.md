# Wave 6 Agent A Report

## Scope Completed

### WL-102: SDK error type hierarchy + non-2xx mapping

- Added SDK HTTP error hierarchy in `packages/thegent-sdk/src/thegent_sdk/client.py`:
  - `ThegentRequestError`
  - `ThegentAuthenticationError`
  - `ThegentNotFoundError`
  - `ThegentRateLimitError`
  - `ThegentServerError`
- Added non-2xx response mapper for both sync/async request and stream paths.
- Added JSON-body detail extraction (`detail`/`error`/`message`) and preserved parsed error body on exceptions.
- Exported new error types from `packages/thegent-sdk/src/thegent_sdk/__init__.py`.
- Added/updated SDK tests in `packages/thegent-sdk/tests/test_client.py` for class mapping and detail parsing.

### WL-103: Persist `context_usage_ratio` in run registry/event payload path

- Extended run-event details builder to include `context_usage_ratio` when present.
- Wired `result.context_usage_ratio` through `run_impl` finish-event path into `RunRegistry.register_end(... event_details=...)`.
- Updated parity and integration tests:
  - `tests/test_wl116_audio_inputs.py`
  - `tests/test_wl119_grounding_sources.py`
  - `tests/test_wl125_run_event_helpers_parity.py`

### WL-105: Dynamic tool timeout/expiry behavior + tests

- Added timeout/expiry lifecycle metadata to dynamic tool calls:
  - `timeout_seconds`
  - `requested_at_utc`
  - `expires_at_utc`
- Added default timeout enforcement and validation in `DynamicToolRegistry`.
- Added expiry checks for pending/resolve paths; expired calls now fail deterministically.
- Extended tool-call request event payload with:
  - `timeoutSeconds`
  - `requestedAt`
  - `expiresAt`
- Added session handler support for `dynamic_tool_invoke` `timeout_seconds` input validation and expiry error handling during completion.
- Added/updated tests:
  - `tests/mcp/test_dynamic_tools.py`
  - `tests/mcp/test_tools_sessions_dynamic_registry.py`

### WL-101: `thegent skill list --json` + tests

- Added `--json` option to `thegent skill list` in `src/thegent/cli/apps/skills.py`.
- JSON mode emits machine-readable array payload (including empty-list output).
- Added tests in `tests/test_wl101_skill_selection_cli.py` for:
  - non-empty JSON list output
  - empty JSON list output

### WL-078: Baseline regression docs in CLI reference

- Added baseline-regression command docs + examples in `docs/site/guide/cli-reference.md`:
  - `task bench:baseline:refresh`
  - benchmark generation example (`scripts/benchmark_python_suite.py`)
  - regression gate example (`scripts/check_python_benchmark_regression.py`)
- Also documented `thegent skill list --json` in the same CLI reference.

## Focused Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py packages/thegent-sdk/src/thegent_sdk/__init__.py src/thegent/cli/apps/skills.py src/thegent/cli/services/run_event_helpers.py src/thegent/cli/commands/impl.py src/thegent/mcp/dynamic_tools.py src/thegent/mcp/server/tools_sessions.py`
  - Result: success
- `uv run pytest -q tests/mcp/test_dynamic_tools.py tests/mcp/test_tools_sessions_dynamic_registry.py`
  - Result: `16 passed`
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/test_wl101_skill_selection_cli.py tests/test_wl116_audio_inputs.py tests/test_wl119_grounding_sources.py tests/test_wl125_run_event_helpers_parity.py`
  - Result: `49 passed`

## Notes

- Did not edit `docs/reference/WORK_STREAM.md`.
- Kept changes scoped to WL-102, WL-103, WL-105, WL-101, and WL-078 deliverables.
