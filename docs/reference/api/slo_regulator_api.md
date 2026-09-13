# slo_regulator API Reference

> **Source**: `src/thegent/planning/slo_regulator.py`

WP-11001: SLO regulator loop controller.

Provides stable control updates with anti-oscillation guarantees for system SLOs.

---

## SLORegulator

Closed-loop controller for regulating system performance against SLOs.

### Methods

#### SLORegulator.**init**

```python
__init__(self: Any, target_latency_ms: float)
```

---

#### SLORegulator.evaluate_and_adjust

```python
evaluate_and_adjust(self: Any, current_latency_ms: float)
```

Evaluate SLO performance and adjust throttle if needed.

---

---

## evaluate_and_adjust

```python
evaluate_and_adjust(self: Any, current_latency_ms: float)
```

Evaluate SLO performance and adjust throttle if needed.

---
