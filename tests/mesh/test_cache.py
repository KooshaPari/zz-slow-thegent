"""Tests for mesh cache: singleflight dedup, inotify invalidation, heat-based LRU.

# @trace TGNT-P9.1 (singleflight dedup)
# @trace TGNT-P9.2 (inotify cache invalidation)
# @trace TGNT-P9.3 (heat-based LRU eviction)
"""

import hashlib
import threading
import time
from pathlib import Path

import orjson as json
import pytest

from thegent.mesh.cache import MeshCache, Singleflight

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sf() -> Singleflight:
    """Fresh Singleflight instance."""
    return Singleflight()


@pytest.fixture
def mesh_cache(tmp_path: Path) -> MeshCache:
    """MeshCache backed by a temporary directory with default capacity."""
    return MeshCache(tmp_path, capacity=1000)


@pytest.fixture
def small_cache(tmp_path: Path) -> MeshCache:
    """MeshCache with capacity=3 for eviction tests."""
    return MeshCache(tmp_path, capacity=3)


# ---------------------------------------------------------------------------
# 1. Singleflight — TGNT-P9.1
# ---------------------------------------------------------------------------


class TestSingleflightBasic:
    """Basic singleflight behaviour: execute once, return cached result."""

    # @trace TGNT-P9.1
    def test_first_call_executes_func(self, sf: Singleflight) -> None:
        """First call for a key actually invokes the callable."""
        result = sf.do("k1", lambda: 42)
        assert result == 42

    # @trace TGNT-P9.1
    def test_second_call_returns_cached(self, sf: Singleflight) -> None:
        """Subsequent calls return the cached result without re-executing."""
        call_count = 0

        def work() -> str:
            nonlocal call_count
            call_count += 1
            return "done"

        assert sf.do("k1", work) == "done"
        assert sf.do("k1", work) == "done"
        assert call_count == 1

    # @trace TGNT-P9.1
    def test_different_keys_independent(self, sf: Singleflight) -> None:
        """Different keys execute independently."""
        r1 = sf.do("a", lambda: "alpha")
        r2 = sf.do("b", lambda: "beta")
        assert r1 == "alpha"
        assert r2 == "beta"


class TestSingleflightConcurrency:
    """Concurrent callers are deduplicated: only one executes."""

    # @trace TGNT-P9.1
    def test_concurrent_calls_deduplicated(self, sf: Singleflight) -> None:
        """Multiple threads calling do() with the same key: only one executes."""
        call_count = 0
        barrier = threading.Barrier(4)

        def slow_work() -> str:
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)
            return "result"

        results: list[str | None] = [None] * 4

        def caller(idx: int) -> None:
            barrier.wait()
            results[idx] = sf.do("shared", slow_work)

        threads = [threading.Thread(target=caller, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # All threads get the same result
        assert all(r == "result" for r in results)
        # The function was called at most once (the first thread executes,
        # the rest find the cached result after the lock is released)
        assert call_count == 1

    # @trace TGNT-P9.1
    def test_exception_propagates(self, sf: Singleflight) -> None:
        """If the callable raises, the exception propagates to the caller."""
        with pytest.raises(ValueError, match="boom"):
            sf.do("fail", lambda: (_ for _ in ()).throw(ValueError("boom")))


# ---------------------------------------------------------------------------
# 2. MeshCache basic operations — TGNT-P9.2 / TGNT-P9.3
# ---------------------------------------------------------------------------


class TestMeshCacheInit:
    """Cache directory is created on construction."""

    def test_cache_dir_created(self, tmp_path: Path) -> None:
        """MeshCache creates the cache sub-directory."""
        MeshCache(tmp_path / "mesh", capacity=10)
        assert (tmp_path / "mesh" / "cache").is_dir()

    def test_idempotent_init(self, tmp_path: Path) -> None:
        """Creating two MeshCache instances on the same root does not raise."""
        MeshCache(tmp_path, capacity=5)
        MeshCache(tmp_path, capacity=5)


class TestMeshCacheGetSet:
    """get/set round-trip and miss behaviour."""

    # @trace TGNT-P9.3
    def test_get_miss_returns_none(self, mesh_cache: MeshCache) -> None:
        """A cache miss returns None."""
        assert mesh_cache.get("nonexistent") is None

    # @trace TGNT-P9.3
    def test_set_then_get(self, mesh_cache: MeshCache) -> None:
        """A stored value is retrievable."""
        mesh_cache.set("k1", {"data": 123})
        assert mesh_cache.get("k1") == {"data": 123}

    # @trace TGNT-P9.3
    def test_overwrite_existing(self, mesh_cache: MeshCache) -> None:
        """Setting a key again overwrites the previous value."""
        mesh_cache.set("k1", "old")
        mesh_cache.set("k1", "new")
        assert mesh_cache.get("k1") == "new"

    # @trace TGNT-P9.3
    def test_heat_map_updated_on_get(self, mesh_cache: MeshCache) -> None:
        """Accessing a key increases its heat."""
        mesh_cache.set("k1", "val")
        initial_heat = mesh_cache.heat_map.get("k1", 0)
        mesh_cache.get("k1")
        assert mesh_cache.heat_map["k1"] > initial_heat


# ---------------------------------------------------------------------------
# 3. Heat-based LRU eviction — TGNT-P9.3
# ---------------------------------------------------------------------------


class TestHeatBasedEviction:
    """Capacity-limited cache evicts the coldest entry."""

    # @trace TGNT-P9.3
    def test_evict_coldest_when_full(self, small_cache: MeshCache) -> None:
        """When capacity is reached, the coldest entry is evicted on next set."""
        # Fill to capacity (3)
        small_cache.set("a", 1)
        small_cache.set("b", 2)
        small_cache.set("c", 3)

        # Access "b" and "c" to raise their heat; "a" stays cold
        small_cache.get("b")
        small_cache.get("c")

        # Adding a 4th key should evict "a" (coldest)
        small_cache.set("d", 4)

        assert small_cache.get("a") is None  # evicted
        assert small_cache.get("d") == 4  # new entry present

    # @trace TGNT-P9.3
    def test_heat_decay(self, mesh_cache: MeshCache) -> None:
        """Heat decays multiplicatively (0.9 factor) on each access."""
        mesh_cache.set("k1", "val")
        # After set, heat is 1.0
        heat_after_set = mesh_cache.heat_map["k1"]

        # Access: new_heat = old_heat * 0.9 + 1.0
        mesh_cache.get("k1")
        expected = heat_after_set * 0.9 + 1.0
        assert abs(mesh_cache.heat_map["k1"] - expected) < 1e-9

    # @trace TGNT-P9.3
    def test_evict_on_empty_heat_map(self, tmp_path: Path) -> None:
        """_evict_coldest on empty heat_map is a no-op."""
        mc = MeshCache(tmp_path, capacity=5)
        mc._evict_coldest()  # should not raise

    # @trace TGNT-P9.3
    def test_eviction_removes_file(self, small_cache: MeshCache) -> None:
        """Evicted entry's JSON file is deleted from disk."""
        small_cache.set("x", 1)
        small_cache.set("y", 2)
        small_cache.set("z", 3)

        # Warm y and z
        small_cache.get("y")
        small_cache.get("z")

        cache_file_x = small_cache.cache_dir / "x.json"
        assert cache_file_x.exists()

        # Trigger eviction of x
        small_cache.set("w", 4)
        assert not cache_file_x.exists()

    # @trace TGNT-P9.3
    def test_multiple_accesses_raise_heat(self, small_cache: MeshCache) -> None:
        """Repeated access significantly raises heat above a single access."""
        small_cache.set("hot", "v")
        small_cache.set("cold", "v")

        for _ in range(10):
            small_cache.get("hot")

        assert small_cache.heat_map["hot"] > small_cache.heat_map["cold"]


# ---------------------------------------------------------------------------
# 4. File-based cache invalidation — TGNT-P9.2
# ---------------------------------------------------------------------------


class TestInvalidateByFile:
    """invalidate_by_file removes entries matching file-path hash."""

    # @trace TGNT-P9.2
    def test_invalidate_matching_entry(self, mesh_cache: MeshCache) -> None:
        """Entry whose key contains the file's MD5 hash is removed."""
        file_path = "/src/thegent/config.py"
        file_hash = hashlib.md5(file_path.encode()).hexdigest()

        # Create a cache file whose name contains the hash
        cache_file = mesh_cache.cache_dir / f"prefix_{file_hash}_suffix.json"
        cache_file.write_text(json.dumps({"cached": True}).decode())

        count = mesh_cache.invalidate_by_file(file_path)
        assert count == 1
        assert not cache_file.exists()

    # @trace TGNT-P9.2
    def test_invalidate_no_match(self, mesh_cache: MeshCache) -> None:
        """Returns 0 when no cache files match the file path."""
        mesh_cache.set("unrelated", {"x": 1})
        count = mesh_cache.invalidate_by_file("/no/such/file.py")
        assert count == 0

    # @trace TGNT-P9.2
    def test_invalidate_multiple_matches(self, mesh_cache: MeshCache) -> None:
        """All matching cache files are removed."""
        file_path = "/models/user.py"
        file_hash = hashlib.md5(file_path.encode()).hexdigest()

        for i in range(3):
            f = mesh_cache.cache_dir / f"entry{i}_{file_hash}.json"
            f.write_text(json.dumps({"i": i}).decode())

        count = mesh_cache.invalidate_by_file(file_path)
        assert count == 3

    # @trace TGNT-P9.2
    def test_invalidate_leaves_unrelated(self, mesh_cache: MeshCache) -> None:
        """Invalidation only removes matching files; others remain."""
        mesh_cache.set("keep_me", "important")

        file_path = "/other/path.py"
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        target = mesh_cache.cache_dir / f"{file_hash}.json"
        target.write_text(json.dumps({"remove": True}).decode())

        mesh_cache.invalidate_by_file(file_path)
        assert mesh_cache.get("keep_me") == "important"
