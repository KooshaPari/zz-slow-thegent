# supermemory_client API Reference

> **Source**: `src/thegent/memory/supermemory_client.py`

Supermemory.ai client for persistent agent memory (L3 layer).

Provides async CRUD operations and semantic search over the Supermemory REST API.
Uses httpx for HTTP, tenacity for retry on transient errors (429/503).

Config:
THGENT_SUPERMEMORY_API_KEY - Required. API key (x-sm-api-key header).
THGENT_SUPERMEMORY_BASE_URL - Optional. Defaults to https://api.supermemory.ai/v3.

---

## MemoryEntry

A single memory entry returned by the Supermemory API.

### Methods

#### MemoryEntry.from_api_dict

```python
from_api_dict(cls: Any, data: dict[(str, Any)])
```

Construct a MemoryEntry from a raw API response dict.

---

---

## SupermemoryAPIError

Raised on unrecoverable API errors (4xx excluding 429, 5xx excluding 503).

**Inherits from**: `Exception`

### Methods

#### SupermemoryAPIError.**init**

```python
__init__(self: Any, status_code: int, message: str)
```

---

---

## SupermemoryClient

Async client for the Supermemory.ai REST API.

Raises SupermemoryConfigError immediately on construction if the API key
is not provided (either via parameter or THGENT_SUPERMEMORY_API_KEY env var).

Uses httpx.AsyncClient and tenacity for retry on 429/503.

Example::

    client = SupermemoryClient(api_key="sm_...")
    memory_id = await client.add("Agent found X while processing Y", tags=["discovery"])
    results = await client.search("X processing", limit=5)
    await client.delete(memory_id)

### Methods

#### SupermemoryClient.**init**

```python
__init__(self: Any, api_key: Any, base_url: Any)
```

Initialise the client.

**Parameters**:

- `api_key`: Supermemory API key. Falls back to THGENT_SUPERMEMORY_API_KEY.
- `base_url`: Override the API base URL. Falls back to THGENT_SUPERMEMORY_BASE_URL
  or https://api.supermemory.ai/v3.

---

---

## SupermemoryConfigError

Raised when SupermemoryClient is misconfigured (e.g. missing API key).

**Inherits from**: `Exception`

---

## from_api_dict

```python
from_api_dict(cls: Any, data: dict[(str, Any)])
```

Construct a MemoryEntry from a raw API response dict.

---
