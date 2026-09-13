# Wave-6 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: enforce exactly one canonical max-lines invocation in CI workflow

- Tightened canonical-path checker semantics:
  - `scripts/check_wl122_max_lines_canonical_path.py`
  - Contract now fails when `.github/workflows/ci.yml` invokes `task quality:max-lines` more than once.
  - Contract still fails if canonical invocation is missing or if `scripts/max-lines-gate.sh` is called directly from CI.
- Expanded focused tests:
  - `tests/test_wl122_max_lines_ci_path.py`
  - Added explicit assertion for duplicate canonical invocations failing the check.

### 2) WL-104: add JSON-RPC `turn/submit` not-implemented contract test stub

- Extended protocol contract tests:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`
  - Added explicit `turn/submit` not-implemented test (`-32004`, method echo, `status=not_implemented`).

### 3) WL-106: add `session fork/rollback` top-level passthrough command stubs/tests

- Added top-level CLI passthrough stubs in modular app entrypoint:
  - `src/thegent/cli/apps/main.py`
  - New commands:
    - `thegent fork ...` -> passthrough to `thegent.cli.apps.run.run_fork`
    - `thegent rollback ...` -> passthrough to `thegent.cli.apps.run.run_rollback`
- Added focused test coverage:
  - `tests/test_wl106_top_level_passthrough.py`
  - Static contract checks ensure command decorators and passthrough call wiring are present.
  - `tests/test_wl106_session_cli_wiring.py` continues to validate run-stream wiring and SessionManager dispatch behavior.

### 4) WL-111: add MCP skills tool schema examples in docs with exact request/response

- Expanded docs with exact payload examples:
  - `docs/reference/MCP_SKILL_TOOL_SCHEMAS.md`
  - Added exact JSON examples for:
    - `tools/call` request for `thegent_list_skills` and success response.
    - `tools/call` request for `thegent_activate_skill` and both success + error responses.

### 5) WL-117: add extension README quickstart validation test (commands exist)

- Added quickstart contract test:
  - `tests/test_wl117_extension_readme_quickstart.py`
  - Verifies `extensions/vscode/README.md` quickstart includes `npm run <script>` commands and each referenced script exists in `extensions/vscode/package.json`.

## Focused Validation

- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py` (pass: 3 passed)
- `uv run python scripts/check_wl122_max_lines_canonical_path.py --strict` (pass)
- `uv run pytest -q tests/protocols/test_jsonrpc_agent_server_contract.py` (pass: 9 passed)
- `uv run pytest -q tests/test_wl106_session_cli_wiring.py tests/test_wl106_top_level_passthrough.py` (pass: 9 passed)
- `uv run pytest -q tests/test_wl117_extension_package_metadata.py tests/test_wl117_extension_readme_quickstart.py` (pass: 4 passed)
- `uv run pytest -q tests/protocols/test_jsonrpc_agent_server_contract.py tests/test_wl122_max_lines_ci_path.py tests/test_wl117_extension_package_metadata.py tests/test_wl117_extension_readme_quickstart.py` (pass: 16 passed)

## Notes

- `tests/commands/test_apps_main.py` currently fails collection in this branch due an existing unrelated import-time issue (`session_cmd` attribute mismatch in `src/thegent/cli/apps/main.py` outside this slice's scope). WL-106 validation was executed via targeted test files above.

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were kept scoped to requested WL items; unrelated workspace edits were left untouched.
