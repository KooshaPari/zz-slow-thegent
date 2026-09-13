# orchestration_modes API Reference

> **Source**: `src/thegent/orchestration_modes.py`

Multi-agent orchestration mode catalog (G-KD-04).

Formalizes orchestration patterns per Kush docs D-D and Kagentop MultiAgentOrchestration.
Mode selection policy tied to risk, urgency, and confidence.

---

## ConflictArbitrator

WP-1006: Arbitration rules and quorum policy for multi-agent consensus.

### Methods

#### ConflictArbitrator.**init**

```python
__init__(self: Any, quorum_threshold: float)
```

---

#### ConflictArbitrator.arbitrate

```python
arbitrate(self: Any, results: list[Any])
```

Arbitrate between conflicting results using quorum policy.

---

#### ConflictArbitrator.detect_conflicts

```python
detect_conflicts(self: Any, results: list[Any])
```

Detect conflicts between multiple agent outputs.

---

---

## ModeEntry

Catalog entry for a multi-agent mode.

---

## MultiAgentMode

Canonical multi-agent orchestration modes.

**Inherits from**: `StrEnum`

---

## arbitrate

```python
arbitrate(self: Any, results: list[Any])
```

Arbitrate between conflicting results using quorum policy.

---

## calculate_risk_score

```python
calculate_risk_score(prompt: str, lane: str)
```

WP-2008: Calculate risk score for a task to trigger oversight.

---

## detect_conflicts

```python
detect_conflicts(self: Any, results: list[Any])
```

Detect conflicts between multiple agent outputs.

---

## get_mode

```python
get_mode(mode_id: str)
```

Return mode entry by id, or None if not found.

---

## list_modes

Return all modes for CLI/MCP discovery.

---

## suggest_mode

```python
suggest_mode(risk: str, urgency: str, confidence: float)
```

Suggest mode based on risk, urgency, and confidence (mode selection policy).

---
