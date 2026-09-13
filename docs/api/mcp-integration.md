# MCP Merge Summary

## Completed Actions

### ✅ 1. Added Unique Tools to atoms-mcp-prod

**Note:** `search_codebase` was initially added but later removed since Claude Agent SDK implements codebase search natively.

### ✅ 2. Removed Duplicate Tools from agentapi/atomsagent

**Removed duplicate tools:**

- ❌ `search_requirements` - Now use `entity_operation(operation='search', entity_type='requirement')` from atoms-mcp-prod
- ❌ `create_requirement` - Now use `entity_operation(operation='create', entity_type='requirement')` from atoms-mcp-prod
- ❌ `analyze_document` - Now use `data_query(query_type='rag_search', entities=['document'])` from atoms-mcp-prod
- ⚠️ `search_codebase` - Removed (Claude Agent SDK provides this natively)

**Kept unique tools:**

- ✅ `execute_in_sandbox` - Vercel Sandbox execution (unique)
- ✅ `get_execution_metrics` - Sandbox metrics (unique)
- ✅ `get_execution_trace` - Distributed tracing (unique)
- ✅ `stream_sandbox_execution` - Streaming execution (unique)

### ✅ 3. Updated agentapi/atomsagent MCP Server

- Renamed server from "atoms-tools" to "atoms-sandbox-tools" to reflect its purpose
- Updated documentation to indicate it's being phased out
- Removed registrations for duplicate tools

## Remaining Tasks

### ⏳ 4. Update agentapi/atomsagent to Compose atoms-mcp-prod

**Action Required:**
Update `agentapi/atomsagent/src/atomsAgent/mcp/integration.py` to automatically include atoms-mcp-prod:

```python
async def compose_mcp_servers(...):
    servers = {}

    # Always include atoms-mcp-prod (official server with all platform tools)
    atoms_mcp_url = os.getenv("ATOMS_MCP_PROD_URL", "https://mcp.atoms.tech/api/mcp")
    servers["atoms-mcp"] = {
        "url": atoms_mcp_url,
        "auth": "bearer",
        "token": user_token,  # AuthKit JWT
    }

    # Include local sandbox tools (unique to agentapi)
    servers.update(get_atoms_sandbox_tools_config())

    # ... rest of composition logic
```

### ⏳ 5. Sandbox Tools Consideration

**Decision Needed:**
The sandbox tools (`execute_in_sandbox`, etc.) depend on:

- `claude-agent-sdk>=0.1.5,<0.2.0`
- `SandboxAgent` service
- `monitoring_service` and `tracing_service`

**Options:**

1. **Keep in agentapi/atomsagent** (current approach) - Sandbox tools stay in agentapi since they're tightly coupled to its infrastructure
2. **Move to atoms-mcp-prod** - Would require adding claude-agent-sdk dependency and porting services

**Recommendation:** Keep sandbox tools in agentapi/atomsagent since they're specific to the agent orchestration service, not the core Atoms platform.

## Migration Guide

### For Users of agentapi/atomsagent MCP Tools

**Before:**

```python
# Old way (duplicate tools)
search_requirements(query="...")
create_requirement(project_id="...", title="...")
analyze_document(document_id="...")
search_codebase(query="...")
```

**After:**

```python
# New way (use atoms-mcp-prod)
# Requirements operations
entity_operation(operation="search", entity_type="requirement", filters={"title": {"ilike": "%...%"}})
entity_operation(operation="create", entity_type="requirement", properties={"project_id": "...", "title": "..."})

# Document analysis
data_query(query_type="rag_search", entities=["document"], query="...", document_id="...")

# Codebase search
codebase_search_tool(query="...", file_pattern="*.py")
```

### For agentapi/atomsagent Integration

**Update `compose_mcp_servers()` to include atoms-mcp-prod:**

```python
# In atomsAgent/mcp/integration.py
async def compose_mcp_servers(...):
    servers = {}

    # 1. Add atoms-mcp-prod (official server)
    servers["atoms-mcp"] = {
        "url": os.getenv("ATOMS_MCP_PROD_URL", "https://mcp.atoms.tech/api/mcp"),
        "auth": "bearer",
        "token": user_token,
    }

    # 2. Add local sandbox tools
    servers.update(get_atoms_sandbox_tools_config())

    # 3. Add user/org/project servers
    # ... existing logic

    return servers
```

## Benefits

✅ **Single Source of Truth**: All platform operations (requirements, documents, entities) come from atoms-mcp-prod
✅ **No Code Duplication**: Removed ~200 lines of duplicate code
✅ **Better Features**: atoms-mcp-prod has more comprehensive features (permissions, relationships, workflows)
✅ **Easier Maintenance**: One place to update platform functionality
✅ **Clear Separation**: agentapi/atomsagent focuses on orchestration, atoms-mcp-prod on platform operations

## Next Steps

1. ✅ Complete tool removal from agentapi/atomsagent
2. ⏳ Update `compose_mcp_servers()` to include atoms-mcp-prod
3. ⏳ Update any tests that reference removed tools
4. ⏳ Update documentation
5. ⏳ Test integration end-to-end
