"""Direct tests for ``PolicyEngine.cache_stats`` (OPT-008 observability).

The OPT-008 decision cache (a ``cachetools.TTLCache``) was previously
opaque to operators: callers could read ``cache_size()`` but had no
way to assert cache wiring, hit rate, or reset state cleanly. This
suite pins the new ``cache_stats()`` observability surface so SOTA
tooling and operator dashboards can rely on the contract.

Coverage:

* Initial state: ``size=0``, ``hits=0``, ``misses=0``, ``hit_rate=0.0``.
* First ``evaluate`` is a miss, increments ``misses``.
* Repeated ``evaluate`` on the same context is a hit, increments
  ``hits`` and yields ``cached=True``.
* ``hit_rate`` is the canonical ``hits / total`` ratio.
* ``invalidate_cache`` resets both counters and clears the size.
* ``cache_stats`` snapshot is consistent (counter reads + size under
  the same ``_lock`` so a concurrent ``evaluate`` can't tear the view).
* Thread-safe snapshot: 8 readers + 4 writers firing ``evaluate``
  concurrently produce a snapshot where ``hits + misses`` matches
  the union of evaluations (no lost counters).
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from thegent.config.settings import ThegentSettings
from thegent.governance.policy_engine import PolicyContext, PolicyEngine

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings(tmp_path: Path) -> ThegentSettings:
    return ThegentSettings(environment="development", session_dir=tmp_path)


@pytest.fixture
def engine(settings: ThegentSettings) -> PolicyEngine:
    # Smaller cache so we can exercise eviction in a single test if needed.
    return PolicyEngine(settings=settings, use_federation=False, cache_maxsize=8)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestCacheStatsInitial:
    """A freshly-constructed engine has empty stats."""

    def test_initial_state_is_zero(self, engine: PolicyEngine) -> None:
        """Before any evaluate, all counters are zero and size is empty."""
        stats = engine.cache_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total"] == 0
        assert stats["hit_rate"] == 0.0

    def test_maxsize_matches_configured_ceiling(self, engine: PolicyEngine) -> None:
        """``maxsize`` mirrors the constructor's ``cache_maxsize`` kwarg."""
        assert engine.cache_stats()["maxsize"] == 8


# ---------------------------------------------------------------------------
# Miss + hit accounting
# ---------------------------------------------------------------------------


class TestCacheStatsMissHit:
    """Each evaluate bumps exactly one of ``hits`` or ``misses``."""

    def test_first_evaluate_is_miss(self, engine: PolicyEngine) -> None:
        """The first evaluate on a fresh context is a miss."""
        ctx = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        engine.evaluate(ctx)
        stats = engine.cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0
        assert stats["total"] == 1
        assert stats["hit_rate"] == 0.0

    def test_repeated_evaluate_is_hit(self, engine: PolicyEngine) -> None:
        """The second evaluate on the same context is a hit, returns ``cached=True``."""
        ctx = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        first = engine.evaluate(ctx)
        assert first.cached is False
        second = engine.evaluate(ctx)
        assert second.cached is True
        stats = engine.cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1
        assert stats["size"] == 1

    def test_hit_rate_two_hits_one_miss(self, engine: PolicyEngine) -> None:
        """``hit_rate`` is ``hits / total`` with floating-point precision."""
        ctx = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        engine.evaluate(ctx)  # miss
        engine.evaluate(ctx)  # hit
        engine.evaluate(ctx)  # hit
        stats = engine.cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 2
        assert stats["total"] == 3
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_distinct_contexts_each_count_miss(self, engine: PolicyEngine) -> None:
        """Two distinct contexts produce two misses, zero hits."""
        ctx_a = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        ctx_b = PolicyContext(agent="gemini", environment="development", confidence=0.95)
        engine.evaluate(ctx_a)
        engine.evaluate(ctx_b)
        stats = engine.cache_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0
        assert stats["size"] == 2


# ---------------------------------------------------------------------------
# Invalidate cache reset
# ---------------------------------------------------------------------------


class TestCacheStatsInvalidate:
    """``invalidate_cache`` resets state to a fresh observation window."""

    def test_invalidate_resets_counters(self, engine: PolicyEngine) -> None:
        """Counters reset; size clears."""
        ctx = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        for _ in range(5):
            engine.evaluate(ctx)  # 1 miss + 4 hits
        assert engine.cache_stats()["hits"] == 4
        assert engine.cache_stats()["misses"] == 1
        engine.invalidate_cache()
        stats = engine.cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0
        assert stats["hit_rate"] == 0.0

    def test_post_invalidate_first_evaluate_is_again_a_miss(
        self,
        engine: PolicyEngine,
    ) -> None:
        """After invalidate, the same context is a miss again."""
        ctx = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        engine.evaluate(ctx)
        engine.invalidate_cache()
        engine.evaluate(ctx)
        stats = engine.cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0


# ---------------------------------------------------------------------------
# Concurrent thread safety
# ---------------------------------------------------------------------------


class TestCacheStatsConcurrent:
    """Concurrent evaluate + stats snapshot is internally consistent."""

    def test_concurrent_evaluations_counters_match_invocations(
        self,
        engine: PolicyEngine,
    ) -> None:
        """8 reader threads + 4 writers → ``hits + misses`` matches invocations.

        Writers fire distinct contexts; readers re-evaluate the same
        context the writers populate. After joining all threads the
        snapshot's ``hits + misses`` equals the total number of
        ``engine.evaluate`` calls made.
        """
        ctx_writer_a = PolicyContext(agent="writer-a", environment="development", confidence=0.95)
        ctx_writer_b = PolicyContext(agent="writer-b", environment="development", confidence=0.95)
        # Pre-populate so the reader threads have something to hit.
        engine.evaluate(ctx_writer_a)
        engine.evaluate(ctx_writer_b)
        baseline_total = engine.cache_stats()["total"]
        assert baseline_total == 2

        readers = 8
        writers = 4
        iters = 50
        threading.Event()

        def reader_loop() -> None:
            for _ in range(iters):
                engine.evaluate(ctx_writer_a)

        def writer_loop() -> None:
            for i in range(iters):
                # Each writer hits distinct contexts; ``i`` varies the
                # prompt so the cache key changes per call (the prompt
                # is hashed into the key).
                engine.evaluate(
                    PolicyContext(
                        agent="writer-c",
                        environment="development",
                        confidence=0.95,
                        prompt=f"writer-c-{i}",
                    )
                )

        threads = [threading.Thread(target=reader_loop, name=f"reader-{i}") for i in range(readers)] + [
            threading.Thread(target=writer_loop, name=f"writer-{i}") for i in range(writers)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = engine.cache_stats()
        expected_total = baseline_total + readers * iters + writers * iters
        # ``hits + misses`` equals the exact number of evaluate calls.
        assert stats["total"] == expected_total
        # size is bounded by maxsize (8 writers × 50 prompts each >> 8).
        assert stats["size"] <= stats["maxsize"]


# ---------------------------------------------------------------------------
# Shape contract (so SOTA tooling can rely on it)
# ---------------------------------------------------------------------------


class TestCacheStatsShape:
    """The stats dict has the documented shape and is JSON-serialisable."""

    def test_keys_match_contract(self, engine: PolicyEngine) -> None:
        """The keys match the docstring contract."""
        stats = engine.cache_stats()
        assert set(stats.keys()) == {
            "size",
            "maxsize",
            "hits",
            "misses",
            "total",
            "hit_rate",
        }

    def test_is_json_serialisable(self, engine: PolicyEngine) -> None:
        """SOTA tooling JSON-serialises the snapshot for downstream consumers."""
        import json

        ctx = PolicyContext(agent="cursor", environment="development", confidence=0.95)
        engine.evaluate(ctx)
        engine.evaluate(ctx)
        # Must not raise.
        json.dumps(engine.cache_stats())
