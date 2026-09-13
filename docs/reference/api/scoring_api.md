# scoring API Reference

> **Source**: `src/thegent/routing/scoring.py`

WP-Y8-rel: Provider scoring with learning.

---

## ProviderScorer

Scores providers based on historical performance and learning.

### Methods

#### ProviderScorer.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### ProviderScorer.get_score

```python
get_score(self: Any, provider_id: str)
```

Get the current score for a provider (0.0 to 1.0).

---

#### ProviderScorer.update_score

```python
update_score(self: Any, provider_id: str, latency_s: float, success: bool)
```

Update provider score based on a new result.

---

---

## get_score

```python
get_score(self: Any, provider_id: str)
```

Get the current score for a provider (0.0 to 1.0).

---

## update_score

```python
update_score(self: Any, provider_id: str, latency_s: float, success: bool)
```

Update provider score based on a new result.

---
