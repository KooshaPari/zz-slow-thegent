# garden API Reference

> **Source**: `src/thegent/memory/garden.py`

WP-11002: Gardener Synthesis Phase 2 - Memory Garden implementation.

---

## GardenCluster

---

## MemoryGarden

Manages clusters of idea seeds for long-term memory synthesis.

### Methods

#### MemoryGarden.**init**

```python
__init__(self: Any, garden_path: Path)
```

---

#### MemoryGarden.add_to_cluster

```python
add_to_cluster(self: Any, cluster_id: str, seed: Seed)
```

---

#### MemoryGarden.find_best_cluster

```python
find_best_cluster(self: Any, seed: Seed)
```

Find the best cluster for a seed based on keyword matching.

---

#### MemoryGarden.save

```python
save(self: Any)
```

---

#### MemoryGarden.synthesize

```python
synthesize(self: Any)
```

Generate a markdown report of the current garden state.

---

---

## add_to_cluster

```python
add_to_cluster(self: Any, cluster_id: str, seed: Seed) -> None
```

---

## find_best_cluster

```python
find_best_cluster(self: Any, seed: Seed)
```

Find the best cluster for a seed based on keyword matching.

---

## save

```python
save(self: Any) -> None
```

---

## synthesize

```python
synthesize(self: Any)
```

Generate a markdown report of the current garden state.

---
