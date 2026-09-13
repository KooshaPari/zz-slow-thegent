# always_dumps API Reference

> **Source**: `src/thegent/research/always_dumps.py`

Always write conversation dumps to docs/.

---

## ConversationDumpWriter

Writer for conversation dumps.

### Methods

#### ConversationDumpWriter.**init**

```python
__init__(self: Any, output_dir: Any)
```

Initialize dump writer.

**Parameters**:

- `output_dir`: Output directory for dumps

---

#### ConversationDumpWriter.write_dump

```python
write_dump(self: Any, conversation: dict[(str, Any)], prefix: str)
```

Write conversation dump to file.

**Parameters**:

- `conversation`: Conversation data
- `prefix`: File prefix

**Returns**: Path to written file

---

---

## write_dump

```python
write_dump(self: Any, conversation: dict[(str, Any)], prefix: str)
```

Write conversation dump to file.

**Parameters**:

- `conversation`: Conversation data
- `prefix`: File prefix

**Returns**: Path to written file

---
