# Wave-8 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: reinforced canonical max-lines wiring in CI + tests

- Reintroduced explicit canonical-gate steps in quality CI workflow:
  - `.github/workflows/ci.yml`
  - Added:
    - `Assert canonical max-lines CI path (WL-122)`
    - `Check extension package metadata sanity (WL-117)`
    - `Run max-lines gate via canonical task path (WL-122)`
- Hardened wiring contract test to validate behavior (not brittle labels):
  - `tests/test_wl122_max_lines_wiring.py`
  - Asserts Task setup via `arduino/setup-task@v2`
  - Asserts canonical WL-122/WL-117 step presence
  - Keeps fail-closed harness-gate shell contract assertions

### 2) WL-104: reinforced JSON-RPC CLI passthrough contract

- Extended CLI wiring test with runtime behavior check:
  - `tests/test_wl104_agent_server_cli_wiring.py`
  - New test monkeypatches `serve_stdio()` and verifies `thegent agent-server` exits with the same code and calls server exactly once.

### 3) WL-106: session fork/rollback contract stability maintained

- No code changes required this wave.
- Existing fork/rollback CLI + session manager contract tests revalidated as passing.

### 4) WL-111: reinforced MCP skill activation contract

- Extended MCP contract tests to enforce canonical skill-name normalization before backend invocation:
  - `tests/mcp/test_tools_skills_contract.py`
  - New assertion: surrounding whitespace is stripped before `activate_skill` backend call.

### 5) WL-117: extension metadata contract wiring reinforced via CI

- CI now explicitly runs strict extension metadata checker before harness gates:
  - `.github/workflows/ci.yml`

## Focused Validation

- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py tests/test_wl122_max_lines_wiring.py tests/test_wl104_agent_server_cli_wiring.py tests/mcp/test_tools_skills_contract.py`
  - Pass: `14 passed`
- `uv run python scripts/check_wl122_max_lines_canonical_path.py --strict`
  - Pass: `ok: True`, `canonical invocations: 1`
- `uv run pytest -q tests/protocols/test_jsonrpc_agent_server_contract.py tests/session/test_session_manager.py tests/test_wl106_session_cli_wiring.py tests/test_wl106_top_level_passthrough.py tests/mcp/test_tools_skills_registry_smoke.py tests/test_wl117_extension_package_metadata.py tests/test_wl117_extension_readme_quickstart.py`
  - Pass: `32 passed` (warnings only: existing FastMCP/Pydantic schema warnings)

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-122, WL-104, WL-106, WL-111, WL-117 contract/wiring surfaces; unrelated workspace edits were left untouched.
