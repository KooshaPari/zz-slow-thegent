# edit_links API Reference

> **Source**: `src/thegent/utils/edit_links.py`

Generate edit-on-GitHub links for documentation.

---

## EditLinksGenerator

Generate edit-on-GitHub links for markdown files.

### Methods

#### EditLinksGenerator.**init**

```python
__init__(self: Any, repo_url: str, branch: str, base_dir: Any)
```

Initialize edit links generator.

**Parameters**:

- `repo_url`: GitHub repository URL
- `branch`: Git branch name
- `base_dir`: Base directory for documentation

---

#### EditLinksGenerator.add_edit_link_to_file

```python
add_edit_link_to_file(self: Any, file_path: Path, position: str)
```

Add edit link to a markdown file.

**Parameters**:

- `file_path`: Path to markdown file
- `position`: Where to add link ("top" or "bottom")

**Returns**: True if successful

---

#### EditLinksGenerator.add_edit_links_batch

```python
add_edit_links_batch(self: Any, files: list[Path], position: str)
```

Add edit links to multiple files.

**Parameters**:

- `files`: List of file paths
- `position`: Where to add links

**Returns**: Dictionary mapping file paths to success status

---

#### EditLinksGenerator.generate_edit_link

```python
generate_edit_link(self: Any, file_path: Path)
```

Generate edit link for a file.

**Parameters**:

- `file_path`: Path to file

**Returns**: GitHub edit URL

---

---

## add_edit_link_to_file

```python
add_edit_link_to_file(self: Any, file_path: Path, position: str)
```

Add edit link to a markdown file.

**Parameters**:

- `file_path`: Path to markdown file
- `position`: Where to add link ("top" or "bottom")

**Returns**: True if successful

---

## add_edit_links_batch

```python
add_edit_links_batch(self: Any, files: list[Path], position: str)
```

Add edit links to multiple files.

**Parameters**:

- `files`: List of file paths
- `position`: Where to add links

**Returns**: Dictionary mapping file paths to success status

---

## generate_edit_link

```python
generate_edit_link(self: Any, file_path: Path)
```

Generate edit link for a file.

**Parameters**:

- `file_path`: Path to file

**Returns**: GitHub edit URL

---
