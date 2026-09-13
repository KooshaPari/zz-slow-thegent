# Wave-12 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: Canonical max-lines pre-commit uniqueness reinforcement

- Tightened canonical checker in:
  - `scripts/check_wl122_max_lines_canonical_path.py`
- New contract:
  - `.pre-commit-config.yaml` must declare `max-lines-gate` exactly once.
- Added focused coverage in:
  - `tests/test_wl122_max_lines_ci_path.py`

### 2) WL-104: JSON-RPC approval diff contract reinforcement

- Tightened daemon request validation in:
  - `src/thegent/protocols/jsonrpc_agent_server.py`
- New contract:
  - `turn/submit` with `requires_approval=true` must include `diff`/`unified_diff`.
  - Diff value must be a non-empty string.
- Added focused coverage in:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`

### 3) WL-106: Session fork/rollback command-boundary reinforcement

- Tightened command guards in:
  - `src/thegent/cli/commands/session_cmds.py`
  - `src/thegent/cli/commands/cli.py`
- New contract:
  - `session_fork_cmd` rejects non-positive `from_turn` when provided.
  - `session_rollback_cmd` rejects non-positive `n_turns`.
- Added focused coverage in:
  - `tests/test_wl106_session_cli_wiring.py`

### 4) WL-111: MCP skill list ambiguity reinforcement

- Tightened skills list contract in:
  - `src/thegent/mcp/server/tools_skills.py`
- New contract:
  - Skill names must be non-empty strings.
  - Skill names must be unique case-insensitively (fail-loud on duplicates).
- Added focused coverage in:
  - `tests/mcp/test_tools_skills_contract.py`

### 5) WL-117: Extension README run-step order reinforcement

- Tightened extension metadata checker in:
  - `scripts/check_extension_package_metadata.py`
- New contract:
  - When both exist, README `Run Steps` must list `npm run lint` before `npm run test`.
- Added focused coverage in:
  - `tests/test_wl117_extension_package_metadata.py`

### 6) Focused QA docs updates

- Updated contract bundle notes in:
  - `docs/guides/QUALITY_ASSURANCE.md`
- Added notes for the WL-122/WL-104/WL-106/WL-111/WL-117 reinforcements above.

## Focused Validation

- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py tests/protocols/test_jsonrpc_agent_server_contract.py tests/test_wl106_session_cli_wiring.py tests/mcp/test_tools_skills_contract.py tests/test_wl117_extension_package_metadata.py`
  - Pass: `56 passed in 18.32s`

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-122, WL-104, WL-106, WL-111, WL-117 contract surfaces plus focused QA docs.
- Unrelated dirty workspace edits were left untouched.
