# redis_concurrency API Reference

> **Source**: `src/thegent/orchestration/consensus/redis_concurrency.py`

Redis-backed distributed concurrency limits for swarm coordination.

Implements distributed concurrency control using Redis SETNX + EXPIRE so that
multiple thegent instances share a single global slot pool. Falls back to the
in-process controller when Redis is not installed or unreachable.

Configuration via environment variables (all read through ThegentSettings):
THGENT_REDIS_HOST - Redis host (default: localhost)
THGENT_REDIS_PORT - Redis port (default: 6379)
THGENT_REDIS_DB - Redis DB index (default: 0)
THGENT_REDIS_PASSWORD - Optional password
THGENT_REDIS_KEY_PREFIX - Key namespace (default: thgent:concurrency)
THGENT_REDIS_CONCURRENCY_LIMIT - Max concurrent slots (default: 10)

swarm-redis-concurrency

---

## RedisConcurrencyController

Distributed concurrency limits backed by Redis SETNX/EXPIRE.

Each acquired slot is represented by a Redis key:
`{key_prefix}:slot:{run_id}`

The key expires automatically after `slot_ttl_s` seconds so stale slots
(from crashed workers) are reclaimed without manual intervention.

Fallback: if the `redis` package is not installed _or_ Redis is
unreachable at construction time, the controller silently falls back to
an in-process `_InMemoryStore` that behaves identically within a single
process. `is_available()` returns `False` in fallback mode.

### Methods

#### RedisConcurrencyController.**init**

```python
__init__(self: Any, redis_config: Any, max_concurrent: Any, slot_ttl_s: float)
```

Initialise the controller.

**Parameters**:

- `redis_config`: Connection parameters. When _None_, reads from env.
- `max_concurrent`: Maximum concurrent slots across all instances.
  Reads `THGENT_REDIS_CONCURRENCY_LIMIT` when _None_
  (default: 10).
- `slot_ttl_s`: TTL in seconds for each slot key. Slots older than
  this are considered stale and released automatically.

---

#### RedisConcurrencyController.get_active_count

```python
get_active_count(self: Any)
```

Return the number of currently active (acquired) slots.

When called from within a running event loop (async context), returns
a synchronous approximate count from the fallback store or 0 for
Redis mode (use `aget_active_count()` from async code).

---

#### RedisConcurrencyController.is_available

```python
is_available(self: Any)
```

Return True when Redis is configured and reachable (not fallback mode).

---

#### RedisConcurrencyController.list_active

```python
list_active(self: Any)
```

Return the list of run_ids currently holding a slot (synchronous).

---

---

## RedisConfig

Connection parameters for the Redis backend.

### Methods

#### RedisConfig.from_env

```python
from_env(cls: Any)
```

Deprecated: Use from_settings() instead. Kept for backwards compatibility.

---

#### RedisConfig.from_settings

```python
from_settings(cls: Any)
```

Build config from ThegentSettings.

---

---

## \_InMemoryStore

Thread-safe in-process slot tracker used as Redis fallback.

### Methods

#### \_InMemoryStore.count_with_prefix_sync

```python
count_with_prefix_sync(self: Any, prefix: str)
```

Synchronous approximate count without pruning (no await required).

---

---

## count_with_prefix_sync

```python
count_with_prefix_sync(self: Any, prefix: str)
```

Synchronous approximate count without pruning (no await required).

---

## from_env

```python
from_env(cls: Any)
```

Deprecated: Use from_settings() instead. Kept for backwards compatibility.

---

## from_settings

```python
from_settings(cls: Any)
```

Build config from ThegentSettings.

---

## get_active_count

```python
get_active_count(self: Any)
```

Return the number of currently active (acquired) slots.

When called from within a running event loop (async context), returns
a synchronous approximate count from the fallback store or 0 for
Redis mode (use `aget_active_count()` from async code).

---

## is_available

```python
is_available(self: Any)
```

Return True when Redis is configured and reachable (not fallback mode).

---

## list_active

```python
list_active(self: Any)
```

Return the list of run_ids currently holding a slot (synchronous).

---

## make_redis_concurrency_controller

```python
make_redis_concurrency_controller(max_concurrent: Any, slot_ttl_s: float)
```

Create a `RedisConcurrencyController` from environment variables.

When `THGENT_REDIS_HOST` is not set, the controller will still be
created but immediately fall back to in-process limits (`is_available()`
returns `False`).

---
