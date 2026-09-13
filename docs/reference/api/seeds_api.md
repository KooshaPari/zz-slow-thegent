# seeds API Reference

> **Source**: `src/thegent/mcp/tools/seeds.py`

MCP tools for idea seed detection and storage.

Provides tools for:

- Detecting seeds in text using pattern matching
- Storing seeds persistently in JSONL format
- Querying and managing seed ideas
- Exporting seeds to markdown

---

## register_seed_tools

```python
register_seed_tools(mcp: FastMCP)
```

Register seed detection and storage tools.

---

## thegent_seed_export

```python
thegent_seed_export(cd: Any)
```

Export seeds to markdown format.

Generates a human-readable markdown file with all seeds grouped by status.

**Parameters**:

- `cd`: Project directory

**Returns**: Markdown content and export status

---

## thegent_seed_stats

```python
thegent_seed_stats(cd: Any)
```

Get seed storage statistics.

**Parameters**:

- `cd`: Project directory

**Returns**: Storage statistics

---

## thegent_seed_update

```python
thegent_seed_update(seed_id: str, status: Any, tags: Any, context: Any, cd: Any)
```

Update seed metadata.

**Parameters**:

- `seed_id`: Seed ID to update
- `status`: New status (new, developing, implemented, archived)
- `tags`: New tags
- `context`: Additional context
- `cd`: Project directory

**Returns**: Updated seed or error

---
