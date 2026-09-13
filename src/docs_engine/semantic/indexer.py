"""Semantic indexer - STUB."""

from typing import Any


class SemanticIndexer:
    def __init__(self, *args, **kwargs):
        pass

    def index(self, text, *args, **kwargs):
        pass

    def search(self, query, *args, **kwargs) -> list[dict[str, Any]]:
        return []


__all__ = ["SemanticIndexer"]
