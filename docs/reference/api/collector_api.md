# collector API Reference

> **Source**: `src/thegent/metrics/collector.py`

Metrics collection system.

---

## MetricsCollector

Metrics collection.

### Methods

#### MetricsCollector.**init**

```python
__init__(self: Any)
```

Initialize metrics collector.

---

#### MetricsCollector.get_stats

```python
get_stats(self: Any, metric_name: str)
```

Get statistics for metric.

**Parameters**:

- `metric_name`: Metric name

**Returns**: Statistics dictionary

---

#### MetricsCollector.record

```python
record(self: Any, metric_name: str, value: float)
```

Record a metric.

**Parameters**:

- `metric_name`: Metric name
- `value`: Metric value

---

---

## get_stats

```python
get_stats(self: Any, metric_name: str)
```

Get statistics for metric.

**Parameters**:

- `metric_name`: Metric name

**Returns**: Statistics dictionary

---

## record

```python
record(self: Any, metric_name: str, value: float)
```

Record a metric.

**Parameters**:

- `metric_name`: Metric name
- `value`: Metric value

---
