# ipc API Reference

> **Source**: `src/thegent/infra/ipc.py`

Phase 11: IPC Primitives implementation.

Includes tmpfs mesh directory, atomic mkdir locks, Maildir queue, and WAL.

---

## IPCMesh

Manages the IPC mesh directory and atomic primitives.

### Methods

#### IPCMesh.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### IPCMesh.acquire_atomic_lock

```python
acquire_atomic_lock(self: Any, lock_name: str, ttl: int)
```

Atomic lock primitive using mkdir (EEXIST).

---

#### IPCMesh.release_atomic_lock

```python
release_atomic_lock(self: Any, lock_name: str)
```

Release atomic lock.

---

---

## MaildirQueue

IPC message queue following Maildir-like tmp/new/cur lifecycle.

### Methods

#### MaildirQueue.**init**

```python
__init__(self: Any, queue_dir: Path)
```

---

#### MaildirQueue.receive

```python
receive(self: Any)
```

Receive message by moving it from 'new' to 'cur'.

---

#### MaildirQueue.send

```python
send(self: Any, message: dict[(str, Any)])
```

Send message by placing it in 'new'.

---

---

## WriteAheadLog

WAL implementation for crash recovery.

### Methods

#### WriteAheadLog.**init**

```python
__init__(self: Any, wal_file: Path)
```

---

#### WriteAheadLog.log

```python
log(self: Any, operation: str, data: dict[(str, Any)])
```

Append entry to WAL before execution.

---

#### WriteAheadLog.replay

```python
replay(self: Any)
```

Read WAL entries for recovery.

---

---

## acquire_atomic_lock

```python
acquire_atomic_lock(self: Any, lock_name: str, ttl: int)
```

Atomic lock primitive using mkdir (EEXIST).

---

## log

```python
log(self: Any, operation: str, data: dict[(str, Any)])
```

Append entry to WAL before execution.

---

## receive

```python
receive(self: Any)
```

Receive message by moving it from 'new' to 'cur'.

---

## release_atomic_lock

```python
release_atomic_lock(self: Any, lock_name: str)
```

Release atomic lock.

---

## replay

```python
replay(self: Any)
```

Read WAL entries for recovery.

---

## send

```python
send(self: Any, message: dict[(str, Any)])
```

Send message by placing it in 'new'.

---
