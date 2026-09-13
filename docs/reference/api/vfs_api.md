# vfs API Reference

> **Source**: `src/thegent/isolation/vfs.py`

Virtual File System (VFS) adapter for efficient home directory management.

---

## VfsAdapter

Adapter for high-performance home directory creation.

Supports:

1. OverlayFS (Linux only) - Extremely fast, minimal disk usage.
2. Reflink (macOS APFS / Btrfs) - Fast cloning without duplication.
3. Fallback: Copy-on-Write (COW) or simple shutil.copytree.

### Methods

#### VfsAdapter.**init**

```python
__init__(self: Any, base_skel_dir: Any)
```

Initialize VfsAdapter.

**Parameters**:

- `base_skel_dir`: Path to the 'skeleton' directory used as a base.

---

#### VfsAdapter.cleanup_home_dir

```python
cleanup_home_dir(self: Any, target_dir: Path, tenant_id: str)
```

Clean up the home directory, including unmounting if necessary.

---

#### VfsAdapter.create_home_dir

```python
create_home_dir(self: Any, target_dir: Path, tenant_id: str)
```

Create a home directory for a tenant using the most efficient method.

---

---

## cleanup_home_dir

```python
cleanup_home_dir(self: Any, target_dir: Path, tenant_id: str)
```

Clean up the home directory, including unmounting if necessary.

---

## create_home_dir

```python
create_home_dir(self: Any, target_dir: Path, tenant_id: str)
```

Create a home directory for a tenant using the most efficient method.

---
