# registry API Reference

> **Source**: `src/thegent/agents/registry.py`

Agent registry.

---

## LearningCandidate

Represents a candidate model or configuration for autonomous learning.

### Methods

#### LearningCandidate.**init**

```python
__init__(self: Any, model_id: str, baseline_id: str)
```

---

#### LearningCandidate.add_metric

```python
add_metric(self: Any, name: str, value: float)
```

---

---

## LearningRegistry

Registry for autonomous learning models and metrics (WP-14001).

### Methods

#### LearningRegistry.**init**

```python
__init__(self: Any)
```

---

#### LearningRegistry.get_active_model

```python
get_active_model(self: Any)
```

Get the currently active model ID.

---

#### LearningRegistry.get_candidate

```python
get_candidate(self: Any, model_id: str)
```

Get candidate metadata.

---

#### LearningRegistry.promote

```python
promote(self: Any, canary_id: str, require_approval: bool)
```

Promote a canary model to default status.

---

#### LearningRegistry.record_feedback

```python
record_feedback(self: Any, model_id: str, success: bool, quality_score: float)
```

Record human or system feedback for a learning candidate.

---

#### LearningRegistry.record_metric

```python
record_metric(self: Any, model_id: str, name: str, value: float)
```

Record a performance metric for a model.

---

#### LearningRegistry.register_canary

```python
register_canary(self: Any, canary_id: str, baseline_id: str)
```

Register a new canary model for testing.

---

#### LearningRegistry.should_rollback

```python
should_rollback(self: Any, canary_id: str)
```

Determine if a canary model should be rolled back to baseline.

---

---

## add_metric

```python
add_metric(self: Any, name: str, value: float)
```

---

## get_active_model

```python
get_active_model(self: Any)
```

Get the currently active model ID.

---

## get_candidate

```python
get_candidate(self: Any, model_id: str)
```

Get candidate metadata.

---

## get_fallback_agents

```python
get_fallback_agents(agent_name: str)
```

Return fallback agents when this provider hits usage limit. Excludes current agent.

---

## get_runner

```python
get_runner(agent_name: str)
```

Get runner for agent. Returns None for unknown.

---

## list_agent_names

List available agent names (canonical CLI names).

---

## list_droid_names

```python
list_droid_names(droids_dir: Path)
```

List available droid names from .md files (legacy; droids disabled).

---

## promote

```python
promote(self: Any, canary_id: str, require_approval: bool)
```

Promote a canary model to default status.

---

## record_feedback

```python
record_feedback(self: Any, model_id: str, success: bool, quality_score: float)
```

Record human or system feedback for a learning candidate.

---

## record_metric

```python
record_metric(self: Any, model_id: str, name: str, value: float)
```

Record a performance metric for a model.

---

## register_canary

```python
register_canary(self: Any, canary_id: str, baseline_id: str)
```

Register a new canary model for testing.

---

## resolve_agent

```python
resolve_agent(agent_name: Any)
```

Resolve label/alias to canonical CLI name. E.g. 'cursor' -> 'cursor-agent'.

---

## should_rollback

```python
should_rollback(self: Any, canary_id: str)
```

Determine if a canary model should be rolled back to baseline.

---
