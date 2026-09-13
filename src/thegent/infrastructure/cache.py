"""Unified caching layer using diskcache and cachetools.

Replaces 8 custom cache implementations (4,000+ LOC) with a single
unified cache using diskcache for persistent storage and cachetools
for in-memory LRU caching.

Libraries used (already installed):
    - diskcache: Persistent disk-based cache
    - cachetools: In-memory LRU/TTL caching
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from cachetools import LRUCache, TTLCache
from diskcache import Cache as DiskCache

T = TypeVar("T")


class UnifiedCache:
    """Unified cache with tiered storage.

    Tier 1: In-memory LRU (fastest, smallest)
    Tier 2: In-memory TTL (fast, time-bounded)
    Tier 3: Persistent disk cache (slowest, largest)

    Replaces: cache_v2.py, cache.py, semantic_cache.py, etc.
    """

    def __init__(
        self,
        disk_path: Path | str = ".cache/thegent",
        lru_size: int = 1000,
        ttl_seconds: int = 300,
    ) -> None:
        self._disk_path = Path(disk_path)
        self._disk_path.mkdir(parents=True, exist_ok=True)

        # Tier 1: In-memory LRU
        self._lru: LRUCache[str, Any] = LRUCache(maxsize=lru_size)

        # Tier 2: In-memory TTL
        self._ttl: TTLCache[str, Any] = TTLCache(maxsize=1000, ttl=ttl_seconds)

        # Tier 3: Persistent disk cache
        self._disk = DiskCache(str(self._disk_path))

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """Create a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get value from cache (checks all tiers)."""
        # Check Tier 1 (LRU) - fastest
        if key in self._lru:
            return self._lru[key]

        # Check Tier 2 (TTL)
        if key in self._ttl:
            return self._ttl[key]

        # Check Tier 3 (Disk)
        value = self._disk.get(key)
        if value is not None:
            # Promote to in-memory caches
            self._ttl[key] = value
            return value

        return None

    def set(self, key: str, value: Any, tier: str = "ttl", expire: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            tier: Which tier to use ("lru", "ttl", "disk")
            expire: Seconds until expiration (disk cache only)
        """
        if tier == "lru":
            self._lru[key] = value
        elif tier == "ttl":
            self._ttl[key] = value
        elif tier == "disk":
            self._disk.set(key, value, expire=expire)
            self._ttl[key] = value  # Also cache in memory
        else:
            raise ValueError(f"Unknown tier: {tier}")

    def delete(self, key: str) -> bool:
        """Delete key from all cache tiers."""
        deleted = False
        for cache in [self._lru, self._ttl, self._disk]:
            try:
                if key in cache:
                    del cache[key]
                    deleted = True
            except (KeyError, Exception):
                pass
        return deleted

    def clear(self, tier: str | None = None) -> None:
        """Clear cache (all tiers or specific tier)."""
        if tier is None or tier == "lru":
            self._lru.clear()
        if tier is None or tier == "ttl":
            self._ttl.clear()
        if tier is None or tier == "disk":
            self._disk.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "lru": {"size": len(self._lru), "maxsize": self._lru.maxsize},
            "ttl": {"size": len(self._ttl), "maxsize": self._ttl.maxsize},
            "disk": {"size": len(self._disk)},
        }

    @contextmanager
    def transaction(self):
        """Context manager for cache transactions."""
        try:
            yield self
        except Exception:
            # Rollback: clear in-memory caches, disk cache is atomic
            self._lru.clear()
            self._ttl.clear()
            raise

    def close(self) -> None:
        """Close the disk cache (cleanup)."""
        self._disk.close()


# Decorator for function-level caching
def cached(
    cache: UnifiedCache | None = None,
    key_func: Any = None,
    tier: str = "ttl",
    expire: int = 300,
):
    """Decorator to cache function results.

    Args:
        cache: Cache instance (uses global if None)
        key_func: Function to generate cache key
        tier: Cache tier to use
        expire: Expiration in seconds
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _cache = cache or get_cache()

            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = _cache._make_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            result = _cache.get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            _cache.set(key, result, tier=tier, expire=expire)
            return result

        return wrapper

    return decorator


# Global cache instance
_default_cache: UnifiedCache | None = None


def get_cache(disk_path: Path | str = ".cache/thegent", lru_size: int = 1000) -> UnifiedCache:
    """Get or create the default cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = UnifiedCache(disk_path=disk_path, lru_size=lru_size)
    return _default_cache


# Convenience functions
def cache_get(key: str) -> Any | None:
    """Get value from global cache."""
    return get_cache().get(key)


def cache_set(key: str, value: Any, tier: str = "ttl", expire: int | None = None) -> None:
    """Set value in global cache."""
    get_cache().set(key, value, tier=tier, expire=expire)


def cache_delete(key: str) -> bool:
    """Delete key from global cache."""
    return get_cache().delete(key)


def cache_clear(tier: str | None = None) -> None:
    """Clear global cache."""
    get_cache().clear(tier)
