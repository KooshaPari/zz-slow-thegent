# swarm_consensus API Reference

> **Source**: `src/thegent/orchestration/swarm_consensus.py`

WP-24001: Swarm Consensus Protocol (Byzantine).

Ensures agreement on task outcomes across a swarm of autonomous agents.
Uses a simplified Byzantine Fault Tolerance (BFT) pattern.

---

## SwarmConsensus

Orchestrates consensus across multiple swarm agents.

### Methods

#### SwarmConsensus.**init**

```python
__init__(self: Any, task_id: str, threshold: float)
```

---

#### SwarmConsensus.evaluate_consensus

```python
evaluate_consensus(self: Any, total_agents: int)
```

Evaluate if consensus has been reached based on the threshold.

---

#### SwarmConsensus.get_audit_trail

```python
get_audit_trail(self: Any)
```

Generate a cryptographic audit trail for the consensus process.

---

#### SwarmConsensus.record_vote

```python
record_vote(self: Any, agent_id: str, vote: Any, signature: str)
```

Record a vote from an agent in the swarm.

---

---

## SwarmVote

A single agent's vote on a task outcome.

**Inherits from**: `BaseModel`

---

## evaluate_consensus

```python
evaluate_consensus(self: Any, total_agents: int)
```

Evaluate if consensus has been reached based on the threshold.

---

## get_audit_trail

```python
get_audit_trail(self: Any)
```

Generate a cryptographic audit trail for the consensus process.

---

## record_vote

```python
record_vote(self: Any, agent_id: str, vote: Any, signature: str)
```

Record a vote from an agent in the swarm.

---
