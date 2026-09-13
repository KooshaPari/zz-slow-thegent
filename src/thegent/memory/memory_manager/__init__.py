"""Stub module."""

from typing import Any


class MemoryManager:
    """Manager for memory operations."""

    def __init__(self) -> None:
        self.memories: dict[str, Any] = {}

    def store(self, key: str, value: Any) -> None:
        """Store a memory."""
        self.memories[key] = value

    def retrieve(self, key: str) -> Any | None:
        """Retrieve a memory."""
        return self.memories.get(key)


__all__ = ["MemoryManager"]
