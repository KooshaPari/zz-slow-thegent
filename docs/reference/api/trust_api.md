# trust API Reference

> **Source**: `src/thegent/governance/trust.py`

WP-3007: Trust boundary checks.

OPT-008: LRU cache for policy evaluation results (with TTL) - `<50ms` repeated evaluations.

---

## TrustBoundaryChecker

Enforces trust boundaries between agents and tasks.

OPT-008: Uses LRU cache with TTL for repeated policy evaluations.

### Methods

#### TrustBoundaryChecker.**init**

```python
__init__(self: Any, settings: ThegentSettings, cache_ttl_sec: int)
```

Initialize trust boundary checker.

**Parameters**:

- `settings`: Thegent settings
- `cache_ttl_sec`: Cache TTL in seconds (default: 5 minutes)

---

#### TrustBoundaryChecker.check_data_flow

```python
check_data_flow(self: Any, source_agent: str, dest_agent: str)
```

Verify data flow from source to destination is allowed.

---

#### TrustBoundaryChecker.evaluate_routing

```python
evaluate_routing(self: Any, task_prompt: str, target_agent: str)
```

Evaluate if routing a task to an agent violates trust boundaries.

Checks for sensitive keywords in prompt vs agent trust level.

OPT-008: Caches results for repeated evaluations (`<50ms` for cached lookups).

**Parameters**:

- `task_prompt`: Task prompt text
- `target_agent`: Target agent name

**Returns**: Evaluation result dict with "allowed", "reason", "agent_trust", "risk_score"

---

#### TrustBoundaryChecker.get_agent_trust

```python
get_agent_trust(self: Any, agent_name: str)
```

Return trust level for an agent.

---

---

## TrustLevel

Trust levels for agents and domains.

**Inherits from**: `enum.IntEnum`

---

## check_data_flow

```python
check_data_flow(self: Any, source_agent: str, dest_agent: str)
```

Verify data flow from source to destination is allowed.

---

## evaluate_routing

```python
evaluate_routing(self: Any, task_prompt: str, target_agent: str)
```

Evaluate if routing a task to an agent violates trust boundaries.

Checks for sensitive keywords in prompt vs agent trust level.

OPT-008: Caches results for repeated evaluations (`<50ms` for cached lookups).

**Parameters**:

- `task_prompt`: Task prompt text
- `target_agent`: Target agent name

**Returns**: Evaluation result dict with "allowed", "reason", "agent_trust", "risk_score"

---

## get_agent_trust

```python
get_agent_trust(self: Any, agent_name: str)
```

Return trust level for an agent.

---
