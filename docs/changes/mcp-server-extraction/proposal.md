---
title: MCP Server Tool Extraction — Proposal
date: 2026-02-21
status: implemented
owner: agent-f (B90-W2-F1)
tags: [wl-126, b90, monolith-split, mcp]
---

# Proposal: Extract Tool Groups from mcp/server.py

## Problem Statement

`src/thegent/mcp/server.py` grew to 3,944 lines pre-wave-2 (3,939 post-wave-2), well
above the 500-line module ceiling. The file contained registration logic for 13+
independent tool groups (sessions, queue, terminal, escalation, governance, research,
planning, contract*observe, locking_planning, skills, coordination, runtime, batch4)
each with its own `\_load_server_tools*<group>\_module()` factory and registration
handler.

These tool groups are independent domains — sessions tooling has no logical dependency
on escalation tooling, for example. Keeping them in a single file causes:

1. **Review friction**: Any change to one tool group requires parsing 3.9k lines.
2. **Merge conflicts**: Parallel agents modifying different tool groups always conflict.
3. **Test isolation impossible**: Cannot import and test a single tool group without
   loading the entire server module.

## Why This Extraction

1. **Tool group isolation**: Each tool group is a coherent domain (sessions, queue,
   governance, research, planning, etc.). Extracting them to `mcp/server/<group>.py`
   enables independent development and testing.

2. **LOC reduction**: The `server/` subdirectory pattern already exists — 24 tool
   group modules live there (`tools_sessions.py`, `tools_governance.py`, etc.).
   The `server.py` monolith only needed to be updated to delegate to these existing
   modules via its `_load_server_tools_<group>_module()` pattern.

3. **Zero business logic duplication**: The extracted modules own the tool definitions;
   `server.py` acts as the router/registrar only.

## Decision

Keep `server.py` as the registrar/lifespan/middleware entry point. All tool group
implementations live in `src/thegent/mcp/server/<group>.py`. The `server.py`
module loads each group at startup via the `_load_server_tools_<group>_module()`
pattern (already in place post-extraction).

## Acceptance Criteria

- `server.py` < 4,000 lines (ceiling; target < 2,000 in wave-5).
- All 13+ tool group modules exist under `src/thegent/mcp/server/`.
- `python -c "from thegent.mcp.server import app"` exits 0 in < 2s.
- MCP test suite passes without modification.
