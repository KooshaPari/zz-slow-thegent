# remote_executor API Reference

> **Source**: `src/thegent/compute/remote_executor.py`

Remote execution of agent tasks on Tailscale nodes via SSH.

---

## RemoteExecutor

Executes tasks on remote Tailscale nodes via SSH.

Node selection uses a simple round-robin strategy when the caller does
not specify an explicit target node on the :class:`RemoteTask`.

Environment variable configuration (read at construction time):

- `THGENT_REMOTE_NODES` — comma-separated list of hostnames/IPs.
- `THGENT_REMOTE_SSH_USER` — SSH login user (optional; defaults to
  the current OS user when omitted).

### Methods

#### RemoteExecutor.**init**

```python
__init__(self: Any, nodes: Any, ssh_user: Any)
```

---

#### RemoteExecutor.available_nodes

```python
available_nodes(self: Any)
```

Return the subset of configured nodes reachable via `ping`.

Each node is tested with a single ICMP packet (`ping -c 1 -W 2`).
Unreachable nodes are logged at DEBUG level and omitted from the
result.

**Returns**: List of reachable node addresses in the order they were
originally configured.

---

#### RemoteExecutor.execute

```python
execute(self: Any, task: RemoteTask)
```

Execute _task_ on a remote node via SSH.

**Parameters**:

- `task`: The task specification to run.

**Returns**: A :class:`RemoteResult` with the outcome.

---

---

## RemoteExecutorError

Raised when a remote execution operation fails.

**Inherits from**: `Exception`

---

## RemoteResult

The outcome of a remote task execution.

---

## RemoteTask

Describes a task to be executed on a remote node.

---

## available_nodes

```python
available_nodes(self: Any)
```

Return the subset of configured nodes reachable via `ping`.

Each node is tested with a single ICMP packet (`ping -c 1 -W 2`).
Unreachable nodes are logged at DEBUG level and omitted from the
result.

**Returns**: List of reachable node addresses in the order they were
originally configured.

---

## execute

```python
execute(self: Any, task: RemoteTask)
```

Execute _task_ on a remote node via SSH.

**Parameters**:

- `task`: The task specification to run.

**Returns**: A :class:`RemoteResult` with the outcome.

**Raises**:

- `RemoteExecutorError`: If no nodes are configured, node selection
  fails, or the SSH process cannot be spawned.

---
