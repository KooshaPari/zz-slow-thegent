# mojo_bridge API Reference

> **Source**: `src/thegent/infra/mojo_bridge.py`

Mojo Bridge - Python to Mojo Interoperability.

This module provides a bridge for calling compiled Mojo modules from Python.
It supports subprocess-based execution of compiled Mojo binaries with JSON I/O.

Note: Mojo ecosystem is still maturing. This bridge uses subprocess to call
compiled Mojo binaries, with future support for C-ABI integration when stable.

---

## MojoBridge

Bridge for calling Mojo modules from Python.

Supports:

- Subprocess-based execution of compiled Mojo binaries
- Graceful fallback when Mojo is not available
- JSON-based I/O for data exchange
- Async execution for better integration

Future:

- C-ABI integration when Mojo's foreign function interface stabilizes
- Direct memory sharing for high-performance scenarios

### Methods

#### MojoBridge.**init**

```python
__init__(self: Any, mojo_root: Any, cache_root: Any)
```

Initialize the Mojo bridge.

**Parameters**:

- `mojo_root`: Root directory for Mojo modules (default: ~/.thegent/mojo)
- `cache_root`: Root directory for cache (default: /tmp/thegent-mojo-cache)

---

#### MojoBridge.install_instructions

```python
install_instructions(self: Any)
```

Get installation instructions for Mojo.

**Returns**: Installation instructions as a string

---

#### MojoBridge.is_available

```python
is_available(self: Any)
```

Check if Mojo is installed and available.

---

---

## MojoModule

Represents a compiled Mojo module.

---

## MojoNotAvailableError

Raised when Mojo is not installed or not accessible.

**Inherits from**: `Exception`

---

## MojoTask

Task to be executed in Mojo.

---

## get_bridge

Get the global Mojo bridge instance.

---

## install_instructions

```python
install_instructions(self: Any)
```

Get installation instructions for Mojo.

**Returns**: Installation instructions as a string

---

## is_available

```python
is_available(self: Any)
```

Check if Mojo is installed and available.

---
