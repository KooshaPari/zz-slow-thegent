# fast_cache API Reference

> **Source**: `src/thegent/infra/fast_cache.py`

Multi-tier caching system for optimal performance.

This module provides a high-performance multi-tier caching system:

- L1: cachetools TTLCache (fastest, automatic TTL, smallest)
- L2: cachetools LRUCache (medium-term, configurable size)
- L3: diskcache (persistent, survives restarts)

Performance improvements:

- Multi-tier caching reduces memory pressure
- Persistent caching survives restarts
- Automatic tier promotion/demotion
- Configurable TTL and size limits
- Library-first (LIBRARY_FIRST_POLICY.md): Uses cachetools for all in-memory caching

---

## MultiTierCache

Multi-tier caching system with automatic tier management.

Tiers:

1. L1: In-memory dict (fastest, smallest, volatile)
2. L2: cachetools LRUCache (medium-term, configurable size)
3. L3: diskcache (persistent, survives restarts)

### Methods

#### MultiTierCache.**init**

```python
__init__(self: Any, l1_size: int, l2_size: int, l3_path: Any, default_ttl: Any)
```

Initialize multi-tier cache.

**Parameters**:

- `l1_size`: Maximum items in L1 cache
- `l2_size`: Maximum items in L2 cache
- `l3_path`: Path for L3 disk cache (None to disable)
- `default_ttl`: Default time-to-live in seconds (None = no expiry)

---

#### MultiTierCache.clear

```python
clear(self: Any)
```

Clear all tiers.

---

#### MultiTierCache.delete

```python
delete(self: Any, key: str)
```

Delete key from all tiers.

---

#### MultiTierCache.enable_invalidation

```python
enable_invalidation(self: Any, directory: Any)
```

Enable real-time cache invalidation based on file changes (TGNT-P9.2).

---

#### MultiTierCache.get

```python
get(self: Any, key: str)
```

Get value from cache (checks all tiers).

**Parameters**:

- `key`: Cache key

**Returns**: Cached value or None if not found

---

#### MultiTierCache.get_with_fetch

```python
get_with_fetch(self: Any, key: str, fetch_func: Any, ttl: Any)
```

Get value from cache, or fetch and store if missing (with Singleflight TGNT-P9.1).

---

#### MultiTierCache.set

```python
set(self: Any, key: str, value: Any, ttl: Any)
```

Set value in cache (stores in all tiers).

**Parameters**:

- `key`: Cache key
- `value`: Value to cache
- `ttl`: Time-to-live in seconds (uses default_ttl if None)

---

#### MultiTierCache.stats

```python
stats(self: Any)
```

Get cache statistics.

---

---

## clear

```python
clear(self: Any)
```

Clear all tiers.

---

## delete

```python
delete(self: Any, key: str)
```

Delete key from all tiers.

---

## enable_invalidation

```python
enable_invalidation(self: Any, directory: Any)
```

Enable real-time cache invalidation based on file changes (TGNT-P9.2).

---

## get

```python
get(self: Any, key: str)
```

Get value from cache (checks all tiers).

**Parameters**:

- `key`: Cache key

**Returns**: Cached value or None if not found

---

## get_cache

```python
get_cache(l1_size: int, l2_size: int, l3_path: Any, default_ttl: Any)
```

Get global multi-tier cache instance.

**Parameters**:

- `l1_size`: Maximum items in L1 cache
- `l2_size`: Maximum items in L2 cache
- `l3_path`: Path for L3 disk cache
- `default_ttl`: Default time-to-live in seconds

**Returns**: MultiTierCache instance

---

## get_with_fetch

```python
get_with_fetch(self: Any, key: str, fetch_func: Any, ttl: Any)
```

Get value from cache, or fetch and store if missing (with Singleflight TGNT-P9.1).

---

## set

```python
set(self: Any, key: str, value: Any, ttl: Any)
```

Set value in cache (stores in all tiers).

**Parameters**:

- `key`: Cache key
- `value`: Value to cache
- `ttl`: Time-to-live in seconds (uses default_ttl if None)

---

## stats

```python
stats(self: Any)
```

Get cache statistics.

---
