# fast_string_ops API Reference

> **Source**: `src/thegent/infra/fast_string_ops.py`

Fast string operations with optimized backends.

This module provides optimized string operations:

- rapidfuzz for fuzzy matching (already installed!)
- regex for advanced regex patterns (already installed!)
- Optimized string operations

Performance improvements:

- rapidfuzz: 10-100x faster fuzzy matching
- regex: Faster complex regex patterns
- Optimized string operations

---

## FastStringOps

High-performance string operations with optimized backends.

### Methods

#### FastStringOps.fuzzy_match

```python
fuzzy_match(query: str, choices: list[str], limit: int, score_cutoff: int)
```

Fuzzy string matching using rapidfuzz (10-100x faster).

**Parameters**:

- `query`: Query string
- `choices`: List of strings to match against
- `limit`: Maximum number of results
- `score_cutoff`: Minimum similarity score (0-100)

**Returns**: List of (match, score, index) tuples

---

#### FastStringOps.fuzzy_ratio

```python
fuzzy_ratio(str1: str, str2: str)
```

Calculate fuzzy similarity ratio (0-100).

**Parameters**:

- `str1`: First string
- `str2`: Second string

**Returns**: Similarity ratio (0-100)

---

#### FastStringOps.regex_findall

```python
regex_findall(pattern: str, text: str)
```

Find all matches using regex library.

**Parameters**:

- `pattern`: Regex pattern
- `text`: Text to search
- `**kwargs`: Additional regex options

**Returns**: List of matches

---

#### FastStringOps.regex_search

```python
regex_search(pattern: str, text: str)
```

Search using regex library (faster for complex patterns).

**Parameters**:

- `pattern`: Regex pattern
- `text`: Text to search
- `**kwargs`: Additional regex options

**Returns**: Match object or None

---

---

## fuzzy_match

```python
fuzzy_match(query: str, choices: list[str], limit: int, score_cutoff: int)
```

Fuzzy string matching using rapidfuzz (10-100x faster).

**Parameters**:

- `query`: Query string
- `choices`: List of strings to match against
- `limit`: Maximum number of results
- `score_cutoff`: Minimum similarity score (0-100)

**Returns**: List of (match, score, index) tuples

---

## fuzzy_ratio

```python
fuzzy_ratio(str1: str, str2: str)
```

Calculate fuzzy similarity ratio (0-100).

**Parameters**:

- `str1`: First string
- `str2`: Second string

**Returns**: Similarity ratio (0-100)

---

## regex_findall

```python
regex_findall(pattern: str, text: str)
```

Find all matches using regex library.

**Parameters**:

- `pattern`: Regex pattern
- `text`: Text to search
- `**kwargs`: Additional regex options

**Returns**: List of matches

---

## regex_search

```python
regex_search(pattern: str, text: str)
```

Search using regex library (faster for complex patterns).

**Parameters**:

- `pattern`: Regex pattern
- `text`: Text to search
- `**kwargs`: Additional regex options

**Returns**: Match object or None

---
