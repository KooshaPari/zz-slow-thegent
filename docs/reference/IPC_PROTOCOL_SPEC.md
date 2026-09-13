# IPC Protocol Specification

**Version:** 1.0
**Date:** 2026-02-22
**Status:** Active

## Overview

Sub-projects communicate via:

1. **MCP Protocol** (Machine Context Protocol) -- standardized tool/resource interface
2. **Session State** -- shared JSONL/SQLite for agent lifecycle
3. **File-based IPC** -- JSONL logs for async communication

## MCP Endpoints

### thegent-agents MCP

- **Port:** 3847 (default)
- **Protocol:** stdio (for CLI), HTTP/SSE (for remote)
- **Tools:** run_agent, list_agents, get_agent_state, stop_agent, query_memory, add_memory

### thegent-mcp MCP

- **Port:** 3848 (default)
- **Tools:** 500+ from zen-mcp-server + new integrations
- **Categories:** github, slack, stripe, openai, anthropic, jira, confluence, salesforce

## Error Contract

All MCP errors follow standard format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "context": {}
  }
}
```

## Error Codes

| Code                  | Meaning                      | HTTP |
| --------------------- | ---------------------------- | ---- |
| AGENT_NOT_FOUND       | Agent persona does not exist | 404  |
| TOOL_NOT_FOUND        | Unknown tool                 | 404  |
| INVALID_ARGS          | Bad arguments                | 400  |
| AUTHENTICATION_FAILED | Auth required/failed         | 401  |
| RESOURCE_EXHAUSTED    | Token/rate limit             | 429  |
| TIMEOUT               | Operation timeout            | 504  |
| INTERNAL_ERROR        | Server error                 | 500  |

## Session State

- `~/.thegent/sessions/run_registry.jsonl` -- all runs
- `~/.thegent/sessions/escalation_queue.jsonl` -- pending escalations
- `~/.thegent/sessions/workstream.db` -- SQLite: completed tasks, metrics
