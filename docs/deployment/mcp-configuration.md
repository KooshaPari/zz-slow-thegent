# System-Scoped MCP Setup: atoms-mcp-prod

## Overview

`atoms-mcp-prod` is now automatically composed as a **system-scoped MCP server**, making it:

- ✅ **Observable**: Visible in frontend management pages
- ✅ **Configurable**: Can be enabled/disabled, configured via UI
- ✅ **Available to all users**: System-scoped servers are accessible to everyone
- ✅ **Automatically included**: No manual installation needed

## Implementation Details

### 1. Database Registration

`atoms-mcp-prod` must be registered in the `mcp_servers` table with:

- `scope = 'system'` - Makes it system-scoped
- `is_internal = true` - Marks it as Atoms platform server
- `enabled = true` - Active by default

### 2. Automatic Composition

The `compose_mcp_servers()` function now:

1. **First** loads system-scoped servers (including atoms-mcp-prod)
2. Then loads user/org/project-specific servers
3. Finally adds local sandbox tools

This ensures atoms-mcp-prod is always available.

### 3. Authentication

System-scoped servers use the user's AuthKit JWT token automatically:

- Token is extracted from the request context
- Passed to atoms-mcp-prod via `Authorization: Bearer <token>` header
- No manual token management needed

## Migration Steps

### Step 1: Run Database Migration

Execute the SQL migration to register atoms-mcp-prod:

```bash
# Option 1: Using psql
psql -d your_database -f agentapi/atomsagent/migrations/register_atoms_mcp_prod.sql

# Option 2: Using Supabase SQL Editor
# Copy and paste the SQL from register_atoms_mcp_prod.sql
```

### Step 2: Verify Registration

Check that atoms-mcp-prod is registered:

```sql
SELECT
    id,
    namespace,
    name,
    scope,
    is_internal,
    enabled,
    url
FROM mcp_servers
WHERE namespace = 'atoms-mcp';
```

Expected result:

- `scope` = `'system'`
- `is_internal` = `true`
- `enabled` = `true`
- `url` = Your atoms-mcp-prod deployment URL

### Step 3: Update Environment Variables

Ensure `ATOMS_MCP_PROD_URL` is set (optional, defaults to production):

```bash
# Production
export ATOMS_MCP_PROD_URL=https://mcp.atoms.tech/api/mcp

# Development
export ATOMS_MCP_PROD_URL=https://mcpdev.atoms.tech/api/mcp

# Local
export ATOMS_MCP_PROD_URL=http://localhost:8000/api/mcp
```

### Step 4: Test Integration

Verify that atoms-mcp-prod is automatically composed:

```python
from atomsAgent.mcp.integration import compose_mcp_servers

# Compose servers (atoms-mcp-prod should be included automatically)
servers = await compose_mcp_servers(user_id="user-123", user_token="jwt-token-here")

# Check that atoms-mcp-prod is included
assert "atoms-mcp" in servers
print(f"Composed {len(servers)} servers: {list(servers.keys())}")
```

## Frontend Management

### Observable Properties

The frontend can display:

- **Server Name**: `atoms-mcp`
- **Description**: Official Atoms Platform MCP Server
- **Status**: Active/Inactive
- **Scope**: System
- **Tools**: List of 5 tools
- **URL**: Deployment URL
- **Authentication**: Bearer token (AuthKit)

### Configurable Properties

Users/admins can configure:

- **Enable/Disable**: Toggle server availability
- **URL**: Override deployment URL (for testing)
- **Tool Permissions**: Restrict specific tools (if needed)
- **Custom Config**: Additional configuration

### UI Integration

The frontend management pages should:

1. **List system-scoped servers** separately from user/org servers
2. **Show atoms-mcp-prod** with special badge (Platform/System)
3. **Allow configuration** but prevent deletion (system servers)
4. **Display tool list** from metadata
5. **Show usage stats** if available

## Code Changes Summary

### New Functions

1. **`get_system_mcp_servers()`** in `mcp/database.py`
   - Fetches all system-scoped MCP servers
   - Filters by `scope='system'` OR `is_internal=true`

2. **Updated `compose_mcp_servers()`** in `mcp/integration.py`
   - Automatically includes system-scoped servers first
   - Includes local sandbox tools at the end

### Database Schema

System-scoped servers use:

- `scope = 'system'` - System-wide availability
- `is_internal = true` - Platform-managed server
- `enabled = true` - Active by default

## Troubleshooting

### atoms-mcp-prod Not Appearing

1. **Check database registration**:

   ```sql
   SELECT * FROM mcp_servers WHERE namespace = 'atoms-mcp';
   ```

2. **Verify scope and is_internal**:

   ```sql
   SELECT scope, is_internal, enabled FROM mcp_servers WHERE namespace = 'atoms-mcp';
   ```

   Should be: `scope='system'`, `is_internal=true`, `enabled=true`

3. **Check logs**:
   ```python
   # Look for: "Composing system-scoped MCP servers"
   # And: "Added system server: atoms-mcp"
   ```

### Authentication Issues

1. **Verify user_token is passed**:

   ```python
   servers = await compose_mcp_servers(user_token="jwt-token")
   ```

2. **Check convert_db_server_to_mcp_config**:
   - Should detect `is_internal=true`
   - Should add `Authorization: Bearer <token>` header

### URL Configuration

If atoms-mcp-prod URL is wrong:

1. Update in database:

   ```sql
   UPDATE mcp_servers
   SET url = 'https://your-url/api/mcp'
   WHERE namespace = 'atoms-mcp';
   ```

2. Or set environment variable:
   ```bash
   export ATOMS_MCP_PROD_URL=https://your-url/api/mcp
   ```

## Benefits

✅ **Single Source of Truth**: atoms-mcp-prod is the official platform server
✅ **Automatic Inclusion**: No manual installation needed
✅ **Observable**: Visible in management UI
✅ **Configurable**: Can be managed via frontend
✅ **System-Wide**: Available to all users automatically
✅ **No Duplication**: Removed duplicate tools from agentapi/atomsagent
