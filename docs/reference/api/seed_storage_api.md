# seed_storage API Reference

> **Source**: `src/thegent/memory/seed_storage.py`

File-based storage for idea seeds using JSONL format.

Seeds are stored in docs/research/seeds.jsonl (one JSON object per line).
Provides read, write, update, and query operations.

---

## SeedStorage

JSONL-based storage for idea seeds.

### Methods

#### SeedStorage.**init**

```python
__init__(self: Any, storage_path: Any)
```

Initialize seed storage.

**Parameters**:

- `storage_path`: Path to seeds.jsonl (defaults to docs/research/seeds.jsonl)

---

#### SeedStorage.archive_seed

```python
archive_seed(self: Any, seed_id: str)
```

Move a seed to archive (mark as archived).

**Parameters**:

- `seed_id`: Seed ID to archive

**Returns**: True if archived, False if not found

---

#### SeedStorage.delete_seed

```python
delete_seed(self: Any, seed_id: str)
```

Delete a seed (actually moves to archive).

**Parameters**:

- `seed_id`: Seed ID to delete

**Returns**: True if deleted, False if not found

---

#### SeedStorage.export_markdown

```python
export_markdown(self: Any, output_path: Any)
```

Export seeds as markdown for easy reading.

**Parameters**:

- `output_path`: Optional path to write markdown file

**Returns**: Markdown content

---

#### SeedStorage.find_by_id

```python
find_by_id(self: Any, seed_id: str)
```

Find a seed by ID.

**Parameters**:

- `seed_id`: Seed ID to find

**Returns**: Seed object or None if not found

---

#### SeedStorage.find_by_source

```python
find_by_source(self: Any, source: SeedSource)
```

Find seeds by source.

**Parameters**:

- `source`: SeedSource to filter by

**Returns**: List of matching Seed objects

---

#### SeedStorage.find_by_status

```python
find_by_status(self: Any, status: str)
```

Find seeds by status.

**Parameters**:

- `status`: Status to filter by (e.g., "new", "developing", "implemented")

**Returns**: List of matching Seed objects

---

#### SeedStorage.find_by_tag

```python
find_by_tag(self: Any, tag: str)
```

Find seeds by tag.

**Parameters**:

- `tag`: Tag to filter by

**Returns**: List of matching Seed objects

---

#### SeedStorage.find_by_text

```python
find_by_text(self: Any, text: str)
```

Find a seed by exact text match.

**Parameters**:

- `text`: Text to match

**Returns**: Seed object or None if not found

---

#### SeedStorage.get_stats

```python
get_stats(self: Any)
```

Get storage statistics.

**Returns**: Dict with stats: total, by_status, by_source, by_confidence

---

#### SeedStorage.load_seeds

```python
load_seeds(self: Any)
```

Load all seeds from storage.

**Returns**: List of Seed objects

---

#### SeedStorage.store_seed

```python
store_seed(self: Any, seed: Seed)
```

Store a seed in the JSONL file.

**Parameters**:

- `seed`: Seed object to store

**Returns**: Seed ID

---

#### SeedStorage.update_seed

```python
update_seed(self: Any, seed_id: str)
```

Update seed fields (status, tags, etc.).

**Parameters**:

- `seed_id`: Seed ID to update
- `**kwargs`: Fields to update (status, tags, context, etc.)

**Returns**: True if updated, False if not found

---

---

## archive_seed

```python
archive_seed(self: Any, seed_id: str)
```

Move a seed to archive (mark as archived).

**Parameters**:

- `seed_id`: Seed ID to archive

**Returns**: True if archived, False if not found

---

## delete_seed

```python
delete_seed(self: Any, seed_id: str)
```

Delete a seed (actually moves to archive).

**Parameters**:

- `seed_id`: Seed ID to delete

**Returns**: True if deleted, False if not found

---

## export_markdown

```python
export_markdown(self: Any, output_path: Any)
```

Export seeds as markdown for easy reading.

**Parameters**:

- `output_path`: Optional path to write markdown file

**Returns**: Markdown content

---

## find_by_id

```python
find_by_id(self: Any, seed_id: str)
```

Find a seed by ID.

**Parameters**:

- `seed_id`: Seed ID to find

**Returns**: Seed object or None if not found

---

## find_by_source

```python
find_by_source(self: Any, source: SeedSource)
```

Find seeds by source.

**Parameters**:

- `source`: SeedSource to filter by

**Returns**: List of matching Seed objects

---

## find_by_status

```python
find_by_status(self: Any, status: str)
```

Find seeds by status.

**Parameters**:

- `status`: Status to filter by (e.g., "new", "developing", "implemented")

**Returns**: List of matching Seed objects

---

## find_by_tag

```python
find_by_tag(self: Any, tag: str)
```

Find seeds by tag.

**Parameters**:

- `tag`: Tag to filter by

**Returns**: List of matching Seed objects

---

## find_by_text

```python
find_by_text(self: Any, text: str)
```

Find a seed by exact text match.

**Parameters**:

- `text`: Text to match

**Returns**: Seed object or None if not found

---

## get_stats

```python
get_stats(self: Any)
```

Get storage statistics.

**Returns**: Dict with stats: total, by_status, by_source, by_confidence

---

## load_seeds

```python
load_seeds(self: Any)
```

Load all seeds from storage.

**Returns**: List of Seed objects

---

## store_seed

```python
store_seed(self: Any, seed: Seed)
```

Store a seed in the JSONL file.

**Parameters**:

- `seed`: Seed object to store

**Returns**: Seed ID

---

## update_seed

```python
update_seed(self: Any, seed_id: str)
```

Update seed fields (status, tags, etc.).

**Parameters**:

- `seed_id`: Seed ID to update
- `**kwargs`: Fields to update (status, tags, context, etc.)

**Returns**: True if updated, False if not found

---
