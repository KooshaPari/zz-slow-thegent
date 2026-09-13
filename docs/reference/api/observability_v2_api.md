# observability_v2 API Reference

> **Source**: `src/thegent/observability/observability_v2.py`

Phase 18: Observability v2 implementation.

Includes JSONL structured logging, advanced metrics, and mesh management CLI.

---

## AdvancedMetrics

Aggregates advanced metrics per agent and command.

### Methods

#### AdvancedMetrics.**init**

```python
__init__(self: Any, metrics_file: Path)
```

---

#### AdvancedMetrics.record

```python
record(self: Any, agent_id: str, command: str, duration: float, success: bool)
```

---

---

## JSONLFormatter

Formats log records as JSONL.

**Inherits from**: `logging.Formatter`

### Methods

#### JSONLFormatter.format

```python
format(self: Any, record: Any)
```

---

---

## MeshCLI

CLI functions for mesh management.

### Methods

#### MeshCLI.status

```python
status(mesh_dir: Path)
```

Show summary status of the agent mesh.

---

#### MeshCLI.tasks

```python
tasks(mesh_dir: Path)
```

Show status of tasks in the mesh.

---

---

## format

```python
format(self: Any, record: Any)
```

---

## record

```python
record(self: Any, agent_id: str, command: str, duration: float, success: bool)
```

---

## status

```python
status(mesh_dir: Path)
```

Show summary status of the agent mesh.

---

## tasks

```python
tasks(mesh_dir: Path)
```

Show status of tasks in the mesh.

---
