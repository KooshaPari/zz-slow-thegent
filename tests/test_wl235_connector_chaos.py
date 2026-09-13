"""Tests for WL-235: Connector Chaos Tests.

Tests cover:
- ChaosScenario dataclass creation
- ConnectorChaosTestSuite scenario management
- Scenario execution with target functions
- Scenario retrieval and listing
"""

from __future__ import annotations

import pytest

from thegent.integrations.connector_chaos import (
    ChaosScenario,
    ConnectorChaosTestSuite,
)


@pytest.mark.requirement("WL-235")
class TestChaosScenario:
    """Tests for the ChaosScenario dataclass."""

    def test_chaos_scenario_creation_default_probability(self) -> None:
        """Test creating a ChaosScenario with default probability."""
        scenario = ChaosScenario(name="timeout-fault", fault_type="timeout")
        assert scenario.name == "timeout-fault"
        assert scenario.fault_type == "timeout"
        assert scenario.probability == 1.0

    def test_chaos_scenario_creation_custom_probability(self) -> None:
        """Test creating a ChaosScenario with custom probability."""
        scenario = ChaosScenario(
            name="flaky-drop",
            fault_type="connection_drop",
            probability=0.5,
        )
        assert scenario.name == "flaky-drop"
        assert scenario.fault_type == "connection_drop"
        assert scenario.probability == 0.5

    def test_chaos_scenario_attributes(self) -> None:
        """Test all ChaosScenario attributes are accessible."""
        scenario = ChaosScenario(
            name="test",
            fault_type="error",
            probability=0.75,
        )
        assert hasattr(scenario, "name")
        assert hasattr(scenario, "fault_type")
        assert hasattr(scenario, "probability")


@pytest.mark.requirement("WL-235")
class TestConnectorChaosTestSuite:
    """Tests for the ConnectorChaosTestSuite class."""

    def test_create_empty_suite(self) -> None:
        """Test creating an empty chaos test suite."""
        suite = ConnectorChaosTestSuite()
        assert suite.scenarios() == []

    def test_add_single_scenario(self) -> None:
        """Test adding a single scenario to the suite."""
        suite = ConnectorChaosTestSuite()
        scenario = suite.add_scenario("timeout", "timeout_fault")
        assert scenario.name == "timeout"
        assert len(suite.scenarios()) == 1

    def test_add_multiple_scenarios(self) -> None:
        """Test adding multiple scenarios to the suite."""
        suite = ConnectorChaosTestSuite()
        suite.add_scenario("timeout", "timeout_fault")
        suite.add_scenario("drop", "connection_drop", 0.5)
        suite.add_scenario("error", "error_response")

        scenarios = suite.scenarios()
        assert len(scenarios) == 3
        assert any(s.name == "timeout" for s in scenarios)
        assert any(s.name == "drop" for s in scenarios)
        assert any(s.name == "error" for s in scenarios)

    def test_add_scenario_with_custom_probability(self) -> None:
        """Test adding scenario with non-default probability."""
        suite = ConnectorChaosTestSuite()
        scenario = suite.add_scenario("flaky", "intermittent_failure", probability=0.3)
        assert scenario.probability == 0.3

    def test_run_simple_target_function(self) -> None:
        """Test running a target function under a scenario."""
        suite = ConnectorChaosTestSuite()
        suite.add_scenario("test-scenario", "test_fault")

        def simple_fn() -> str:
            return "success"

        result = suite.run("test-scenario", simple_fn)
        assert result == "success"

    def test_run_with_side_effects(self) -> None:
        """Test running a function with side effects."""
        suite = ConnectorChaosTestSuite()
        suite.add_scenario("scenario", "fault_type")

        state: dict[str, int] = {"count": 0}

        def increment_fn() -> int:
            state["count"] += 1
            return state["count"]

        result = suite.run("scenario", increment_fn)
        assert result == 1
        assert state["count"] == 1

    def test_run_nonexistent_scenario_raises_keyerror(self) -> None:
        """Test that run raises KeyError for nonexistent scenario."""
        suite = ConnectorChaosTestSuite()

        def dummy_fn() -> None:
            pass

        with pytest.raises(KeyError):
            suite.run("nonexistent", dummy_fn)

    def test_run_returns_target_function_return_value(self) -> None:
        """Test that run returns the target function's return value."""
        suite = ConnectorChaosTestSuite()
        suite.add_scenario("return-test", "test")

        def return_dict_fn() -> dict:
            return {"status": "ok", "value": 42}

        result = suite.run("return-test", return_dict_fn)
        assert result == {"status": "ok", "value": 42}

    def test_run_with_exception_in_target(self) -> None:
        """Test that exceptions in target function propagate."""
        suite = ConnectorChaosTestSuite()
        suite.add_scenario("exception-test", "test")

        def raises_fn() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            suite.run("exception-test", raises_fn)

    def test_scenarios_retrieval_order(self) -> None:
        """Test that scenarios are retrievable."""
        suite = ConnectorChaosTestSuite()
        suite.add_scenario("first", "type1")
        suite.add_scenario("second", "type2")
        suite.add_scenario("third", "type3")

        scenarios = suite.scenarios()
        names = [s.name for s in scenarios]
        assert "first" in names
        assert "second" in names
        assert "third" in names
