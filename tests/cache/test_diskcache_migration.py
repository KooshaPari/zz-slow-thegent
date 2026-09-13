"""Tests covering the diskcache migration of ad-hoc caches to MultiLevelCache.

FR traceability: FR-CACHE-002 (diskcache migration: quality/speed/models caches)

Modules under test:
  - thegent.models.quality_values (_CACHE, invalidate_quality_index_cache)
  - thegent.models.speed_values   (_CACHE, invalidate_speed_index_cache)
  - thegent.models.scrapers       (_MODELS_CACHE, _load_cached, _save_cache,
                                   invalidate_models_cache, get_models_cache_path)
  - thegent.cache.multi_level     (l2_dir property added for public introspection)
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Module-level skip guard: tests require the optional `diskcache` dependency.
# Converting from `pytest.fail` to `pytest.importorskip` lets the file collect
# cleanly when diskcache is absent (CI may not always install every optional
# dep) while still skipping every test when diskcache is missing.
pytest.importorskip("diskcache", reason="diskcache dependency is required for diskcache migration tests")

from thegent.cache.multi_level import MultiLevelCache

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cache(tmp_path: Path, l1_ttl: float = 60, l2_ttl: float = 3600) -> MultiLevelCache:
    """Factory: two-level cache backed by a temp directory."""
    cache = MultiLevelCache(
        l1_maxsize=8,
        l1_ttl=l1_ttl,
        l2_dir=tmp_path / "mlc",
        l2_ttl=l2_ttl,
    )
    return cache


# ---------------------------------------------------------------------------
# FR-CACHE-002: l2_dir property on MultiLevelCache
# ---------------------------------------------------------------------------


class TestMultiLevelCacheL2DirProperty:
    """FR-CACHE-002: Public l2_dir property exposes the disk-cache directory."""

    def test_l2_dir_none_when_l2_disabled(self) -> None:
        # @trace FR-CACHE-002
        cache = MultiLevelCache(l1_maxsize=4, l1_ttl=60)
        assert cache.l2_dir is None

    def test_l2_dir_returns_path_when_l2_enabled(self, tmp_path: Path) -> None:
        # @trace FR-CACHE-002
        cache = _make_cache(tmp_path)
        try:
            assert cache.l2_dir is not None
            assert isinstance(cache.l2_dir, Path)
        finally:
            cache.close()

    def test_l2_dir_matches_configured_path(self, tmp_path: Path) -> None:
        # @trace FR-CACHE-002
        l2_path = tmp_path / "specific-cache"
        cache = MultiLevelCache(l1_maxsize=4, l1_ttl=60, l2_dir=l2_path)
        try:
            assert cache.l2_dir is not None
            assert cache.l2_dir.resolve() == l2_path.resolve()
        finally:
            cache.close()

    def test_l2_dir_directory_exists_after_init(self, tmp_path: Path) -> None:
        # @trace FR-CACHE-002
        cache = _make_cache(tmp_path)
        try:
            assert cache.l2_dir is not None
            assert cache.l2_dir.is_dir()
        finally:
            cache.close()


# ---------------------------------------------------------------------------
# FR-CACHE-002: quality_values._CACHE is now MultiLevelCache
# ---------------------------------------------------------------------------


class TestQualityValuesCache:
    """FR-CACHE-002: quality_values uses MultiLevelCache instead of plain TTLCache."""

    def test_cache_is_multi_level_cache_instance(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.quality_values import _CACHE

        assert isinstance(_CACHE, MultiLevelCache)

    def test_cache_set_and_get_roundtrip(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.quality_values import _CACHE

        _CACHE.clear()
        sample: dict[str, dict[str, float]] = {"gpt-5": {"openai": 0.9}}
        _CACHE.set("default", sample)
        assert _CACHE.get("default") == sample

    def test_invalidate_quality_index_cache_clears_entries(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.quality_values import _CACHE, invalidate_quality_index_cache

        _CACHE.set("default", {"model": {"prov": 0.8}})
        assert _CACHE.get("default") is not None
        invalidate_quality_index_cache()
        assert _CACHE.get("default") is None

    def test_get_model_provider_quality_indices_populates_cache(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.quality_values import (
            _CACHE,
            get_model_provider_quality_indices,
            invalidate_quality_index_cache,
        )

        invalidate_quality_index_cache()
        # Patch out expensive internals so the test is fast and isolated.
        with (
            patch("thegent.models.quality_values._load_benchmarks", return_value={}),
            patch(
                "thegent.models.cost_values._iter_catalog_routes",
                return_value=[],
            ),
        ):
            result = get_model_provider_quality_indices(use_cache=True)
        assert isinstance(result, dict)
        # Cache should now be populated.
        assert _CACHE.get("default") is not None

    def test_get_model_provider_quality_indices_uses_cache_on_second_call(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.quality_values import (
            _CACHE,
            get_model_provider_quality_indices,
            invalidate_quality_index_cache,
        )

        invalidate_quality_index_cache()
        sentinel: dict[str, dict[str, float]] = {"sentinel-model": {"provider": 0.42}}
        _CACHE.set("default", sentinel)
        # With use_cache=True the cache hit should be returned directly.
        result = get_model_provider_quality_indices(use_cache=True)
        assert result == sentinel

    def test_use_cache_false_bypasses_cache(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.quality_values import (
            _CACHE,
            get_model_provider_quality_indices,
        )

        sentinel: dict[str, dict[str, float]] = {"stale": {"prov": 0.0}}
        _CACHE.set("default", sentinel)
        # use_cache=False must bypass the sentinel.
        with (
            patch("thegent.models.quality_values._load_benchmarks", return_value={}),
            patch("thegent.models.cost_values._iter_catalog_routes", return_value=[]),
        ):
            result = get_model_provider_quality_indices(use_cache=False)
        # Result is freshly computed (empty routes -> empty dict), not the sentinel.
        assert result != sentinel


# ---------------------------------------------------------------------------
# FR-CACHE-002: speed_values._CACHE is now MultiLevelCache
# ---------------------------------------------------------------------------


class TestSpeedValuesCache:
    """FR-CACHE-002: speed_values uses MultiLevelCache instead of plain TTLCache."""

    def test_cache_is_multi_level_cache_instance(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.speed_values import _CACHE

        assert isinstance(_CACHE, MultiLevelCache)

    def test_cache_set_and_get_roundtrip(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.speed_values import _CACHE

        _CACHE.clear()
        sample: dict[str, dict[str, float]] = {"gpt-5": {"openai": 0.7}}
        _CACHE.set("default", sample)
        assert _CACHE.get("default") == sample

    def test_invalidate_speed_index_cache_clears_entries(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.speed_values import _CACHE, invalidate_speed_index_cache

        _CACHE.set("default", {"model": {"prov": 0.5}})
        assert _CACHE.get("default") is not None
        invalidate_speed_index_cache()
        assert _CACHE.get("default") is None

    def test_get_model_provider_speed_indices_uses_cache(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.speed_values import (
            _CACHE,
            get_model_provider_speed_indices,
            invalidate_speed_index_cache,
        )

        invalidate_speed_index_cache()
        sentinel: dict[str, dict[str, float]] = {"fast-model": {"prov": 0.99}}
        _CACHE.set("default", sentinel)
        result = get_model_provider_speed_indices(use_cache=True)
        assert result == sentinel

    def test_use_cache_false_bypasses_speed_cache(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.speed_values import (
            _CACHE,
            get_model_provider_speed_indices,
        )

        sentinel: dict[str, dict[str, float]] = {"stale-speed": {"prov": 0.0}}
        _CACHE.set("default", sentinel)
        # fetch_provider_metrics is imported inside get_model_provider_speed_indices
        # via a local import from thegent.agents.cliproxy_manager, so patch there.
        with (
            patch(
                "thegent.agents.cliproxy_manager.fetch_provider_metrics",
                return_value=None,
            ),
            patch("thegent.models.cost_values._iter_catalog_routes", return_value=[]),
        ):
            result = get_model_provider_speed_indices(use_cache=False)
        # Result is freshly computed (empty routes -> empty dict), not the sentinel.
        assert result != sentinel


# ---------------------------------------------------------------------------
# FR-CACHE-002: scrapers._MODELS_CACHE is MultiLevelCache
# ---------------------------------------------------------------------------


class TestScrapersCache:
    """FR-CACHE-002: scrapers uses MultiLevelCache (replaces bare diskcache.Cache)."""

    def test_models_cache_is_multi_level_cache(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import _MODELS_CACHE

        assert isinstance(_MODELS_CACHE, MultiLevelCache)

    def test_save_cache_stores_by_provider(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import _MODELS_CACHE, _save_cache

        _MODELS_CACHE.clear()
        data = {"gemini": ["gemini-3-flash"], "claude": ["claude-haiku-4.5"]}
        _save_cache(data, ttl_sec=300)
        assert _MODELS_CACHE.get("by_provider") == data

    def test_load_cached_returns_none_on_empty(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import _MODELS_CACHE, _load_cached

        _MODELS_CACHE.clear()
        assert _load_cached() is None

    def test_load_cached_returns_saved_data(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import _MODELS_CACHE, _load_cached, _save_cache

        _MODELS_CACHE.clear()
        data = {"copilot": ["gpt-5.3-codex"]}
        _save_cache(data, ttl_sec=300)
        result = _load_cached()
        assert result is not None
        by_provider, mtime = result
        assert by_provider == data
        assert isinstance(mtime, float)

    def test_invalidate_models_cache_clears_data(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import (
            _MODELS_CACHE,
            _save_cache,
            invalidate_models_cache,
        )

        _MODELS_CACHE.clear()
        _save_cache({"cursor-agent": ["gpt-4"]})
        had_entries = invalidate_models_cache()
        assert had_entries is True
        assert _MODELS_CACHE.get("by_provider") is None

    def test_invalidate_models_cache_on_empty_returns_false(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import _MODELS_CACHE, invalidate_models_cache

        _MODELS_CACHE.clear()
        assert invalidate_models_cache() is False

    def test_get_models_cache_path_returns_path(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import get_models_cache_path

        path = get_models_cache_path()
        assert isinstance(path, Path)

    def test_save_and_load_roundtrip_with_mtime(self) -> None:
        # @trace FR-CACHE-002
        from thegent.models.scrapers import _MODELS_CACHE, _load_cached, _save_cache

        _MODELS_CACHE.clear()
        before = time.time()
        data = {"antigravity": ["minimax-m2.5"]}
        _save_cache(data, ttl_sec=300)
        result = _load_cached()
        assert result is not None
        by_provider, mtime = result
        assert by_provider == data
        # mtime should be ≥ before (stored as float unix ts)
        assert mtime >= before
