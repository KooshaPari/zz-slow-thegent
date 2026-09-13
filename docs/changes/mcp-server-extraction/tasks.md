---
title: MCP Server Tool Extraction — Remaining Tasks
date: 2026-02-21
status: in-progress
owner: agent-f (B90-W2-F1)
tags: [wl-126, b90, monolith-split, mcp]
---

# Remaining Tasks: MCP Server Split

## Completed

- [x] All 13+ tool group files exist under `src/thegent/mcp/server/`
- [x] `server.py` loads each group via `_load_server_tools_<group>_module()` pattern
- [x] Helper modules extracted: `server_dispatch_helpers.py`,
      `server_policy_quality_helpers.py`, `server_runtime_helpers.py`,
      `server_meta_helpers.py`, `server_result_helpers.py`,
      `server_elicitation_cache_helpers.py`, `server_elicitation_response_helpers.py`,
      `server_module_loader.py`
- [x] **W3-C3 (slice, 2026-02-21)** Collapsed remaining manual loader boilerplate in
      `server.py` to shared `server_load_module` wrappers while preserving
      `_load_server_tools_<group>_module()` call surface (`server.py` line-count
      baseline: `3867 -> 3845` in `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.json`)

## Remaining Extractions (Future Waves)

### Wave-3: server.py lifespan and registration further reduction

| ID    | Target                                                           | Estimated LOC | Depends on     | Status               |
| ----- | ---------------------------------------------------------------- | ------------- | -------------- | -------------------- |
| W3-C1 | Extract auth/lifecycle loading into `server_bootstrap.py`        | ~200          | pattern stable | DONE (28 LOC final)  |
| W3-C2 | Extract resource group loading into `server_resources.py`        | ~150          | pattern stable | DONE (78 LOC final)  |
| W3-C3 | Extract tool group loading into `server_tool_loader.py`          | ~300          | pattern stable | DONE (218 LOC final) |
| W3-C4 | Extract middleware setup into `server_middleware.py`             | ~100          | pattern stable | DONE (57 LOC final)  |
| W3-C5 | `server.py` reduced to lifespan + import delegation (~200 lines) | 952 final     | W3-C1..C4      | DONE                 |

### Wave-4: Tool group unit tests

| ID    | Target                                     | Notes                            |
| ----- | ------------------------------------------ | -------------------------------- |
| W4-C1 | `tests/mcp/tools/test_tools_governance.py` | Currently no isolated tool tests |
| W4-C2 | `tests/mcp/tools/test_tools_planning.py`   |                                  |
| W4-C3 | `tests/mcp/tools/test_tools_sessions.py`   |                                  |
| W4-C4 | `tests/mcp/tools/test_tools_research.py`   |                                  |

## Cut-over Gate (per extraction)

Before removing a loader stub from `server.py`:

1. Tool group module imports cleanly: `python -c "import thegent.mcp.server.<group>"`
2. FastMCP tool registration call succeeds in isolated test
3. MCP integration tests still pass: `pytest tests/mcp/ -q`
4. `python -c "from thegent.mcp.server import app"` still exits 0 in < 2s
5. No new ruff errors in the extracted module

## Target Ceiling

- `server.py`: reduce from 3,939 to < 500 lines by end of Wave-5
- Each tool group module: < 500 lines (enforced by `contracts/max_lines.json`)
