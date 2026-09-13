# versioning API Reference

> **Source**: `src/thegent/docgen/versioning.py`

Implement version switcher for documentation.

---

## VersioningManager

Manage documentation versioning.

### Methods

#### VersioningManager.**init**

```python
__init__(self: Any, versions: list[str])
```

---

#### VersioningManager.generate_version_manifest

```python
generate_version_manifest(self: Any)
```

Generate version manifest for documentation site.

**Returns**: JSON version manifest string

---

#### VersioningManager.generate_version_switcher_html

```python
generate_version_switcher_html(self: Any, current_version: str)
```

Generate HTML for version switcher.

**Parameters**:

- `current_version`: Currently selected version

**Returns**: Version switcher HTML content

---

---

## generate_version_manifest

```python
generate_version_manifest(self: Any)
```

Generate version manifest for documentation site.

**Returns**: JSON version manifest string

---

## generate_version_switcher_html

```python
generate_version_switcher_html(self: Any, current_version: str)
```

Generate HTML for version switcher.

**Parameters**:

- `current_version`: Currently selected version

**Returns**: Version switcher HTML content

---
