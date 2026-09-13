# queue API Reference

> **Source**: `src/thegent/task_queue/queue.py`

Task queue system.

---

## TaskQueue

Task queue implementation.

### Methods

#### TaskQueue.**init**

```python
__init__(self: Any)
```

Initialize task queue.

---

#### TaskQueue.complete

```python
complete(self: Any, task_id: str)
```

Mark task as complete.

**Parameters**:

- `task_id`: Task identifier

---

#### TaskQueue.dequeue

```python
dequeue(self: Any)
```

Dequeue a task.

**Returns**: Task tuple or None

---

#### TaskQueue.enqueue

```python
enqueue(self: Any, task_id: str, task: dict[(str, Any)])
```

Enqueue a task.

**Parameters**:

- `task_id`: Task identifier
- `task`: Task dictionary

---

---

## complete

```python
complete(self: Any, task_id: str)
```

Mark task as complete.

**Parameters**:

- `task_id`: Task identifier

---

## dequeue

```python
dequeue(self: Any)
```

Dequeue a task.

**Returns**: Task tuple or None

---

## enqueue

```python
enqueue(self: Any, task_id: str, task: dict[(str, Any)])
```

Enqueue a task.

**Parameters**:

- `task_id`: Task identifier
- `task`: Task dictionary

---
