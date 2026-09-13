# cache API Reference

> **Source**: `src/thegent/memory/cache.py`

L1 and L2 cache infrastructure for multi-layer memory architecture.

L1: In-process LRU cache with TTL expiration
L2: File-based persistent cache with fallback

---

## L1Cache

In-process LRU cache with TTL expiration.

### Methods

#### L1Cache.**init**

```python
__init__(self: Any, max_size: int, ttl_seconds: int)
```

Initialize L1 cache.

**Parameters**:

- `max_size`: Maximum cache size (default 1000)
- `ttl_seconds`: Time-to-live per entry (default 3600s)

---

#### L1Cache.clear

```python
clear(self: Any)
```

Clear all entries.

---

#### L1Cache.get

```python
get(self: Any, key: str)
```

Get value from cache.

**Parameters**:

- `key`: Cache key

**Returns**: Cached value or None if not found or expired

---

#### L1Cache.set

```python
set(self: Any, key: str, value: Any)
```

Set value in cache.

**Parameters**:

- `key`: Cache key
- `value`: Value to cache

---

#### L1Cache.stats

```python
stats(self: Any)
```

Get cache statistics.

**Returns**: Dict with hit_count, miss_count, hit_rate, size

---

---

## L2Cache

File-based persistent cache.

Stores cache entries to disk for persistence across process restarts.

### Methods

#### L2Cache.**init**

```python
__init__(self: Any, cache_dir: str, ttl_seconds: int)
```

Initialize L2 cache.

**Parameters**:

- `cache_dir`: Directory for cache files (default .cache/l2)
- `ttl_seconds`: Time-to-live per entry (default 86400s = 1 day)

---

#### L2Cache.clear

```python
clear(self: Any)
```

Clear all cache files.

---

#### L2Cache.get

```python
get(self: Any, key: str)
```

Get value from L2 cache.

**Parameters**:

- `key`: Cache key

**Returns**: Cached value or None if not found or expired

---

#### L2Cache.set

```python
set(self: Any, key: str, value: Any)
```

Set value in L2 cache.

**Parameters**:

- `key`: Cache key
- `value`: Value to cache

---

#### L2Cache.stats

```python
stats(self: Any)
```

Get cache statistics.

---

---

## LayeredCache

Layered cache with L1 → L2 fallback.

Implements fallback logic:

1. Check L1 (fast, in-process)
2. Check L2 (slower, file-based)
3. Return None if not found in either layer

### Methods

#### LayeredCache.**init**

```python
__init__(self: Any, l1_size: int, l2_dir: str)
```

Initialize layered cache.

**Parameters**:

- `l1_size`: Max size for L1 cache
- `l2_dir`: Directory for L2 cache

---

#### LayeredCache.clear

```python
clear(self: Any)
```

Clear both layers.

---

#### LayeredCache.get

```python
get(self: Any, key: str)
```

Get from L1, fallback to L2.

**Parameters**:

- `key`: Cache key

**Returns**: Value from L1 or L2, or None

---

#### LayeredCache.set

```python
set(self: Any, key: str, value: Any)
```

Store in both L1 and L2.

**Parameters**:

- `key`: Cache key
- `value`: Value to cache

---

#### LayeredCache.stats

```python
stats(self: Any)
```

Get stats from both layers.

---

---

## clear

```python
clear(self: Any)
```

Clear both layers.

---

## get

```python
get(self: Any, key: str)
```

Get from L1, fallback to L2.

**Parameters**:

- `key`: Cache key

**Returns**: Value from L1 or L2, or None

---

## set

```python
set(self: Any, key: str, value: Any)
```

Store in both L1 and L2.

**Parameters**:

- `key`: Cache key
- `value`: Value to cache

---

## stats

```python
stats(self: Any)
```

Get stats from both layers.

---
