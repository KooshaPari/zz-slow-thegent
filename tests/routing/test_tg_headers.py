"""Tests for GW-20: tg-* per-request header namespace (cliproxy_adapter).

# @trace FR-ROUTE-020
"""

from __future__ import annotations

import pytest

from thegent.cliproxy_adapter import _TG_HEADER_NAMES, TgHeaders, extract_tg_headers


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_defaults() -> None:
    """No tg-* headers present — all fields are at their defaults."""
    result = extract_tg_headers({})
    assert result.cache_ttl is None
    assert result.skip_cache is False
    assert result.cache_namespace == "default"
    assert result.cache_force_refresh is False
    assert result.custom_cost is None


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_cache_ttl_valid() -> None:
    result = extract_tg_headers({"tg-cache-ttl": "300"})
    assert result.cache_ttl == 300.0


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_cache_ttl_invalid() -> None:
    """Non-numeric tg-cache-ttl yields None (no crash)."""
    result = extract_tg_headers({"tg-cache-ttl": "not-a-number"})
    assert result.cache_ttl is None


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_skip_cache_true() -> None:
    result = extract_tg_headers({"tg-skip-cache": "true"})
    assert result.skip_cache is True


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_skip_cache_false() -> None:
    result = extract_tg_headers({"tg-skip-cache": "false"})
    assert result.skip_cache is False


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_cache_namespace() -> None:
    result = extract_tg_headers({"tg-cache-namespace": "my-project"})
    assert result.cache_namespace == "my-project"


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_cache_force_refresh() -> None:
    result = extract_tg_headers({"tg-cache-force-refresh": "true"})
    assert result.cache_force_refresh is True


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_custom_cost_valid() -> None:
    result = extract_tg_headers({"tg-custom-cost": "0.0025"})
    assert result.custom_cost == pytest.approx(0.0025)


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_custom_cost_invalid() -> None:
    """Non-numeric tg-custom-cost yields None (no crash)."""
    result = extract_tg_headers({"tg-custom-cost": "free"})
    assert result.custom_cost is None


@pytest.mark.requirement("FR-ROUTE-020")
def test_extract_tg_headers_case_insensitive() -> None:
    """Header names are normalised to lowercase before matching."""
    result = extract_tg_headers({"TG-SKIP-CACHE": "TRUE"})
    assert result.skip_cache is True


@pytest.mark.requirement("FR-ROUTE-020")
def test_tg_headers_dataclass_defaults() -> None:
    """TgHeaders() with no arguments has the documented default values."""
    h = TgHeaders()
    assert h.cache_ttl is None
    assert h.skip_cache is False
    assert h.cache_namespace == "default"
    assert h.cache_force_refresh is False
    assert h.custom_cost is None


@pytest.mark.requirement("FR-ROUTE-020")
def test_tg_header_names_all_tg_prefix() -> None:
    """Every entry in _TG_HEADER_NAMES must start with 'tg-'."""
    for name in _TG_HEADER_NAMES:
        assert name.startswith("tg-"), f"Header {name!r} does not start with 'tg-'"
