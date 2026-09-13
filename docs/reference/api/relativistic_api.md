# relativistic API Reference

> **Source**: `src/thegent/discovery/relativistic.py`

WP-43001: Relativistic Clock Sync Protocol.

Simulates clock synchronization across agents located in different gravitational wells or moving
at high relative velocities. Adjusts for time dilation using Lorentz transformations.

---

## RelativisticClockSync

Manages time dilation compensation for interstellar agent coordination.

### Methods

#### RelativisticClockSync.**init**

```python
__init__(self: Any, base_node: RelativisticNode)
```

---

#### RelativisticClockSync.add_peer

```python
add_peer(self: Any, node: RelativisticNode)
```

Register a peer with its physical parameters.

---

#### RelativisticClockSync.calculate_dilation_factor

```python
calculate_dilation_factor(self: Any, peer_id: str)
```

WP-43001: Calculate the time dilation factor (Gamma) for a peer.

---

#### RelativisticClockSync.sync_timestamp

```python
sync_timestamp(self: Any, peer_id: str, remote_ts: float)
```

Convert a remote timestamp to the local base node's time frame.

---

---

## RelativisticNode

A node in the relativistic network.

---

## add_peer

```python
add_peer(self: Any, node: RelativisticNode)
```

Register a peer with its physical parameters.

---

## calculate_dilation_factor

```python
calculate_dilation_factor(self: Any, peer_id: str)
```

WP-43001: Calculate the time dilation factor (Gamma) for a peer.

---

## sync_timestamp

```python
sync_timestamp(self: Any, peer_id: str, remote_ts: float)
```

Convert a remote timestamp to the local base node's time frame.

---
