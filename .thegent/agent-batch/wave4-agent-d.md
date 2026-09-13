# Wave-4 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: canonical max-lines developer command path in docs

- Added canonical task path documentation:
  - `docs/guides/QUALITY_ASSURANCE.md` now documents `task quality:max-lines` as the single developer entrypoint.
- Restored explicit task wiring for that path:
  - Added `quality:max-lines` task in `Taskfile.yml`.
  - Wired `quality_project` to invoke `quality:max-lines`.
- Updated wiring assertion test to include docs contract:
  - `tests/test_wl122_max_lines_wiring.py` now asserts presence of `task quality:max-lines` in QA docs.

### 2) WL-104: session/list stub method contract + tests

- Kept `session/list` in agent-server supported-not-implemented set (`src/thegent/protocols/jsonrpc_agent_server.py`).
- Expanded contract tests:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`
  - Added assertion that `config/read` includes `session/list` in `not_implemented_methods`.
  - Added explicit `session/list` not-implemented response contract test (`-32004`, method echo).

### 3) WL-106: CLI wiring for fork/rollback stubs calling SessionManager APIs

- Added CLI command implementations:
  - `src/thegent/cli/commands/cli.py`
  - `session_fork_cmd(session_id, from_turn, new_session_id)`
  - `session_rollback_cmd(session_id, n_turns)`
  - Both instantiate `SessionManager` and call `fork_session`/`rollback_session` directly.
  - Fail-loud behavior on `SessionManagerError` with exit code 2.
- Exposed run-stream commands:
  - `src/thegent/cli/apps/run.py`
  - `thegent run fork ...`
  - `thegent run rollback ...`
- Exported command symbols:
  - `src/thegent/cli/__init__.py`
- Added focused wiring/API-call tests:
  - `tests/test_wl106_session_cli_wiring.py`

### 4) WL-111: MCP skill tool schema docs + registry smoke tests

- Added schema docs:
  - `docs/reference/MCP_SKILL_TOOL_SCHEMAS.md`
  - Documents input/output schema for `thegent_list_skills` and `thegent_activate_skill`.
- Added registry smoke tests through live server registry listing:
  - `tests/mcp/test_tools_skills_registry_smoke.py`
  - Confirms both tools appear in `mcp.list_tools()`.
  - Confirms activate tool requires `skill_name` string and list tool has object/no-additional-properties schema.

### 5) WL-117: VSCode command registration smoke + README run steps

- Added README run steps:
  - `extensions/vscode/README.md`
  - `npm run lint` and `npm run test` documented.
- Strengthened command registration smoke test:
  - `extensions/vscode/test/protocolClient.test.js`
  - Verifies contributed command IDs in `package.json` are present in activation events and registered via `registerCommand(...)` in extension source.
  - Verifies README run-step commands are present.

## Focused Validation

- `python -m py_compile src/thegent/cli/apps/run.py src/thegent/cli/commands/cli.py tests/test_wl106_session_cli_wiring.py tests/test_wl122_max_lines_wiring.py tests/protocols/test_jsonrpc_agent_server_contract.py tests/mcp/test_tools_skills_registry_smoke.py` (pass)
- `uv run pytest -q tests/protocols/test_jsonrpc_agent_server_contract.py tests/session/test_session_manager.py tests/test_wl106_session_cli_wiring.py tests/mcp/test_tools_skills_contract.py tests/mcp/test_tools_skills_registry_smoke.py tests/test_wl122_max_lines_wiring.py` (pass: 25 passed)
- `cd extensions/vscode && npm run test` (pass: `protocolClient scaffold checks passed`)

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to requested WL items; unrelated workspace edits were left untouched.

## Files Added

- `docs/reference/MCP_SKILL_TOOL_SCHEMAS.md`
- `tests/mcp/test_tools_skills_registry_smoke.py`
- `tests/test_wl106_session_cli_wiring.py`

## Files Updated

- `Taskfile.yml`
- `docs/guides/QUALITY_ASSURANCE.md`
- `extensions/vscode/README.md`
- `extensions/vscode/test/protocolClient.test.js`
- `src/thegent/cli/__init__.py`
- `src/thegent/cli/apps/run.py`
- `src/thegent/cli/commands/cli.py`
- `tests/protocols/test_jsonrpc_agent_server_contract.py`
- `tests/test_wl122_max_lines_wiring.py`
