# reputation API Reference

> **Source**: `src/thegent/economy/reputation.py`

WP-26003: Decentralized Reputation System.

Tracks agent performance and reliability across the global mesh.
Uses weighted feedback and consensus to build decentralized trust scores.

---

## ReputationEntry

A single reputation event for an agent.

**Inherits from**: `BaseModel`

---

## ReputationManager

Manages decentralized trust and reputation for mesh agents.

### Methods

#### ReputationManager.**init**

```python
__init__(self: Any, db_path: Any)
```

---

#### ReputationManager.get_all_scores

```python
get_all_scores(self: Any)
```

Get all agent trust scores.

---

#### ReputationManager.get_reputation_report

```python
get_reputation_report(self: Any, agent_id: str)
```

Generate a detailed reputation report for an agent.

---

#### ReputationManager.get_trust_score

```python
get_trust_score(self: Any, agent_id: str)
```

Retrieve the current trust score for an agent.

---

#### ReputationManager.submit_rating

```python
submit_rating(self: Any, agent_id: str, reviewer_id: str, task_id: str, rating: float, feedback: str)
```

Submit a rating for an agent's performance on a task.

---

---

## get_all_scores

```python
get_all_scores(self: Any)
```

Get all agent trust scores.

---

## get_reputation_report

```python
get_reputation_report(self: Any, agent_id: str)
```

Generate a detailed reputation report for an agent.

---

## get_trust_score

```python
get_trust_score(self: Any, agent_id: str)
```

Retrieve the current trust score for an agent.

---

## submit_rating

```python
submit_rating(self: Any, agent_id: str, reviewer_id: str, task_id: str, rating: float, feedback: str)
```

Submit a rating for an agent's performance on a task.

---
