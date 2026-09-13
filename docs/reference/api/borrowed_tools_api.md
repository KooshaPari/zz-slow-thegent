# borrowed_tools API Reference

> **Source**: `src/thegent/mcp/borrowed_tools.py`

Port thegent MCP tools to other projects.

---

## BorrowedMCPTools

MCP tools borrowed from thegent for other projects.

### Methods

#### BorrowedMCPTools.**init**

```python
__init__(self: Any)
```

Initialize borrowed MCP tools.

---

#### BorrowedMCPTools.get_tool

```python
get_tool(self: Any, name: str)
```

Get a borrowed tool.

**Parameters**:

- `name`: Tool name

**Returns**: Tool implementation

---

#### BorrowedMCPTools.list_tools

```python
list_tools(self: Any)
```

List all borrowed tools.

**Returns**: List of tool names

---

#### BorrowedMCPTools.register_tool

```python
register_tool(self: Any, name: str, tool: Any)
```

Register a borrowed tool.

**Parameters**:

- `name`: Tool name
- `tool`: Tool implementation

---

---

## get_tool

```python
get_tool(self: Any, name: str)
```

Get a borrowed tool.

**Parameters**:

- `name`: Tool name

**Returns**: Tool implementation

---

## list_tools

```python
list_tools(self: Any)
```

List all borrowed tools.

**Returns**: List of tool names

---

## register_tool

```python
register_tool(self: Any, name: str, tool: Any)
```

Register a borrowed tool.

**Parameters**:

- `name`: Tool name
- `tool`: Tool implementation

---
