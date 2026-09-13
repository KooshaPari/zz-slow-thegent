"""Zmx session module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ZmxSessionConfig:
    """Configuration for ZmxSession."""
    session_id: str = ""
    timeout: int = 30
    options: dict[str, Any] | None = None


class ZmxSessionManager:
    """Manager for Zmx sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Any] = {}

    def create_session(self, config: ZmxSessionConfig) -> str:
        """Create a new session."""
        session_id = config.session_id or f"session-{len(self._sessions)}"
        self._sessions[session_id] = {"id": session_id, "config": config}
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions."""
        return list(self._sessions.values())

    def close_session(self, session_id: str) -> bool:
        """Close a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


__all__ = ["ZmxSessionConfig", "ZmxSessionManager", "make_zmx_session_manager"]


def make_zmx_session_manager() -> ZmxSessionManager:
    """Factory function to create a ZmxSessionManager."""
    return ZmxSessionManager()
