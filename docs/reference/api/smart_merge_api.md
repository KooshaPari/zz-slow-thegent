# smart_merge API Reference

> **Source**: `src/thegent/coordination/smart_merge.py`

Phase 7: Smart Merge implementation.

Includes Mergiraf integration, conflict prediction, and structural merge.

---

## SmartMerger

Smart merge coordination using Mergiraf and structural aware merges.

### Methods

#### SmartMerger.**init**

```python
__init__(self: Any, mergiraf_path: str)
```

---

#### SmartMerger.merge_ast

```python
merge_ast(self: Any, base: Path, local: Path, remote: Path, output: Path)
```

Perform AST-aware merge using Mergiraf.

---

#### SmartMerger.merge_structural

```python
merge_structural(self: Any, base_file: Path, local_file: Path, remote_file: Path, output_file: Path)
```

Perform structural merge for JSON/YAML files.

---

#### SmartMerger.predict_conflicts

```python
predict_conflicts(self: Any, intents: list[dict[(str, Any)]])
```

Predict potential conflicts based on agent intents.

---

#### SmartMerger.resolve_imports

```python
resolve_imports(self: Any, content: str, lang: str)
```

Automatically resolve import union conflicts.

---

---

## merge_ast

```python
merge_ast(self: Any, base: Path, local: Path, remote: Path, output: Path)
```

Perform AST-aware merge using Mergiraf.

---

## merge_structural

```python
merge_structural(self: Any, base_file: Path, local_file: Path, remote_file: Path, output_file: Path)
```

Perform structural merge for JSON/YAML files.

---

## predict_conflicts

```python
predict_conflicts(self: Any, intents: list[dict[(str, Any)]])
```

Predict potential conflicts based on agent intents.

---

## resolve_imports

```python
resolve_imports(self: Any, content: str, lang: str)
```

Automatically resolve import union conflicts.

---
