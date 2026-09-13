# omega API Reference

> **Source**: `src/thegent/planning/omega.py`

WP-45001: Entropy-Minimizing Execution Loop (Omega).

Optimizes execution by minimizing planning entropy and pruning redundant actions.

---

## OmegaExecutionResult

Result of an entropy-minimized execution step.

**Inherits from**: `BaseModel`

---

## OmegaLoop

The final-stage execution loop for thegent (Phase 45).

Focuses on minimizing entropy (wasted effort, redundant plans, and uncertainty).

### Methods

#### OmegaLoop.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### OmegaLoop.calculate_entropy

```python
calculate_entropy(self: Any, plan: list[dict[(str, Any)]])
```

Calculate the entropy (unpredictability/redundancy) of a proposed plan.

---

#### OmegaLoop.minimize_entropy

```python
minimize_entropy(self: Any, cycle_id: str, proposed_plan: list[dict[(str, Any)]])
```

Optimize a plan by pruning redundant or high-entropy actions.

---

---

## calculate_entropy

```python
calculate_entropy(self: Any, plan: list[dict[(str, Any)]])
```

Calculate the entropy (unpredictability/redundancy) of a proposed plan.

---

## minimize_entropy

```python
minimize_entropy(self: Any, cycle_id: str, proposed_plan: list[dict[(str, Any)]])
```

Optimize a plan by pruning redundant or high-entropy actions.

---
