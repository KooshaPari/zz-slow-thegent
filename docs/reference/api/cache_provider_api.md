# cache_provider API Reference

> **Source**: `src/thegent/memory/cache_provider.py`

Abstract cache provider interface for Supermemory L1/L2 cache layers.

This module defines the CacheProvider ABC that all concrete cache implementations
(Redis, FileCache, Memory) must implement. It supports TTL, eviction policies,
and hierarchical cache management.

---

## CacheItem

Represents a single cache item with metadata.

### Methods

#### CacheItem.is_expired

```python
is_expired(self: Any)
```

Check if this item has expired.

---

#### CacheItem.ttl_remaining

```python
ttl_remaining(self: Any)
```

Get remaining TTL in seconds, or None if no expiry.

---

---

## CacheProvider

Abstract base class for cache providers.

Defines the interface that all cache implementations must follow.
Implementations should support:

- Key-value storage with optional TTL
- Automatic expiration
- Hit/miss tracking (optional)
- Flush and eviction operations

**Inherits from**: `ABC`

---

## is_expired

```python
is_expired(self: Any)
```

Check if this item has expired.

---

## ttl_remaining

```python
ttl_remaining(self: Any)
```

Get remaining TTL in seconds, or None if no expiry.

---
