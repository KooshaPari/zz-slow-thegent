# Wave-9 Agent-D Execution Report

## Scope Delivered

### 1) WL-122 + WL-117: Canonical CI contract reinforcement

- Tightened canonical checker behavior in:
  - `scripts/check_wl122_max_lines_canonical_path.py`
- Added two new fail-closed requirements:
  - CI must include strict WL-117 metadata check (`check_extension_package_metadata.py --strict`)
  - WL-117 metadata check must run before WL-122 max-lines gate (`task quality:max-lines`)

### 2) WL-122 tests: expanded contract coverage

- Extended:
  - `tests/test_wl122_max_lines_ci_path.py`
- Added coverage for:
  - Missing WL-117 strict metadata checker (must fail)
  - WL-117 checker ordered after max-lines gate (must fail)
  - Updated canonical passing fixtures to include WL-117 strict checker

### 3) WL-104 contract reinforcement

- Extended:
  - `tests/protocols/test_jsonrpc_agent_server_contract.py`
- Added assertion that `config/read` returns canonical method inventory exactly as `sorted(SUPPORTED_METHODS)`.

### 4) WL-106 contract reinforcement

- Extended:
  - `tests/test_wl106_session_cli_wiring.py`
- Added explicit passthrough assertion that `from_turn=None` is forwarded unchanged to SessionManager API calls.

### 5) WL-111 contract reinforcement

- Extended:
  - `tests/mcp/test_tools_skills_contract.py`
- Added assertion that missing-skill error payload reports normalized `skill_name` (trimmed input).

### 6) Docs reinforcement

- Updated QA runbook with canonical focused lane:
  - `docs/guides/QUALITY_ASSURANCE.md`
- Added a compact command bundle for WL-104/106/111/117/122 contract checks and strict checker ordering notes.

## Focused Validation

- `uv run python scripts/check_wl122_max_lines_canonical_path.py --strict`
  - Pass: `ok: True`, `canonical invocations: 1`
- `uv run pytest -q tests/test_wl122_max_lines_ci_path.py tests/protocols/test_jsonrpc_agent_server_contract.py tests/test_wl106_session_cli_wiring.py tests/mcp/test_tools_skills_contract.py tests/test_wl117_extension_package_metadata.py`
  - Pass: `35 passed in 52.42s`

## Guardrails

- `docs/reference/WORK_STREAM.md` was not modified.
- Edits were scoped to WL-122, WL-104, WL-106, WL-111, WL-117 contract surfaces plus QA docs.
- Unrelated dirty workspace changes were left untouched.
