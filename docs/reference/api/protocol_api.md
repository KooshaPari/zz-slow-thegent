# protocol API Reference

> **Source**: `src/thegent/discovery/p2p/protocol.py`

WP-13001: P2P Agent Discovery and Peer-to-Peer Orchestration.

---

## P2PDiscovery

Zeroconf-style discovery for agents on the local network.

### Methods

#### P2PDiscovery.**init**

```python
__init__(self: Any, agent_id: str, port: int, capabilities: list[str])
```

---

#### P2PDiscovery.list_peers

```python
list_peers(self: Any)
```

Return list of active peers (seen in last 30s).

---

#### P2PDiscovery.start

```python
start(self: Any)
```

Start discovery and heartbeat threads.

---

#### P2PDiscovery.stop

```python
stop(self: Any)
```

---

---

## PeerAgent

Metadata for a peer agent on the network.

**Inherits from**: `BaseModel`

---

## list_peers

```python
list_peers(self: Any)
```

Return list of active peers (seen in last 30s).

---

## start

```python
start(self: Any)
```

Start discovery and heartbeat threads.

---

## stop

```python
stop(self: Any)
```

---
