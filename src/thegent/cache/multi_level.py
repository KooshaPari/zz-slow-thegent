"""Multi-level caching system.

FR traceability: FR-CACHE-001 (multi-level caching: L1 memory -> L2 disk)
"""

from __future__ import annotations

import functools
import threading
from pathlib import Path
from typing import Any

# Check if diskcache is available
try:
    import diskcache

    _DISKCACHE_AVAILABLE = True
except ImportError:
    _DISKCACHE_AVAILABLE = False

try:
    from cachetools import TTLCache
except ImportError:  # pragma: no cover
    TTLCache = None  # type: ignore[misc,assignment]


class CacheEntry:
    """A cache entry."""

    def __init__(self, key: str, value: Any, ttl: int | None = None) -> None:
        self.key = key
        self.value = value
        self.ttl = ttl


class _L2Wrapper:
    """Thin wrapper around diskcache.Cache that mirrors the API used by MultiLevelCache."""

    def __init__(self, directory: Path, ttl: int) -> None:
        self._cache: diskcache.Cache = diskcache.Cache(str(directory))
        self._ttl = ttl

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expire = ttl if ttl is not None else self._ttl
        self._cache.set(key, value, expire=expire if expire else None)

    def delete(self, key: str) -> None:
        self._cache.delete(key)

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def close(self) -> None:
        self._cache.close()


class MultiLevelCache:
    """Multi-level cache with L1 (TTL memory) and optional L2 (diskcache disk) tiers.

    On a cache miss in L1 the lookup falls through to L2 (if available).
    A successful L2 hit promotes the value back to L1 (read-through promotion).
    Writes are always write-through: both L1 and L2 are updated on `set`.
    """

    def __init__(
        self,
        l1_maxsize: int = 256,
        l1_ttl: float = 300,
        l2_dir: Path | str | None = None,
        l2_ttl: int = 3600,
    ) -> None:
        self._l1_lock = threading.Lock()
        if TTLCache is not None:
            self._l1: TTLCache = TTLCache(maxsize=l1_maxsize, ttl=l1_ttl)
        else:  # pragma: no cover
            self._l1 = {}  # type: ignore[assignment]

        self._l2: _L2Wrapper | None = None
        self.l2_available: bool = False
        self.l2_init_status: dict[str, Any] = {"ok": True}

        if l2_dir is not None:
            self._init_l2(Path(l2_dir), l2_ttl)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_l2(self, directory: Path, ttl: int) -> None:
        if not _DISKCACHE_AVAILABLE:
            self.l2_available = False
            self.l2_init_status = {"ok": False, "reason": "diskcache_unavailable"}
            return
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as exc:
            self.l2_available = False
            self.l2_init_status = {
                "ok": False,
                "reason": "directory_error",
                "detail": str(exc),
            }
            return
        if not directory.is_dir():
            self.l2_available = False
            self.l2_init_status = {
                "ok": False,
                "reason": "directory_error",
                "detail": "path is not a directory",
            }
            return
        try:
            self._l2 = _L2Wrapper(directory, ttl)
            self.l2_available = True
            self.l2_init_status = {"ok": True}
        except Exception as exc:  # noqa: BLE001
            self.l2_available = False
            self.l2_init_status = {
                "ok": False,
                "reason": "open_failed",
                "detail": str(exc),
            }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any | None:
        """Get value from cache, checking L1 then L2.

        On L2 hit the value is promoted to L1.
        """
        with self._l1_lock:
            if key in self._l1:
                return self._l1[key]

        if self._l2 is not None:
            value = self._l2.get(key)
            if value is not None:
                with self._l1_lock:
                    self._l1[key] = value
                return value

        return None

    def set(self, key: str, value: Any, ttl: int | None = None, level: int = 1) -> None:
        """Write-through set: stores in both L1 and L2 (if available)."""
        with self._l1_lock:
            self._l1[key] = value
        if self._l2 is not None:
            self._l2.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        """Delete from all cache levels."""
        with self._l1_lock:
            self._l1.pop(key, None)
        if self._l2 is not None:
            self._l2.delete(key)

    def clear(self, level: int | None = None) -> None:
        """Clear cache (both levels by default)."""
        if level is None or level <= 1:
            with self._l1_lock:
                self._l1.clear()
        if (level is None or level > 1) and self._l2 is not None:
            self._l2.clear()

    def stats(self) -> dict[str, Any]:
        """Return basic size statistics for each tier."""
        with self._l1_lock:
            l1_size = len(self._l1)
        l2_size = len(self._l2) if self._l2 is not None else 0
        return {"l1_size": l1_size, "l2_size": l2_size}

    def close(self) -> None:
        """Close L2 backing store if open."""
        if self._l2 is not None:
            self._l2.close()
            self._l2 = None
            self.l2_available = False


def cached_multi(cache: MultiLevelCache) -> Any:
    """Decorator that caches a function's return value in a MultiLevelCache.

    - Unhashable arguments bypass the cache (the function is called normally).
    - ``None`` return values are not cached.
    - The wrapped function exposes a ``.cache`` attribute pointing to the cache.
    """

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Verify args/kwargs are hashable before building a cache key
                hash(args)
                hash(tuple(sorted(kwargs.items())))
                key = str((func.__qualname__, args, tuple(sorted(kwargs.items()))))
            except TypeError:
                return func(*args, **kwargs)

            cached = cache.get(key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            if result is not None:
                cache.set(key, result)
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator


__all__ = ["CacheEntry", "MultiLevelCache", "_DISKCACHE_AVAILABLE", "cached_multi"]
