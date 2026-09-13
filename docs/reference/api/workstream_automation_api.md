# workstream_automation API Reference

> **Source**: `src/thegent/utils/workstream_automation.py`

Automate work stream operations (read, parse, update).

---

## WorkStreamAutomation

Automate work stream markdown operations.

### Methods

#### WorkStreamAutomation.**init**

```python
__init__(self: Any, work_stream_path: Any)
```

Initialize work stream automation.

**Parameters**:

- `work_stream_path`: Path to WORK_STREAM.md

---

#### WorkStreamAutomation.claim_item

```python
claim_item(self: Any, item_id: str, agent_id: str)
```

Claim an item from backlog.

**Parameters**:

- `item_id`: Item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

#### WorkStreamAutomation.complete_item

```python
complete_item(self: Any, item_id: str, agent_id: str)
```

Complete an item and move to completed section.

**Parameters**:

- `item_id`: Item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

#### WorkStreamAutomation.read_backlog

```python
read_backlog(self: Any)
```

Read backlog items from work stream.

**Returns**: List of backlog item dictionaries

---

---

## claim_item

```python
claim_item(self: Any, item_id: str, agent_id: str)
```

Claim an item from backlog.

**Parameters**:

- `item_id`: Item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

## complete_item

```python
complete_item(self: Any, item_id: str, agent_id: str)
```

Complete an item and move to completed section.

**Parameters**:

- `item_id`: Item ID
- `agent_id`: Agent identifier

**Returns**: True if successful

---

## read_backlog

```python
read_backlog(self: Any)
```

Read backlog items from work stream.

**Returns**: List of backlog item dictionaries

---
