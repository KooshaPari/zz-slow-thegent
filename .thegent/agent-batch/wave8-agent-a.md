# Wave 8 Agent A Report

## Objective

Deepen reliability + docs + tests for WL-102, WL-103, WL-105, WL-101, WL-078 by closing one additional edge case per work item.

## Completed slices

### WL-102: SDK nested error detail extraction hardening

- Expanded non-2xx JSON error detail extraction to handle nested `error.detail` and `error.reason` (in addition to `error.message`).
- Added test coverage for nested `error.detail` mapping to `ThegentRequestError.detail`.
- Updated SDK README error-detail note to include nested `error.detail` behavior.

Files:

- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/tests/test_client.py`
- `packages/thegent-sdk/README.md`

### WL-103: context usage ratio serialization robustness for malformed inputs

- Hardened run-event detail serialization to skip invalid `context_usage_ratio` values that cannot be safely converted to finite floats.
- Added regression test proving non-numeric values are omitted instead of raising.

Files:

- `src/thegent/cli/services/run_event_helpers.py`
- `tests/cli/services/test_run_event_helpers.py`

### WL-105: dynamic tool/session identifier normalization

- Normalized/trimmed `session_id` and tool `name` during registration and call creation.
- Ensures calls and lookups remain consistent even when clients send whitespace-padded identifiers.
- Added focused ownership/pending-path test for normalized identifiers.

Files:

- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`

### WL-101: deterministic `skill list --json` ordering under case-colliding names

- Strengthened JSON listing sort key to deterministic two-level ordering: `(name.lower(), name)`.
- Added test for stable ordering when names differ only by case (`Alpha` vs `alpha`).

Files:

- `src/thegent/cli/apps/skills.py`
- `tests/test_wl101_skill_selection_cli.py`
- `docs/site/guide/cli-reference.md`

### WL-078: benchmark checker input validation for invalid numeric payloads

- Hardened regression checker row parsing to reject non-finite or negative `avg_microseconds` values.
- Added tests for NaN, infinity, and negative values.
- Documented value constraints in QA and CLI reference docs.

Files:

- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`
- `docs/site/guide/cli-reference.md`
- `docs/guides/QUALITY_ASSURANCE.md`

## Validation

- `uv run python -m py_compile packages/thegent-sdk/src/thegent_sdk/client.py src/thegent/cli/services/run_event_helpers.py src/thegent/mcp/dynamic_tools.py src/thegent/cli/apps/skills.py scripts/check_python_benchmark_regression.py`
  - Result: success
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py tests/cli/services/test_run_event_helpers.py tests/mcp/test_dynamic_tools.py tests/test_wl101_skill_selection_cli.py tests/performance/test_python_benchmark_regression.py`
  - Result: `68 passed`

## Constraints check

- Did not edit `docs/reference/WORK_STREAM.md`.
