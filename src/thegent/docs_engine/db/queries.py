"""Stub module."""

from __future__ import annotations


class QueryBuilder:
    """Query builder for docs_engine."""

    def __init__(self) -> None:
        self._conditions: list[str] = []

    def where(self, condition: str) -> QueryBuilder:
        self._conditions.append(condition)
        return self

    def execute(self) -> list[dict]:
        return []


__all__ = ["QueryBuilder"]
