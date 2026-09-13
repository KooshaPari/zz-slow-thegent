# runtime_dispatcher API Reference

> **Source**: `src/thegent/infra/runtime_dispatcher.py`

Performance-optimized dispatcher for multi-runtime support.

This module handles the 'splitting' of code into optimal paths for:

1. PyPy (JIT-optimized pure Python)
2. CPython 3.13/3.14 (Native extensions and freethreading support)
3. Compiled backends (Rust, Go, Zig via FFI/Wasm)

---

## MojoDispatcher

High-speed compute offloading to Mojo kernels.

---

## PerformanceModule

Base class for performance-critical modules with multiple implementations.

### Methods

#### PerformanceModule.**init**

```python
__init__(self: Any, name: str)
```

---

#### PerformanceModule.get_impl

```python
get_impl(self: Any)
```

---

#### PerformanceModule.register

```python
register(self: Any, runtime: str, impl: Any)
```

---

---

## WasmDispatcher

Portable performance modules using Extism/Wasm (Zig/Rust).

### Methods

#### WasmDispatcher.call_plugin

```python
call_plugin(plugin_path: str, func_name: str, data: bytes)
```

---

---

## call_plugin

```python
call_plugin(plugin_path: str, func_name: str, data: bytes) -> bytes
```

---

## get_impl

```python
get_impl(self: Any) -> Any
```

---

## get_json_dumps

---

## get_json_loads

---

## get_router

---

## get_runtime_status

---

## get_toml_loads

---

## register

```python
register(self: Any, runtime: str, impl: Any)
```

---
