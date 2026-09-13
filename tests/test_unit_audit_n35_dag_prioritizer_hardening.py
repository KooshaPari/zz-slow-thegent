"""Spec-only hardening tests for the dormant DagPrioritizer surface.

@trace FR-ORC-020 -- DAG task addition and deduplication (task_id-keyed).
@trace FR-ORC-021 -- Single-node DAG: critical path is the node itself.
@trace FR-ORC-022 -- Linear chain critical path equals the full chain.
@trace FR-ORC-023 -- Diamond DAG: critical path follows the longer branch.
@trace FR-ORC-024 -- Multiple independent paths: critical path is the longest.
@trace FR-ORC-025 -- Cycle detection raises DagCycleError on every code path.
@trace FR-ORC-026 -- Ready tasks filtered by completed set + sorted by priority.
@trace FR-ORC-027 -- Topological sort produces a valid execution order.
@trace FR-ORC-028 -- Priority score is higher for tasks on the critical path.
@trace FR-ORC-029 -- Unknown dependency raises ValueError.
@trace FR-ORC-030 -- Empty DAG returns empty results.

This file is the AUDIT-N+35 contract spec: it pins the dormant-core
behaviour expected of ``DagPrioritizer`` after the SOTA pass-19 source
patch. It is committed first (spec-first pattern, mirrors AUDIT-N+34)
so the next step is to make every assertion here pass without
introducing new regressions in the AUDIT-N+33 / AUDIT-N+34 corridor.
"""

from __future__ import annotations

import pytest

from thegent.orchestration.execution.dag_prioritization import (
    DagCycleError,
    DagPrioritizer,
    DagTask,
    DependencyRouter,
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
    position = {tid: i for i, tid in enumerate(order)}
    for task in prioritizer._tasks.values():
        for dep in task.dependencies:
            if position[dep] >= position[task.task_id]:
                return False
    return True


# ---------------------------------------------------------------------------
# DagTask dataclass — contract surface
# ---------------------------------------------------------------------------


class TestDagTaskDataclass:
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
        """Per-instance list default — no shared-state bug."""
        t1 = DagTask("a")
        t2 = DagTask("b")
        t1.dependencies.append("z")
        assert t2.dependencies == []

    def test_positional_first_arg(self) -> None:
        """DagTask accepts task_id positionally (legacy form)."""
        t = DagTask("z")
        assert t.task_id == "z"

    def test_kwarg_form(self) -> None:
        t = DagTask(task_id="z", estimated_duration_s=2.0, priority=1)
        assert t.task_id == "z"
        assert t.estimated_duration_s == 2.0
        assert t.priority == 1


# ---------------------------------------------------------------------------
# Empty DAG behaviour (NEW-1)
# ---------------------------------------------------------------------------


class TestEmptyDagContract:
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

    def test_tasks_dict_empty(self) -> None:
        """Dormant-core invariant: _tasks starts empty."""
        p = DagPrioritizer()
        assert p._tasks == {}
        assert len(p._tasks) == 0


# ---------------------------------------------------------------------------
# Single-node DAG (NEW-2)
# ---------------------------------------------------------------------------


class TestSingleNodeContract:
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
# Linear chain (NEW-3)
# ---------------------------------------------------------------------------


class TestLinearChainContract:
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

    def test_priority_scores_all_on_critical_path(
        self, prioritizer: DagPrioritizer
    ) -> None:
        sa = prioritizer.get_priority_score("a")
        sb = prioritizer.get_priority_score("b")
        sc = prioritizer.get_priority_score("c")
        # All on critical path → same priority score (project makespan = 6.0).
        assert sa == pytest.approx(6.0)
        assert sb == pytest.approx(6.0)
        assert sc == pytest.approx(6.0)

    def test_ready_tasks_initial(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed=set()) == ["a"]

    def test_ready_tasks_after_a(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed={"a"}) == ["b"]

    def test_ready_tasks_after_ab(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed={"a", "b"}) == ["c"]

    def test_ready_tasks_all_completed(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed={"a", "b", "c"}) == []


# ---------------------------------------------------------------------------
# Diamond DAG (NEW-4)
# ---------------------------------------------------------------------------


class TestDiamondDagContract:
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
        assert prioritizer.get_priority_score("b") > prioritizer.get_priority_score("c")

    def test_ready_tasks_initial(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed=set()) == ["a"]

    def test_ready_tasks_after_a_both_branches(
        self, prioritizer: DagPrioritizer
    ) -> None:
        ready = prioritizer.ready_tasks(completed={"a"})
        assert set(ready) == {"b", "c"}
        assert ready[0] == "b"

    def test_ready_tasks_after_a_and_b(self, prioritizer: DagPrioritizer) -> None:
        ready = prioritizer.ready_tasks(completed={"a", "b"})
        assert set(ready) == {"c"}

    def test_ready_tasks_d_unblocked(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.ready_tasks(completed={"a", "b", "c"}) == ["d"]


# ---------------------------------------------------------------------------
# Multiple independent paths (NEW-5)
# ---------------------------------------------------------------------------


class TestMultipleIndependentPathsContract:
    """@trace FR-ORC-024"""

    @pytest.fixture
    def prioritizer(self) -> DagPrioritizer:
        p = DagPrioritizer()
        p.add_task(_make("x1", duration=1.0))
        p.add_task(_make("x2", duration=2.0, deps=["x1"]))
        p.add_task(_make("y1", duration=1.0))
        p.add_task(_make("y2", duration=2.0, deps=["y1"]))
        p.add_task(_make("y3", duration=3.0, deps=["y2"]))
        p.add_task(_make("z", duration=0.5))
        return p

    def test_critical_path_is_longest(self, prioritizer: DagPrioritizer) -> None:
        assert prioritizer.compute_critical_path() == ["y1", "y2", "y3"]

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
        assert set(ready) == {"x1", "y1", "z"}
        assert ready[0] == "y1"


# ---------------------------------------------------------------------------
# Cycle detection (NEW-6)
# ---------------------------------------------------------------------------


class TestCycleDetectionContract:
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
        p.add_task(_make("x2", deps=["y"]))
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
# Unknown dependency (NEW-7)
# ---------------------------------------------------------------------------


class TestUnknownDependencyContract:
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
# add_task deduplication (NEW-8)
# ---------------------------------------------------------------------------


class TestAddTaskDeduplicationContract:
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
# Topological sort validity (NEW-9)
# ---------------------------------------------------------------------------


class TestTopologicalSortValidityContract:
    """@trace FR-ORC-027"""

    def test_complex_graph_topo_valid(self) -> None:
        p = DagPrioritizer()
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
# Priority score ordering (NEW-10)
# ---------------------------------------------------------------------------


class TestPriorityScoreOrderingContract:
    """@trace FR-ORC-028"""

    def test_critical_path_tasks_outrank_non_critical(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a", duration=1.0))
        p.add_task(_make("b", duration=10.0, deps=["a"]))
        p.add_task(_make("c", duration=1.0, deps=["a"]))
        assert p.get_priority_score("b") > p.get_priority_score("c")

    def test_unknown_task_raises_key_error(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        with pytest.raises(KeyError):
            p.get_priority_score("bogus")


# ---------------------------------------------------------------------------
# Ready tasks ordering (NEW-11)
# ---------------------------------------------------------------------------


class TestReadyTasksOrderingContract:
    """@trace FR-ORC-026"""

    def test_critical_task_first_among_ready(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("root", duration=1.0))
        p.add_task(_make("hot", duration=100.0, deps=["root"]))
        p.add_task(_make("cold", duration=0.1, deps=["root"]))
        ready = p.ready_tasks(completed={"root"})
        assert ready[0] == "hot"

    def test_tiebreak_by_task_id(self) -> None:
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


# ---------------------------------------------------------------------------
# DependencyRouter — preserved legacy stub (NEW-12)
# ---------------------------------------------------------------------------


class TestDependencyRouterContract:
    """Legacy stub preserved for backwards compat."""

    def test_route_returns_empty_for_unknown(self) -> None:
        router = DependencyRouter()
        assert router.route("nope") == []

    def test_route_returns_registered_deps(self) -> None:
        router = DependencyRouter()
        router.routes["x"] = ["a", "b"]
        assert router.route("x") == ["a", "b"]

    def test_default_routes_is_empty_dict(self) -> None:
        router = DependencyRouter()
        assert router.routes == {}


# ---------------------------------------------------------------------------
# DagCycleError — exception surface (NEW-13)
# ---------------------------------------------------------------------------


class TestDagCycleErrorContract:
    """DagCycleError is the canonical cycle surface exception."""

    def test_is_exception_subclass(self) -> None:
        assert issubclass(DagCycleError, Exception)

    def test_constructable_with_message(self) -> None:
        err = DagCycleError("cycle at node a")
        assert str(err) == "cycle at node a"


# ---------------------------------------------------------------------------
# Hardening invariants — additional dormant-core contracts (NEW-14)
# ---------------------------------------------------------------------------


class TestHardeningInvariantsContract:
    """Dormant-core invariants pinned by the AUDIT-N+35 hardening."""

    def test_add_task_returns_none(self) -> None:
        """add_task returns None (mutable in-place contract)."""
        p = DagPrioritizer()
        assert p.add_task(_make("a")) is None

    def test_add_task_overwrite_preserves_task_id(self) -> None:
        """add_task overwrite keeps the same task_id key."""
        p = DagPrioritizer()
        p.add_task(_make("a", duration=1.0))
        p.add_task(_make("a", duration=5.0))
        assert "a" in p._tasks
        assert p._tasks["a"].task_id == "a"

    def test_topological_sort_returns_list(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        p.add_task(_make("b", deps=["a"]))
        order = p.topological_sort()
        assert isinstance(order, list)

    def test_ready_tasks_with_completed_includes_all_with_satisfied_deps(
        self,
    ) -> None:
        p = DagPrioritizer()
        p.add_task(_make("a"))
        p.add_task(_make("b"))
        p.add_task(_make("c", deps=["a", "b"]))
        ready = p.ready_tasks(completed={"a", "b"})
        assert ready == ["c"]

    def test_priority_score_matches_duration_for_single_node(self) -> None:
        """Single-node: priority_score == duration (no slack)."""
        p = DagPrioritizer()
        p.add_task(_make("solo", duration=4.2))
        assert p.get_priority_score("solo") == pytest.approx(4.2)

    def test_priority_score_higher_for_longer_path_terminus(self) -> None:
        p = DagPrioritizer()
        p.add_task(_make("root"))
        p.add_task(_make("short", duration=1.0, deps=["root"]))
        p.add_task(_make("long", duration=10.0, deps=["root"]))
        assert p.get_priority_score("long") > p.get_priority_score("short")

    def test_dependency_router_route_returns_default_for_unknown(self) -> None:
        """Unknown node returns empty list (legacy contract)."""
        router = DependencyRouter()
        assert router.route("missing") == []
