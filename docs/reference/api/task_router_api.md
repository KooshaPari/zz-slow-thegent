# task_router API Reference

> **Source**: `src/thegent/routing/task_router.py`

## ConstraintValidator

Validates task metadata against configured constraints.

### Methods

#### ConstraintValidator.**init**

```python
__init__(self: Any, config: ThegentSettings)
```

---

#### ConstraintValidator.validate

```python
validate(self: Any, task_metadata: TaskMetadata, registry: RunRegistry | None, model: Any)
```

Validate task against hard constraints:

- Instantaneous cost (per-call)
- Cumulative cost (MTD per category)
- Speed (SLA)

---

---

## TaskClassifier

Categorizes tasks based on prompt analysis and heuristics.

### Methods

#### TaskClassifier.**init**

```python
__init__(self: Any, config: ThegentSettings)
```

---

#### TaskClassifier.classify

```python
classify(self: Any, prompt: str, agent_role: Any)
```

Classify task complexity based on prompt content.

Heuristics:

- Word count (token estimate proxy)
- Keywords (architecture, design -> HIGH_COMPLEX)
- Structure (bullets, code blocks -> COMPLEX)

---

#### TaskClassifier.detect_role

```python
detect_role(self: Any, prompt: str, agent_role: Any)
```

Detect task role from agent metadata or prompt keywords.

Priority:

1. Agent-specified role (from agent frontmatter)
2. Auto-detect from prompt keywords
3. Default to "workhorse"

**Parameters**:

- `prompt`: User prompt text
- `agent_role`: Role from agent metadata (e.g., "planner", "writer", "researcher")

**Returns**: Role string (workhorse/researcher/writer_fast/writer_high/planner/large_context)

---

---

## TaskRouter

Orchestrates task classification and constraint validation.

### Methods

#### TaskRouter.**init**

```python
__init__(self: Any, config: ThegentSettings)
```

---

#### TaskRouter.classify

```python
classify(self: Any, prompt: str)
```

Classify task.

---

#### TaskRouter.find_active_terminal_for_path

```python
find_active_terminal_for_path(self: Any, path: str)
```

Find an active tmux pane matching the given project path.

Returns pane_id if found.

---

#### TaskRouter.get_fallback_chain

```python
get_fallback_chain(self: Any, category: TaskCategory)
```

Get LiteLLM-style fallback chain for task category (WP-1001).

---

#### TaskRouter.route

```python
route(self: Any, prompt: str, registry: RunRegistry | None, model: Any)
```

Full routing: classify + validate.

Returns (TaskMetadata, violations).

---

#### TaskRouter.route_by_capability

```python
route_by_capability(self: Any, task_type: str)
```

Route to an agent based on task capability (WP-1007).

---

#### TaskRouter.route_dag_tasks

```python
route_dag_tasks(self: Any, dag: Any)
```

Route multiple tasks from a DAG, considering dependencies (WP-1001).

---

#### TaskRouter.shape_task

```python
shape_task(self: Any, prompt: str, category: TaskCategory)
```

WP-11006: Adaptive task shaping (split/merge engine).

---

#### TaskRouter.should_delegate_to_reviewer

```python
should_delegate_to_reviewer(self: Any, confidence: float)
```

Determine if a task should be delegated to a reviewer based on confidence (WP-1007).

---

#### TaskRouter.validate

```python
validate(self: Any, task_metadata: TaskMetadata, registry: RunRegistry | None, model: Any)
```

Validate task against constraints.

---

---

## classify

```python
classify(self: Any, prompt: str)
```

Classify task.

---

## detect_role

```python
detect_role(self: Any, prompt: str, agent_role: Any)
```

Detect task role from agent metadata or prompt keywords.

Priority:

1. Agent-specified role (from agent frontmatter)
2. Auto-detect from prompt keywords
3. Default to "workhorse"

**Parameters**:

- `prompt`: User prompt text
- `agent_role`: Role from agent metadata (e.g., "planner", "writer", "researcher")

**Returns**: Role string (workhorse/researcher/writer_fast/writer_high/planner/large_context)

---

## find_active_terminal_for_path

```python
find_active_terminal_for_path(self: Any, path: str)
```

Find an active tmux pane matching the given project path.

Returns pane_id if found.

---

## get_fallback_chain

```python
get_fallback_chain(self: Any, category: TaskCategory)
```

Get LiteLLM-style fallback chain for task category (WP-1001).

---

## route

```python
route(self: Any, prompt: str, registry: RunRegistry | None, model: Any)
```

Full routing: classify + validate.

Returns (TaskMetadata, violations).

---

## route_by_capability

```python
route_by_capability(self: Any, task_type: str)
```

Route to an agent based on task capability (WP-1007).

---

## route_dag_tasks

```python
route_dag_tasks(self: Any, dag: Any)
```

Route multiple tasks from a DAG, considering dependencies (WP-1001).

---

## shape_task

```python
shape_task(self: Any, prompt: str, category: TaskCategory)
```

WP-11006: Adaptive task shaping (split/merge engine).

---

## should_delegate_to_reviewer

```python
should_delegate_to_reviewer(self: Any, confidence: float)
```

Determine if a task should be delegated to a reviewer based on confidence (WP-1007).

---

## validate

```python
validate(self: Any, task_metadata: TaskMetadata, registry: RunRegistry | None, model: Any)
```

Validate task against constraints.

---
