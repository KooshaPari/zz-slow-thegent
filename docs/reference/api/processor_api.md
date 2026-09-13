# processor API Reference

> **Source**: `src/thegent/agents/document/processor.py`

Document Processor

Processes markdown files from the queue, applying transformations,
analysis, and categorization.

---

## DocumentProcessor

Processes documents from the queue.

### Methods

#### DocumentProcessor.**init**

```python
__init__(self: Any, pipeline: Any)
```

---

#### DocumentProcessor.get_statistics

```python
get_statistics(self: Any)
```

Get processing statistics.

---

#### DocumentProcessor.process_batch

```python
process_batch(self: Any, filepaths: list[str])
```

Process multiple files.

---

#### DocumentProcessor.process_file

```python
process_file(self: Any, filepath: str)
```

Process a single file.

---

---

## ProcessingPipeline

Pipeline for processing documents through multiple stages.

### Methods

#### ProcessingPipeline.**init**

```python
__init__(self: Any)
```

---

#### ProcessingPipeline.add_stage

```python
add_stage(self: Any, stage: Callable[(Any, dict[(str, Any)])])
```

Add a processing stage to the pipeline.

---

#### ProcessingPipeline.process

```python
process(self: Any, filepath: Path)
```

Process a document through all stages.

---

---

## ProcessingResult

Result of processing a document.

### Methods

---

## ProcessingStatus

Status of document processing.

**Inherits from**: `Enum`

---

## add_stage

```python
add_stage(self: Any, stage: Callable[(Any, dict[(str, Any)])])
```

Add a processing stage to the pipeline.

---

## calculate_readability

```python
calculate_readability(filepath: Path)
```

Calculate basic readability metrics.

---

## compute_file_hash

```python
compute_file_hash(filepath: Path)
```

Compute file hash.

---

## count_lines

```python
count_lines(filepath: Path)
```

Count lines in file.

---

## extract_code_blocks

```python
extract_code_blocks(filepath: Path)
```

Extract code block information.

---

## extract_frontmatter

```python
extract_frontmatter(filepath: Path)
```

Extract YAML frontmatter from markdown file.

---

## extract_headings

```python
extract_headings(filepath: Path)
```

Extract headings from markdown file.

---

## extract_links

```python
extract_links(filepath: Path)
```

Extract links from markdown file.

---

## extract_metadata

```python
extract_metadata(filepath: Path)
```

Extract basic file metadata.

---

## get_statistics

```python
get_statistics(self: Any)
```

Get processing statistics.

---

## process

```python
process(self: Any, filepath: Path)
```

Process a document through all stages.

---

## process_batch

```python
process_batch(self: Any, filepaths: list[str])
```

Process multiple files.

---

## process_file

```python
process_file(self: Any, filepath: str)
```

Process a single file.

---
