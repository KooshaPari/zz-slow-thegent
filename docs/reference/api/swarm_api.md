# swarm API Reference

> **Source**: `src/thegent/orchestration/swarm.py`

Swarm coordination and shared memory for thegent (WP-1006).

---

## ACLMessage

WP-1006: JSON-ACL Message for inter-agent communication.

**Inherits from**: `BaseModel`

---

## Blackboard

WP-1006: Shared memory for multi-agent coordination.

### Methods

#### Blackboard.**init**

```python
__init__(self: Any, namespace: str)
```

---

#### Blackboard.list_keys

```python
list_keys(self: Any)
```

List all keys on the blackboard.

---

#### Blackboard.post

```python
post(self: Any, key: str, value: Any)
```

Post a finding or result to the blackboard.

---

#### Blackboard.read

```python
read(self: Any, key: str)
```

Read a value from the blackboard.

---

---

## ConsensusManager

WP-1006: Resolves conflicts when multiple agents propose solutions.

### Methods

#### ConsensusManager.resolve_by_confidence

```python
resolve_by_confidence(proposals: list[dict[(str, Any)]])
```

Pick the proposal with the highest confidence score.

---

#### ConsensusManager.resolve_by_vote

```python
resolve_by_vote(proposals: list[dict[(str, Any)]])
```

Majority vote on identical proposal values.

---

---

## NegotiationEngine

WP-1006: Handles inter-agent negotiation and Nash Equilibrium selection.

### Methods

#### NegotiationEngine.**init**

```python
__init__(self: Any, blackboard: Blackboard)
```

---

#### NegotiationEngine.resolve_conflict

```python
resolve_conflict(self: Any, proposals: list[ACLMessage])
```

Find the optimal proposal using utility scores.

---

---

## list_keys

```python
list_keys(self: Any)
```

List all keys on the blackboard.

---

## post

```python
post(self: Any, key: str, value: Any)
```

Post a finding or result to the blackboard.

---

## read

```python
read(self: Any, key: str)
```

Read a value from the blackboard.

---

## resolve_by_confidence

```python
resolve_by_confidence(proposals: list[dict[(str, Any)]])
```

Pick the proposal with the highest confidence score.

---

## resolve_by_vote

```python
resolve_by_vote(proposals: list[dict[(str, Any)]])
```

Majority vote on identical proposal values.

---

## resolve_conflict

```python
resolve_conflict(self: Any, proposals: list[ACLMessage])
```

Find the optimal proposal using utility scores.

---
