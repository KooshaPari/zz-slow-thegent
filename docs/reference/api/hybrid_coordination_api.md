# hybrid_coordination API Reference

> **Source**: `src/thegent/coordination/hybrid_coordination.py`

Adaptive hierarchical/P2P coordination strategy.

Switches between hierarchical (tree-based) and P2P (mesh) coordination
modes based on swarm size and average agent load.

Mode selection:
HIERARCHICAL — swarm_size &lt; THGENT_HIER_THRESHOLD (default 5) OR avg_load &lt; 0.3
P2P — swarm_size &gt;= threshold AND avg_load &gt;= 0.7
ADAPTIVE — gradual blend in the range [0.3, 0.7) avg_load

Routing:
HIERARCHICAL — always delegate to agents[0] (coordinator)
P2P — round-robin across all agents
ADAPTIVE — weighted blend: probabilistically picks coordinator vs
round-robin based on avg_load

---

## CoordinationMetrics

Snapshot of a routing decision.

---

## CoordinationMode

Available coordination modes.

**Inherits from**: `Enum`

---

## HybridCoordinationStrategy

Adaptive coordination strategy that blends hierarchical and P2P routing.

Usage::

    strategy = HybridCoordinationStrategy()
    mode = strategy.select_mode(swarm_size=8, avg_load=0.65)
    agent = strategy.route_task("task-1", agents, mode)

### Methods

#### HybridCoordinationStrategy.**init**

```python
__init__(self: Any)
```

Initialise strategy.

**Parameters**:

- `seed`: Optional RNG seed for deterministic ADAPTIVE routing in tests.

---

#### HybridCoordinationStrategy.coordinate

```python
coordinate(self: Any, task_id: str, agents: list[str], swarm_size: int, avg_load: float)
```

Select mode, route the task, and return :class:`CoordinationMetrics`.

**Parameters**:

- `task_id`: Task identifier.
- `agents`: Available agent IDs (non-empty).
- `swarm_size`: Total swarm size (may differ from `len(agents)`).
- `avg_load`: Average agent load (0.0 – 1.0).

**Returns**: :class:`CoordinationMetrics` with the routing decision.

---

#### HybridCoordinationStrategy.route_task

```python
route_task(self: Any, task_id: str, agents: list[str], mode: CoordinationMode, avg_load: float)
```

Route a task to an agent according to the given mode.

**Parameters**:

- `task_id`: Identifier of the task being routed.
- `agents`: Ordered list of available agent IDs. Must be non-empty.
- `mode`: The :class:`CoordinationMode` to apply.
- `avg_load`: Current average load (used only in ADAPTIVE mode for
  weighting; defaults to 0.5).

**Returns**: The chosen agent ID.

---

#### HybridCoordinationStrategy.select_mode

```python
select_mode(self: Any, swarm_size: int, avg_load: float)
```

Select the coordination mode based on swarm size and average load.

**Parameters**:

- `swarm_size`: Number of agents currently in the swarm.
- `avg_load`: Average load across agents (0.0 – 1.0).

**Returns**: The appropriate :class:`CoordinationMode`.

---

---

## coordinate

```python
coordinate(self: Any, task_id: str, agents: list[str], swarm_size: int, avg_load: float)
```

Select mode, route the task, and return :class:`CoordinationMetrics`.

**Parameters**:

- `task_id`: Task identifier.
- `agents`: Available agent IDs (non-empty).
- `swarm_size`: Total swarm size (may differ from `len(agents)`).
- `avg_load`: Average agent load (0.0 – 1.0).

**Returns**: :class:`CoordinationMetrics` with the routing decision.

---

## route_task

```python
route_task(self: Any, task_id: str, agents: list[str], mode: CoordinationMode, avg_load: float)
```

Route a task to an agent according to the given mode.

**Parameters**:

- `task_id`: Identifier of the task being routed.
- `agents`: Ordered list of available agent IDs. Must be non-empty.
- `mode`: The :class:`CoordinationMode` to apply.
- `avg_load`: Current average load (used only in ADAPTIVE mode for
  weighting; defaults to 0.5).

**Returns**: The chosen agent ID.

**Raises**:

- `ValueError`: If _agents_ is empty.

---

## select_mode

```python
select_mode(self: Any, swarm_size: int, avg_load: float)
```

Select the coordination mode based on swarm size and average load.

**Parameters**:

- `swarm_size`: Number of agents currently in the swarm.
- `avg_load`: Average load across agents (0.0 – 1.0).

**Returns**: The appropriate :class:`CoordinationMode`.

---
