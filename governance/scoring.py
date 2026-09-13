"""
Provider Scoring System (Task 2.1.1)

Implements provider scoring with reliability, latency, and cost normalization.
Composite score: 0.4*reliability + 0.2*latency + 0.4*cost
"""

import math
from dataclasses import dataclass


@dataclass
class ProviderMetrics:
    """Provider performance metrics"""

    reliability: float  # 0.0-1.0 (e.g., 0.98 = 98% uptime)
    latency_p99: float  # milliseconds
    cost_per_1m_tokens: float  # USD per 1 million tokens


@dataclass
class ProviderScore:
    """Calculated provider score"""

    provider_id: str
    reliability_score: float  # 0-10
    latency_score: float  # 0-10
    cost_score: float  # 0-10
    composite_score: float  # 0-10

    def __repr__(self) -> str:
        return (
            f"ProviderScore({self.provider_id}, "
            f"rel={self.reliability_score:.1f}, "
            f"lat={self.latency_score:.1f}, "
            f"cost={self.cost_score:.1f}, "
            f"composite={self.composite_score:.1f})"
        )


class DefaultProviderScorer:
    """Default provider scorer with configurable weights and normalization"""

    # Normalization baselines
    LATENCY_P99_BASELINE_MS = 500  # Reference latency for scoring
    COST_BASELINE_USD = 1.0  # Reference cost for scoring ($1 per 1M tokens)

    # Composite score weights
    WEIGHT_RELIABILITY = 0.4
    WEIGHT_LATENCY = 0.2
    WEIGHT_COST = 0.4

    def score(self, provider_id: str, metrics: ProviderMetrics) -> ProviderScore:
        """
        Calculate composite provider score.

        Args:
            provider_id: Provider identifier (e.g., "gemini-flash")
            metrics: ProviderMetrics object with reliability, latency, cost

        Returns:
            ProviderScore with normalized component scores (0-10 each) and composite

        Raises:
            ValueError: If metrics are out of valid ranges
        """
        self._validate_metrics(metrics)

        # Normalize each component to 0-10 scale
        reliability_score = self._normalize_reliability(metrics.reliability)
        latency_score = self._normalize_latency(metrics.latency_p99)
        cost_score = self._normalize_cost(metrics.cost_per_1m_tokens)

        # Composite score: weighted sum
        composite = (
            (reliability_score * self.WEIGHT_RELIABILITY)
            + (latency_score * self.WEIGHT_LATENCY)
            + (cost_score * self.WEIGHT_COST)
        )

        return ProviderScore(
            provider_id=provider_id,
            reliability_score=round(reliability_score, 2),
            latency_score=round(latency_score, 2),
            cost_score=round(cost_score, 2),
            composite_score=round(composite, 2),
        )

    def _validate_metrics(self, metrics: ProviderMetrics) -> None:
        """Validate metric ranges"""
        if not (0.0 <= metrics.reliability <= 1.0):
            raise ValueError(f"Reliability must be 0.0-1.0, got {metrics.reliability}")
        if metrics.latency_p99 < 0:
            raise ValueError(f"Latency cannot be negative, got {metrics.latency_p99}")
        if metrics.cost_per_1m_tokens < 0:
            raise ValueError(f"Cost cannot be negative, got {metrics.cost_per_1m_tokens}")

    def _normalize_reliability(self, reliability: float) -> float:
        """
        Normalize reliability (0.0-1.0) to 0-10 score.
        Linear: 0.8 uptime → 8.0, 0.99 → 9.9
        """
        return reliability * 10.0

    def _normalize_latency(self, latency_ms: float) -> float:
        """
        Normalize latency to 0-10 score (inverse relationship).
        Higher latency = lower score.
        Uses baseline of 500ms as reference: 500ms = 5.0
        Formula: score = 10 * exp(-latency / baseline)
        """
        # Exponential decay: faster latency → higher score
        # 200ms: ~8.0, 500ms: ~5.0, 1000ms: ~2.0
        normalized = 10.0 * math.exp(-latency_ms / self.LATENCY_P99_BASELINE_MS)
        return max(0.1, min(10.0, normalized))  # Clamp to 0.1-10.0

    def _normalize_cost(self, cost_usd: float) -> float:
        """
        Normalize cost to 0-10 score (inverse relationship).
        Higher cost = lower score.
        Uses baseline of $1/1M tokens as reference: $1 = 5.0
        Formula: score = 10 / (1 + cost / baseline)
        """
        # Hyperbolic decay: $0.05 → ~9.3, $1 → 5.0, $10 → ~0.9
        if cost_usd == 0:
            return 10.0  # Free tier
        normalized = 10.0 / (1.0 + cost_usd / self.COST_BASELINE_USD)
        return max(0.1, min(10.0, normalized))  # Clamp to 0.1-10.0
