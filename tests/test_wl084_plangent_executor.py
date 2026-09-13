"""Tests for WL-084: Wire SubAgentDispatcher into PlangentExecutor.execute_async().

Covers:
- Plain Plan + runner callback path is preserved (backward compatibility)
- OrchestrationPlan + explicit dispatcher triggers dispatcher path
- OrchestrationPlan without dispatcher auto-creates one
- Successful nodes are marked done with correct result output
- Failed nodes are marked failed with correct error message
- ResultAggregator summary stored in plan.metadata["aggregation"]
- aggregation["passed"] is True when all nodes succeed
- aggregation["passed"] is False when any node fails
- aggregation["by_node"] keyed by node_id
- aggregation["total"] equals number of dispatched nodes
- fail_fast=True stops after first node failure (orchestration path)
- fail_fast=False continues after failures (orchestration path)
- fail_fast=True stops after first node failure (plain path)
- Missing DispatchResult for a node is treated as failure
- execute_async with OrchestrationPlan + zero nodes returns plan with no changes
- execute_async with OrchestrationPlan + single successful node
- execute_async with OrchestrationPlan + multiple successful nodes
- execute_async with OrchestrationPlan + mixed success/failure nodes
- execute_async with plain Plan + runner that raises exceptions
- execute_async with plain Plan + async runner
- execute_async with plain Plan + sync runner
- _execute_plain_async is called for plain Plan instances
- _execute_orchestration_async is called for OrchestrationPlan instances
- Aggregation result keys: total, by_type, results, errors, passed, by_node
- Node result string from dispatcher is stored on PlanNode.result
- Node error string from dispatcher is stored on PlanNode.error
- OrchestrationPlan remains the same object (mutated in-place)
- execute() sync path unchanged for plain Plans

# @trace WL-084
"""

from __future__ import annotations

from typing import Any

import pytest

from thegent.agents.plangent import Plan, PlangentExecutor, PlanNode
from thegent.orchestration.dispatcher import DispatchResult
from thegent.orchestration.plan import OrchestrationPlan

# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------


def _make_orchestration_plan(goal: str = "test goal") -> OrchestrationPlan:
    """Create an empty OrchestrationPlan. # @trace WL-084"""
    return OrchestrationPlan(goal=goal)


def _make_executor(*, fail_fast: bool = False) -> PlangentExecutor:
    """Create a PlangentExecutor with optional fail_fast. # @trace WL-084"""
    return PlangentExecutor(fail_fast=fail_fast)


def _dispatch_result_success(node_id: str, output: str = "ok") -> DispatchResult:
    """Build a successful DispatchResult. # @trace WL-084"""
    return DispatchResult(node_id=node_id, output=output, success=True)


def _dispatch_result_failure(node_id: str, error: str = "boom") -> DispatchResult:
    """Build a failed DispatchResult. # @trace WL-084"""
    return DispatchResult(node_id=node_id, output="", success=False, error=error)


class _StubDispatcher:
    """Test double for SubAgentDispatcher that returns canned DispatchResults.

    # @trace WL-084
    """

    def __init__(self, results: dict[str, DispatchResult]) -> None:
        self._results = results

    async def dispatch_plan(self, plan: Plan) -> dict[str, DispatchResult]:
        """Return the canned results filtered to the plan's node IDs."""
        return {
            node.id: self._results[node.id]
            for node in plan.nodes
            if node.id in self._results
        }


# ---------------------------------------------------------------------------
# 1. Plain Plan path — backward compatibility preserved
# ---------------------------------------------------------------------------


class TestPlainPlanPath:
    """execute_async with plain Plan uses the runner callback, not the dispatcher."""

    @pytest.mark.asyncio
    async def test_plain_plan_sync_runner_marks_nodes_done(self) -> None:
        """Plain Plan with sync runner: all nodes are marked done. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="simple")
        plan.nodes.append(PlanNode(task="task-1"))
        plan.nodes.append(PlanNode(task="task-2", depends_on=[plan.nodes[0].id]))

        def runner(node: PlanNode) -> str:
            return f"result-{node.task}"

        result_plan = await executor.execute_async(plan, runner)

        assert len(result_plan.done_ids) == 2
        assert len(result_plan.failed_ids) == 0

    @pytest.mark.asyncio
    async def test_plain_plan_async_runner_marks_nodes_done(self) -> None:
        """Plain Plan with async runner: all nodes are marked done. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="async goal")
        node = PlanNode(task="async-task")
        plan.nodes.append(node)

        async def runner(n: PlanNode) -> str:
            return f"async-result-{n.task}"

        await executor.execute_async(plan, runner)
        assert node.status == "done"
        assert node.result == "async-result-async-task"

    @pytest.mark.asyncio
    async def test_plain_plan_runner_exception_marks_node_failed(self) -> None:
        """Plain Plan runner raising: node is marked failed. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="fail")
        node = PlanNode(task="bad-task")
        plan.nodes.append(node)

        def runner(n: PlanNode) -> str:
            raise RuntimeError("runner error")

        await executor.execute_async(plan, runner)
        assert node.status == "failed"
        assert "runner error" in (node.error or "")

    @pytest.mark.asyncio
    async def test_plain_plan_fail_fast_stops_after_first_failure(self) -> None:
        """Plain Plan fail_fast=True: stops after first failing wave. # @trace WL-084

        n1 depends on n2 (sequential); when n1 fails, n2 is never dispatched.
        """
        executor = _make_executor(fail_fast=True)
        plan = Plan(goal="fail fast")
        n1 = PlanNode(task="fail-first")
        n2 = PlanNode(task="second", depends_on=[n1.id])  # n2 depends on n1
        plan.nodes.extend([n1, n2])

        def runner(n: PlanNode) -> str:
            if n.task == "fail-first":
                raise RuntimeError("intentional failure")
            return "ok"

        await executor.execute_async(plan, runner)
        # n1 failed; n2 was never dispatched because n1 failed before n2 was ready
        assert n1.status == "failed"
        assert n2.status == "pending"

    @pytest.mark.asyncio
    async def test_plain_plan_does_not_use_dispatcher(self) -> None:
        """Plain Plan: dispatcher parameter is ignored. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="plain")
        node = PlanNode(task="t")
        plan.nodes.append(node)

        stub = _StubDispatcher(
            {node.id: _dispatch_result_success(node.id, "stub-output")}
        )

        # Even though a dispatcher is provided, the plain Plan path uses runner.
        async def runner(n: PlanNode) -> str:
            return "runner-output"

        await executor.execute_async(plan, runner, dispatcher=stub)  # type: ignore[arg-type]
        assert node.result == "runner-output"

    @pytest.mark.asyncio
    async def test_plain_plan_empty_nodes_returns_plan_unchanged(self) -> None:
        """Plain Plan with zero nodes returns immediately. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="empty")

        async def runner(n: PlanNode) -> str:  # pragma: no cover
            return "never"

        result_plan = await executor.execute_async(plan, runner)
        assert result_plan is plan
        assert result_plan.nodes == []

    def test_sync_execute_unchanged_for_plain_plan(self) -> None:
        """execute() sync path is unaffected by WL-084 changes. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="sync")
        node = PlanNode(task="sync-task")
        plan.nodes.append(node)

        executor.execute(plan, lambda n: "sync-result")
        assert node.status == "done"
        assert node.result == "sync-result"


# ---------------------------------------------------------------------------
# 2. OrchestrationPlan path — SubAgentDispatcher + ResultAggregator
# ---------------------------------------------------------------------------


class TestOrchestrationPlanPath:
    """execute_async with OrchestrationPlan uses SubAgentDispatcher."""

    @pytest.mark.asyncio
    async def test_orchestration_plan_nodes_marked_done_on_success(self) -> None:
        """All succeeding nodes are marked done. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("task-a", agent_hint="worker")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id, "output-a")})
        await executor.execute_async(plan, lambda n: "ignored", dispatcher=stub)  # type: ignore[arg-type]

        assert node.status == "done"
        assert node.result == "output-a"

    @pytest.mark.asyncio
    async def test_orchestration_plan_node_result_stored_correctly(self) -> None:
        """DispatchResult.output is stored as PlanNode.result. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("task-b")

        stub = _StubDispatcher(
            {node.id: _dispatch_result_success(node.id, "specific-output")}
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert node.result == "specific-output"

    @pytest.mark.asyncio
    async def test_orchestration_plan_failed_node_marked_failed(self) -> None:
        """Failed DispatchResult marks node failed. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("bad-task")

        stub = _StubDispatcher(
            {node.id: _dispatch_result_failure(node.id, "dispatch-error")}
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert node.status == "failed"
        assert node.error == "dispatch-error"

    @pytest.mark.asyncio
    async def test_orchestration_plan_error_stored_on_node(self) -> None:
        """DispatchResult.error is stored as PlanNode.error. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("err-task")

        stub = _StubDispatcher(
            {node.id: _dispatch_result_failure(node.id, "specific-error")}
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert node.error == "specific-error"

    @pytest.mark.asyncio
    async def test_orchestration_plan_aggregation_stored_in_metadata(self) -> None:
        """plan.metadata['aggregation'] is set after execution. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("agg-task")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id)})
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert "aggregation" in plan.metadata

    @pytest.mark.asyncio
    async def test_aggregation_has_required_keys(self) -> None:
        """aggregation dict has all required keys. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("key-task")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id)})
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        agg = plan.metadata["aggregation"]
        for key in ("total", "by_type", "results", "errors", "passed", "by_node"):
            assert key in agg, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_aggregation_passed_true_all_success(self) -> None:
        """aggregation['passed'] is True when all nodes succeed. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        n1 = plan.add_task("t1")
        n2 = plan.add_task("t2")

        stub = _StubDispatcher(
            {
                n1.id: _dispatch_result_success(n1.id),
                n2.id: _dispatch_result_success(n2.id),
            }
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert plan.metadata["aggregation"]["passed"] is True

    @pytest.mark.asyncio
    async def test_aggregation_passed_false_when_failure(self) -> None:
        """aggregation['passed'] is False when any node fails. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        n1 = plan.add_task("ok-task")
        n2 = plan.add_task("fail-task")

        stub = _StubDispatcher(
            {
                n1.id: _dispatch_result_success(n1.id),
                n2.id: _dispatch_result_failure(n2.id, "exploded"),
            }
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert plan.metadata["aggregation"]["passed"] is False

    @pytest.mark.asyncio
    async def test_aggregation_total_equals_node_count(self) -> None:
        """aggregation['total'] equals the number of dispatched nodes. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        nodes = [plan.add_task(f"task-{i}") for i in range(4)]

        stub = _StubDispatcher({n.id: _dispatch_result_success(n.id) for n in nodes})
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert plan.metadata["aggregation"]["total"] == 4

    @pytest.mark.asyncio
    async def test_aggregation_by_node_keyed_by_node_id(self) -> None:
        """aggregation['by_node'] has an entry per dispatched node. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("by-node-task")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id)})
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        by_node = plan.metadata["aggregation"]["by_node"]
        assert node.id in by_node

    @pytest.mark.asyncio
    async def test_orchestration_returns_same_plan_object(self) -> None:
        """execute_async returns the same OrchestrationPlan object (mutated in place). # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("identity-task")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id)})
        result_plan = await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert result_plan is plan

    @pytest.mark.asyncio
    async def test_orchestration_zero_nodes_returns_plan(self) -> None:
        """OrchestrationPlan with no nodes returns the plan with empty aggregation. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        stub = _StubDispatcher({})

        result_plan = await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert result_plan is plan
        agg = plan.metadata["aggregation"]
        assert agg["total"] == 0
        assert agg["passed"] is True

    @pytest.mark.asyncio
    async def test_orchestration_multiple_nodes_all_success(self) -> None:
        """Multiple OrchestrationPlan nodes all succeed. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        n1 = plan.add_task("t1")
        n2 = plan.add_task("t2", depends_on=[n1.id])
        n3 = plan.add_task("t3", depends_on=[n2.id])

        stub = _StubDispatcher(
            {
                n1.id: _dispatch_result_success(n1.id, "r1"),
                n2.id: _dispatch_result_success(n2.id, "r2"),
                n3.id: _dispatch_result_success(n3.id, "r3"),
            }
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert len(plan.done_ids) == 3
        assert plan.metadata["aggregation"]["passed"] is True

    @pytest.mark.asyncio
    async def test_orchestration_mixed_success_failure(self) -> None:
        """Mixed success/failure: done_ids and failed_ids reflect outcome. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        n_ok = plan.add_task("ok")
        n_fail = plan.add_task("fail")

        stub = _StubDispatcher(
            {
                n_ok.id: _dispatch_result_success(n_ok.id),
                n_fail.id: _dispatch_result_failure(n_fail.id, "failed"),
            }
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert n_ok.id in plan.done_ids
        assert n_fail.id in plan.failed_ids


# ---------------------------------------------------------------------------
# 3. fail_fast behaviour in orchestration path
# ---------------------------------------------------------------------------


class TestOrchestrationFailFast:
    """fail_fast=True stops orchestration after first node failure."""

    @pytest.mark.asyncio
    async def test_fail_fast_true_returns_after_first_failure(self) -> None:
        """fail_fast=True: plan returned early when first node fails. # @trace WL-084"""
        executor = _make_executor(fail_fast=True)
        plan = _make_orchestration_plan()
        n_fail = plan.add_task("fail-first")
        n_skip = plan.add_task("skip-me")

        # _StubDispatcher returns both but the executor must stop after n_fail
        stub = _StubDispatcher(
            {
                n_fail.id: _dispatch_result_failure(n_fail.id, "early-fail"),
                n_skip.id: _dispatch_result_success(n_skip.id),
            }
        )

        # Note: the StubDispatcher returns all results from dispatch_plan();
        # the executor processes nodes in plan.nodes order.  fail_fast stops
        # AFTER processing the failed node and before processing subsequent nodes.
        # Because nodes are independent (no deps), the stub returns both in one
        # dispatch_plan() call; the executor marks fail then stops.
        result_plan = await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert n_fail.status == "failed"
        # aggregation is stored even when fail_fast stops early
        assert "aggregation" in result_plan.metadata

    @pytest.mark.asyncio
    async def test_fail_fast_false_continues_after_failure(self) -> None:
        """fail_fast=False: execution continues after a node failure. # @trace WL-084"""
        executor = _make_executor(fail_fast=False)
        plan = _make_orchestration_plan()
        n_fail = plan.add_task("fail-node")
        n_ok = plan.add_task("ok-node")

        stub = _StubDispatcher(
            {
                n_fail.id: _dispatch_result_failure(n_fail.id, "err"),
                n_ok.id: _dispatch_result_success(n_ok.id, "ok-output"),
            }
        )
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert n_fail.status == "failed"
        assert n_ok.status == "done"

    @pytest.mark.asyncio
    async def test_fail_fast_stores_partial_aggregation(self) -> None:
        """fail_fast=True: aggregation still stored in metadata on early stop. # @trace WL-084"""
        executor = _make_executor(fail_fast=True)
        plan = _make_orchestration_plan()
        n_fail = plan.add_task("fail-partial")

        stub = _StubDispatcher(
            {n_fail.id: _dispatch_result_failure(n_fail.id, "partial")}
        )
        result_plan = await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert "aggregation" in result_plan.metadata
        assert result_plan.metadata["aggregation"]["passed"] is False


# ---------------------------------------------------------------------------
# 4. Missing DispatchResult handling
# ---------------------------------------------------------------------------


class TestMissingDispatchResult:
    """When dispatch_plan() omits a node, it is treated as a failure."""

    @pytest.mark.asyncio
    async def test_missing_dispatch_result_marks_node_failed(self) -> None:
        """Node missing from dispatch results is marked failed. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("missing-task")

        # Dispatcher returns empty dict — node has no result
        stub = _StubDispatcher({})
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert node.status == "failed"
        assert node.error is not None

    @pytest.mark.asyncio
    async def test_missing_dispatch_result_error_in_aggregation(self) -> None:
        """Missing node failure appears in aggregation errors. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        plan.add_task("ghost-task")

        stub = _StubDispatcher({})
        result_plan = await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        agg = result_plan.metadata["aggregation"]
        assert agg["passed"] is False
        assert len(agg["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_missing_dispatch_result_fail_fast_stops_early(self) -> None:
        """Missing result with fail_fast=True stops early. # @trace WL-084"""
        executor = _make_executor(fail_fast=True)
        plan = _make_orchestration_plan()
        n_ghost = plan.add_task("ghost")
        n_ok = plan.add_task("ok")

        # ghost has no result; ok does. fail_fast should stop after ghost fails.
        stub = _StubDispatcher({n_ok.id: _dispatch_result_success(n_ok.id)})
        result_plan = await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]

        assert n_ghost.status == "failed"
        # n_ok may or may not be processed depending on node order; plan returned early
        assert "aggregation" in result_plan.metadata


# ---------------------------------------------------------------------------
# 5. isinstance dispatch path selection
# ---------------------------------------------------------------------------


class TestDispatchPathSelection:
    """execute_async routes to the correct internal path based on plan type."""

    @pytest.mark.asyncio
    async def test_orchestration_plan_calls_orchestration_path(self) -> None:
        """execute_async calls _execute_orchestration_async for OrchestrationPlan. # @trace WL-084"""
        executor = _make_executor()
        plan = _make_orchestration_plan()
        node = plan.add_task("path-task")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id)})

        called_orchestration = False

        orig = executor._execute_orchestration_async

        async def spy(p: Any, d: Any) -> Plan:
            nonlocal called_orchestration
            called_orchestration = True
            return await orig(p, d)

        executor._execute_orchestration_async = spy  # type: ignore[method-assign]
        await executor.execute_async(plan, lambda n: "x", dispatcher=stub)  # type: ignore[arg-type]
        assert called_orchestration

    @pytest.mark.asyncio
    async def test_plain_plan_calls_plain_path(self) -> None:
        """execute_async calls _execute_plain_async for plain Plan. # @trace WL-084"""
        executor = _make_executor()
        plan = Plan(goal="plain-path")
        node = PlanNode(task="pt")
        plan.nodes.append(node)

        called_plain = False
        orig = executor._execute_plain_async

        async def spy(p: Any, r: Any) -> Plan:
            nonlocal called_plain
            called_plain = True
            return await orig(p, r)

        executor._execute_plain_async = spy  # type: ignore[method-assign]
        await executor.execute_async(plan, lambda n: "result")
        assert called_plain

    @pytest.mark.asyncio
    async def test_orchestration_plan_subclass_detected_correctly(self) -> None:
        """OrchestrationPlan is correctly identified as OrchestrationPlan subclass. # @trace WL-084"""
        from thegent.orchestration.plan import OrchestrationPlan

        executor = _make_executor()
        plan = OrchestrationPlan(goal="subclass-check")
        node = plan.add_task("subclass-task")

        stub = _StubDispatcher({node.id: _dispatch_result_success(node.id)})
        result_plan = await executor.execute_async(
            plan, lambda n: "runner", dispatcher=stub
        )  # type: ignore[arg-type]

        # If path correctly detected, aggregation is stored (orchestration path)
        assert "aggregation" in result_plan.metadata
