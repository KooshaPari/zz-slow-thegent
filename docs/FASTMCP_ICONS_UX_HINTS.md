# FastMCP Icons and UX Hints (G-FM-04)

**Purpose:** Icon and UX hint mapping for MCP tools; wire when FastMCP supports.
**Date:** 2026-02-14
**Source:** THGENT_FASTMCP_IMPLEMENTATION_PLAN §14.8

---

## 1. Tool Icon Mapping

| Tool                | Icon | Hint       | Purpose                                |
| ------------------- | ---- | ---------- | -------------------------------------- |
| thegent_run         | ▶   | play       | Execution; run agent synchronously     |
| thegent_bg          | ⏸   | background | Fire-and-forget; start background task |
| thegent_stop        | ⏹   | stop       | Destructive; confirm in UI before use  |
| thegent_logs        | ▤    | logs       | Read-only; session log output          |
| thegent_ps          | ≡    | list       | Discovery; list background sessions    |
| thegent_status      | ℹ   | status     | Session status                         |
| thegent_wait        | ⏳   | wait       | Block until session completes          |
| thegent_inspect     | ⌕    | inspect    | Multi-session status + logs            |
| thegent_list_agents | ⊕    | agents     | List available agents                  |
| thegent_list_droids | ◉    | droids     | List droids                            |
| thegent_list_models | ⊞    | models     | Model catalog                          |
| thegent_dag_list    | ▣    | dag        | DAG task list                          |

---

## 2. Implementation Status

- **Annotations:** ✓ `readOnlyHint`, `destructiveHint`, `idempotentHint` already on all tools.
- **Icons:** □ Pending FastMCP API — use `icons=[...]` or `ToolTransform` when available.
- **Code:** `TOOL_ICONS` dict in `mcp_server.py` — ready to wire.

---

## 3. Wiring (When API Available)

```python
# In mcp_server.py, when FastMCP supports icon parameter:
TOOL_ICONS = {
    "thegent_run": "▶",
    "thegent_bg": "⏸",
    "thegent_stop": "⏹",
    "thegent_logs": "▤",
    "thegent_ps": "≡",
    "thegent_status": "ℹ",
    "thegent_wait": "⏳",
    "thegent_inspect": "⌕",
    "thegent_list_agents": "⊕",
    "thegent_list_droids": "◉",
    "thegent_list_models": "⊞",
    "thegent_dag_list": "▣",
}

# Example: mcp.tool(icon=TOOL_ICONS.get("thegent_run"), ...)
# Or: mcp.add_transform(ToolTransform({"thegent_run": {"icon": "▶"}}))
```

---

## 4. References

- `docs/plans/THGENT_FASTMCP_IMPLEMENTATION_PLAN.md` §14.8
- `src/thegent/mcp_server.py` — tool definitions with annotations
