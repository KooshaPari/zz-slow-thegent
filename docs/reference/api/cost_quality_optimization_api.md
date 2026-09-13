# cost_quality_optimization API Reference

> **Source**: `src/thegent/cost/cost_quality_optimization.py`

Cost-quality optimization (RouteLLM-style).

---

## CostQualityOptimizer

Optimize cost vs quality trade-offs.

### Methods

#### CostQualityOptimizer.**init**

```python
__init__(self: Any)
```

Initialize cost-quality optimizer.

---

#### CostQualityOptimizer.get_routing_stats

```python
get_routing_stats(self: Any)
```

Get routing statistics.

**Returns**: Routing statistics

---

#### CostQualityOptimizer.register_model

```python
register_model(self: Any, model_id: str, cost_per_token: float, quality_score: float)
```

Register a model with cost and quality metrics.

**Parameters**:

- `model_id`: Model identifier
- `cost_per_token`: Cost per token
- `quality_score`: Quality score (0.0-1.0)

---

#### CostQualityOptimizer.route_request

```python
route_request(self: Any, task_complexity: float, quality_threshold: float, max_cost: Any)
```

Route request to optimal model.

**Parameters**:

- `task_complexity`: Task complexity (0.0-1.0)
- `quality_threshold`: Minimum quality threshold
- `max_cost`: Maximum cost constraint

**Returns**: Selected model ID

---

---

## get_routing_stats

```python
get_routing_stats(self: Any)
```

Get routing statistics.

**Returns**: Routing statistics

---

## register_model

```python
register_model(self: Any, model_id: str, cost_per_token: float, quality_score: float)
```

Register a model with cost and quality metrics.

**Parameters**:

- `model_id`: Model identifier
- `cost_per_token`: Cost per token
- `quality_score`: Quality score (0.0-1.0)

---

## route_request

```python
route_request(self: Any, task_complexity: float, quality_threshold: float, max_cost: Any)
```

Route request to optimal model.

**Parameters**:

- `task_complexity`: Task complexity (0.0-1.0)
- `quality_threshold`: Minimum quality threshold
- `max_cost`: Maximum cost constraint

**Returns**: Selected model ID

---
