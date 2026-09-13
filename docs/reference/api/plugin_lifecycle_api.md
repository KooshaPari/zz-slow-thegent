# plugin_lifecycle API Reference

> **Source**: `src/thegent/governance/plugin_lifecycle.py`

WP-10008: Plugin lifecycle and conformance checks.

Manages the registration and conformance validation of system plugins.

---

## PluginLifecycleManager

Manages the state and conformance of system plugins.

### Methods

#### PluginLifecycleManager.**init**

```python
__init__(self: Any)
```

---

#### PluginLifecycleManager.get_plugin_status

```python
get_plugin_status(self: Any, plugin_id: str)
```

Return the current status of a plugin.

---

#### PluginLifecycleManager.register_plugin

```python
register_plugin(self: Any, plugin_id: str, metadata: dict[(str, Any)])
```

Register a new plugin for validation.

---

#### PluginLifecycleManager.run_conformance

```python
run_conformance(self: Any, plugin_id: str)
```

WP-10008: Run conformance tests on a plugin.

---

---

## PluginStatus

**Inherits from**: `StrEnum`

---

## get_plugin_status

```python
get_plugin_status(self: Any, plugin_id: str)
```

Return the current status of a plugin.

---

## register_plugin

```python
register_plugin(self: Any, plugin_id: str, metadata: dict[(str, Any)])
```

Register a new plugin for validation.

---

## run_conformance

```python
run_conformance(self: Any, plugin_id: str)
```

WP-10008: Run conformance tests on a plugin.

---
