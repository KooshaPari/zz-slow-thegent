"""Tests for WL-077: lru_cache singleton for ThegentSettings in mcp/server.py.

Verifies that _get_settings() returns the same object on every call, that
ThegentSettings() is only constructed once per process lifetime, and that
BearerAuthMiddleware.dispatch uses the singleton.

# @trace WL-077
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGetSettingsSingleton:
    """WL-077: _get_settings() is a process-wide singleton via lru_cache."""

    def _clear_lru_cache(self):
        from thegent.mcp.server import _get_settings

        _get_settings.cache_clear()

    def test_repeated_calls_return_identical_object(self):
        """# @trace WL-077 — two consecutive calls to _get_settings() return the exact same object."""
        self._clear_lru_cache()
        fake_settings = MagicMock(name="settings_singleton")

        with patch("thegent.mcp.server.ThegentSettings", return_value=fake_settings) as mock_cls:
            from thegent.mcp.server import _get_settings

            s1 = _get_settings()
            s2 = _get_settings()

        assert s1 is s2, "_get_settings() must return the same instance on every call"
        mock_cls.assert_called_once()

    def test_thegent_settings_constructor_called_once(self):
        """# @trace WL-077 — ThegentSettings() is invoked exactly once regardless of call count."""
        self._clear_lru_cache()
        fake_settings = MagicMock(name="settings_once")

        with patch("thegent.mcp.server.ThegentSettings", return_value=fake_settings) as mock_cls:
            from thegent.mcp.server import _get_settings

            for _ in range(50):
                _get_settings()

        mock_cls.assert_called_once()

    def test_get_settings_returns_thegent_settings_instance(self):
        """# @trace WL-077 — return value is whatever ThegentSettings() produces."""
        self._clear_lru_cache()
        sentinel = MagicMock(name="settings_value")

        with patch("thegent.mcp.server.ThegentSettings", return_value=sentinel):
            from thegent.mcp.server import _get_settings

            result = _get_settings()

        assert result is sentinel

    def test_get_settings_function_is_lru_cached(self):
        """# @trace WL-077 — _get_settings exposes cache_info() from lru_cache."""
        from thegent.mcp.server import _get_settings

        assert hasattr(_get_settings, "cache_info"), "_get_settings must be decorated with lru_cache"
        assert hasattr(_get_settings, "cache_clear"), "_get_settings must support cache_clear()"

    def test_bearer_auth_middleware_dispatch_uses_singleton(self):
        """# @trace WL-077 — BearerAuthMiddleware.dispatch calls _get_settings, not ThegentSettings()."""
        self._clear_lru_cache()

        fake_settings = MagicMock()
        fake_settings.mcp_auth_mode = "none"  # Disable auth to pass through

        call_count = {"n": 0}
        original_settings = fake_settings

        def singleton():
            call_count["n"] += 1
            return original_settings

        mock_request = MagicMock()
        mock_request.url.path = "/tools/call"
        mock_request.headers.get.return_value = None

        async def mock_call_next(req):
            return MagicMock(status_code=200)

        import asyncio

        with patch("thegent.mcp.server._get_settings", side_effect=singleton):
            from thegent.mcp.server import BearerAuthMiddleware

            middleware = BearerAuthMiddleware(app=MagicMock())
            asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        assert call_count["n"] >= 1, "_get_settings must be called during dispatch"

    def test_cache_clear_forces_reconstruction(self):
        """# @trace WL-077 — after cache_clear(), a fresh ThegentSettings() is constructed."""
        self._clear_lru_cache()
        first = MagicMock(name="first_settings")
        second = MagicMock(name="second_settings")

        with patch("thegent.mcp.server.ThegentSettings", side_effect=[first, second]) as mock_cls:
            from thegent.mcp.server import _get_settings

            s1 = _get_settings()
            _get_settings.cache_clear()
            s2 = _get_settings()

        assert s1 is first
        assert s2 is second
        assert mock_cls.call_count == 2
