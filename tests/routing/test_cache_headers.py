"""Tests for GW-24, GW-25, GW-27: cache control header extraction and response headers.

# @trace FR-CACHE-024 FR-CACHE-025 FR-CACHE-027
"""

from __future__ import annotations

import pytest

from thegent.cliproxy_adapter import (
    CacheControl,
    build_cache_response_headers,
    extract_cache_control,
)


def _make_request(headers: dict[str, str]):
    """Build a minimal Starlette Request with the given headers for testing."""
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/chat/completions",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "query_string": b"",
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# CacheControl dataclass
# ---------------------------------------------------------------------------


class TestCacheControlDataclass:
    """@trace FR-CACHE-024 FR-CACHE-025"""

    @pytest.mark.requirement("FR-CACHE-024")
    def test_cache_control_defaults(self) -> None:
        cc = CacheControl()
        assert cc.namespace == "default"
        assert cc.force_refresh is False
        assert cc.skip_cache is False

    @pytest.mark.requirement("FR-CACHE-024")
    def test_cache_control_custom_values(self) -> None:
        cc = CacheControl(namespace="team-x", force_refresh=True, skip_cache=True)
        assert cc.namespace == "team-x"
        assert cc.force_refresh is True
        assert cc.skip_cache is True


# ---------------------------------------------------------------------------
# extract_cache_control
# ---------------------------------------------------------------------------


class TestExtractCacheControl:
    """@trace FR-CACHE-024 FR-CACHE-025"""

    @pytest.mark.requirement("FR-CACHE-024")
    def test_extract_cache_control_defaults(self) -> None:
        request = _make_request({})
        cc = extract_cache_control(request)
        assert cc.namespace == "default"
        assert cc.force_refresh is False
        assert cc.skip_cache is False

    @pytest.mark.requirement("FR-CACHE-024")
    def test_extract_cache_namespace_header(self) -> None:
        request = _make_request({"tg-cache-namespace": "user-123"})
        cc = extract_cache_control(request)
        assert cc.namespace == "user-123"

    @pytest.mark.requirement("FR-CACHE-025")
    def test_extract_cache_force_refresh_true(self) -> None:
        request = _make_request({"tg-cache-force-refresh": "true"})
        cc = extract_cache_control(request)
        assert cc.force_refresh is True

    @pytest.mark.requirement("FR-CACHE-025")
    def test_extract_cache_force_refresh_false(self) -> None:
        request = _make_request({"tg-cache-force-refresh": "false"})
        cc = extract_cache_control(request)
        assert cc.force_refresh is False

    @pytest.mark.requirement("FR-CACHE-025")
    def test_extract_cache_force_refresh_case_insensitive(self) -> None:
        request = _make_request({"tg-cache-force-refresh": "TRUE"})
        cc = extract_cache_control(request)
        assert cc.force_refresh is True

    @pytest.mark.requirement("FR-CACHE-025")
    def test_extract_skip_cache_true(self) -> None:
        request = _make_request({"tg-skip-cache": "true"})
        cc = extract_cache_control(request)
        assert cc.skip_cache is True

    @pytest.mark.requirement("FR-CACHE-024")
    def test_extract_cache_control_all_headers(self) -> None:
        request = _make_request(
            {
                "tg-cache-namespace": "org-456",
                "tg-cache-force-refresh": "true",
                "tg-skip-cache": "true",
            }
        )
        cc = extract_cache_control(request)
        assert cc.namespace == "org-456"
        assert cc.force_refresh is True
        assert cc.skip_cache is True


# ---------------------------------------------------------------------------
# build_cache_response_headers
# ---------------------------------------------------------------------------


class TestBuildCacheResponseHeaders:
    """@trace FR-CACHE-027"""

    @pytest.mark.requirement("FR-CACHE-027")
    def test_cache_hit_headers(self) -> None:
        result = build_cache_response_headers(hit=True, ttl=60.0, namespace="default")
        assert result["x-cache-status"] == "HIT"

    @pytest.mark.requirement("FR-CACHE-027")
    def test_cache_miss_headers(self) -> None:
        result = build_cache_response_headers(hit=False, ttl=60.0, namespace="default")
        assert result["x-cache-status"] == "MISS"

    @pytest.mark.requirement("FR-CACHE-027")
    def test_cache_ttl_in_headers(self) -> None:
        result = build_cache_response_headers(hit=True, ttl=300.5, namespace="default")
        assert result["x-cache-ttl"] == "300"

    @pytest.mark.requirement("FR-CACHE-027")
    def test_cache_namespace_in_headers(self) -> None:
        result = build_cache_response_headers(hit=False, ttl=120.0, namespace="user-123")
        assert result["x-cache-namespace"] == "user-123"

    @pytest.mark.requirement("FR-CACHE-027")
    def test_cache_headers_all_keys_present(self) -> None:
        result = build_cache_response_headers(hit=True, ttl=45.0, namespace="ns-abc")
        assert "x-cache-status" in result
        assert "x-cache-ttl" in result
        assert "x-cache-namespace" in result
