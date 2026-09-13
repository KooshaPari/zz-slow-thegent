# task_queue API Reference

> **Source**: `src/thegent/mesh/task_queue.py`

Maildir-style teammate task queue for agent mesh coordination (heliosShield Phase 11).

All file operations are atomic using os.rename (POSIX rename guarantee).
The queue is fully crash-recoverable: no in-memory state is required.
Tasks stranded in `cur/` after a crash are visible via `list_pending()`.

---

## MaildirQueue

Filesystem-backed task queue using Maildir conventions.

Directory layout::

    &lt;path&gt;/
      tmp/   # staging area; task is written here first
      new/   # ready to be claimed by a worker
      cur/   # claimed by a worker; in-flight

Atomic delivery: write to `tmp/` then `os.rename` to `new/`.
Atomic claim: `os.rename` from `new/` to `cur/`.

Task file format (JSON)::

    {
        "id":         "&lt;uuid&gt;",
        "payload":    &lt;any JSON-serialisable value&gt;,
        "priority":   &lt;int, 0-9; lower = higher priority&gt;,
        "created_at": &lt;unix timestamp float&gt;,
        "attempts":   &lt;int&gt;
    }

### Methods

#### MaildirQueue.**init**

```python
__init__(self: Any, path: Path)
```

---

#### MaildirQueue.ack

```python
ack(self: Any, task_id: str)
```

Acknowledge successful completion of _task_id_.

Removes the task file from `cur/`. Silently ignores a missing file
(idempotent — safe to call more than once).

**Parameters**:

- `task_id`: The task ID returned by :py:meth:`enqueue`.

---

#### MaildirQueue.dequeue

```python
dequeue(self: Any)
```

Claim the highest-priority task from `new/`.

Moves the chosen file from `new/` to `cur/` atomically.
Returns `None` when the queue is empty.

Priority ordering: tasks with a lower `priority` value (e.g. 0)
are returned before higher values. Ties are broken by
`created_at` (oldest first, FIFO within the same priority).

**Returns**: The task envelope dict, or `None` if the queue is empty.

---

#### MaildirQueue.enqueue

```python
enqueue(self: Any, task: dict[(str, Any)], priority: int)
```

Write _task_ to the queue atomically.

1. Serialise the envelope to `tmp/&lt;id&gt;`.
2. `os.rename` to `new/&lt;id&gt;` (atomic on POSIX).

**Parameters**:

- `task`: Arbitrary JSON-serialisable payload.
- `priority`: Integer 0-9; lower numbers are consumed first by
  :py:meth:`dequeue`. Defaults to 5 (middle).

**Returns**: The unique task ID string.

---

#### MaildirQueue.list_pending

```python
list_pending(self: Any)
```

Return all pending tasks from both `new/` and `cur/`.

Tasks in `cur/` are in-flight (being processed or stranded after a
crash). Tasks in `new/` are waiting to be claimed.

**Returns**: List of task envelope dicts, unsorted.

---

#### MaildirQueue.nack

```python
nack(self: Any, task_id: str)
```

Negative-acknowledge _task_id_: return it to `new/` for retry.

Moves the file from `cur/` back to `new/` atomically.
Silently ignores a missing file (idempotent).

**Parameters**:

- `task_id`: The task ID returned by :py:meth:`enqueue`.

---

---

## ack

```python
ack(self: Any, task_id: str)
```

Acknowledge successful completion of _task_id_.

Removes the task file from `cur/`. Silently ignores a missing file
(idempotent — safe to call more than once).

**Parameters**:

- `task_id`: The task ID returned by :py:meth:`enqueue`.

---

## dequeue

```python
dequeue(self: Any)
```

Claim the highest-priority task from `new/`.

Moves the chosen file from `new/` to `cur/` atomically.
Returns `None` when the queue is empty.

Priority ordering: tasks with a lower `priority` value (e.g. 0)
are returned before higher values. Ties are broken by
`created_at` (oldest first, FIFO within the same priority).

**Returns**: The task envelope dict, or `None` if the queue is empty.

---

## enqueue

```python
enqueue(self: Any, task: dict[(str, Any)], priority: int)
```

Write _task_ to the queue atomically.

1. Serialise the envelope to `tmp/&lt;id&gt;`.
2. `os.rename` to `new/&lt;id&gt;` (atomic on POSIX).

**Parameters**:

- `task`: Arbitrary JSON-serialisable payload.
- `priority`: Integer 0-9; lower numbers are consumed first by
  :py:meth:`dequeue`. Defaults to 5 (middle).

**Returns**: The unique task ID string.

---

## list_pending

```python
list_pending(self: Any)
```

Return all pending tasks from both `new/` and `cur/`.

Tasks in `cur/` are in-flight (being processed or stranded after a
crash). Tasks in `new/` are waiting to be claimed.

**Returns**: List of task envelope dicts, unsorted.

---

## nack

```python
nack(self: Any, task_id: str)
```

Negative-acknowledge _task_id_: return it to `new/` for retry.

Moves the file from `cur/` back to `new/` atomically.
Silently ignores a missing file (idempotent).

**Parameters**:

- `task_id`: The task ID returned by :py:meth:`enqueue`.

---
