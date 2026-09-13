# Wave-13 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: Canonical pre-commit entry strictness reinforcement

- Tightened canonical checker in:
  - `scripts/check_wl122_max_lines_canonical_path.py`
- New contract:
  - `.pre-commit-config.yaml` must contain exact canonical entry line `entry: task quality:max-lines` (no extra args).
- Added focused coverage in:
  - `tests/test_wl122_max_lines_ci_path.py`

### 2) WL-104: JSON-RPC whitespace-ID normalization reinforcement

- Tightened daemon request validation in:
  - `src/thegent/protocols/jsonrpc_agent_server.py`
- New contract:
  - Whitespace-only `session_id` / `turn_id` / `approval_id` params are invalid (treated as missing required field).
- Added focused coverage in:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`

### 3) WL-106: Session fork identity-collision reinforcement

- Tightened session fork command boundary in:
  - `src/thegent/cli/commands/session_cmds.py`
  - `src/thegent/cli/commands/cli.py`
- New contract:
  - `session_fork_cmd` rejects `--new-session-id` when it matches source `session_id`.
- Added focused coverage in:
  - `tests/test_wl106_session_cli_wiring.py`

### 4) WL-111: MCP skill name canonicalization reinforcement

- Tightened skill list contract in:
  - `src/thegent/mcp/server/tools_skills.py`
- New contract:
  - Skill names are whitespace-trimmed before output sorting and duplicate detection.
  - Duplicate detection is fail-loud after trim + case-insensitive normalization.
- Added focused coverage in:
  - `tests/mcp/test_tools_skills_contract.py`

### 5) WL-117: Extension README duplicate run-step reinforcement

- Tightened extension metadata checker in:
  - `scripts/check_extension_package_metadata.py`
- New contract:
  - README `## Run Steps` must not repeat the same `npm run <script>` command.
- Added focused coverage in:
  - `tests/test_wl117_extension_package_metadata.py`

### 6) Focused QA docs update

- Updated canonical contract bundle notes in:
  - `docs/guides/QUALITY_ASSURANCE.md`
- Added the new WL-122/WL-104/WL-106/WL-111/WL-117 reinforcement notes above.

## Focused Validation

- `uv run python -m py_compile scripts/check_wl122_max_lines_canonical_path.py src/thegent/protocols/jsonrpc_agent_server.py src/thegent/cli/commands/cli.py src/thegent/cli/commands/session_cmds.py src/thegent/mcp/server/tools_skills.py scripts/check_extension_package_metadata.py`
  - Pass
- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py tests/protocols/test_jsonrpc_agent_server_contract.py tests/test_wl106_session_cli_wiring.py tests/mcp/test_tools_skills_contract.py tests/test_wl117_extension_package_metadata.py`
  - Pass: `62 passed in 2.09s`

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-122, WL-104, WL-106, WL-111, WL-117 contract surfaces, focused tests, QA notes, and this report file.
- Unrelated dirty workspace edits were left untouched.
