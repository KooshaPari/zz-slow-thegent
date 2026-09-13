"""Tests for thegent.integrations.connector_toggle — Runtime connector toggle controls.

@trace WL-306
"""

from __future__ import annotations

import pytest

from thegent.integrations.capability_alerts import (
    ConnectorSLAEvaluator,
    ConnectorSLAThresholds,
)
from thegent.integrations.connector_toggle import ConnectorToggleRegistry
from thegent.integrations.error_budget import ErrorBudgetTracker
from thegent.integrations.pipeline_percentiles import PipelinePercentileTracker


class TestConnectorToggleRegistry:
    """Test ConnectorToggleRegistry operations. @trace WL-306"""

    @pytest.fixture
    def registry(self) -> ConnectorToggleRegistry:
        """Provide a ConnectorToggleRegistry instance."""
        return ConnectorToggleRegistry()

    @pytest.mark.requirement("WL-306")
    def test_register_connector(self, registry: ConnectorToggleRegistry) -> None:
        """Can register a connector with enabled state."""
        registry.register("github", enabled=True)
        assert registry.is_enabled("github") is True

    @pytest.mark.requirement("WL-306")
    def test_register_connector_disabled(self, registry: ConnectorToggleRegistry) -> None:
        """Can register a connector in disabled state."""
        registry.register("linear", enabled=False)
        assert registry.is_enabled("linear") is False

    @pytest.mark.requirement("WL-306")
    def test_register_default_enabled(self, registry: ConnectorToggleRegistry) -> None:
        """Connector registers as enabled by default."""
        registry.register("slack")
        assert registry.is_enabled("slack") is True

    @pytest.mark.requirement("WL-306")
    def test_register_duplicate_raises_error(self, registry: ConnectorToggleRegistry) -> None:
        """Registering duplicate connector raises ValueError."""
        registry.register("github")
        with pytest.raises(ValueError, match="already registered"):
            registry.register("github")

    @pytest.mark.requirement("WL-306")
    def test_enable_connector(self, registry: ConnectorToggleRegistry) -> None:
        """Can enable a connector."""
        registry.register("github", enabled=False)
        registry.enable("github")
        assert registry.is_enabled("github") is True

    @pytest.mark.requirement("WL-306")
    def test_enable_unregistered_raises_error(self, registry: ConnectorToggleRegistry) -> None:
        """Enabling unregistered connector raises ValueError."""
        with pytest.raises(ValueError, match="not registered"):
            registry.enable("nonexistent")

    @pytest.mark.requirement("WL-306")
    def test_disable_connector(self, registry: ConnectorToggleRegistry) -> None:
        """Can disable a connector."""
        registry.register("github", enabled=True)
        registry.disable("github")
        assert registry.is_enabled("github") is False

    @pytest.mark.requirement("WL-306")
    def test_disable_unregistered_raises_error(self, registry: ConnectorToggleRegistry) -> None:
        """Disabling unregistered connector raises ValueError."""
        with pytest.raises(ValueError, match="not registered"):
            registry.disable("nonexistent")

    @pytest.mark.requirement("WL-306")
    def test_is_enabled_unregistered_returns_false(self, registry: ConnectorToggleRegistry) -> None:
        """is_enabled returns False for unregistered connector."""
        result = registry.is_enabled("unknown")
        assert result is False

    @pytest.mark.requirement("WL-306")
    def test_toggle_enabled_to_disabled(self, registry: ConnectorToggleRegistry) -> None:
        """toggle flips enabled state to disabled and returns False."""
        registry.register("github", enabled=True)
        result = registry.toggle("github")

        assert result is False
        assert registry.is_enabled("github") is False

    @pytest.mark.requirement("WL-306")
    def test_toggle_disabled_to_enabled(self, registry: ConnectorToggleRegistry) -> None:
        """toggle flips disabled state to enabled and returns True."""
        registry.register("github", enabled=False)
        result = registry.toggle("github")

        assert result is True
        assert registry.is_enabled("github") is True

    @pytest.mark.requirement("WL-306")
    def test_toggle_unregistered_raises_error(self, registry: ConnectorToggleRegistry) -> None:
        """Toggling unregistered connector raises ValueError."""
        with pytest.raises(ValueError, match="not registered"):
            registry.toggle("nonexistent")

    @pytest.mark.requirement("WL-306")
    def test_toggle_multiple_times(self, registry: ConnectorToggleRegistry) -> None:
        """Toggling multiple times works correctly."""
        registry.register("github", enabled=True)

        assert registry.toggle("github") is False  # Now disabled
        assert registry.toggle("github") is True  # Now enabled
        assert registry.toggle("github") is False  # Now disabled

        assert registry.is_enabled("github") is False

    @pytest.mark.requirement("WL-306")
    def test_list_all_empty(self, registry: ConnectorToggleRegistry) -> None:
        """list_all returns empty dict for empty registry."""
        result = registry.list_all()
        assert result == {}

    @pytest.mark.requirement("WL-306")
    def test_list_all_single(self, registry: ConnectorToggleRegistry) -> None:
        """list_all returns single connector entry."""
        registry.register("github", enabled=True)
        result = registry.list_all()

        assert result == {"github": True}

    @pytest.mark.requirement("WL-306")
    def test_list_all_multiple(self, registry: ConnectorToggleRegistry) -> None:
        """list_all returns all registered connectors."""
        registry.register("github", enabled=True)
        registry.register("linear", enabled=False)
        registry.register("slack", enabled=True)

        result = registry.list_all()

        assert result == {
            "github": True,
            "linear": False,
            "slack": True,
        }

    @pytest.mark.requirement("WL-306")
    def test_list_all_returns_copy(self, registry: ConnectorToggleRegistry) -> None:
        """list_all returns a copy, not the internal registry."""
        registry.register("github", enabled=True)
        result1 = registry.list_all()

        # Modify the returned dict
        result1["github"] = False

        # Original registry should be unchanged
        assert registry.is_enabled("github") is True

    @pytest.mark.requirement("WL-306")
    def test_multiple_connectors_independent(self, registry: ConnectorToggleRegistry) -> None:
        """Connector states are independent."""
        registry.register("github", enabled=True)
        registry.register("linear", enabled=False)
        registry.register("slack", enabled=True)

        registry.disable("github")
        registry.enable("linear")

        assert registry.is_enabled("github") is False
        assert registry.is_enabled("linear") is True
        assert registry.is_enabled("slack") is True


class TestConnectorSLATracking:
    """Tests for WL-233 connector SLA latency/error budget tracking."""

    @pytest.mark.requirement("WL-306")
    @pytest.mark.requirement("WL-233")
    def test_sla_within_threshold(self) -> None:
        tracker = PipelinePercentileTracker()
        for value in (110.0, 120.0, 115.0, 105.0, 118.0):
            tracker.record("github", value, "cycle-a")
        budget = ErrorBudgetTracker()
        for _ in range(20):
            budget.record_success()
        budget.record_failure()
        evaluator = ConnectorSLAEvaluator()
        result = evaluator.evaluate(
            connector_name="github",
            latency_summary=tracker.summary("github"),
            error_budget_stats=budget.get_stats(),
            thresholds=ConnectorSLAThresholds(p95_latency_ms=300.0, max_failure_rate=0.10),
        )
        assert result["within_sla"] is True
        assert result["breaches"] == []

    @pytest.mark.requirement("WL-306")
    @pytest.mark.requirement("WL-233")
    def test_sla_breach_latency_and_error_budget(self) -> None:
        tracker = PipelinePercentileTracker()
        for value in (200.0, 220.0, 260.0, 280.0, 400.0):
            tracker.record("linear", value, "cycle-b")
        budget = ErrorBudgetTracker()
        for _ in range(3):
            budget.record_success()
        for _ in range(3):
            budget.record_failure()
        evaluator = ConnectorSLAEvaluator()
        result = evaluator.evaluate(
            connector_name="linear",
            latency_summary=tracker.summary("linear"),
            error_budget_stats=budget.get_stats(),
            thresholds=ConnectorSLAThresholds(p95_latency_ms=250.0, max_failure_rate=0.20),
        )
        assert result["within_sla"] is False
        assert len(result["breaches"]) == 2
        assert "latency breach" in result["breaches"][0] or "latency breach" in result["breaches"][1]
        assert "failure rate breach" in result["breaches"][0] or "failure rate breach" in result["breaches"][1]
