# tool_safety API Reference

> **Source**: `src/thegent/verification/tool_safety.py`

WP-25002: Safety Invariants for Tool Composition.

Analyzes chains of tool calls to ensure safety properties are maintained.
Prevents "compositional escalation" where benign tools combined produce unsafe effects.

---

## SafetyViolation

Details of a detected safety invariant violation.

**Inherits from**: `BaseModel`

---

## ToolSafetyChecker

Verifies safety invariants across tool execution chains.

### Methods

#### ToolSafetyChecker.**init**

```python
__init__(self: Any)
```

---

#### ToolSafetyChecker.analyze_chain

```python
analyze_chain(self: Any, tool_chain: list[str])
```

Analyze a sequence of tool calls for safety violations.

---

#### ToolSafetyChecker.check_pre_flight

```python
check_pre_flight(self: Any, proposed_chain: list[str])
```

Pre-flight check for a proposed tool chain.

---

---

## analyze_chain

```python
analyze_chain(self: Any, tool_chain: list[str])
```

Analyze a sequence of tool calls for safety violations.

---

## check_pre_flight

```python
check_pre_flight(self: Any, proposed_chain: list[str])
```

Pre-flight check for a proposed tool chain.

---
