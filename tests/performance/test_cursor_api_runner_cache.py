"""Tests for WL-073: Cursor API reachability cache."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.requirement("FR-OPT-004")
class TestCursorApiReachabilityCache:
    """Verify _is_cursor_api_reachable() caches results with 30 s TTL."""

    def _clear_cache(self):
        """Reset the module-level reachability cache."""
        from thegent.agents import cursor_api_runner as mod

        mod._reachability_cache.clear()

    def test_cache_hit_skips_http_probe(self):
        """Second call with same args returns cached result without HTTP call."""
        from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

        self._clear_cache()

        with patch("thegent.agents.cursor_api_runner._check_cursor_api_reachable") as mock_check:
            mock_check.return_value = (True, False, 200)

            first = _is_cursor_api_reachable("http://localhost:8080", "tok")
            second = _is_cursor_api_reachable("http://localhost:8080", "tok")

        assert first is True
        assert second is True
        mock_check.assert_called_once()

    def test_cache_miss_triggers_probe(self):
        """First call triggers the HTTP probe."""
        from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

        self._clear_cache()

        with patch("thegent.agents.cursor_api_runner._check_cursor_api_reachable") as mock_check:
            mock_check.return_value = (False, False, None)

            result = _is_cursor_api_reachable("http://localhost:9999", "tok2")

        assert result is False
        mock_check.assert_called_once()

    def test_connection_failure_invalidates_cache(self):
        """Connection error does NOT cache the result, so next call re-probes."""
        from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

        self._clear_cache()

        with patch("thegent.agents.cursor_api_runner._check_cursor_api_reachable") as mock_check:
            # First call: connection error — result not cached
            mock_check.return_value = (False, True, None)
            _is_cursor_api_reachable("http://localhost:8080", "tok")

            # Second call: should re-probe (cache was not populated)
            mock_check.return_value = (True, False, 200)
            result = _is_cursor_api_reachable("http://localhost:8080", "tok")

        assert result is True
        assert mock_check.call_count == 2
