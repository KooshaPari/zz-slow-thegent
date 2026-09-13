"""Redlock-based atomic acquire/release (dormant SOTA pass-22 hardening).

@trace FR-ORC-003 (swarm-redlock-atomic)
@trace FR-ORC-CON-060 .. FR-ORC-CON-074 (dormant hardening invariants)

The controller operates in one of two modes:

* **Redis mode** — at least one node in ``_clients`` answered a successful
  ``PING``; acquire uses ``SET key value NX PX ttl_ms`` on every node and
  declares success when a *quorum* (majority, rounded up) of the nodes
  returns a truthy result.  Release / extend use a Lua ``GET+DEL`` /
  ``GET+PEXPIRE`` script so only the original owner can release or extend.

* **Fallback mode** — the ``redis`` module is not importable or no node
  answered ``PING``; acquire falls back to a single in-process
  ``_InMemoryLockState`` (thread-safe, TTL-aware).  This keeps the
  pipeline unblocked when Redis is unavailable while preserving
  correctness for in-process consumers.
"""

from __future__ import annotations

import contextlib
import os
import time
import uuid
from dataclasses import dataclass
from threading import RLock
from typing import Any

__all__ = [
    "RedlockAcquireResult",
    "RedlockAtomic",
    "RedlockController",
    "_InMemoryLockState",
    "_parse_node_urls_from_env",
    "_parse_redis_url",
    "_import_redis_sync",
    "make_redlock_controller",
]


# Lua scripts — only the original owner may release / extend.
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

_EXTEND_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('pexpire', KEYS[1], ARGV[2])
else
    return 0
end
"""


def _import_redis_sync():
    """Import the synchronous ``redis`` module, returning ``None`` if unavailable.

    The factory / constructor patches this symbol in tests so the
    controller can be forced into fallback mode without monkey-patching
    ``redis`` itself.
    """
    try:
        import redis as _redis_sync  # type: ignore[import-not-found]

        return _redis_sync
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# RedlockAcquireResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RedlockAcquireResult:
    """Immutable result of a Redlock acquire attempt.

    Attributes:
        acquired: ``True`` when quorum was achieved (Redis mode) or the
            in-process lock was free (fallback mode).
        lock_id: Unique token identifying this acquire.  Empty string
            when ``acquired=False``.  Pass back to ``release()`` /
            ``extend()`` to prove ownership.
        expires_at: Monotonic timestamp at which the lock expires.
            ``0.0`` when ``acquired=False``.
    """

    acquired: bool
    lock_id: str = ""
    expires_at: float = 0.0


# ---------------------------------------------------------------------------
# _InMemoryLockState — TTL-aware in-process lock
# ---------------------------------------------------------------------------


class _InMemoryLockState:
    """In-process lock state with TTL expiry.  Thread-safe via ``RLock``."""

    def __init__(self) -> None:
        self._lock_id: str | None = None
        self._expires_at: float = 0.0
        self._lock = RLock()

    def acquire(self, lock_id: str, ttl_ms: int) -> bool:
        """Acquire the in-process lock if it is free or expired.

        Args:
            lock_id: Unique identifier supplied by the caller.
            ttl_ms: Time-to-live in milliseconds.

        Returns:
            ``True`` if the lock was acquired; ``False`` if a non-expired
            lock is already held by another owner.
        """
        with self._lock:
            now = time.monotonic()
            if self._lock_id is not None and now < self._expires_at:
                return False
            self._lock_id = lock_id
            self._expires_at = now + ttl_ms / 1000.0
            return True

    def release(self, lock_id: str) -> bool:
        """Release the in-process lock if ``lock_id`` matches the active owner."""
        with self._lock:
            now = time.monotonic()
            if self._lock_id is None or now >= self._expires_at:
                self._lock_id = None
                self._expires_at = 0.0
                return False
            if self._lock_id != lock_id:
                return False
            self._lock_id = None
            self._expires_at = 0.0
            return True

    def extend(self, lock_id: str, ttl_ms: int) -> bool:
        """Extend the active lock's TTL if ``lock_id`` matches the owner."""
        with self._lock:
            now = time.monotonic()
            if self._lock_id is None or now >= self._expires_at or self._lock_id != lock_id:
                return False
            self._expires_at = now + ttl_ms / 1000.0
            return True

    def is_locked(self) -> bool:
        """Return ``True`` when the in-process lock is currently held."""
        with self._lock:
            return self._lock_id is not None and time.monotonic() < self._expires_at


# ---------------------------------------------------------------------------
# URL / env helpers
# ---------------------------------------------------------------------------


def _parse_redis_url(url: str) -> dict[str, Any]:
    """Parse a ``redis://`` URL into host/port/db[/password] components.

    The returned dictionary only carries a ``"password"`` key when the URL
    embeds ``:password@``; callers can therefore test for the presence of
    an auth secret with ``"password" in kw``.
    """
    result: dict[str, Any] = {"host": "localhost", "port": 6379, "db": 0}
    if url.startswith("redis://"):
        remainder = url[len("redis://") :]
        if "@" in remainder:
            auth, remainder = remainder.split("@", 1)
            if ":" in auth:
                result["password"] = auth.split(":", 1)[1]
        if "/" in remainder:
            host_port, db = remainder.rsplit("/", 1)
            with contextlib.suppress(ValueError):
                result["db"] = int(db)
            remainder = host_port
        if ":" in remainder:
            host, port = remainder.split(":", 1)
            result["host"] = host
            with contextlib.suppress(ValueError):
                result["port"] = int(port)
        else:
            result["host"] = remainder
    return result


def _parse_node_urls_from_env() -> list[str]:
    """Return the list of Redlock node URLs from ``THGENT_REDLOCK_NODES``.

    Empty / unset env var → ``["redis://localhost:6379"]``.  Whitespace is
    stripped and empty entries are dropped so callers can use a
    comma-separated list with optional spaces.
    """
    env_val = os.environ.get("THGENT_REDLOCK_NODES", "")
    if not env_val:
        return ["redis://localhost:6379"]
    return [url.strip() for url in env_val.split(",") if url.strip()]


# ---------------------------------------------------------------------------
# RedlockController — quorum acquire / release / extend
# ---------------------------------------------------------------------------


class RedlockController:
    """Controller for Redlock distributed locking.

    The controller is constructed by attempting to import the ``redis``
    package and pinging each ``redis_nodes`` URL.  When the import fails
    or no node responds, the controller falls back to a single
    in-process ``_InMemoryLockState``.

    Attributes:
        _fallback: In-process lock used when no Redis node is reachable.
        _clients: Connected Redis client handles (empty in fallback mode).
        _redis_available: ``True`` when at least one Redis node is connected.
        _ttl_ms: Default lock TTL in milliseconds.
        _nodes_urls: Configured Redis node URLs.
        _lock: ``RLock`` guarding mode transitions.
        _active_lock_id: The ``lock_id`` of the currently held lock, or
            ``None`` when no lock is held.
    """

    def __init__(self, key: str, ttl_ms: int = 30000, redis_nodes: list[str] | None = None) -> None:
        self._key = key
        self._ttl_ms = ttl_ms
        self._nodes_urls = list(redis_nodes) if redis_nodes else _parse_node_urls_from_env()
        self._fallback: _InMemoryLockState | None = None
        self._clients: list[Any] = []
        self._redis_available = False
        self._active_lock_id: str | None = None
        self._lock = RLock()
        self._connect()

    # -- mode detection ------------------------------------------------------

    def _connect(self) -> None:
        """Attempt to connect to each configured Redis node."""
        redis_sync = _import_redis_sync()
        if redis_sync is None:
            self._fallback = _InMemoryLockState()
            return
        clients: list[Any] = []
        for url in self._nodes_urls:
            try:
                client = redis_sync.Redis.from_url(url, socket_connect_timeout=0.5)
                if client.ping():
                    clients.append(client)
            except Exception:  # noqa: BLE001 — any Redis client failure falls back.
                continue
        if not clients:
            self._fallback = _InMemoryLockState()
            return
        self._clients = clients
        self._redis_available = True

    def is_available(self) -> bool:
        """Return ``True`` when at least one Redis client is connected."""
        return self._redis_available

    # -- acquire -------------------------------------------------------------

    def acquire(self) -> RedlockAcquireResult:
        """Attempt to acquire the lock under quorum semantics.

        Returns a frozen ``RedlockAcquireResult`` whose ``acquired`` flag
        reflects whether quorum was achieved (Redis mode) or the
        in-process lock was free (fallback mode).
        """
        lock_id = uuid.uuid4().hex
        with self._lock:
            if not self._redis_available:
                assert self._fallback is not None
                if self._fallback.acquire(lock_id, self._ttl_ms):
                    self._active_lock_id = lock_id
                    return RedlockAcquireResult(
                        acquired=True,
                        lock_id=lock_id,
                        expires_at=time.monotonic() + self._ttl_ms / 1000.0,
                    )
                return RedlockAcquireResult(acquired=False)
            successes = 0
            for client in self._clients:
                try:
                    ok = client.set(self._key, lock_id, nx=True, px=self._ttl_ms)
                except Exception:  # noqa: BLE001
                    ok = False
                if ok:
                    successes += 1
            quorum = (len(self._clients) // 2) + 1
            if successes >= quorum:
                self._active_lock_id = lock_id
                return RedlockAcquireResult(
                    acquired=True,
                    lock_id=lock_id,
                    expires_at=time.monotonic() + self._ttl_ms / 1000.0,
                )
            return RedlockAcquireResult(acquired=False)

    # -- release -------------------------------------------------------------

    def release(self, lock_id: str) -> bool:
        """Release the lock if ``lock_id`` matches the active owner."""
        with self._lock:
            if not self._redis_available:
                assert self._fallback is not None
                return self._fallback.release(lock_id)
            released = False
            for client in self._clients:
                try:
                    result = client.eval(_RELEASE_SCRIPT, 1, self._key, lock_id)
                except Exception:  # noqa: BLE001
                    continue
                if result:
                    released = True
            if released:
                self._active_lock_id = None
            return released

    # -- extend --------------------------------------------------------------

    def extend(self, lock_id: str, ttl_ms: int) -> bool:
        """Extend the active lock's TTL if ``lock_id`` matches the owner."""
        with self._lock:
            if not self._redis_available:
                assert self._fallback is not None
                return self._fallback.extend(lock_id, ttl_ms)
            extended = False
            for client in self._clients:
                try:
                    result = client.eval(_EXTEND_SCRIPT, 1, self._key, lock_id, ttl_ms)
                except Exception:  # noqa: BLE001
                    continue
                if result:
                    extended = True
            return extended

    # -- is_locked -----------------------------------------------------------

    def is_locked(self) -> bool:
        """Return ``True`` when the controller currently holds any lock."""
        with self._lock:
            if not self._redis_available:
                assert self._fallback is not None
                return self._fallback.is_locked()
            for client in self._clients:
                try:
                    if client.exists(self._key):
                        return True
                except Exception:  # noqa: BLE001
                    continue
            return False


# ---------------------------------------------------------------------------
# Legacy / back-compat surface
# ---------------------------------------------------------------------------


class RedlockAtomic:
    """Legacy in-memory lock surface retained for dormant callers."""

    def __init__(self) -> None:
        self.locks: dict[str, bool] = {}

    def acquire(self, key: str, ttl_ms: int = 30000) -> RedlockAcquireResult:
        self.locks[key] = True
        return RedlockAcquireResult(
            acquired=True,
            lock_id=key,
            expires_at=time.monotonic() + ttl_ms / 1000.0,
        )

    def release(self, key: str) -> bool:
        if key in self.locks:
            del self.locks[key]
            return True
        return False


def make_redlock_controller(
    key: str,
    ttl_ms: int = 30000,
    redis_nodes: list[str] | None = None,
) -> RedlockController:
    """Factory: build a ``RedlockController`` honouring ``_import_redis_sync`` patches.

    Tests patch ``thegent.orchestration.redlock_atomic._import_redis_sync``
    to ``return None`` so this factory falls back to in-process mode
    without monkey-patching the ``redis`` package itself.
    """
    return RedlockController(key=key, ttl_ms=ttl_ms, redis_nodes=redis_nodes)
