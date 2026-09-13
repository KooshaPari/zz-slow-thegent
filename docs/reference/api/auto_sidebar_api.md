# auto_sidebar API Reference

> **Source**: `src/thegent/docgen/auto_sidebar.py`

Auto-generate sidebar from directory structure.

---

## AutoSidebarGenerator

Generate sidebar automatically from directory structure.

### Methods

#### AutoSidebarGenerator.**init**

```python
__init__(self: Any, docs_root: Path)
```

Initialize auto-sidebar generator.

**Parameters**:

- `docs_root`: Root directory of documentation

---

#### AutoSidebarGenerator.generate_sidebar_config

```python
generate_sidebar_config(self: Any)
```

Generate sidebar configuration.

**Returns**: Sidebar configuration list

---

#### AutoSidebarGenerator.scan_structure

```python
scan_structure(self: Any)
```

Scan directory structure.

**Returns**: Structure dictionary

---

---

## generate_sidebar_config

```python
generate_sidebar_config(self: Any)
```

Generate sidebar configuration.

**Returns**: Sidebar configuration list

---

## scan_structure

```python
scan_structure(self: Any)
```

Scan directory structure.

**Returns**: Structure dictionary

---
