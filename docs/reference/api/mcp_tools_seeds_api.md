# mcp_tools_seeds API Reference

> **Source**: `src/thegent/mcp_tools_seeds.py`

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

## thegent_seed_detect

```python
thegent_seed_detect(text: str, source: str, use_llm: bool)
```

Detect idea seeds in text using pattern matching.

Seed ideas are nascent concepts, half-formed requirements, design sketches,
or problem statements that could grow into full features.

Pattern detection:

- Explicit markers: "What if...", "Consider...", "We should..."
- Code quality: TODO, FIXME, XXX comments
- Design keywords: architecture, refactor, optimize, performance, security

**Parameters**:

- `text`: Input text to analyze (max 5000 chars)
- `source`: Source of text (user_prompt, agent_output, claude_history, etc.)
- `use_llm`: Use LLM for classification (slower but catches non-obvious seeds)

**Returns**: Detected seeds with metadata

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

## thegent_seed_list

```python
thegent_seed_list(status: str, tag: Any, source: Any, cd: Any)
```

List stored seeds with optional filtering.

**Parameters**:

- `status`: Filter by status (new, developing, implemented, archived)
- `tag`: Filter by tag (e.g., "performance", "security")
- `source`: Filter by source
- `cd`: Project directory

**Returns**: List of matching seeds

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

## thegent_seed_store

```python
thegent_seed_store(text: str, source: str, confidence: float, tags: Any, cd: Any)
```

Store an idea seed in persistent JSONL storage.

Seeds are stored in docs/research/seeds.jsonl (one JSON object per line).

**Parameters**:

- `text`: Seed text (max 500 chars stored, full text in context)
- `source`: Source of seed
- `confidence`: Confidence level 0.0-1.0
- `tags`: Optional tags (e.g., ["performance", "security"])
- `cd`: Project directory (auto-detected if not provided)

**Returns**: Stored seed with ID and metadata

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
