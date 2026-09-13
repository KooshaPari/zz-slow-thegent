# remediation_planner API Reference

> **Source**: `src/thegent/planning/remediation_planner.py`

DAG-based remediation plan generation.

Converts prioritised findings from the analyzer into an executable DAG of
remediation tasks that the agent deployer can dispatch. Uses
`graphlib.TopologicalSorter` (stdlib) for DAG resolution and reuses the
PERT forward-pass from `thegent.planning.simulation` for critical-path
estimation.

---

## Finding

---

## RemediationPlan

An executable DAG of remediation tasks.

**Inherits from**: `BaseModel`

---

## RemediationPlanner

Converts findings into an executable remediation DAG.

### Methods

#### RemediationPlanner.**init**

```python
__init__(self: Any, health_targets_path: Path)
```

---

#### RemediationPlanner.plan

```python
plan(self: Any, findings: list[Finding], budget_remaining_calls: int)
```

Build a remediation plan from _findings_ within _budget_.

---

---

## RemediationTask

A single task in a remediation plan.

**Inherits from**: `BaseModel`

---

## plan

```python
plan(self: Any, findings: list[Finding], budget_remaining_calls: int)
```

Build a remediation plan from _findings_ within _budget_.

---
