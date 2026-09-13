# plan_system API Reference

> **Source**: `src/thegent/integration/plan_system.py`

Integration with PLAN.md and plan status tracking.

---

## PlanSystemIntegration

Integrate with PLAN.md and plan status.

This class handles integration with the project plan system,
including parsing PLAN.md, tracking task status, and managing dependencies.

### Methods

#### PlanSystemIntegration.**init**

```python
__init__(self: Any, plan_file: Any, plan_status_file: Any)
```

Initialize plan system integration.

**Parameters**:

- `plan_file`: Path to PLAN.md file. Defaults to PLAN.md
- `plan_status_file`: Path to PLAN_STATUS.md file.
  Defaults to docs/reference/PLAN_STATUS.md

---

#### PlanSystemIntegration.get_blocked_tasks

```python
get_blocked_tasks(self: Any)
```

Get tasks blocked by incomplete dependencies.

**Returns**: List of blocked task dictionaries

---

#### PlanSystemIntegration.get_tasks_for_phase

```python
get_tasks_for_phase(self: Any, phase: str)
```

Get tasks for specific phase.

**Parameters**:

- `phase`: Phase identifier (e.g., "Phase 1" or "1")

**Returns**: List of task dictionaries

---

#### PlanSystemIntegration.update_task_status

```python
update_task_status(self: Any, task_id: str, status: str)
```

Update task status in plan.

Updates both PLAN.md (if task is in plan) and PLAN_STATUS.md.

**Parameters**:

- `task_id`: ID of task to update
- `status`: New status (e.g., "completed", "in_progress", "pending")

---

---

## get_blocked_tasks

```python
get_blocked_tasks(self: Any)
```

Get tasks blocked by incomplete dependencies.

**Returns**: List of blocked task dictionaries

---

## get_tasks_for_phase

```python
get_tasks_for_phase(self: Any, phase: str)
```

Get tasks for specific phase.

**Parameters**:

- `phase`: Phase identifier (e.g., "Phase 1" or "1")

**Returns**: List of task dictionaries

---

## update_task_status

```python
update_task_status(self: Any, task_id: str, status: str)
```

Update task status in plan.

Updates both PLAN.md (if task is in plan) and PLAN_STATUS.md.

**Parameters**:

- `task_id`: ID of task to update
- `status`: New status (e.g., "completed", "in_progress", "pending")

---
