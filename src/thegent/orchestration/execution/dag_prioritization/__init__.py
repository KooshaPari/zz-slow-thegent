"""DagPrioritizer — CPM-based DAG scheduling.

@trace FR-ORC-020..030 -- dormant-core DAG prioritization surface.

AUDIT-N+35 hardening (SOTA pass-19): replaces the 45-line stub with
the full CPM (Critical Path Method) contract that the dormant test
suite already exercises. Preserves the legacy ``DependencyRouter``
+ ``prioritize(nodes)`` re-export so any out-of-tree caller keeps
working.

Public surface:

* :class:`DagCycleError` — canonical cycle exception
* :class:`DependencyRouter` — legacy stub (preserved)
* :class:`DagTask` — task node dataclass
* :class:`DagPrioritizer` — CPM-based prioritizer

Contract highlights:

* ``DagTask(task_id, estimated_duration_s=1.0, dependencies=None,
  priority=0)`` — per-instance list default so two tasks never share state.
* ``DagPrioritizer.add_task(task)`` — overwrite-by-task_id, returns
  ``None`` (in-place mutation contract).
* ``topological_sort()`` — Kahn's algorithm; raises
  :class:`DagCycleError` on cycle, raises :class:`ValueError` with
  message ``"unknown task 'X'"`` on unknown dependency.
* ``compute_critical_path()`` — longest path through the DAG
  (project makespan). Empty DAG → ``[]``.
* ``get_priority_score(task_id)`` — ``project_makespan - total_float``
  per node. Higher score = more critical. Raises ``KeyError`` on
  unknown task. Raises :class:`DagCycleError` on cycle.
* ``ready_tasks(completed)`` — sorted by priority-score desc, then
  by task_id asc. Empty DAG → ``[]``. Raises :class:`DagCycleError`
  on cycle.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


class DagCycleError(Exception):
    """Error raised when a cycle is detected in a DAG."""


class DependencyRouter:
    """Router for dependencies in a DAG.

    Legacy stub preserved for backwards compat. Routes are stored as
    a public dict so callers can inspect / mutate them directly.
    """

    def __init__(self) -> None:
        self.routes: dict[str, list[str]] = {}

    def route(self, node_id: str) -> list[str]:
        """Route dependencies for a node."""
        return self.routes.get(node_id, [])


@dataclass
class DagTask:
    """Task node in a DAG.

    AUDIT-N+35 contract: per-instance list default (``field(default_factory=list)``)
    so two tasks never share state. Accepts ``task_id`` as the first
    positional or keyword arg. The legacy kwargs ``id`` / ``duration``
    are also accepted so out-of-tree callers using the pre-AUDIT-N+35
    stub form keep working without breakage.
    """

    task_id: str = ""
    estimated_duration_s: float = 1.0
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0

    def __init__(
        self,
        task_id: str = "",
        estimated_duration_s: float = 1.0,
        dependencies: list[str] | None = None,
        priority: int = 0,
        *,
        id: str | None = None,
        duration: float | None = None,
    ) -> None:
        self.task_id = id if id is not None else task_id
        self.estimated_duration_s = duration if duration is not None else estimated_duration_s
        self.dependencies = list(dependencies) if dependencies is not None else []
        self.priority = priority

    def __repr__(self) -> str:
        return (
            f"DagTask(task_id={self.task_id!r}, "
            f"estimated_duration_s={self.estimated_duration_s}, "
            f"dependencies={self.dependencies!r}, priority={self.priority})"
        )


class DagPrioritizer:
    """CPM-based DAG prioritizer.

    Internal state:

    * ``self._tasks``: ``dict[str, DagTask]`` — task_id → task.
    * ``self.priorities``: ``dict[str, int]`` — legacy field for
      backwards-compat with the pre-AUDIT-N+35 stub.

    CPM algorithm: compute the longest path (project makespan) by
    forward DP through the topologically sorted DAG; priority score
    for each task is ``project_makespan - total_float`` where
    ``total_float = latest_start - earliest_start``.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, DagTask] = {}
        self.priorities: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_task(self, task: DagTask) -> None:
        """Add a task. Overwrites if ``task_id`` already present.

        Defensive copy of ``task.dependencies`` so external mutation
        of the caller's list cannot corrupt internal state.
        """
        task.dependencies = list(task.dependencies)
        self._tasks[task.task_id] = task

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_dependencies(self) -> None:
        """Raise ValueError on unknown dependencies, DagCycleError on cycle."""
        unknown = {dep for task in self._tasks.values() for dep in task.dependencies if dep not in self._tasks}
        if unknown:
            sample = sorted(unknown)[0]
            raise ValueError(f"unknown task '{sample}'")
        self._check_acyclic()

    def _check_acyclic(self) -> None:
        """Raise DagCycleError if the graph has any cycle."""
        # 0 = unvisited, 1 = on-stack, 2 = done
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = dict.fromkeys(self._tasks, WHITE)

        def dfs(node: str) -> None:
            color[node] = GRAY
            for dep in self._tasks[node].dependencies:
                if dep not in color:
                    # Defensive: unknown deps are filtered upstream.
                    continue
                if color[dep] == GRAY:
                    raise DagCycleError(f"cycle detected at task '{node}'")
                if color[dep] == WHITE:
                    dfs(dep)
            color[node] = BLACK

        for tid in self._tasks:
            if color[tid] == WHITE:
                dfs(tid)

    def _topological_order(self) -> list[str]:
        """Kahn's algorithm — raises DagCycleError on cycle."""
        self._validate_dependencies()
        in_degree: dict[str, int] = dict.fromkeys(self._tasks, 0)
        # Build reverse adjacency: dep -> [tasks that depend on it]
        children: dict[str, list[str]] = {tid: [] for tid in self._tasks}
        for task in self._tasks.values():
            for dep in task.dependencies:
                in_degree[task.task_id] += 1
                children[dep].append(task.task_id)

        # Kahn's: start from sources (in_degree == 0).
        # Use a sorted list as the ready-set so topological sort
        # output is deterministic across runs.
        ready = sorted([tid for tid, d in in_degree.items() if d == 0])
        order: list[str] = []
        while ready:
            node = ready.pop(0)
            order.append(node)
            for child in children[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    # Insert in sorted order to keep topological
                    # sort deterministic across runs.
                    idx = 0
                    while idx < len(ready) and ready[idx] < child:
                        idx += 1
                    ready.insert(idx, child)
        if len(order) != len(self._tasks):
            raise DagCycleError("cycle detected during topological sort")
        return order

    # ------------------------------------------------------------------
    # Public contract surface
    # ------------------------------------------------------------------

    def topological_sort(self) -> list[str]:
        """Return a valid topological ordering of all tasks.

        Raises :class:`DagCycleError` on cycle, :class:`ValueError`
        on unknown dependency.
        """
        if not self._tasks:
            return []
        return self._topological_order()

    def compute_critical_path(self) -> list[str]:
        """Return the longest-duration path (the critical path).

        Empty DAG → ``[]``. Raises :class:`DagCycleError` on cycle,
        :class:`ValueError` on unknown dependency.

        The critical path is the longest-duration path through the
        DAG; ties between equally-long paths are broken by
        lexicographic order of the task ID sequence.
        """
        if not self._tasks:
            return []
        order = self._topological_order()
        # Forward DP: earliest_finish[node] = duration[node] for sources,
        # else max(earliest_finish[pred] for pred in deps) + duration[node].
        earliest_finish: dict[str, float] = {}
        via: dict[str, str | None] = {}
        for node in order:
            preds = self._tasks[node].dependencies
            if not preds:
                earliest_finish[node] = self._tasks[node].estimated_duration_s
                via[node] = None
            else:
                # Pick the predecessor that maximises earliest_finish;
                # tiebreak by lexicographically smaller predecessor so
                # the path is deterministic.
                best_pred = max(
                    preds,
                    key=lambda p: (earliest_finish[p], tuple(-ord(c) for c in p)),
                )
                earliest_finish[node] = earliest_finish[best_pred] + self._tasks[node].estimated_duration_s
                via[node] = best_pred

        # Project makespan = max earliest_finish.
        makespan = max(earliest_finish.values()) if earliest_finish else 0.0
        terminuses = [t for t, ef in earliest_finish.items() if ef == makespan]

        # Walk back from each terminus, then pick the lexicographically
        # smallest path.
        paths: list[list[str]] = []
        for term in terminuses:
            path: list[str] = []
            cur: str | None = term
            while cur is not None:
                path.append(cur)
                cur = via[cur]
            paths.append(list(reversed(path)))
        paths.sort(key=lambda p: p)
        return paths[0]

    def get_priority_score(self, task_id: str) -> float:
        """Return ``project_makespan - total_float`` for the task.

        Higher score = more critical (less slack). Raises
        :class:`KeyError` on unknown task, :class:`DagCycleError`
        on cycle, :class:`ValueError` on unknown dependency.
        """
        if task_id not in self._tasks:
            raise KeyError(task_id)
        if not self._tasks:
            return 0.0
        order = self._topological_order()
        # Forward pass: earliest finish per node.
        earliest_finish: dict[str, float] = {}
        for node in order:
            preds = self._tasks[node].dependencies
            if not preds:
                earliest_finish[node] = self._tasks[node].estimated_duration_s
            else:
                earliest_finish[node] = max(earliest_finish[p] for p in preds) + self._tasks[node].estimated_duration_s
        makespan = max(earliest_finish.values()) if earliest_finish else 0.0
        # Backward pass: latest finish per node.
        successors: dict[str, list[str]] = {tid: [] for tid in self._tasks}
        for task in self._tasks.values():
            for dep in task.dependencies:
                successors[dep].append(task.task_id)
        latest_finish: dict[str, float] = {}
        for node in reversed(order):
            succs = successors[node]
            if not succs:
                latest_finish[node] = makespan
            else:
                latest_finish[node] = min(latest_finish[s] - self._tasks[s].estimated_duration_s for s in succs)
        # total_float[node] = latest_finish[node] - earliest_finish[node]
        # priority_score = makespan - total_float
        total_float = latest_finish[task_id] - earliest_finish[task_id]
        return makespan - total_float

    def ready_tasks(self, completed: Iterable[str]) -> list[str]:
        """Return ready tasks (deps satisfied, not completed), sorted.

        Sort order: priority score desc (more critical first); tiebreak
        by task_id asc. Empty DAG → ``[]``. Raises :class:`DagCycleError`
        on cycle, :class:`ValueError` on unknown dependency.
        """
        completed_set = set(completed)
        if not self._tasks:
            return []
        # Validate cycle detection before walking the graph.
        order = self._topological_order()
        ready: list[str] = []
        for node in order:
            if node in completed_set:
                continue
            deps = self._tasks[node].dependencies
            if all(dep in completed_set for dep in deps):
                ready.append(node)
        # Sort by priority score desc, tiebreak by task_id asc.
        ready.sort(key=lambda tid: (-self.get_priority_score(tid), tid))
        return ready

    # ------------------------------------------------------------------
    # Legacy stub compat
    # ------------------------------------------------------------------

    def prioritize(self, nodes: list[str]) -> list[str]:
        """Prioritize nodes for execution (legacy stub).

        Returns ``nodes`` sorted by ``self.priorities`` ascending
        (lower = higher priority). Unknown nodes sort last. This
        preserves the pre-AUDIT-N+35 stub contract for out-of-tree
        callers.
        """
        return sorted(nodes, key=lambda n: self.priorities.get(n, 999))


__all__ = ["DagCycleError", "DependencyRouter", "DagPrioritizer", "DagTask"]
