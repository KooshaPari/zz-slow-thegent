# release_packager API Reference

> **Source**: `src/thegent/tools/release_packager.py`

WP-12009: Automation of release docs packaging.

Compiles PRD, WBS, and test artifacts into a deterministic release package.

---

## ReleasePackager

Packager for system release documentation and artifacts.

### Methods

#### ReleasePackager.**init**

```python
__init__(self: Any, workspace_root: Path)
```

---

#### ReleasePackager.compile_package

```python
compile_package(self: Any, version: str)
```

Compile all required documents and generate checksums.

---

---

## compile_package

```python
compile_package(self: Any, version: str)
```

Compile all required documents and generate checksums.

---
