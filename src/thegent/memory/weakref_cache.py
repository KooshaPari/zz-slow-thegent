"""Weak-reference cache and cleanup helpers.

The cockpit and progress emitter keep small in-memory caches of
event/decision objects. Over a long-running operator session these
caches can grow if callers forget to drop references. The helpers
here provide:

* :class:`WeakrefCache` — a thread-safe ``key -> value`` cache that
  holds values via :class:`weakref.ref` so callers can drop the
  strong reference and the entry becomes collectable.
* :func:`register_finalizer` — utility for attaching a finalizer
  callback to an object that runs when the referent is garbage
  collected. Useful for "fire and forget" log lines or audit hooks.
* :func:`cleanup_weakrefs` — context manager that on exit empties
  the supplied weakref containers and runs their finalizers.

**Traces to**: L19 Memory (audit scorecard), WP-4030 (resource hygiene).
"""

from __future__ import annotations

import weakref
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from threading import RLock
from typing import Any, TypeVar

_K = TypeVar("_K")
_V = TypeVar("_V")


class WeakrefCache[K, V]:
    """Thread-safe ``key -> weakref(value)`` cache.

    ``set`` keeps a strong reference to ``value`` via :class:`weakref.ref`
    so the entry becomes eligible for collection as soon as the caller
    drops its reference. ``get`` returns the live value (or ``None`` if
    the referent has been collected) and prunes the dead entry on the
    fly.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[_K, weakref.ref[_V]] = {}

    def set(self, key: _K, value: _V) -> None:
        """Insert ``value`` under ``key``. ``value`` must be weakly referenceable."""
        with self._lock:
            self._entries[key] = weakref.ref(value)

    def get(self, key: _K) -> _V | None:
        """Return the live value for ``key`` or ``None`` if missing/collected."""
        ref = self._entries.get(key)
        if ref is None:
            return None
        value = ref()
        if value is None:
            # Stale entry — prune to keep the cache bounded.
            with self._lock:
                self._entries.pop(key, None)
            return None
        return value

    def pop(self, key: _K) -> _V | None:
        """Return and remove the entry under ``key``."""
        with self._lock:
            ref = self._entries.pop(key, None)
        if ref is None:
            return None
        return ref()

    def clear(self) -> None:
        """Drop all entries without running finalizers."""
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def __contains__(self, key: _K) -> bool:
        with self._lock:
            return key in self._entries

    def __iter__(self) -> Iterator[_K]:
        with self._lock:
            return iter(list(self._entries.keys()))


def register_finalizer(
    obj: Any,
    callback: Callable[[Any], None],
    *,
    args: tuple[Any, ...] = (),
) -> weakref.finalize:
    """Attach a finalizer to ``obj`` that runs ``callback`` on collection.

    The returned :class:`weakref.finalize` can be detached by
    :func:`weakref.finalize.detach` if the caller needs to cancel it.
    """
    return weakref.finalize(obj, callback, *args)


@contextmanager
def cleanup_weakrefs(
    *containers: Iterable[Any],
) -> Iterator[None]:
    """Context manager that clears ``containers`` on exit.

    Each container is expected to expose ``.clear()``. The intent is
    to wrap long-lived loops in tests / CLIs so that intermediate
    state is released promptly after the block ends.
    """
    try:
        yield
    finally:
        for container in containers:
            clear = getattr(container, "clear", None)
            if callable(clear):
                clear()


__all__ = [
    "WeakrefCache",
    "cleanup_weakrefs",
    "register_finalizer",
]
