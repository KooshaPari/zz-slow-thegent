# refactoring API Reference

> **Source**: `src/thegent/agents/refactoring.py`

WP-37002: Recursive Cognitive Refactoring.

Allows agents to analyze their own reasoning chains and refactor their logic for better performance.

---

## CognitiveRefactorer

Analyzes and optimizes agent 'thought patterns' or prompt hierarchies.

### Methods

#### CognitiveRefactorer.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### CognitiveRefactorer.analyze_reasoning_efficiency

```python
analyze_reasoning_efficiency(self: Any, run_history: list[dict[(str, Any)]])
```

Analyze how efficiently the agent reaches a solution.

---

#### CognitiveRefactorer.apply_refactor

```python
apply_refactor(self: Any, refactor_plan: str)
```

Update the agent's internal reasoning template.

---

#### CognitiveRefactorer.propose_refactor

```python
propose_refactor(self: Any, efficiency_report: dict[(str, float)])
```

WP-37002: Generate a refactored 'cognitive template' (refined prompt instructions).

---

---

## analyze_reasoning_efficiency

```python
analyze_reasoning_efficiency(self: Any, run_history: list[dict[(str, Any)]])
```

Analyze how efficiently the agent reaches a solution.

---

## apply_refactor

```python
apply_refactor(self: Any, refactor_plan: str)
```

Update the agent's internal reasoning template.

---

## propose_refactor

```python
propose_refactor(self: Any, efficiency_report: dict[(str, float)])
```

WP-37002: Generate a refactored 'cognitive template' (refined prompt instructions).

---
