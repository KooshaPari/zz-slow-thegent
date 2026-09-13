# cost_predictor API Reference

> **Source**: `src/thegent/planning/cost_predictor.py`

Cost prediction for agent actions (WP-14001).

---

## CostPredictor

Predicts costs for future agent actions based on model and token estimates.

### Methods

#### CostPredictor.**init**

```python
__init__(self: Any)
```

---

#### CostPredictor.predict_cost

```python
predict_cost(self: Any, model: str, tokens_estimate: int, action_type: str)
```

Predict cost for an action.

**Parameters**:

- `model`: Model ID
- `tokens_estimate`: Estimated token count
- `action_type`: Type of action

**Returns**: Predicted cost in USD

---

---

## predict_cost

```python
predict_cost(self: Any, model: str, tokens_estimate: int, action_type: str)
```

Predict cost for an action.

**Parameters**:

- `model`: Model ID
- `tokens_estimate`: Estimated token count
- `action_type`: Type of action

**Returns**: Predicted cost in USD

---
