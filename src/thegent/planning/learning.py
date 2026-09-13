"""STUB MODULE - thegent.planning.learning

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any


class LearningRegistry:
    """Registry for learning data."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def register(self, key: str, value: Any) -> None:
        """Register a learning entry."""
        self.entries.append({"key": key, "value": value})

    def get(self, key: str) -> Any | None:
        """Get a learning entry by key."""
        for entry in self.entries:
            if entry["key"] == key:
                return entry["value"]
        return None


# Stub implementation - functionality not available
__all__ = ["LearningRegistry"]
