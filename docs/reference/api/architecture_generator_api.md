# architecture_generator API Reference

> **Source**: `src/thegent/docgen/architecture_generator.py`

Auto-generate architecture diagrams from code.

---

## ArchitectureGenerator

Generate architecture diagrams from code structure.

### Methods

#### ArchitectureGenerator.**init**

```python
__init__(self: Any)
```

Initialize architecture generator.

---

#### ArchitectureGenerator.analyze_structure

```python
analyze_structure(self: Any, root_path: Path)
```

Analyze code structure.

**Parameters**:

- `root_path`: Root directory to analyze

**Returns**: Structure analysis

---

#### ArchitectureGenerator.generate_mermaid

```python
generate_mermaid(self: Any, structure: dict[(str, Any)])
```

Generate Mermaid diagram.

**Parameters**:

- `structure`: Structure dictionary

**Returns**: Mermaid diagram code

---

---

## add_nodes

```python
add_nodes(d: dict[(str, Any)], prefix: str)
```

---

## analyze_structure

```python
analyze_structure(self: Any, root_path: Path)
```

Analyze code structure.

**Parameters**:

- `root_path`: Root directory to analyze

**Returns**: Structure analysis

---

## generate_mermaid

```python
generate_mermaid(self: Any, structure: dict[(str, Any)])
```

Generate Mermaid diagram.

**Parameters**:

- `structure`: Structure dictionary

**Returns**: Mermaid diagram code

---
