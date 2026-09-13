# WL-120 WaveX Test Hardening (cli/impl/mcp)

Date: 2026-02-21
Lane: WL-120 test-hardening
Scope: Narrow, deterministic extraction-regression tests for command routing/import surface.

## Files Updated

- `tests/commands/test_wl120_extraction_import_routing.py`
- `tests/mcp/test_wl120_mcp_server_extraction.py`

## What Was Strengthened

### 1) CLI routing surface regressions

In `tests/commands/test_wl120_extraction_import_routing.py`:

- Added WL-120 trace tag for the lane-specific test surface.
- Added assertions that `thegent.cli.commands.cli` re-exported command symbols originate from extracted domain modules:
  - `plan_cmds`
  - `run_cmds`
  - `session_cmds`
  - `model_cmds`
  - `governance_cmds`
- Added source-level guardrails that `cli.py` continues explicit domain wildcard re-exports.
- Added source-level guardrails that key `impl.py` wrappers remain thin delegates to extracted helper modules (`run_input_helpers`, `run_event_helpers`, `run_audio_helpers`, `run_model_helpers`).

### 2) MCP import/loading surface regressions

In `tests/mcp/test_wl120_mcp_server_extraction.py`:

- Kept dynamic-registry extraction import and callable checks.
- Added deterministic contract test for `server_tool_loader.load_tools_dynamic_registry(...)`:
  - verifies loader target filename/import-name/failure-message.
- Added source-level wiring checks in `mcp/server.py` for:
  - `_load_tools_dynamic_registry` binding
  - tuple assignment from `register_dynamic_registry_tools(...)`
  - expected exported tool names (`thegent_register_tool`, `thegent_complete_tool_call`, `thegent_list_dynamic_tools`)
- Added source-level guard that `mcp/server.py` keeps required `cli.commands.impl` import surface for workstream-routing commands.

## Validation Run

Command:

- `uv run pytest -q tests/commands/test_wl120_extraction_import_routing.py tests/mcp/test_wl120_mcp_server_extraction.py`

Result:

- `16 passed, 6 warnings in 91.98s`

Warnings:

- Pydantic JSON schema warnings from FastMCP `Depends` default serialization during server import path; no test failures.

## Notes

- No attempt was made to clean or alter unrelated dirty worktree files.
- Changes are intentionally test-only and focused on extraction regression boundaries for `cli/impl/mcp`.
