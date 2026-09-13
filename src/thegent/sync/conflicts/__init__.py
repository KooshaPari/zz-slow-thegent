"""Stub module."""

from typing import Any


class SyncConflict:
    """Represents a sync conflict."""

    def __init__(self, key: str, local: Any, remote: Any) -> None:
        self.key = key
        self.local = local
        self.remote = remote

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "local": self.local, "remote": self.remote}


def recommend_action(conflict: SyncConflict) -> str:
    """Recommend an action to resolve a sync conflict."""
    return "use_local"  # Default recommendation


__all__ = ["SyncConflict", "recommend_action", "render_conflict_surface"]


def render_conflict_surface(conflict: SyncConflict) -> str:
    """Render a conflict as a visual surface representation."""
    return f"Conflict: {conflict.key}"
