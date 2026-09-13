# Wave 11 Agent A Report

## Objective

Deliver one additional reliability/integration slice per item: `WL-102`, `WL-103`, `WL-105`, `WL-101`, `WL-078`, with focused tests/docs.

## Completed slices

### WL-102: SDK nested list detail extraction in object payloads

- Hardened SDK HTTP error detail extraction to recurse through nested dict/list structures for message fields (`msg`, `message`, `detail`, `reason`).
- Covers nested payload shapes like `{"error": {"detail": [{"msg": "..."}]}}`.
- Added focused unit test and updated SDK README note.

Files:

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/tests/test_client.py`
- `packages/thegent-sdk/README.md`

### WL-103: Context usage ratio fail-safe in JSON output fallback path

- Hardened `append_context_usage` fallback path to normalize `context_usage_ratio` before serialization.
- Invalid values (non-numeric, non-finite, bool, out-of-range) are now omitted instead of raising or emitting invalid payload values.
- Added focused parametric tests for malformed ratios when window fields are unavailable.

Files:

- `src/thegent/cli/services/run_input_helpers.py`
- `tests/test_wl108_wl114_slices.py`

### WL-105: Fail-loud session-id contract for registry lookup/cleanup APIs

- Enforced non-empty `session_id` validation in `list_dynamic_tools`, `pending_calls_for_session`, and `clear_session`.
- Prevents silent no-op/empty-list behavior on invalid session identifiers.
- Added focused tests for each fail-loud path.

Files:

- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`

### WL-101: Skill selection shell safety for control characters

- Added explicit guard in `thegent skill select` to reject control characters in skill names before printing shell command usage.
- Keeps the command output copy-safe and avoids malformed shell command hints.
- Added focused CLI test for newline/control-character rejection.

Files:

- `src/thegent/cli/apps/skills.py`
- `tests/test_wl101_skill_selection_cli.py`

### WL-078: Baseline validity contract for regression checker

- Strengthened regression checker to fail loudly when baseline benchmark averages are non-positive (`<= 0`).
- Retains current-payload allowance for zero values so improvements to zero are handled normally.
- Added focused tests for baseline-zero rejection and current-zero acceptance.

Files:

- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`

## Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/cli/services/run_input_helpers.py src/thegent/mcp/dynamic_tools.py src/thegent/cli/apps/skills.py scripts/check_python_benchmark_regression.py`
  - Result: success
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/test_wl108_wl114_slices.py tests/mcp/test_dynamic_tools.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py`
  - Result: `111 passed in 50.68s`

## Constraints check

- Did not edit `docs/reference/WORK_STREAM.md`.
