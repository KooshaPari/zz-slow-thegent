# arbitrage API Reference

> **Source**: `src/thegent/economy/arbitrage.py`

WP-35001: Global Compute Arbitrage Engine.

Optimizes task execution cost by finding the cheapest available agent service globally.

---

## ArbitrageEngine

Finds and exploits price differences across regional agent markets.

### Methods

#### ArbitrageEngine.**init**

```python
__init__(self: Any, market: AgentMarket)
```

---

#### ArbitrageEngine.estimate_global_savings

```python
estimate_global_savings(self: Any, run_count: int)
```

Estimate total savings using arbitrage over standard fixed routing.

---

#### ArbitrageEngine.find_best_value

```python
find_best_value(self: Any, task_id: str, capabilities: list[str], max_budget: float)
```

WP-35001: Run an arbitrage cycle to find the highest value provider.

---

---

## estimate_global_savings

```python
estimate_global_savings(self: Any, run_count: int)
```

Estimate total savings using arbitrage over standard fixed routing.

---

## find_best_value

```python
find_best_value(self: Any, task_id: str, capabilities: list[str], max_budget: float)
```

WP-35001: Run an arbitrage cycle to find the highest value provider.

---
