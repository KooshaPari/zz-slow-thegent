"""Stub module."""

from typing import TYPE_CHECKING, Any


class TeamCoordinator:
    """Team coordinator stub."""

    def __init__(self) -> None:
        self.members: list[str] = []

    def coordinate(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"coordinated": True}


__all__ = ["TeamCoordinator"]
