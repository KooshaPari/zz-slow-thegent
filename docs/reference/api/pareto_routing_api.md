# pareto_routing API Reference

> **Source**: `src/thegent/research/pareto_routing.py`

Pareto Routing & Hysteresis.

---

## ParetoRouting

Pareto-optimal routing with hysteresis.

### Methods

#### ParetoRouting.**init**

```python
__init__(self: Any)
```

Initialize Pareto routing.

---

#### ParetoRouting.apply_hysteresis

```python
apply_hysteresis(self: Any, current_route: str, new_route: str, cost_diff: float)
```

Apply hysteresis to prevent route oscillation.

**Parameters**:

- `current_route`: Current route
- `new_route`: Proposed new route
- `cost_diff`: Cost difference

**Returns**: Selected route

---

#### ParetoRouting.find_pareto_optimal

```python
find_pareto_optimal(self: Any, options: list[dict[(str, Any)]])
```

Find Pareto-optimal options.

**Parameters**:

- `options`: List of routing options with cost/quality metrics

**Returns**: List of Pareto-optimal options

---

---

## apply_hysteresis

```python
apply_hysteresis(self: Any, current_route: str, new_route: str, cost_diff: float)
```

Apply hysteresis to prevent route oscillation.

**Parameters**:

- `current_route`: Current route
- `new_route`: Proposed new route
- `cost_diff`: Cost difference

**Returns**: Selected route

---

## find_pareto_optimal

```python
find_pareto_optimal(self: Any, options: list[dict[(str, Any)]])
```

Find Pareto-optimal options.

**Parameters**:

- `options`: List of routing options with cost/quality metrics

**Returns**: List of Pareto-optimal options

---
