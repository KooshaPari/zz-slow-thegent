import contextlib
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

# Library-first (LIBRARY_FIRST_POLICY.md): Using cachetools.TTLCache for in-memory caching
from cachetools import TTLCache

_log = logging.getLogger(__name__)


class ResourceCache:
    """WP-DX-023: Simple ETag-based caching for FastMCP resources.

    Hybrid caching strategy:
    - In-memory: TTLCache for fast access (cachetools handles TTL automatically)
    - File-based: Persistent storage across sessions (manual JSON file I/O)
    - ETag: Change detection for cache invalidation
    """

    def __init__(self, cache_dir: Path, ttl_seconds: int = 60, max_memory_items: int = 50) -> None:
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        # Library-first (LIBRARY_FIRST_POLICY.md): In-memory TTL cache for frequently accessed items
        self.memory_cache: TTLCache[str, Any] = TTLCache(maxsize=max_memory_items, ttl=ttl_seconds)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        hashed = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed}.json"

    def get(self, key: str) -> Any | None:
        # Check in-memory cache first (cachetools handles TTL automatically)
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Fall back to file-based cache
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Library-first (LIBRARY_FIRST_POLICY.md): Manual TTL check for file layer only
            if time.time() - data.get("timestamp", 0) > self.ttl_seconds:
                return None
            payload = data.get("payload")
            # Promote to in-memory cache (cachetools handles eviction)
            if payload is not None:
                self.memory_cache[key] = payload
            return payload
        except Exception:
            return None

    def set(self, key: str, payload: Any) -> str:
        data = {
            "timestamp": time.time(),
            "payload": payload,
            "etag": hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest(),
        }
        # Write to file (persistent storage)
        path = self._get_path(key)
        path.write_text(json.dumps(data), encoding="utf-8")
        # Update in-memory cache (cachetools handles eviction and TTL)
        self.memory_cache[key] = payload
        return data["etag"]

    def clear(self) -> None:
        """Clear both in-memory and file-based cache."""
        self.memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            with contextlib.suppress(Exception):
                cache_file.unlink()

    def enable_invalidation(self, directory: Path) -> None:
        """Enable real-time cache invalidation based on file changes (TGNT-P9.2)."""
        from thegent.infra.cache_v2 import CacheInvalidator

        self.invalidator = CacheInvalidator(self)
        self.invalidator.watch(directory)
        _log.info(f"Real-time cache invalidation enabled for {directory}")
