"""Unit tests for Omega Loop (WP-45001)."""

import pytest

from thegent.planning.omega import OmegaExecutionResult, OmegaLoop


@pytest.mark.unit
class TestOmegaLoop:
    """Omega Loop (WP-45001)."""

    def test_minimize_entropy_pruning(self) -> None:
        # @trace FR-PLN-001
        """Can prune redundant actions to minimize entropy."""
        loop = OmegaLoop(agent_id="test-agent")

        # Plan with a redundant action (same ID or same payload)
        proposed_plan = [
            {"id": "a1", "payload": "task 1", "depends_on": []},
            {"id": "a2", "payload": "task 2", "depends_on": ["a1"]},
            {"id": "a1", "payload": "task 1", "depends_on": []},  # Redundant ID
            {
                "id": "a3",
                "payload": "task 2",
                "depends_on": ["a1"],
            },  # Redundant payload
        ]

        result = loop.minimize_entropy("cycle-1", proposed_plan)

        assert isinstance(result, OmegaExecutionResult)
        assert len(result.executed_actions) == 2  # Only a1 and a2 should remain
        assert "a1" in result.pruned_actions
        assert "a3" in result.pruned_actions
        assert result.efficiency_gain >= 0.0

    def test_entropy_calculation(self) -> None:
        # @trace FR-PLN-001
        """Entropy calculation heuristic works."""
        loop = OmegaLoop(agent_id="test-agent")

        plan1 = [{"id": "a1", "depends_on": ["d1"]}]
        entropy1 = loop.calculate_entropy(plan1)

        plan2 = [
            {"id": "a1", "depends_on": ["d1"]},
            {"id": "a2", "depends_on": ["d1", "d2"]},
        ]
        entropy2 = loop.calculate_entropy(plan2)

        # More actions/dependencies should generally change entropy
        assert entropy1 != entropy2
        assert 0.0 <= entropy1 <= 1.0
        assert 0.0 <= entropy2 <= 1.0

    def test_empty_plan(self) -> None:
        # @trace FR-PLN-001
        """Handles empty plan gracefully."""
        loop = OmegaLoop(agent_id="test-agent")
        result = loop.minimize_entropy("empty-cycle", [])

        assert result.entropy_score == 0.0
        assert len(result.executed_actions) == 0
        assert len(result.pruned_actions) == 0
