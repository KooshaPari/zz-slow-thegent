"""Stub module."""

from typing import Any


class WorkStreamManager:
    """Work stream manager stub."""

    def __init__(self) -> None:
        self.streams: dict[str, Any] = {}

    def create(self, name: str) -> str:
        return name


__all__ = ["WorkStreamManager"]
