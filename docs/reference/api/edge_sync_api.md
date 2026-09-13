# edge_sync API Reference

> **Source**: `src/thegent/discovery/edge_sync.py`

WP-40003: Edge-Agent Low-Power Synchronization.

Enables agents running on constrained edge devices (IoT, Mobile) to synchronize state
using delta-compression and adaptive polling to conserve energy.

---

## EdgeSyncController

Manages low-power synchronization between edge agents and the mesh.

### Methods

#### EdgeSyncController.**init**

```python
__init__(self: Any, device_id: str)
```

---

#### EdgeSyncController.apply_remote_delta

```python
apply_remote_delta(self: Any, compressed_delta: bytes)
```

Apply a received delta to the local base state.

---

#### EdgeSyncController.compute_delta

```python
compute_delta(self: Any, current_state: dict[(str, Any)])
```

WP-40003: Generate a compressed delta between base and current state.

---

#### EdgeSyncController.get_adaptive_polling_interval

```python
get_adaptive_polling_interval(self: Any, battery_level: float)
```

Adjust sync frequency based on battery (0.0 - 1.0).

---

---

## apply_remote_delta

```python
apply_remote_delta(self: Any, compressed_delta: bytes)
```

Apply a received delta to the local base state.

---

## compute_delta

```python
compute_delta(self: Any, current_state: dict[(str, Any)])
```

WP-40003: Generate a compressed delta between base and current state.

---

## get_adaptive_polling_interval

```python
get_adaptive_polling_interval(self: Any, battery_level: float)
```

Adjust sync frequency based on battery (0.0 - 1.0).

---
