# always_write_dumps API Reference

> **Source**: `src/thegent/research/always_write_dumps.py`

CLAUDE.md: always write conversation dumps to docs/.

---

## ConversationDumper

Always write conversation dumps to docs/.

### Methods

#### ConversationDumper.**init**

```python
__init__(self: Any, docs_dir: Path)
```

---

#### ConversationDumper.dump_conversation

```python
dump_conversation(self: Any, conversation_id: str, content: str)
```

Dump conversation content to a file.

**Parameters**:

- `conversation_id`: Unique identifier for the conversation
- `content`: Conversation content to dump

**Returns**: Path to the created dump file

---

#### ConversationDumper.list_dumps

```python
list_dumps(self: Any)
```

List all conversation dumps.

**Returns**: List of paths to dump files

---

---

## dump_conversation

```python
dump_conversation(self: Any, conversation_id: str, content: str)
```

Dump conversation content to a file.

**Parameters**:

- `conversation_id`: Unique identifier for the conversation
- `content`: Conversation content to dump

**Returns**: Path to the created dump file

---

## list_dumps

```python
list_dumps(self: Any)
```

List all conversation dumps.

**Returns**: List of paths to dump files

---
