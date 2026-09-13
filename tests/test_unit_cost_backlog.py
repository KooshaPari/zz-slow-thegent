"""Unit tests for CostController (budget management) and BacklogManager (issue queue)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from thegent.cost.aggregator_controller import BudgetTier, CostController
from thegent.governance.backlog import BacklogItem, BacklogManager, BacklogStatus

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared contract data
# ---------------------------------------------------------------------------

_TARGETS_DATA: dict = {
    "version": "1.0.0",
    "dimensions": {
        "test_coverage": {
            "weight": 0.20,
            "target": 80,
            "direction": "higher_is_better",
        },
    },
    "budget": {
        "daily_agent_calls": 20,
        "tiers": {
            "normal": {"max_utilization_pct": 50, "description": "All agent types available"},
            "cautious": {"max_utilization_pct": 80, "description": "Prefer cheaper/faster agents"},
            "restricted": {"max_utilization_pct": 95, "description": "Only essential tasks"},
            "halted": {"max_utilization_pct": 100, "description": "No new agent spawns"},
        },
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def targets_path(tmp_path: Path) -> Path:
    """Write health-targets.json to tmp_path and return its path.

    Traces to: FR-GOV-002
    """
    p = tmp_path / "health-targets.json"
    p.write_text(json.dumps(_TARGETS_DATA).decode())
    return p


@pytest.fixture
def cost(tmp_path: Path, targets_path: Path) -> CostController:
    """Return a CostController with a fresh session dir.

    Traces to: FR-GOV-002
    """
    return CostController(session_dir=tmp_path, health_targets_path=targets_path)


@pytest.fixture
def backlog(tmp_path: Path) -> BacklogManager:
    """Return a BacklogManager with a fresh session dir.

    Traces to: FR-GOV-002
    """
    return BacklogManager(session_dir=tmp_path)


# ---------------------------------------------------------------------------
# CostController tests
# ---------------------------------------------------------------------------


def test_initial_usage_zero(cost: CostController) -> None:
    """Fresh CostController has 0 calls used.

    Traces to: FR-GOV-002
    """
    usage = cost.get_today_usage()
    assert usage.calls_used == 0
    assert usage.calls_limit == 20


def test_record_call_increments(cost: CostController) -> None:
    """record_call bumps calls_used by 1 each time.

    Traces to: FR-GOV-002
    """
    cost.record_call("test_coverage", "scanner")
    assert cost.get_today_usage().calls_used == 1
    cost.record_call("test_coverage", "scanner")
    assert cost.get_today_usage().calls_used == 2


def test_per_dimension_tracking(cost: CostController) -> None:
    """record_call tracks per-dimension call counts.

    Traces to: FR-GOV-002
    """
    cost.record_call("test_coverage", "agent_a")
    cost.record_call("test_coverage", "agent_b")
    cost.record_call("lint_violations", "agent_a")
    usage = cost.get_today_usage()
    assert usage.per_dimension["test_coverage"] == 2
    assert usage.per_dimension["lint_violations"] == 1


def test_per_agent_tracking(cost: CostController) -> None:
    """record_call tracks per-agent call counts.

    Traces to: FR-GOV-002
    """
    cost.record_call("test_coverage", "agent_a")
    cost.record_call("lint_violations", "agent_a")
    cost.record_call("lint_violations", "agent_b")
    usage = cost.get_today_usage()
    assert usage.per_agent["agent_a"] == 2
    assert usage.per_agent["agent_b"] == 1


def test_tier_normal(cost: CostController) -> None:
    """0 calls out of 20 -> NORMAL tier (< 50% utilization).

    Traces to: FR-GOV-002
    """
    assert cost.get_tier() == BudgetTier.NORMAL


def test_tier_cautious(cost: CostController) -> None:
    """11 calls out of 20 = 55% -> CAUTIOUS tier (50-80%).

    Traces to: FR-GOV-002
    """
    for _ in range(11):
        cost.record_call("test_coverage", "agent")
    assert cost.get_tier() == BudgetTier.CAUTIOUS


def test_tier_restricted(cost: CostController) -> None:
    """17 calls out of 20 = 85% -> RESTRICTED tier (80-95%).

    Traces to: FR-GOV-002
    """
    for _ in range(17):
        cost.record_call("test_coverage", "agent")
    assert cost.get_tier() == BudgetTier.RESTRICTED


def test_tier_halted(cost: CostController) -> None:
    """20 calls out of 20 = 100% -> HALTED tier (>= 95%).

    Traces to: FR-GOV-002
    """
    for _ in range(20):
        cost.record_call("test_coverage", "agent")
    assert cost.get_tier() == BudgetTier.HALTED


def test_can_spawn_normal(cost: CostController) -> None:
    """can_spawn returns True when not in HALTED tier.

    Traces to: FR-GOV-002
    """
    assert cost.can_spawn() is True
    for _ in range(11):
        cost.record_call("test_coverage", "agent")
    assert cost.can_spawn() is True  # CAUTIOUS, still allowed


def test_can_spawn_halted(cost: CostController) -> None:
    """can_spawn returns False when in HALTED tier.

    Traces to: FR-GOV-002
    """
    for _ in range(20):
        cost.record_call("test_coverage", "agent")
    assert cost.can_spawn() is False


def test_calls_remaining(cost: CostController) -> None:
    """calls_remaining = calls_limit - calls_used.

    Traces to: FR-GOV-002
    """
    assert cost.calls_remaining() == 20
    cost.record_call("test_coverage", "agent")
    assert cost.calls_remaining() == 19
    for _ in range(19):
        cost.record_call("test_coverage", "agent")
    assert cost.calls_remaining() == 0


# ---------------------------------------------------------------------------
# BacklogManager tests
# ---------------------------------------------------------------------------


def test_add_item(backlog: BacklogManager) -> None:
    """add() creates an item that appears in get_all().

    Traces to: FR-GOV-002
    """
    item = backlog.add(
        finding_id="F-001",
        dimension="test_coverage",
        severity=0.8,
        description="Coverage below 80%",
    )
    assert isinstance(item, BacklogItem)
    assert item.status == BacklogStatus.PENDING
    all_items = backlog.get_all()
    assert len(all_items) == 1
    assert all_items[0].finding_id == "F-001"


def test_get_pending_sorted(backlog: BacklogManager) -> None:
    """get_pending returns items sorted by severity descending.

    Traces to: FR-GOV-002
    """
    backlog.add("F-001", "lint", 0.3, "Minor lint issue")
    backlog.add("F-002", "security", 0.9, "Critical vuln")
    backlog.add("F-003", "coverage", 0.6, "Medium coverage gap")
    pending = backlog.get_pending()
    assert len(pending) == 3
    assert pending[0].severity == 0.9
    assert pending[1].severity == 0.6
    assert pending[2].severity == 0.3


def test_resolve_item(backlog: BacklogManager) -> None:
    """resolve() changes item status to RESOLVED.

    Traces to: FR-GOV-002
    """
    item = backlog.add("F-001", "coverage", 0.5, "Gap")
    backlog.resolve(item.item_id)
    all_items = backlog.get_all()
    assert all_items[0].status == BacklogStatus.RESOLVED


def test_defer_item(backlog: BacklogManager) -> None:
    """defer() sets status to DEFERRED and stores reason.

    Traces to: FR-GOV-002
    """
    item = backlog.add("F-001", "coverage", 0.5, "Gap")
    backlog.defer(item.item_id, reason="Budget exhausted")
    all_items = backlog.get_all()
    assert all_items[0].status == BacklogStatus.DEFERRED
    assert all_items[0].deferred_reason == "Budget exhausted"


def test_increment_attempt(backlog: BacklogManager) -> None:
    """increment_attempt bumps the attempts counter and sets timestamp.

    Traces to: FR-GOV-002
    """
    item = backlog.add("F-001", "lint", 0.4, "Lint issue")
    assert item.attempts == 0
    backlog.increment_attempt(item.item_id)
    updated = backlog.get_all()[0]
    assert updated.attempts == 1
    assert updated.last_attempted_at is not None
    backlog.increment_attempt(item.item_id)
    assert backlog.get_all()[0].attempts == 2


def test_get_pending_excludes_resolved(backlog: BacklogManager) -> None:
    """get_pending excludes resolved and deferred items.

    Traces to: FR-GOV-002
    """
    item_a = backlog.add("F-001", "coverage", 0.8, "Gap A")
    item_b = backlog.add("F-002", "lint", 0.5, "Lint B")
    backlog.add("F-003", "security", 0.9, "Vuln C")
    backlog.resolve(item_a.item_id)
    backlog.defer(item_b.item_id, reason="Out of budget")
    pending = backlog.get_pending()
    assert len(pending) == 1
    assert pending[0].finding_id == "F-003"
