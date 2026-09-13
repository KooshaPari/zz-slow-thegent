# work_stream API Reference

> **Source**: `src/thegent/planning/work_stream.py`

WP-13001: Work stream and WBS automation manager.

---

## WorkStreamManager

Manages the lifecycle of work packages across WORK_STREAM, WBS_AGENT_PROGRESS, and UNIFIED-WBS.

### Methods

#### WorkStreamManager.**init**

```python
__init__(self: Any, settings: ThegentSettings, base_dir: Any)
```

---

#### WorkStreamManager.claim

```python
claim(self: Any, item_id: str, agent_id: str)
```

Claim an item across all coordination files.

---

#### WorkStreamManager.complete

```python
complete(self: Any, item_id: str, agent_id: str)
```

Mark an item as complete across all files.

---

---

## claim

```python
claim(self: Any, item_id: str, agent_id: str)
```

Claim an item across all coordination files.

---

## complete

```python
complete(self: Any, item_id: str, agent_id: str)
```

Mark an item as complete across all files.

---
