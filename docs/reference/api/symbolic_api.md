# symbolic API Reference

> **Source**: `src/thegent/verification/symbolic.py`

WP-18002: Symbolic Execution for Risk Assessment.

Uses symbolic execution principles to explore possible execution paths and identify high-risk branches.

---

## RiskPath

A specific execution path with its associated risk score.

---

## SymbolicRiskExplorer

Symbolically explores task dependency graphs to identify potential failures.

### Methods

#### SymbolicRiskExplorer.**init**

```python
__init__(self: Any, dag: dict[(str, Any)])
```

---

#### SymbolicRiskExplorer.explore

```python
explore(self: Any, start_node: str)
```

Explore all reachable paths from start_node and calculate risk.

---

#### SymbolicRiskExplorer.get_highest_risk_path

```python
get_highest_risk_path(self: Any)
```

Return the path with the highest risk score.

---

---

## explore

```python
explore(self: Any, start_node: str)
```

Explore all reachable paths from start_node and calculate risk.

---

## get_highest_risk_path

```python
get_highest_risk_path(self: Any)
```

Return the path with the highest risk score.

---
