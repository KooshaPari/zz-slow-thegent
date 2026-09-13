# Wave-5 Agent-D Execution Report

## Scope Delivered

### 1) WL-122: CI/check script asserting canonical max-lines task path only

- Added canonical-path CI checker:
  - `scripts/check_wl122_max_lines_canonical_path.py`
  - Enforces:
    - `Taskfile.yml` defines `quality:max-lines` with `sh scripts/max-lines-gate.sh`.
    - `.github/workflows/ci.yml` invokes `task quality:max-lines`.
    - `.github/workflows/ci.yml` does not invoke `scripts/max-lines-gate.sh` directly.
- Added focused unit tests:
  - `tests/test_wl122_max_lines_ci_path.py`
- Wired checker and canonical task execution in CI quality lane:
  - `.github/workflows/ci.yml`

### 2) WL-104: JSON-RPC method contract stub `session/read` + tests

- Extended contract tests to lock in `session/read` behavior:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`
  - Asserts `config/read` reports `session/read` under `not_implemented_methods`.
  - Adds explicit `session/read` not-implemented response test (`-32004`, method echo).

### 3) WL-106: session fork/rollback CLI help docs + argument validation tests

- Tightened CLI argument validation for fork:
  - `src/thegent/cli/apps/run.py`
  - `--from-turn` now enforces `min=1` and help text is explicitly 1-based.
- Added argument validation tests:
  - `tests/test_wl106_session_cli_wiring.py`
  - Verifies CLI rejects `--from-turn 0` and `--n-turns 0` with exit code `2` and without dispatching command handlers.
- Added CLI reference docs for fork/rollback usage:
  - `docs/site/guide/cli-reference.md`

### 4) WL-111: MCP tools list/assertion test for skills tool registration

- Added explicit registry assertion coverage:
  - `tests/mcp/test_tools_skills_registry_smoke.py`
  - Adds a list/assertion test that skills-related registered tools include both:
    - `thegent_list_skills`
    - `thegent_activate_skill`

### 5) WL-117: extension package metadata sanity check script/test

- Added extension metadata checker:
  - `scripts/check_extension_package_metadata.py`
  - Validates required extension package contract (`name`, `displayName`, `description`, semver `version`, `engines.vscode`, `main`, `activationEvents`, `contributes.commands`, and command activation parity).
- Added focused tests:
  - `tests/test_wl117_extension_package_metadata.py`
- Wired metadata checker in CI quality lane:
  - `.github/workflows/ci.yml`

## Focused Validation

- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py tests/test_wl117_extension_package_metadata.py tests/protocols/test_jsonrpc_agent_server_contract.py tests/test_wl106_session_cli_wiring.py tests/mcp/test_tools_skills_registry_smoke.py` (pass: 24 passed)
- `uv run python scripts/check_wl122_max_lines_canonical_path.py --strict` (pass)
- `uv run python scripts/check_extension_package_metadata.py --strict` (pass)
- `uv run python -m py_compile scripts/check_wl122_max_lines_canonical_path.py scripts/check_extension_package_metadata.py src/thegent/cli/apps/run.py src/thegent/protocols/jsonrpc_agent_server.py` (pass)

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Changes were kept scoped to requested WL items; unrelated workspace edits were left untouched.
