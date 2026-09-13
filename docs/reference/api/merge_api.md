# merge API Reference

> **Source**: `src/thegent/mesh/merge.py`

Smart merge and conflict resolution for the agent mesh.

---

## SmartMerge

Smart merge and conflict resolution (SCLI-P5.1–P5.4).

### Methods

#### SmartMerge.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### SmartMerge.merge_ast_aware

```python
merge_ast_aware(self: Any, base: Path, ours: Path, theirs: Path, output: Path)
```

Mergiraf integration (AST-aware merge) (SCLI-P5.1).

---

#### SmartMerge.merge_structural

```python
merge_structural(self: Any, path_a: Path, path_b: Path, output: Path)
```

JSON/YAML structural merge (SCLI-P5.4).

---

#### SmartMerge.predict_conflicts

```python
predict_conflicts(self: Any, agent_intents: list[dict])
```

Conflict prediction before commit (trial merge from intents) (SCLI-P5.2).

---

#### SmartMerge.resolve_imports

```python
resolve_imports(self: Any, content_a: str, content_b: str, language: str)
```

Import union auto-resolution (SCLI-P5.3).

---

---

## merge_ast_aware

```python
merge_ast_aware(self: Any, base: Path, ours: Path, theirs: Path, output: Path)
```

Mergiraf integration (AST-aware merge) (SCLI-P5.1).

---

## merge_structural

```python
merge_structural(self: Any, path_a: Path, path_b: Path, output: Path)
```

JSON/YAML structural merge (SCLI-P5.4).

---

## predict_conflicts

```python
predict_conflicts(self: Any, agent_intents: list[dict])
```

Conflict prediction before commit (trial merge from intents) (SCLI-P5.2).

---

## resolve_imports

```python
resolve_imports(self: Any, content_a: str, content_b: str, language: str)
```

Import union auto-resolution (SCLI-P5.3).

---
