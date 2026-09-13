"""Research engine schema definitions."""

from __future__ import annotations

from typing import Any


class ResearchSchema:
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, data, *args, **kwargs) -> bool:
        return True


class ResearchItem:
    """Represents a research item."""

    def __init__(self, title: str = "", url: str = "", content: str = "") -> None:
        """Initialize research item."""
        self.title = title
        self.url = url
        self.content = content
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "metadata": self.metadata,
        }


__all__ = ["ResearchSchema", "ResearchItem"]
