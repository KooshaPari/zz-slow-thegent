# router_logic API Reference

> **Source**: `src/thegent/agents/crew/router_logic.py`

Pure Python JIT-friendly routing logic for PyPy and non-native runtimes.

---

## PurePythonRouter

JIT-friendly implementation of RouterManager.

### Methods

#### PurePythonRouter.**init**

```python
__init__(self: Any, strategy: RoutingStrategy)
```

---

#### PurePythonRouter.select_agent

```python
select_agent(self: Any, task_description: str, available_agents: list)
```

---

---

## RouteMetrics

---

## RoutingStrategy

**Inherits from**: `StrEnum`

---

## select_agent

```python
select_agent(self: Any, task_description: str, available_agents: list) -> Any
```

---
