# memory API Reference

> **Source**: `src/thegent/orchestration/memory.py`

## FrictionScope

**Inherits from**: `StrEnum`

---

## MemoryCategory

**Inherits from**: `StrEnum`

---

## MemoryFragment

---

## MemorySystem

MTSP-17: Dual Issue & Memory Collection System.

Append-only audit log for agent observations, synthesized into formal docs.

### Methods

#### MemorySystem.**init**

```python
__init__(self: Any, project_root: Path)
```

---

#### MemorySystem.get_recent

```python
get_recent(self: Any, limit: int, category: Any)
```

---

#### MemorySystem.record

```python
record(self: Any, content: str, category: MemoryCategory, agent_id: str, scope: Any, metadata: Any)
```

---

#### MemorySystem.synthesize_to_markdown

```python
synthesize_to_markdown(self: Any)
```

Helper to generate a summary for an agent to incorporate.

---

---

## get_recent

```python
get_recent(self: Any, limit: int, category: Any) -> list[MemoryFragment]
```

---

## record

```python
record(self: Any, content: str, category: MemoryCategory, agent_id: str, scope: Any, metadata: Any) -> MemoryFragment
```

---

## synthesize_to_markdown

```python
synthesize_to_markdown(self: Any)
```

Helper to generate a summary for an agent to incorporate.

---
