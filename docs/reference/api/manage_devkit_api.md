# manage_devkit API Reference

> **Source**: `src/thegent/integration/manage_devkit.py`

Integration with manage devkit system.

---

## ManageDevkitIntegration

Integrate with manage devkit system.

This class handles integration with external "manage" devkit systems,
including path sharing, tool registration, and configuration harmonization.

### Methods

#### ManageDevkitIntegration.**init**

```python
__init__(self: Any)
```

Initialize manage devkit integration.

---

#### ManageDevkitIntegration.integrate_paths

```python
integrate_paths(self: Any)
```

Integrate thegent paths with manage devkit.

Creates shared configuration structure if manage devkit uses
similar directory structure. Creates symlinks to share config.

---

#### ManageDevkitIntegration.integrate_tools

```python
integrate_tools(self: Any)
```

Integrate thegent tools with manage devkit.

Creates symlink to thegent binary in manage devkit bin directory.

---

#### ManageDevkitIntegration.register_with_manage

```python
register_with_manage(self: Any)
```

Register thegent with manage devkit.

Adds thegent to the list of tools in manage devkit configuration.

---

---

## integrate_paths

```python
integrate_paths(self: Any)
```

Integrate thegent paths with manage devkit.

Creates shared configuration structure if manage devkit uses
similar directory structure. Creates symlinks to share config.

---

## integrate_tools

```python
integrate_tools(self: Any)
```

Integrate thegent tools with manage devkit.

Creates symlink to thegent binary in manage devkit bin directory.

---

## register_with_manage

```python
register_with_manage(self: Any)
```

Register thegent with manage devkit.

Adds thegent to the list of tools in manage devkit configuration.

---
