"""Indexer - STUB."""

from typing import Any


class Indexer:
    def __init__(self, *args, **kwargs):
        pass

    def index(self, doc, *args, **kwargs):
        pass

    def search(self, query, *args, **kwargs) -> list[dict[str, Any]]:
        return []


__all__ = ["Indexer", "DocIndexer"]

# Alias for backwards compatibility
DocIndexer = Indexer
