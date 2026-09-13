# borrow API Reference

> **Source**: `src/thegent/utils/borrow.py`

Tool borrowing: export thegent MCP tools for use in other projects.

Enables other projects to "borrow" thegent MCP tools without copying code.
Generates MCP server config and CLAUDE.md snippets pointing at a running
thegent MCP server instance.

# @trace FR-TOOLS-BORROW-001

---

## BorrowConfig

Connection configuration for a running thegent MCP server.

### Methods

#### BorrowConfig.url

```python
url(self: Any)
```

---

---

## ToolBorrower

Discovers and exports thegent MCP tools for cross-project use.

Other projects call this class to:

1. Enumerate available tools (`list_available_tools`).
2. Build an MCP server config fragment (`export_tool_config`).
3. Write an `mcp.json` file suitable for Claude Code (`generate_mcp_json`).
4. Generate a CLAUDE.md snippet instructing Claude to use the tools
   (`generate_claude_md_snippet`).

Example::

    borrower = ToolBorrower()
    borrower.generate_mcp_json(
        ["thegent_run", "thegent_ps", "thegent_ddg_search"],
        output_path=Path("my-other-project"),
    )

### Methods

#### ToolBorrower.**init**

```python
__init__(self: Any, config: Any)
```

---

#### ToolBorrower.export_tool_config

```python
export_tool_config(self: Any, tool_names: list[str])
```

Build an MCP server config dict for the requested tools.

The returned dict is the `mcpServers` entry for a Claude Code
`mcp.json` / `.claude.json` config. It points at the running
thegent HTTP+SSE MCP server; no tool filtering is applied at the
config level because the server exposes all tools and MCP clients
select the ones they need.

**Parameters**:

- `tool_names`: List of tool names to document in the config metadata.
  Pass an empty list to include all tools.

**Returns**: Dict with shape `{"thegent": {"type": "http", "url": ..., ...}}`.

---

#### ToolBorrower.generate_claude_md_snippet

```python
generate_claude_md_snippet(self: Any, tool_names: list[str])
```

Generate a CLAUDE.md section instructing Claude to use thegent tools.

**Parameters**:

- `tool_names`: Tools to document. Empty list includes all tools.

**Returns**: Markdown string ready to paste into a project's CLAUDE.md.

---

#### ToolBorrower.generate_mcp_json

```python
generate_mcp_json(self: Any, tool_names: list[str], output_path: Path)
```

Write (or update) an `mcp.json` file in `output_path`.

The file uses Claude Code's `mcpServers` format. When `merge=True`
and the file already exists, the `thegent` server entry is upserted
without touching existing entries.

**Parameters**:

- `tool_names`: Tools to document. Empty list borrows all tools.
- `output_path`: Directory where `mcp.json` will be written.
- `merge`: If True, merge with existing `mcp.json`; otherwise overwrite.

**Returns**: Absolute path to the written file.

---

#### ToolBorrower.get_tool

```python
get_tool(self: Any, name: str)
```

Return the manifest for a tool by name, or None if not found.

---

#### ToolBorrower.list_available_tools

```python
list_available_tools(self: Any)
```

Return all borrowable tool manifests, sorted by category then name.

---

#### ToolBorrower.list_available_tools_by_category

```python
list_available_tools_by_category(self: Any)
```

Return tools grouped by category.

---

#### ToolBorrower.validate_server_reachable

```python
validate_server_reachable(self: Any)
```

Check whether the configured thegent MCP server is reachable.

Performs a simple HTTP GET to the `/health` endpoint.

**Returns**: True if the server responds with status 200, False otherwise.

---

---

## ToolManifest

Manifest entry for a single borrowable thegent MCP tool.

### Methods

#### ToolManifest.to_dict

```python
to_dict(self: Any)
```

Serialize to plain dict for JSON output.

---

---

## export_tool_config

```python
export_tool_config(self: Any, tool_names: list[str])
```

Build an MCP server config dict for the requested tools.

The returned dict is the `mcpServers` entry for a Claude Code
`mcp.json` / `.claude.json` config. It points at the running
thegent HTTP+SSE MCP server; no tool filtering is applied at the
config level because the server exposes all tools and MCP clients
select the ones they need.

**Parameters**:

- `tool_names`: List of tool names to document in the config metadata.
  Pass an empty list to include all tools.

**Returns**: Dict with shape `{"thegent": {"type": "http", "url": ..., ...}}`.

**Raises**:

- `ValueError`: If any requested tool name is not found in the catalog.

---

## generate_claude_md_snippet

```python
generate_claude_md_snippet(self: Any, tool_names: list[str])
```

Generate a CLAUDE.md section instructing Claude to use thegent tools.

**Parameters**:

- `tool_names`: Tools to document. Empty list includes all tools.

**Returns**: Markdown string ready to paste into a project's CLAUDE.md.

**Raises**:

- `ValueError`: If any requested tool name is not found in the catalog.

---

## generate_mcp_json

```python
generate_mcp_json(self: Any, tool_names: list[str], output_path: Path)
```

Write (or update) an `mcp.json` file in `output_path`.

The file uses Claude Code's `mcpServers` format. When `merge=True`
and the file already exists, the `thegent` server entry is upserted
without touching existing entries.

**Parameters**:

- `tool_names`: Tools to document. Empty list borrows all tools.
- `output_path`: Directory where `mcp.json` will be written.
- `merge`: If True, merge with existing `mcp.json`; otherwise overwrite.

**Returns**: Absolute path to the written file.

---

## get_tool

```python
get_tool(self: Any, name: str)
```

Return the manifest for a tool by name, or None if not found.

---

## list_available_tools

```python
list_available_tools(self: Any)
```

Return all borrowable tool manifests, sorted by category then name.

---

## list_available_tools_by_category

```python
list_available_tools_by_category(self: Any)
```

Return tools grouped by category.

---

## to_dict

```python
to_dict(self: Any)
```

Serialize to plain dict for JSON output.

---

## url

```python
url(self: Any) -> str
```

---

## validate_server_reachable

```python
validate_server_reachable(self: Any)
```

Check whether the configured thegent MCP server is reachable.

Performs a simple HTTP GET to the `/health` endpoint.

**Returns**: True if the server responds with status 200, False otherwise.

---
