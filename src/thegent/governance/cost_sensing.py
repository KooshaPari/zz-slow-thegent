"""Cost sensing module for governance tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ObjectiveWeights:
    """Objective weights for model selection.

    Attributes:
        latency: Weight for latency (0.0-1.0)
        quality: Weight for quality (0.0-1.0)
        cost: Weight for cost (0.0-1.0)
    """

    latency: float = 0.0
    quality: float = 0.0
    cost: float = 0.0


class ObjectiveSelector:
    """Selects the best model based on objective weights.

    Given a list of models with metrics (latency, quality, cost) and a
    profile of weights, returns the best model for the profile.
    """

    def select(self, candidates: list[dict], profile: ObjectiveWeights | None = None) -> dict:
        """Select the best candidate for the given objective weights.

        Args:
            candidates: List of candidate models with keys:
                - id: str
                - latency: float
                - quality: float
                - cost: float
            profile: Objective weights profile (default: equal weights)

        Returns:
            The best candidate model for the given weights
        """
        if not candidates:
            raise ValueError("No candidates provided")
        if profile is None:
            profile = ObjectiveWeights(latency=1.0, quality=1.0, cost=1.0)
        if not isinstance(profile, ObjectiveWeights):
            raise ValueError("profile must be an ObjectiveWeights instance")
        best = candidates[0]
        best_score = self._score(best, profile)
        for candidate in candidates[1:]:
            score = self._score(candidate, profile)
            if score > best_score:
                best_score = score
                best = candidate
        return best

    def _score(self, candidate: dict, profile: ObjectiveWeights) -> float:
        """Score a candidate for the given objective weights.

        For each dimension, lower values are better (latency, cost),
        except quality which is higher-is-better.

        Args:
            candidate: A candidate model with latency, quality, cost
            profile: Objective weights profile

        Returns:
            Score (higher is better)
        """
        # Quality is higher-is-better
        quality_score = candidate.get("quality", 0.0)
        # Latency is lower-is-better
        latency_score = 1.0 - candidate.get("latency", 0.0)
        # Cost is lower-is-better
        cost_score = 1.0 - candidate.get("cost", 0.0)
        return (
            profile.latency * latency_score
            + profile.quality * quality_score
            + profile.cost * cost_score
        )


class CostPredictor:
    """Predicts costs for model actions.

    Given a model with cost_per_1m_tokens and a token estimate,
    predicts the cost for a specific action type.
    """

    def predict_cost(self, model: dict, tokens_estimate: int, action_type: str) -> float:
        """Predict the cost of an action.

        Args:
            model: Model dict with cost_per_1m_tokens
            tokens_estimate: Estimated token count
            action_type: Type of action (currently unused)

        Returns:
            Predicted cost in USD
        """
        if not model:
            raise ValueError("model is required")
        cost_per_1m = model.get("cost_per_1m_tokens", 0.0)
        return cost_per_1m * tokens_estimate / 1_000_000

    def __init__(self) -> None:
        """Initialize CostPredictor."""
