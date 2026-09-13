"""Stub module."""

from dataclasses import dataclass


@dataclass
class MemoryEntry:
    """A memory entry."""

    key: str
    value: str
    timestamp: float = 0.0


__all__ = [
    "MemoryEntry",
    "SupermemoryConfigError",
    "SupermemoryAPIError",
    "SupermemoryClient",
    "_is_retryable",
]


class SupermemoryClient:
    """Client for Supermemory operations."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key
        self._entries: list[MemoryEntry] = []

    def store(self, key: str, value: str) -> None:
        """Store a memory entry."""
        self._entries.append(MemoryEntry(key=key, value=value, timestamp=0.0))

    def retrieve(self, key: str) -> str | None:
        """Retrieve a memory entry by key."""
        for entry in self._entries:
            if entry.key == key:
                return entry.value
        return None


class SupermemoryConfigError(Exception):
    """Exception raised for Supermemory configuration errors."""


class SupermemoryAPIError(Exception):
    """Exception raised for Supermemory API errors."""


def _is_retryable(exception: Exception) -> bool:
    """Check if an exception is retryable."""
    return isinstance(exception, SupermemoryAPIError)
