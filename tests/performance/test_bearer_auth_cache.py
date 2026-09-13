"""Tests for WL-077: Cache ThegentSettings in BearerAuthMiddleware."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# The auth module lives at src/thegent/mcp/server/auth.py but is NOT importable
# as `thegent.mcp.server.auth` because `thegent.mcp.server` resolves to server.py.
# Load it the same way the production code does: via importlib.
_AUTH_MODULE_PATH = Path(__file__).resolve().parents[2] / "src" / "thegent" / "mcp" / "server" / "auth.py"


def _load_auth_module():
    spec = importlib.util.spec_from_file_location("thegent.mcp._server_auth", _AUTH_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load auth module from: {_AUTH_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_auth = _load_auth_module()
BearerAuthMiddleware = _auth.BearerAuthMiddleware
_get_settings = _auth.get_settings


@pytest.mark.requirement("FR-OPT-005")
class TestBearerAuthSettingsCache:
    """Verify BearerAuthMiddleware caches the ThegentSettings instance."""

    def _reset(self):
        """Reset the class-level cached settings."""
        BearerAuthMiddleware._settings = None

    def _make_request(self, *, path: str = "/test"):
        """Build a minimal fake Starlette Request."""
        req = MagicMock()
        req.url = MagicMock()
        req.url.path = path
        req.headers = {}
        return req

    @pytest.mark.asyncio
    async def test_second_dispatch_reuses_settings(self):
        """Two dispatches use the same ThegentSettings object."""
        self._reset()

        fake_settings = MagicMock()
        fake_settings.mcp_auth_mode = "none"

        with patch.object(_auth, "get_settings", return_value=fake_settings) as mock_get:
            middleware = BearerAuthMiddleware(app=MagicMock())
            call_next = AsyncMock(return_value=MagicMock())

            await middleware.dispatch(self._make_request(), call_next)
            await middleware.dispatch(self._make_request(), call_next)

        # get_settings called only once (first dispatch populates, second reuses)
        mock_get.assert_called_once()

        self._reset()

    @pytest.mark.asyncio
    async def test_reload_settings_forces_rebuild(self):
        """reload_settings() resets cache so next dispatch calls get_settings again."""
        self._reset()

        fake_a = MagicMock()
        fake_a.mcp_auth_mode = "none"
        fake_b = MagicMock()
        fake_b.mcp_auth_mode = "none"

        with patch.object(_auth, "get_settings", side_effect=[fake_a, fake_b]) as mock_get:
            middleware = BearerAuthMiddleware(app=MagicMock())
            call_next = AsyncMock(return_value=MagicMock())

            await middleware.dispatch(self._make_request(), call_next)
            BearerAuthMiddleware.reload_settings()
            await middleware.dispatch(self._make_request(), call_next)

        assert mock_get.call_count == 2

        self._reset()
