"""Tests for DagPrioritizer (swarm-dag-prioritization).

@trace FR-ORC-020 -- DAG task addition and deduplication.
@trace FR-ORC-021 -- Single-node DAG: critical path is the node itself.
@trace FR-ORC-022 -- Linear chain critical path equals the full chain.
@trace FR-ORC-023 -- Diamond DAG: critical path follows the longer branch.
@trace FR-ORC-024 -- Multiple independent paths: critical path is the longest.
@trace FR-ORC-025 -- Cycle detection raises DagCycleError.
@trace FR-ORC-026 -- Ready tasks are filtered by completed set and sorted by priority.
@trace FR-ORC-027 -- Topological sort produces a valid execution order.
@trace FR-ORC-028 -- Priority score is higher for tasks on the critical path.
@trace FR-ORC-029 -- Unknown dependency raises ValueError.
@trace FR-ORC-030 -- Empty DAG returns empty results.
"""

from __future__ import annotations

import pytest

from thegent.orchestration.execution.dag_prioritization import (
    DagCycleError,
    DagPrioritizer,
    DagTask,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make(
    task_id: str,
    duration: float = 1.0,
    deps: list[str] | None = None,
    priority: int = 0,
) -> DagTask:
    return DagTask(
        task_id=task_id,
        estimated_duration_s=duration,
        dependencies=deps or [],
        priority=priority,
    )


def _topo_valid(order: list[str], prioritizer: DagPrioritizer) -> bool:
    """Return True iff *order* is a valid topological ordering."""
    position = {tid: i for i, tid in enumerate(order)}
    for task in prioritizer._tasks.values():
        for dep in task.dependencies:
            if position[dep] >= position[task.task_id]:
                return False
    return True


# ---------------------------------------------------------------------------
# DagTask dataclass
# ---------------------------------------------------------------------------


class TestDagTask:
    """@trace FR-ORC-020"""

    def test_defaults(self) -> None:
        t = DagTask(task_id="x")
        assert t.task_id == "x"
        assert t.estimated_duration_s == 1.0
        assert t.dependencies == []
        assert t.priority == 0

    def test_custom_fields(self) -> None:
        t = DagTask("y", estimated_duration_s=5.0, dependencies=["x"], priority=3)
        assert t.task_id == "y"
        assert t.estimated_duration_s == 5.0
        assert t.dependencies == ["x"]
        assert t.priority == 3

    def test_mutable_deps_are_independent(self) -> None:
        t1 = DagTask("a")
        t2 = DagTask("b")
        t1.dependencies.append("z")
        assert t2.dependencies == []


# ---------------------------------------------------------------------------
# Empty DAG
# ---------------------------------------------------------------------------


class TestEmptyDag:
    """@trace FR-ORC-030"""

    def test_compute_critical_path_empty(self) -> None:
        p = DagPrioritizer()
        assert p.compute_critical_path() == []

    def test_topological_sort_empty(self) -> None:
        p = DagPrioritizer()
        assert p.topological_sort() == []

    def test_ready_tasks_empty(self) -> None:
        p = DagPrioritizer()
        assert p.ready_tasks(completed=set()) == []

    def test_get_priority_score_unknown_raises(self) -> None:
        p = DagPrioritizer()
        with pytest.raises(KeyError):
            p.get_priority_score("nonexistent")


# ---------------------------------------------------------------------------
# Single-node DAG
# ---------------------------------------------------------------------------


class TestSingleNode:
    """@trace FR-ORC-021"""

    @pytest.fixture
    def prioritizer(self) -> DagPrioritizer:
        p = DagPrioritizer()
        p.add_task(_make("solo", duration=3.5))
        return p

    def test_critical_path_is_solo(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.compute_critical_path() == ["solo"]

    def test_topological_sort_is_solo(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.topological_sort() == ["solo"]

    def test_priority_score_equals_duration(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.get_priority_score("solo") == pytest.approx(3.5)

    def test_ready_tasks_no_completed(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed=set()) == ["solo"]

    def test_ready_tasks_completed(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed={"solo"}) == []


# ---------------------------------------------------------------------------
# Linear chain  a → b → c
# ---------------------------------------------------------------------------


class TestLinearChain:
    """@trace FR-ORC-022"""

    @pytest.fixture
    def prioritizer(self) -> DagPrioritizer:
        p = DagPrioritizer()
        p.add_task(_make("a", duration=1.0))
        p.add_task(_make("b", duration=2.0, deps=["a"]))
        p.add_task(_make("c", duration=3.0, deps=["b"]))
        return p

    def test_critical_path_is_full_chain(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.compute_critical_path() == ["a", "b", "c"]

    def test_topological_sort_valid(self, prioritizer: DagPrioritizer) -> None:
        order = prioritizer.topological_sort()
        assert order.index("a") < order.index("b") < order.index("c")

    def test_priority_scores_all_on_critical_path(self, prioritizer: DagPrioritizer) -> None:
        # All three tasks are on the critical path (a→b→c, total = 1+2+3 = 6).
        # Standard CPM: total float is zero for every node on the critical path.
        # Priority score = project_makespan - total_float = 6.0 for all.
        sa = prioritizer.get_priority_score("a")
        sb = prioritizer.get_priority_score("b")
        sc = prioritizer.get_priority_score("c")
        # All on critical path → same priority score (project makespan = 6.0).
        assert sa == pytest.approx(6.0)
        assert sb == pytest.approx(6.0)
        assert sc == pytest.approx(6.0)

    def test_ready_tasks_initial(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed=set())
        assert ready == ["a"]

    def test_ready_tasks_after_a(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed={"a"})
        assert ready == ["b"]

    def test_ready_tasks_after_ab(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed={"a", "b"})
        assert ready == ["c"]

    def test_ready_tasks_all_completed(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed={"a", "b", "c"}) == []


# ---------------------------------------------------------------------------
# Diamond DAG:  a → b → d
#               a → c → d   (b is longer)
# ---------------------------------------------------------------------------


class TestDiamondDag:
    """@trace FR-ORC-023"""

    @pytest.fixture
    def prioritizer(self) -> DagPrioritizer:
        p = DagPrioritizer()
        p.add_task(_make("a", duration=1.0))
        p.add_task(_make("b", duration=5.0, deps=["a"]))  # long branch
        p.add_task(_make("c", duration=1.0, deps=["a"]))  # short branch
        p.add_task(_make("d", duration=1.0, deps=["b", "c"]))
        return p

    def test_critical_path_through_b(self, prioritizer: DagPrioritizer) -> None:
        cp = prioritizer.compute_critical_path()
        assert cp == ["a", "b", "d"]

    def test_critical_path_excludes_c(self, prioritizer: DagPrioritizer) -> None:
        cp = prioritizer.compute_critical_path()
        assert "c" not in cp

    def test_topological_sort_valid(self, prioritizer: DagPrioritizer) -> None:
        order = prioritizer.topological_sort()
        assert _topo_valid(order, prioritizer)
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_b_has_higher_priority_than_c(self, prioritizer: DagPrioritizer) -> None:
        sb = prioritizer.get_priority_score("b")
        sc = prioritizer.get_priority_score("c")
        assert sb > sc

    def test_ready_tasks_initial(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed=set())
        assert ready == ["a"]

    def test_ready_tasks_after_a_both_branches(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed={"a"})
        assert set(ready) == {"b", "c"}
        # b is on the critical path → should be first
        assert ready[0] == "b"

    def test_ready_tasks_after_a_and_b(self, prioritizer: DagPrioritizer) -> None:
        # c is still pending; d cannot start yet
        ready = prioritizer.ready_tasks(completed={"a", "b"})
        assert set(ready) == {"c"}

    def test_ready_tasks_d_unblocked(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed={"a", "b", "c"})
        assert ready == ["d"]


# ---------------------------------------------------------------------------
# Multiple independent paths
# ---------------------------------------------------------------------------


class TestMultipleIndependentPaths:
    """@trace FR-ORC-024"""

    @pytest.fixture
    def prioritizer(self) -> DagPrioritizer:
        p = DagPrioritizer()
        # Path 1: x1 → x2 (total = 3)
        p.add_task(_make("x1", duration=1.0))
        p.add_task(_make("x2", duration=2.0, deps=["x1"]))
        # Path 2: y1 → y2 → y3 (total = 6)
        p.add_task(_make("y1", duration=1.0))
        p.add_task(_make("y2", duration=2.0, deps=["y1"]))
        p.add_task(_make("y3", duration=3.0, deps=["y2"]))
        # Isolated node: z (total = 0.5)
        p.add_task(_make("z", duration=0.5))
        return p

    def test_critical_path_is_longest(self, prioritizer: DagPrioritizer) -> None:
        cp = prioritizer.compute_critical_path()
        assert cp == ["y1", "y2", "y3"]

    def test_topological_sort_valid(self, prioritizer: DagPrioritizer) -> None:
        order = prioritizer.topological_sort()
        assert _topo_valid(order, prioritizer)

    def test_y_nodes_have_highest_priority(self, prioritizer: DagPrioritizer) -> None:
        sy3 = prioritizer.get_priority_score("y3")
        sx2 = prioritizer.get_priority_score("x2")
        sz = prioritizer.get_priority_score("z")
        assert sy3 >= sx2 >= sz

    def test_ready_initial_all_sources(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed=set())
        # x1, y1, z are source nodes; y-path nodes have higher priority
        assert set(ready) == {"x1", "y1", "z"}
        # y1 should appear first (higher priority path)
        assert ready[0] == "y1"


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------


class TestCycleDetection:
    """@trace FR-ORC-025"""

    def test_simple_self_loop(self) -> None:
        p = DagPrioritizer()
        p.add_task(DagTask("a", dependencies=["a"]))
        with pytest.raises(DagCycleError):
            p.topological_sort()

    def test_two_node_cycle(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", deps=["b"]))
        p.add_task(_make("b", deps=["a"]))
        with pytest.raises(DagCycleError):
            p.topological_sort()

    def test_three_node_cycle(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", deps=["c"]))
        p.add_task(_make("b", deps=["a"]))
        p.add_task(_make("c", deps=["b"]))
        with pytest.raises(DagCycleError):
            p.compute_critical_path()

    def test_cycle_embedded_in_larger_graph(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("root"))
        p.add_task(_make("x", deps=["root"]))
        p.add_task(_make("y", deps=["x"]))
        p.add_task(_make("x2", deps=["y"]))  # y depends on x, x2 on y — ok so far
        # Introduce cycle: x depends on x2
        p._tasks["x"].dependencies.append("x2")
        with pytest.raises(DagCycleError):
            p.topological_sort()

    def test_cycle_also_raises_on_ready_tasks(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", deps=["b"]))
        p.add_task(_make("b", deps=["a"]))
        with pytest.raises(DagCycleError):
            p.ready_tasks(completed=set())

    def test_cycle_also_raises_on_priority_score(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", deps=["b"]))
        p.add_task(_make("b", deps=["a"]))
        with pytest.raises(DagCycleError):
            p.get_priority_score("a")


# ---------------------------------------------------------------------------
# Unknown dependency
# ---------------------------------------------------------------------------


class TestUnknownDependency:
    """@trace FR-ORC-029"""

    def test_unknown_dep_raises_value_error_on_topo(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", deps=["ghost"]))
        with pytest.raises(ValueError, match="unknown task 'ghost'"):
            p.topological_sort()

    def test_unknown_dep_raises_value_error_on_critical_path(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", deps=["ghost"]))
        with pytest.raises(ValueError):
            p.compute_critical_path()


# ---------------------------------------------------------------------------
# add_task overwrite
# ---------------------------------------------------------------------------


class TestAddTaskDeduplication:
    """@trace FR-ORC-020"""

    def test_duplicate_id_overwrites(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", duration=1.0))
        p.add_task(_make("a", duration=99.0))
        assert p._tasks["a"].estimated_duration_s == 99.0

    def test_task_count_stays_same_on_overwrite(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        p.add_task(_make("b"))
        p.add_task(_make("a", duration=5.0))
        assert len(p._tasks) == 2


# ---------------------------------------------------------------------------
# Topological sort validity — complex graph
# ---------------------------------------------------------------------------


class TestTopologicalSortValidity:
    """@trace FR-ORC-027"""

    def test_complex_graph_topo_valid(self) -> None:
        p = DagPrioritizer()
        # Build a graph with multiple levels and fan-in/fan-out.
        p.add_task(_make("a"))
        p.add_task(_make("b", deps=["a"]))
        p.add_task(_make("c", deps=["a"]))
        p.add_task(_make("d", deps=["b", "c"]))
        p.add_task(_make("e", deps=["b"]))
        p.add_task(_make("f", deps=["d", "e"]))
        order = p.topological_sort()
        assert len(order) == 6
        assert _topo_valid(order, p)

    def test_topo_contains_all_tasks(self) -> None:
        p = DagPrioritizer()
        for i in range(10):
            deps = [str(i - 1)] if i > 0 else []
            p.add_task(_make(str(i), deps=deps))
        order = p.topological_sort()
        assert set(order) == {str(i) for i in range(10)}


# ---------------------------------------------------------------------------
# Priority score ordering
# ---------------------------------------------------------------------------


class TestPriorityScoreOrdering:
    """@trace FR-ORC-028"""

    def test_critical_path_tasks_outrank_non_critical(self) -> None:
        # a → b (long, 10s) — critical path
        # a → c (short, 1s) — off critical path
        p = DagPrioritizer()
        p.add_task(_make("a", duration=1.0))
        p.add_task(_make("b", duration=10.0, deps=["a"]))
        p.add_task(_make("c", duration=1.0, deps=["a"]))
        sb = p.get_priority_score("b")
        sc = p.get_priority_score("c")
        assert sb > sc

    def test_unknown_task_raises_key_error(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        with pytest.raises(KeyError):
            p.get_priority_score("bogus")


# ---------------------------------------------------------------------------
# Ready tasks ordering
# ---------------------------------------------------------------------------


class TestReadyTasksOrdering:
    """@trace FR-ORC-026"""

    def test_critical_task_first_among_ready(self) -> None:
        # After 'root' completes, 'hot' (critical) and 'cold' are both ready.
        # 'hot' has a much longer duration → stays on critical path → higher score.
        p = DagPrioritizer()
        p.add_task(_make("root", duration=1.0))
        p.add_task(_make("hot", duration=100.0, deps=["root"]))
        p.add_task(_make("cold", duration=0.1, deps=["root"]))
        ready = p.ready_tasks(completed={"root"})
        assert ready[0] == "hot"

    def test_tiebreak_by_task_id(self) -> None:
        # Two independent tasks with identical durations → alphabetical tiebreak.
        p = DagPrioritizer()
        p.add_task(_make("alpha", duration=5.0))
        p.add_task(_make("beta", duration=5.0))
        ready = p.ready_tasks(completed=set())
        assert ready == ["alpha", "beta"]

    def test_completed_tasks_excluded(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        p.add_task(_make("b"))
        ready = p.ready_tasks(completed={"a"})
        assert "a" not in ready
        assert "b" in ready

    def test_tasks_with_unsatisfied_deps_excluded(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        p.add_task(_make("b", deps=["a"]))
        ready = p.ready_tasks(completed=set())
        assert "b" not in ready
        assert "a" in ready
