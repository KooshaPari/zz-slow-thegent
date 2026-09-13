# reward_model API Reference

> **Source**: `src/thegent/agents/reward_model.py`

WP-39003: Recursive Reward Modeling Optimization.

This module implements recursive reward modeling for agent optimization,
integrating with heliosShield bridge (WP-16003) for task coordination.

---

## RecursiveRewardModel

WP-39003: Recursive Reward Modeling Optimization.

Implements recursive reward modeling that learns from agent performance
and optimizes reward signals over time. Integrates with heliosShield bridge
for task coordination.

### Methods

#### RecursiveRewardModel.**init**

```python
__init__(self: Any)
```

Initialize the recursive reward model.

---

#### RecursiveRewardModel.get_reward_statistics

```python
get_reward_statistics(self: Any)
```

Get statistics about recorded rewards.

**Returns**: Dictionary with reward statistics

---

#### RecursiveRewardModel.optimize

```python
optimize(self: Any)
```

Perform recursive optimization of reward model.

**Returns**: Dictionary with optimization results and metrics

---

#### RecursiveRewardModel.record_reward

```python
record_reward(self: Any, agent_id: str, task_id: str, reward_value: float, metadata: Any)
```

Record a reward signal for optimization.

**Parameters**:

- `agent_id`: Identifier for the agent
- `task_id`: Identifier for the task
- `reward_value`: Reward value (higher is better)
- `metadata`: Optional metadata about the reward

---

---

## RewardSignal

Represents a reward signal for model optimization.

---

## get_reward_statistics

```python
get_reward_statistics(self: Any)
```

Get statistics about recorded rewards.

**Returns**: Dictionary with reward statistics

---

## optimize

```python
optimize(self: Any)
```

Perform recursive optimization of reward model.

**Returns**: Dictionary with optimization results and metrics

---

## record_reward

```python
record_reward(self: Any, agent_id: str, task_id: str, reward_value: float, metadata: Any)
```

Record a reward signal for optimization.

**Parameters**:

- `agent_id`: Identifier for the agent
- `task_id`: Identifier for the task
- `reward_value`: Reward value (higher is better)
- `metadata`: Optional metadata about the reward

---
