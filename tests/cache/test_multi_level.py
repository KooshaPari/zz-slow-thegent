"""Tests for thegent.cache.multi_level — MultiLevelCache and cached_multi.

FR traceability: FR-CACHE-001 (multi-level caching: L1 memory -> L2 disk)
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Module-level skip guard: tests require the optional `diskcache` dependency.
# Converting from `pytest.fail` to `pytest.skip(allow_module_level=True)` lets
# the file collect cleanly when diskcache is absent (CI may not always install
# every optional dep) while still skipping every test when diskcache is missing.
# The fine-grained `@pytest.mark.skipif(not _DISKCACHE_AVAILABLE, ...)` on
# individual tests is preserved for symmetry.
pytest.importorskip("diskcache", reason="diskcache dependency is required for cache integration tests")

from thegent.cache.multi_level import (
    _DISKCACHE_AVAILABLE,
    MultiLevelCache,
    cached_multi,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def l1_only_cache() -> MultiLevelCache:
    """Return an L1-only cache (no disk layer)."""
    return MultiLevelCache(l1_maxsize=10, l1_ttl=60)


@pytest.fixture
def two_level_cache(tmp_path: Path) -> MultiLevelCache:
    """Return a two-level cache backed by a temp directory."""
    cache = MultiLevelCache(l1_maxsize=10, l1_ttl=60, l2_dir=tmp_path / "cache", l2_ttl=3600)
    yield cache
    cache.close()


# ---------------------------------------------------------------------------
# FR-CACHE-001: Basic L1 operations
# ---------------------------------------------------------------------------


class TestL1Only:
    """FR-CACHE-001: L1-only mode (no diskcache) behaves correctly."""

    def test_get_returns_none_on_empty(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        assert l1_only_cache.get("missing") is None

    def test_set_and_get_roundtrip(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.set("key", "value")
        assert l1_only_cache.get("key") == "value"

    def test_set_overwrites_existing(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.set("key", "v1")
        l1_only_cache.set("key", "v2")
        assert l1_only_cache.get("key") == "v2"

    def test_delete_removes_key(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.set("key", "value")
        l1_only_cache.delete("key")
        assert l1_only_cache.get("key") is None

    def test_delete_nonexistent_key_is_noop(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.delete("no-such-key")  # must not raise

    def test_clear_empties_cache(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        for i in range(5):
            l1_only_cache.set(f"k{i}", i)
        l1_only_cache.clear()
        for i in range(5):
            assert l1_only_cache.get(f"k{i}") is None

    def test_l2_not_available_without_dir(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        assert not l1_only_cache.l2_available

    def test_stats_l1_only(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.set("a", 1)
        stats = l1_only_cache.stats()
        assert stats["l1_size"] == 1
        assert stats["l2_size"] == 0

    def test_various_value_types(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.set("int", 42)
        l1_only_cache.set("list", [1, 2, 3])
        l1_only_cache.set("dict", {"a": 1})
        assert l1_only_cache.get("int") == 42
        assert l1_only_cache.get("list") == [1, 2, 3]
        assert l1_only_cache.get("dict") == {"a": 1}


# ---------------------------------------------------------------------------
# FR-CACHE-001: L1 TTL expiry
# ---------------------------------------------------------------------------


class TestL1TTL:
    """FR-CACHE-001: TTL expiry on L1 is delegated to cachetools (no custom logic)."""

    def test_entry_expires_after_ttl(self) -> None:
        # @trace FR-CACHE-001
        cache = MultiLevelCache(l1_maxsize=10, l1_ttl=0.1)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.15)
        assert cache.get("key") is None

    def test_entry_still_present_before_ttl(self) -> None:
        # @trace FR-CACHE-001
        cache = MultiLevelCache(l1_maxsize=10, l1_ttl=5)
        cache.set("key", "value")
        assert cache.get("key") == "value"


# ---------------------------------------------------------------------------
# FR-CACHE-001: Two-level read-through and write-through
# ---------------------------------------------------------------------------


class TestTwoLevel:
    """FR-CACHE-001: Two-level cache (L1 + L2 diskcache) behaviour."""

    def test_l2_available_with_dir(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        assert two_level_cache.l2_available

    def test_write_through_to_l2(self, two_level_cache: MultiLevelCache, tmp_path: Path) -> None:
        # @trace FR-CACHE-001
        two_level_cache.set("key", "value")
        # Read directly from L2 to confirm write-through
        assert two_level_cache._l2.get("key") == "value"

    def test_l2_hit_promotes_to_l1(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        # Write directly to L2, bypassing L1
        two_level_cache._l2.set("key", "from_l2")
        # L1 should miss initially
        with two_level_cache._l1_lock:
            assert "key" not in two_level_cache._l1
        # get() should find it in L2 and promote to L1
        result = two_level_cache.get("key")
        assert result == "from_l2"
        # Now L1 should have it
        with two_level_cache._l1_lock:
            assert "key" in two_level_cache._l1

    def test_l2_miss_returns_none(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        assert two_level_cache.get("ghost") is None

    def test_delete_removes_from_both_levels(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        two_level_cache.set("key", "value")
        two_level_cache.delete("key")
        assert two_level_cache.get("key") is None
        assert two_level_cache._l2.get("key") is None

    def test_clear_removes_from_both_levels(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        for i in range(3):
            two_level_cache.set(f"k{i}", i)
        two_level_cache.clear()
        for i in range(3):
            assert two_level_cache.get(f"k{i}") is None
            assert two_level_cache._l2.get(f"k{i}") is None

    def test_custom_per_entry_ttl_propagates_to_l2(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        # Verify ttl override is accepted without error (actual expiry tested by L2 itself)
        two_level_cache.set("key", "val", ttl=10)
        assert two_level_cache.get("key") == "val"

    def test_stats_includes_l2_size(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        two_level_cache.set("a", 1)
        stats = two_level_cache.stats()
        assert "l2_size" in stats
        assert stats["l2_size"] >= 1

    def test_l1_serves_hit_without_touching_l2(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        two_level_cache.set("key", "value")
        mock_l2_get = MagicMock(return_value="value")
        two_level_cache._l2.get = mock_l2_get
        result = two_level_cache.get("key")
        assert result == "value"
        mock_l2_get.assert_not_called()


# ---------------------------------------------------------------------------
# FR-CACHE-001: L2 disabled when diskcache not installed
# ---------------------------------------------------------------------------


class TestDiskcacheFallback:
    """FR-CACHE-001: L1-only mode when diskcache is unavailable."""

    def test_l1_only_when_diskcache_missing(self, tmp_path: Path) -> None:
        # @trace FR-CACHE-001
        with patch("thegent.cache.multi_level._DISKCACHE_AVAILABLE", False):
            cache = MultiLevelCache(l1_maxsize=10, l1_ttl=60, l2_dir=tmp_path / "cache")
            assert not cache.l2_available
            assert cache.l2_init_status["reason"] == "diskcache_unavailable"
            cache.set("key", "value")
            assert cache.get("key") == "value"

    def test_l2_init_status_permission_denied(self, tmp_path: Path) -> None:
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("nope")):
            cache = MultiLevelCache(l1_maxsize=10, l1_ttl=60, l2_dir=tmp_path / "cache")
        assert cache.l2_available is False
        assert cache.l2_init_status["reason"] == "directory_error"

    def test_l2_init_status_open_failed(self, tmp_path: Path) -> None:
        with patch("diskcache.Cache", side_effect=RuntimeError("disk fail")):
            cache = MultiLevelCache(l1_maxsize=10, l1_ttl=60, l2_dir=tmp_path / "cache")
        assert cache.l2_available is False
        assert cache.l2_init_status["reason"] == "open_failed"

    def test_l2_init_status_invalid_path_file(self, tmp_path: Path) -> None:
        invalid_path = tmp_path / "not_a_dir"
        invalid_path.write_text("x", encoding="utf-8")
        cache = MultiLevelCache(l1_maxsize=10, l1_ttl=60, l2_dir=invalid_path)
        assert cache.l2_available is False
        assert cache.l2_init_status["reason"] == "directory_error"


# ---------------------------------------------------------------------------
# FR-CACHE-001: Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """FR-CACHE-001: Concurrent reads and writes are safe."""

    def test_concurrent_writes_do_not_corrupt(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        errors: list[Exception] = []

        def writer(n: int) -> None:
            try:
                for i in range(20):
                    l1_only_cache.set(f"key-{n}-{i}", n * 100 + i)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

    def test_concurrent_reads_and_writes(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        l1_only_cache.set("shared", "initial")
        errors: list[Exception] = []

        def reader() -> None:
            try:
                for _ in range(50):
                    l1_only_cache.get("shared")
            except Exception as exc:
                errors.append(exc)

        def writer() -> None:
            try:
                for i in range(50):
                    l1_only_cache.set("shared", f"v{i}")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(3)]
        threads += [threading.Thread(target=writer) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"


# ---------------------------------------------------------------------------
# FR-CACHE-001: cached_multi decorator
# ---------------------------------------------------------------------------


class TestCachedMultiDecorator:
    """FR-CACHE-001: cached_multi wraps functions with multi-level caching."""

    def test_decorator_caches_return_value(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        call_count = 0

        @cached_multi(l1_only_cache)
        def compute(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert compute(5) == 10
        assert compute(5) == 10
        assert call_count == 1  # second call served from cache

    def test_different_args_cached_separately(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        call_count = 0

        @cached_multi(l1_only_cache)
        def double(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert double(3) == 6
        assert double(7) == 14
        assert call_count == 2

    def test_unhashable_args_bypass_cache(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        call_count = 0

        @cached_multi(l1_only_cache)
        def process(data: list) -> int:
            nonlocal call_count
            call_count += 1
            return len(data)

        # Unhashable arg -- should not raise, just bypass cache
        assert process([1, 2, 3]) == 3
        assert process([1, 2, 3]) == 3
        assert call_count == 2  # cache bypassed both times

    def test_none_return_not_cached(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        call_count = 0

        @cached_multi(l1_only_cache)
        def might_return_none(flag: bool) -> int | None:
            nonlocal call_count
            call_count += 1
            return None if flag else 99

        assert might_return_none(True) is None
        assert might_return_none(True) is None
        assert call_count == 2  # None not cached; function called both times

    def test_cache_attribute_exposed_on_wrapper(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        @cached_multi(l1_only_cache)
        def fn(x: int) -> int:
            return x

        assert fn.cache is l1_only_cache

    def test_kwargs_produce_stable_key(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        call_count = 0

        @cached_multi(l1_only_cache)
        def add(a: int, b: int = 0) -> int:
            nonlocal call_count
            call_count += 1
            return a + b

        assert add(1, b=2) == 3
        assert add(1, b=2) == 3
        assert call_count == 1

    def test_functools_wraps_preserves_name(self, l1_only_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        @cached_multi(l1_only_cache)
        def my_func() -> int:
            return 1

        assert my_func.__name__ == "my_func"

    @pytest.mark.skipif(not _DISKCACHE_AVAILABLE, reason="diskcache not installed")
    def test_decorator_with_two_level_cache(self, two_level_cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-001
        call_count = 0

        @cached_multi(two_level_cache)
        def fetch(key: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{key}"

        assert fetch("x") == "result-x"
        assert fetch("x") == "result-x"
        assert call_count == 1
