# analyzer API Reference

> **Source**: `src/thegent/agents/document/analyzer.py`

Document Analyzer

Analyzes markdown files to categorize, extract metadata, and identify
patterns or characteristics.

---

## DocumentAnalysis

Analysis results for a document.

### Methods

#### DocumentAnalysis.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

---

---

## DocumentAnalyzer

Analyzes markdown documents.

### Methods

#### DocumentAnalyzer.**init**

```python
__init__(self: Any)
```

---

#### DocumentAnalyzer.analyze

```python
analyze(self: Any, filepath: Path)
```

Analyze a markdown file.

---

---

## DocumentCategory

Categories for documents.

**Inherits from**: `Enum`

---

## analyze

```python
analyze(self: Any, filepath: Path)
```

Analyze a markdown file.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

---
