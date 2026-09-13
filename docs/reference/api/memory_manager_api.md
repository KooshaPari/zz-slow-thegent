# memory_manager API Reference

> **Source**: `src/thegent/memory/memory_manager.py`

MemoryManager: wraps SupermemoryClient for agent lifecycle integration (L3 layer).

Provides a safe, optional facade over SupermemoryClient. When
THGENT_SUPERMEMORY_API_KEY is absent the manager operates in no-op mode:
every method returns an empty result without raising.

# @trace FR-MEM-002

---

## MemoryManager

Facade over SupermemoryClient for agent lifecycle integration.

Instantiate once per process; it is safe to share across coroutines.
All public methods are `async` and silently no-op when the API key
is not configured.

Example::

    mgr = MemoryManager()
    context = await mgr.load_context("claude")
    # ... run agent ...
    await mgr.save_discovery("claude", "Discovered that X causes Y")

### Methods

#### MemoryManager.**init**

```python
__init__(self: Any, api_key: Any, base_url: Any)
```

---

#### MemoryManager.enabled

```python
enabled(self: Any)
```

True when the Supermemory API key is configured.

---

---

## enabled

```python
enabled(self: Any)
```

True when the Supermemory API key is configured.

---
