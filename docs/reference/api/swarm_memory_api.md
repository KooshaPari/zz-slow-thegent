# swarm_memory API Reference

> **Source**: `src/thegent/orchestration/swarm_memory.py`

WP-24003: Swarm Memory Consolidation.

Consolidates distributed agent memories into a unified swarm knowledge base.
Uses cross-agent memory synthesis to eliminate redundancy and conflicts.

---

## SwarmMemoryConsolidator

Synthesizes memory artifacts from multiple agents into a unified view.

### Methods

#### SwarmMemoryConsolidator.**init**

```python
__init__(self: Any, swarm_id: str, local_memory: DualMemory)
```

---

#### SwarmMemoryConsolidator.consolidate

```python
consolidate(self: Any, peer_memories: list[dict[(str, Any)]])
```

Consolidate peer memories with local memory.

---

---

## consolidate

```python
consolidate(self: Any, peer_memories: list[dict[(str, Any)]])
```

Consolidate peer memories with local memory.

---
