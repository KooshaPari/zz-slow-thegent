# replay API Reference

> **Source**: `src/thegent/simulation/replay.py`

Simulation & Sandbox (Deterministic Replay).

---

## SimulationReplay

Deterministic simulation replay.

### Methods

#### SimulationReplay.**init**

```python
__init__(self: Any, replay_dir: Any)
```

Initialize simulation replay.

**Parameters**:

- `replay_dir`: Replay directory

---

#### SimulationReplay.load_replay

```python
load_replay(self: Any, replay_id: str)
```

Load replay from file.

**Parameters**:

- `replay_id`: Replay identifier

**Returns**: List of events

---

#### SimulationReplay.record_event

```python
record_event(self: Any, event_type: str, data: dict[(str, Any)])
```

Record an event.

**Parameters**:

- `event_type`: Event type
- `data`: Event data

---

#### SimulationReplay.replay

```python
replay(self: Any, replay_id: str)
```

Replay a simulation.

**Parameters**:

- `replay_id`: Replay identifier

**Returns**: Replay results

---

#### SimulationReplay.save_replay

```python
save_replay(self: Any, replay_id: str)
```

Save replay to file.

**Parameters**:

- `replay_id`: Replay identifier

**Returns**: Path to replay file

---

---

## load_replay

```python
load_replay(self: Any, replay_id: str)
```

Load replay from file.

**Parameters**:

- `replay_id`: Replay identifier

**Returns**: List of events

---

## record_event

```python
record_event(self: Any, event_type: str, data: dict[(str, Any)])
```

Record an event.

**Parameters**:

- `event_type`: Event type
- `data`: Event data

---

## replay

```python
replay(self: Any, replay_id: str)
```

Replay a simulation.

**Parameters**:

- `replay_id`: Replay identifier

**Returns**: Replay results

---

## save_replay

```python
save_replay(self: Any, replay_id: str)
```

Save replay to file.

**Parameters**:

- `replay_id`: Replay identifier

**Returns**: Path to replay file

---
