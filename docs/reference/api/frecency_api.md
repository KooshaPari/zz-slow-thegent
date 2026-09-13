# frecency API Reference

> **Source**: `src/thegent/cache/frecency.py`

Frecency-ranked cache: combines frequency + recency scoring.

Frecency = frequency × recency, where recency decays exponentially over time.

Formula:
score = access_count × e^(-λ × age_seconds)
λ = ln(2) / half_life_seconds

A `half_life_seconds` of 3600 (1 hour) means an item's _recency_ component
halves every hour regardless of access count.

Optionally persists frecency data via a :class:`~thegent.cache.MultiLevelCache`
L2 backend so scores survive process restarts.

FR traceability: FR-CACHE-002 (frecency algorithm for command/model/resource history)

---

## FrecencyCache

Frecency-ranked in-memory cache with optional persistence.

### Methods

#### FrecencyCache.**init**

```python
__init__(self: Any, maxsize: int, half_life_seconds: float, storage: Any)
```

---

#### FrecencyCache.access

```python
access(self: Any, key: str)
```

Record an access for _key_ and return the updated frecency score.

On first access, a new entry is created with `access_count = 1`.
On subsequent accesses, `access_count` is incremented, `last_access`
is refreshed, and the score is recomputed.

If a `storage` backend was provided, the updated entry is persisted.

If the cache is at `maxsize` capacity after inserting a new key, the
lowest-scored entry is evicted to maintain the size bound.

**Parameters**:

- `key`: Identifier for the accessed item.

**Returns**: The new frecency score for _key_.

---

#### FrecencyCache.clear

```python
clear(self: Any)
```

Remove all entries from memory and (if configured) from storage.

---

#### FrecencyCache.evict_lowest

```python
evict_lowest(self: Any, n: int)
```

Evict the _n_ lowest-scored entries and return their keys.

**Parameters**:

- `n`: Number of entries to evict. Clamped to the current entry count.

**Returns**: List of evicted keys.

---

#### FrecencyCache.get_entry

```python
get_entry(self: Any, key: str)
```

Return the :class:`FrecencyEntry` for _key_, or `None` if absent.

The entry's score is recomputed before it is returned.

---

#### FrecencyCache.half_life

```python
half_life(self: Any)
```

Half-life in seconds for the exponential decay component.

---

#### FrecencyCache.maxsize

```python
maxsize(self: Any)
```

Maximum number of entries held in memory.

---

#### FrecencyCache.score

```python
score(self: Any, key: str)
```

Return the current frecency score for _key_ without recording an access.

The score is recomputed using current wall-clock time so it reflects
elapsed decay even without new accesses.

**Returns**: Current score, or `0.0` if the key is unknown.

---

#### FrecencyCache.top_n

```python
top_n(self: Any, n: int)
```

Return the _n_ highest-scoring entries, sorted descending.

Scores are recomputed at call time to account for decay since last
access.

**Parameters**:

- `n`: Number of entries to return. If _n_ exceeds the number of
  tracked entries, all entries are returned.

**Returns**: List of :class:`FrecencyEntry` sorted by score descending.

---

---

## FrecencyEntry

Snapshot of frecency data for a single key.

### Methods

#### FrecencyEntry.age_seconds

```python
age_seconds(self: Any, now: Any)
```

Return elapsed seconds since `last_access`.

---

#### FrecencyEntry.recalculate_score

```python
recalculate_score(self: Any, half_life: float, now: Any)
```

Recompute frecency score using the exponential decay formula.

**Parameters**:

- `half_life`: Half-life in seconds for the recency decay factor.
- `now`: Reference time (defaults to current UTC time).

**Returns**: Updated score. The entry's `score` attribute is mutated in place.

---

---

## FrecencyModelSelector

Prefer recently-and-frequently used models using frecency scoring.

Wraps a :class:`FrecencyCache` and exposes model-selection helpers.

Example usage::

    selector = FrecencyModelSelector()
    selector.record_use("claude-sonnet-4-5")
    selector.record_use("claude-sonnet-4-5")
    selector.record_use("gemini-3-flash")

    best = selector.preferred_model(["claude-sonnet-4-5", "gemini-3-flash"])
    # -&gt; "claude-sonnet-4-5"  (higher frecency)

### Methods

#### FrecencyModelSelector.**init**

```python
__init__(self: Any, maxsize: int, half_life_seconds: float, storage: Any)
```

---

#### FrecencyModelSelector.cache

```python
cache(self: Any)
```

Underlying :class:`FrecencyCache` for advanced access.

---

#### FrecencyModelSelector.preferred_model

```python
preferred_model(self: Any, candidates: list[str])
```

Return the highest-scoring model from _candidates_.

If none of the candidates have been recorded yet (all score 0), the
first candidate is returned as a tiebreaker.

**Returns**: The model identifier with the highest frecency score, or `None`
if _candidates_ is empty.

---

#### FrecencyModelSelector.record_use

```python
record_use(self: Any, model_id: str)
```

Record that _model_id_ was used. Returns the updated score.

---

#### FrecencyModelSelector.score

```python
score(self: Any, model_id: str)
```

Return the current frecency score for _model_id_.

---

#### FrecencyModelSelector.top_models

```python
top_models(self: Any, n: int)
```

Return the _n_ most frecently used model identifiers.

---

---

## access

```python
access(self: Any, key: str)
```

Record an access for _key_ and return the updated frecency score.

On first access, a new entry is created with `access_count = 1`.
On subsequent accesses, `access_count` is incremented, `last_access`
is refreshed, and the score is recomputed.

If a `storage` backend was provided, the updated entry is persisted.

If the cache is at `maxsize` capacity after inserting a new key, the
lowest-scored entry is evicted to maintain the size bound.

**Parameters**:

- `key`: Identifier for the accessed item.

**Returns**: The new frecency score for _key_.

---

## age_seconds

```python
age_seconds(self: Any, now: Any)
```

Return elapsed seconds since `last_access`.

---

## cache

```python
cache(self: Any)
```

Underlying :class:`FrecencyCache` for advanced access.

---

## clear

```python
clear(self: Any)
```

Remove all entries from memory and (if configured) from storage.

---

## evict_lowest

```python
evict_lowest(self: Any, n: int)
```

Evict the _n_ lowest-scored entries and return their keys.

**Parameters**:

- `n`: Number of entries to evict. Clamped to the current entry count.

**Returns**: List of evicted keys.

---

## get_entry

```python
get_entry(self: Any, key: str)
```

Return the :class:`FrecencyEntry` for _key_, or `None` if absent.

The entry's score is recomputed before it is returned.

---

## half_life

```python
half_life(self: Any)
```

Half-life in seconds for the exponential decay component.

---

## maxsize

```python
maxsize(self: Any)
```

Maximum number of entries held in memory.

---

## preferred_model

```python
preferred_model(self: Any, candidates: list[str])
```

Return the highest-scoring model from _candidates_.

If none of the candidates have been recorded yet (all score 0), the
first candidate is returned as a tiebreaker.

**Returns**: The model identifier with the highest frecency score, or `None`
if _candidates_ is empty.

---

## recalculate_score

```python
recalculate_score(self: Any, half_life: float, now: Any)
```

Recompute frecency score using the exponential decay formula.

**Parameters**:

- `half_life`: Half-life in seconds for the recency decay factor.
- `now`: Reference time (defaults to current UTC time).

**Returns**: Updated score. The entry's `score` attribute is mutated in place.

---

## record_use

```python
record_use(self: Any, model_id: str)
```

Record that _model_id_ was used. Returns the updated score.

---

## score

```python
score(self: Any, model_id: str)
```

Return the current frecency score for _model_id_.

---

## top_models

```python
top_models(self: Any, n: int)
```

Return the _n_ most frecently used model identifiers.

---

## top_n

```python
top_n(self: Any, n: int)
```

Return the _n_ highest-scoring entries, sorted descending.

Scores are recomputed at call time to account for decay since last
access.

**Parameters**:

- `n`: Number of entries to return. If _n_ exceeds the number of
  tracked entries, all entries are returned.

**Returns**: List of :class:`FrecencyEntry` sorted by score descending.

---
