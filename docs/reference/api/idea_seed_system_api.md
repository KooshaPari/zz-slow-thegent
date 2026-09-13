# idea_seed_system API Reference

> **Source**: `src/thegent/research/idea_seed_system.py`

Idea Seed Detection & Storage System.

---

## IdeaSeedSystem

System for detecting and storing idea seeds.

### Methods

#### IdeaSeedSystem.**init**

```python
__init__(self: Any, storage_path: Any)
```

Initialize idea seed system.

**Parameters**:

- `storage_path`: Storage directory path

---

#### IdeaSeedSystem.detect_seed

```python
detect_seed(self: Any, content: str, context: Any)
```

Detect an idea seed in content.

**Parameters**:

- `content`: Content to analyze
- `context`: Additional context

**Returns**: Idea seed dictionary or None

---

#### IdeaSeedSystem.get_seeds

```python
get_seeds(self: Any, keyword: Any)
```

Get stored seeds.

**Parameters**:

- `keyword`: Optional keyword filter

**Returns**: List of seeds

---

#### IdeaSeedSystem.store_seed

```python
store_seed(self: Any, seed: dict[(str, Any)])
```

Store an idea seed.

**Parameters**:

- `seed`: Seed dictionary

**Returns**: Path to stored seed file

---

---

## detect_seed

```python
detect_seed(self: Any, content: str, context: Any)
```

Detect an idea seed in content.

**Parameters**:

- `content`: Content to analyze
- `context`: Additional context

**Returns**: Idea seed dictionary or None

---

## get_seeds

```python
get_seeds(self: Any, keyword: Any)
```

Get stored seeds.

**Parameters**:

- `keyword`: Optional keyword filter

**Returns**: List of seeds

---

## store_seed

```python
store_seed(self: Any, seed: dict[(str, Any)])
```

Store an idea seed.

**Parameters**:

- `seed`: Seed dictionary

**Returns**: Path to stored seed file

---
