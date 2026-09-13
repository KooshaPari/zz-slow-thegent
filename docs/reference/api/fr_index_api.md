# fr_index API Reference

> **Source**: `src/thegent/hooks/fr_index.py`

Implement fr-ids and fr-index subcommands (FR parsing/indexing).

---

## FRIndexSubcommands

FR (Functional Requirement) parsing and indexing.

### Methods

#### FRIndexSubcommands.**init**

```python
__init__(self: Any)
```

Initialize FR index subcommands.

---

#### FRIndexSubcommands.extract_fr_ids

```python
extract_fr_ids(self: Any, content: str)
```

Extract FR IDs from content.

**Parameters**:

- `content`: Content to parse

**Returns**: List of FR IDs

---

#### FRIndexSubcommands.get_fr_references

```python
get_fr_references(self: Any, fr_id: str)
```

Get files referencing an FR.

**Parameters**:

- `fr_id`: FR identifier

**Returns**: List of file paths

---

#### FRIndexSubcommands.index_file

```python
index_file(self: Any, file_path: Path)
```

Index a file for FR references.

**Parameters**:

- `file_path`: File to index

**Returns**: Index entry

---

---

## extract_fr_ids

```python
extract_fr_ids(self: Any, content: str)
```

Extract FR IDs from content.

**Parameters**:

- `content`: Content to parse

**Returns**: List of FR IDs

---

## get_fr_references

```python
get_fr_references(self: Any, fr_id: str)
```

Get files referencing an FR.

**Parameters**:

- `fr_id`: FR identifier

**Returns**: List of file paths

---

## index_file

```python
index_file(self: Any, file_path: Path)
```

Index a file for FR references.

**Parameters**:

- `file_path`: File to index

**Returns**: Index entry

---
