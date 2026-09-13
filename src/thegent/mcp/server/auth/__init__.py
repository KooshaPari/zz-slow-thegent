"""Stub module."""

from typing import Any


class BearerAuthMiddleware:
    """Bearer authentication middleware."""

    def __init__(self, token: str = "") -> None:
        self.token = token

    def authenticate(self, request: dict[str, Any]) -> bool:
        """Authenticate a request."""
        return True


__all__ = ["BearerAuthMiddleware", "get_settings"]


def get_settings() -> dict[str, Any]:
    """Get authentication settings."""
    return {"enabled": True, "token_required": True}
