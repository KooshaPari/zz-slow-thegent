# policy_evolver API Reference

> **Source**: `src/thegent/agents/policy_evolver.py`

WP-20001: Self-Evolving Policy Controller.

Analyzes run failures and evolves policy thresholds automatically.

---

## PolicyEvolver

Analyzes execution logs and proposes automatic policy adjustments.

### Methods

#### PolicyEvolver.**init**

```python
__init__(self: Any, session_dir: Path, settings: Any)
```

---

#### PolicyEvolver.evolve

```python
evolve(self: Any, lookback_runs: int)
```

Analyze recent runs and propose policy updates.

---

---

## evolve

```python
evolve(self: Any, lookback_runs: int)
```

Analyze recent runs and propose policy updates.

---
