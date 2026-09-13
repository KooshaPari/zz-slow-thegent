# parallel_generation API Reference

> **Source**: `src/thegent/docgen/parallel_generation.py`

Parallel documentation generation.

---

## ParallelGenerator

Generate documentation in parallel.

### Methods

#### ParallelGenerator.**init**

```python
__init__(self: Any, max_workers: int, use_processes: bool)
```

Initialize parallel generator.

**Parameters**:

- `max_workers`: Maximum number of workers
- `use_processes`: Use processes instead of threads

---

#### ParallelGenerator.generate_batch

```python
generate_batch(self: Any, files: list[Path], generator_func: Callable[(Any, dict[(str, Any)])], batch_size: int)
```

Generate documentation in batches.

**Parameters**:

- `files`: List of files to process
- `generator_func`: Function to generate docs
- `batch_size`: Size of each batch

**Returns**: List of generation results

---

#### ParallelGenerator.generate_parallel

```python
generate_parallel(self: Any, files: list[Path], generator_func: Callable[(Any, dict[(str, Any)])])
```

Generate documentation in parallel.

**Parameters**:

- `files`: List of files to process
- `generator_func`: Function to generate docs for each file

**Returns**: List of generation results

---

---

## generate_batch

```python
generate_batch(self: Any, files: list[Path], generator_func: Callable[(Any, dict[(str, Any)])], batch_size: int)
```

Generate documentation in batches.

**Parameters**:

- `files`: List of files to process
- `generator_func`: Function to generate docs
- `batch_size`: Size of each batch

**Returns**: List of generation results

---

## generate_parallel

```python
generate_parallel(self: Any, files: list[Path], generator_func: Callable[(Any, dict[(str, Any)])])
```

Generate documentation in parallel.

**Parameters**:

- `files`: List of files to process
- `generator_func`: Function to generate docs for each file

**Returns**: List of generation results

---
