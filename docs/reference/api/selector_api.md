# selector API Reference

> **Source**: `src/thegent/planning/selector.py`

WP-14001: Cost-aware objective selector for multi-objective optimization.

---

## ObjectiveSelector

Optimizes model selection across multiple objectives (WP-14001).

### Methods

#### ObjectiveSelector.**init**

```python
__init__(self: Any, weights: Any)
```

---

#### ObjectiveSelector.select

```python
select(self: Any, models: list[dict[(str, Any)]], profile: Any)
```

Select the best model from a list of model dictionaries.

---

#### ObjectiveSelector.select_best_model

```python
select_best_model(self: Any, candidate_ids: list[str])
```

Score and select the best model from the candidates.

---

---

## ObjectiveWeights

### Methods

#### ObjectiveWeights.validate

```python
validate(self: Any)
```

---

---

## get_objective_profile

```python
get_objective_profile(profile_name: str)
```

Return a predefined objective profile.

---

## score_model

```python
score_model(m: Any)
```

---

## select

```python
select(self: Any, models: list[dict[(str, Any)]], profile: Any)
```

Select the best model from a list of model dictionaries.

---

## select_best_model

```python
select_best_model(self: Any, candidate_ids: list[str])
```

Score and select the best model from the candidates.

---

## validate

```python
validate(self: Any) -> None
```

---
