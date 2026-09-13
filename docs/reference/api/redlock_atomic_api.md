# redlock_atomic API Reference

> **Source**: `src/thegent/orchestration/consensus/redlock_atomic.py`

Redlock-based atomic distributed lock for swarm coordination.

Implements the Redlock algorithm (https://redis.io/docs/manual/patterns/distributed-locks/)
using SET NX PX across multiple Redis nodes with quorum consensus for
fault-tolerant distributed mutual exclusion.

Falls back to an in-process threading.Lock when Redis is not installed
or unreachable, with a logged warning.

Configuration via environment variable:
THGENT_REDLOCK_NODES - Comma-separated Redis URLs
(default: redis://localhost:6379)

swarm-redlock-atomic

---

## RedlockAcquireResult

Result returned from `RedlockController.acquire`.

---

## RedlockController

Distributed Redlock-style acquire/release for a single named key.

When multiple Redis nodes are configured (`THGENT_REDLOCK_NODES`), uses
quorum consensus: a lock is acquired when SET NX PX succeeds on a majority
(&gt; N/2) of nodes and the total time taken is less than the requested TTL.

When only one node is configured (the common case), degrades gracefully to
a simple `SET key lock_id NX PX ttl` on that single node.

On Redis unavailability (import error _or_ connection error), falls back to
an in-process `threading.Lock` with a warning log — suitable for
single-process usage.

### Methods

#### RedlockController.**init**

```python
__init__(self: Any, key: str, ttl_ms: int)
```

Create a controller for the given lock key.

**Parameters**:

- `key`: The Redis key name for the lock.
- `ttl_ms`: Lock TTL in milliseconds. Stale locks auto-expire.
- `redis_nodes`: List of Redis URLs. When `None`, reads
  `THGENT_REDLOCK_NODES` from the environment,
  defaulting to `["redis://localhost:6379"]`.

---

#### RedlockController.acquire

```python
acquire(self: Any)
```

Attempt to acquire the distributed lock atomically.

Uses `SET key lock_id NX PX ttl` on each configured Redis node.
For multi-node setups, requires quorum (majority) and validates that
the elapsed time is within the granted TTL (drift-aware check).

**Returns**: `RedlockAcquireResult` with `acquired=True` and a unique
`lock_id` on success; `acquired=False, lock_id="", expires_at=0.0`
on failure.

---

#### RedlockController.extend

```python
extend(self: Any, lock_id: str, ttl_ms: int)
```

Extend the lock TTL if still owned.

Uses a Lua script to atomically extend only when the lock is still held
by the given `lock_id`.

**Parameters**:

- `lock_id`: The token from the original `acquire()` call.
- `ttl_ms`: New TTL in milliseconds from now.

**Returns**: `True` if the TTL was extended; `False` otherwise.

---

#### RedlockController.is_available

```python
is_available(self: Any)
```

Return `True` when backed by real Redis (not in-memory fallback).

---

#### RedlockController.is_locked

```python
is_locked(self: Any)
```

Return `True` if any valid lock exists for this key.

Note: This is a point-in-time check subject to race conditions; do not
use it for coordination decisions — use `acquire()` instead.

---

#### RedlockController.release

```python
release(self: Any, lock_id: str)
```

Release the lock atomically only if we are the owner.

Uses a Lua script (`GET` + `DEL`) to ensure we never delete a lock
held by another process/thread.

**Parameters**:

- `lock_id`: The token returned by a successful `acquire()` call.

**Returns**: `True` if the lock was released; `False` if not held or
already expired.

---

---

## \_InMemoryLockState

In-process lock state used when Redis is unavailable.

### Methods

#### \_InMemoryLockState.acquire

```python
acquire(self: Any, lock_id: str, ttl_ms: int)
```

Acquire the in-memory lock. Returns True if successful.

---

#### \_InMemoryLockState.extend

```python
extend(self: Any, lock_id: str, ttl_ms: int)
```

Extend TTL if still owned by lock_id. Returns True if extended.

---

#### \_InMemoryLockState.is_locked

```python
is_locked(self: Any)
```

Return True if a valid lock is currently held.

---

#### \_InMemoryLockState.release

```python
release(self: Any, lock_id: str)
```

Release the lock if held by lock_id. Returns True if released.

---

---

## acquire

```python
acquire(self: Any)
```

Attempt to acquire the distributed lock atomically.

Uses `SET key lock_id NX PX ttl` on each configured Redis node.
For multi-node setups, requires quorum (majority) and validates that
the elapsed time is within the granted TTL (drift-aware check).

**Returns**: `RedlockAcquireResult` with `acquired=True` and a unique
`lock_id` on success; `acquired=False, lock_id="", expires_at=0.0`
on failure.

---

## extend

```python
extend(self: Any, lock_id: str, ttl_ms: int)
```

Extend the lock TTL if still owned.

Uses a Lua script to atomically extend only when the lock is still held
by the given `lock_id`.

**Parameters**:

- `lock_id`: The token from the original `acquire()` call.
- `ttl_ms`: New TTL in milliseconds from now.

**Returns**: `True` if the TTL was extended; `False` otherwise.

---

## is_available

```python
is_available(self: Any)
```

Return `True` when backed by real Redis (not in-memory fallback).

---

## is_locked

```python
is_locked(self: Any)
```

Return `True` if any valid lock exists for this key.

Note: This is a point-in-time check subject to race conditions; do not
use it for coordination decisions — use `acquire()` instead.

---

## make_redlock_controller

```python
make_redlock_controller(key: str)
```

Create a `RedlockController` for the given lock key.

Keyword arguments are forwarded to `RedlockController.__init__`
(e.g. `ttl_ms`, `redis_nodes`).

Example::

    rl = make_redlock_controller("my-lock", ttl_ms=3000)
    result = rl.acquire()
    if result.acquired:
        try:
            ...
        finally:
            rl.release(result.lock_id)

---

## release

```python
release(self: Any, lock_id: str)
```

Release the lock atomically only if we are the owner.

Uses a Lua script (`GET` + `DEL`) to ensure we never delete a lock
held by another process/thread.

**Parameters**:

- `lock_id`: The token returned by a successful `acquire()` call.

**Returns**: `True` if the lock was released; `False` if not held or
already expired.

---
