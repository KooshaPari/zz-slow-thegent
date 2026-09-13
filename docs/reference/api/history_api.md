# history API Reference

> **Source**: `src/thegent/infra/history.py`

WP-22001: Context-Aware Shell History.

Stores shell commands with rich context (cwd, task_id, exit_code) in a local SQLite database.
Enables semantic search and task reconstruction.

---

## ContextHistory

Manages the persistent store for context-aware shell history.

### Methods

#### ContextHistory.**init**

```python
__init__(self: Any, db_path: Any)
```

---

#### ContextHistory.get_task_sequence

```python
get_task_sequence(self: Any, task_id: str)
```

Retrieve the sequence of commands executed for a specific task.

---

#### ContextHistory.record

```python
record(self: Any, entry: HistoryEntry)
```

Record a new command in history.

---

#### ContextHistory.search

```python
search(self: Any, query: Any, task_id: Any, cwd: Any, limit: int)
```

Search history with filters.

---

---

## HistoryEntry

Rich metadata for a single shell command.

**Inherits from**: `BaseModel`

---

## get_task_sequence

```python
get_task_sequence(self: Any, task_id: str)
```

Retrieve the sequence of commands executed for a specific task.

---

## record

```python
record(self: Any, entry: HistoryEntry)
```

Record a new command in history.

---

## search

```python
search(self: Any, query: Any, task_id: Any, cwd: Any, limit: int)
```

Search history with filters.

---
