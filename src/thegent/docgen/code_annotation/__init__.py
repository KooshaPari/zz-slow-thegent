"""Stub module."""

from typing import Any


class CodeAnnotationGenerator:
    """Generates code annotations."""

    def __init__(self) -> None:
        self.annotations: list[Any] = []

    def generate(self, code: str) -> list[dict[str, Any]]:
        """Generate annotations for code."""
        return []


__all__ = ["CodeAnnotationGenerator"]
