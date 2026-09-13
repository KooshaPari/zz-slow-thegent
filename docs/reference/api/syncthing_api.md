# syncthing API Reference

> **Source**: `src/thegent/compute/syncthing.py`

Syncthing workspace synchronization for thegent compute offloading.

---

## SyncthingConfig

Configuration for the Syncthing API client.

Reads from environment variables:
THGENT_SYNCTHING_API_KEY — Syncthing GUI/API key
THGENT_SYNCTHING_URL — Base URL of the Syncthing REST API

**Inherits from**: `BaseSettings`

---

## SyncthingDevice

Represents a Syncthing peer device.

---

## SyncthingError

Raised when a Syncthing API operation fails.

**Inherits from**: `Exception`

---

## SyncthingFolder

Represents a Syncthing shared folder.

---

## SyncthingManager

Manages Syncthing workspace synchronisation via its REST API.

All network calls use `httpx.AsyncClient`. The client is created
lazily and reused across calls. Call :meth:`close` (or use the
async context manager) to release the underlying connection pool.

### Methods

#### SyncthingManager.**init**

```python
__init__(self: Any, config: Any)
```

---

---
