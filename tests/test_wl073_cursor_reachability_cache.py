"""Tests for WL-073: TTLCache on _is_cursor_api_reachable().

Verifies that repeated calls within the TTL window avoid making redundant HTTP
requests and that expiry causes a fresh check to be issued.

# @trace WL-073
"""

from __future__ import annotations

from unittest.mock import patch


class TestCursorApiReachabilityCache:
    """WL-073: _is_cursor_api_reachable() caches result for 30 seconds."""

    def _clear_cache(self):
        from thegent.agents.cursor_api_runner import _reachability_cache

        _reachability_cache.clear()

    def test_repeated_calls_return_cached_result(self):
        """# @trace WL-073 — second call reuses cached True without a new HTTP request."""
        self._clear_cache()

        with patch(
            "thegent.agents.cursor_api_runner._check_cursor_api_reachable", return_value=(True, False)
        ) as mock_check:
            from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

            r1 = _is_cursor_api_reachable("http://localhost:7777", "tok")
            r2 = _is_cursor_api_reachable("http://localhost:7777", "tok")

        assert r1 is True
        assert r2 is True
        mock_check.assert_called_once(), "HTTP check must only fire once per TTL window"

    def test_negative_result_is_also_cached(self):
        """# @trace WL-073 — False result is cached; no retry within TTL."""
        self._clear_cache()

        with patch(
            "thegent.agents.cursor_api_runner._check_cursor_api_reachable", return_value=(False, False)
        ) as mock_check:
            from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

            r1 = _is_cursor_api_reachable("http://localhost:7777", "tok")
            r2 = _is_cursor_api_reachable("http://localhost:7777", "tok")
            r3 = _is_cursor_api_reachable("http://localhost:7777", "tok")

        assert r1 is False
        assert r2 is False
        assert r3 is False
        mock_check.assert_called_once()

    def test_different_base_urls_have_separate_cache_entries(self):
        """# @trace WL-073 — distinct (base_url, token) pairs are cached independently."""
        self._clear_cache()
        call_args_log = []

        def fake_check(url, token, timeout=3.0):
            call_args_log.append((url, token))
            return (True, False)

        with patch("thegent.agents.cursor_api_runner._check_cursor_api_reachable", side_effect=fake_check):
            from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

            _is_cursor_api_reachable("http://localhost:7001", "tok")
            _is_cursor_api_reachable("http://localhost:7002", "tok")
            # These should hit cache
            _is_cursor_api_reachable("http://localhost:7001", "tok")
            _is_cursor_api_reachable("http://localhost:7002", "tok")

        assert len(call_args_log) == 2, "Each distinct URL should only trigger one HTTP call"
        assert ("http://localhost:7001", "tok") in call_args_log
        assert ("http://localhost:7002", "tok") in call_args_log

    def test_cache_expiry_triggers_new_http_request(self):
        """# @trace WL-073 — after cache cleared (TTL expired), fresh HTTP request is issued."""
        self._clear_cache()
        responses = [(True, False), (False, False)]

        with patch(
            "thegent.agents.cursor_api_runner._check_cursor_api_reachable",
            side_effect=responses,
        ) as mock_check:
            from thegent.agents.cursor_api_runner import (
                _is_cursor_api_reachable,
                _reachability_cache,
            )

            r1 = _is_cursor_api_reachable("http://localhost:7777", "tok")
            # Simulate TTL expiry by clearing the cache
            _reachability_cache.clear()
            r2 = _is_cursor_api_reachable("http://localhost:7777", "tok")

        assert r1 is True
        assert r2 is False
        assert mock_check.call_count == 2

    def test_reachability_cache_module_level_ttl_is_30(self):
        """# @trace WL-073 — _reachability_cache has 30-second TTL."""
        from thegent.agents.cursor_api_runner import _reachability_cache

        assert _reachability_cache.ttl == 30

    def test_check_function_receives_correct_arguments(self):
        """# @trace WL-073 — underlying _check_cursor_api_reachable receives URL, token, timeout."""
        self._clear_cache()

        with patch(
            "thegent.agents.cursor_api_runner._check_cursor_api_reachable", return_value=(True, False)
        ) as mock_check:
            from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

            _is_cursor_api_reachable("http://cursor-host:8080", "my-token", 5.0)

        mock_check.assert_called_once_with("http://cursor-host:8080", "my-token", 5.0)

    def test_multiple_tokens_same_url_separate_entries(self):
        """# @trace WL-073 — same URL with different tokens are cached independently."""
        self._clear_cache()
        call_log = []

        def fake_check(url, token, timeout=3.0):
            call_log.append(token)
            return (True, False)

        with patch("thegent.agents.cursor_api_runner._check_cursor_api_reachable", side_effect=fake_check):
            from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

            _is_cursor_api_reachable("http://localhost:7777", "token-a")
            _is_cursor_api_reachable("http://localhost:7777", "token-b")
            # Repeated calls — must hit cache
            _is_cursor_api_reachable("http://localhost:7777", "token-a")
            _is_cursor_api_reachable("http://localhost:7777", "token-b")

        assert call_log.count("token-a") == 1
        assert call_log.count("token-b") == 1

    def test_connection_failure_resets_cache(self):
        """# @trace WL-073 — connection error causes cache entry to be reset, allowing retry."""
        self._clear_cache()

        # First call returns True (reachable)
        # Second call returns (False, True) - connection error, should reset cache
        # Third call returns True again - should NOT use cache (cache was reset)
        responses = [(True, False), (False, True), (True, False)]

        with patch(
            "thegent.agents.cursor_api_runner._check_cursor_api_reachable",
            side_effect=responses,
        ) as mock_check:
            from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

            r1 = _is_cursor_api_reachable("http://localhost:7777", "tok")
            r2 = _is_cursor_api_reachable("http://localhost:7777", "tok")  # Connection error
            r3 = _is_cursor_api_reachable("http://localhost:7777", "tok")  # Should retry

        assert r1 is True
        assert r2 is False
        assert r3 is True
        # Should be called 3 times because cache was reset after connection error
        assert mock_check.call_count == 3
