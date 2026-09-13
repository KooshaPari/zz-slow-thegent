"""Research engine store module."""

from __future__ import annotations


class ResearchStore:
    """Store for research data."""

    def __init__(self) -> None:
        """Initialize the store."""
        self.data: dict[str, Any] = {}

    def save(self, key: str, value: Any) -> None:
        """Save data to store."""
        self.data[key] = value

    def get(self, key: str) -> Any | None:
        """Get data from store."""
        return self.data.get(key)


__all__ = ["ResearchStore"]
