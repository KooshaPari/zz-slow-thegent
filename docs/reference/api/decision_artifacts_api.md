# decision_artifacts API Reference

> **Source**: `src/thegent/artifacts/decision_artifacts.py`

Decision-Related Artifacts - Agent decisions and branching points.

Provides specialized artifacts for:

- Planning and decision making
- Branching points (conditional choices)
- Strategy selection

---

## BranchingPointArtifact

Artifact for branching points in execution.

Specialized tracking for:

- Conditional branching
- Loop/iteration decisions
- Path selection
- Fallback strategies

**Inherits from**: `BaseArtifact`

### Methods

#### BranchingPointArtifact.create

```python
create(cls: Any, maif: MAIFArtifact, condition: str, condition_result: bool, true_branch: str, false_branch: str)
```

Create branching point artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `condition`: Condition string
- `condition_result`: Condition evaluation result
- `true_branch`: True branch description
- `false_branch`: False branch description
- `**kwargs`: Additional fields

**Returns**: BranchingPointArtifact instance

---

---

## DecisionArtifact

Artifact for agent decision points.

Tracks:

- Decision context and options
- Rationale for choice
- Metrics used in decision
- Outcome and feedback

**Inherits from**: `BaseArtifact`

### Methods

#### DecisionArtifact.create

```python
create(cls: Any, maif: MAIFArtifact, decision_type: DecisionType, options_considered: list[str], selected_option: str)
```

Create decision artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `decision_type`: Type of decision
- `options_considered`: Options evaluated
- `selected_option`: Option that was selected
- `**kwargs`: Additional fields

**Returns**: DecisionArtifact instance

---

---

## DecisionType

Types of decisions.

**Inherits from**: `str, Enum`

---

## create

```python
create(cls: Any, maif: MAIFArtifact, condition: str, condition_result: bool, true_branch: str, false_branch: str)
```

Create branching point artifact.

**Parameters**:

- `maif`: Base MAIF artifact
- `condition`: Condition string
- `condition_result`: Condition evaluation result
- `true_branch`: True branch description
- `false_branch`: False branch description
- `**kwargs`: Additional fields

**Returns**: BranchingPointArtifact instance

---
