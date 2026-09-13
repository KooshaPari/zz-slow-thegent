# multiverse API Reference

> **Source**: `src/thegent/planning/multiverse.py`

WP-38001: Alternate Reality Simulator (Plan Forks).

Allows the agent to simulate parallel timelines for a project plan to evaluate risks and opportunities.

---

## TimelineFork

A parallel version of the project plan.

---

## multiverseSimulator

Simulates multiple plan 'forks' simultaneously.

### Methods

#### multiverseSimulator.**init**

```python
__init__(self: Any, current_plan: Any)
```

---

#### multiverseSimulator.create_fork

```python
create_fork(self: Any, divergence_wp: str, proposed_delta: str)
```

WP-38001: Create a new parallel timeline for simulation.

---

#### multiverseSimulator.merge_timeline

```python
merge_timeline(self: Any, fork_id: str)
```

WP-38003: Reconcile a parallel timeline back into the main branch.

---

#### multiverseSimulator.simulate_impact

```python
simulate_impact(self: Any, fork_id: str)
```

WP-38002: Analyze the impact of a specific fork.

---

---

## create_fork

```python
create_fork(self: Any, divergence_wp: str, proposed_delta: str)
```

WP-38001: Create a new parallel timeline for simulation.

---

## merge_timeline

```python
merge_timeline(self: Any, fork_id: str)
```

WP-38003: Reconcile a parallel timeline back into the main branch.

---

## simulate_impact

```python
simulate_impact(self: Any, fork_id: str)
```

WP-38002: Analyze the impact of a specific fork.

---
