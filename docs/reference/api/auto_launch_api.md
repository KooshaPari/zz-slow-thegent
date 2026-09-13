# auto_launch API Reference

> **Source**: `src/thegent/planning/auto_launch.py`

Auto-launch system for workstream items.

Event-driven system that automatically launches workstream items when:

- Agent sessions complete
- Dependencies are cleared
- Capacity becomes available

Harmonized with all thegent components: WorkStreamManager, EvidenceLedger,
LaneModel, CostEstimator, DeferralManager, TaskRouter, TeamCoordinator, etc.

---

## AutoLaunchSystem

Event-driven auto-launch system for workstream items.

### Methods

#### AutoLaunchSystem.**init**

```python
__init__(self: Any, settings: Any)
```

Initialize auto-launch system with all component integrations.

**Parameters**:

- `settings`: ThegentSettings instance. Defaults to ThegentSettings().

---

#### AutoLaunchSystem.handle_completion

```python
handle_completion(self: Any, session_id: str, exit_code: int)
```

Handle session completion event.

**Parameters**:

- `session_id`: Completed session ID
- `exit_code`: Session exit code

---

#### AutoLaunchSystem.record_event

```python
record_event(self: Any, event_type: str, session_id: Any, item_id: Any, payload: Any)
```

Record an auto-launch event in the database.

**Parameters**:

- `event_type`: Type of event
- `session_id`: Associated session ID
- `item_id`: Associated workstream item ID
- `payload`: Optional event payload

---

#### AutoLaunchSystem.start

```python
start(self: Any)
```

Start the auto-launch system.

---

#### AutoLaunchSystem.stop

```python
stop(self: Any)
```

Stop the auto-launch system.

---

#### AutoLaunchSystem.sync_database

```python
sync_database(self: Any)
```

Sync workstream database with WORK_STREAM.md.

---

---

## handle_completion

```python
handle_completion(self: Any, session_id: str, exit_code: int)
```

Handle session completion event.

**Parameters**:

- `session_id`: Completed session ID
- `exit_code`: Session exit code

---

## periodic_tasks

---

## record_event

```python
record_event(self: Any, event_type: str, session_id: Any, item_id: Any, payload: Any)
```

Record an auto-launch event in the database.

**Parameters**:

- `event_type`: Type of event
- `session_id`: Associated session ID
- `item_id`: Associated workstream item ID
- `payload`: Optional event payload

---

## start

```python
start(self: Any)
```

Start the auto-launch system.

---

## stop

```python
stop(self: Any)
```

Stop the auto-launch system.

---

## sync_database

```python
sync_database(self: Any)
```

Sync workstream database with WORK_STREAM.md.

---
