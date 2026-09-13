# locking API Reference

> **Source**: `src/thegent/queue/locking.py`

Advisory file locking for queue operations (atomic claim, release, extend_lease).

---

## QueueLock

Advisory exclusive lock on the queue file for atomic multi-line updates.

Provides read/write through the locked file handle so all I/O uses the same fd.

### Methods

#### QueueLock.**init**

```python
__init__(self: Any, queue_path: Path)
```

---

#### QueueLock.read_entries

```python
read_entries(self: Any)
```

Read entries from the locked file. Call only while holding the lock.

---

#### QueueLock.write_entries

```python
write_entries(self: Any, entries: list[dict])
```

Write entries to the locked file (truncate + rewrite). Call only while holding the lock.

---

---

## read_entries

```python
read_entries(self: Any)
```

Read entries from the locked file. Call only while holding the lock.

---

## write_entries

```python
write_entries(self: Any, entries: list[dict])
```

Write entries to the locked file (truncate + rewrite). Call only while holding the lock.

---
