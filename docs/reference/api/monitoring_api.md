# monitoring API Reference

> **Source**: `src/thegent/crew/monitoring.py`

MonitoringEngine for health, performance, and cost tracking.

---

## CostMetrics

Cost tracking metrics.

---

## HealthStatus

Health status of a crew or agent.

---

## MonitoringEngine

Monitoring engine for crew execution.

Tracks:

- Health status
- Performance metrics
- Cost metrics
- Agent utilization

### Methods

#### MonitoringEngine.**init**

```python
__init__(self: Any)
```

Initialize MonitoringEngine.

---

#### MonitoringEngine.check_health

```python
check_health(self: Any, crew: Crew)
```

Check health of a crew.

**Parameters**:

- `crew`: Crew to check

**Returns**: HealthStatus

---

#### MonitoringEngine.get_summary

```python
get_summary(self: Any, crew_id: str)
```

Get monitoring summary for a crew.

**Parameters**:

- `crew_id`: Crew identifier

**Returns**: Summary dictionary

---

#### MonitoringEngine.record_execution

```python
record_execution(self: Any, crew_id: str, results: dict[(str, ExecutionResult)], metadata: Any)
```

Record execution for history tracking.

**Parameters**:

- `crew_id`: Crew identifier
- `results`: Execution results
- `metadata`: Optional metadata

---

#### MonitoringEngine.track_costs

```python
track_costs(self: Any, crew_id: str, results: dict[(str, ExecutionResult)])
```

Track cost metrics for crew execution.

**Parameters**:

- `crew_id`: Crew identifier
- `results`: Execution results

**Returns**: CostMetrics

---

#### MonitoringEngine.track_performance

```python
track_performance(self: Any, crew_id: str, results: dict[(str, ExecutionResult)])
```

Track performance metrics for crew execution.

**Parameters**:

- `crew_id`: Crew identifier
- `results`: Execution results

**Returns**: PerformanceMetrics

---

---

## PerformanceMetrics

Performance metrics.

---

## check_health

```python
check_health(self: Any, crew: Crew)
```

Check health of a crew.

**Parameters**:

- `crew`: Crew to check

**Returns**: HealthStatus

---

## get_summary

```python
get_summary(self: Any, crew_id: str)
```

Get monitoring summary for a crew.

**Parameters**:

- `crew_id`: Crew identifier

**Returns**: Summary dictionary

---

## record_execution

```python
record_execution(self: Any, crew_id: str, results: dict[(str, ExecutionResult)], metadata: Any)
```

Record execution for history tracking.

**Parameters**:

- `crew_id`: Crew identifier
- `results`: Execution results
- `metadata`: Optional metadata

---

## track_costs

```python
track_costs(self: Any, crew_id: str, results: dict[(str, ExecutionResult)])
```

Track cost metrics for crew execution.

**Parameters**:

- `crew_id`: Crew identifier
- `results`: Execution results

**Returns**: CostMetrics

---

## track_performance

```python
track_performance(self: Any, crew_id: str, results: dict[(str, ExecutionResult)])
```

Track performance metrics for crew execution.

**Parameters**:

- `crew_id`: Crew identifier
- `results`: Execution results

**Returns**: PerformanceMetrics

---
