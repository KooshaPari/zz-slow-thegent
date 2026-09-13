# MCP Domain Technical Specification

## Overview

The MCP (Model Context Protocol) domain implements the MCP server for tool exposure and resource management.

## Components

### Server Architecture

```
MCP Request
    ↓
[Transport: stdio/HTTP/WebSocket]
    ↓
[JSON-RPC 2.0 Protocol]
    ↓
[Capability Router]
    ↓
[Tool Handler / Resource Handler / Prompt Handler]
```

### Tool Categories

| Category       | Count | Files                 |
| -------------- | ----- | --------------------- |
| Session tools  | 50+   | `tools_sessions.py`   |
| Terminal tools | 20+   | `tools_terminal.py`   |
| Governance     | 15+   | `tools_governance.py` |
| Planning       | 10+   | `tools_planning.py`   |
| Research       | 10+   | `tools_research.py`   |

## MCP Protocol Implementation

### Transport

| Transport | Status     | File                  |
| --------- | ---------- | --------------------- |
| stdio     | ✅ Default | `server_bootstrap.py` |
| HTTP      | ✅         | `server.py`           |
| WebSocket | P1         | Future                |

### Handlers

| Handler   | Purpose          | Path                  |
| --------- | ---------------- | --------------------- |
| Tools     | Tool execution   | `tools_*.py`          |
| Resources | Data access      | `resources_*.py`      |
| Prompts   | Prompt templates | `workflow_prompts.py` |
| Sampling  | LLM sampling     | `server_sampling.py`  |

## Tool Discovery

```python
# Dynamic tool loading
class ToolRegistry:
    def discover_tools(self) -> list[Tool]: ...
    def load_tools(self, module: str) -> list[Tool]: ...
    def validate_tool(self, tool: Tool) -> bool: ...
```

## Performance

| Metric          | Target             |
| --------------- | ------------------ |
| Tool discovery  | <50ms              |
| Tool execution  | Provider-dependent |
| Resource access | <10ms              |

## Security

| Mechanism     | Implementation       |
| ------------- | -------------------- |
| Auth          | OAuth 2.0 / API keys |
| Rate limiting | Per-client limits    |
| Sandboxing    | Process isolation    |

## Integration Points

| Integration     | Path             |
| --------------- | ---------------- |
| Agent execution | `agents/`        |
| Routing         | `routing/`       |
| Storage         | `mcp/storage.py` |
| Observability   | `observability/` |

## MCP Protocol Version

- **Spec**: v1.0 (Anthropic compatible)
- **JSON-RPC**: 2.0
- **Transport**: stdio, HTTP, WebSocket
