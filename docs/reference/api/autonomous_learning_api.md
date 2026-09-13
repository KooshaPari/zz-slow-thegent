# autonomous_learning API Reference

> **Source**: `src/thegent/research/autonomous_learning.py`

Autonomous learning surface map.

---

## AutonomousLearningSurface

Surface map for autonomous learning.

### Methods

#### AutonomousLearningSurface.**init**

```python
__init__(self: Any)
```

Initialize autonomous learning surface.

---

#### AutonomousLearningSurface.add_learning_point

```python
add_learning_point(self: Any, context: str, action: str, outcome: Any)
```

Add a learning point.

**Parameters**:

- `context`: Context of learning
- `action`: Action taken
- `outcome`: Outcome observed

---

#### AutonomousLearningSurface.get_recommendation

```python
get_recommendation(self: Any, context: str)
```

Get recommendation based on learning.

**Parameters**:

- `context`: Current context

**Returns**: Recommended action or None

---

---

## add_learning_point

```python
add_learning_point(self: Any, context: str, action: str, outcome: Any)
```

Add a learning point.

**Parameters**:

- `context`: Context of learning
- `action`: Action taken
- `outcome`: Outcome observed

---

## get_recommendation

```python
get_recommendation(self: Any, context: str)
```

Get recommendation based on learning.

**Parameters**:

- `context`: Current context

**Returns**: Recommended action or None

---
