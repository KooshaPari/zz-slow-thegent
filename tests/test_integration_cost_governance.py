"""Integration tests for cost tracking with governance.

Tests CostEstimator + CostAggregator pipeline and cost governance
with PolicyEngine budget enforcement via the RunRegistry.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.conftest_factories import make_run_meta
from thegent.cost.aggregator import CostAggregator, CostEstimator
from thegent.execution import PolicyEngine, RunRegistry


def _make_settings(**overrides: Any) -> SimpleNamespace:
    """Build a minimal settings object for PolicyEngine."""
    defaults = {
        "environment": "development",
        "trust_score_threshold": 0.8,
        "opa_url": "",
        "opa_timeout_ms": 500,
        "opa_fallback_allow": False,
        "session_dir": Path("/tmp/test-session"),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.mark.integration
class TestCostEstimatorAggregatorPipeline:
    """Tests CostEstimator producing estimates fed into CostAggregator via RunRegistry."""

    def test_estimator_with_known_model(self) -> None:
        # @trace FR-GOV-001
        """CostEstimator should use pricing table for known models."""
        estimator = CostEstimator()
        cost = estimator.estimate(
            model="claude-sonnet-4",
            tokens_in=1000,
            tokens_out=500,
        )
        # claude-sonnet-4: (0.003, 0.015) per 1k tokens
        expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
        assert abs(cost - expected) < 0.001

    def test_estimator_fallback_for_unknown_model(self) -> None:
        # @trace FR-GOV-001
        """CostEstimator should use heuristic fallback for unknown models."""
        estimator = CostEstimator()
        cost = estimator.estimate(model="unknown-model", prompt_length=1000)

        assert cost > 0.0

    def test_cost_aggregator_daily_total_from_registry(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """CostAggregator should sum cost_usd from today's finish events in the registry."""
        registry = RunRegistry(tmp_path)
        estimator = CostEstimator()

        # Register and complete two runs with cost data
        run1 = make_run_meta(agent="claude")
        registry.register_start(run1)
        cost1 = estimator.estimate(model="claude-sonnet-4", tokens_in=2000, tokens_out=1000)
        registry.register_end(
            run_id=run1.run_id,
            exit_code=0,
            status="completed",
            ended_at_utc=datetime.now(UTC).isoformat(),
            duration_s=30.0,
            cost_usd=cost1,
        )

        run2 = make_run_meta(agent="gemini")
        registry.register_start(run2)
        cost2 = estimator.estimate(model="gemini-2.0-flash", tokens_in=5000, tokens_out=2000)
        registry.register_end(
            run_id=run2.run_id,
            exit_code=0,
            status="completed",
            ended_at_utc=datetime.now(UTC).isoformat(),
            duration_s=20.0,
            cost_usd=cost2,
        )

        aggregator = CostAggregator(session_dir=tmp_path)
        daily = aggregator.daily_total(owner="test-owner")

        # The aggregator sums all finish events for today (regardless of owner in current impl)
        assert daily >= cost1 + cost2 - 0.001

    def test_cost_governance_with_policy_engine(self, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        """PolicyEngine should allow runs in dev even when costs accumulate."""
        registry = RunRegistry(tmp_path)
        settings = _make_settings(session_dir=tmp_path)
        engine = PolicyEngine(settings)

        # Register a bunch of runs with cost data
        for _i in range(5):
            run = make_run_meta(agent="claude")
            run.confidence = 0.8
            registry.register_start(run)
            registry.register_end(
                run_id=run.run_id,
                exit_code=0,
                status="completed",
                ended_at_utc=datetime.now(UTC).isoformat(),
                duration_s=10.0,
                cost_usd=0.10,
            )

        # Evaluate a new run -- should still allow in development
        new_run = make_run_meta(agent="claude")
        new_run.confidence = 0.85
        result, _reason = engine.evaluate(new_run, registry=registry)

        assert result == "allow"

        # Verify aggregator sees the costs
        aggregator = CostAggregator(session_dir=tmp_path)
        daily = aggregator.daily_total(owner="test-owner")
        assert daily >= 0.45  # 5 * $0.10 - tolerance
