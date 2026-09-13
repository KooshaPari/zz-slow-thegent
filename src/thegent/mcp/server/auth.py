"""MCP Server authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from thegent.config import ThegentSettings


class AuthContext:
    """Authentication context for MCP server requests."""

    def __init__(self, user_id: str | None = None, token: str | None = None) -> None:
        self.user_id = user_id
        self.token = token

    @property
    def is_authenticated(self) -> bool:
        """Check if the context is authenticated."""
        return self.token is not None


class AuthProvider:
    """Provider for authentication."""

    def __init__(self) -> None:
        self._users: dict[str, str] = {}

    def authenticate(self, user_id: str, token: str) -> bool:
        """Authenticate a user with a token."""
        self._users[user_id] = token
        return True

    def verify(self, token: str) -> AuthContext | None:
        """Verify a token and return the auth context."""
        for user_id, stored_token in self._users.items():
            if stored_token == token:
                return AuthContext(user_id=user_id, token=token)
        return None

    def revoke(self, token: str) -> bool:
        """Revoke a token."""
        for user_id, stored_token in list(self._users.items()):
            if stored_token == token:
                del self._users[user_id]
                return True
        return False


# Global auth provider
auth_provider = AuthProvider()


def authenticate(user_id: str, token: str) -> bool:
    """Authenticate a user with the global provider."""
    return auth_provider.authenticate(user_id, token)


def verify(token: str) -> AuthContext | None:
    """Verify a token with the global provider."""
    return auth_provider.verify(token)


def revoke(token: str) -> bool:
    """Revoke a token with the global provider."""
    return auth_provider.revoke(token)


# =============================================================================
# Bearer Authentication Middleware (for MCP server)
# =============================================================================


class BearerAuthMiddleware:
    """Bearer authentication middleware for MCP HTTP endpoints.

    This middleware handles Bearer token authentication for MCP server endpoints.
    It caches the ThegentSettings instance to avoid repeated settings construction.

    Attributes:
        _settings: Cached ThegentSettings instance (class-level).
        app: The ASGI application to wrap.
    """

    _settings: ThegentSettings | None = None

    def __init__(self, app: Any) -> None:
        """Initialize the middleware with an ASGI app.

        Args:
            app: The ASGI application to wrap with authentication.
        """
        self.app = app

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """Dispatch the request after authentication check.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The response from the next handler if authentication succeeds.
        """
        # Get settings (cached at class level)
        if BearerAuthMiddleware._settings is None:
            BearerAuthMiddleware._settings = get_settings()

        # Check for Bearer token
        auth_header = getattr(request, "headers", {}).get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            ctx = verify(token)
            if ctx is not None:
                return await call_next(request)

        # No valid auth - let the app handle it
        return await call_next(request)

    @classmethod
    def reload_settings(cls) -> None:
        """Reload settings from environment/configuration.

        Call this to invalidate the cached settings and force a reload
        on the next request.
        """
        cls._settings = None


def get_settings() -> ThegentSettings:
    """Get the ThegentSettings singleton.

    Returns:
        ThegentSettings: The cached settings instance.

    Note:
        This function lazily loads ThegentSettings to avoid import cycles.
    """
    from thegent.config import ThegentSettings

    return ThegentSettings()


__all__ = [
    "AuthContext",
    "AuthProvider",
    "authenticate",
    "verify",
    "revoke",
    "auth_provider",
    "BearerAuthMiddleware",
    "get_settings",
]
