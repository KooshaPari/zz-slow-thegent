"""Tests for plangent-style planning sub-agents.

Covers PlangentPlanner and PlangentExecutor.

# @trace FR-AGT-020
"""

from __future__ import annotations

import asyncio

import pytest

from thegent.agents.plangent import Plan, PlangentExecutor, PlangentPlanner, PlanNode

# ---------------------------------------------------------------------------
# PlanNode tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPlanNode:
    """Tests for PlanNode dataclass behaviour.

    # @trace FR-AGT-020
    """

    def test_default_id_is_generated(self) -> None:
        """PlanNode.id is auto-generated as a non-empty string."""
        node = PlanNode(task="do something")
        assert node.id
        assert isinstance(node.id, str)

    def test_default_status_is_pending(self) -> None:
        """PlanNode defaults to 'pending' status."""
        node = PlanNode(task="do something")
        assert node.status == "pending"

    def test_is_ready_no_deps(self) -> None:
        """A pending node with no dependencies is always ready."""
        node = PlanNode(task="independent")
        assert node.is_ready(set()) is True

    def test_is_ready_deps_satisfied(self) -> None:
        """A pending node is ready when all dependency IDs are in done_ids."""
        dep = PlanNode(task="dep")
        dep.status = "done"
        node = PlanNode(task="child", depends_on=[dep.id])
        assert node.is_ready({dep.id}) is True

    def test_is_ready_deps_not_satisfied(self) -> None:
        """A pending node is NOT ready when a dependency is not yet done."""
        dep = PlanNode(task="dep")
        node = PlanNode(task="child", depends_on=[dep.id])
        assert node.is_ready(set()) is False

    def test_is_ready_running_node_not_ready(self) -> None:
        """A running node is not considered ready for re-dispatch."""
        node = PlanNode(task="running")
        node.status = "running"
        assert node.is_ready(set()) is False

    def test_to_dict_keys(self) -> None:
        """to_dict contains all expected keys."""
        node = PlanNode(task="test", depends_on=["abc"])
        d = node.to_dict()
        assert set(d.keys()) == {"id", "task", "depends_on", "status", "result", "error", "metadata"}

    def test_to_dict_values(self) -> None:
        """to_dict values are consistent with the instance."""
        node = PlanNode(task="write tests", depends_on=["x"])
        d = node.to_dict()
        assert d["task"] == "write tests"
        assert d["depends_on"] == ["x"]
        assert d["status"] == "pending"
        assert d["result"] is None


# ---------------------------------------------------------------------------
# Plan tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPlan:
    """Tests for Plan dataclass and properties.

    # @trace FR-AGT-020
    """

    def test_default_id_generated(self) -> None:
        """Plan.id is auto-generated."""
        plan = Plan(goal="build something")
        assert plan.id
        assert isinstance(plan.id, str)

    def test_done_ids_empty_initially(self) -> None:
        """done_ids returns empty set when no nodes are done."""
        plan = Plan(goal="g", nodes=[PlanNode(task="t")])
        assert plan.done_ids == set()

    def test_done_ids_includes_done_nodes(self) -> None:
        """done_ids includes only nodes with status='done'."""
        n1 = PlanNode(task="a")
        n1.status = "done"
        n2 = PlanNode(task="b")
        plan = Plan(goal="g", nodes=[n1, n2])
        assert plan.done_ids == {n1.id}

    def test_failed_ids(self) -> None:
        """failed_ids returns IDs of nodes with status='failed'."""
        n = PlanNode(task="broken")
        n.status = "failed"
        plan = Plan(goal="g", nodes=[n])
        assert plan.failed_ids == {n.id}

    def test_get_node_found(self) -> None:
        """get_node returns the correct node when ID exists."""
        n = PlanNode(task="specific")
        plan = Plan(goal="g", nodes=[n])
        assert plan.get_node(n.id) is n

    def test_get_node_not_found(self) -> None:
        """get_node returns None for an unknown ID."""
        plan = Plan(goal="g")
        assert plan.get_node("nonexistent") is None

    def test_to_dict_structure(self) -> None:
        """to_dict returns expected keys and serialised node list."""
        n = PlanNode(task="t")
        plan = Plan(goal="do stuff", nodes=[n])
        d = plan.to_dict()
        assert d["goal"] == "do stuff"
        assert len(d["nodes"]) == 1
        assert d["nodes"][0]["task"] == "t"


# ---------------------------------------------------------------------------
# PlangentPlanner tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPlangentPlanner:
    """Tests for PlangentPlanner.

    # @trace FR-AGT-020
    """

    def setup_method(self) -> None:
        self.planner = PlangentPlanner()

    def test_decompose_empty_goal_raises(self) -> None:
        """decompose raises ValueError for empty or whitespace-only goals."""
        with pytest.raises(ValueError, match="non-empty"):
            self.planner.decompose("")
        with pytest.raises(ValueError, match="non-empty"):
            self.planner.decompose("   ")

    def test_decompose_simple_goal_creates_plan(self) -> None:
        """decompose returns a Plan with at least one node for a simple goal."""
        plan = self.planner.decompose("build a feature")
        assert isinstance(plan, Plan)
        assert len(plan.nodes) >= 1

    def test_decompose_goal_stored_in_plan(self) -> None:
        """decompose stores the (stripped) goal in plan.goal."""
        plan = self.planner.decompose("  my goal  ")
        assert plan.goal == "my goal"

    def test_decompose_all_nodes_pending(self) -> None:
        """All nodes produced by decompose start in 'pending' status."""
        plan = self.planner.decompose("refactor codebase")
        assert all(n.status == "pending" for n in plan.nodes)

    def test_decompose_separator_splits_goal(self) -> None:
        """decompose splits on separator character when present."""
        planner = PlangentPlanner(separator=".")
        plan = planner.decompose("step one. step two. step three")
        assert len(plan.nodes) == 3
        assert plan.nodes[0].task == "step one"
        assert plan.nodes[1].task == "step two"
        assert plan.nodes[2].task == "step three"

    def test_decompose_linear_dependency_chain(self) -> None:
        """Nodes form a linear dependency chain (n+1 depends on n)."""
        plan = self.planner.decompose("sequential workflow")
        for i, node in enumerate(plan.nodes[1:], 1):
            assert node.depends_on == [plan.nodes[i - 1].id]

    def test_decompose_first_node_no_deps(self) -> None:
        """The first node has no dependencies."""
        plan = self.planner.decompose("start here")
        assert plan.nodes[0].depends_on == []

    def test_decompose_max_depth_limits_nodes(self) -> None:
        """max_depth limits the total node count via max_nodes_per_level * max_depth."""
        planner = PlangentPlanner(max_nodes_per_level=2)
        plan = planner.decompose("big compound goal", max_depth=2)
        assert len(plan.nodes) <= 4  # 2 * 2 = 4 max

    def test_next_ready_tasks_empty_plan(self) -> None:
        """next_ready_tasks returns empty list for an empty plan."""
        plan = Plan(goal="empty")
        assert self.planner.next_ready_tasks(plan) == []

    def test_next_ready_tasks_first_node(self) -> None:
        """First node (no deps) is returned as ready immediately."""
        plan = self.planner.decompose("first ready")
        ready = self.planner.next_ready_tasks(plan)
        assert ready == [plan.nodes[0]]

    def test_next_ready_tasks_after_first_done(self) -> None:
        """Second node becomes ready after marking first as done."""
        plan = self.planner.decompose("sequential")
        self.planner.mark_done(plan, plan.nodes[0].id, "ok")
        ready = self.planner.next_ready_tasks(plan)
        assert len(ready) == 1
        assert ready[0].id == plan.nodes[1].id

    def test_mark_done_updates_status_and_result(self) -> None:
        """mark_done sets node status='done' and stores the result."""
        plan = self.planner.decompose("test me")
        node = plan.nodes[0]
        self.planner.mark_done(plan, node.id, "success output")
        assert node.status == "done"
        assert node.result == "success output"

    def test_mark_done_unknown_node_raises(self) -> None:
        """mark_done raises ValueError for unknown node IDs."""
        plan = Plan(goal="g")
        with pytest.raises(ValueError, match="not found"):
            self.planner.mark_done(plan, "missing-id", "result")

    def test_mark_failed_updates_status_and_error(self) -> None:
        """mark_failed sets node status='failed' and stores the error."""
        plan = self.planner.decompose("will fail")
        node = plan.nodes[0]
        self.planner.mark_failed(plan, node.id, "boom")
        assert node.status == "failed"
        assert node.error == "boom"

    def test_mark_failed_unknown_node_raises(self) -> None:
        """mark_failed raises ValueError for unknown node IDs."""
        plan = Plan(goal="g")
        with pytest.raises(ValueError, match="not found"):
            self.planner.mark_failed(plan, "bad-id", "err")

    def test_is_complete_all_done(self) -> None:
        """is_complete returns True when all nodes are 'done'."""
        plan = self.planner.decompose("finish me")
        for node in plan.nodes:
            node.status = "done"
        assert self.planner.is_complete(plan) is True

    def test_is_complete_mixed_done_failed(self) -> None:
        """is_complete returns True with a mix of done and failed nodes."""
        plan = self.planner.decompose("mixed")
        plan.nodes[0].status = "done"
        for node in plan.nodes[1:]:
            node.status = "failed"
        assert self.planner.is_complete(plan) is True

    def test_is_complete_pending_node(self) -> None:
        """is_complete returns False when any node is still pending."""
        plan = self.planner.decompose("not done yet")
        assert self.planner.is_complete(plan) is False

    def test_to_work_stream_rows_structure(self) -> None:
        """to_work_stream_rows returns one dict per node with expected keys."""
        plan = self.planner.decompose("work stream")
        rows = self.planner.to_work_stream_rows(plan)
        assert len(rows) == len(plan.nodes)
        expected_keys = {"id", "title", "source", "priority", "depends", "status"}
        for row in rows:
            assert set(row.keys()) == expected_keys

    def test_to_work_stream_rows_source_contains_plan_id(self) -> None:
        """Each work-stream row source field references the plan ID."""
        plan = self.planner.decompose("ws test")
        rows = self.planner.to_work_stream_rows(plan)
        for row in rows:
            assert plan.id in row["source"]

    def test_to_work_stream_first_node_no_depends(self) -> None:
        """First node row has 'depends' of '-' (no deps)."""
        plan = self.planner.decompose("ws deps test")
        rows = self.planner.to_work_stream_rows(plan)
        assert rows[0]["depends"] == "-"


# ---------------------------------------------------------------------------
# PlangentExecutor tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPlangentExecutor:
    """Tests for PlangentExecutor sync and async execution.

    # @trace FR-AGT-020
    """

    def setup_method(self) -> None:
        self.planner = PlangentPlanner()
        self.executor = PlangentExecutor(planner=self.planner)

    def _make_plan(self, n_nodes: int = 3) -> Plan:
        return self.planner.decompose("execute me", max_depth=n_nodes)

    def test_execute_all_success(self) -> None:
        """All nodes transition to 'done' when runner always succeeds."""
        plan = self._make_plan()

        def runner(node: PlanNode) -> str:
            return f"done:{node.task}"

        result = self.executor.execute(plan, runner)
        assert all(n.status == "done" for n in result.nodes)

    def test_execute_returns_plan(self) -> None:
        """execute returns the same Plan object (mutated in-place)."""
        plan = self._make_plan(1)

        def runner(_: PlanNode) -> str:
            return "ok"

        returned = self.executor.execute(plan, runner)
        assert returned is plan

    def test_execute_fail_fast_stops_on_error(self) -> None:
        """With fail_fast=True, execution halts after the first failure."""
        executor = PlangentExecutor(planner=self.planner, fail_fast=True)
        plan = self._make_plan(3)
        calls: list[str] = []

        def runner(node: PlanNode) -> str:
            calls.append(node.id)
            raise RuntimeError("explode")

        executor.execute(plan, runner)
        # Only the first node should have been attempted
        assert len(calls) == 1

    def test_execute_no_fail_fast_continues_on_error(self) -> None:
        """Without fail_fast, nodes that CAN run still execute after a failure."""
        executor = PlangentExecutor(planner=self.planner, fail_fast=False)
        # Create a plan with one independent node (no deps)
        plan = Plan(goal="independent nodes")
        n1 = PlanNode(task="will fail")
        n2 = PlanNode(task="independent success")
        plan.nodes = [n1, n2]

        def runner(node: PlanNode) -> str:
            if node.id == n1.id:
                raise RuntimeError("fail")
            return "success"

        executor.execute(plan, runner)
        # n1 failed, n2 should have run and succeeded
        assert n1.status == "failed"
        assert n2.status == "done"

    def test_execute_result_stored_in_node(self) -> None:
        """execute stores the runner's return value in node.result."""
        plan = self._make_plan(1)

        def runner(node: PlanNode) -> str:
            return "my output"

        self.executor.execute(plan, runner)
        assert plan.nodes[0].result == "my output"

    def test_execute_error_stored_in_node(self) -> None:
        """execute stores the exception message in node.error on failure."""
        plan = self._make_plan(1)

        def runner(_: PlanNode) -> str:
            raise ValueError("something broke")

        self.executor.execute(plan, runner)
        assert plan.nodes[0].status == "failed"
        assert "something broke" in (plan.nodes[0].error or "")

    def test_execute_empty_plan(self) -> None:
        """execute on an empty plan returns immediately without error."""
        plan = Plan(goal="empty")
        result = self.executor.execute(plan, lambda n: "ok")
        assert result.nodes == []

    def test_execute_async_all_success(self) -> None:
        """execute_async completes all nodes successfully with a sync runner."""
        plan = self._make_plan(2)

        def runner(node: PlanNode) -> str:
            return f"async-ok:{node.task}"

        result = asyncio.run(self.executor.execute_async(plan, runner))
        assert all(n.status == "done" for n in result.nodes)

    def test_execute_async_with_coroutine_runner(self) -> None:
        """execute_async works correctly with a coroutine runner."""
        plan = self._make_plan(2)

        async def async_runner(node: PlanNode) -> str:
            await asyncio.sleep(0)
            return f"coro:{node.task}"

        result = asyncio.run(self.executor.execute_async(plan, async_runner))
        assert all(n.status == "done" for n in result.nodes)

    def test_execute_async_fail_fast(self) -> None:
        """execute_async with fail_fast=True stops after first failure."""
        executor = PlangentExecutor(planner=self.planner, fail_fast=True)
        plan = self._make_plan(2)
        calls: list[str] = []

        def runner(node: PlanNode) -> str:
            calls.append(node.id)
            raise RuntimeError("boom")

        asyncio.run(executor.execute_async(plan, runner))
        assert len(calls) == 1

    def test_execute_async_returns_plan(self) -> None:
        """execute_async returns the same Plan object."""
        plan = self._make_plan(1)
        returned = asyncio.run(self.executor.execute_async(plan, lambda n: "ok"))
        assert returned is plan

    def test_default_planner_created_if_none(self) -> None:
        """PlangentExecutor creates a default PlangentPlanner when none given."""
        executor = PlangentExecutor()
        assert isinstance(executor.planner, PlangentPlanner)

    def test_custom_separator_decompose(self) -> None:
        """PlangentPlanner respects custom separator in decompose."""
        planner = PlangentPlanner(separator="|")
        plan = planner.decompose("task one|task two|task three")
        assert len(plan.nodes) == 3
        assert plan.nodes[0].task == "task one"
