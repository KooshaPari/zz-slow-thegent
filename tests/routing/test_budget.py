"""Tests for GW-29/GW-30/GW-31: Budget hierarchy, reset periods, and soft alerts.

Tags used:
  @pytest.mark.requirement("FR-BUDGET-029")  — hierarchy tests
  @pytest.mark.requirement("FR-BUDGET-030")  — reset period tests
  @pytest.mark.requirement("FR-BUDGET-031")  — soft alert / hard block tests

# @trace FR-BUDGET-029 FR-BUDGET-030 FR-BUDGET-031
"""

from __future__ import annotations

import time

import pytest

from thegent.utils.routing_impl.budget import (
    BudgetCheckResult,
    BudgetHierarchy,
    BudgetPeriod,
    BudgetRecord,
    BudgetResetChecker,
    get_budget_hierarchy,
    reset_budget_hierarchy,
)

# ---------------------------------------------------------------------------
# BudgetRecord properties
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_record_not_exhausted_when_under_limit() -> None:
    """A record with spend below budget must not be exhausted."""
    record = BudgetRecord(entity_id="u1", entity_type="user", budget_usd=10.0, spent_usd=5.0)
    assert record.is_exhausted is False


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_record_exhausted_at_limit() -> None:
    """A record with spend equal to budget must be exhausted."""
    record = BudgetRecord(entity_id="u1", entity_type="user", budget_usd=10.0, spent_usd=10.0)
    assert record.is_exhausted is True


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_record_exhausted_over_limit() -> None:
    """A record with spend exceeding budget must be exhausted."""
    record = BudgetRecord(entity_id="u1", entity_type="user", budget_usd=10.0, spent_usd=15.0)
    assert record.is_exhausted is True


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_record_soft_alert_at_threshold() -> None:
    """A record at exactly 80% spend must trigger soft alert (not exhausted)."""
    record = BudgetRecord(
        entity_id="u1",
        entity_type="user",
        budget_usd=10.0,
        spent_usd=8.0,
        alert_threshold=0.80,
    )
    assert record.is_exhausted is False
    assert record.is_soft_alert is True


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_record_no_soft_alert_when_under_threshold() -> None:
    """A record below the alert threshold must NOT trigger soft alert."""
    record = BudgetRecord(
        entity_id="u1",
        entity_type="user",
        budget_usd=10.0,
        spent_usd=7.9,
        alert_threshold=0.80,
    )
    assert record.is_soft_alert is False


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_record_no_soft_alert_when_exhausted() -> None:
    """An exhausted record must NOT show soft alert (it is hard-blocked instead)."""
    record = BudgetRecord(
        entity_id="u1",
        entity_type="user",
        budget_usd=10.0,
        spent_usd=10.0,
        alert_threshold=0.80,
    )
    assert record.is_exhausted is True
    assert record.is_soft_alert is False


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_record_fraction_used() -> None:
    """fraction_used should equal spent_usd / budget_usd."""
    record = BudgetRecord(entity_id="u1", entity_type="user", budget_usd=20.0, spent_usd=5.0)
    assert record.fraction_used == pytest.approx(0.25)


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_record_no_budget_fraction_is_zero() -> None:
    """When budget_usd=0 (unlimited), fraction_used must be 0.0."""
    record = BudgetRecord(entity_id="u1", entity_type="user", budget_usd=0.0, spent_usd=99.0)
    assert record.fraction_used == 0.0


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_record_no_budget_not_exhausted() -> None:
    """When budget_usd=0 (unlimited), is_exhausted must be False."""
    record = BudgetRecord(entity_id="u1", entity_type="user", budget_usd=0.0, spent_usd=9999.0)
    assert record.is_exhausted is False


# ---------------------------------------------------------------------------
# BudgetResetChecker
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_reset_checker_resets_when_elapsed() -> None:
    """When period_start is far in the past the checker must reset spent_usd to 0."""
    record = BudgetRecord(
        entity_id="u1",
        entity_type="user",
        budget_usd=100.0,
        period=BudgetPeriod.DAILY,
        spent_usd=50.0,
        period_start=time.time() - 90_000,  # ~25 hours ago — past the 24h daily period
    )
    did_reset = BudgetResetChecker.maybe_reset(record)
    assert did_reset is True
    assert record.spent_usd == 0.0
    # period_start should have been updated to approximately now
    assert abs(record.period_start - time.time()) < 5.0


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_reset_checker_no_reset_when_not_elapsed() -> None:
    """When the period has not elapsed the checker must leave the record unchanged."""
    record = BudgetRecord(
        entity_id="u1",
        entity_type="user",
        budget_usd=100.0,
        period=BudgetPeriod.DAILY,
        spent_usd=50.0,
        period_start=time.time() - 3_600,  # 1 hour ago — well within 24h period
    )
    did_reset = BudgetResetChecker.maybe_reset(record)
    assert did_reset is False
    assert record.spent_usd == 50.0


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_period_daily_seconds() -> None:
    """PERIOD_SECONDS for DAILY must be 86400."""
    assert BudgetResetChecker.PERIOD_SECONDS[BudgetPeriod.DAILY] == 86_400.0


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_period_weekly_seconds() -> None:
    """PERIOD_SECONDS for WEEKLY must be 604800."""
    assert BudgetResetChecker.PERIOD_SECONDS[BudgetPeriod.WEEKLY] == 604_800.0


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_period_monthly_seconds() -> None:
    """PERIOD_SECONDS for MONTHLY must be 2592000 (30 days)."""
    assert BudgetResetChecker.PERIOD_SECONDS[BudgetPeriod.MONTHLY] == 2_592_000.0


# ---------------------------------------------------------------------------
# BudgetHierarchy
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_hierarchy_register_and_get() -> None:
    """A registered record must be retrievable by entity_id."""
    hierarchy = BudgetHierarchy()
    record = BudgetRecord(entity_id="team-1", entity_type="team", budget_usd=100.0)
    hierarchy.register(record)
    retrieved = hierarchy.get("team-1")
    assert retrieved is record


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_hierarchy_get_missing_returns_none() -> None:
    """Getting an unregistered entity must return None."""
    hierarchy = BudgetHierarchy()
    assert hierarchy.get("nonexistent") is None


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_hierarchy_record_spend() -> None:
    """record_spend must add cost to all listed entity records."""
    hierarchy = BudgetHierarchy()
    team = BudgetRecord(entity_id="team-1", entity_type="team", budget_usd=100.0, spent_usd=0.0)
    user = BudgetRecord(entity_id="user-1", entity_type="user", budget_usd=50.0, spent_usd=0.0)
    key = BudgetRecord(entity_id="sk-tg-k1", entity_type="key", budget_usd=10.0, spent_usd=0.0)
    hierarchy.register(team)
    hierarchy.register(user)
    hierarchy.register(key)

    hierarchy.record_spend(["team-1", "user-1", "sk-tg-k1"], 2.50)

    assert hierarchy.get("team-1").spent_usd == pytest.approx(2.50)
    assert hierarchy.get("user-1").spent_usd == pytest.approx(2.50)
    assert hierarchy.get("sk-tg-k1").spent_usd == pytest.approx(2.50)


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_hierarchy_check_budget_allowed() -> None:
    """When no entity is exhausted, check_budget must return allowed=True."""
    hierarchy = BudgetHierarchy()
    hierarchy.register(BudgetRecord(entity_id="team-1", entity_type="team", budget_usd=100.0, spent_usd=10.0))
    hierarchy.register(BudgetRecord(entity_id="user-1", entity_type="user", budget_usd=50.0, spent_usd=5.0))
    result = hierarchy.check_budget(["team-1", "user-1"])
    assert result.allowed is True
    assert result.blocking_entity is None


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_hierarchy_check_budget_blocked() -> None:
    """When an entity is exhausted, check_budget must return allowed=False."""
    hierarchy = BudgetHierarchy()
    hierarchy.register(BudgetRecord(entity_id="team-1", entity_type="team", budget_usd=100.0, spent_usd=10.0))
    hierarchy.register(BudgetRecord(entity_id="user-1", entity_type="user", budget_usd=5.0, spent_usd=5.0))
    result = hierarchy.check_budget(["team-1", "user-1"])
    assert result.allowed is False
    assert result.blocking_entity == "user-1"


@pytest.mark.requirement("FR-BUDGET-031")
def test_budget_hierarchy_check_soft_alert() -> None:
    """When an entity is at soft threshold, check_budget must return soft_alert=True."""
    hierarchy = BudgetHierarchy()
    hierarchy.register(BudgetRecord(entity_id="team-1", entity_type="team", budget_usd=100.0, spent_usd=85.0))
    hierarchy.register(BudgetRecord(entity_id="user-1", entity_type="user", budget_usd=50.0, spent_usd=10.0))
    result = hierarchy.check_budget(["team-1", "user-1"])
    assert result.allowed is True
    assert result.soft_alert is True
    assert "team-1" in result.alert_entities


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_hierarchy_missing_entity_ignored() -> None:
    """Entity IDs not in the hierarchy are silently skipped without error."""
    hierarchy = BudgetHierarchy()
    hierarchy.register(BudgetRecord(entity_id="team-1", entity_type="team", budget_usd=100.0, spent_usd=5.0))
    # "ghost-entity" is not registered
    result = hierarchy.check_budget(["team-1", "ghost-entity"])
    assert result.allowed is True


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_hierarchy_period_reset_on_check() -> None:
    """When a period has elapsed, check_budget resets it and must report allowed=True."""
    hierarchy = BudgetHierarchy()
    record = BudgetRecord(
        entity_id="user-1",
        entity_type="user",
        budget_usd=10.0,
        period=BudgetPeriod.DAILY,
        spent_usd=10.0,  # currently exhausted
        period_start=time.time() - 90_000,  # period elapsed
    )
    hierarchy.register(record)
    result = hierarchy.check_budget(["user-1"])
    # After reset, spent_usd becomes 0 so budget is no longer exhausted
    assert result.allowed is True
    assert hierarchy.get("user-1").spent_usd == 0.0


@pytest.mark.requirement("FR-BUDGET-030")
def test_budget_hierarchy_period_reset_on_record_spend() -> None:
    """record_spend resets the period if elapsed before adding cost."""
    hierarchy = BudgetHierarchy()
    record = BudgetRecord(
        entity_id="user-1",
        entity_type="user",
        budget_usd=100.0,
        period=BudgetPeriod.DAILY,
        spent_usd=50.0,
        period_start=time.time() - 90_000,  # elapsed
    )
    hierarchy.register(record)
    hierarchy.record_spend(["user-1"], 3.0)
    # After reset, spent starts at 0 then adds 3.0
    assert hierarchy.get("user-1").spent_usd == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# BudgetCheckResult defaults
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-BUDGET-029")
def test_budget_check_result_defaults() -> None:
    """BudgetCheckResult defaults: soft_alert=False, blocking_entity=None, alert_entities=[]."""
    result = BudgetCheckResult(allowed=True)
    assert result.soft_alert is False
    assert result.blocking_entity is None
    assert result.alert_entities == []


# ---------------------------------------------------------------------------
# Singleton behaviour
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-BUDGET-029")
def test_singleton_same_instance() -> None:
    """get_budget_hierarchy() must return the same instance on every call."""
    reset_budget_hierarchy()
    h1 = get_budget_hierarchy()
    h2 = get_budget_hierarchy()
    assert h1 is h2


@pytest.mark.requirement("FR-BUDGET-029")
def test_reset_budget_hierarchy() -> None:
    """reset_budget_hierarchy() causes get_budget_hierarchy() to return a fresh instance."""
    reset_budget_hierarchy()
    h_before = get_budget_hierarchy()
    reset_budget_hierarchy()
    h_after = get_budget_hierarchy()
    assert h_before is not h_after
