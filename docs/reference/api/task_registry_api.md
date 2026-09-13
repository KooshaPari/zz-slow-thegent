# task_registry API Reference

> **Source**: `src/thegent/mcp/task_registry.py`

FastMCP task mode support for thegent.

Provides an asyncio-based task registry that allows long-running MCP tool calls
to be tracked, status-polled, and cancelled by MCP clients.

Usage: # Wrap a long-running call as a background task
task_id = \_TASK_REGISTRY.create(asyncio.create_task(some_coroutine()))

    # Client polls status
    status = _TASK_REGISTRY.status(task_id)

    # Client cancels
    _TASK_REGISTRY.cancel(task_id)

The registry is module-level (process singleton) and is safe for concurrent
asyncio access. It does NOT persist across process restarts.

---

## AsyncTaskRegistry

Registry mapping task_id -&gt; asyncio.Task with status/progress tracking.

Thread-safety: this class is designed for asyncio single-threaded use.
All mutations happen within the event loop; no locks are required.

### Methods

#### AsyncTaskRegistry.**init**

```python
__init__(self: Any)
```

---

#### AsyncTaskRegistry.cancel

```python
cancel(self: Any, task_id: str) -> {"task_id"
```

Request cancellation of a running task.

**Returns** (`{"task_id"`): str, "cancelled": bool, "status": str}

---

#### AsyncTaskRegistry.cleanup

```python
cleanup(self: Any, max_age_s: float)
```

Remove completed tasks older than max_age_s seconds. Returns count removed.

---

#### AsyncTaskRegistry.create

```python
create(self: Any, task: asyncio.Task[Any], task_id: Any)
```

Register a running asyncio task and return its task_id.

---

#### AsyncTaskRegistry.list_tasks

```python
list_tasks(self: Any)
```

Return status summary for all tracked tasks.

---

#### AsyncTaskRegistry.status

```python
status(self: Any, task_id: str)
```

Return status dict for task_id.

**Returns**: {
"task_id": str,
"status": "running" | "done" | "error" | "cancelled",
"progress": float,
"total": float | None,
"message": str,
"result": Any | None, # only when done
"error": str | None, # only when error
"elapsed_s": float,
}

---

#### AsyncTaskRegistry.update_progress

```python
update_progress(self: Any, task_id: str, progress: float, total: Any, message: str)
```

Update progress metadata for an in-flight task (called from within the task).

---

---

## \_TaskEntry

Internal record for a tracked asyncio task.

### Methods

#### \_TaskEntry.**init**

```python
__init__(self: Any, task_id: str, task: asyncio.Task[Any])
```

---

---

## cancel

```python
cancel(self: Any, task_id: str) -> {"task_id"
```

Request cancellation of a running task.

**Returns** (`{"task_id"`): str, "cancelled": bool, "status": str}

---

## cleanup

```python
cleanup(self: Any, max_age_s: float)
```

Remove completed tasks older than max_age_s seconds. Returns count removed.

---

## create

```python
create(self: Any, task: asyncio.Task[Any], task_id: Any)
```

Register a running asyncio task and return its task_id.

---

## get_task_registry

Return the process-singleton AsyncTaskRegistry.

---

## list_tasks

```python
list_tasks(self: Any)
```

Return status summary for all tracked tasks.

---

## status

```python
status(self: Any, task_id: str)
```

Return status dict for task_id.

**Returns**: {
"task_id": str,
"status": "running" | "done" | "error" | "cancelled",
"progress": float,
"total": float | None,
"message": str,
"result": Any | None, # only when done
"error": str | None, # only when error
"elapsed_s": float,
}

---

## update_progress

```python
update_progress(self: Any, task_id: str, progress: float, total: Any, message: str)
```

Update progress metadata for an in-flight task (called from within the task).

---
