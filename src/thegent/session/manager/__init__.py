"""Stub module."""

from typing import Any


class InvalidTurnIndexError(Exception):
    """Exception raised when an invalid turn index is provided."""

    def __init__(self, index: int) -> None:
        super().__init__(f"Invalid turn index: {index}")
        self.index = index


__all__ = [
    "InvalidTurnIndexError",
    "RollbackOutOfRangeError",
    "SessionAlreadyExistsError",
    "SessionManager",
]


class SessionManager:
    """Session manager for agent sessions."""

    def __init__(self) -> None:
        self.sessions: dict[str, Any] = {}

    def create(self, session_id: str) -> None:
        """Create a new session."""
        if session_id in self.sessions:
            raise SessionAlreadyExistsError(session_id)
        self.sessions[session_id] = {}

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Get a session by ID."""
        return self.sessions.get(session_id)


class SessionAlreadyExistsError(Exception):
    """Exception raised when a session already exists."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session already exists: {session_id}")
        self.session_id = session_id


class RollbackOutOfRangeError(Exception):
    """Exception raised when rollback is out of range."""

    def __init__(self, requested: int, available: int) -> None:
        super().__init__(f"Rollback {requested} out of range, available: {available}")
        self.requested = requested
        self.available = available
