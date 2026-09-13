# promotion API Reference

> **Source**: `src/thegent/learning/promotion.py`

WP-14002: Autonomous learning and model promotion.

---

## ModelPromoter

Manages autonomous model promotion based on performance metrics.

### Methods

#### ModelPromoter.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### ModelPromoter.evaluate_promotion

```python
evaluate_promotion(self: Any, model_id: str, success_rate: float, cost_efficiency: float)
```

Evaluate if a model should be promoted to a higher tier (e.g. from experimental to production).

---

---

## evaluate_promotion

```python
evaluate_promotion(self: Any, model_id: str, success_rate: float, cost_efficiency: float)
```

Evaluate if a model should be promoted to a higher tier (e.g. from experimental to production).

---
