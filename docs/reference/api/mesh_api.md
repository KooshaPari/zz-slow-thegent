# mesh API Reference

> **Source**: `src/thegent/discovery/mesh.py`

WP-26001: Global Mesh Networking for Agents.

Extends agent discovery beyond the local network using a global mesh protocol.
Inspired by libp2p and Tailscale-style overlay networking.

---

## AgentMesh

Manages global agent connectivity and peer discovery.

### Methods

#### AgentMesh.**init**

```python
__init__(self: Any, node_id: str, registry_url: str)
```

---

#### AgentMesh.discover_peers

```python
discover_peers(self: Any, capability: Any)
```

Discover peers in the global mesh with specific capabilities.

---

#### AgentMesh.join_mesh

```python
join_mesh(self: Any, public_addr: str)
```

Register the local agent with the global mesh registry.

---

#### AgentMesh.route_to_peer

```python
route_to_peer(self: Any, peer_id: str, payload: dict[(str, Any)])
```

Route a message payload over the mesh overlay network.

---

---

## MeshNode

Metadata for a node in the global agent mesh.

**Inherits from**: `BaseModel`

---

## discover_peers

```python
discover_peers(self: Any, capability: Any)
```

Discover peers in the global mesh with specific capabilities.

---

## join_mesh

```python
join_mesh(self: Any, public_addr: str)
```

Register the local agent with the global mesh registry.

---

## route_to_peer

```python
route_to_peer(self: Any, peer_id: str, payload: dict[(str, Any)])
```

Route a message payload over the mesh overlay network.

---
