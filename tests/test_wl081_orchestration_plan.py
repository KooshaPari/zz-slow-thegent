"""Tests for WL-081: OrchestrationPlan Extended PlanNode Metadata + Convenience Factory.

Covers:
- Node creation with all extended metadata fields
- Default values (None) for optional fields
- add_task() factory method and chaining
- from_goal() classmethod
- total_budget_used() dict return with both budget_tokens and budget_time_s
- sandbox / require_hitl boolean helpers
- Agent/model filtering helpers

# @trace WL-081
"""

from __future__ import annotations

import pytest

from thegent.agents.plangent import Plan, PlanNode
from thegent.orchestration.plan import (
    AGENT_HINT,
    BUDGET_TIME_S,
    BUDGET_TOKENS,
    MODEL_HINT,
    OUTPUT_SCHEMA,
    PARENT_RUN_ID,
    REQUIRE_HITL,
    SANDBOX,
    OrchestrationPlan,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plan(goal: str = "test goal") -> OrchestrationPlan:
    return OrchestrationPlan(goal=goal)


# ---------------------------------------------------------------------------
# 1. Subclass relationship
# ---------------------------------------------------------------------------


def test_orchestration_plan_is_subclass_of_plan() -> None:
    """OrchestrationPlan must be a proper subclass of Plan. # @trace WL-081"""
    plan = _make_plan()
    assert isinstance(plan, Plan)


def test_orchestration_plan_has_plan_fields() -> None:
    """Inherits id, goal, nodes, created_at, metadata from Plan. # @trace WL-081"""
    plan = _make_plan("my goal")
    assert plan.goal == "my goal"
    assert plan.id is not None
    assert isinstance(plan.nodes, list)
    assert isinstance(plan.metadata, dict)
    assert plan.created_at is not None


# ---------------------------------------------------------------------------
# 2. add_task() — basic node creation
# ---------------------------------------------------------------------------


def test_add_task_returns_plan_node() -> None:
    """add_task must return a PlanNode instance. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("do something")
    assert isinstance(node, PlanNode)


def test_add_task_appends_to_nodes() -> None:
    """add_task must append the created node to plan.nodes. # @trace WL-081"""
    plan = _make_plan()
    assert len(plan.nodes) == 0
    plan.add_task("task 1")
    assert len(plan.nodes) == 1
    plan.add_task("task 2")
    assert len(plan.nodes) == 2


def test_add_task_sets_task_description() -> None:
    """Node.task must equal the prompt string passed to add_task. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("execute the mission")
    assert node.task == "execute the mission"


# ---------------------------------------------------------------------------
# 3. add_task() — extended metadata fields default to None (absent from metadata)
# ---------------------------------------------------------------------------


def test_add_task_agent_hint_defaults_absent() -> None:
    """agent_hint must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert AGENT_HINT not in node.metadata


def test_add_task_model_hint_defaults_absent() -> None:
    """model_hint must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert MODEL_HINT not in node.metadata


def test_add_task_budget_tokens_defaults_absent() -> None:
    """budget_tokens must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert BUDGET_TOKENS not in node.metadata


def test_add_task_budget_time_s_defaults_absent() -> None:
    """budget_time_s must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert BUDGET_TIME_S not in node.metadata


def test_add_task_sandbox_defaults_absent() -> None:
    """sandbox must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert SANDBOX not in node.metadata


def test_add_task_require_hitl_defaults_absent() -> None:
    """require_hitl must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert REQUIRE_HITL not in node.metadata


def test_add_task_output_schema_defaults_absent() -> None:
    """output_schema must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert OUTPUT_SCHEMA not in node.metadata


def test_add_task_parent_run_id_defaults_absent() -> None:
    """parent_run_id must not be in metadata when not provided. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert PARENT_RUN_ID not in node.metadata


# ---------------------------------------------------------------------------
# 4. add_task() — explicit metadata field storage
# ---------------------------------------------------------------------------


def test_add_task_stores_agent_hint() -> None:
    """agent_hint must be stored in node.metadata under AGENT_HINT. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", agent_hint="researcher")
    assert node.metadata[AGENT_HINT] == "researcher"


def test_add_task_stores_model_hint() -> None:
    """model_hint must be stored in node.metadata under MODEL_HINT. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", model_hint="claude-opus-4")
    assert node.metadata[MODEL_HINT] == "claude-opus-4"


def test_add_task_stores_budget_tokens() -> None:
    """budget_tokens must be stored as int in node.metadata. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", budget_tokens=4096)
    assert node.metadata[BUDGET_TOKENS] == 4096


def test_add_task_stores_budget_time_s() -> None:
    """budget_time_s must be stored as float in node.metadata. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", budget_time_s=30.5)
    assert node.metadata[BUDGET_TIME_S] == 30.5


def test_add_task_stores_sandbox_true() -> None:
    """sandbox=True must be stored in node.metadata. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", sandbox=True)
    assert node.metadata[SANDBOX] is True


def test_add_task_stores_sandbox_false() -> None:
    """sandbox=False must be stored in node.metadata when explicitly passed. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", sandbox=False)
    assert node.metadata[SANDBOX] is False


def test_add_task_stores_require_hitl_true() -> None:
    """require_hitl=True must be stored in node.metadata. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", require_hitl=True)
    assert node.metadata[REQUIRE_HITL] is True


def test_add_task_stores_output_schema() -> None:
    """output_schema dict must be stored in node.metadata. # @trace WL-081"""
    plan = _make_plan()
    schema = {"type": "object", "properties": {"result": {"type": "string"}}}
    node = plan.add_task("t", output_schema=schema)
    assert node.metadata[OUTPUT_SCHEMA] == schema


def test_add_task_stores_parent_run_id() -> None:
    """parent_run_id must be stored as str in node.metadata. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t", parent_run_id="run-abc-123")
    assert node.metadata[PARENT_RUN_ID] == "run-abc-123"


# ---------------------------------------------------------------------------
# 5. add_task() — depends_on wiring
# ---------------------------------------------------------------------------


def test_add_task_depends_on_empty_by_default() -> None:
    """depends_on defaults to empty list. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("t")
    assert node.depends_on == []


def test_add_task_depends_on_stored() -> None:
    """depends_on list is passed through to PlanNode. # @trace WL-081"""
    plan = _make_plan()
    first = plan.add_task("first")
    second = plan.add_task("second", depends_on=[first.id])
    assert second.depends_on == [first.id]


# ---------------------------------------------------------------------------
# 6. add_task() chaining (multiple calls)
# ---------------------------------------------------------------------------


def test_add_task_chaining_three_nodes() -> None:
    """Three add_task calls produce three distinct nodes. # @trace WL-081"""
    plan = _make_plan()
    n1 = plan.add_task("one")
    n2 = plan.add_task("two")
    n3 = plan.add_task("three")
    assert len(plan.nodes) == 3
    ids = {n1.id, n2.id, n3.id}
    assert len(ids) == 3  # all unique


# ---------------------------------------------------------------------------
# 7. from_goal() classmethod
# ---------------------------------------------------------------------------


def test_from_goal_returns_orchestration_plan() -> None:
    """from_goal must return an OrchestrationPlan instance. # @trace WL-081"""
    plan = OrchestrationPlan.from_goal("build a widget")
    assert isinstance(plan, OrchestrationPlan)


def test_from_goal_sets_goal() -> None:
    """from_goal must set the goal field on the plan. # @trace WL-081"""
    plan = OrchestrationPlan.from_goal("deploy the fleet")
    assert plan.goal == "deploy the fleet"


def test_from_goal_starts_with_empty_nodes() -> None:
    """from_goal must produce a plan with no nodes initially. # @trace WL-081"""
    plan = OrchestrationPlan.from_goal("do stuff")
    assert plan.nodes == []


def test_from_goal_stores_agent_hint_in_metadata() -> None:
    """from_goal with agent_hint must store it in plan.metadata. # @trace WL-081"""
    plan = OrchestrationPlan.from_goal("research topic", agent_hint="researcher")
    assert plan.metadata[AGENT_HINT] == "researcher"


def test_from_goal_without_agent_hint_stores_none() -> None:
    """from_goal without agent_hint stores None under AGENT_HINT. # @trace WL-081"""
    plan = OrchestrationPlan.from_goal("generic task")
    assert plan.metadata[AGENT_HINT] is None


def test_from_goal_has_unique_id() -> None:
    """Two from_goal calls must produce plans with different IDs. # @trace WL-081"""
    p1 = OrchestrationPlan.from_goal("goal")
    p2 = OrchestrationPlan.from_goal("goal")
    assert p1.id != p2.id


# ---------------------------------------------------------------------------
# 8. total_budget_used() — dict return type and keys
# ---------------------------------------------------------------------------


def test_total_budget_used_returns_dict() -> None:
    """total_budget_used must return a dict. # @trace WL-081"""
    plan = _make_plan()
    result = plan.total_budget_used()
    assert isinstance(result, dict)


def test_total_budget_used_has_budget_tokens_key() -> None:
    """total_budget_used dict must contain 'budget_tokens' key. # @trace WL-081"""
    plan = _make_plan()
    result = plan.total_budget_used()
    assert "budget_tokens" in result


def test_total_budget_used_has_budget_time_s_key() -> None:
    """total_budget_used dict must contain 'budget_time_s' key. # @trace WL-081"""
    plan = _make_plan()
    result = plan.total_budget_used()
    assert "budget_time_s" in result


def test_total_budget_used_empty_plan_returns_zeros() -> None:
    """Empty plan must return budget_tokens=0 and budget_time_s=0.0. # @trace WL-081"""
    plan = _make_plan()
    result = plan.total_budget_used()
    assert result["budget_tokens"] == 0
    assert result["budget_time_s"] == 0.0


def test_total_budget_used_sums_tokens_across_all_nodes() -> None:
    """budget_tokens sums across all nodes regardless of status. # @trace WL-081"""
    plan = _make_plan()
    plan.add_task("task1", budget_tokens=1000)
    plan.add_task("task2", budget_tokens=500)
    result = plan.total_budget_used()
    assert result["budget_tokens"] == 1500


def test_total_budget_used_sums_time_s_across_all_nodes() -> None:
    """budget_time_s sums across all nodes regardless of status. # @trace WL-081"""
    plan = _make_plan()
    plan.add_task("task1", budget_time_s=10.0)
    plan.add_task("task2", budget_time_s=5.5)
    result = plan.total_budget_used()
    assert result["budget_time_s"] == pytest.approx(15.5)


def test_total_budget_used_nodes_without_budget_are_skipped() -> None:
    """Nodes with no budget fields set do not contribute to totals. # @trace WL-081"""
    plan = _make_plan()
    plan.add_task("no budget task")
    plan.add_task("budgeted", budget_tokens=200, budget_time_s=5.0)
    result = plan.total_budget_used()
    assert result["budget_tokens"] == 200
    assert result["budget_time_s"] == pytest.approx(5.0)


def test_total_budget_used_includes_pending_nodes() -> None:
    """total_budget_used must include budget from pending (not just done) nodes. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task("pending task", budget_tokens=300)
    # Status remains "pending" (default)
    assert node.status == "pending"
    result = plan.total_budget_used()
    assert result["budget_tokens"] == 300


def test_total_budget_used_mixed_status_nodes() -> None:
    """total_budget_used sums budgets from nodes in all statuses. # @trace WL-081"""
    plan = _make_plan()
    n1 = plan.add_task("done task", budget_tokens=100, budget_time_s=1.0)
    n2 = plan.add_task("pending task", budget_tokens=200, budget_time_s=2.0)
    n1.status = "done"
    assert n2.status == "pending"
    result = plan.total_budget_used()
    assert result["budget_tokens"] == 300
    assert result["budget_time_s"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# 9. Sandbox / HITL helper methods
# ---------------------------------------------------------------------------


def test_get_sandbox_nodes_returns_only_sandboxed() -> None:
    """get_sandbox_nodes returns only nodes with sandbox=True. # @trace WL-081"""
    plan = _make_plan()
    plan.add_task("safe", sandbox=False)
    sandboxed = plan.add_task("risky", sandbox=True)
    plan.add_task("no sandbox flag")
    nodes = plan.get_sandbox_nodes()
    assert len(nodes) == 1
    assert nodes[0].id == sandboxed.id


def test_get_hitl_nodes_returns_only_hitl() -> None:
    """get_hitl_nodes returns only nodes with require_hitl=True. # @trace WL-081"""
    plan = _make_plan()
    plan.add_task("no hitl", require_hitl=False)
    hitl_node = plan.add_task("needs approval", require_hitl=True)
    plan.add_task("also no hitl")
    nodes = plan.get_hitl_nodes()
    assert len(nodes) == 1
    assert nodes[0].id == hitl_node.id


# ---------------------------------------------------------------------------
# 10. Agent / model filtering
# ---------------------------------------------------------------------------


def test_get_nodes_by_agent_filters_correctly() -> None:
    """get_nodes_by_agent returns nodes matching the given agent_hint. # @trace WL-081"""
    plan = _make_plan()
    a = plan.add_task("research", agent_hint="researcher")
    plan.add_task("code", agent_hint="coder")
    plan.add_task("review")
    nodes = plan.get_nodes_by_agent("researcher")
    assert len(nodes) == 1
    assert nodes[0].id == a.id


def test_get_nodes_by_model_filters_correctly() -> None:
    """get_nodes_by_model returns nodes matching the given model_hint. # @trace WL-081"""
    plan = _make_plan()
    plan.add_task("t1", model_hint="claude-opus-4")
    n2 = plan.add_task("t2", model_hint="gpt-5")
    nodes = plan.get_nodes_by_model("gpt-5")
    assert len(nodes) == 1
    assert nodes[0].id == n2.id


# ---------------------------------------------------------------------------
# 11. Node inherits PlanNode.is_ready() logic
# ---------------------------------------------------------------------------


def test_node_is_ready_when_dependencies_done() -> None:
    """Node created via add_task uses PlanNode.is_ready() correctly. # @trace WL-081"""
    plan = _make_plan()
    first = plan.add_task("first")
    second = plan.add_task("second", depends_on=[first.id])
    assert not second.is_ready(set())
    first.status = "done"
    assert second.is_ready(plan.done_ids)


# ---------------------------------------------------------------------------
# 12. to_dict serialisation round-trips metadata
# ---------------------------------------------------------------------------


def test_node_to_dict_includes_extended_metadata() -> None:
    """PlanNode.to_dict preserves extended metadata fields. # @trace WL-081"""
    plan = _make_plan()
    node = plan.add_task(
        "task",
        agent_hint="tester",
        model_hint="claude-sonnet-4",
        budget_tokens=2048,
        budget_time_s=60.0,
        sandbox=True,
        require_hitl=False,
        parent_run_id="run-xyz",
    )
    d = node.to_dict()
    assert d["metadata"][AGENT_HINT] == "tester"
    assert d["metadata"][MODEL_HINT] == "claude-sonnet-4"
    assert d["metadata"][BUDGET_TOKENS] == 2048
    assert d["metadata"][BUDGET_TIME_S] == 60.0
    assert d["metadata"][SANDBOX] is True
    assert d["metadata"][REQUIRE_HITL] is False
    assert d["metadata"][PARENT_RUN_ID] == "run-xyz"


def test_plan_to_dict_preserves_goal() -> None:
    """OrchestrationPlan.to_dict (inherited) must include the goal. # @trace WL-081"""
    plan = OrchestrationPlan.from_goal("serialise me")
    d = plan.to_dict()
    assert d["goal"] == "serialise me"
    assert "nodes" in d
