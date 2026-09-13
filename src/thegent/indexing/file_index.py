"""Stub module."""

from __future__ import annotations


class FileIndex:
    """File indexing."""

    def __init__(self) -> None:
        self._index: dict = {}

    def add(self, path: str, metadata: dict) -> None:
        self._index[path] = metadata

    def get(self, path: str) -> dict | None:
        return self._index.get(path)


__all__ = ["FileIndex", "_DEFAULT_EXCLUDE_DIRS", "_DEFAULT_TTL"]

_DEFAULT_TTL = 3600  # 1 hour default TTL

_DEFAULT_EXCLUDE_DIRS = [
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]
