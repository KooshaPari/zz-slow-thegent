"""Watcher daemon module for file system watching."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WatchEvent(Enum):
    """Watch event types."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class WatcherDaemon:
    """Watcher daemon for file system watching."""

    _instance: WatcherDaemon | None = None

    def __new__(cls, config: dict[str, Any] | None = None) -> WatcherDaemon:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.config = config or {}
        self.running = False
        self._initialized = True

    def start(self) -> None:
        """Start the watcher daemon."""
        self.running = True

    def stop(self) -> None:
        """Stop the watcher daemon."""
        self.running = False

    def watch(self, path: str, callback: Any = None) -> WatchSpec:
        """Register a watch on a path."""
        return WatchSpec(path=path, recursive=False)


def _reset_singleton() -> None:
    """Reset the singleton instance (for testing)."""
    WatcherDaemon._instance = None


class _SpecHandler:
    """Internal handler for watch specifications."""

    def __init__(self, spec: WatchSpec) -> None:
        self.spec = spec
        self.active = False

    def activate(self) -> None:
        """Activate this handler."""
        self.active = True

    def deactivate(self) -> None:
        """Deactivate this handler."""
        self.active = False


def _try_get_breaker(circuit_name: str) -> Any:
    """Try to get a circuit breaker by name."""
    return None


def get_watcher_daemon() -> WatcherDaemon:
    """Get the global watcher daemon instance."""
    return WatcherDaemon()


__all__ = ["WatcherDaemon", "WatchEvent", "WatchSpec", "_reset_singleton", "_SpecHandler", "_try_get_breaker", "get_watcher_daemon"]


@dataclass
class WatchSpec:
    """Specification for a watch operation."""
    path: str
    recursive: bool = False
    patterns: list[str] = field(default_factory=list)
