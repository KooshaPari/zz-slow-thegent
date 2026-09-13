# workstream API Reference

> **Source**: `src/thegent/utils/workstream.py`

Automated work stream operations (read, parse, update).

---

## WorkStreamOps

Automated operations on work stream files.

### Methods

#### WorkStreamOps.**init**

```python
__init__(self: Any, base_dir: Any)
```

Initialize work stream operations.

**Parameters**:

- `base_dir`: Base directory for work stream files

---

#### WorkStreamOps.claim_item

```python
claim_item(self: Any, item_id: str, agent_id: str)
```

Claim an item by adding it to CLAIMED section.

**Parameters**:

- `item_id`: Work item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

#### WorkStreamOps.complete_item

```python
complete_item(self: Any, item_id: str, agent_id: str)
```

Mark an item as complete.

**Parameters**:

- `item_id`: Work item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

#### WorkStreamOps.read_backlog

```python
read_backlog(self: Any)
```

Read all items from BACKLOG section.

**Returns**: List of backlog items with id, title, priority, depends

---

---

## claim_item

```python
claim_item(self: Any, item_id: str, agent_id: str)
```

Claim an item by adding it to CLAIMED section.

**Parameters**:

- `item_id`: Work item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

## complete_item

```python
complete_item(self: Any, item_id: str, agent_id: str)
```

Mark an item as complete.

**Parameters**:

- `item_id`: Work item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

## read_backlog

```python
read_backlog(self: Any)
```

Read all items from BACKLOG section.

**Returns**: List of backlog items with id, title, priority, depends

---
