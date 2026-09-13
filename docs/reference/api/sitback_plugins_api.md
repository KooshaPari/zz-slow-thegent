# sitback_plugins API Reference

> **Source**: `src/thegent/sitback_plugins.py`

Sitback plugin API: dashboard widgets and startup steps.

Plugins are discovered from ~/.claude/sitback-plugins/ (JSON or Python).
Each plugin can register:

- dashboard_widgets: dict[str, callable] -> name -> fn() -> dict (title, content, border_style)
- startup_steps: list[str] -> extra lines for startup prompt
- harness_status: callable -> dict | None (for heliosShield/FUSE; returns None if unavailable)

---

## SitbackPluginRegistry

Registry for sitback plugins: widgets, startup steps, harness status.

### Methods

#### SitbackPluginRegistry.**init**

```python
__init__(self: Any)
```

---

#### SitbackPluginRegistry.get_harness_status

```python
get_harness_status(self: Any)
```

Return harness status if provider available, else None.

---

#### SitbackPluginRegistry.get_startup_steps

```python
get_startup_steps(self: Any)
```

Return registered startup steps.

---

#### SitbackPluginRegistry.get_widgets

```python
get_widgets(self: Any)
```

Run all widgets, return {name: result}. Skips failures.

---

#### SitbackPluginRegistry.register_harness_status

```python
register_harness_status(self: Any, fn: Callable[(Any, Any)])
```

Register harness status provider (e.g. heliosShield). Returns None if unavailable.

---

#### SitbackPluginRegistry.register_startup_step

```python
register_startup_step(self: Any, step: str)
```

Register an extra startup step (appended to startup prompt).

---

#### SitbackPluginRegistry.register_widget

```python
register_widget(self: Any, name: str, fn: Callable[(Any, dict[(str, Any)])])
```

Register a dashboard widget. fn() returns {title, content, border_style}.

---

---

## get_harness_status

```python
get_harness_status(self: Any)
```

Return harness status if provider available, else None.

---

## get_registry

Get or create the global plugin registry.

---

## get_startup_steps

```python
get_startup_steps(self: Any)
```

Return registered startup steps.

---

## get_widgets

```python
get_widgets(self: Any)
```

Run all widgets, return {name: result}. Skips failures.

---

## register_harness_status

```python
register_harness_status(self: Any, fn: Callable[(Any, Any)])
```

Register harness status provider (e.g. heliosShield). Returns None if unavailable.

---

## register_startup_step

```python
register_startup_step(self: Any, step: str)
```

Register an extra startup step (appended to startup prompt).

---

## register_widget

```python
register_widget(self: Any, name: str, fn: Callable[(Any, dict[(str, Any)])])
```

Register a dashboard widget. fn() returns {title, content, border_style}.

---
