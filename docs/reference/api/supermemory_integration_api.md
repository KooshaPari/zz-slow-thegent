# supermemory_integration API Reference

> **Source**: `src/thegent/research/supermemory_integration.py`

Supermemory.ai Universal Memory (L3/L4) integration.

---

## SupermemoryIntegration

Integration with Supermemory.ai Universal Memory.

### Methods

#### SupermemoryIntegration.**init**

```python
__init__(self: Any, api_key: Any)
```

Initialize Supermemory integration.

**Parameters**:

- `api_key`: Supermemory API key

---

#### SupermemoryIntegration.retrieve_memory

```python
retrieve_memory(self: Any, query: str, level: str)
```

Retrieve memories from Supermemory.

**Parameters**:

- `query`: Search query
- `level`: Memory level

**Returns**: List of matching memories

---

#### SupermemoryIntegration.store_memory

```python
store_memory(self: Any, content: str, level: str)
```

Store memory in Supermemory.

**Parameters**:

- `content`: Content to store
- `level`: Memory level (L3 or L4)

**Returns**: Storage result

---

---

## retrieve_memory

```python
retrieve_memory(self: Any, query: str, level: str)
```

Retrieve memories from Supermemory.

**Parameters**:

- `query`: Search query
- `level`: Memory level

**Returns**: List of matching memories

---

## store_memory

```python
store_memory(self: Any, content: str, level: str)
```

Store memory in Supermemory.

**Parameters**:

- `content`: Content to store
- `level`: Memory level (L3 or L4)

**Returns**: Storage result

---
