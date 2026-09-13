# changed_files_enhance API Reference

> **Source**: `src/thegent/hooks/changed_files_enhance.py`

Enhance changed-files: filtering, shared file support, ls-files integration.

---

## ChangedFilesEnhance

Enhanced changed files detection.

### Methods

#### ChangedFilesEnhance.**init**

```python
__init__(self: Any)
```

Initialize changed files enhance.

---

#### ChangedFilesEnhance.get_changed_files

```python
get_changed_files(self: Any, repo_path: Path, filter_patterns: Any)
```

Get changed files with filtering.

**Parameters**:

- `repo_path`: Repository path
- `filter_patterns`: Optional filter patterns

**Returns**: List of changed file paths

---

#### ChangedFilesEnhance.get_shared_files

```python
get_shared_files(self: Any, repo_path: Path)
```

Get shared files (symlinks, etc.).

**Parameters**:

- `repo_path`: Repository path

**Returns**: List of shared file paths

---

#### ChangedFilesEnhance.integrate_ls_files

```python
integrate_ls_files(self: Any, repo_path: Path)
```

Integrate git ls-files for comprehensive file listing.

**Parameters**:

- `repo_path`: Repository path

**Returns**: List of all tracked files

---

---

## get_changed_files

```python
get_changed_files(self: Any, repo_path: Path, filter_patterns: Any)
```

Get changed files with filtering.

**Parameters**:

- `repo_path`: Repository path
- `filter_patterns`: Optional filter patterns

**Returns**: List of changed file paths

---

## get_shared_files

```python
get_shared_files(self: Any, repo_path: Path)
```

Get shared files (symlinks, etc.).

**Parameters**:

- `repo_path`: Repository path

**Returns**: List of shared file paths

---

## integrate_ls_files

```python
integrate_ls_files(self: Any, repo_path: Path)
```

Integrate git ls-files for comprehensive file listing.

**Parameters**:

- `repo_path`: Repository path

**Returns**: List of all tracked files

---
