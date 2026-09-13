"""Tests for GW-63: Dynamic routing node types (PercentageSplit, BudgetLimitRoute).

# @trace FR-AROUTE-063
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.route_config import BudgetLimitRoute, PercentageSplit

# ---------------------------------------------------------------------------
# PercentageSplit
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_selects_first_at_zero() -> None:
    """rand_value=0.0 always selects the first target."""
    split = PercentageSplit(targets=["a", "b", "c"], weights=[50, 30, 20])
    assert split.select(rand_value=0.0) == "a"


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_selects_last_at_one() -> None:
    """rand_value approaching 1.0 selects the last target."""
    split = PercentageSplit(targets=["a", "b", "c"], weights=[50, 30, 20])
    # 0.9999 is well past the 0.8 cumulative boundary for "c"
    assert split.select(rand_value=0.9999) == "c"


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_normalized_weights() -> None:
    """Weights that don't sum to 100 are normalised before selection."""
    # weights [1, 1] -> each 50% -> boundary at 0.5
    split = PercentageSplit(targets=["x", "y"], weights=[1, 1])
    assert split.select(rand_value=0.0) == "x"
    assert split.select(rand_value=0.9) == "y"


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_equal_weights() -> None:
    """Equal weights produce equal probability splits at expected boundaries."""
    split = PercentageSplit(targets=["a", "b"], weights=[50, 50])
    # boundary is at 0.5 (exclusive lower)
    assert split.select(rand_value=0.0) == "a"
    assert split.select(rand_value=0.49) == "a"
    assert split.select(rand_value=0.5) == "b"
    assert split.select(rand_value=0.99) == "b"


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_single_target() -> None:
    """A single-target split always returns that target."""
    split = PercentageSplit(targets=["only"], weights=[100])
    assert split.select(rand_value=0.0) == "only"
    assert split.select(rand_value=0.5) == "only"
    assert split.select(rand_value=0.9999) == "only"


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_uses_random_when_no_rand_value() -> None:
    """When rand_value is None, select() calls random.random() internally."""
    split = PercentageSplit(targets=["a", "b"], weights=[50, 50])
    # Just verify it returns a valid target without raising
    result = split.select()
    assert result in ("a", "b")


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_mismatched_lengths_raises() -> None:
    """Mismatched targets and weights lengths raise ValueError."""
    split = PercentageSplit(targets=["a", "b"], weights=[100])
    with pytest.raises(ValueError, match="same length"):
        split.select(rand_value=0.5)


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_empty_targets_raises() -> None:
    """Empty targets list raises ValueError."""
    split = PercentageSplit(targets=[], weights=[])
    with pytest.raises(ValueError):
        split.select(rand_value=0.5)


@pytest.mark.requirement("FR-AROUTE-063")
def test_percentage_split_three_way_mid_boundary() -> None:
    """Mid-range rand_value hits the second bucket correctly."""
    split = PercentageSplit(targets=["a", "b", "c"], weights=[33, 33, 34])
    # cumulative after "a": 33/100 = 0.33
    # cumulative after "b": 66/100 = 0.66
    assert split.select(rand_value=0.34) == "b"
    assert split.select(rand_value=0.67) == "c"


# ---------------------------------------------------------------------------
# BudgetLimitRoute
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-063")
def test_budget_limit_route_within_budget() -> None:
    """When spend is below budget, primary_target is returned."""
    route = BudgetLimitRoute(
        primary_target="gpt-4o",
        fallback_target="gpt-4o-mini",
        budget_usd=10.0,
        entity_id="user-123",
    )
    assert route.select(current_spend_usd=5.0) == "gpt-4o"
    assert route.select(current_spend_usd=0.0) == "gpt-4o"
    assert route.select(current_spend_usd=9.99) == "gpt-4o"


@pytest.mark.requirement("FR-AROUTE-063")
def test_budget_limit_route_over_budget() -> None:
    """When spend exceeds budget, fallback_target is returned."""
    route = BudgetLimitRoute(
        primary_target="gpt-4o",
        fallback_target="gpt-4o-mini",
        budget_usd=10.0,
        entity_id="user-123",
    )
    assert route.select(current_spend_usd=10.01) == "gpt-4o-mini"
    assert route.select(current_spend_usd=999.0) == "gpt-4o-mini"


@pytest.mark.requirement("FR-AROUTE-063")
def test_budget_limit_route_exactly_at_limit() -> None:
    """When spend equals budget exactly (>=), fallback_target is returned."""
    route = BudgetLimitRoute(
        primary_target="gpt-4o",
        fallback_target="gpt-4o-mini",
        budget_usd=10.0,
        entity_id="user-123",
    )
    # >= boundary: exactly at limit triggers fallback
    assert route.select(current_spend_usd=10.0) == "gpt-4o-mini"


@pytest.mark.requirement("FR-AROUTE-063")
def test_budget_limit_route_zero_budget() -> None:
    """A zero budget always routes to fallback (any spend >= 0)."""
    route = BudgetLimitRoute(
        primary_target="expensive",
        fallback_target="cheap",
        budget_usd=0.0,
        entity_id="team-a",
    )
    assert route.select(current_spend_usd=0.0) == "cheap"
    assert route.select(current_spend_usd=0.001) == "cheap"


@pytest.mark.requirement("FR-AROUTE-063")
def test_budget_limit_route_entity_id_preserved() -> None:
    """entity_id is stored correctly (for integration with BudgetHierarchy)."""
    route = BudgetLimitRoute(
        primary_target="primary",
        fallback_target="fallback",
        budget_usd=5.0,
        entity_id="org-xyz",
    )
    assert route.entity_id == "org-xyz"
    assert route.budget_usd == 5.0
