# shared_server_integration API Reference

> **Source**: `src/thegent/shared_server_integration.py`

Shared Server Integration - Session Management

Integrates shared LSP/MCP servers into thegent session lifecycle.

---

## cleanup_shared_servers_for_session

```python
cleanup_shared_servers_for_session(project_root: Any)
```

Cleanup shared servers when session ends.

Note: Servers are shared, so we don't stop them here.
Only cleanup session-specific resources.

---

## get_session_server_info

```python
get_session_server_info(project_root: Any)
```

Get current server information for a session.

Useful for debugging and monitoring.

---

## initialize_shared_servers_for_session

```python
initialize_shared_servers_for_session(project_root: Any, languages: Any)
```

Initialize shared servers for a new session.

Called when a thegent session starts.

**Returns**: {
'mcp_url': str,
'lsp_servers': {language: socket_path},
'scope': 'system' | 'project'
}

---
