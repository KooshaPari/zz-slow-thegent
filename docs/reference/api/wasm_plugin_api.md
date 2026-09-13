# wasm_plugin API Reference

> **Source**: `src/thegent/infra/wasm_plugin.py`

WP-31002: Wasm Plugin System using Extism.

Provides a comprehensive Wasm-based plugin system for sandboxed tool execution.
This module integrates with Extism to enable secure, isolated execution of
Zig-compiled Wasm tools.

Key features:

- Extism Python bindings integration
- Plugin loading and execution
- Resource limits (memory, CPU time)
- Graceful fallback if Wasm not available

---

## ExtismPlugin

Extism-based Wasm plugin implementation.

**Inherits from**: `WasmPlugin`

**Method Resolution Order**: `ExtismPlugin -> WasmPlugin`

### Methods

#### ExtismPlugin.**init**

```python
__init__(self: Any, plugin_path: Path, metadata: WasmPluginMetadata, limits: Any, config: Any, allow_wasi: bool)
```

---

#### ExtismPlugin.execute

```python
execute(self: Any, input_data: Any)
```

Execute the plugin with the given input.

---

#### ExtismPlugin.load

```python
load(self: Any)
```

Load the plugin into the Extism runtime.

---

#### ExtismPlugin.unload

```python
unload(self: Any)
```

Unload the plugin and release resources.

---

---

## ExtismRuntime

Extism runtime wrapper with resource management.

### Methods

#### ExtismRuntime.**init**

```python
__init__(self: Any)
```

---

#### ExtismRuntime.error_message

```python
error_message(self: Any)
```

Get the error message if status is ERROR.

---

#### ExtismRuntime.get_extism

```python
get_extism(self: Any)
```

Get the Extism module.

**Returns**: The Extism module if available, None otherwise.

---

#### ExtismRuntime.initialize

```python
initialize(self: Any)
```

Initialize the Extism runtime.

**Returns**: True if initialization was successful, False otherwise.

---

#### ExtismRuntime.is_available

```python
is_available(self: Any)
```

Check if Extism is available.

---

#### ExtismRuntime.status

```python
status(self: Any)
```

Get the current runtime status.

---

---

## PluginStatus

Status of a loaded plugin.

**Inherits from**: `Enum`

---

## ResourceLimits

Resource limits for Wasm execution.

These limits help ensure that Wasm plugins cannot consume
excessive resources or run indefinitely.

---

## WasmCapability

Capabilities that can be granted to a Wasm plugin.

**Inherits from**: `Enum`

---

## WasmExecutionResult

Result of Wasm plugin execution.

---

## WasmPlugin

Abstract base class for Wasm plugins.

**Inherits from**: `ABC`

### Methods

#### WasmPlugin.**init**

```python
__init__(self: Any, plugin_path: Path, metadata: WasmPluginMetadata, limits: Any, config: Any)
```

---

#### WasmPlugin.execute

```python
execute(self: Any, input_data: Any)
```

Execute the plugin with the given input.

**Parameters**:

- `input_data`: Input data to pass to the plugin.

**Returns**: Execution result containing output or error.

---

#### WasmPlugin.load

```python
load(self: Any)
```

Load the plugin into the runtime.

**Returns**: True if loading was successful, False otherwise.

---

#### WasmPlugin.status

```python
status(self: Any)
```

Get the current plugin status.

---

#### WasmPlugin.unload

```python
unload(self: Any)
```

Unload the plugin and release resources.

**Returns**: True if unloading was successful, False otherwise.

---

---

## WasmPluginManager

Manager for Wasm plugins with lifecycle management.

### Methods

#### WasmPluginManager.**init**

```python
__init__(self: Any, plugin_dir: Any)
```

---

#### WasmPluginManager.clear

```python
clear(self: Any)
```

Remove and unload all plugins.

---

#### WasmPluginManager.execute_plugin

```python
execute_plugin(self: Any, name: str, input_data: Any)
```

Execute a registered plugin.

**Parameters**:

- `name`: The plugin name.
- `input_data`: Input data to pass to the plugin.

**Returns**: Execution result if successful, None if plugin not found.

---

#### WasmPluginManager.get_plugin

```python
get_plugin(self: Any, name: str)
```

Get a registered plugin by name.

**Parameters**:

- `name`: The plugin name.

**Returns**: The plugin if found, None otherwise.

---

#### WasmPluginManager.initialize

```python
initialize(self: Any)
```

Initialize the Wasm runtime.

---

#### WasmPluginManager.is_available

```python
is_available(self: Any)
```

Check if the Wasm runtime is available.

---

#### WasmPluginManager.list_plugins

```python
list_plugins(self: Any)
```

List all registered plugin names.

**Returns**: List of plugin names.

---

#### WasmPluginManager.load_plugin

```python
load_plugin(self: Any, name: str)
```

Load a registered plugin.

**Parameters**:

- `name`: The plugin name.

**Returns**: True if loading was successful, False otherwise.

---

#### WasmPluginManager.register_plugin

```python
register_plugin(self: Any, plugin: WasmPlugin)
```

Register a plugin with the manager.

**Parameters**:

- `plugin`: The plugin to register.

**Returns**: True if registration was successful, False otherwise.

---

#### WasmPluginManager.remove_plugin

```python
remove_plugin(self: Any, name: str)
```

Remove and unload a plugin.

**Parameters**:

- `name`: The plugin name.

**Returns**: True if removal was successful, False otherwise.

---

#### WasmPluginManager.unload_plugin

```python
unload_plugin(self: Any, name: str)
```

Unload a registered plugin.

**Parameters**:

- `name`: The plugin name.

**Returns**: True if unloading was successful, False otherwise.

---

---

## WasmPluginMetadata

Metadata for a Wasm plugin.

---

## WasmRuntimeStatus

Status of the Wasm runtime.

**Inherits from**: `Enum`

---

## clear

```python
clear(self: Any)
```

Remove and unload all plugins.

---

## create_plugin_from_manifest

```python
create_plugin_from_manifest(manifest_path: Path)
```

Create a plugin from a manifest file.

**Parameters**:

- `manifest_path`: Path to the plugin manifest JSON file.

**Returns**: An ExtismPlugin instance if successful, None otherwise.

---

## error_message

```python
error_message(self: Any)
```

Get the error message if status is ERROR.

---

## execute

```python
execute(self: Any, input_data: Any)
```

Execute the plugin with the given input.

---

## execute_plugin

```python
execute_plugin(self: Any, name: str, input_data: Any)
```

Execute a registered plugin.

**Parameters**:

- `name`: The plugin name.
- `input_data`: Input data to pass to the plugin.

**Returns**: Execution result if successful, None if plugin not found.

---

## get_extism

```python
get_extism(self: Any)
```

Get the Extism module.

**Returns**: The Extism module if available, None otherwise.

---

## get_plugin

```python
get_plugin(self: Any, name: str)
```

Get a registered plugin by name.

**Parameters**:

- `name`: The plugin name.

**Returns**: The plugin if found, None otherwise.

---

## get_plugin_manager

Get the global plugin manager instance.

**Returns**: The global WasmPluginManager instance.

---

## initialize

```python
initialize(self: Any)
```

Initialize the Wasm runtime.

---

## is_available

```python
is_available(self: Any)
```

Check if the Wasm runtime is available.

---

## list_plugins

```python
list_plugins(self: Any)
```

List all registered plugin names.

**Returns**: List of plugin names.

---

## load

```python
load(self: Any)
```

Load the plugin into the Extism runtime.

---

## load_plugin

```python
load_plugin(self: Any, name: str)
```

Load a registered plugin.

**Parameters**:

- `name`: The plugin name.

**Returns**: True if loading was successful, False otherwise.

---

## register_plugin

```python
register_plugin(self: Any, plugin: WasmPlugin)
```

Register a plugin with the manager.

**Parameters**:

- `plugin`: The plugin to register.

**Returns**: True if registration was successful, False otherwise.

---

## remove_plugin

```python
remove_plugin(self: Any, name: str)
```

Remove and unload a plugin.

**Parameters**:

- `name`: The plugin name.

**Returns**: True if removal was successful, False otherwise.

---

## status

```python
status(self: Any)
```

Get the current plugin status.

---

## unload

```python
unload(self: Any)
```

Unload the plugin and release resources.

---

## unload_plugin

```python
unload_plugin(self: Any, name: str)
```

Unload a registered plugin.

**Parameters**:

- `name`: The plugin name.

**Returns**: True if unloading was successful, False otherwise.

---
