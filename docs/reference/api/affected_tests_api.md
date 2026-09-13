# affected_tests API Reference

> **Source**: `src/thegent/hooks/affected_tests.py`

Implement affected-tests subcommand (pattern + coverage + imports).

---

## AffectedTestsSubcommand

Affected tests detection.

### Methods

#### AffectedTestsSubcommand.**init**

```python
__init__(self: Any)
```

Initialize affected tests.

---

#### AffectedTestsSubcommand.find_affected_tests

```python
find_affected_tests(self: Any, changed_files: list[Path], test_dir: Any)
```

Find tests affected by changed files.

**Parameters**:

- `changed_files`: List of changed files
- `test_dir`: Test directory

**Returns**: List of affected test files

---

---

## find_affected_tests

```python
find_affected_tests(self: Any, changed_files: list[Path], test_dir: Any)
```

Find tests affected by changed files.

**Parameters**:

- `changed_files`: List of changed files
- `test_dir`: Test directory

**Returns**: List of affected test files

---
