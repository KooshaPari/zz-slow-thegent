"""Tests for thegent.cache.pre_warmer — CachePreWarmer and WarmingStrategy.

FR traceability: FR-CACHE-003 (predictive pre-warming based on usage patterns)
"""

from __future__ import annotations

import threading
import time
from datetime import timedelta

import pytest

from thegent.cache.multi_level import MultiLevelCache
from thegent.cache.pre_warmer import (
    CachePreWarmer,
    WarmingStrategy,
    _should_run,
    _utcnow,
    model_list_strategy,
    session_list_strategy,
)

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_cache() -> MultiLevelCache:
    """Return a simple L1-only cache for testing."""
    return MultiLevelCache(l1_maxsize=100, l1_ttl=300)


def _noop_load(key: str) -> str:
    """Simple load function that returns a value based on the key."""
    return f"value:{key}"


def _always_fail_load(_key: str) -> str:
    raise RuntimeError("simulated load failure")


def _make_strategy(
    name: str = "test",
    keys: list[str] | None = None,
    load_fn=_noop_load,
    schedule_seconds: float = 300.0,
) -> WarmingStrategy:
    """Build a WarmingStrategy with simple defaults."""
    if keys is None:
        keys = ["k1", "k2"]
    frozen = list(keys)
    return WarmingStrategy(
        name=name,
        predict_fn=lambda: frozen,
        load_fn=load_fn,
        schedule_seconds=schedule_seconds,
    )


@pytest.fixture
def cache() -> MultiLevelCache:
    """Return an L1-only MultiLevelCache."""
    return _make_cache()


@pytest.fixture
def warmer(cache: MultiLevelCache) -> CachePreWarmer:
    """Return a CachePreWarmer backed by *cache*."""
    return CachePreWarmer(cache)


# ---------------------------------------------------------------------------
# WarmingStrategy validation
# ---------------------------------------------------------------------------


class TestWarmingStrategyValidation:
    """FR-CACHE-003: WarmingStrategy rejects invalid configuration."""

    def test_empty_name_raises(self) -> None:
        # @trace FR-CACHE-003
        with pytest.raises(ValueError, match="name must not be empty"):
            WarmingStrategy(
                name="",
                predict_fn=list,
                load_fn=_noop_load,
            )

    def test_zero_schedule_raises(self) -> None:
        # @trace FR-CACHE-003
        with pytest.raises(ValueError, match="schedule_seconds must be positive"):
            WarmingStrategy(
                name="bad",
                predict_fn=list,
                load_fn=_noop_load,
                schedule_seconds=0.0,
            )

    def test_negative_schedule_raises(self) -> None:
        # @trace FR-CACHE-003
        with pytest.raises(ValueError, match="schedule_seconds must be positive"):
            WarmingStrategy(
                name="bad",
                predict_fn=list,
                load_fn=_noop_load,
                schedule_seconds=-1.0,
            )

    def test_valid_strategy_constructs(self) -> None:
        # @trace FR-CACHE-003
        s = _make_strategy()
        assert s.name == "test"
        assert s.schedule_seconds == 300.0

    def test_default_schedule_seconds(self) -> None:
        # @trace FR-CACHE-003
        s = WarmingStrategy(name="x", predict_fn=list, load_fn=_noop_load)
        assert s.schedule_seconds == 300.0


# ---------------------------------------------------------------------------
# register_strategy / unregister_strategy
# ---------------------------------------------------------------------------


class TestRegisterStrategy:
    """FR-CACHE-003: register_strategy correctly manages strategy set."""

    def test_register_adds_strategy(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        s = _make_strategy("alpha")
        warmer.register_strategy(s)
        stats = warmer.get_stats()
        assert stats["strategies"] == 1

    def test_register_two_strategies(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("a"))
        warmer.register_strategy(_make_strategy("b"))
        stats = warmer.get_stats()
        assert stats["strategies"] == 2

    def test_register_replaces_existing_name(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("dup"))
        warmer.register_strategy(_make_strategy("dup"))
        assert warmer.get_stats()["strategies"] == 1

    def test_unregister_removes_strategy(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("alpha"))
        removed = warmer.unregister_strategy("alpha")
        assert removed is True
        assert warmer.get_stats()["strategies"] == 0

    def test_unregister_missing_returns_false(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        assert warmer.unregister_strategy("nonexistent") is False


# ---------------------------------------------------------------------------
# warm_key
# ---------------------------------------------------------------------------


class TestWarmKey:
    """FR-CACHE-003: warm_key fetches data and stores it in cache."""

    def test_warm_key_stores_value_in_cache(self, warmer: CachePreWarmer, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        result = warmer.warm_key("mykey", lambda: "myvalue")
        assert result is True
        assert cache.get("mykey") == "myvalue"

    def test_warm_key_returns_false_on_none(self, warmer: CachePreWarmer, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        result = warmer.warm_key("k", lambda: None)
        assert result is False
        assert cache.get("k") is None

    def test_warm_key_returns_false_on_exception(self, warmer: CachePreWarmer, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        def bad_load() -> str:
            raise ValueError("boom")

        result = warmer.warm_key("k", bad_load)
        assert result is False
        assert cache.get("k") is None

    def test_warm_key_increments_total_warm_count(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.warm_key("k1", lambda: "v1")
        warmer.warm_key("k2", lambda: "v2")
        assert warmer.get_stats()["warm_count"] == 2

    def test_warm_key_failed_does_not_increment_count(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.warm_key("k", lambda: None)
        assert warmer.get_stats()["warm_count"] == 0


# ---------------------------------------------------------------------------
# warm_all
# ---------------------------------------------------------------------------


class TestWarmAll:
    """FR-CACHE-003: warm_all runs all strategies and returns per-key results."""

    def test_warm_all_empty_strategies_returns_empty(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        results = warmer.warm_all()
        assert results == {}

    def test_warm_all_single_strategy(self, warmer: CachePreWarmer, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("s", keys=["k1", "k2"]))
        results = warmer.warm_all()
        assert results == {"k1": True, "k2": True}
        assert cache.get("k1") == "value:k1"
        assert cache.get("k2") == "value:k2"

    def test_warm_all_two_strategies(self, warmer: CachePreWarmer, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("s1", keys=["a"]))
        warmer.register_strategy(_make_strategy("s2", keys=["b"]))
        results = warmer.warm_all()
        assert "a" in results
        assert "b" in results
        assert results["a"] is True
        assert results["b"] is True

    def test_warm_all_failing_load_fn_records_false(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("s", keys=["k"], load_fn=_always_fail_load))
        results = warmer.warm_all()
        assert results["k"] is False

    def test_warm_all_predict_fn_exception_skips_strategy(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        def bad_predict() -> list[str]:
            raise RuntimeError("predict error")

        warmer.register_strategy(WarmingStrategy(name="bad", predict_fn=bad_predict, load_fn=_noop_load))
        results = warmer.warm_all()
        assert results == {}

    def test_warm_all_updates_last_run(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        assert warmer.get_stats()["last_run"] is None
        warmer.warm_all()
        assert warmer.get_stats()["last_run"] is not None

    def test_warm_all_calls_load_fn_with_correct_key(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        captured: list[str] = []

        def track_load(key: str) -> str:
            captured.append(key)
            return f"v:{key}"

        warmer.register_strategy(_make_strategy("s", keys=["x", "y"], load_fn=track_load))
        warmer.warm_all()
        assert captured == ["x", "y"]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestGetStats:
    """FR-CACHE-003: get_stats returns correct snapshot."""

    def test_initial_stats(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        stats = warmer.get_stats()
        assert stats["strategies"] == 0
        assert stats["warm_count"] == 0
        assert stats["last_run"] is None
        assert stats["background_running"] is False
        assert stats["strategy_stats"] == []

    def test_stats_after_register(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("alpha"))
        stats = warmer.get_stats()
        assert stats["strategies"] == 1
        assert stats["strategy_stats"][0]["name"] == "alpha"

    def test_stats_strategy_warm_count(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("s", keys=["k1", "k2"]))
        warmer.warm_all()
        s_stats = warmer.get_stats()["strategy_stats"][0]
        assert s_stats["warm_count"] == 2
        assert s_stats["error_count"] == 0

    def test_stats_strategy_error_count_on_failure(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("s", keys=["k"], load_fn=_always_fail_load))
        warmer.warm_all()
        s_stats = warmer.get_stats()["strategy_stats"][0]
        assert s_stats["error_count"] == 1
        assert s_stats["warm_count"] == 0

    def test_stats_strategy_last_run_set_after_warm_all(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.register_strategy(_make_strategy("s"))
        warmer.warm_all()
        s_stats = warmer.get_stats()["strategy_stats"][0]
        assert s_stats["last_run"] is not None


# ---------------------------------------------------------------------------
# Background daemon
# ---------------------------------------------------------------------------


class TestBackgroundDaemon:
    """FR-CACHE-003: background daemon starts, warms, and stops correctly."""

    def test_start_background_sets_is_running(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        try:
            warmer.start_background()
            assert warmer.is_running is True
        finally:
            warmer.stop_background()

    def test_stop_background_clears_is_running(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        warmer.start_background()
        stopped = warmer.stop_background(timeout=3.0)
        assert stopped is True
        assert warmer.is_running is False

    def test_start_background_idempotent(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003 — calling start_background twice is safe
        try:
            warmer.start_background()
            warmer.start_background()  # should be a no-op
            assert warmer.is_running is True
        finally:
            warmer.stop_background()

    def test_stop_background_without_start_returns_true(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        result = warmer.stop_background()
        assert result is True

    def test_background_daemon_warms_keys(self, warmer: CachePreWarmer, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003 — daemon runs strategies with schedule_seconds=0 quickly
        warmer.register_strategy(_make_strategy("s", keys=["bg_k1"], schedule_seconds=0.01))
        warmer.start_background()
        # Give daemon 2 seconds to fire at least once
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if cache.get("bg_k1") is not None:
                break
            time.sleep(0.05)
        warmer.stop_background()
        assert cache.get("bg_k1") == "value:bg_k1"

    def test_background_stats_background_running_field(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        assert warmer.get_stats()["background_running"] is False
        warmer.start_background()
        try:
            assert warmer.get_stats()["background_running"] is True
        finally:
            warmer.stop_background()


# ---------------------------------------------------------------------------
# _should_run helper
# ---------------------------------------------------------------------------


class TestShouldRun:
    """FR-CACHE-003: _should_run correctly computes due-for-run state."""

    def test_returns_true_when_last_run_is_none(self) -> None:
        # @trace FR-CACHE-003
        from thegent.cache.pre_warmer import _StrategyState

        state = _StrategyState(strategy=_make_strategy())
        assert _should_run(state, _utcnow()) is True

    def test_returns_false_when_run_recently(self) -> None:
        # @trace FR-CACHE-003
        from thegent.cache.pre_warmer import _StrategyState

        state = _StrategyState(strategy=_make_strategy(schedule_seconds=300.0))
        state.last_run = _utcnow()
        assert _should_run(state, _utcnow()) is False

    def test_returns_true_when_elapsed_exceeds_schedule(self) -> None:
        # @trace FR-CACHE-003
        from thegent.cache.pre_warmer import _StrategyState

        state = _StrategyState(strategy=_make_strategy(schedule_seconds=1.0))
        state.last_run = _utcnow() - timedelta(seconds=2)
        assert _should_run(state, _utcnow()) is True


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------


class TestBuiltInStrategies:
    """FR-CACHE-003: model_list_strategy and session_list_strategy are correct."""

    def test_model_list_strategy_default_keys(self) -> None:
        # @trace FR-CACHE-003
        s = model_list_strategy(load_fn=_noop_load)
        assert s.name == "model_list"
        keys = s.predict_fn()
        assert "models:list" in keys
        assert "models:available" in keys

    def test_model_list_strategy_custom_keys(self) -> None:
        # @trace FR-CACHE-003
        s = model_list_strategy(load_fn=_noop_load, model_keys=["models:custom"])
        assert s.predict_fn() == ["models:custom"]

    def test_model_list_strategy_custom_schedule(self) -> None:
        # @trace FR-CACHE-003
        s = model_list_strategy(load_fn=_noop_load, schedule_seconds=60.0)
        assert s.schedule_seconds == 60.0

    def test_session_list_strategy_default_keys(self) -> None:
        # @trace FR-CACHE-003
        s = session_list_strategy(load_fn=_noop_load)
        assert s.name == "session_list"
        keys = s.predict_fn()
        assert "sessions:active" in keys
        assert "sessions:recent" in keys

    def test_session_list_strategy_custom_keys(self) -> None:
        # @trace FR-CACHE-003
        s = session_list_strategy(load_fn=_noop_load, session_keys=["sessions:mine"])
        assert s.predict_fn() == ["sessions:mine"]

    def test_model_list_strategy_warms_cache(self, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        warmer = CachePreWarmer(cache)
        warmer.register_strategy(
            model_list_strategy(
                load_fn=lambda key: f"data:{key}",
                model_keys=["models:test"],
            )
        )
        results = warmer.warm_all()
        assert results.get("models:test") is True
        assert cache.get("models:test") == "data:models:test"

    def test_session_list_strategy_warms_cache(self, cache: MultiLevelCache) -> None:
        # @trace FR-CACHE-003
        warmer = CachePreWarmer(cache)
        warmer.register_strategy(
            session_list_strategy(
                load_fn=lambda key: f"data:{key}",
                session_keys=["sessions:test"],
            )
        )
        results = warmer.warm_all()
        assert results.get("sessions:test") is True
        assert cache.get("sessions:test") == "data:sessions:test"


# ---------------------------------------------------------------------------
# Thread safety / concurrent registration
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """FR-CACHE-003: concurrent registrations and warm_all calls are safe."""

    def test_concurrent_register_and_warm(self, warmer: CachePreWarmer) -> None:
        # @trace FR-CACHE-003
        errors: list[Exception] = []

        def register_and_warm(idx: int) -> None:
            try:
                name = f"strategy_{idx}"
                warmer.register_strategy(_make_strategy(name, keys=[f"k{idx}"]))
                warmer.warm_all()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=register_and_warm, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert errors == [], f"Thread errors: {errors}"
