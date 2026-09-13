# metrics API Reference

> **Source**: `src/thegent/governance/metrics.py`

Provider metrics collection and storage (WP-5003).

Collects and maintains provider performance metrics (latency, reliability, cost)
for use in provider scoring and cost-aware routing decisions.

See: docs/changes/research-economic-governance/design.md § 2.1

---

## AggregatedMetrics

Aggregated provider metrics over a time window.

### Methods

#### AggregatedMetrics.latency_mean

```python
latency_mean(self: Any)
```

Calculate mean latency in milliseconds.

**Returns**: Mean latency, or 250.0 if no samples

---

#### AggregatedMetrics.latency_p99

```python
latency_p99(self: Any)
```

Calculate 99th percentile latency in milliseconds.

**Returns**: P99 latency, or baseline (250ms) if insufficient samples

---

#### AggregatedMetrics.reliability

```python
reliability(self: Any)
```

Calculate success rate (0.0-1.0).

**Returns**: Success rate, or 0.0 if no requests

---

---

## MetricsCollector

Collects and aggregates provider metrics.

Maintains in-memory metrics with periodic aggregation.
Supports persistence to JSON for historical analysis.

### Methods

#### MetricsCollector.**init**

```python
__init__(self: Any, storage_dir: Any)
```

Initialize metrics collector.

**Parameters**:

- `storage_dir`: Optional directory for persistent storage (JSON files)

---

#### MetricsCollector.clear_all

```python
clear_all(self: Any)
```

Clear all metrics (for testing).

WARNING: This should only be called during tests.

---

#### MetricsCollector.get_all_metrics

```python
get_all_metrics(self: Any)
```

Get aggregated metrics for all providers.

**Returns**: Dictionary mapping provider_id -> AggregatedMetrics

---

#### MetricsCollector.get_metrics

```python
get_metrics(self: Any, provider_id: str)
```

Get aggregated metrics for a provider.

**Parameters**:

- `provider_id`: Provider identifier

**Returns**: Aggregated metrics or None if provider not found

---

#### MetricsCollector.get_query_latency_ms

```python
get_query_latency_ms(self: Any)
```

Get metrics query latency (should be `<50ms` per SLO).

**Returns**: Estimated query latency in milliseconds (always ~0 for in-memory)

---

#### MetricsCollector.load_from_file

```python
load_from_file(self: Any, filepath: Path)
```

Load metrics from JSON file.

**Parameters**:

- `filepath`: Path to metrics JSON file

**Returns**: Loaded metrics or None on error

---

#### MetricsCollector.record

```python
record(self: Any, snapshot: ProviderMetricsSnapshot)
```

Record a single provider measurement.

**Parameters**:

- `snapshot`: Performance measurement to record

---

#### MetricsCollector.reset_provider

```python
reset_provider(self: Any, provider_id: str)
```

Reset metrics for a provider (for testing).

**Parameters**:

- `provider_id`: Provider identifier to reset

---

#### MetricsCollector.save_to_file

```python
save_to_file(self: Any, provider_id: str)
```

Save metrics for a provider to JSON file.

**Parameters**:

- `provider_id`: Provider identifier

**Returns**: Path to saved file or None if storage not configured

---

---

## ProviderMetricsSnapshot

Single measurement of provider performance.

---

## clear_all

```python
clear_all(self: Any)
```

Clear all metrics (for testing).

WARNING: This should only be called during tests.

---

## get_all_metrics

```python
get_all_metrics(self: Any)
```

Get aggregated metrics for all providers.

**Returns**: Dictionary mapping provider_id -> AggregatedMetrics

---

## get_metrics

```python
get_metrics(self: Any, provider_id: str)
```

Get aggregated metrics for a provider.

**Parameters**:

- `provider_id`: Provider identifier

**Returns**: Aggregated metrics or None if provider not found

---

## get_metrics_collector

Get or create the global metrics collector.

**Returns**: Metrics collector instance

---

## get_query_latency_ms

```python
get_query_latency_ms(self: Any)
```

Get metrics query latency (should be `<50ms` per SLO).

**Returns**: Estimated query latency in milliseconds (always ~0 for in-memory)

---

## initialize_metrics_collector

```python
initialize_metrics_collector(storage_dir: Any)
```

Initialize the global metrics collector.

**Parameters**:

- `storage_dir`: Optional directory for persistent storage

**Returns**: Initialized metrics collector

---

## latency_mean

```python
latency_mean(self: Any)
```

Calculate mean latency in milliseconds.

**Returns**: Mean latency, or 250.0 if no samples

---

## latency_p99

```python
latency_p99(self: Any)
```

Calculate 99th percentile latency in milliseconds.

**Returns**: P99 latency, or baseline (250ms) if insufficient samples

---

## load_from_file

```python
load_from_file(self: Any, filepath: Path)
```

Load metrics from JSON file.

**Parameters**:

- `filepath`: Path to metrics JSON file

**Returns**: Loaded metrics or None on error

---

## record

```python
record(self: Any, snapshot: ProviderMetricsSnapshot)
```

Record a single provider measurement.

**Parameters**:

- `snapshot`: Performance measurement to record

---

## reliability

```python
reliability(self: Any)
```

Calculate success rate (0.0-1.0).

**Returns**: Success rate, or 0.0 if no requests

---

## reset_provider

```python
reset_provider(self: Any, provider_id: str)
```

Reset metrics for a provider (for testing).

**Parameters**:

- `provider_id`: Provider identifier to reset

---

## save_to_file

```python
save_to_file(self: Any, provider_id: str)
```

Save metrics for a provider to JSON file.

**Parameters**:

- `provider_id`: Provider identifier

**Returns**: Path to saved file or None if storage not configured

---
