# discovery_native API Reference

> **Source**: `src/thegent/native/discovery_native.py`

BKM-08: Python wrapper for the thegent-discovery binary.

DiscoveryClient calls the `thegent-discovery` binary (built from
`crates/thegent-discovery/src/main.rs`) via a single subprocess and returns
structured Python objects. When the binary is not found on PATH it falls back
to individual subprocess / psutil calls so the module is always usable.

Usage::

    from thegent.native.discovery_native import DiscoveryClient

    client = DiscoveryClient()
    sessions  = client.sessions()          # list[dict]
    tools     = client.tools()             # list[dict]
    processes = client.processes()         # list[dict]
    all_data  = client.all()               # dict with keys sessions/tools/processes
    client.is_native                       # True if binary is available

FR-trace: BKM-08 (PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)

---

## DiscoveryClient

Thin Python wrapper around the `thegent-discovery` binary (BKM-08).

Falls back to individual subprocess / psutil calls when the binary is not
available so that callers always get usable results.

### Methods

#### DiscoveryClient.**init**

```python
__init__(self: Any)
```

---

#### DiscoveryClient.all

```python
all(self: Any, pattern: Any)
```

Return combined discovery: sessions + tools + processes.

**Parameters**:

- `pattern`: Optional process filter regex.

**Returns**: Dict with keys: `sessions`, `tools`, `processes`.

---

#### DiscoveryClient.processes

```python
processes(self: Any, pattern: Any)
```

Return matching processes as a list of dicts.

**Parameters**:

- `pattern`: Optional regex pattern to filter by process name or
  command line. Defaults to the built-in agent pattern.

**Returns**: List of process dicts with keys: `pid`, `ppid`, `name`,
`cmd`, `memory_kb`, `cpu_usage`, `run_time_s`.

---

#### DiscoveryClient.sessions

```python
sessions(self: Any)
```

Return tmux/screen sessions as a list of dicts.

**Returns**: List of session dicts with keys: `session_name`, `windows`,
`created`, `attached`, `source`.

---

#### DiscoveryClient.tools

```python
tools(self: Any)
```

Return tool availability as a list of dicts.

**Returns**: List of dicts with keys: `tool`, `available`, `path`.

---

#### DiscoveryClient.tools_map

```python
tools_map(self: Any)
```

Convenience: return `{"tool": available}` dict.

**Returns**: Mapping of tool name to availability boolean.

---

---

## all

```python
all(self: Any, pattern: Any)
```

Return combined discovery: sessions + tools + processes.

**Parameters**:

- `pattern`: Optional process filter regex.

**Returns**: Dict with keys: `sessions`, `tools`, `processes`.

---

## processes

```python
processes(self: Any, pattern: Any)
```

Return matching processes as a list of dicts.

**Parameters**:

- `pattern`: Optional regex pattern to filter by process name or
  command line. Defaults to the built-in agent pattern.

**Returns**: List of process dicts with keys: `pid`, `ppid`, `name`,
`cmd`, `memory_kb`, `cpu_usage`, `run_time_s`.

---

## sessions

```python
sessions(self: Any)
```

Return tmux/screen sessions as a list of dicts.

**Returns**: List of session dicts with keys: `session_name`, `windows`,
`created`, `attached`, `source`.

---

## tools

```python
tools(self: Any)
```

Return tool availability as a list of dicts.

**Returns**: List of dicts with keys: `tool`, `available`, `path`.

---

## tools_map

```python
tools_map(self: Any)
```

Convenience: return `{"tool": available}` dict.

**Returns**: Mapping of tool name to availability boolean.

---
