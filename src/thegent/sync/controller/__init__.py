"""Stub module."""

from typing import TYPE_CHECKING, Any


class SyncController:
    """Sync controller stub."""

    def __init__(self) -> None:
        self.syncing = False

    def sync(self) -> dict[str, Any]:
        return {"synced": True}


__all__ = ["SyncController"]
