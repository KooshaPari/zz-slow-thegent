# slo API Reference

> **Source**: `src/thegent/governance/slo.py`

Service Level Objective (SLO) regulation and monitoring (WP-5001).

---

## SLORegulator

Monitors and regulates actions to meet defined Service Level Objectives.

### Methods

#### SLORegulator.**init**

```python
__init__(self: Any, latency_slo_ms: float, error_slo_rate: float)
```

---

#### SLORegulator.is_compliant

```python
is_compliant(self: Any)
```

Check if currently compliant with SLOs.

---

#### SLORegulator.record_execution

```python
record_execution(self: Any, latency_ms: float, success: bool)
```

Record an execution metric.

---

---

## is_compliant

```python
is_compliant(self: Any)
```

Check if currently compliant with SLOs.

---

## record_execution

```python
record_execution(self: Any, latency_ms: float, success: bool)
```

Record an execution metric.

---
