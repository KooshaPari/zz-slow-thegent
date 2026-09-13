# WL-120 Extraction Wave X (MCP server)

## Scope

- Target: `src/thegent/mcp/server.py`
- Wave goal: extract another boilerplate loader/wiring chunk while preserving public wrappers.

## What Was Extracted

- Extracted provider/model MCP tool wiring block from `src/thegent/mcp/server.py` into:
  - `src/thegent/mcp/server/tools_provider_models.py`
- Added loader wiring:
  - `src/thegent/mcp/server_tool_loader.py` now exports `load_tools_provider_models(...)`
- Preserved wrapper names in `server.py` by binding registration tuple back to the same exported symbols:
  - `list_providers`, `get_provider`, `add_provider`, `update_provider`, `delete_provider`, `list_credentials`, `add_api_key`, `remove_api_key`, `validate_provider`, `discover_models`, `list_models`, `add_model_alias`, `remove_model_alias`.

## Tests Added

- `tests/mcp/test_wl120_provider_model_tools_extraction.py`
  - Verifies extracted module imports and exposes `register_provider_model_tools`.
  - Verifies registration returns 13 tools and registers expected wrapper names.
  - Verifies `thegent.mcp.server` still exposes all provider/model wrapper names.

## LOC Delta

- `src/thegent/mcp/server.py`: `3461 -> 3307` (**-154**)
- `src/thegent/mcp/server/tools_provider_models.py`: **+197** (new)
- `src/thegent/mcp/server_tool_loader.py`: **+10**
- `tests/mcp/test_wl120_provider_model_tools_extraction.py`: **+103** (new)
- Net across touched files in this wave: **+156** lines

## Validation

- Syntax check:
  - `python -m py_compile src/thegent/mcp/server.py src/thegent/mcp/server_tool_loader.py src/thegent/mcp/server/tools_provider_models.py tests/mcp/test_wl120_provider_model_tools_extraction.py`
  - Result: pass
- Targeted tests:
  - `uv run pytest -q tests/mcp/test_wl120_provider_model_tools_extraction.py tests/mcp/test_wl120_mcp_server_extraction.py`
  - Result: `11 passed` (warnings only)

## Notes

- System `pytest` in this environment is missing `pytest_asyncio`; used `uv run pytest` for project-managed test deps.
