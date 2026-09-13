# tool_artifacts API Reference

> **Source**: `src/thegent/artifacts/tool_artifacts.py`

Tool-Related Artifacts - External tool invocations and API calls.

Provides specialized artifacts for:

- MCP (Model Context Protocol) tool calls
- External API invocations
- Command-line tool execution

---

## MCPCallArtifact

Artifact for MCP (Model Context Protocol) tool calls.

Specialized tracking for MCP interactions with:

- Server and tool information
- Request/response schemas
- Error handling

**Inherits from**: `BaseArtifact`

### Methods

#### MCPCallArtifact.create

```python
create(cls: Any, maif: MAIFArtifact, mcp_server: str, mcp_tool: str, call_status: ToolResultStatus)
```

Create MCP call artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `mcp_server`: MCP server name
- `mcp_tool`: MCP tool name
- `call_status`: Call status
- `**kwargs`: Additional fields

**Returns**: MCPCallArtifact instance

---

---

## ToolInvocationArtifact

Artifact for external tool invocations.

Tracks:

- Tool name, type, and version
- Input arguments and parameters
- Output/result
- Execution status and metrics

**Inherits from**: `BaseArtifact`

### Methods

#### ToolInvocationArtifact.create

```python
create(cls: Any, maif: MAIFArtifact, tool_type: ToolType, tool_name: str, arguments: dict[(str, Any)], result_status: ToolResultStatus)
```

Create tool invocation artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `tool_type`: Type of tool
- `tool_name`: Name of tool
- `arguments`: Tool arguments
- `result_status`: Execution status
- `**kwargs`: Additional fields

**Returns**: ToolInvocationArtifact instance

---

---

## ToolResultStatus

Status of tool execution.

**Inherits from**: `str, Enum`

---

## ToolType

Types of external tools.

**Inherits from**: `str, Enum`

---

## create

```python
create(cls: Any, maif: MAIFArtifact, mcp_server: str, mcp_tool: str, call_status: ToolResultStatus)
```

Create MCP call artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `mcp_server`: MCP server name
- `mcp_tool`: MCP tool name
- `call_status`: Call status
- `**kwargs`: Additional fields

**Returns**: MCPCallArtifact instance

---
