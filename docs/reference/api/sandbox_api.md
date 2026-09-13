# sandbox API Reference

> **Source**: `src/thegent/infra/sandbox.py`

WP-31002: Containerized Agent Sandboxes (Wasm).

Provides lightweight, secure execution environments for untrusted agent code using WebAssembly.
Ensures near-native performance with strict memory and capability isolation.

---

## SandboxConfig

Configuration for a Wasm sandbox.

**Inherits from**: `BaseModel`

---

## WasmSandbox

Manages secure execution of agent code in a Wasm environment using Extism.

### Methods

#### WasmSandbox.**init**

```python
__init__(self: Any, sandbox_id: str, config: Optional[SandboxConfig])
```

---

#### WasmSandbox.run_function

```python
run_function(self: Any, wasm_binary_path: str, function_name: str, input_data: Any)
```

Execute a function inside the Wasm sandbox using Extism.

---

#### WasmSandbox.shutdown

```python
shutdown(self: Any)
```

Tear down the sandbox and release resources.

---

---

## run_function

```python
run_function(self: Any, wasm_binary_path: str, function_name: str, input_data: Any)
```

Execute a function inside the Wasm sandbox using Extism.

---

## shutdown

```python
shutdown(self: Any)
```

Tear down the sandbox and release resources.

---
