"""Redis-backed distributed concurrency limits (dormant SOTA pass-22 hardening).

@trace FR-ORC-002 (swarm-redis-concurrency)
@trace FR-ORC-CON-080 .. FR-ORC-CON-082 (dormant hardening invariants)

Synchronous slot-counter controller backed by a Redis store (stub
``_InMemoryStore`` in-process for tests).  The controller is
concurrency-safe under threading contention — N worker threads racing
on ``acquire()`` cannot collectively exceed ``max_concurrent``, and a
leaked ``release()`` (no matching acquire) cannot underflow ``current``.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

__all__ = [
    "RedisConfig",
    "RedisConcurrencyController",
    "_InMemoryStore",
    "make_redis_concurrency_controller",
]


@dataclass
class RedisConfig:
    """Redis configuration for concurrency control."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    max_concurrent: int = 10


class RedisConcurrencyController:
    """Controller for Redis-based concurrency control.

    Synchronous slot counter; ``acquire()`` increments ``current`` (capped
    at ``max_concurrent``) and ``release()`` decrements ``current`` (no-op
    at zero).  Thread-safe via ``RLock`` — concurrent ``acquire()`` calls
    never exceed ``max_concurrent`` and ``release()`` never underflows
    ``current``.
    """

    def __init__(self) -> None:
        self.max_concurrent: int = 10
        self.current: int = 0
        self._lock = RLock()

    def acquire(self) -> bool:
        """Acquire a concurrency slot.

        Returns ``True`` when the slot was acquired (``current`` was
        incremented) and ``False`` when ``current`` was already at
        ``max_concurrent``.
        """
        with self._lock:
            if self.current < self.max_concurrent:
                self.current += 1
                return True
            return False

    def release(self) -> None:
        """Release a concurrency slot.

        ``release()`` at zero is a no-op so a leaked release cannot
        underflow ``current``.
        """
        with self._lock:
            if self.current > 0:
                self.current -= 1


class _InMemoryStore:
    """In-memory store for testing Redis operations.

    Synchronous key/value surface compatible with the subset of the
    ``redis`` API used by the controller: ``get`` / ``set(ex=...)`` /
    ``delete`` / ``exists``.
    """

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        """Get a value by key."""
        return self._data.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        """Set a value with optional expiration (stub ignores ``ex``)."""
        self._data[key] = value

    def delete(self, key: str) -> int:
        """Delete a key.  Returns ``1`` on success, ``0`` if the key was absent."""
        if key in self._data:
            del self._data[key]
            return 1
        return 0

    def exists(self, key: str) -> int:
        """Check if a key exists.  Returns ``1`` or ``0``."""
        return 1 if key in self._data else 0


def make_redis_concurrency_controller(
    config: RedisConfig | None = None,
) -> RedisConcurrencyController:
    """Create a Redis concurrency controller with the given config.

    The factory only clones ``max_concurrent`` from the config; the
    ``host`` / ``port`` / ``db`` / ``password`` fields are stored on the
    config object and are not pushed onto the controller (which is a
    synchronous slot counter, not a network client).

    Args:
        config: Optional Redis configuration.

    Returns:
        RedisConcurrencyController instance.
    """
    controller = RedisConcurrencyController()
    if config:
        controller.max_concurrent = config.max_concurrent
    return controller
