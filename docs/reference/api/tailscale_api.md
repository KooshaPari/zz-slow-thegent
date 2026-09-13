# tailscale API Reference

> **Source**: `src/thegent/compute/tailscale.py`

Tailscale node management for compute offload.

---

## TailscaleConfig

Configuration for Tailscale integration.

Reads from environment variables prefixed with THGENT*TAILSCALE*.

**Inherits from**: `BaseSettings`

---

## TailscaleError

Raised when a Tailscale operation fails.

**Inherits from**: `Exception`

---

## TailscaleManager

Manages Tailscale nodes for compute offload.

Uses the `tailscale` CLI binary to discover and interact with nodes
on the Tailscale network. Falls back to empty results when the binary
is not installed rather than raising unconditionally, so callers can
check :meth:`is_available` before proceeding.

### Methods

#### TailscaleManager.**init**

```python
__init__(self: Any, config: Any)
```

Initialise the manager.

**Parameters**:

- `config`: Optional :class:`TailscaleConfig`. If _None_, one is
  constructed from the environment.

---

#### TailscaleManager.get_online_nodes

```python
get_online_nodes(self: Any)
```

Return only nodes that are currently online.

**Returns**: Filtered list of :class:`TailscaleNode` objects with
:attr:`TailscaleNode.is_online` set to _True_.

---

#### TailscaleManager.is_available

```python
is_available(self: Any)
```

Return _True_ if the `tailscale` binary is on `PATH`.

**Returns**: Whether the Tailscale CLI can be found.

---

#### TailscaleManager.list_nodes

```python
list_nodes(self: Any)
```

Return all nodes reported by `tailscale status --json`.

If the Tailscale binary is not installed the method logs a warning
and returns an empty list rather than raising.

**Returns**: Parsed list of :class:`TailscaleNode` objects.

---

#### TailscaleManager.ping_node

```python
ping_node(self: Any, hostname: str)
```

Ping _hostname_ via `tailscale ping`.

**Parameters**:

- `hostname`: The Tailscale hostname or IP to ping.

**Returns**: _True_ if the ping succeeds, _False_ otherwise.

---

---

## TailscaleNode

Represents a node on the Tailscale network.

---

## get_online_nodes

```python
get_online_nodes(self: Any)
```

Return only nodes that are currently online.

**Returns**: Filtered list of :class:`TailscaleNode` objects with
:attr:`TailscaleNode.is_online` set to _True_.

---

## is_available

```python
is_available(self: Any)
```

Return _True_ if the `tailscale` binary is on `PATH`.

**Returns**: Whether the Tailscale CLI can be found.

---

## list_nodes

```python
list_nodes(self: Any)
```

Return all nodes reported by `tailscale status --json`.

If the Tailscale binary is not installed the method logs a warning
and returns an empty list rather than raising.

**Returns**: Parsed list of :class:`TailscaleNode` objects.

**Raises**:

- `TailscaleError`: If the binary is installed but the command fails
  or its output cannot be parsed.

---

## ping_node

```python
ping_node(self: Any, hostname: str)
```

Ping _hostname_ via `tailscale ping`.

**Parameters**:

- `hostname`: The Tailscale hostname or IP to ping.

**Returns**: _True_ if the ping succeeds, _False_ otherwise.

**Raises**:

- `TailscaleError`: If the binary is not available.

---
