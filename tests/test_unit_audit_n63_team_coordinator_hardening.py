"""AUDIT-N+63 hardening tests for governance/team_coordinator.py.

Invariant contract: FR-GOV-TW-001..015
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from thegent.governance import team_coordinator as team_mod
from thegent.governance.agent_hierarchy import (
    AgentHierarchyManager,
    AgentNode,
    AgentRelationship,
    AgentRole,
    AgentTeam,
    CoordinationMode,
    RelationshipType,
    TeamType,
)
from thegent.governance.team_coordinator import TeamCoordinator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(
    run_id: str,
    role: AgentRole = AgentRole.SPECIALIST,
    team_id: str | None = "team-a",
    parent_id: str | None = None,
    status: str = "active",
) -> MagicMock:
    """Return a MagicMock mimicking an AgentNode."""
    agent = MagicMock(spec=AgentNode)
    agent.run_id = run_id
    agent.role = role
    agent.team_id = team_id
    agent.parent_id = parent_id
    agent.status = status
    return agent


def _make_relationship(
    relationship_id: str = "rel-1",
    parent_id: str = "a",
    child_id: str = "b",
    rel_type: RelationshipType = RelationshipType.TEAM_MEMBERSHIP,
    status: str = "active",
) -> MagicMock:
    rel = MagicMock(spec=AgentRelationship)
    rel.relationship_id = relationship_id
    rel.parent_id = parent_id
    rel.child_id = child_id
    rel.relationship_type = rel_type
    rel.status = status
    return rel


def _make_team(
    team_id: str = "team-a",
    name: str = "Alpha",
    lead_id: str = "lead-a",
    coordination_mode: CoordinationMode = CoordinationMode.HIERARCHICAL,
) -> MagicMock:
    team = MagicMock(spec=AgentTeam)
    team.team_id = team_id
    team.name = name
    team.lead_id = lead_id
    team.coordination_mode = coordination_mode
    team.team_type = TeamType.FUNCTIONAL
    team.status = "active"
    return team


def _make_manager() -> MagicMock:
    return MagicMock(spec=AgentHierarchyManager)


def _coordinator(mgr: MagicMock | None = None) -> tuple[TeamCoordinator, MagicMock]:
    if mgr is None:
        mgr = _make_manager()
    return TeamCoordinator(mgr), mgr


# ---------------------------------------------------------------------------
# FR-GOV-TW-001..015
# ---------------------------------------------------------------------------


class TestFRGOVTW001:
    """TW-001: __init__ stores hierarchy_manager reference."""

    def test_stores_reference(self) -> None:
        mgr = _make_manager()
        tc = TeamCoordinator(mgr)
        assert tc.hierarchy is mgr


class TestFRGOVTW002:
    """TW-002: delegate_within_team raises ValueError when from_agent not found."""

    def test_from_agent_missing(self) -> None:
        tc, mgr = _coordinator()
        mgr.get_agent.return_value = None
        with pytest.raises(ValueError, match="Agent not found"):
            tc.delegate_within_team("missing", "target", "do something")


class TestFRGOVTW003:
    """TW-003: delegate_within_team raises ValueError when to_agent not found."""

    def test_to_agent_missing(self) -> None:
        tc, mgr = _coordinator()
        from_ag = _make_agent("from-id")
        mgr.get_agent.side_effect = lambda aid: from_ag if aid == "from-id" else None
        with pytest.raises(ValueError, match="Agent not found"):
            tc.delegate_within_team("from-id", "missing", "do something")


class TestFRGOVTW004:
    """TW-004: delegate_within_team raises ValueError when agents in different teams."""

    def test_different_teams(self) -> None:
        tc, mgr = _coordinator()
        a = _make_agent("a", team_id="team-a")
        b = _make_agent("b", team_id="team-b")
        mgr.get_agent.side_effect = lambda aid: a if aid == "a" else b
        with pytest.raises(ValueError, match="Agents not in same team"):
            tc.delegate_within_team("a", "b", "do something")


class TestFRGOVTW005:
    """TW-005: delegate_within_team returns AgentRelationship on success."""

    def test_success(self) -> None:
        tc, mgr = _coordinator()
        a = _make_agent("a", team_id="team-a")
        b = _make_agent("b", team_id="team-a")
        mgr.get_agent.side_effect = lambda aid: a if aid == "a" else b
        expected = _make_relationship(parent_id="a", child_id="b")
        mgr.create_relationship.return_value = expected
        result = tc.delegate_within_team("a", "b", "task", context={"k": "v"})
        mgr.create_relationship.assert_called_once_with(
            parent_id="a",
            child_id="b",
            relationship_type=RelationshipType.TEAM_MEMBERSHIP,
            delegation_prompt="task",
            handoff_context={"k": "v"},
        )
        assert result is expected


class TestFRGOVTW006:
    """TW-006: delegate_cross_team raises ValueError when from_agent not found."""

    def test_from_agent_missing(self) -> None:
        tc, mgr = _coordinator()
        mgr.get_agent.return_value = None
        with pytest.raises(ValueError, match="Agent not found"):
            tc.delegate_cross_team("missing", "target", "do something")


class TestFRGOVTW007:
    """TW-007: delegate_cross_team raises ValueError when agents in same team."""

    def test_same_team(self) -> None:
        tc, mgr = _coordinator()
        a = _make_agent("a", team_id="team-a")
        b = _make_agent("b", team_id="team-a")
        mgr.get_agent.side_effect = lambda aid: a if aid == "a" else b
        with pytest.raises(ValueError, match="Agents in same team"):
            tc.delegate_cross_team("a", "b", "do something")


class TestFRGOVTW008:
    """TW-008: delegate_cross_team creates cross-team relationship with mediator context."""

    def test_cross_team_with_mediator(self) -> None:
        tc, mgr = _coordinator()
        a = _make_agent("a", team_id="team-a")
        b = _make_agent("b", team_id="team-b")
        mgr.get_agent.side_effect = lambda aid: a if aid == "a" else b
        expected = _make_relationship(
            parent_id="a",
            child_id="b",
            rel_type=RelationshipType.CROSS_TEAM_COLLABORATION,
        )
        mgr.create_relationship.return_value = expected
        result = tc.delegate_cross_team(
            "a", "b", "task", context={"x": 1}, mediator_id="med-1"
        )
        mgr.create_relationship.assert_called_once_with(
            parent_id="a",
            child_id="b",
            relationship_type=RelationshipType.CROSS_TEAM_COLLABORATION,
            delegation_prompt="task",
            handoff_context={"mediator_id": "med-1", "cross_team": True, "x": 1},
        )
        assert result is expected


class TestFRGOVTW009:
    """TW-009: coordinate_team_task raises ValueError when team not found."""

    def test_team_not_found(self) -> None:
        tc, mgr = _coordinator()
        mgr.get_team.return_value = None
        with pytest.raises(ValueError, match="not found"):
            tc.coordinate_team_task("nonexistent", "task")


class TestFRGOVTW010:
    """TW-010: coordinate_team_task returns error for team with no active members."""

    def test_no_active_members(self) -> None:
        tc, mgr = _coordinator()
        mgr.get_team.return_value = _make_team()
        mgr.get_team_members.return_value = [
            _make_agent("m1", status="inactive"),
        ]
        result = tc.coordinate_team_task("team-a", "task")
        assert result["status"] == "error"
        assert "No active members" in result["message"]


class TestFRGOVTW011:
    """TW-011: coordinate_team_task dispatches to hierarchical mode correctly."""

    def test_hierarchical(self) -> None:
        tc, mgr = _coordinator()
        team = _make_team(
            lead_id="lead-a",
            coordination_mode=CoordinationMode.HIERARCHICAL,
        )
        mgr.get_team.return_value = team
        lead = _make_agent("lead-a", role=AgentRole.TEAM_LEAD, team_id="team-a")
        member = _make_agent("m1", team_id="team-a")
        mgr.get_team_members.return_value = [lead, member]
        rel = _make_relationship(parent_id="lead-a", child_id="m1")
        mgr.get_agent.side_effect = lambda aid: lead if aid == "lead-a" else member
        mgr.create_relationship.return_value = rel

        result = tc.coordinate_team_task("team-a", "do work")
        assert result["status"] == "success"
        assert result["coordination_mode"] == "hierarchical"
        assert result["assigned_by"] == "lead-a"


class TestFRGOVTW012:
    """TW-012: coordinate_team_task dispatches to swarm mode correctly."""

    def test_swarm(self) -> None:
        tc, mgr = _coordinator()
        team = _make_team(coordination_mode=CoordinationMode.SWARM)
        mgr.get_team.return_value = team
        m1 = _make_agent("m1", team_id="team-a")
        m2 = _make_agent("m2", team_id="team-a")
        mgr.get_team_members.return_value = [m1, m2]

        result = tc.coordinate_team_task("team-a", "do work")
        assert result["status"] == "success"
        assert result["coordination_mode"] == "swarm"
        assert "m1" in result["assignments"]
        assert "m2" in result["assignments"]


class TestFRGOVTW013:
    """TW-013: _evaluate_task_complexity returns float between 0.0 and 1.0."""

    def test_bounds(self) -> None:
        tc, _ = _coordinator()
        # Empty task, no context
        score = tc._evaluate_task_complexity("")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_long_task_high_complexity(self) -> None:
        tc, _ = _coordinator()
        score = tc._evaluate_task_complexity("x" * 1000, context={"complexity": 1.0})
        assert 0.0 <= score <= 1.0

    def test_many_artifacts(self) -> None:
        tc, _ = _coordinator()
        score = tc._evaluate_task_complexity(
            "task", context={"required_artifacts": [1, 2, 3, 4, 5, 6, 7]}
        )
        assert 0.0 <= score <= 1.0


class TestFRGOVTW014:
    """TW-014: _find_orchestrator returns run_id of executive agent or None."""

    def test_finds_executive(self) -> None:
        tc, mgr = _coordinator()
        exec_agent = _make_agent("exec-1", role=AgentRole.EXECUTIVE, parent_id=None)
        mgr.list_all_agents.return_value = [exec_agent]
        assert tc._find_orchestrator() == "exec-1"

    def test_returns_none_when_no_executive(self) -> None:
        tc, mgr = _coordinator()
        specialist = _make_agent("spec-1", role=AgentRole.SPECIALIST)
        mgr.list_all_agents.return_value = [specialist]
        assert tc._find_orchestrator() is None

    def test_returns_none_when_executive_has_parent(self) -> None:
        tc, mgr = _coordinator()
        exec_agent = _make_agent(
            "exec-1", role=AgentRole.EXECUTIVE, parent_id="some-parent"
        )
        mgr.list_all_agents.return_value = [exec_agent]
        assert tc._find_orchestrator() is None


class TestFRGOVTW015:
    """TW-015: __all__ exports exactly ['TeamCoordinator']."""

    def test_all_exports(self) -> None:
        assert team_mod.__all__ == ["TeamCoordinator"]
