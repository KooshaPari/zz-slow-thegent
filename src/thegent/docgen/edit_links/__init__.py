"""Stub module."""

from dataclasses import dataclass


@dataclass
class EditLinkGenerator:
    """Generator for edit links."""

    def generate(self, file_path: str, line: int) -> str:
        """Generate an edit link for a file and line."""
        return f"edit:{file_path}:{line}"


__all__ = ["EditLinkGenerator"]
