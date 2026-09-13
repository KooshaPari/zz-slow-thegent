# discovery_v2 API Reference

> **Source**: `src/thegent/infra/discovery_v2.py`

Phase 12: Process Discovery implementation (v2).

Includes /proc scanner with agent patterns, heartbeats, and cleanup.

---

## AgentManifest

Manages agent manifest files.

### Methods

#### AgentManifest.create

```python
create(manifest_path: Path, agent_info: dict[(str, Any)])
```

Create or update agent manifest.

---

---

## AgentScanner

Scans for agent processes using specific patterns.

### Methods

#### AgentScanner.scan

```python
scan(self: Any)
```

Scan process tree for agents.

---

---

## HeartbeatMonitor

Manages agent heartbeats and stale detection.

### Methods

#### HeartbeatMonitor.**init**

```python
__init__(self: Any, heartbeat_dir: Path, failure_threshold: int)
```

---

#### HeartbeatMonitor.beat

```python
beat(self: Any, agent_id: str)
```

Register a heartbeat for an agent.

---

#### HeartbeatMonitor.cleanup_stale

```python
cleanup_stale(self: Any, callback: Any)
```

Cleanup stale agent records.

---

#### HeartbeatMonitor.get_stale_agents

```python
get_stale_agents(self: Any)
```

Find agents that haven't beaten within threshold.

---

---

## beat

```python
beat(self: Any, agent_id: str)
```

Register a heartbeat for an agent.

---

## cleanup_stale

```python
cleanup_stale(self: Any, callback: Any)
```

Cleanup stale agent records.

---

## create

```python
create(manifest_path: Path, agent_info: dict[(str, Any)])
```

Create or update agent manifest.

---

## get_stale_agents

```python
get_stale_agents(self: Any)
```

Find agents that haven't beaten within threshold.

---

## scan

```python
scan(self: Any)
```

Scan process tree for agents.

---
