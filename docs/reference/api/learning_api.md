# learning API Reference

> **Source**: `src/thegent/hooks/learning.py`

Implement learning-record/should-skip subcommands (learning-based).

---

## LearningSubcommands

Learning-based subcommands.

### Methods

#### LearningSubcommands.**init**

```python
__init__(self: Any, learning_db_path: Any)
```

Initialize learning subcommands.

**Parameters**:

- `learning_db_path`: Learning database path

---

#### LearningSubcommands.record

```python
record(self: Any, pattern: str, skipped: bool, reason: str)
```

Record a learning decision.

**Parameters**:

- `pattern`: Pattern that was evaluated
- `skipped`: Whether it was skipped
- `reason`: Reason for skipping

---

#### LearningSubcommands.should_skip

```python
should_skip(self: Any, pattern: str, threshold: float)
```

Determine if pattern should be skipped.

**Parameters**:

- `pattern`: Pattern to evaluate
- `threshold`: Skip threshold (0.0-1.0)

**Returns**: True if should skip

---

---

## record

```python
record(self: Any, pattern: str, skipped: bool, reason: str)
```

Record a learning decision.

**Parameters**:

- `pattern`: Pattern that was evaluated
- `skipped`: Whether it was skipped
- `reason`: Reason for skipping

---

## should_skip

```python
should_skip(self: Any, pattern: str, threshold: float)
```

Determine if pattern should be skipped.

**Parameters**:

- `pattern`: Pattern to evaluate
- `threshold`: Skip threshold (0.0-1.0)

**Returns**: True if should skip

---
