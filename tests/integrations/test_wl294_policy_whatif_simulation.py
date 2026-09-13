"""Tests for WL-294 policy what-if simulation."""

from __future__ import annotations

import pytest

from thegent.integrations.policy_whatif_simulation import (
    PolicySimulationInput,
    simulate_policy_change,
)


@pytest.mark.requirement("WL-294")
def test_simulate_policy_change_reports_improvement_for_faster_cycle() -> None:
    result = simulate_policy_change(
        PolicySimulationInput(
            total_items=100,
            open_items=40,
            blocked_items=10,
            current_cycle_interval_seconds=600,
            proposed_cycle_interval_seconds=300,
            max_changes_per_cycle=5,
        )
    )

    assert result.proposed_open_rate_per_hour > result.current_open_rate_per_hour
    assert result.improvement_hours > 0


@pytest.mark.requirement("WL-294")
def test_simulate_policy_change_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="blocked_items cannot exceed open_items"):
        simulate_policy_change(
            PolicySimulationInput(
                total_items=5,
                open_items=2,
                blocked_items=3,
                current_cycle_interval_seconds=600,
                proposed_cycle_interval_seconds=300,
                max_changes_per_cycle=1,
            )
        )
