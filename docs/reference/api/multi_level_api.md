# multi_level API Reference

> **Source**: `src/thegent/cache/multi_level.py`

Multi-level cache: L1 (in-process TTLCache) -&gt; L2 (diskcache on disk).

Architecture:

- L1: cachetools.TTLCache -- fastest, in-process, bounded by maxsize + TTL
- L2: diskcache.Cache -- persistent, SQLite-backed, optional (graceful L1-only fallback)

Read path: L1 hit -&gt; return immediately
L1 miss -&gt; L2 hit -&gt; promote to L1 -&gt; return
L2 miss -&gt; return None (caller computes and calls set())

Write path: write-through to L1 and L2 simultaneously

Thread safety: cachetools.TTLCache is _not_ thread-safe by default; we use threading.Lock
for all L1 mutations. diskcache.Cache is process-safe and thread-safe natively.

Library-first compliance (LIBRARY_FIRST_POLICY.md):

- L1: cachetools.TTLCache -- no custom TTL logic
- L2: diskcache.Cache -- no custom disk serialisation/TTL logic

---

## MultiLevelCache

Two-level cache: L1 in-memory TTLCache -&gt; L2 diskcache on disk.

### Methods

#### MultiLevelCache.**init**

```python
__init__(self: Any, l1_maxsize: int, l1_ttl: float, l2_dir: Any, l2_ttl: float)
```

---

#### MultiLevelCache.clear

```python
clear(self: Any)
```

Clear all entries from both L1 and L2.

---

#### MultiLevelCache.close

```python
close(self: Any)
```

Release resources held by L2 (diskcache file handles).

---

#### MultiLevelCache.delete

```python
delete(self: Any, key: Any)
```

Remove _key_ from both L1 and L2.

---

#### MultiLevelCache.get

```python
get(self: Any, key: Any)
```

Return cached value for _key_, or `None` on a full miss.

Read-through order: L1 -&gt; L2.
On an L2 hit the value is promoted into L1.

---

#### MultiLevelCache.l2_available

```python
l2_available(self: Any)
```

Return True if L2 (diskcache) is active.

---

#### MultiLevelCache.l2_dir

```python
l2_dir(self: Any)
```

Return the disk-cache directory path, or `None` if L2 is inactive.

---

#### MultiLevelCache.set

```python
set(self: Any, key: Any, value: Any, ttl: Any)
```

Store _value_ for _key_ in both L1 and L2 simultaneously (write-through).

**Parameters**:

- `key`: Cache key (must be hashable for L1; must be picklable for L2).
- `value`: Value to store. Must be picklable if L2 is active.
- `ttl`: Per-entry TTL override in seconds. If `None`:
- L1 uses its configured _l1_ttl_.
- L2 uses its configured _l2_ttl_.

---

#### MultiLevelCache.stats

```python
stats(self: Any)
```

Return a snapshot of current cache occupancy.

---

---

## cached_multi

```python
cached_multi(cache: MultiLevelCache)
```

Decorator that memoises a function's return value via _cache_.

The cache key is built from the function's qualified name and its
positional and keyword arguments. Only hashable argument combinations
are cached; unhashable arguments cause the function to run uncached.

Example::

    cache = MultiLevelCache(l1_maxsize=500, l1_ttl=30)

    @cached_multi(cache)
    def expensive(x: int) -&gt; str:
        ...

---

## clear

```python
clear(self: Any)
```

Clear all entries from both L1 and L2.

---

## close

```python
close(self: Any)
```

Release resources held by L2 (diskcache file handles).

---

## decorator

```python
decorator(func: Any)
```

---

## delete

```python
delete(self: Any, key: Any)
```

Remove _key_ from both L1 and L2.

---

## get

```python
get(self: Any, key: Any)
```

Return cached value for _key_, or `None` on a full miss.

Read-through order: L1 -&gt; L2.
On an L2 hit the value is promoted into L1.

---

## l2_available

```python
l2_available(self: Any)
```

Return True if L2 (diskcache) is active.

---

## l2_dir

```python
l2_dir(self: Any)
```

Return the disk-cache directory path, or `None` if L2 is inactive.

---

## set

```python
set(self: Any, key: Any, value: Any, ttl: Any)
```

Store _value_ for _key_ in both L1 and L2 simultaneously (write-through).

**Parameters**:

- `key`: Cache key (must be hashable for L1; must be picklable for L2).
- `value`: Value to store. Must be picklable if L2 is active.
- `ttl`: Per-entry TTL override in seconds. If `None`:
- L1 uses its configured _l1_ttl_.
- L2 uses its configured _l2_ttl_.

---

## stats

```python
stats(self: Any)
```

Return a snapshot of current cache occupancy.

---

## wrapper

---
