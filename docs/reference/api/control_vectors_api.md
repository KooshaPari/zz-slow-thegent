# control_vectors API Reference

> **Source**: `src/thegent/governance/control_vectors.py`

WP-33002: Behavioral Steering via Semantic Injection.

Influences black-box agents by proactively modifying their environment and context.
Injects 'control vectors' (semantic hints, mock tools, system state) to steer behavior.

---

## ControlVectorManager

Manages semantic injection vectors for steering black-box agents.

### Methods

#### ControlVectorManager.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### ControlVectorManager.analyze_and_inject

```python
analyze_and_inject(self: Any, prompt: str, agent_state: dict[(str, Any)])
```

Analyze prompt and state to decide which control vectors to inject.

---

#### ControlVectorManager.prepare_environment

```python
prepare_environment(self: Any, workspace_path: Path)
```

Proactively modify the physical environment to steer behavior (e.g. mock tools).

---

---

## analyze_and_inject

```python
analyze_and_inject(self: Any, prompt: str, agent_state: dict[(str, Any)])
```

Analyze prompt and state to decide which control vectors to inject.

---

## prepare_environment

```python
prepare_environment(self: Any, workspace_path: Path)
```

Proactively modify the physical environment to steer behavior (e.g. mock tools).

---
