"""Session hook - STUB."""

from __future__ import annotations

from typing import Any


class SessionHook:
    def __init__(self, *args, **kwargs):
        pass

    def on_session_start(self, *args, **kwargs):
        pass

    def on_session_end(self, *args, **kwargs):
        pass


def write_conversation_dump(session_id: str, data: dict[str, Any]) -> bool:
    """Write a conversation dump for a session."""
    return True


__all__ = ["SessionHook", "write_conversation_dump"]
