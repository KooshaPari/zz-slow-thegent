"""Stub module."""

from __future__ import annotations

__all__ = ["ResearchItem"]


class ResearchItem:
    """Placeholder for research item."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize research item."""
        self.kwargs = kwargs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.kwargs
