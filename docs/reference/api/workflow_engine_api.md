# workflow_engine API Reference

> **Source**: `src/thegent/agent/workflow_engine.py`

Workflow engine for agent coordination.

---

## WorkflowEngine

Engine for managing agent workflows.

### Methods

#### WorkflowEngine.**init**

```python
__init__(self: Any)
```

Initialize workflow engine.

---

#### WorkflowEngine.execute_workflow

```python
execute_workflow(self: Any, name: str, context: dict[(str, Any)])
```

Execute a workflow.

**Parameters**:

- `name`: Workflow name
- `context`: Execution context

**Returns**: Execution result

---

#### WorkflowEngine.register_workflow

```python
register_workflow(self: Any, name: str, workflow: dict[(str, Any)])
```

Register a workflow.

**Parameters**:

- `name`: Workflow name
- `workflow`: Workflow definition

---

---

## execute_workflow

```python
execute_workflow(self: Any, name: str, context: dict[(str, Any)])
```

Execute a workflow.

**Parameters**:

- `name`: Workflow name
- `context`: Execution context

**Returns**: Execution result

---

## register_workflow

```python
register_workflow(self: Any, name: str, workflow: dict[(str, Any)])
```

Register a workflow.

**Parameters**:

- `name`: Workflow name
- `workflow`: Workflow definition

---
