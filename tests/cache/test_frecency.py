"""Tests for thegent.cache.frecency — FrecencyCache and FrecencyModelSelector.

FR traceability: FR-CACHE-002 (frecency algorithm for command/model/resource history)
"""

from __future__ import annotations

import math
import threading
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

# Module-level skip guard: tests require the optional `diskcache` dependency.
# Converting from `pytest.fail` to `pytest.importorskip` lets the file collect
# cleanly when diskcache is absent (CI may not always install every optional
# dep) while still skipping every test when diskcache is missing.
pytest.importorskip(
    "diskcache",
    reason="diskcache dependency is required for frecency persistence tests",
)

from thegent.cache.frecency import (
    FrecencyCache,
    FrecencyEntry,
    FrecencyModelSelector,
)
from thegent.cache.multi_level import _DISKCACHE_AVAILABLE, MultiLevelCache

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_past(seconds: float) -> datetime:
    """Return a UTC datetime that is *seconds* in the past."""
    return datetime.now(UTC) - timedelta(seconds=seconds)


def _expected_score(access_count: int, age_seconds: float, half_life: float) -> float:
    lam = math.log(2) / half_life
    return access_count * math.exp(-lam * age_seconds)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cache() -> FrecencyCache:
    """Return a small FrecencyCache with a 1-hour half-life."""
    return FrecencyCache(maxsize=10, half_life_seconds=3600.0)


@pytest.fixture
def two_level_storage(tmp_path: Path) -> MultiLevelCache:
    """Return a two-level MultiLevelCache backed by a temp directory."""
    storage = MultiLevelCache(l1_maxsize=100, l1_ttl=3600, l2_dir=tmp_path / "frecency_db", l2_ttl=86400)
    yield storage
    storage.close()


# ---------------------------------------------------------------------------
# FR-CACHE-002: FrecencyEntry dataclass
# ---------------------------------------------------------------------------


class TestFrecencyEntry:
    """FR-CACHE-002: FrecencyEntry behaves correctly."""

    def test_age_seconds_returns_zero_immediately(self) -> None:
        # @trace FR-CACHE-002
        now = datetime.now(UTC)
        entry = FrecencyEntry(key="k", score=0.0, access_count=1, last_access=now)
        assert entry.age_seconds(now) == 0.0

    def test_age_seconds_with_past_last_access(self) -> None:
        # @trace FR-CACHE-002
        last = _make_past(120)
        entry = FrecencyEntry(key="k", score=0.0, access_count=1, last_access=last)
        now = datetime.now(UTC)
        age = entry.age_seconds(now)
        assert 119.0 <= age <= 121.0

    def test_recalculate_score_formula(self) -> None:
        # @trace FR-CACHE-002
        # With age=0, score should equal access_count * 1.0
        now = datetime.now(UTC)
        entry = FrecencyEntry(key="k", score=0.0, access_count=5, last_access=now)
        score = entry.recalculate_score(half_life=3600.0, now=now)
        assert score == pytest.approx(5.0, rel=1e-9)

    def test_recalculate_score_decays_with_age(self) -> None:
        # @trace FR-CACHE-002
        last = _make_past(3600)  # exactly one half-life ago
        entry = FrecencyEntry(key="k", score=0.0, access_count=4, last_access=last)
        now = datetime.now(UTC)
        score = entry.recalculate_score(half_life=3600.0, now=now)
        # After one half-life, score ≈ 4 * 0.5 = 2.0
        assert score == pytest.approx(2.0, rel=0.01)

    def test_recalculate_score_mutates_entry(self) -> None:
        # @trace FR-CACHE-002
        now = datetime.now(UTC)
        entry = FrecencyEntry(key="k", score=0.0, access_count=3, last_access=now)
        new_score = entry.recalculate_score(half_life=3600.0, now=now)
        assert entry.score == new_score

    def test_created_defaults_to_now(self) -> None:
        # @trace FR-CACHE-002
        before = datetime.now(UTC)
        entry = FrecencyEntry(key="k", score=0.0, access_count=0, last_access=before)
        after = datetime.now(UTC)
        assert before <= entry.created <= after


# ---------------------------------------------------------------------------
# FR-CACHE-002: FrecencyCache — basic operations
# ---------------------------------------------------------------------------


class TestFrecencyCacheBasic:
    """FR-CACHE-002: FrecencyCache core behaviour."""

    def test_access_new_key_returns_positive_score(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        score = cache.access("cmd:ls")
        assert score > 0.0

    def test_score_unknown_key_returns_zero(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        assert cache.score("no-such-key") == 0.0

    def test_access_increments_count(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("k")
        cache.access("k")
        entry = cache.get_entry("k")
        assert entry is not None
        assert entry.access_count == 2

    def test_score_increases_with_each_access(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        s1 = cache.access("k")
        s2 = cache.access("k")
        s3 = cache.access("k")
        # Each access refreshes last_access to now, so score = count * 1 exactly
        assert s2 > s1
        assert s3 > s2

    def test_get_entry_returns_none_for_missing_key(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        assert cache.get_entry("ghost") is None

    def test_get_entry_returns_entry_after_access(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("present")
        entry = cache.get_entry("present")
        assert entry is not None
        assert entry.key == "present"

    def test_len_reflects_tracked_entries(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        assert len(cache) == 0
        cache.access("a")
        cache.access("b")
        assert len(cache) == 2

    def test_contains_returns_correct_bool(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("x")
        assert "x" in cache
        assert "y" not in cache

    def test_clear_removes_all_entries(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("a")
        cache.access("b")
        cache.clear()
        assert len(cache) == 0
        assert cache.score("a") == 0.0

    def test_invalid_maxsize_raises(self) -> None:
        # @trace FR-CACHE-002
        with pytest.raises(ValueError, match="maxsize"):
            FrecencyCache(maxsize=0)

    def test_invalid_half_life_raises(self) -> None:
        # @trace FR-CACHE-002
        with pytest.raises(ValueError, match="half_life"):
            FrecencyCache(half_life_seconds=0.0)


# ---------------------------------------------------------------------------
# FR-CACHE-002: Score decay over time
# ---------------------------------------------------------------------------


class TestFrecencyDecay:
    """FR-CACHE-002: Score decays correctly over time."""

    def test_score_decays_after_time_passes(self) -> None:
        # @trace FR-CACHE-002
        # Set last_access to 1 half-life ago; score should be ~half of access_count
        half_life = 100.0
        cache = FrecencyCache(maxsize=10, half_life_seconds=half_life)
        cache.access("k")
        entry = cache.get_entry("k")
        assert entry is not None

        # Manually move last_access backward by one half-life
        entry.last_access = _make_past(half_life)
        score_now = cache.score("k")
        # access_count=1, age=half_life → score ≈ 1 * 0.5 = 0.5
        assert score_now == pytest.approx(0.5, rel=0.05)

    def test_shorter_half_life_decays_faster(self) -> None:
        # @trace FR-CACHE-002
        age_seconds = 60.0
        cache_fast = FrecencyCache(maxsize=10, half_life_seconds=30.0)
        cache_slow = FrecencyCache(maxsize=10, half_life_seconds=3600.0)

        for cache in (cache_fast, cache_slow):
            cache.access("k")
            entry = cache.get_entry("k")
            assert entry is not None
            entry.last_access = _make_past(age_seconds)

        score_fast = cache_fast.score("k")
        score_slow = cache_slow.score("k")
        assert score_fast < score_slow

    def test_mock_datetime_controls_decay(self) -> None:
        # @trace FR-CACHE-002
        half_life = 1000.0
        cache = FrecencyCache(maxsize=10, half_life_seconds=half_life)

        fixed_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        past = fixed_now - timedelta(seconds=half_life)  # exactly 1 half-life ago

        with patch("thegent.cache.frecency._utcnow", return_value=fixed_now):
            cache.access("k")
            entry = cache.get_entry("k")
            assert entry is not None
            entry.last_access = past
            score = cache.score("k")

        # access_count=1, age=half_life → score ≈ 0.5
        assert score == pytest.approx(0.5, rel=0.01)


# ---------------------------------------------------------------------------
# FR-CACHE-002: top_n ordering
# ---------------------------------------------------------------------------


class TestTopN:
    """FR-CACHE-002: top_n returns correctly ordered entries."""

    def test_top_n_returns_highest_scoring(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("a")  # count=1
        for _ in range(3):
            cache.access("b")  # count=3
        for _ in range(2):
            cache.access("c")  # count=2

        top = cache.top_n(2)
        assert len(top) == 2
        assert top[0].key == "b"
        assert top[1].key == "c"

    def test_top_n_with_n_larger_than_entries(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("x")
        cache.access("y")
        top = cache.top_n(100)
        assert len(top) == 2

    def test_top_n_zero_returns_empty(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("x")
        assert cache.top_n(0) == []

    def test_top_n_descending_order(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        for i in range(5):
            for _ in range(i + 1):
                cache.access(f"key-{i}")
        top = cache.top_n(5)
        scores = [e.score for e in top]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_invalid_n_raises(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        with pytest.raises(ValueError, match="n must be"):
            cache.top_n(-1)


# ---------------------------------------------------------------------------
# FR-CACHE-002: evict_lowest
# ---------------------------------------------------------------------------


class TestEvictLowest:
    """FR-CACHE-002: evict_lowest removes the correct items."""

    def test_evict_lowest_removes_one(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("a")
        cache.access("b")
        cache.access("b")
        evicted = cache.evict_lowest(1)
        assert evicted == ["a"]
        assert "a" not in cache
        assert "b" in cache

    def test_evict_lowest_removes_n(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("lo")
        for _ in range(5):
            cache.access("hi")
        evicted = cache.evict_lowest(1)
        assert "lo" in evicted
        assert len(cache) == 1

    def test_evict_lowest_clamped_to_entry_count(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        cache.access("only")
        evicted = cache.evict_lowest(100)
        assert evicted == ["only"]
        assert len(cache) == 0

    def test_evict_lowest_empty_cache_returns_empty(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        assert cache.evict_lowest(3) == []

    def test_evict_lowest_invalid_n_raises(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        with pytest.raises(ValueError, match="n must be"):
            cache.evict_lowest(-1)


# ---------------------------------------------------------------------------
# FR-CACHE-002: maxsize eviction
# ---------------------------------------------------------------------------


class TestMaxsizeEviction:
    """FR-CACHE-002: LFU-style eviction when maxsize is reached."""

    def test_evicts_lowest_on_overflow(self) -> None:
        # @trace FR-CACHE-002
        # Build deterministic scores: popular(count=5) > medium(count=2) > rare(count=1)
        cache = FrecencyCache(maxsize=3, half_life_seconds=3600.0)
        for _ in range(5):
            cache.access("popular")
        for _ in range(2):
            cache.access("medium")
        cache.access("rare")
        # Cache is full (3 entries); adding a 4th key must evict "rare" (lowest score=1)
        cache.access("new-key")
        assert len(cache) == 3
        assert "rare" not in cache
        assert "popular" in cache

    def test_maxsize_one_always_replaces_on_new_key(self) -> None:
        # @trace FR-CACHE-002
        cache = FrecencyCache(maxsize=1, half_life_seconds=3600.0)
        cache.access("first")
        cache.access("second")  # should evict "first"
        assert len(cache) == 1


# ---------------------------------------------------------------------------
# FR-CACHE-002: Persistence via MultiLevelCache
# ---------------------------------------------------------------------------


class TestPersistence:
    """FR-CACHE-002: Frecency data survives via MultiLevelCache persistence."""

    def test_entry_persisted_on_access(self, two_level_storage: MultiLevelCache) -> None:
        # @trace FR-CACHE-002
        cache = FrecencyCache(maxsize=10, half_life_seconds=3600.0, storage=two_level_storage)
        cache.access("model-x")
        payload = two_level_storage.get("frecency:model-x")
        assert payload is not None
        assert payload["key"] == "model-x"
        assert payload["access_count"] == 1

    def test_entry_restored_from_storage_on_new_cache(self, two_level_storage: MultiLevelCache) -> None:
        # @trace FR-CACHE-002
        cache1 = FrecencyCache(maxsize=10, half_life_seconds=3600.0, storage=two_level_storage)
        for _ in range(4):
            cache1.access("model-y")

        # New cache instance — should restore from storage on first access
        cache2 = FrecencyCache(maxsize=10, half_life_seconds=3600.0, storage=two_level_storage)
        score = cache2.score("model-y")
        entry = cache2.get_entry("model-y")
        assert entry is not None
        assert entry.access_count == 4
        assert score > 0.0

    def test_clear_removes_persisted_entries(self, two_level_storage: MultiLevelCache) -> None:
        # @trace FR-CACHE-002
        cache = FrecencyCache(maxsize=10, half_life_seconds=3600.0, storage=two_level_storage)
        cache.access("model-z")
        cache.clear()
        assert two_level_storage.get("frecency:model-z") is None

    def test_evict_lowest_removes_from_storage(self, two_level_storage: MultiLevelCache) -> None:
        # @trace FR-CACHE-002
        cache = FrecencyCache(maxsize=10, half_life_seconds=3600.0, storage=two_level_storage)
        cache.access("lo")
        for _ in range(5):
            cache.access("hi")
        cache.evict_lowest(1)
        assert two_level_storage.get("frecency:lo") is None
        assert two_level_storage.get("frecency:hi") is not None


# ---------------------------------------------------------------------------
# FR-CACHE-002: Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """FR-CACHE-002: Concurrent accesses do not corrupt state."""

    def test_concurrent_access_does_not_corrupt(self, cache: FrecencyCache) -> None:
        # @trace FR-CACHE-002
        errors: list[Exception] = []

        def worker(key: str) -> None:
            try:
                for _ in range(20):
                    cache.access(key)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(f"key-{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert len(cache) <= cache.maxsize


# ---------------------------------------------------------------------------
# FR-CACHE-002: FrecencyModelSelector
# ---------------------------------------------------------------------------


class TestFrecencyModelSelector:
    """FR-CACHE-002: FrecencyModelSelector selects models by frecency."""

    def test_preferred_model_returns_most_used(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        sel.record_use("claude-sonnet-4-5")
        sel.record_use("claude-sonnet-4-5")
        sel.record_use("gemini-3-flash")
        best = sel.preferred_model(["claude-sonnet-4-5", "gemini-3-flash"])
        assert best == "claude-sonnet-4-5"

    def test_preferred_model_empty_candidates_returns_none(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        assert sel.preferred_model([]) is None

    def test_preferred_model_unknown_candidates_returns_candidate(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        # All have score 0 — max picks one deterministically
        result = sel.preferred_model(["a", "b", "c"])
        assert result in {"a", "b", "c"}

    def test_top_models_returns_n_ids(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        sel.record_use("model-a")
        sel.record_use("model-b")
        sel.record_use("model-b")
        sel.record_use("model-c")
        top = sel.top_models(2)
        assert len(top) == 2
        assert top[0] == "model-b"

    def test_score_returns_float(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        sel.record_use("m")
        assert isinstance(sel.score("m"), float)
        assert sel.score("m") > 0

    def test_cache_property_exposes_inner_cache(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        assert isinstance(sel.cache, FrecencyCache)

    def test_record_use_returns_increasing_score(self) -> None:
        # @trace FR-CACHE-002
        sel = FrecencyModelSelector()
        s1 = sel.record_use("m")
        s2 = sel.record_use("m")
        s3 = sel.record_use("m")
        assert s3 > s2 > s1

    @pytest.mark.skipif(not _DISKCACHE_AVAILABLE, reason="diskcache not installed")
    def test_model_selector_with_storage_backend(self, tmp_path: Path) -> None:
        # @trace FR-CACHE-002
        storage = MultiLevelCache(l1_maxsize=50, l1_ttl=3600, l2_dir=tmp_path / "sel_db", l2_ttl=86400)
        try:
            sel = FrecencyModelSelector(storage=storage)
            for _ in range(3):
                sel.record_use("preferred-model")
            sel.record_use("other-model")
            assert sel.preferred_model(["preferred-model", "other-model"]) == "preferred-model"
        finally:
            storage.close()


# ---------------------------------------------------------------------------
# FR-CACHE-002: Half-life parameter effect
# ---------------------------------------------------------------------------


class TestHalfLifeEffect:
    """FR-CACHE-002: half_life_seconds controls decay rate correctly."""

    def test_half_life_property_exposed(self) -> None:
        # @trace FR-CACHE-002
        cache = FrecencyCache(maxsize=10, half_life_seconds=500.0)
        assert cache.half_life == 500.0

    def test_maxsize_property_exposed(self) -> None:
        # @trace FR-CACHE-002
        cache = FrecencyCache(maxsize=42, half_life_seconds=100.0)
        assert cache.maxsize == 42

    def test_large_half_life_preserves_score_longer(self) -> None:
        # @trace FR-CACHE-002
        age = 300.0  # 5 minutes
        cache_short = FrecencyCache(maxsize=5, half_life_seconds=60.0)
        cache_long = FrecencyCache(maxsize=5, half_life_seconds=86400.0)

        for c in (cache_short, cache_long):
            c.access("k")
            entry = c.get_entry("k")
            assert entry is not None
            entry.last_access = _make_past(age)

        assert cache_short.score("k") < cache_long.score("k")
