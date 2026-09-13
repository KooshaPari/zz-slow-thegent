# monitoring_engine API Reference

> **Source**: `src/thegent/agent/monitoring_engine.py`

Monitoring engine for agent crew.

---

## MonitoringEngine

Monitor agent crew execution.

### Methods

#### MonitoringEngine.**init**

```python
__init__(self: Any)
```

Initialize monitoring engine.

---

#### MonitoringEngine.get_metrics

```python
get_metrics(self: Any, name: Any)
```

Get metrics.

**Parameters**:

- `name`: Optional metric name filter

**Returns**: List of metrics

---

#### MonitoringEngine.get_summary

```python
get_summary(self: Any)
```

Get monitoring summary.

**Returns**: Summary dictionary

---

#### MonitoringEngine.record_metric

```python
record_metric(self: Any, name: str, value: Any, tags: Any)
```

Record a metric.

**Parameters**:

- `name`: Metric name
- `value`: Metric value
- `tags`: Optional tags

---

---

## get_metrics

```python
get_metrics(self: Any, name: Any)
```

Get metrics.

**Parameters**:

- `name`: Optional metric name filter

**Returns**: List of metrics

---

## get_summary

```python
get_summary(self: Any)
```

Get monitoring summary.

**Returns**: Summary dictionary

---

## record_metric

```python
record_metric(self: Any, name: str, value: Any, tags: Any)
```

Record a metric.

**Parameters**:

- `name`: Metric name
- `value`: Metric value
- `tags`: Optional tags

---
