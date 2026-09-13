# Wave-11 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: Canonical CI wiring reinforcement (Task runner contract)

- Tightened fail-closed checker behavior in:
  - `scripts/check_wl122_max_lines_canonical_path.py`
- Added requirement:
  - If CI runs `task quality:max-lines`, it must install Task via `arduino/setup-task@v2`.
- Added focused tests in:
  - `tests/test_wl122_max_lines_ci_path.py`
- New test coverage:
  - Missing Task setup action fails canonical CI contract check.

### 2) WL-104: JSON-RPC request contract reinforcement

- Tightened daemon contract in:
  - `src/thegent/protocols/jsonrpc_agent_server.py`
- Added fail-loud checks:
  - Request `id` must be JSON-RPC scalar (`string`/`number`/`null`), otherwise `Invalid Request`.
  - `turn/submit` `requires_approval` must be boolean when provided.
- Added focused tests in:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`
- New test coverage:
  - Non-boolean `requires_approval` is rejected with `-32602` invalid params.
  - Invalid request `id` object is rejected with `-32600` invalid request.

### 3) WL-106: Session CLI boundary contract reinforcement

- Tightened command-boundary validation in:
  - `src/thegent/cli/commands/session_cmds.py`
  - `src/thegent/cli/commands/cli.py`
- Added fail-loud checks:
  - `session_fork_cmd` rejects blank `session_id`.
  - `session_rollback_cmd` rejects blank `session_id`.
  - `session_fork_cmd` trims and rejects blank explicit `--new-session-id`.
- Added focused tests in:
  - `tests/test_wl106_session_cli_wiring.py`
- New test coverage:
  - Blank `session_id` fork/rollback paths fail with exit code `2` and do not call SessionManager.

### 4) WL-111: MCP skill list ordering contract reinforcement

- Tightened deterministic ordering in:
  - `src/thegent/mcp/server/tools_skills.py`
- Added canonical rule:
  - Skill lists are sorted case-insensitively by `name` (stable output contract).
- Added focused tests in:
  - `tests/mcp/test_tools_skills_contract.py`
- Docs updated in:
  - `docs/reference/MCP_SKILL_TOOL_SCHEMAS.md`

### 5) WL-117: Extension quickstart metadata contract reinforcement

- Tightened metadata checker in:
  - `scripts/check_extension_package_metadata.py`
- Added canonical README Run Steps requirements:
  - Must include `npm run lint`
  - Must include `npm run test`
- Added focused tests in:
  - `tests/test_wl117_extension_package_metadata.py`
  - `tests/test_wl117_extension_readme_quickstart.py`

### 6) QA docs reinforcement

- Updated bundle notes in:
  - `docs/guides/QUALITY_ASSURANCE.md`
- Captured new WL-122/WL-104/WL-106/WL-111/WL-117 contract expectations.

## Focused Validation

- `uv run python scripts/check_wl122_max_lines_canonical_path.py --strict`
  - Pass: `ok: True`, `canonical invocations: 1`
- `uv run python scripts/check_extension_package_metadata.py --strict`
  - Pass: `ok: True`, `checked_extensions: vscode`
- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py`
  - Pass: `9 passed in 6.04s`
- `uv run pytest -q tests/protocols/test_jsonrpc_agent_server_contract.py`
  - Pass: `12 passed in 6.45s`
- `uv run pytest -q tests/test_wl106_session_cli_wiring.py tests/mcp/test_tools_skills_contract.py tests/test_wl117_extension_package_metadata.py tests/test_wl117_extension_readme_quickstart.py`
  - Pass: `29 passed in 27.76s`

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Edits were scoped to WL-122, WL-104, WL-106, WL-111, WL-117 surfaces + focused QA docs.
- Unrelated dirty workspace changes were left untouched.
