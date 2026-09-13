# harmonized_paths API Reference

> **Source**: `src/thegent/integration/harmonized_paths.py`

Harmonized path strategy across all integrated systems.

---

## HarmonizedPathManager

Harmonize paths across systems.

This class creates consistent path mappings across all integrated systems
(thegent, manage devkit, workstream, plan system) to ensure harmonious
directory structures.

### Methods

#### HarmonizedPathManager.**init**

```python
__init__(self: Any)
```

Initialize harmonized path manager.

---

#### HarmonizedPathManager.create_shared_structure

```python
create_shared_structure(self: Any)
```

Create shared directory structure.

Creates common parent directories and ensures consistent structure
across all integrated systems.

---

#### HarmonizedPathManager.get_harmonized_path

```python
get_harmonized_path(self: Any, system: str, path_type: str)
```

Get harmonized path for system.

**Parameters**:

- `system`: System name (thegent, manage, workstream, plan)
- `path_type`: Path type (config, cache, data, bin, log, temp)

**Returns**: Path object, or None if not found

---

---

## create_shared_structure

```python
create_shared_structure(self: Any)
```

Create shared directory structure.

Creates common parent directories and ensures consistent structure
across all integrated systems.

---

## get_harmonized_path

```python
get_harmonized_path(self: Any, system: str, path_type: str)
```

Get harmonized path for system.

**Parameters**:

- `system`: System name (thegent, manage, workstream, plan)
- `path_type`: Path type (config, cache, data, bin, log, temp)

**Returns**: Path object, or None if not found

---
