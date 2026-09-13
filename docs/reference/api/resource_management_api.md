# resource_management API Reference

> **Source**: `src/thegent/orchestration/resource_management.py`

Advanced resource management with extended indices, prediction, and harness modeling.

Features:

- Extended resource indices (CPU, memory, FD, network, disk, GPU, etc.)
- Statistical distributions (min, avg, peak, stddev, percentiles) for all resources
- Prediction engine for forecasting resource needs
- Harness card system for modeling harness usage with statistical models
- Leak detection (memory leaks, FD leaks, child process leaks)
- Child process and thread tracking
- Bottleneck detection and analysis
- Speculative execution strategies
- Work chunking and parallelization

---

## BottleneckDetector

Detect bottlenecks in agent execution loops.

### Methods

#### BottleneckDetector.**init**

```python
__init__(self: Any)
```

---

#### BottleneckDetector.detect_resource_contention

```python
detect_resource_contention(self: Any, snapshot: ExtendedResourceSnapshot, harness_cards: dict[(str, HarnessCard)])
```

Detect resource contention between harnesses.

---

#### BottleneckDetector.identify_slow_points

```python
identify_slow_points(self: Any)
```

Identify slow points in agent loops.

---

#### BottleneckDetector.record_loop_timing

```python
record_loop_timing(self: Any, loop_id: str, duration_ms: float)
```

Record timing for an agent loop iteration.

---

---

## ExtendedResourceSnapshot

Extended resource snapshot with comprehensive system metrics.

---

## HarnessCard

Model for individual harness type resource usage with statistical distributions.

### Methods

#### HarnessCard.estimate_resources

```python
estimate_resources(self: Any, session_count: int, isolated: bool, use_peak: bool, use_p95: bool)
```

Estimate resource usage for N sessions using statistical distributions.

**Parameters**:

- `session_count`: Number of sessions
- `isolated`: Whether sessions run in isolation
- `use_peak`: Use peak values instead of average (conservative)
- `use_p95`: Use p95 values instead of average (recommended)

---

---

## LeakMetrics

Metrics for detecting resource leaks.

---

## ResourceDistribution

Statistical distribution for a resource metric.

### Methods

#### ResourceDistribution.compute_stats

```python
compute_stats(self: Any, values: list[float])
```

Compute full statistics from a list of values.

---

#### ResourceDistribution.update

```python
update(self: Any, value: float)
```

Update distribution with a new value.

---

---

## ResourcePredictionEngine

Predict future resource needs based on historical patterns.

### Methods

#### ResourcePredictionEngine.**init**

```python
__init__(self: Any, history_file: Any)
```

---

#### ResourcePredictionEngine.detect_anomalies

```python
detect_anomalies(self: Any, current: ExtendedResourceSnapshot)
```

Detect anomalous resource usage patterns.

---

#### ResourcePredictionEngine.predict_next_interval

```python
predict_next_interval(self: Any, interval_seconds: int)
```

Predict resource usage for next interval.

---

#### ResourcePredictionEngine.record

```python
record(self: Any, snapshot: ExtendedResourceSnapshot)
```

Record a resource snapshot and detect leaks.

---

---

## compute_stats

```python
compute_stats(self: Any, values: list[float])
```

Compute full statistics from a list of values.

---

## create_harness_cards

Create default harness cards with statistical distributions for all resources.

---

## detect_anomalies

```python
detect_anomalies(self: Any, current: ExtendedResourceSnapshot)
```

Detect anomalous resource usage patterns.

---

## detect_leaks

```python
detect_leaks(history: deque[ExtendedResourceSnapshot], current: ExtendedResourceSnapshot, window_hours: float)
```

Detect resource leaks from historical snapshots.

---

## detect_resource_contention

```python
detect_resource_contention(self: Any, snapshot: ExtendedResourceSnapshot, harness_cards: dict[(str, HarnessCard)])
```

Detect resource contention between harnesses.

---

## estimate_resources

```python
estimate_resources(self: Any, session_count: int, isolated: bool, use_peak: bool, use_p95: bool)
```

Estimate resource usage for N sessions using statistical distributions.

**Parameters**:

- `session_count`: Number of sessions
- `isolated`: Whether sessions run in isolation
- `use_peak`: Use peak values instead of average (conservative)
- `use_p95`: Use p95 values instead of average (recommended)

---

## identify_slow_points

```python
identify_slow_points(self: Any)
```

Identify slow points in agent loops.

---

## predict_next_interval

```python
predict_next_interval(self: Any, interval_seconds: int)
```

Predict resource usage for next interval.

---

## record

```python
record(self: Any, snapshot: ExtendedResourceSnapshot)
```

Record a resource snapshot and detect leaks.

---

## record_loop_timing

```python
record_loop_timing(self: Any, loop_id: str, duration_ms: float)
```

Record timing for an agent loop iteration.

---

## sample_extended_resources

Sample extended system resources including child processes, threads, sockets, and leak indicators.

---

## update

```python
update(self: Any, value: float)
```

Update distribution with a new value.

---
