# idea_seeds API Reference

> **Source**: `src/thegent/commands/idea_seeds.py`

Idea seed scanner: find and manage embedded improvement opportunities.

Scans codebases for embedded idea seeds — improvement opportunities, TODOs
with context, refactoring hints, and similar code-level annotations.

Provides:

- IdeaSeed dataclass representing a found seed with surrounding context
- IdeaSeedScanner for recursive directory and single-file scanning
- Export to markdown and WORK_STREAM.md compatible rows
- Typer CLI sub-application (registered under `thegent seeds`)

---

## IdeaSeed

A single idea seed found in source code.

### Methods

#### IdeaSeed.to_dict

```python
to_dict(self: Any)
```

Serialise to a plain dictionary.

---

---

## IdeaSeedScanner

Scan source files for embedded idea seeds.

### Methods

#### IdeaSeedScanner.**init**

```python
__init__(self: Any, context_lines: int)
```

---

#### IdeaSeedScanner.export_markdown

```python
export_markdown(self: Any, seeds: list[IdeaSeed], output: Path)
```

Export seeds to a markdown file grouped by pattern type.

**Parameters**:

- `seeds`: Seeds to export.
- `output`: Destination file path (created / overwritten).

---

#### IdeaSeedScanner.filter_by_type

```python
filter_by_type(self: Any, seeds: list[IdeaSeed], types: list[str])
```

Keep only seeds whose pattern*type is in \_types*.

**Parameters**:

- `seeds`: Input seed list.
- `types`: Pattern type strings to keep (case-insensitive).

**Returns**: Filtered seed list.

---

#### IdeaSeedScanner.scan_directory

```python
scan_directory(self: Any, root: Path, extensions: Any)
```

Recursively scan a directory for idea seeds.

**Parameters**:

- `root`: Root directory to scan.
- `extensions`: File extensions to include (e.g. [".py", ".ts"]).
  Defaults to DEFAULT_EXTENSIONS when None.

**Returns**: Ordered list of IdeaSeed objects across all matched files.

---

#### IdeaSeedScanner.scan_file

```python
scan_file(self: Any, path: Path)
```

Scan a single file for idea seeds.

**Parameters**:

- `path`: Path to the file to scan.

**Returns**: Ordered list of IdeaSeed objects found in the file.

---

#### IdeaSeedScanner.to_work_stream_items

```python
to_work_stream_items(self: Any, seeds: list[IdeaSeed])
```

Convert seeds to WORK_STREAM.md-compatible row dictionaries.

Each row has keys: id, title, source, priority, depends.

**Parameters**:

- `seeds`: List of IdeaSeed objects.

**Returns**: List of dicts ready to be serialised as WORK_STREAM table rows.

---

---

## export_markdown

```python
export_markdown(self: Any, seeds: list[IdeaSeed], output: Path)
```

Export seeds to a markdown file grouped by pattern type.

**Parameters**:

- `seeds`: Seeds to export.
- `output`: Destination file path (created / overwritten).

---

## filter_by_type

```python
filter_by_type(self: Any, seeds: list[IdeaSeed], types: list[str])
```

Keep only seeds whose pattern*type is in \_types*.

**Parameters**:

- `seeds`: Input seed list.
- `types`: Pattern type strings to keep (case-insensitive).

**Returns**: Filtered seed list.

---

## scan_directory

```python
scan_directory(self: Any, root: Path, extensions: Any)
```

Recursively scan a directory for idea seeds.

**Parameters**:

- `root`: Root directory to scan.
- `extensions`: File extensions to include (e.g. [".py", ".ts"]).
  Defaults to DEFAULT_EXTENSIONS when None.

**Returns**: Ordered list of IdeaSeed objects across all matched files.

---

## scan_file

```python
scan_file(self: Any, path: Path)
```

Scan a single file for idea seeds.

**Parameters**:

- `path`: Path to the file to scan.

**Returns**: Ordered list of IdeaSeed objects found in the file.

---

## seeds_add_to_workstream

```python
seeds_add_to_workstream(directory: Path, workstream: Path, types: str, dry_run: bool)
```

Append unclaimed idea seeds as BACKLOG items in WORK_STREAM.md.

---

## seeds_export

```python
seeds_export(directory: Path, output: Path, types: str, extensions: str)
```

Export found idea seeds to a markdown file.

---

## seeds_scan

```python
seeds_scan(directory: Path, types: str, extensions: str, output_json: bool)
```

Scan a directory for embedded idea seeds and display results.

---

## to_dict

```python
to_dict(self: Any)
```

Serialise to a plain dictionary.

---

## to_work_stream_items

```python
to_work_stream_items(self: Any, seeds: list[IdeaSeed])
```

Convert seeds to WORK_STREAM.md-compatible row dictionaries.

Each row has keys: id, title, source, priority, depends.

**Parameters**:

- `seeds`: List of IdeaSeed objects.

**Returns**: List of dicts ready to be serialised as WORK_STREAM table rows.

---
