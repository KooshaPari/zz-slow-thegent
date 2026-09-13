"""Stub module for cost-aware objective selection."""
from __future__ import annotations

from dataclasses import dataclass


class Selector:
    """Selector for planning."""

    def __init__(self) -> None:
        self._options: list = []

    def select(self) -> str | None:
        if self._options:
            return self._options[0]
        return None


class ObjectiveSelector:
    """Selector for cost-aware objectives."""

    def __init__(self) -> None:
        self._objectives: list = []

    def add_objective(self, objective: dict) -> None:
        """Add an objective."""
        self._objectives.append(objective)

    def select(self, models: list[dict], profile: ObjectiveWeights) -> dict:
        """Select the best model based on weighted profile.

        Args:
            models: List of model dicts with keys: id, latency, quality, cost
            profile: ObjectiveWeights defining the selection criteria

        Returns:
            The model dict that best matches the profile.
        """
        if not models:
            raise ValueError("No models provided")
        best = models[0]
        best_score = profile.score(best)
        for model in models:
            score = profile.score(model)
            if score > best_score:
                best = model
                best_score = score
        return best

    def select_next(self) -> dict | None:
        """Select the next objective."""
        if self._objectives:
            return self._objectives.pop(0)
        return None

    def get_all(self) -> list:
        """Get all objectives."""
        return self._objectives


__all__ = ["Selector", "ObjectiveSelector", "ObjectiveWeights", "get_objective_profile"]


@dataclass
class ObjectiveWeights:
    """Weights for different objective criteria (cost-aware selection)."""

    latency: float = 0.0
    quality: float = 0.0
    cost: float = 0.0

    def score(self, objective: dict) -> float:
        """Calculate weighted score for an objective/model.

        Args:
            objective: Dict with keys: latency, quality, cost

        Returns:
            Weighted score (higher is better).
        """
        score = 0.0
        # Lower latency is better (invert)
        latency = objective.get("latency", 0)
        if latency == 0:
            score += self.latency * 1.0
        else:
            score += self.latency * (1.0 / latency)
        # Higher quality is better
        score += self.quality * objective.get("quality", 0)
        # Lower cost is better (invert)
        cost = objective.get("cost", 0)
        if cost == 0:
            score += self.cost * 1.0
        else:
            score += self.cost * (1.0 / cost)
        return score


def get_objective_profile(profile_name: str) -> ObjectiveWeights:
    """Get a predefined objective weight profile.

    Args:
        profile_name: Name of the profile ("balanced", "speed", "quality", "cheapest").

    Returns:
        ObjectiveWeights instance.
    """
    profiles = {
        "balanced": ObjectiveWeights(latency=0.33, quality=0.33, cost=0.33),
        "speed": ObjectiveWeights(latency=0.7, quality=0.2, cost=0.1),
        "quality": ObjectiveWeights(latency=0.1, quality=0.7, cost=0.2),
        "cheapest": ObjectiveWeights(latency=0.1, quality=0.3, cost=0.6),
    }
    return profiles.get(profile_name, ObjectiveWeights())
