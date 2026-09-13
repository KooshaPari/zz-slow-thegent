# acp_mcp_bridge API Reference

> **Source**: `src/thegent/adapters/acp_mcp_bridge.py`

ACP &lt;-&gt; MCP Bridge Adapter.

Bridges MCP tools to ACP task endpoints and vice versa:

- `mcp_tool_to_acp_task`: Wrap an MCP tool call as an ACP task sent to a
  remote ACP server.
- `acp_agent_to_mcp_tool`: Call a remote ACP agent and return its output in
  MCP tool response format (plain string).
- `get_mcp_tool_manifest`: Introspect all registered FastMCP tools and return
  them as ACP-compatible task descriptors.

The bridge is deliberately stateless. Callers are responsible for providing an

---

## ACPAgentCallError

Raised when calling an ACP agent fails non-transiently.

**Inherits from**: `BridgeError`

**Method Resolution Order**: `ACPAgentCallError -> BridgeError`

### Methods

#### ACPAgentCallError.**init**

```python
__init__(self: Any, agent_url: str, detail: str)
```

---

---

## ACPToolDescriptor

ACP-compatible descriptor for a single MCP tool.

### Methods

#### ACPToolDescriptor.to_dict

```python
to_dict(self: Any)
```

Serialise to a plain dict suitable for JSON transport.

---

---

## AcpMcpBridge

Bridges MCP tools to ACP task endpoints and vice versa.

### Methods

#### AcpMcpBridge.**init**

```python
__init__(self: Any, acp_client: ACPClient, mcp_app: Any, mcp_server_url: Any)
```

---

#### AcpMcpBridge.get_mcp_tool_manifest

```python
get_mcp_tool_manifest(self: Any)
```

Return all registered MCP tools as ACP-compatible task descriptors.

Introspects the FastMCP application (if provided at construction time)
and converts each registered tool into an :class:`ACPToolDescriptor`,
serialised as a plain dict.

When no FastMCP application is available the method returns an empty
list rather than raising, so callers can safely call it unconditionally.

**Returns**: List of dicts, each with keys `name`, `description`,
`parameters`, and `version`.

---

---

## BridgeError

Base class for bridge-specific errors.

**Inherits from**: `Exception`

---

## MCPToolNotFoundError

Raised when a requested MCP tool is not registered.

**Inherits from**: `BridgeError`

**Method Resolution Order**: `MCPToolNotFoundError -> BridgeError`

### Methods

#### MCPToolNotFoundError.**init**

```python
__init__(self: Any, tool_name: str)
```

---

---

## get_mcp_tool_manifest

```python
get_mcp_tool_manifest(self: Any)
```

Return all registered MCP tools as ACP-compatible task descriptors.

Introspects the FastMCP application (if provided at construction time)
and converts each registered tool into an :class:`ACPToolDescriptor`,
serialised as a plain dict.

When no FastMCP application is available the method returns an empty
list rather than raising, so callers can safely call it unconditionally.

**Returns**: List of dicts, each with keys `name`, `description`,
`parameters`, and `version`.

---

## to_dict

```python
to_dict(self: Any)
```

Serialise to a plain dict suitable for JSON transport.

---
