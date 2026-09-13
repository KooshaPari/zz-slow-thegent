"""Tests for the Agent Hierarchy MVP (src/thegent/agents/hierarchy.py).

This file is the canonical test suite for the new SmolAgents-integrated
AgentHierarchyManager in thegent.agents.hierarchy.

Covers:
- AgentCapability enum membership
- AgentState enum membership
- AgentNode creation, capability matching, serialisation
- AgentHierarchyManager: spawn_agent, parent/child wiring, root detection
- Validation: duplicate IDs, missing parent
- Route task: capability_match, round_robin, least_loaded
- Execute task: mock executor, state transitions, counters
- Execute task: smolagent integration path
- Execute task: error propagation
- Parallel execution: ordering, concurrency, mixed success
- collect_results: filtering by agent and success flag
- Tree traversal: get_children, get_ancestors, get_descendants
- get_hierarchy_tree: nested dict structure
- remove_agent: unlinking, root clearing, child reparenting
- Summary dict correctness
- End-to-end orchestrator -> specialist flow
"""

from __future__ import annotations

import threading
from typing import Any
from unittest.mock import MagicMock

import pytest

from thegent.agents.hierarchy import (
    AgentCapability,
    AgentHierarchyManager,
    AgentNode,
    AgentState,
    RoutingStrategy,
    TaskResult,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_executor(output: Any = "ok", success: bool = True, error: str | None = None):
    """Return a simple callable that plays the role of task_executor."""

    def _executor(node: AgentNode, task: str, context: dict[str, Any]) -> TaskResult:
        return TaskResult(
            task_id="",  # will be overwritten by execute_task
            agent_id=node.agent_id,
            success=success,
            output=output,
            error=error,
        )

    return _executor


@pytest.fixture
def manager() -> AgentHierarchyManager:
    """Hierarchy manager with a default succeed-all executor."""
    return AgentHierarchyManager(task_executor=_make_executor("result"))


@pytest.fixture
def populated_manager() -> AgentHierarchyManager:
    """Manager pre-populated with an orchestrator and three specialists."""
    m = AgentHierarchyManager(task_executor=_make_executor("result"))
    m.spawn_agent(
        {AgentCapability.ORCHESTRATE},
        agent_id="orch",
        name="orchestrator",
        description="Root orchestrator",
    )
    m.spawn_agent(
        {AgentCapability.CODE, AgentCapability.TEST},
        agent_id="coder",
        parent_id="orch",
        name="coder",
    )
    m.spawn_agent(
        {AgentCapability.RESEARCH},
        agent_id="researcher",
        parent_id="orch",
        name="researcher",
    )
    m.spawn_agent(
        {AgentCapability.REVIEW, AgentCapability.SECURITY},
        agent_id="reviewer",
        parent_id="orch",
        name="reviewer",
    )
    return m


# ---------------------------------------------------------------------------
# 1. AgentCapability enum
# ---------------------------------------------------------------------------


class TestAgentCapabilityEnum:
    def test_all_expected_capabilities_exist(self):
        expected = {
            "CODE",
            "RESEARCH",
            "REVIEW",
            "TEST",
            "DEPLOY",
            "PLAN",
            "SECURITY",
            "DATA",
            "DOCUMENTATION",
            "ORCHESTRATE",
        }
        actual = {c.name for c in AgentCapability}
        assert expected.issubset(actual)

    def test_capabilities_are_distinct(self):
        caps = list(AgentCapability)
        assert len(caps) == len(set(caps))


# ---------------------------------------------------------------------------
# 2. AgentState enum
# ---------------------------------------------------------------------------


class TestAgentStateEnum:
    def test_all_states_exist(self):
        expected = {"idle", "running", "completed", "failed", "cancelled"}
        actual = {s.value for s in AgentState}
        assert expected == actual


# ---------------------------------------------------------------------------
# 3. AgentNode
# ---------------------------------------------------------------------------


class TestAgentNode:
    def test_default_name_is_generated(self):
        node = AgentNode(agent_id="abc123")
        assert node.name  # non-empty
        assert "abc1" in node.name  # uses first chars of agent_id

    def test_explicit_name_preserved(self):
        node = AgentNode(agent_id="x", name="my-agent")
        assert node.name == "my-agent"

    def test_has_capability_true(self):
        node = AgentNode(capabilities={AgentCapability.CODE})
        assert node.has_capability(AgentCapability.CODE) is True

    def test_has_capability_false(self):
        node = AgentNode(capabilities={AgentCapability.CODE})
        assert node.has_capability(AgentCapability.RESEARCH) is False

    def test_has_any_capability_overlap(self):
        node = AgentNode(capabilities={AgentCapability.CODE, AgentCapability.TEST})
        assert node.has_any_capability({AgentCapability.TEST, AgentCapability.DEPLOY}) is True

    def test_has_any_capability_no_overlap(self):
        node = AgentNode(capabilities={AgentCapability.CODE})
        assert node.has_any_capability({AgentCapability.RESEARCH}) is False

    def test_to_dict_excludes_smolagent(self):
        mock_agent = MagicMock()
        node = AgentNode(agent_id="n1", capabilities={AgentCapability.CODE}, smolagent=mock_agent)
        d = node.to_dict()
        assert "smolagent" not in d
        assert "CODE" in d["capabilities"]
        assert d["agent_id"] == "n1"

    def test_to_dict_contains_required_keys(self):
        node = AgentNode(agent_id="n1", capabilities={AgentCapability.PLAN})
        d = node.to_dict()
        required = {
            "agent_id",
            "capabilities",
            "model",
            "name",
            "description",
            "parent_id",
            "children",
            "state",
            "active_task_count",
            "total_tasks_completed",
            "metadata",
        }
        assert required.issubset(d.keys())


# ---------------------------------------------------------------------------
# 4. spawn_agent
# ---------------------------------------------------------------------------


class TestSpawnAgent:
    def test_spawn_root_sets_root_id(self):
        m = AgentHierarchyManager()
        node = m.spawn_agent({AgentCapability.ORCHESTRATE}, agent_id="root")
        assert m.get_root() is node

    def test_spawn_child_wires_parent_link(self):
        m = AgentHierarchyManager()
        m.spawn_agent({AgentCapability.ORCHESTRATE}, agent_id="root")
        child = m.spawn_agent({AgentCapability.CODE}, agent_id="child", parent_id="root")
        assert child.parent_id == "root"
        assert "child" in m.get_node("root").children

    def test_spawn_raises_on_missing_parent(self):
        m = AgentHierarchyManager()
        with pytest.raises(ValueError, match="not found"):
            m.spawn_agent({AgentCapability.CODE}, agent_id="orphan", parent_id="nonexistent")

    def test_spawn_raises_on_duplicate_id(self):
        m = AgentHierarchyManager()
        m.spawn_agent({AgentCapability.CODE}, agent_id="dup")
        with pytest.raises(ValueError, match="already registered"):
            m.spawn_agent({AgentCapability.CODE}, agent_id="dup")

    def test_spawn_auto_generates_id_when_none(self):
        m = AgentHierarchyManager()
        node = m.spawn_agent({AgentCapability.CODE})
        assert node.agent_id  # uuid generated
        assert m.get_node(node.agent_id) is node

    def test_spawn_metadata_stored(self):
        m = AgentHierarchyManager()
        m.spawn_agent({AgentCapability.CODE}, agent_id="n1", metadata={"tier": "paid"})
        assert m.get_node("n1").metadata["tier"] == "paid"


# ---------------------------------------------------------------------------
# 5. list_agents / get_node / get_root
# ---------------------------------------------------------------------------


class TestAgentRegistry:
    def test_list_agents_returns_all(self, populated_manager):
        agents = populated_manager.list_agents()
        assert len(agents) == 4  # orch + 3 specialists

    def test_get_node_returns_none_for_unknown(self, manager):
        assert manager.get_node("nope") is None

    def test_get_root_none_when_empty(self):
        m = AgentHierarchyManager()
        assert m.get_root() is None


# ---------------------------------------------------------------------------
# 6. route_task
# ---------------------------------------------------------------------------


class TestRouteTask:
    def test_route_returns_none_when_no_match(self, populated_manager):
        result = populated_manager.route_task({AgentCapability.DATA})
        assert result is None

    def test_route_capability_match_full_match_preferred(self, populated_manager):
        # coder has CODE + TEST; reviewer has REVIEW + SECURITY
        # Asking for CODE+TEST should prefer coder (full match)
        node = populated_manager.route_task({AgentCapability.CODE, AgentCapability.TEST})
        assert node is not None
        assert node.agent_id == "coder"

    def test_route_capability_match_partial(self, populated_manager):
        # Only coder has CODE
        node = populated_manager.route_task({AgentCapability.CODE})
        assert node is not None
        assert node.agent_id == "coder"

    def test_route_excludes_specified_ids(self, populated_manager):
        node = populated_manager.route_task({AgentCapability.CODE}, exclude_ids={"coder"})
        # No other agent has CODE
        assert node is None

    def test_route_round_robin_cycles(self):
        m = AgentHierarchyManager(routing_strategy=RoutingStrategy.ROUND_ROBIN)
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        m.spawn_agent({AgentCapability.CODE}, agent_id="a2")
        first = m.route_task({AgentCapability.CODE})
        second = m.route_task({AgentCapability.CODE})
        assert first is not None
        assert second is not None
        assert first.agent_id != second.agent_id

    def test_route_least_loaded_picks_idle(self):
        m = AgentHierarchyManager(
            routing_strategy=RoutingStrategy.LEAST_LOADED,
            task_executor=_make_executor(),
        )
        m.spawn_agent({AgentCapability.CODE}, agent_id="busy")
        m.spawn_agent({AgentCapability.CODE}, agent_id="idle")
        m.get_node("busy").active_task_count = 5
        node = m.route_task({AgentCapability.CODE})
        assert node.agent_id == "idle"


# ---------------------------------------------------------------------------
# 7. execute_task — state transitions and counters
# ---------------------------------------------------------------------------


class TestExecuteTask:
    def test_execute_task_succeeds(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        result = manager.execute_task("a1", "do something")
        assert result.success is True
        assert result.output == "result"

    def test_execute_task_failure_from_executor(self):
        m = AgentHierarchyManager(task_executor=_make_executor(success=False, error="oops"))
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        result = m.execute_task("a1", "fail me")
        assert result.success is False
        assert "oops" in (result.error or "")

    def test_execute_task_raises_for_unknown_agent(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.execute_task("ghost", "hello")

    def test_execute_task_raises_without_executor_or_smolagent(self):
        m = AgentHierarchyManager()  # No executor
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        with pytest.raises(RuntimeError, match="No smolagent"):
            m.execute_task("a1", "do it")

    def test_execute_task_increments_total_tasks_completed(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.execute_task("a1", "task1")
        manager.execute_task("a1", "task2")
        assert manager.get_node("a1").total_tasks_completed == 2

    def test_execute_task_active_count_returns_to_zero(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.execute_task("a1", "task")
        assert manager.get_node("a1").active_task_count == 0

    def test_execute_task_returns_idle_after_success(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.execute_task("a1", "task")
        assert manager.get_node("a1").state == AgentState.IDLE

    def test_execute_task_uses_smolagent_when_present(self):
        mock_sa = MagicMock()
        mock_sa.run.return_value = "smolagent-output"

        m = AgentHierarchyManager()
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1", smolagent=mock_sa)
        result = m.execute_task("a1", "run this")
        assert result.success is True
        assert result.output == "smolagent-output"
        mock_sa.run.assert_called_once_with("run this")

    def test_execute_task_stores_result(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        result = manager.execute_task("a1", "task", task_id="tid-42")
        assert manager.get_result("tid-42") is result

    def test_execute_task_explicit_task_id_honoured(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        result = manager.execute_task("a1", "task", task_id="custom-id")
        assert result.task_id == "custom-id"


# ---------------------------------------------------------------------------
# 8. execute_parallel
# ---------------------------------------------------------------------------


class TestExecuteParallel:
    def test_parallel_returns_all_results(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.spawn_agent({AgentCapability.RESEARCH}, agent_id="a2")
        tasks = [
            {"agent_id": "a1", "task_description": "code task"},
            {"agent_id": "a2", "task_description": "research task"},
        ]
        results = manager.execute_parallel(tasks)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_parallel_preserves_order(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        task_ids = ["t1", "t2", "t3"]
        tasks = [{"agent_id": "a1", "task_description": f"task {tid}", "task_id": tid} for tid in task_ids]
        results = manager.execute_parallel(tasks)
        result_ids = [r.task_id for r in results]
        assert result_ids == task_ids

    def test_parallel_handles_mixed_success(self):
        call_count = [0]

        def _alternating(node, task, ctx):
            call_count[0] += 1
            success = call_count[0] % 2 == 1
            return TaskResult(task_id="", agent_id=node.agent_id, success=success)

        m = AgentHierarchyManager(task_executor=_alternating)
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        tasks = [{"agent_id": "a1", "task_description": f"t{i}"} for i in range(4)]
        results = m.execute_parallel(tasks)
        successes = [r.success for r in results]
        assert True in successes
        assert False in successes


# ---------------------------------------------------------------------------
# 9. collect_results
# ---------------------------------------------------------------------------


class TestCollectResults:
    def test_collect_all(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.execute_task("a1", "t1")
        manager.execute_task("a1", "t2")
        assert len(manager.collect_results()) == 2

    def test_collect_filtered_by_agent(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.spawn_agent({AgentCapability.RESEARCH}, agent_id="a2")
        manager.execute_task("a1", "t1")
        manager.execute_task("a2", "t2")
        results = manager.collect_results(agent_id="a1")
        assert all(r.agent_id == "a1" for r in results)
        assert len(results) == 1

    def test_collect_success_only(self):
        m = AgentHierarchyManager(task_executor=_make_executor(success=False))
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        m.execute_task("a1", "fail")
        assert m.collect_results(success_only=True) == []

    def test_clear_results(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.execute_task("a1", "t1")
        manager.clear_results()
        assert manager.collect_results() == []


# ---------------------------------------------------------------------------
# 10. Tree traversal
# ---------------------------------------------------------------------------


class TestTreeTraversal:
    def test_get_children(self, populated_manager):
        children = populated_manager.get_children("orch")
        child_ids = {c.agent_id for c in children}
        assert child_ids == {"coder", "researcher", "reviewer"}

    def test_get_children_empty_for_leaf(self, populated_manager):
        assert populated_manager.get_children("coder") == []

    def test_get_ancestors(self, populated_manager):
        ancestors = populated_manager.get_ancestors("coder")
        assert len(ancestors) == 1
        assert ancestors[0].agent_id == "orch"

    def test_get_ancestors_empty_for_root(self, populated_manager):
        assert populated_manager.get_ancestors("orch") == []

    def test_get_descendants(self, populated_manager):
        descendants = populated_manager.get_descendants("orch")
        desc_ids = {d.agent_id for d in descendants}
        assert desc_ids == {"coder", "researcher", "reviewer"}

    def test_get_descendants_empty_for_leaf(self, populated_manager):
        assert populated_manager.get_descendants("coder") == []

    def test_get_hierarchy_tree_structure(self, populated_manager):
        tree = populated_manager.get_hierarchy_tree()
        assert tree["agent_id"] == "orch"
        assert len(tree["children"]) == 3
        child_names = {c["agent_id"] for c in tree["children"]}
        assert child_names == {"coder", "researcher", "reviewer"}

    def test_get_hierarchy_tree_custom_root(self, populated_manager):
        tree = populated_manager.get_hierarchy_tree(root_id="coder")
        assert tree["agent_id"] == "coder"
        assert tree["children"] == []

    def test_get_hierarchy_tree_empty_when_unknown_root(self, populated_manager):
        tree = populated_manager.get_hierarchy_tree(root_id="nonexistent")
        assert tree == {}


# ---------------------------------------------------------------------------
# 11. remove_agent
# ---------------------------------------------------------------------------


class TestRemoveAgent:
    def test_remove_leaf_node(self, populated_manager):
        assert populated_manager.remove_agent("coder") is True
        assert populated_manager.get_node("coder") is None
        # Parent's children list updated
        assert "coder" not in populated_manager.get_node("orch").children

    def test_remove_nonexistent_returns_false(self, manager):
        assert manager.remove_agent("ghost") is False

    def test_remove_root_clears_root_id(self):
        m = AgentHierarchyManager()
        m.spawn_agent({AgentCapability.ORCHESTRATE}, agent_id="root")
        m.remove_agent("root")
        assert m.get_root() is None


# ---------------------------------------------------------------------------
# 12. summary
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_structure(self, manager):
        manager.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        manager.execute_task("a1", "t1")
        s = manager.summary()
        assert s["total_agents"] == 1
        assert s["total_tasks_run"] == 1
        assert s["total_tasks_succeeded"] == 1
        assert s["total_tasks_failed"] == 0
        assert isinstance(s["agents"], list)

    def test_summary_counts_failures(self):
        m = AgentHierarchyManager(task_executor=_make_executor(success=False))
        m.spawn_agent({AgentCapability.CODE}, agent_id="a1")
        m.execute_task("a1", "bad task")
        s = m.summary()
        assert s["total_tasks_failed"] == 1
        assert s["total_tasks_succeeded"] == 0


# ---------------------------------------------------------------------------
# 13. End-to-end orchestrator -> specialist flow
# ---------------------------------------------------------------------------


class TestEndToEndFlow:
    def test_orchestrator_routes_and_executes(self):
        """Simulate orchestrator picking the right specialist for each task."""
        log: list[str] = []

        def executor(node: AgentNode, task: str, ctx: dict) -> TaskResult:
            log.append(f"{node.agent_id}:{task}")
            return TaskResult(task_id="", agent_id=node.agent_id, success=True, output="done")

        m = AgentHierarchyManager(
            routing_strategy=RoutingStrategy.CAPABILITY_MATCH,
            task_executor=executor,
        )
        m.spawn_agent({AgentCapability.ORCHESTRATE}, agent_id="orch")
        m.spawn_agent({AgentCapability.CODE}, agent_id="coder", parent_id="orch")
        m.spawn_agent({AgentCapability.RESEARCH}, agent_id="scout", parent_id="orch")

        # Route and execute a code task
        agent = m.route_task({AgentCapability.CODE})
        assert agent.agent_id == "coder"
        m.execute_task(agent.agent_id, "write tests")

        # Route and execute a research task
        agent = m.route_task({AgentCapability.RESEARCH})
        assert agent.agent_id == "scout"
        m.execute_task(agent.agent_id, "research options")

        assert len(m.collect_results()) == 2
        assert "coder:write tests" in log
        assert "scout:research options" in log

    def test_parallel_specialist_execution(self):
        """Multiple specialists run in parallel on independent tasks."""
        call_order: list[str] = []
        lock = threading.Lock()

        def executor(node: AgentNode, task: str, ctx: dict) -> TaskResult:
            with lock:
                call_order.append(node.agent_id)
            return TaskResult(task_id="", agent_id=node.agent_id, success=True)

        m = AgentHierarchyManager(task_executor=executor)
        m.spawn_agent({AgentCapability.CODE}, agent_id="c1")
        m.spawn_agent({AgentCapability.RESEARCH}, agent_id="r1")
        m.spawn_agent({AgentCapability.REVIEW}, agent_id="rv1")

        tasks = [
            {"agent_id": "c1", "task_description": "code"},
            {"agent_id": "r1", "task_description": "research"},
            {"agent_id": "rv1", "task_description": "review"},
        ]
        results = m.execute_parallel(tasks)
        assert len(results) == 3
        assert all(r.success for r in results)
        # All three agents participated
        assert set(call_order) == {"c1", "r1", "rv1"}
