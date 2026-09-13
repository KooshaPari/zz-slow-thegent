"""Tests for GW-60: EWMA latency tracking.

# @trace FR-AROUTE-060
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.latency_tracker import (
    EWMAConfig,
    EWMALatencyTracker,
    get_latency_tracker,
    reset_latency_tracker,
)


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the singleton before each test."""
    reset_latency_tracker()
    yield
    reset_latency_tracker()


@pytest.mark.requirement("FR-AROUTE-060")
class TestEWMALatencyTracker:
    def test_latency_tracker_initial_returns_default(self) -> None:
        tracker = EWMALatencyTracker()
        result = tracker.get_latency("openai", "gpt-4o")
        assert result == 1000.0  # default initial_latency_ms

    def test_latency_tracker_initial_custom_config(self) -> None:
        config = EWMAConfig(initial_latency_ms=500.0)
        tracker = EWMALatencyTracker(config=config)
        result = tracker.get_latency("anthropic", "claude-3")
        assert result == 500.0

    def test_latency_tracker_record_and_get(self) -> None:
        tracker = EWMALatencyTracker()
        tracker.record("openai", "gpt-4o", 200.0)
        result = tracker.get_latency("openai", "gpt-4o")
        # First sample: ewma = 200.0
        assert result == 200.0

    def test_latency_tracker_ewma_converges(self) -> None:
        config = EWMAConfig(alpha=0.5, initial_latency_ms=1000.0)
        tracker = EWMALatencyTracker(config=config)
        # Feed in consistent low latency — EWMA should converge downward
        for _ in range(20):
            tracker.record("openai", "gpt-4o", 100.0)
        result = tracker.get_latency("openai", "gpt-4o")
        # After 20 samples of 100ms with alpha=0.5, EWMA should be very close to 100
        assert result < 110.0

    def test_latency_tracker_ewma_formula(self) -> None:
        config = EWMAConfig(alpha=0.3, initial_latency_ms=1000.0)
        tracker = EWMALatencyTracker(config=config)
        # First record: ewma = 400.0 (sets to sample directly)
        tracker.record("openai", "gpt-4o", 400.0)
        # Second record: ewma = 0.3 * 200.0 + 0.7 * 400.0 = 60 + 280 = 340
        tracker.record("openai", "gpt-4o", 200.0)
        result = tracker.get_latency("openai", "gpt-4o")
        assert abs(result - 340.0) < 0.01

    def test_latency_tracker_rank_by_latency(self) -> None:
        tracker = EWMALatencyTracker()
        tracker.record("openai", "gpt-4o", 300.0)
        tracker.record("anthropic", "claude-3", 100.0)
        tracker.record("google", "gemini-pro", 200.0)

        candidates = [
            ("openai", "gpt-4o"),
            ("anthropic", "claude-3"),
            ("google", "gemini-pro"),
        ]
        ranked = tracker.rank_by_latency(candidates)

        assert ranked[0] == ("anthropic", "claude-3")
        assert ranked[1] == ("google", "gemini-pro")
        assert ranked[2] == ("openai", "gpt-4o")

    def test_latency_tracker_rank_unknown_uses_default(self) -> None:
        config = EWMAConfig(initial_latency_ms=500.0)
        tracker = EWMALatencyTracker(config=config)
        tracker.record("fast-provider", "model-a", 50.0)

        candidates = [("unknown-provider", "model-x"), ("fast-provider", "model-a")]
        ranked = tracker.rank_by_latency(candidates)

        assert ranked[0] == ("fast-provider", "model-a")
        assert ranked[1] == ("unknown-provider", "model-x")

    def test_latency_tracker_separate_keys_per_provider_model(self) -> None:
        tracker = EWMALatencyTracker()
        tracker.record("openai", "gpt-4o", 100.0)
        tracker.record("openai", "gpt-4o-mini", 50.0)

        assert tracker.get_latency("openai", "gpt-4o") == 100.0
        assert tracker.get_latency("openai", "gpt-4o-mini") == 50.0

    def test_latency_tracker_rank_empty_candidates(self) -> None:
        tracker = EWMALatencyTracker()
        result = tracker.rank_by_latency([])
        assert result == []


@pytest.mark.requirement("FR-AROUTE-060")
class TestSingleton:
    def test_singleton_returns_same_instance(self) -> None:
        t1 = get_latency_tracker()
        t2 = get_latency_tracker()
        assert t1 is t2

    def test_singleton_reset_creates_new(self) -> None:
        t1 = get_latency_tracker()
        reset_latency_tracker()
        t2 = get_latency_tracker()
        assert t1 is not t2

    def test_singleton_is_ewma_tracker(self) -> None:
        tracker = get_latency_tracker()
        assert isinstance(tracker, EWMALatencyTracker)

    def test_singleton_persists_data(self) -> None:
        tracker = get_latency_tracker()
        tracker.record("openai", "gpt-4o", 123.0)
        same_tracker = get_latency_tracker()
        assert same_tracker.get_latency("openai", "gpt-4o") == 123.0
