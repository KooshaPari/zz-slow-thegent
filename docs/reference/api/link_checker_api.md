# link_checker API Reference

> **Source**: `src/thegent/utils/link_checker.py`

Automated link checking for documentation.

---

## LinkChecker

Check links in markdown files.

### Methods

#### LinkChecker.**init**

```python
__init__(self: Any, base_dir: Any)
```

Initialize link checker.

**Parameters**:

- `base_dir`: Base directory for documentation

---

#### LinkChecker.check_directory

```python
check_directory(self: Any, dir_path: Path, pattern: str)
```

Check all markdown files in a directory.

**Parameters**:

- `dir_path`: Directory to check
- `pattern`: File pattern to match

**Returns**: Summary dictionary with results

---

#### LinkChecker.check_file

```python
check_file(self: Any, file_path: Path)
```

Check all links in a file.

**Parameters**:

- `file_path`: Path to markdown file

**Returns**: List of check results

---

#### LinkChecker.check_link

```python
check_link(self: Any, url: str, base_path: Path)
```

Check if a link is valid.

**Parameters**:

- `url`: Link URL
- `base_path`: Base path for relative links

**Returns**: Dictionary with status, error, etc.

---

#### LinkChecker.find_links

```python
find_links(self: Any, file_path: Path)
```

Find all links in a markdown file.

**Parameters**:

- `file_path`: Path to markdown file

**Returns**: List of link dictionaries with url, line, type

---

---

## check_directory

```python
check_directory(self: Any, dir_path: Path, pattern: str)
```

Check all markdown files in a directory.

**Parameters**:

- `dir_path`: Directory to check
- `pattern`: File pattern to match

**Returns**: Summary dictionary with results

---

## check_file

```python
check_file(self: Any, file_path: Path)
```

Check all links in a file.

**Parameters**:

- `file_path`: Path to markdown file

**Returns**: List of check results

---

## check_link

```python
check_link(self: Any, url: str, base_path: Path)
```

Check if a link is valid.

**Parameters**:

- `url`: Link URL
- `base_path`: Base path for relative links

**Returns**: Dictionary with status, error, etc.

---

## find_links

```python
find_links(self: Any, file_path: Path)
```

Find all links in a markdown file.

**Parameters**:

- `file_path`: Path to markdown file

**Returns**: List of link dictionaries with url, line, type

---
