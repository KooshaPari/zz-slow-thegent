# observability API Reference

> **Source**: `src/thegent/mesh/observability.py`

Observability and metrics for the agent mesh.

---

## MeshLogger

JSONL structured logging (SCLI-P13.1).

### Methods

#### MeshLogger.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### MeshLogger.log

```python
log(self: Any, agent_id: str, event: str, data: Any)
```

Append a structured log entry.

---

---

## MetricsAggregator

Mesh metrics aggregation (SCLI-P13.2).

### Methods

#### MetricsAggregator.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### MetricsAggregator.get_summary

```python
get_summary(self: Any)
```

Aggregate metrics for all agents (SCLI-P13.4).

---

#### MetricsAggregator.record_metric

```python
record_metric(self: Any, agent_id: str, name: str, value: float)
```

Record a single metric point.

---

---

## get_summary

```python
get_summary(self: Any)
```

Aggregate metrics for all agents (SCLI-P13.4).

---

## log

```python
log(self: Any, agent_id: str, event: str, data: Any)
```

Append a structured log entry.

---

## mesh_status_cmd

```python
mesh_status_cmd(mesh_root: Path)
```

CLI 'mesh status' (SCLI-P13.3).

---

## record_metric

```python
record_metric(self: Any, agent_id: str, name: str, value: float)
```

Record a single metric point.

---
