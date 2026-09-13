"""STUB MODULE - thegent.indexing

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any


class FileIndex:
    """File index for search operations."""

    def __init__(self) -> None:
        self.files: dict[str, Any] = {}

    def add(self, file_path: str, metadata: dict[str, Any]) -> None:
        """Add a file to the index."""
        self.files[file_path] = metadata

    def search(self, query: str) -> list[str]:
        """Search for files matching a query."""
        return []


# Stub implementation - functionality not available
__all__ = ["FileIndex"]
