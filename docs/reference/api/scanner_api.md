# scanner API Reference

> **Source**: `src/thegent/agents/document/scanner.py`

Markdown File Scanner

Scans directories for markdown files, organizing them by modification date
and location. Supports configurable scan parameters and exclusion patterns.

---

## MarkdownScanner

Scans directories for markdown files and organizes by date/location.

### Methods

#### MarkdownScanner.**init**

```python
__init__(self: Any, config: ScanConfig)
```

---

#### MarkdownScanner.get_file_date

```python
get_file_date(self: Any, filepath: Path)
```

Get file modification date as YYYY-MM.

---

#### MarkdownScanner.get_summary

```python
get_summary(self: Any)
```

Get summary statistics of scan results.

---

#### MarkdownScanner.save_results

```python
save_results(self: Any, output_path: Any)
```

Save scan results to JSON file.

---

#### MarkdownScanner.scan

```python
scan(self: Any)
```

Perform scan of all configured locations.

---

#### MarkdownScanner.scan_directory

```python
scan_directory(self: Any, base_path: str, recursive: bool, max_depth: Any)
```

Scan directory for .md files.

---

#### MarkdownScanner.should_exclude

```python
should_exclude(self: Any, filepath: Path)
```

Check if filepath should be excluded.

---

---

## ScanConfig

Configuration for markdown file scanning.

### Methods

---

## get_file_date

```python
get_file_date(self: Any, filepath: Path)
```

Get file modification date as YYYY-MM.

---

## get_summary

```python
get_summary(self: Any)
```

Get summary statistics of scan results.

---

## save_results

```python
save_results(self: Any, output_path: Any)
```

Save scan results to JSON file.

---

## scan

```python
scan(self: Any)
```

Perform scan of all configured locations.

---

## scan_directory

```python
scan_directory(self: Any, base_path: str, recursive: bool, max_depth: Any)
```

Scan directory for .md files.

---

## should_exclude

```python
should_exclude(self: Any, filepath: Path)
```

Check if filepath should be excluded.

---
