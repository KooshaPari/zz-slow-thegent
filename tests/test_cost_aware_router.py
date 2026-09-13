"""Tests for CostAwareRouter.

Traces to: FR-COST-001, FR-COST-002, FR-COST-003
"""

import pytest

from thegent.utils.routing_impl.cost_aware_router import (
    BudgetExceededError,
    CostAwareRouter,
    CostBudget,
    RouteCandidate,
    SimpleCostTracker,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CANDIDATES = [
    RouteCandidate(name="cheap-fast", cost_per_call=0.001, quality=0.70),
    RouteCandidate(name="mid-tier", cost_per_call=0.005, quality=0.80),
    RouteCandidate(name="premium", cost_per_call=0.020, quality=0.95),
]

BUDGET = CostBudget(daily_limit_usd=10.0, session_limit_usd=2.0, warn_at_pct=0.8)


def _router(session_spend: float = 0.0, daily_spend: float = 0.0) -> CostAwareRouter:
    tracker = SimpleCostTracker()
    if session_spend:
        tracker.record(session_spend)
    if daily_spend > session_spend:
        # record the delta so daily reflects the requested total
        tracker.record(daily_spend - session_spend)
    return CostAwareRouter(BUDGET, tracker)


# ---------------------------------------------------------------------------
# SimpleCostTracker unit tests — FR-COST-001
# ---------------------------------------------------------------------------


def test_tracker_starts_at_zero():
    """Traces to: FR-COST-001"""
    t = SimpleCostTracker()
    assert t.session_total() == 0.0
    assert t.daily_total() == 0.0


def test_tracker_record_accumulates():
    """Traces to: FR-COST-001"""
    t = SimpleCostTracker()
    t.record(0.10)
    t.record(0.25)
    assert t.session_total() == pytest.approx(0.35)
    assert t.daily_total() == pytest.approx(0.35)


def test_tracker_reset_session():
    """Traces to: FR-COST-001"""
    t = SimpleCostTracker()
    t.record(1.0)
    t.reset_session()
    assert t.session_total() == 0.0
    # daily total is unaffected by session reset
    assert t.daily_total() == pytest.approx(1.0)


def test_tracker_negative_raises():
    """Traces to: FR-COST-001"""
    t = SimpleCostTracker()
    with pytest.raises(ValueError):
        t.record(-0.01)


# ---------------------------------------------------------------------------
# Under-budget: best quality selected — FR-COST-003
# ---------------------------------------------------------------------------


def test_under_budget_selects_best_quality():
    """Under budget → highest-quality candidate returned. Traces to: FR-COST-003"""
    router = _router(session_spend=0.0)
    result = router.select(CANDIDATES)
    assert result.name == "premium"


def test_single_candidate_always_selected():
    """Single candidate is always returned regardless of budget state. Traces to: FR-COST-003"""
    router = _router(session_spend=0.0)
    only = [RouteCandidate(name="only", cost_per_call=0.001, quality=0.5)]
    assert router.select(only).name == "only"


def test_empty_candidates_raises():
    """Empty candidate list raises ValueError. Traces to: FR-COST-003"""
    router = _router()
    with pytest.raises(ValueError):
        router.select([])


# ---------------------------------------------------------------------------
# Near limit: cheapest 50% selected — FR-COST-003
# ---------------------------------------------------------------------------


def test_near_session_limit_selects_cheap_half():
    """At 80% of session limit → cheapest 50% filtered, best quality among them chosen.
    Traces to: FR-COST-003
    """
    # 80% of session_limit_usd (2.0) = 1.6
    router = _router(session_spend=1.6)
    result = router.select(CANDIDATES)
    # cheapest half of [0.001, 0.005, 0.020] = top 2 by price = [cheap-fast, mid-tier]
    # best quality among those = mid-tier (0.80)
    assert result.name == "mid-tier"


def test_near_daily_limit_selects_cheap_half():
    """At 80% of daily limit → cheapest 50% selected. Traces to: FR-COST-003"""
    # Use a budget where daily limit is tighter than session so daily warn fires first
    # daily=10, session=100 → 80% daily = 8.0, session far from warn
    big_session_budget = CostBudget(daily_limit_usd=10.0, session_limit_usd=100.0, warn_at_pct=0.8)
    tracker = SimpleCostTracker()
    tracker.record(8.0)
    router = CostAwareRouter(big_session_budget, tracker)
    result = router.select(CANDIDATES)
    assert result.name == "mid-tier"


def test_near_limit_two_candidates():
    """Near limit with exactly 2 candidates → cheapest 1 selected. Traces to: FR-COST-003"""
    tracker = SimpleCostTracker()
    tracker.record(1.6)  # 80% of session 2.0
    router = CostAwareRouter(BUDGET, tracker)
    two = [
        RouteCandidate(name="cheap", cost_per_call=0.001, quality=0.60),
        RouteCandidate(name="pricey", cost_per_call=0.010, quality=0.90),
    ]
    result = router.select(two)
    assert result.name == "cheap"


# ---------------------------------------------------------------------------
# Over limit: BudgetExceededError raised — FR-COST-002
# ---------------------------------------------------------------------------


def test_session_limit_exceeded_raises():
    """Session spend >= session_limit → BudgetExceededError. Traces to: FR-COST-002"""
    router = _router(session_spend=2.0)
    with pytest.raises(BudgetExceededError) as exc_info:
        router.select(CANDIDATES)
    err = exc_info.value
    assert err.budget_type == "session"
    assert err.limit == pytest.approx(2.0)
    assert err.current == pytest.approx(2.0)


def test_daily_limit_exceeded_raises():
    """Daily spend >= daily_limit → BudgetExceededError. Traces to: FR-COST-002"""
    # Use a budget where daily_limit is lower than session_limit so daily check fires first
    daily_budget = CostBudget(daily_limit_usd=5.0, session_limit_usd=100.0, warn_at_pct=0.8)
    tracker = SimpleCostTracker()
    tracker.record(5.0)
    router = CostAwareRouter(daily_budget, tracker)
    with pytest.raises(BudgetExceededError) as exc_info:
        router.select(CANDIDATES)
    err = exc_info.value
    assert err.budget_type == "daily"
    assert err.limit == pytest.approx(5.0)


def test_session_limit_exceeded_error_message():
    """BudgetExceededError message is informative. Traces to: FR-COST-002"""
    err = BudgetExceededError("session", 2.0, 2.5)
    assert "session" in str(err)
    assert "2.5" in str(err)
    assert "2.0" in str(err)
