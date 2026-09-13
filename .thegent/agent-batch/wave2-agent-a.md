# Wave 2 Agent A (2026-02-21)

## Completed slices

- WL-078
  - Hardened benchmark regression parser to fail fast on malformed payloads (`benchmarks` must be list, rows must be objects) and duplicate labels.
  - Added regression tests for malformed/duplicate-input behavior.
- WL-101
  - Made skill discovery deterministic by sorting directory iteration.
  - Added manifest name validation (empty/whitespace names are rejected).
  - Added `load_skill` input validation for empty/whitespace skill names.
  - Added unit tests for deterministic ordering and manifest/name validation behavior.
- WL-102
  - Implemented minimal typed SDK slice at `packages/thegent-sdk`:
    - `ThegentClient` with `run()` and `list_sessions()`.
    - Typed DTOs (`RunResult`, `SessionInfo`) and parsers.
    - Error contract (`ThegentClientError`, `ThegentHTTPError`) with explicit non-2xx failure semantics.
    - `py.typed` marker and package exports.
  - Added 10 unit tests with `httpx.MockTransport` covering success/failure contracts and request shape.
- WL-103
  - Added standalone `ContextCompactor` primitive (`usage_ratio` + deterministic compaction) with bounded summary form to guarantee shrink behavior.
  - Added focused unit suite for threshold behavior, min-turn behavior, ratio checks, constructor validation, and compaction reduction.
- WL-105
  - Extended dynamic tool registry with:
    - `pending_calls_for_session()`
    - `resolve_tool_call_for_session()` ownership enforcement
    - `clear_session()` lifecycle cleanup for tools + pending calls
  - Added tests for session-scoped pending calls, ownership checks, and cleanup behavior.

## Validation

- `uv run pytest -q tests/performance/test_python_benchmark_regression.py`
  - Passed: `4 passed`
- `uv run pytest -q tests/test_unit_skills.py -k "skill_md_only or missing_json or invalid_json or sorts_results or empty_manifest_name or rejects_empty_name"`
  - Passed: `7 passed, 13 deselected`
- `uv run pytest -q tests/mcp/test_dynamic_tools.py`
  - Passed: `7 passed`
- `uv run pytest -q tests/test_wl103_context_compactor.py`
  - Passed: `7 passed`
- `uv run pytest -q packages/thegent-sdk/tests/test_client.py`
  - Passed: `10 passed`
- `uv run python -m py_compile scripts/check_python_benchmark_regression.py src/thegent/skills/discovery.py src/thegent/mcp/dynamic_tools.py src/thegent/agents/context_compactor.py packages/thegent-sdk/src/thegent_sdk/client.py packages/thegent-sdk/src/thegent_sdk/types.py`
  - Passed (exit 0)

## Blockers

- WL-102 dependency note:
  - SDK currently assumes `/v1/run` and `/v1/sessions` HTTP routes. Final endpoint contract confirmation with MCP/server HTTP surface is still required before productionizing.
- WL-103 dependency note:
  - Compactor is implemented as an isolated primitive; runner integration and provider/tokenizer calibration remain a follow-up slice.
- WL-105 dependency note:
  - Registry primitives are complete for session-local lifecycle; wiring into full MCP session-init/dispatch path remains a follow-up integration step.

## Exact files touched

- `scripts/check_python_benchmark_regression.py`
- `tests/performance/test_python_benchmark_regression.py`
- `src/thegent/skills/discovery.py`
- `tests/test_unit_skills.py`
- `packages/thegent-sdk/pyproject.toml`
- `packages/thegent-sdk/README.md`
- `packages/thegent-sdk/src/thegent_sdk/__init__.py`
- `packages/thegent-sdk/src/thegent_sdk/client.py`
- `packages/thegent-sdk/src/thegent_sdk/types.py`
- `packages/thegent-sdk/src/thegent_sdk/py.typed`
- `packages/thegent-sdk/tests/test_client.py`
- `src/thegent/agents/context_compactor.py`
- `tests/test_wl103_context_compactor.py`
- `src/thegent/mcp/dynamic_tools.py`
- `tests/mcp/test_dynamic_tools.py`
