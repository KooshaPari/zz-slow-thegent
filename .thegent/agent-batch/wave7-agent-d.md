# Wave-7 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: strengthen canonical max-lines contract across CI + pre-commit

- Updated pre-commit to call the canonical task path instead of direct script invocation:
  - `.pre-commit-config.yaml`
  - `max-lines-gate` hook now uses `task quality:max-lines`.
- Hardened canonical-path checker:
  - `scripts/check_wl122_max_lines_canonical_path.py`
  - Checker now validates all of the following:
    - CI invokes `task quality:max-lines` exactly once.
    - CI runs `scripts/check_wl122_max_lines_canonical_path.py --strict`.
    - CI does not invoke `scripts/max-lines-gate.sh` directly.
    - pre-commit defines `max-lines-gate` and routes through `task quality:max-lines`.
- Extended checker tests:
  - `tests/test_wl122_max_lines_ci_path.py`
  - Added pass/fail cases for strict checker presence and pre-commit canonical wiring.
- Restored quality-lane contract steps in CI:
  - `.github/workflows/ci.yml`
  - Re-added strict WL-122 checker step and canonical max-lines task step.

### 2) WL-104: expand JSON-RPC/CLI contract coverage for `agent-server`

- Extended protocol contract tests:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`
  - Added coverage for:
    - notification-style `turn/submit` (no `id`) returning no response but emitting notifications and mutating session history.
    - invalid `params` type (`params` not object) returning `-32602` with stable `params_must_be_object` reason.
- Added CLI wiring contract test for `thegent agent-server`:
  - `tests/test_wl104_agent_server_cli_wiring.py`
  - Static passthrough check ensures command exists and exits via `serve_stdio()` return code.

### 3) WL-106: fail-loud collision guard for session IDs

- Tightened session manager semantics to prevent silent overwrite of existing sessions:
  - `src/thegent/session/manager.py`
  - Added `SessionAlreadyExistsError` for duplicate IDs in both `create_session()` and `fork_session(..., new_session_id=...)`.
- Exported new error in session package surface:
  - `src/thegent/session/__init__.py`
- Added focused tests:
  - `tests/session/test_session_manager.py`
  - New checks for duplicate create/fork target IDs failing loudly.

### 4) WL-111: tighten skill activation input contract + docs

- Added explicit runtime type validation for `skill_name`:
  - `src/thegent/mcp/server/tools_skills.py`
  - Non-string values now return structured fail-loud error payload instead of raising on `.strip()`.
- Extended contract tests:
  - `tests/mcp/test_tools_skills_contract.py`
  - Added non-string `skill_name` error case.
- Updated reference schema docs with exact invalid-type error example:
  - `docs/reference/MCP_SKILL_TOOL_SCHEMAS.md`

### 5) WL-117: enforce extension README quickstart contract in metadata checker

- Enhanced metadata checker to validate extension README quickstart contract:
  - `scripts/check_extension_package_metadata.py`
  - Now enforces:
    - `README.md` exists.
    - `## Run Steps` includes at least one `npm run <script>` command.
    - each referenced script exists in `package.json` scripts.
- Expanded checker tests:
  - `tests/test_wl117_extension_package_metadata.py`
  - Added case for README script reference drift (`npm run package` missing from scripts).
- Existing quickstart contract test remains in place:
  - `tests/test_wl117_extension_readme_quickstart.py`

## Docs Updated

- `docs/guides/QUALITY_ASSURANCE.md`
  - Clarified that pre-commit/CI should use canonical `task quality:max-lines` path rather than direct script invocation.

## Focused Validation

- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py` (pass: 4 passed)
- `uv run python scripts/check_wl122_max_lines_canonical_path.py --strict` (pass)
- `uv run pytest -q tests/protocols/test_jsonrpc_agent_server_contract.py tests/test_wl104_agent_server_cli_wiring.py` (pass: 9 passed)
- `uv run pytest -q tests/session/test_session_manager.py tests/test_wl106_session_cli_wiring.py tests/test_wl106_top_level_passthrough.py` (pass: 16 passed)
- `uv run pytest -q tests/mcp/test_tools_skills_contract.py` (pass: 5 passed)
- `uv run pytest -q tests/mcp/test_tools_skills_contract.py tests/mcp/test_tools_skills_registry_smoke.py` (pass: 8 passed, warnings only)
- `uv run pytest -q tests/test_wl117_extension_package_metadata.py tests/test_wl117_extension_readme_quickstart.py` (pass: 5 passed)
- `uv run python scripts/check_extension_package_metadata.py --strict` (pass)
- `uv run python -m py_compile scripts/check_wl122_max_lines_canonical_path.py scripts/check_extension_package_metadata.py src/thegent/session/manager.py src/thegent/mcp/server/tools_skills.py` (pass)

## Notes

- `tests/mcp/test_tools_skills_registry_smoke.py` passed with existing `PydanticJsonSchemaWarning` warnings from FastMCP dependency defaults; no functional failures in this WL slice.

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were scoped to WL-122, WL-104, WL-106, WL-111, WL-117 surfaces and left unrelated workspace edits untouched.
