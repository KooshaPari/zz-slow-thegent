# cost_sensitivity API Reference

> **Source**: `src/thegent/phases/cost_sensitivity.py`

Phase13: Cost sensitivity experiment (baseline + A/B).

---

## CostSensitivityExperiment

Cost sensitivity experiment framework.

### Methods

#### CostSensitivityExperiment.**init**

```python
__init__(self: Any)
```

Initialize cost sensitivity experiment.

---

#### CostSensitivityExperiment.analyze

```python
analyze(self: Any)
```

Analyze cost sensitivity.

**Returns**: Analysis results

---

#### CostSensitivityExperiment.record_baseline

```python
record_baseline(self: Any, cost: float)
```

Record baseline cost.

**Parameters**:

- `cost`: Cost value

---

#### CostSensitivityExperiment.record_variant

```python
record_variant(self: Any, cost: float)
```

Record variant cost.

**Parameters**:

- `cost`: Cost value

---

---

## analyze

```python
analyze(self: Any)
```

Analyze cost sensitivity.

**Returns**: Analysis results

---

## record_baseline

```python
record_baseline(self: Any, cost: float)
```

Record baseline cost.

**Parameters**:

- `cost`: Cost value

---

## record_variant

```python
record_variant(self: Any, cost: float)
```

Record variant cost.

**Parameters**:

- `cost`: Cost value

---
