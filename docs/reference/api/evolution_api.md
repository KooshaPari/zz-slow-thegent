# evolution API Reference

> **Source**: `src/thegent/planning/evolution.py`

WP-37003: Infinite Plan Evolution Loop.

Continously evolves the project plan (DAG) as new information is discovered.

---

## PlanEvolver

Orchestrates the continuous evolution of the Work Breakdown Structure and DAG.

### Methods

#### PlanEvolver.**init**

```python
__init__(self: Any, current_dag: Any)
```

---

#### PlanEvolver.evolve_dag

```python
evolve_dag(self: Any, discovery_events: list[dict[(str, Any)]])
```

WP-37003: Analyze discovery events and append new work packages to the plan.

---

#### PlanEvolver.sandbox_evolution

```python
sandbox_evolution(self: Any, proposed_changes: list[str])
```

Run a simulation to see if the evolved plan is faster or cheaper.

---

---

## evolve_dag

```python
evolve_dag(self: Any, discovery_events: list[dict[(str, Any)]])
```

WP-37003: Analyze discovery events and append new work packages to the plan.

---

## sandbox_evolution

```python
sandbox_evolution(self: Any, proposed_changes: list[str])
```

Run a simulation to see if the evolved plan is faster or cheaper.

---
