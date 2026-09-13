# workflow API Reference

> **Source**: `src/thegent/crew/workflow.py`

WorkflowEngine for multi-crew stages.

---

## CrewStage

A stage in a workflow containing one or more crews.

---

## WorkflowEngine

Manages multi-crew workflows with stages.

Supports:

- Multi-crew execution
- Stage dependencies
- Parallel stage execution
- Result aggregation

### Methods

#### WorkflowEngine.**init**

```python
__init__(self: Any)
```

Initialize WorkflowEngine.

---

#### WorkflowEngine.add_stage

```python
add_stage(self: Any, stage: CrewStage)
```

Add a stage to the workflow.

---

#### WorkflowEngine.execute

```python
execute(self: Any)
```

Execute entire workflow respecting stage dependencies.

**Returns**: Map of stage_id -> {crew_id -> {task_id -> ExecutionResult}}

---

#### WorkflowEngine.execute_stage

```python
execute_stage(self: Any, stage: CrewStage)
```

Execute all crews in a stage.

**Parameters**:

- `stage`: Stage to execute

**Returns**: Map of crew_id -> {task_id -> ExecutionResult}

---

#### WorkflowEngine.resolve_stage_dependencies

```python
resolve_stage_dependencies(self: Any)
```

Resolve stage dependencies using topological sort.

Returns stages in execution order.

---

---

## add_stage

```python
add_stage(self: Any, stage: CrewStage)
```

Add a stage to the workflow.

---

## execute

```python
execute(self: Any)
```

Execute entire workflow respecting stage dependencies.

**Returns**: Map of stage_id -> {crew_id -> {task_id -> ExecutionResult}}

---

## execute_stage

```python
execute_stage(self: Any, stage: CrewStage)
```

Execute all crews in a stage.

**Parameters**:

- `stage`: Stage to execute

**Returns**: Map of crew_id -> {task_id -> ExecutionResult}

---

## resolve_stage_dependencies

```python
resolve_stage_dependencies(self: Any)
```

Resolve stage dependencies using topological sort.

Returns stages in execution order.

---
