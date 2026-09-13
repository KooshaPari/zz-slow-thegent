# llm_output API Reference

> **Source**: `src/thegent/docgen/llm_output.py`

Generate LLM-friendly documentation (.llms.txt).

---

## LLMOutputGenerator

Generate LLM-friendly documentation format.

### Methods

#### LLMOutputGenerator.**init**

```python
__init__(self: Any, output_dir: Any)
```

Initialize LLM output generator.

**Parameters**:

- `output_dir`: Output directory for .llms.txt files

---

#### LLMOutputGenerator.generate_batch

```python
generate_batch(self: Any, md_files: list[Path])
```

Generate .llms.txt files for multiple markdown files.

**Parameters**:

- `md_files`: List of markdown files

**Returns**: List of generated .llms.txt file paths

---

#### LLMOutputGenerator.generate_from_markdown

```python
generate_from_markdown(self: Any, md_file: Path)
```

Generate .llms.txt from markdown file.

**Parameters**:

- `md_file`: Markdown file path

**Returns**: Path to generated .llms.txt file

---

---

## generate_batch

```python
generate_batch(self: Any, md_files: list[Path])
```

Generate .llms.txt files for multiple markdown files.

**Parameters**:

- `md_files`: List of markdown files

**Returns**: List of generated .llms.txt file paths

---

## generate_from_markdown

```python
generate_from_markdown(self: Any, md_file: Path)
```

Generate .llms.txt from markdown file.

**Parameters**:

- `md_file`: Markdown file path

**Returns**: Path to generated .llms.txt file

---
