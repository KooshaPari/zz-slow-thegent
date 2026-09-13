"""Stub module."""

from __future__ import annotations


class SubUserProvider:
    """Provider for sub-users."""

    def __init__(self) -> None:
        self._users: dict = {}

    def get_user(self, user_id: str) -> dict | None:
        return self._users.get(user_id)


class SubUserIsolationProvider:
    """Provider for sub-user isolation."""

    def __init__(self) -> None:
        self._isolations: dict = {}

    def isolate(self, user_id: str, config: dict) -> bool:
        """Isolate a sub-user."""
        self._isolations[user_id] = config
        return True

    def get_isolation(self, user_id: str) -> dict | None:
        """Get isolation config for a user."""
        return self._isolations.get(user_id)


__all__ = ["SubUserProvider", "SubUserIsolationProvider"]
