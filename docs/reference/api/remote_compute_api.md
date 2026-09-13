# remote_compute API Reference

> **Source**: `src/thegent/research/remote_compute.py`

Remote compute implementation for thegent run --remote.

---

## RemoteComputeClient

Client for remote compute execution using SSH/rsync.

### Methods

#### RemoteComputeClient.**init**

```python
__init__(self: Any, remote_host: str, remote_port: int)
```

Initialize remote compute client.

**Parameters**:

- `remote_host`: Remote host address (e.g. user@host)
- `remote_port`: SSH port

---

#### RemoteComputeClient.execute_remote

```python
execute_remote(self: Any, command: str, cwd: Any)
```

Execute command on remote host.

**Parameters**:

- `command`: Command to execute
- `cwd`: Working directory on remote host

**Returns**: Execution result

---

#### RemoteComputeClient.transfer_files

```python
transfer_files(self: Any, local_path: Path, remote_path: str)
```

Transfer files to remote host using rsync.

**Parameters**:

- `local_path`: Local file path or directory
- `remote_path`: Remote destination path (e.g. /tmp/thegent-run)

**Returns**: True if successful

---

---

## execute_remote

```python
execute_remote(self: Any, command: str, cwd: Any)
```

Execute command on remote host.

**Parameters**:

- `command`: Command to execute
- `cwd`: Working directory on remote host

**Returns**: Execution result

---

## transfer_files

```python
transfer_files(self: Any, local_path: Path, remote_path: str)
```

Transfer files to remote host using rsync.

**Parameters**:

- `local_path`: Local file path or directory
- `remote_path`: Remote destination path (e.g. /tmp/thegent-run)

**Returns**: True if successful

---
