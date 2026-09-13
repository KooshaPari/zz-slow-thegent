# process_registry API Reference

> **Source**: `src/thegent/infra/process_registry.py`

Process registry for tracking and cleaning up subprocesses.

---

## ProcessHandle

Handle for a tracked subprocess.

### Methods

#### ProcessHandle.get_psutil_process

```python
get_psutil_process(self: Any)
```

Get psutil Process object for introspection.

**Returns**: psutil.Process object, or None if process not found.

---

#### ProcessHandle.get_resource_usage

```python
get_resource_usage(self: Any)
```

Get resource usage using psutil.

**Returns**: Dictionary with resource usage information, or None if unavailable.

---

#### ProcessHandle.is_alive

```python
is_alive(self: Any)
```

Check if process is still running.

---

#### ProcessHandle.terminate

```python
terminate(self: Any, timeout: float)
```

Terminate process gracefully.

---

---

## ProcessRegistry

Registry for tracking subprocesses with automatic cleanup.

### Methods

#### ProcessRegistry.**init**

```python
__init__(self: Any)
```

---

#### ProcessRegistry.cleanup_all

```python
cleanup_all(self: Any, timeout: float)
```

Clean up all registered processes.

---

#### ProcessRegistry.cleanup_orphaned

```python
cleanup_orphaned(self: Any)
```

Clean up processes that have died but weren't unregistered.

---

#### ProcessRegistry.cleanup_process_tree

```python
cleanup_process_tree(self: Any, pid: int, timeout: float)
```

Clean up process and all children using psutil.

**Parameters**:

- `pid`: Process ID to clean up.
- `timeout`: Timeout in seconds for process termination.

**Returns**: Number of processes cleaned up.

---

#### ProcessRegistry.get

```python
get(self: Any, pid: int)
```

Get process handle by PID.

---

#### ProcessRegistry.get_stats

```python
get_stats(self: Any)
```

Get registry statistics.

---

#### ProcessRegistry.list_alive

```python
list_alive(self: Any)
```

List all alive processes.

---

#### ProcessRegistry.register

```python
register(self: Any, proc: subprocess.Popen, name: str, cleanup_on_exit: bool, timeout: Any)
```

Register a process for tracking.

---

#### ProcessRegistry.unregister

```python
unregister(self: Any, pid: int)
```

Unregister a process.

---

---

## cleanup_all

```python
cleanup_all(self: Any, timeout: float)
```

Clean up all registered processes.

---

## cleanup_orphaned

```python
cleanup_orphaned(self: Any)
```

Clean up processes that have died but weren't unregistered.

---

## cleanup_process_tree

```python
cleanup_process_tree(self: Any, pid: int, timeout: float)
```

Clean up process and all children using psutil.

**Parameters**:

- `pid`: Process ID to clean up.
- `timeout`: Timeout in seconds for process termination.

**Returns**: Number of processes cleaned up.

---

## get

```python
get(self: Any, pid: int)
```

Get process handle by PID.

---

## get_psutil_process

```python
get_psutil_process(self: Any)
```

Get psutil Process object for introspection.

**Returns**: psutil.Process object, or None if process not found.

---

## get_registry

Get global process registry.

---

## get_resource_usage

```python
get_resource_usage(self: Any)
```

Get resource usage using psutil.

**Returns**: Dictionary with resource usage information, or None if unavailable.

---

## get_stats

```python
get_stats(self: Any)
```

Get registry statistics.

---

## is_alive

```python
is_alive(self: Any)
```

Check if process is still running.

---

## list_alive

```python
list_alive(self: Any)
```

List all alive processes.

---

## register

```python
register(self: Any, proc: subprocess.Popen, name: str, cleanup_on_exit: bool, timeout: Any)
```

Register a process for tracking.

---

## terminate

```python
terminate(self: Any, timeout: float)
```

Terminate process gracefully.

---

## unregister

```python
unregister(self: Any, pid: int)
```

Unregister a process.

---
