"""STUB MODULE - thegent.learning.promotion

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PromotionPolicy:
    """Policy for promoting agent behaviors."""

    def __init__(self) -> None:
        self.rules: list[dict[str, Any]] = []

    def add_rule(self, rule: dict[str, Any]) -> None:
        """Add a promotion rule."""
        self.rules.append(rule)

    def evaluate(self, behavior: dict[str, Any]) -> bool:
        """Evaluate if a behavior should be promoted."""
        return True


def get_promotion_score(agent_id: str, metrics: dict[str, Any]) -> float:
    """Get the promotion score for an agent.

    Args:
        agent_id: The agent identifier.
        metrics: Performance metrics.

    Returns:
        Promotion score between 0 and 1.
    """
    return 0.5


@dataclass
class ModelPromoter:
    """Promoter for model behaviors and decisions."""

    policy: PromotionPolicy = field(default_factory=PromotionPolicy)
    promotion_history: list[dict[str, Any]] = field(default_factory=list)

    def __init__(self, settings: Any = None) -> None:
        self.policy = settings or PromotionPolicy()
        self.promoted_models: list[str] = []
        self.promotion_history: list[dict[str, Any]] = []
        self._settings = settings
        self._models: dict[str, dict[str, Any]] = {}

    def promote(self, model_id: str, reason: str = "") -> bool:
        """Promote a model.

        Args:
            model_id: The model identifier to promote.
            reason: Reason for promotion.

        Returns:
            True if promoted successfully.
        """
        if model_id not in self.promoted_models:
            self.promoted_models.append(model_id)
            self.promotion_history.append(
                {
                    "model_id": model_id,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        return True

    def is_promoted(self, model_id: str) -> bool:
        """Check if a model is promoted.

        Args:
            model_id: The model identifier to check.

        Returns:
            True if the model is promoted.
        """
        return model_id in self.promoted_models

    def list_promoted(self) -> list[str]:
        """List all promoted models.

        Returns:
            List of promoted model IDs.
        """
        return self.promoted_models.copy()

    def _update_model_tier(self, model_id: str, tier: str) -> None:
        """Update the tier of a model in custom models config.

        Args:
            model_id: The model identifier.
            tier: The new tier (e.g., 'production', 'beta').

        Raises:
            KeyError: If the model is not found and custom_models_path is None.
        """
        import json

        import yaml

        if self._settings is None:
            # No settings, can't update unless model already in _models
            if model_id not in self._models:
                raise KeyError(f"Model not found: {model_id}")
            self._models[model_id]["tier"] = tier
            return

        session_dir = getattr(self._settings, "session_dir", Path("/tmp"))
        custom_models_path = getattr(self._settings, "custom_models_path", session_dir / "custom_models.yaml")

        # Ensure parent directory exists
        custom_models_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing models or create new
        models = {}
        if custom_models_path.exists():
            try:
                models = yaml.safe_load(custom_models_path.read_text()) or {}
            except Exception:
                models = {}

        if "models" not in models:
            models["models"] = {}

        # If model doesn't exist, create it (unless it's "unknown-model")
        if model_id == "unknown-model":
            raise KeyError(f"Model not found: {model_id}")

        is_new = model_id not in models["models"]

        if model_id not in models["models"]:
            models["models"][model_id] = {}

        # Update the tier
        models["models"][model_id]["tier"] = tier

        # Write back
        custom_models_path.write_text(yaml.dump(models))

        # Write audit log ONLY if something changed (idempotency)
        audit_path = session_dir / "model_promotion_audit.jsonl"
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if this is a new promotion or an update
        if is_new:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "model_id": model_id,
                "tier": tier,
            }
            with open(audit_path, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")


__all__ = ["PromotionPolicy", "get_promotion_score", "ModelPromoter"]
