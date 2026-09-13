# plangent API Reference

> **Source**: `src/thegent/agents/plangent.py`

Plangent-style planning sub-agents for thegent.

Provides DAG-based task decomposition and structured plan execution.
The PlangentPlanner decomposes a goal into a directed acyclic graph (DAG)
of sub-tasks, and the PlangentExecutor dispatches each ready node to a
caller-supplied runner (sync or async).

# @trace FR-AGT-020

---

## Plan

A complete execution plan composed of a DAG of PlanNodes.

### Methods

#### Plan.done_ids

```python
done_ids(self: Any)
```

Set of node IDs whose status is `done`.

---

#### Plan.failed_ids

```python
failed_ids(self: Any)
```

Set of node IDs whose status is `failed`.

---

#### Plan.get_node

```python
get_node(self: Any, node_id: str)
```

Return the node with the given ID, or `None`.

---

#### Plan.to_dict

```python
to_dict(self: Any)
```

Serialize to a plain dict.

---

---

## PlanNode

A single task node within a Plan DAG.

### Methods

#### PlanNode.is_ready

```python
is_ready(self: Any, done_ids: set[str])
```

Return True when all dependencies are satisfied.

---

#### PlanNode.to_dict

```python
to_dict(self: Any)
```

Serialize to a plain dict for JSON / JSONL serialisation.

---

---

## PlangentExecutor

Executes a Plan by dispatching sub-tasks to thegent agents.

The executor iterates over ready nodes, invokes the caller-supplied
_runner_ callback, and updates node status (`done` / `failed`).
It repeats until the plan is complete or a blocking failure is detected.

### Methods

#### PlangentExecutor.**init**

```python
__init__(self: Any, planner: Any)
```

Initialise the executor.

**Parameters**:

- `planner`: :class:`PlangentPlanner` instance used to inspect plan
  state. A default `PlangentPlanner()` is created if not
  provided.
- `fail_fast`: Stop on first failure when `True`.

---

#### PlangentExecutor.execute

```python
execute(self: Any, plan: Plan, runner: RunnerType)
```

Execute _plan_ synchronously by dispatching each ready node.

The method loops until the plan is complete (all nodes done/failed)
or until no progress can be made (deadlock — remaining pending nodes
have unsatisfied dependencies due to failures).

**Parameters**:

- `plan`: The :class:`Plan` to execute.
- `runner`: Callable `(PlanNode) -&gt; str` invoked for each ready
  node. Must return the result string on success or raise an
  exception on failure.

**Returns**: The mutated _plan_ with updated node statuses.

---

---

## PlangentPlanner

Decomposes a goal into a DAG of sub-tasks.

The default `decompose` implementation produces a simple deterministic
breakdown that requires no LLM call. Subclass and override
`_generate_sub_tasks` to inject an LLM-backed decomposition strategy.

### Methods

#### PlangentPlanner.**init**

```python
__init__(self: Any)
```

Initialise the planner.

**Parameters**:

- `separator`: Character used to split compound goal strings during
  heuristic decomposition.
- `max_nodes_per_level`: Maximum sub-tasks per depth level when
  decomposing a compound goal.

---

#### PlangentPlanner.decompose

```python
decompose(self: Any, goal: str, max_depth: int)
```

Break _goal_ into a :class:`Plan` with a DAG of :class:`PlanNode`.

Each node inherits the previous node as a dependency, forming a
simple linear chain by default. Override `_generate_sub_tasks` to
produce arbitrary DAG shapes.

**Parameters**:

- `goal`: Natural-language goal to decompose.
- `max_depth`: Maximum depth of the resulting DAG. Ignored by the
  default heuristic implementation but forwarded to
  `_generate_sub_tasks`.

**Returns**: A :class:`Plan` instance with all nodes in `pending` status.

---

#### PlangentPlanner.is_complete

```python
is_complete(self: Any, plan: Plan)
```

Return `True` when every node is `done` or `failed`.

**Parameters**:

- `plan`: The plan to evaluate.

---

#### PlangentPlanner.mark_done

```python
mark_done(self: Any, plan: Plan, node_id: str, result: str)
```

Mark a node as successfully completed.

**Parameters**:

- `plan`: The plan containing the node.
- `node_id`: ID of the node to update.
- `result`: Output produced by the node.

---

#### PlangentPlanner.mark_failed

```python
mark_failed(self: Any, plan: Plan, node_id: str, error: str)
```

Mark a node as failed.

**Parameters**:

- `plan`: The plan containing the node.
- `node_id`: ID of the node to update.
- `error`: Error message explaining the failure.

---

#### PlangentPlanner.next_ready_tasks

```python
next_ready_tasks(self: Any, plan: Plan)
```

Return all nodes that are ready to execute.

A node is _ready_ when its status is `pending` and every dependency
is `done`.

**Parameters**:

- `plan`: The plan to evaluate.

**Returns**: List of nodes that can start immediately (may be empty).

---

#### PlangentPlanner.to_work_stream_rows

```python
to_work_stream_rows(self: Any, plan: Plan)
```

Convert a Plan into WORK_STREAM-compatible row dicts.

Each row has keys: `id`, `title`, `source`, `priority`,
`depends`, `status`.

**Parameters**:

- `plan`: The plan to convert.

**Returns**: List of dicts, one per node.

---

---

## decompose

```python
decompose(self: Any, goal: str, max_depth: int)
```

Break _goal_ into a :class:`Plan` with a DAG of :class:`PlanNode`.

Each node inherits the previous node as a dependency, forming a
simple linear chain by default. Override `_generate_sub_tasks` to
produce arbitrary DAG shapes.

**Parameters**:

- `goal`: Natural-language goal to decompose.
- `max_depth`: Maximum depth of the resulting DAG. Ignored by the
  default heuristic implementation but forwarded to
  `_generate_sub_tasks`.

**Returns**: A :class:`Plan` instance with all nodes in `pending` status.

---

## done_ids

```python
done_ids(self: Any)
```

Set of node IDs whose status is `done`.

---

## execute

```python
execute(self: Any, plan: Plan, runner: RunnerType)
```

Execute _plan_ synchronously by dispatching each ready node.

The method loops until the plan is complete (all nodes done/failed)
or until no progress can be made (deadlock — remaining pending nodes
have unsatisfied dependencies due to failures).

**Parameters**:

- `plan`: The :class:`Plan` to execute.
- `runner`: Callable `(PlanNode) -&gt; str` invoked for each ready
  node. Must return the result string on success or raise an
  exception on failure.

**Returns**: The mutated _plan_ with updated node statuses.

---

## failed_ids

```python
failed_ids(self: Any)
```

Set of node IDs whose status is `failed`.

---

## get_node

```python
get_node(self: Any, node_id: str)
```

Return the node with the given ID, or `None`.

---

## is_complete

```python
is_complete(self: Any, plan: Plan)
```

Return `True` when every node is `done` or `failed`.

**Parameters**:

- `plan`: The plan to evaluate.

---

## is_ready

```python
is_ready(self: Any, done_ids: set[str])
```

Return True when all dependencies are satisfied.

---

## mark_done

```python
mark_done(self: Any, plan: Plan, node_id: str, result: str)
```

Mark a node as successfully completed.

**Parameters**:

- `plan`: The plan containing the node.
- `node_id`: ID of the node to update.
- `result`: Output produced by the node.

**Raises**:

- `ValueError`: If `node_id` is not found in the plan.

---

## mark_failed

```python
mark_failed(self: Any, plan: Plan, node_id: str, error: str)
```

Mark a node as failed.

**Parameters**:

- `plan`: The plan containing the node.
- `node_id`: ID of the node to update.
- `error`: Error message explaining the failure.

**Raises**:

- `ValueError`: If `node_id` is not found in the plan.

---

## next_ready_tasks

```python
next_ready_tasks(self: Any, plan: Plan)
```

Return all nodes that are ready to execute.

A node is _ready_ when its status is `pending` and every dependency
is `done`.

**Parameters**:

- `plan`: The plan to evaluate.

**Returns**: List of nodes that can start immediately (may be empty).

---

## to_dict

```python
to_dict(self: Any)
```

Serialize to a plain dict.

---

## to_work_stream_rows

```python
to_work_stream_rows(self: Any, plan: Plan)
```

Convert a Plan into WORK_STREAM-compatible row dicts.

Each row has keys: `id`, `title`, `source`, `priority`,
`depends`, `status`.

**Parameters**:

- `plan`: The plan to convert.

**Returns**: List of dicts, one per node.

---
