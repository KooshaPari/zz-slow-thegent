"""Digest for research engine."""

from __future__ import annotations

from typing import Any


class DigestGenerator:
    """Generator for research digests."""

    def __init__(self) -> None:
        self.items: list[Any] = []

    def generate(self) -> dict[str, Any]:
        """Generate a digest."""
        return {"count": len(self.items), "items": self.items}


class ResearchDigest:
    """Digest of research results."""

    def __init__(self) -> None:
        self.items: list[Any] = []

    def add(self, item: Any) -> None:
        self.items.append(item)

    def summarize(self) -> dict[str, Any]:
        return {"count": len(self.items), "items": self.items}


__all__ = ["DigestGenerator", "ResearchDigest"]
