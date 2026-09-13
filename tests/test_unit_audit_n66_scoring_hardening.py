"""AUDIT-N+66 — scoring.py hardening.

Pins the post-AUDIT-N+66 contract surface for the provider scoring
module. Every public class, constant, method dispatch, normalization
formula, clamping boundary, and composite-score invariant is covered
by an isolated test.

Items covered (FR-GOV-SCR-001 .. FR-GOV-SCR-025):

* 001 — ProviderMetrics field types
* 002 — ProviderMetrics default sample_size
* 003 — ProviderScore field types
* 004 — ProviderScore timestamp is set on construction
* 005 — ProviderScorer is abstract (cannot instantiate)
* 006 — DefaultProviderScorer.RELIABILITY_WEIGHT == 0.4
* 007 — DefaultProviderScorer.LATENCY_WEIGHT == 0.2
* 008 — DefaultProviderScorer.COST_WEIGHT == 0.4
* 009 — DefaultProviderScorer.BASELINE_LATENCY_MS == 250.0
* 010 — DefaultProviderScorer.BASELINE_COST_PER_1M == 0.15
* 011 — normalize() dispatches 'reliability'
* 012 — normalize() dispatches 'latency'
* 013 — normalize() dispatches 'cost'
* 014 — normalize() raises ValueError for unknown type
* 015 — normalize() is case-insensitive
* 016 — _normalize_reliability(1.0) == 10.0
* 017 — _normalize_reliability(0.5) == 5.0
* 018 — _normalize_reliability clamped to [0, 10]
* 019 — _normalize_latency baseline == 5.0
* 020 — _normalize_latency negative == 10.0
* 021 — _normalize_cost baseline == 5.0
* 022 — composite_score correctness (weighted average)
* 023 — all scores in [0.0, 10.0] range
* 024 — score() returns ProviderScore with correct provider_id
* 025 — ProviderScore ordering by composite_score
"""

from __future__ import annotations

from abc import ABC

import pytest

from thegent.governance.scoring import (
    DefaultProviderScorer,
    ProviderMetrics,
    ProviderScorer,
)


def _metrics(
    *,
    provider_id: str = "openai",
    reliability: float = 0.95,
    latency_p99: float = 200.0,
    cost_per_1m_tokens: float = 0.10,
) -> ProviderMetrics:
    return ProviderMetrics(
        provider_id=provider_id,
        reliability=reliability,
        latency_p99=latency_p99,
        cost_per_1m_tokens=cost_per_1m_tokens,
    )


# ---------------------------------------------------------------------------
# FR-GOV-SCR-001 — ProviderMetrics field types
# ---------------------------------------------------------------------------


class TestFRGOOSCR001ProviderMetricsFieldTypes:
    """ProviderMetrics fields must be the correct types."""

    def test_field_types(self) -> None:
        m = _metrics()
        assert isinstance(m.provider_id, str)
        assert isinstance(m.reliability, float)
        assert isinstance(m.latency_p99, float)
        assert isinstance(m.cost_per_1m_tokens, float)
        assert isinstance(m.last_updated, float)
        assert isinstance(m.sample_size, int)


# ---------------------------------------------------------------------------
# FR-GOV-SCR-002 — ProviderMetrics default sample_size
# ---------------------------------------------------------------------------


class TestFRGOOSCR002ProviderMetricsDefaultSampleSize:
    """ProviderMetrics.sample_size defaults to 1000."""

    def test_default_sample_size(self) -> None:
        m = _metrics()
        assert m.sample_size == 1000


# ---------------------------------------------------------------------------
# FR-GOV-SCR-003 — ProviderScore field types
# ---------------------------------------------------------------------------


class TestFRGOOSCR003ProviderScoreFieldTypes:
    """ProviderScore fields must be the correct types."""

    def test_field_types(self) -> None:
        scorer = DefaultProviderScorer()
        score = scorer.score(_metrics())
        assert isinstance(score.provider_id, str)
        assert isinstance(score.reliability_score, float)
        assert isinstance(score.latency_score, float)
        assert isinstance(score.cost_score, float)
        assert isinstance(score.composite_score, float)
        assert isinstance(score.timestamp, float)


# ---------------------------------------------------------------------------
# FR-GOV-SCR-004 — ProviderScore timestamp is set
# ---------------------------------------------------------------------------


class TestFRGOOSCR004ProviderScoreTimestampIsSet:
    """ProviderScore.timestamp must be a positive float (non-default)."""

    def test_timestamp_is_set(self) -> None:
        scorer = DefaultProviderScorer()
        score = scorer.score(_metrics())
        assert score.timestamp > 0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-005 — ProviderScorer is abstract
# ---------------------------------------------------------------------------


class TestFRGOOSCR005ProviderScorerIsAbstract:
    """ProviderScorer cannot be instantiated directly."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            ProviderScorer()  # type: ignore[abstract]

    def test_is_abc_subclass(self) -> None:
        assert issubclass(ProviderScorer, ABC)


# ---------------------------------------------------------------------------
# FR-GOV-SCR-006 — RELIABILITY_WEIGHT == 0.4
# ---------------------------------------------------------------------------


class TestFRGOOSCR006ReliabilityWeight:
    """DefaultProviderScorer.RELIABILITY_WEIGHT must equal 0.4."""

    def test_value(self) -> None:
        assert DefaultProviderScorer.RELIABILITY_WEIGHT == 0.4


# ---------------------------------------------------------------------------
# FR-GOV-SCR-007 — LATENCY_WEIGHT == 0.2
# ---------------------------------------------------------------------------


class TestFRGOOSCR007LatencyWeight:
    """DefaultProviderScorer.LATENCY_WEIGHT must equal 0.2."""

    def test_value(self) -> None:
        assert DefaultProviderScorer.LATENCY_WEIGHT == 0.2


# ---------------------------------------------------------------------------
# FR-GOV-SCR-008 — COST_WEIGHT == 0.4
# ---------------------------------------------------------------------------


class TestFRGOOSCR008CostWeight:
    """DefaultProviderScorer.COST_WEIGHT must equal 0.4."""

    def test_value(self) -> None:
        assert DefaultProviderScorer.COST_WEIGHT == 0.4


# ---------------------------------------------------------------------------
# FR-GOV-SCR-009 — BASELINE_LATENCY_MS == 250.0
# ---------------------------------------------------------------------------


class TestFRGOOSCR009BaselineLatencyMs:
    """DefaultProviderScorer.BASELINE_LATENCY_MS must equal 250.0."""

    def test_value(self) -> None:
        assert DefaultProviderScorer.BASELINE_LATENCY_MS == 250.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-010 — BASELINE_COST_PER_1M == 0.15
# ---------------------------------------------------------------------------


class TestFRGOOSCR010BaselineCostPer1m:
    """DefaultProviderScorer.BASELINE_COST_PER_1M must equal 0.15."""

    def test_value(self) -> None:
        assert DefaultProviderScorer.BASELINE_COST_PER_1M == 0.15


# ---------------------------------------------------------------------------
# FR-GOV-SCR-011 — normalize() dispatches 'reliability'
# ---------------------------------------------------------------------------


class TestFRGOOSCR011NormalizeDispatchesReliability:
    """normalize() with metric_type='reliability' delegates to
    _normalize_reliability."""

    def test_dispatch(self) -> None:
        scorer = DefaultProviderScorer()
        result = scorer.normalize(0.8, "reliability")
        expected = scorer._normalize_reliability(0.8)
        assert result == expected


# ---------------------------------------------------------------------------
# FR-GOV-SCR-012 — normalize() dispatches 'latency'
# ---------------------------------------------------------------------------


class TestFRGOOSCR012NormalizeDispatchesLatency:
    """normalize() with metric_type='latency' delegates to
    _normalize_latency."""

    def test_dispatch(self) -> None:
        scorer = DefaultProviderScorer()
        result = scorer.normalize(300.0, "latency")
        expected = scorer._normalize_latency(300.0)
        assert result == expected


# ---------------------------------------------------------------------------
# FR-GOV-SCR-013 — normalize() dispatches 'cost'
# ---------------------------------------------------------------------------


class TestFRGOOSCR013NormalizeDispatchesCost:
    """normalize() with metric_type='cost' delegates to _normalize_cost."""

    def test_dispatch(self) -> None:
        scorer = DefaultProviderScorer()
        result = scorer.normalize(0.20, "cost")
        expected = scorer._normalize_cost(0.20)
        assert result == expected


# ---------------------------------------------------------------------------
# FR-GOV-SCR-014 — normalize() raises ValueError for unknown type
# ---------------------------------------------------------------------------


class TestFRGOOSCR014NormalizeRaisesForUnknownType:
    """normalize() with an unknown metric_type raises ValueError."""

    def test_raises_value_error(self) -> None:
        scorer = DefaultProviderScorer()
        with pytest.raises(ValueError, match="Unknown metric type"):
            scorer.normalize(1.0, "throughput")


# ---------------------------------------------------------------------------
# FR-GOV-SCR-015 — normalize() is case-insensitive
# ---------------------------------------------------------------------------


class TestFRGOOSCR015NormalizeCaseInsensitive:
    """normalize() treats metric_type as case-insensitive."""

    def test_uppercase(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer.normalize(0.5, "RELIABILITY") == scorer.normalize(0.5, "reliability")

    def test_mixed_case(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer.normalize(200.0, "Latency") == scorer.normalize(200.0, "latency")

    def test_title_case(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer.normalize(0.10, "Cost") == scorer.normalize(0.10, "cost")


# ---------------------------------------------------------------------------
# FR-GOV-SCR-016 — _normalize_reliability(1.0) == 10.0
# ---------------------------------------------------------------------------


class TestFRGOOSCR016NormalizeReliabilityMax:
    """_normalize_reliability(1.0) must return 10.0."""

    def test_perfect_reliability(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_reliability(1.0) == 10.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-017 — _normalize_reliability(0.5) == 5.0
# ---------------------------------------------------------------------------


class TestFRGOOSCR017NormalizeReliabilityMidpoint:
    """_normalize_reliability(0.5) must return 5.0."""

    def test_half_reliability(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_reliability(0.5) == 5.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-018 — _normalize_reliability clamped [0, 10]
# ---------------------------------------------------------------------------


class TestFRGOOSCR018NormalizeReliabilityClamped:
    """_normalize_reliability output is clamped to [0.0, 10.0]."""

    def test_above_one_clamps(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_reliability(1.5) == 10.0

    def test_below_zero_clamps(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_reliability(-0.5) == 0.0

    def test_zero_returns_zero(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_reliability(0.0) == 0.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-019 — _normalize_latency baseline
# ---------------------------------------------------------------------------


class TestFRGOOSCR019NormalizeLatencyBaseline:
    """_normalize_latency at baseline (250ms) returns 10.0
    (formula: 10/(1+(1-1)*0.5) = 10.0)."""

    def test_baseline_latency(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_latency(250.0) == 10.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-020 — _normalize_latency negative == 10.0
# ---------------------------------------------------------------------------


class TestFRGOOSCR020NormalizeLatencyNegative:
    """_normalize_latency with negative value returns 10.0."""

    def test_negative_latency(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_latency(-100.0) == 10.0

    def test_zero_latency(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_latency(0.0) == 10.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-021 — _normalize_cost baseline
# ---------------------------------------------------------------------------


class TestFRGOOSCR021NormalizeCostBaseline:
    """_normalize_cost at baseline ($0.15/1M) returns 10.0
    (formula: 10/(1+(1-1)*0.5) = 10.0).  Negative cost returns 10.0."""

    def test_baseline_cost(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_cost(0.15) == 10.0

    def test_negative_cost(self) -> None:
        scorer = DefaultProviderScorer()
        assert scorer._normalize_cost(-0.5) == 10.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-022 — composite_score correctness
# ---------------------------------------------------------------------------


class TestFRGOOSCR022CompositeScoreCorrectness:
    """composite_score equals the weighted average of the three
    component scores."""

    def test_weighted_average(self) -> None:
        scorer = DefaultProviderScorer()
        m = _metrics(reliability=0.80, latency_p99=200.0, cost_per_1m_tokens=0.10)
        score = scorer.score(m)

        r = scorer._normalize_reliability(0.80)
        l = scorer._normalize_latency(200.0)
        c = scorer._normalize_cost(0.10)
        expected = r * 0.4 + l * 0.2 + c * 0.4

        assert score.composite_score == pytest.approx(expected)


# ---------------------------------------------------------------------------
# FR-GOV-SCR-023 — all scores in [0.0, 10.0] range
# ---------------------------------------------------------------------------


class TestFRGOOSCR023AllScoresInRange:
    """Every score component and composite must be in [0.0, 10.0]."""

    def test_extreme_values(self) -> None:
        scorer = DefaultProviderScorer()
        # Best possible: perfect reliability, zero latency, zero cost
        best = _metrics(reliability=1.0, latency_p99=0.0, cost_per_1m_tokens=0.0)
        best_score = scorer.score(best)
        for val in (
            best_score.reliability_score,
            best_score.latency_score,
            best_score.cost_score,
            best_score.composite_score,
        ):
            assert 0.0 <= val <= 10.0

    def test_worst_values(self) -> None:
        scorer = DefaultProviderScorer()
        # Worst: zero reliability, huge latency, huge cost
        worst = _metrics(reliability=0.0, latency_p99=10_000.0, cost_per_1m_tokens=100.0)
        worst_score = scorer.score(worst)
        for val in (
            worst_score.reliability_score,
            worst_score.latency_score,
            worst_score.cost_score,
            worst_score.composite_score,
        ):
            assert 0.0 <= val <= 10.0


# ---------------------------------------------------------------------------
# FR-GOV-SCR-024 — score() returns correct provider_id
# ---------------------------------------------------------------------------


class TestFRGOOSCR024ScoreReturnsCorrectProviderId:
    """ProviderScore.provider_id must match the input metrics."""

    def test_provider_id_propagated(self) -> None:
        scorer = DefaultProviderScorer()
        m = _metrics(provider_id="anthropic-claude")
        score = scorer.score(m)
        assert score.provider_id == "anthropic-claude"


# ---------------------------------------------------------------------------
# FR-GOV-SCR-025 — ProviderScore ordering by composite_score
# ---------------------------------------------------------------------------


class TestFRGOOSCR025ProviderScoreOrdering:
    """Higher composite_score means a better provider; sorting by
    composite_score descending gives the expected ranking."""

    def test_higher_reliability_higher_composite(self) -> None:
        scorer = DefaultProviderScorer()
        reliable = scorer.score(_metrics(provider_id="a", reliability=0.99))
        unreliable = scorer.score(_metrics(provider_id="b", reliability=0.50))
        assert reliable.composite_score > unreliable.composite_score

    def test_lower_cost_higher_composite(self) -> None:
        scorer = DefaultProviderScorer()
        cheap = scorer.score(_metrics(provider_id="c", cost_per_1m_tokens=0.05))
        expensive = scorer.score(_metrics(provider_id="d", cost_per_1m_tokens=0.50))
        assert cheap.composite_score > expensive.composite_score

    def test_sort_by_composite_descending(self) -> None:
        scorer = DefaultProviderScorer()
        scores = [
            scorer.score(_metrics(provider_id="x", reliability=0.90)),
            scorer.score(_metrics(provider_id="y", reliability=0.70)),
            scorer.score(_metrics(provider_id="z", reliability=0.95)),
        ]
        ranked = sorted(scores, key=lambda s: s.composite_score, reverse=True)
        assert ranked[0].provider_id == "z"
        assert ranked[-1].provider_id == "y"
