# cost_aggregation API Reference

> **Source**: `src/thegent/governance/cost_aggregation.py`

Per-run cost aggregation.

---

## CostAggregator

Per-run cost aggregation.

### Methods

#### CostAggregator.**init**

```python
__init__(self: Any)
```

Initialize cost aggregator.

---

#### CostAggregator.get_cost_by_model

```python
get_cost_by_model(self: Any)
```

Get cost breakdown by model.

**Returns**: Dictionary mapping model to total cost

---

#### CostAggregator.get_total_cost

```python
get_total_cost(self: Any)
```

Get total cost across all runs.

**Returns**: Total cost

---

#### CostAggregator.record_run_cost

```python
record_run_cost(self: Any, run_id: str, cost: float, model: str, tokens: dict[(str, int)])
```

Record cost for a run.

**Parameters**:

- `run_id`: Run identifier
- `cost`: Total cost
- `model`: Model used
- `tokens`: Token counts (input, output)

---

---

## get_cost_by_model

```python
get_cost_by_model(self: Any)
```

Get cost breakdown by model.

**Returns**: Dictionary mapping model to total cost

---

## get_total_cost

```python
get_total_cost(self: Any)
```

Get total cost across all runs.

**Returns**: Total cost

---

## record_run_cost

```python
record_run_cost(self: Any, run_id: str, cost: float, model: str, tokens: dict[(str, int)])
```

Record cost for a run.

**Parameters**:

- `run_id`: Run identifier
- `cost`: Total cost
- `model`: Model used
- `tokens`: Token counts (input, output)

---
