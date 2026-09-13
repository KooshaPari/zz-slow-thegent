# health_scorer API Reference

> **Source**: `src/thegent/governance/health_scorer.py`

Health score calculator for thegent project governance.

---

## DimensionScore

Individual dimension score.

**Inherits from**: `TypedDict`

---

## HealthReport

Overall health report.

**Inherits from**: `TypedDict`

---

## HealthScorer

Calculates project health based on defined targets.

### Methods

#### HealthScorer.**init**

```python
__init__(self: Any, targets_file: Any)
```

Load health targets configuration.

**Parameters**:

- `targets_file`: Path to health-targets.json

---

#### HealthScorer.calculate_overall

```python
calculate_overall(self: Any, scores: list[DimensionScore])
```

Calculate weighted overall score.

**Parameters**:

- `scores`: List of dimension scores

**Returns**: Overall weighted score (0-100)

---

#### HealthScorer.dimension_status

```python
dimension_status(self: Any, score: float)
```

Get status label for a score.

**Parameters**:

- `score`: Score 0-100

**Returns**: Status label (excellent, healthy, warning, critical)

---

#### HealthScorer.generate_report

```python
generate_report(self: Any, measurements: dict[(str, float)])
```

Generate a full health report.

**Parameters**:

- `measurements`: Dict mapping dimension keys to actual values

**Returns**: Complete health report

---

#### HealthScorer.normalize_score

```python
normalize_score(self: Any, actual: float, target: float, direction: str)
```

Normalize a score to 0-100 scale.

**Parameters**:

- `actual`: Actual measured value
- `target`: Target value
- `direction`: "higher_is_better" or "lower_is_better"

**Returns**: Normalized score (0-100)

---

#### HealthScorer.score_dimension

```python
score_dimension(self: Any, dimension_key: str, actual: float)
```

Score a single dimension.

**Parameters**:

- `dimension_key`: Dimension ID (e.g., "test_coverage")
- `actual`: Actual measured value

**Returns**: Dimension score details

---

---

## calculate_overall

```python
calculate_overall(self: Any, scores: list[DimensionScore])
```

Calculate weighted overall score.

**Parameters**:

- `scores`: List of dimension scores

**Returns**: Overall weighted score (0-100)

---

## dimension_status

```python
dimension_status(self: Any, score: float)
```

Get status label for a score.

**Parameters**:

- `score`: Score 0-100

**Returns**: Status label (excellent, healthy, warning, critical)

---

## generate_report

```python
generate_report(self: Any, measurements: dict[(str, float)])
```

Generate a full health report.

**Parameters**:

- `measurements`: Dict mapping dimension keys to actual values

**Returns**: Complete health report

---

## normalize_score

```python
normalize_score(self: Any, actual: float, target: float, direction: str)
```

Normalize a score to 0-100 scale.

**Parameters**:

- `actual`: Actual measured value
- `target`: Target value
- `direction`: "higher_is_better" or "lower_is_better"

**Returns**: Normalized score (0-100)

---

## score_dimension

```python
score_dimension(self: Any, dimension_key: str, actual: float)
```

Score a single dimension.

**Parameters**:

- `dimension_key`: Dimension ID (e.g., "test_coverage")
- `actual`: Actual measured value

**Returns**: Dimension score details

---
