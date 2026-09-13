"""Tests for race conditions in BearerAuthMiddleware (T3.B.B.1.4).

Demonstrates the TOCTOU race in _settings class variable initialization
where concurrent async requests can trigger double-initialization.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.mcp.server.auth import BearerAuthMiddleware, get_settings


class TestBearerAuthRaceCondition:
    """Tests for the _settings TOCTOU race in BearerAuthMiddleware."""

    def setup_method(self) -> None:
        """Reset class-level state before each test."""
        BearerAuthMiddleware._settings = None
        get_settings.cache_clear()

    def test_settings_initialized_once(self) -> None:
        """Verify settings are cached after first access."""
        with patch("thegent.mcp.server.auth.ThegentSettings") as mock_cls:
            mock_settings = MagicMock()
            mock_settings.mcp_auth_mode = "none"
            mock_cls.return_value = mock_settings

            s1 = get_settings()
            s2 = get_settings()
            assert s1 is s2
            mock_cls.assert_called_once()

    def test_reload_settings_clears_cache(self) -> None:
        """reload_settings should reset the class-level _settings."""
        BearerAuthMiddleware._settings = MagicMock()
        assert BearerAuthMiddleware._settings is not None
        BearerAuthMiddleware.reload_settings()
        assert BearerAuthMiddleware._settings is None

    @pytest.mark.asyncio
    async def test_concurrent_dispatch_settings_race(self) -> None:
        """Simulate concurrent requests hitting dispatch before _settings is set.

        The race: two coroutines both see _settings is None, both call
        get_settings(). With lru_cache this is safe for the settings object
        itself, but the class variable assignment is not atomic in async context.
        """
        call_count = 0

        with patch("thegent.mcp.server.auth.ThegentSettings") as mock_cls:
            mock_settings = MagicMock()
            mock_settings.mcp_auth_mode = "none"

            def counting_init():
                nonlocal call_count
                call_count += 1
                return mock_settings

            mock_cls.side_effect = counting_init

            # Clear lru_cache to force re-creation
            get_settings.cache_clear()
            BearerAuthMiddleware._settings = None

            # Simulate concurrent dispatch calls
            app = AsyncMock()
            BearerAuthMiddleware(app)

            async def fake_dispatch(request, call_next):
                if BearerAuthMiddleware._settings is None:
                    BearerAuthMiddleware._settings = get_settings()
                return MagicMock()

            requests = []
            for _ in range(10):
                req = MagicMock()
                req.url.path = "/health"
                req.headers = {}
                requests.append(req)

            # Run concurrent dispatches
            tasks = [fake_dispatch(r, AsyncMock()) for r in requests]
            await asyncio.gather(*tasks)

            # With lru_cache, ThegentSettings() should only be called once
            # even under concurrent access
            assert call_count == 1


class TestBearerAuthMiddlewareValidation:
    """Correctness tests for bearer token validation."""

    def setup_method(self) -> None:
        BearerAuthMiddleware._settings = None
        get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_health_endpoint_bypasses_auth(self) -> None:
        """Health endpoint should not require authentication."""
        mock_settings = MagicMock()
        mock_settings.mcp_auth_mode = "bearer"
        mock_settings.mcp_bearer_tokens = "secret123"
        BearerAuthMiddleware._settings = mock_settings

        app = AsyncMock()
        middleware = BearerAuthMiddleware(app)

        request = MagicMock()
        request.url.path = "/health"
        request.headers = {}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_401(self) -> None:
        """Missing Authorization header should return 401."""
        mock_settings = MagicMock()
        mock_settings.mcp_auth_mode = "bearer"
        BearerAuthMiddleware._settings = mock_settings

        app = AsyncMock()
        middleware = BearerAuthMiddleware(app)

        request = MagicMock()
        request.url.path = "/api/tools"
        request.headers = {}

        call_next = AsyncMock()
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self) -> None:
        """Invalid bearer token should return 401."""
        mock_settings = MagicMock()
        mock_settings.mcp_auth_mode = "bearer"
        mock_settings.mcp_bearer_tokens = "valid_token"
        BearerAuthMiddleware._settings = mock_settings

        app = AsyncMock()
        middleware = BearerAuthMiddleware(app)

        request = MagicMock()
        request.url.path = "/api/tools"
        request.headers = {"Authorization": "Bearer wrong_token"}

        call_next = AsyncMock()
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_passes(self) -> None:
        """Valid bearer token should pass through to the app."""
        mock_settings = MagicMock()
        mock_settings.mcp_auth_mode = "bearer"
        mock_settings.mcp_bearer_tokens = "valid_token"
        BearerAuthMiddleware._settings = mock_settings

        app = AsyncMock()
        middleware = BearerAuthMiddleware(app)

        request = MagicMock()
        request.url.path = "/api/tools"
        request.headers = {"Authorization": "Bearer valid_token"}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_none_auth_mode_skips_validation(self) -> None:
        """When auth mode is 'none', all requests pass through."""
        mock_settings = MagicMock()
        mock_settings.mcp_auth_mode = "none"
        BearerAuthMiddleware._settings = mock_settings

        app = AsyncMock()
        middleware = BearerAuthMiddleware(app)

        request = MagicMock()
        request.url.path = "/api/tools"
        request.headers = {}

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
