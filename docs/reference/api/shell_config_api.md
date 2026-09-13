# shell_config API Reference

> **Source**: `src/thegent/utils/shell_config.py`

Shell configuration manager: audit and consolidate shell scripts.

Audits Zsh configuration files across a project to identify:

- Duplicate function definitions across files
- Source relationships between files
- Alias definitions
- Consolidation opportunities

---

## ShellConfigAuditor

Audit and consolidate shell configuration files.

Usage::

    auditor = ShellConfigAuditor()
    configs = auditor.audit([Path("shell"), Path("scripts")])
    dupes = auditor.find_duplicates(configs)
    issues = auditor.check_sourcing_order(configs)
    merged = auditor.generate_consolidated(configs)

### Methods

#### ShellConfigAuditor.audit

```python
audit(self: Any, search_dirs: list[Path])
```

Discover and parse shell config files in the given directories.

Walks each directory recursively and parses all files identified as
shell configuration files (Zsh or generic shell scripts).

**Parameters**:

- `search_dirs`: List of directories to search.

**Returns**: List of parsed ShellConfigFile instances, sorted by path.

---

#### ShellConfigAuditor.check_sourcing_order

```python
check_sourcing_order(self: Any, configs: list[ShellConfigFile])
```

Detect potential sourcing issues among the config files.

Checks:

- Files that source other files not present in the discovered set.
- Circular sourcing chains.
- Files that are sourced but have no functions or aliases.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: List of human-readable issue strings. Empty list means no issues.

---

#### ShellConfigAuditor.find_duplicate_aliases

```python
find_duplicate_aliases(self: Any, configs: list[ShellConfigFile])
```

Find alias names that are defined in more than one file.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Mapping from alias name to the list of files that define it.
Only entries with two or more files are included.

---

#### ShellConfigAuditor.find_duplicates

```python
find_duplicates(self: Any, configs: list[ShellConfigFile])
```

Find function names that are defined in more than one file.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Mapping from function name to the list of files that define it.
Only entries with two or more files are included.

---

#### ShellConfigAuditor.generate_consolidated

```python
generate_consolidated(self: Any, configs: list[ShellConfigFile])
```

Generate a merged shell script from all config files.

Each file's content is included with a header comment indicating
its origin. Duplicate function definitions are warned about in
inline comments.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Single string containing the consolidated shell script content.

---

#### ShellConfigAuditor.sourcing_graph

```python
sourcing_graph(self: Any, configs: list[ShellConfigFile])
```

Build a human-readable sourcing dependency graph.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Mapping from file name to list of sourced file names/paths.

---

---

## ShellConfigFile

Represents a parsed shell configuration file.

### Methods

#### ShellConfigFile.parse

```python
parse(cls: Any, path: Path)
```

Parse a shell config file and extract metadata.

**Parameters**:

- `path`: Path to the shell configuration file.

**Returns**: Populated ShellConfigFile instance.

---

---

## audit

```python
audit(self: Any, search_dirs: list[Path])
```

Discover and parse shell config files in the given directories.

Walks each directory recursively and parses all files identified as
shell configuration files (Zsh or generic shell scripts).

**Parameters**:

- `search_dirs`: List of directories to search.

**Returns**: List of parsed ShellConfigFile instances, sorted by path.

---

## check_sourcing_order

```python
check_sourcing_order(self: Any, configs: list[ShellConfigFile])
```

Detect potential sourcing issues among the config files.

Checks:

- Files that source other files not present in the discovered set.
- Circular sourcing chains.
- Files that are sourced but have no functions or aliases.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: List of human-readable issue strings. Empty list means no issues.

---

## find_duplicate_aliases

```python
find_duplicate_aliases(self: Any, configs: list[ShellConfigFile])
```

Find alias names that are defined in more than one file.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Mapping from alias name to the list of files that define it.
Only entries with two or more files are included.

---

## find_duplicates

```python
find_duplicates(self: Any, configs: list[ShellConfigFile])
```

Find function names that are defined in more than one file.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Mapping from function name to the list of files that define it.
Only entries with two or more files are included.

---

## generate_consolidated

```python
generate_consolidated(self: Any, configs: list[ShellConfigFile])
```

Generate a merged shell script from all config files.

Each file's content is included with a header comment indicating
its origin. Duplicate function definitions are warned about in
inline comments.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Single string containing the consolidated shell script content.

---

## parse

```python
parse(cls: Any, path: Path)
```

Parse a shell config file and extract metadata.

**Parameters**:

- `path`: Path to the shell configuration file.

**Returns**: Populated ShellConfigFile instance.

**Raises**:

- `OSError`: If the file cannot be read.

---

## sourcing_graph

```python
sourcing_graph(self: Any, configs: list[ShellConfigFile])
```

Build a human-readable sourcing dependency graph.

**Parameters**:

- `configs`: List of parsed shell config files.

**Returns**: Mapping from file name to list of sourced file names/paths.

---
