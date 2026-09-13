# kpis API Reference

> **Source**: `src/thegent/ux/kpis.py`

WP-Y7: TRAFFIC KPI dashboard.

---

## KPIDashboard

Aggregates and displays TRAFFIC KPIs (Throughput, Reliability, Availability, Finance, Fatigue, Integrity, Continuity).

### Methods

#### KPIDashboard.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### KPIDashboard.get_metrics

```python
get_metrics(self: Any)
```

Aggregate KPIs from various subsystems.

---

#### KPIDashboard.render_summary

```python
render_summary(self: Any)
```

Render a text-based KPI summary.

---

---

## get_metrics

```python
get_metrics(self: Any)
```

Aggregate KPIs from various subsystems.

---

## render_summary

```python
render_summary(self: Any)
```

Render a text-based KPI summary.

---
