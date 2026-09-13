# health_score API Reference

> **Source**: `src/thegent/governance/health_score.py`

## DimensionScore

Score for a single health dimension with normalization against target.

**Inherits from**: `BaseModel`

---

## HealthBand

Health classification bands derived from composite score.

**Inherits from**: `StrEnum`

---

## HealthScore

Composite health score aggregating all governance dimensions.

**Inherits from**: `BaseModel`

---

## HealthScoreComputer

Computes composite health scores from raw dimension measurements.

Loads dimension definitions (weights, targets, directions) from the
contracts/health-targets.json file and normalizes incoming raw values
into a weighted 0-100 composite score.

### Methods

#### HealthScoreComputer.**init**

```python
__init__(self: Any, health_targets_path: Path)
```

---

#### HealthScoreComputer.compute

```python
compute(self: Any, dimension_values: dict[(str, float)])
```

Compute a health score from raw dimension measurements.

**Parameters**:

- `dimension_values`: mapping of dimension name to raw measured value.
  Dimensions not present in the dict default to their worst case
  (0 for higher_is_better, target\*2 for lower_is_better).

**Returns**: A fully populated HealthScore.

---

#### HealthScoreComputer.compute_with_trend

```python
compute_with_trend(self: Any, dimension_values: dict[(str, float)], previous_score: Any)
```

Compute health score and derive trend from comparison with previous score.

---

---

## compute

```python
compute(self: Any, dimension_values: dict[(str, float)])
```

Compute a health score from raw dimension measurements.

**Parameters**:

- `dimension_values`: mapping of dimension name to raw measured value.
  Dimensions not present in the dict default to their worst case
  (0 for higher_is_better, target\*2 for lower_is_better).

**Returns**: A fully populated HealthScore.

---

## compute_with_trend

```python
compute_with_trend(self: Any, dimension_values: dict[(str, float)], previous_score: Any)
```

Compute health score and derive trend from comparison with previous score.

---

## get_band

```python
get_band(score: float)
```

Return the appropriate HealthBand for a numeric score (0-100).

---
