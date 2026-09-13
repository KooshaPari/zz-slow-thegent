# dag_prioritization API Reference

> **Source**: `src/thegent/orchestration/execution/dag_prioritization.py`

DAG-aware critical-path task prioritization for swarm scheduling.

Computes the critical path through a directed acyclic graph (DAG) of tasks
and surfaces priority scores so the swarm scheduler can schedule the most
blocking work first.

Usage::

    from thegent.orchestration.execution.dag_prioritization import DagPrioritizer, DagTask

    p = DagPrioritizer()
    p.add_task(DagTask("a", estimated_duration_s=3.0))
    p.add_task(DagTask("b", estimated_duration_s=5.0, dependencies=["a"]))
    p.add_task(DagTask("c", estimated_duration_s=2.0, dependencies=["a"]))

    critical = p.compute_critical_path()   # ["a", "b"]
    order    = p.topological_sort()        # valid execution order
    ready    = p.ready_tasks(completed=set())   # ["a"]

---

## DagCycleError

Raised when the task graph contains a cycle.

**Inherits from**: `Exception`

---

## DagPrioritizer

Compute critical paths and priority scores for a DAG of tasks.

All methods are synchronous and read-only after tasks are added.
The internal graph is rebuilt lazily when :meth:`compute_critical_path`
or :meth:`topological_sort` is called.

### Methods

#### DagPrioritizer.**init**

```python
__init__(self: Any)
```

---

#### DagPrioritizer.add_task

```python
add_task(self: Any, task: DagTask)
```

Register _task_ with the prioritizer.

Duplicate `task_id` values overwrite the previous entry.

---

#### DagPrioritizer.compute_critical_path

```python
compute_critical_path(self: Any)
```

Return the ordered list of task IDs on the critical path.

The critical path is the longest path (by total `estimated_duration_s`)
from any source node to any sink node. The returned list is ordered
from the first task to execute to the last.

Raises :class:`DagCycleError` if the graph contains a cycle.
Raises :class:`ValueError` if any dependency references an unknown task.

---

#### DagPrioritizer.get_priority_score

```python
get_priority_score(self: Any, task_id: str)
```

Return a priority score for _task_id_.

Higher values indicate that the task is on (or close to) the critical
path. The score equals the `estimated_duration_s` of the longest
path that passes _through_ this task — that is, the sum of the
critical sub-path from this task to any sink.

Raises :class:`KeyError` if _task_id_ is not registered.
Raises :class:`DagCycleError` if the graph contains a cycle.

---

#### DagPrioritizer.ready_tasks

```python
ready_tasks(self: Any, completed: set[str])
```

Return tasks whose dependencies are all satisfied, sorted by priority.

_completed_ is the set of already-finished `task_id` values. Tasks
in _completed_ are excluded from the result.

Tasks are returned in descending priority order (highest

---

#### DagPrioritizer.topological_sort

```python
topological_sort(self: Any)
```

Return a valid execution order respecting all dependencies.

Raises :class:`DagCycleError` if the graph contains a cycle.
Raises :class:`ValueError` if any dependency references an unknown task.

---

---

## DagTask

A single node in the scheduling DAG.

---

## add_task

```python
add_task(self: Any, task: DagTask)
```

Register _task_ with the prioritizer.

Duplicate `task_id` values overwrite the previous entry.

---

## compute_critical_path

```python
compute_critical_path(self: Any)
```

Return the ordered list of task IDs on the critical path.

The critical path is the longest path (by total `estimated_duration_s`)
from any source node to any sink node. The returned list is ordered
from the first task to execute to the last.

Raises :class:`DagCycleError` if the graph contains a cycle.
Raises :class:`ValueError` if any dependency references an unknown task.

---

## get_priority_score

```python
get_priority_score(self: Any, task_id: str)
```

Return a priority score for _task_id_.

Higher values indicate that the task is on (or close to) the critical
path. The score equals the `estimated_duration_s` of the longest
path that passes _through_ this task — that is, the sum of the
critical sub-path from this task to any sink.

Raises :class:`KeyError` if _task_id_ is not registered.
Raises :class:`DagCycleError` if the graph contains a cycle.

---

## ready_tasks

```python
ready_tasks(self: Any, completed: set[str])
```

Return tasks whose dependencies are all satisfied, sorted by priority.

_completed_ is the set of already-finished `task_id` values. Tasks
in _completed_ are excluded from the result.

Tasks are returned in descending priority order (highest

---

## topological_sort

```python
topological_sort(self: Any)
```

Return a valid execution order respecting all dependencies.

Raises :class:`DagCycleError` if the graph contains a cycle.
Raises :class:`ValueError` if any dependency references an unknown task.

---
