# research_integration API Reference

> **Source**: `src/thegent/sync/research_integration.py`

Research sprawl integration.

---

## ResearchIntegration

Integrate research documents into work stream.

### Methods

#### ResearchIntegration.**init**

```python
__init__(self: Any, research_dir: Any)
```

Initialize research integration.

**Parameters**:

- `research_dir`: Research directory path

---

#### ResearchIntegration.extract_items

```python
extract_items(self: Any, research_file: Path)
```

Extract work items from research document.

**Parameters**:

- `research_file`: Research document path

**Returns**: List of extracted items

---

#### ResearchIntegration.integrate_all

```python
integrate_all(self: Any)
```

Integrate all research documents.

**Returns**: Integration results

---

#### ResearchIntegration.scan_research_docs

```python
scan_research_docs(self: Any)
```

Scan for research documents.

**Returns**: List of research document paths

---

---

## extract_items

```python
extract_items(self: Any, research_file: Path)
```

Extract work items from research document.

**Parameters**:

- `research_file`: Research document path

**Returns**: List of extracted items

---

## integrate_all

```python
integrate_all(self: Any)
```

Integrate all research documents.

**Returns**: Integration results

---

## scan_research_docs

```python
scan_research_docs(self: Any)
```

Scan for research documents.

**Returns**: List of research document paths

---
