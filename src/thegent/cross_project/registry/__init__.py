"""Stub module."""

from typing import Any


class CrossProjectRegistry:
    """Registry for cross-project resources."""

    def __init__(self) -> None:
        self._entries: dict[str, Any] = {}

    def register(self, key: str, value: Any) -> None:
        """Register an entry."""
        self._entries[key] = value

    def get(self, key: str) -> Any | None:
        """Get an entry."""
        return self._entries.get(key)


__all__ = ["CrossProjectRegistry"]
