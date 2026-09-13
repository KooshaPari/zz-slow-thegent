<DONE>
# Shared LSP/MCP Optimization - System-Wide First Update

**Date:** 2026-02-18  
**Status:** ✅ Plan Updated

## Key Changes

Updated `SHARED_LSP_MCP_OPTIMIZATION_PLAN.md` to prioritize **system-wide sharing by default**.

### Architecture Change

**Before:** Per-project shared servers (default)  
**After:** System-wide shared servers (default), scope down only when needed

### New Architecture

```
System-Wide (All Projects) - DEFAULT
  ├─ Shared LSP Server (1-2GB) ← All sessions from all projects
  ├─ Shared MCP Server (100-500MB) ← All sessions from all projects
  │
  ├─ Project A Sessions → Connect to system-wide servers
  ├─ Project B Sessions → Connect to system-wide servers
  └─ Project C Sessions → Connect to system-wide servers

Total: ~2-2.5GB (shared) + N × (10-50MB per session)
```

**Scoping Down (Per-Project) - Only When Needed:**

- Different LSP/MCP configurations
- Project isolation required (security/compliance)
- Different language versions (Python 3.11 vs 3.12)
- Project-specific MCP servers required

### Implementation Updates

1. **Default Scope:** System-wide (`~/.cache/thegent/mcp/system.lock`)
2. **Scoping Logic:** Check for `.thegent/isolate_servers` file to force project isolation
3. **Code Examples:** Updated to show system-wide first approach
4. **Configuration:** `THGENT_SHARED_SCOPE=system` (default)

### Benefits

- **Maximum efficiency:** One server for all projects
- **Simpler management:** Single server lifecycle
- **Better resource usage:** Optimal memory utilization
- **Flexible:** Can still scope down when needed

### Project Isolation Override

To force project isolation, create:

```bash
# .thegent/isolate_servers
# This file forces project-scoped servers for this project
```

### Updated Files

- ✅ `docs/research/SHARED_LSP_MCP_OPTIMIZATION_PLAN.md` - Updated with system-wide first approach
- ✅ Code examples updated to reflect system-wide default
- ✅ Configuration options updated

## Next Steps

1. ✅ **Updated:** Plan reflects system-wide first approach
2. ⏭️ **Implement:** System-wide shared MCP server manager
3. ⏭️ **Implement:** System-wide shared LSP server manager
4. ⏭️ **Add:** Project isolation override mechanism
5. ⏭️ **Test:** Verify system-wide sharing works across projects
