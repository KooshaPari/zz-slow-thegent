# checker API Reference

> **Source**: `src/thegent/agents/checker.py`

Checker Agent (Head LLM) for Lifecycle loops.

---

## CheckerAgent

Head LLM that decides the next action in a loop.

### Methods

#### CheckerAgent.**init**

```python
__init__(self: Any, settings: ThegentSettings, agent_name: str)
```

---

#### CheckerAgent.decide

```python
decide(self: Any, governance_report: dict[(str, Any, str)], todo_spec: str, wbs_status: dict[(str, Any, str)], agent_response: str)
```

Invoke the Checker Agent to make a decision.

---

---

## CheckerDecision

Possible decisions by the Checker Agent.

**Inherits from**: `StrEnum`

---

## CheckerResult

Result of a Checker Agent decision.

**Inherits from**: `BaseModel`

---

## decide

```python
decide(self: Any, governance_report: dict[(str, Any, str)], todo_spec: str, wbs_status: dict[(str, Any, str)], agent_response: str)
```

Invoke the Checker Agent to make a decision.

---
