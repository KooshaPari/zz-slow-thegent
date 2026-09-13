# jetbrains_cli API Reference

> **Source**: `src/thegent/lsp/jetbrains_cli.py`

JetBrains IDE CLI Integration.

---

## JetBrainsCLI

Wrapper for JetBrains IDE CLI tools.

### Methods

#### JetBrainsCLI.**init**

```python
__init__(self: Any, ide_path: Any)
```

Initialize JetBrains CLI wrapper.

**Parameters**:

- `ide_path`: Path to IntelliJ IDEA executable (e.g., /Applications/IntelliJ IDEA.app/Contents/MacOS/idea)
  If None, tries to find in PATH or common locations.

---

#### JetBrainsCLI.diff

```python
diff(self: Any, file1: Path, file2: Path)
```

Show diff between two files.

**Parameters**:

- `file1`: First file
- `file2`: Second file

**Returns**: Dict with diff output

---

#### JetBrainsCLI.format

```python
format(self: Any, files: list[Path], project_root: Any)
```

Format files using IntelliJ IDEA formatter.

**Parameters**:

- `files`: List of files to format
- `project_root`: Project root directory (optional)

**Returns**: Dict with 'success', 'stdout', 'stderr'

---

#### JetBrainsCLI.inspect

```python
inspect(self: Any, project_root: Path, profile: Any)
```

Run code inspections using IntelliJ IDEA.

**Parameters**:

- `project_root`: Project root directory
- `profile`: Inspection profile name (optional)

**Returns**: Dict with inspection results

---

#### JetBrainsCLI.merge

```python
merge(self: Any, file1: Path, file2: Path, base: Path, output: Path)
```

Merge two files with base.

**Parameters**:

- `file1`: First file
- `file2`: Second file
- `base`: Base file
- `output`: Output file

**Returns**: Dict with merge result

---

---

## diff

```python
diff(self: Any, file1: Path, file2: Path)
```

Show diff between two files.

**Parameters**:

- `file1`: First file
- `file2`: Second file

**Returns**: Dict with diff output

---

## format

```python
format(self: Any, files: list[Path], project_root: Any)
```

Format files using IntelliJ IDEA formatter.

**Parameters**:

- `files`: List of files to format
- `project_root`: Project root directory (optional)

**Returns**: Dict with 'success', 'stdout', 'stderr'

---

## inspect

```python
inspect(self: Any, project_root: Path, profile: Any)
```

Run code inspections using IntelliJ IDEA.

**Parameters**:

- `project_root`: Project root directory
- `profile`: Inspection profile name (optional)

**Returns**: Dict with inspection results

---

## merge

```python
merge(self: Any, file1: Path, file2: Path, base: Path, output: Path)
```

Merge two files with base.

**Parameters**:

- `file1`: First file
- `file2`: Second file
- `base`: Base file
- `output`: Output file

**Returns**: Dict with merge result

---
