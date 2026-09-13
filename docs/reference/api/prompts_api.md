# prompts API Reference

> **Source**: `src/thegent/orchestration/prompts.py`

WP-Y5: Hierarchical prompt orchestration.

---

## PromptOrchestrator

Manages hierarchical decomposition of prompts and multi-agent routing.

### Methods

#### PromptOrchestrator.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### PromptOrchestrator.decompose

```python
decompose(self: Any, goal: str)
```

Decompose a high-level goal into a sequence of sub-tasks.

In a real system, this would call an LLM (Decomposer Agent).
For now, we use a simple rule-based approach for demonstration.

---

#### PromptOrchestrator.route_subtasks

```python
route_subtasks(self: Any, sub_tasks: list[dict[(str, Any)]])
```

Assign appropriate agents to sub-tasks based on content.

---

---

## decompose

```python
decompose(self: Any, goal: str)
```

Decompose a high-level goal into a sequence of sub-tasks.

In a real system, this would call an LLM (Decomposer Agent).
For now, we use a simple rule-based approach for demonstration.

---

## route_subtasks

```python
route_subtasks(self: Any, sub_tasks: list[dict[(str, Any)]])
```

Assign appropriate agents to sub-tasks based on content.

---
