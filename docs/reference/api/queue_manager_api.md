# queue_manager API Reference

> **Source**: `src/thegent/agents/document/queue_manager.py`

Queue Manager for Document Processing

Manages the processing queue, tracks progress, and provides queue operations
for iterating through documents by month and location.

---

## QueueManager

Manages document processing queue.

### Methods

#### QueueManager.**init**

```python
__init__(self: Any, queue_file: Path, state_file: Any)
```

---

#### QueueManager.get_month_files

```python
get_month_files(self: Any, month: str, location: Any)
```

Get all files for a specific month, optionally filtered by location.

---

#### QueueManager.get_next_month

```python
get_next_month(self: Any)
```

Get the next month to process.

---

#### QueueManager.get_summary

```python
get_summary(self: Any)
```

Get queue summary statistics.

---

#### QueueManager.get_unprocessed_files

```python
get_unprocessed_files(self: Any, month: Any, location: Any)
```

Get list of unprocessed files.

---

#### QueueManager.list_months

```python
list_months(self: Any)
```

List all months in the queue.

---

#### QueueManager.load_queue

```python
load_queue(self: Any)
```

Load queue data from file.

---

#### QueueManager.mark_file_failed

```python
mark_file_failed(self: Any, filepath: str)
```

Mark a file as failed.

---

#### QueueManager.mark_file_processed

```python
mark_file_processed(self: Any, filepath: str)
```

Mark a file as processed.

---

#### QueueManager.mark_file_skipped

```python
mark_file_skipped(self: Any, filepath: str)
```

Mark a file as skipped.

---

#### QueueManager.mark_month_complete

```python
mark_month_complete(self: Any, month: str, location: Any)
```

Mark a month/location as complete.

---

---

## QueueState

State tracking for queue processing.

### Methods

#### QueueState.from_dict

```python
from_dict(cls: Any, data: dict)
```

Create from dictionary.

---

#### QueueState.mark_failed

```python
mark_failed(self: Any, filepath: str)
```

Mark a file as failed.

---

#### QueueState.mark_processed

```python
mark_processed(self: Any, filepath: str)
```

Mark a file as processed.

---

#### QueueState.mark_skipped

```python
mark_skipped(self: Any, filepath: str)
```

Mark a file as skipped.

---

#### QueueState.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---

---

## from_dict

```python
from_dict(cls: Any, data: dict)
```

Create from dictionary.

---

## get_month_files

```python
get_month_files(self: Any, month: str, location: Any)
```

Get all files for a specific month, optionally filtered by location.

---

## get_next_month

```python
get_next_month(self: Any)
```

Get the next month to process.

---

## get_summary

```python
get_summary(self: Any)
```

Get queue summary statistics.

---

## get_unprocessed_files

```python
get_unprocessed_files(self: Any, month: Any, location: Any)
```

Get list of unprocessed files.

---

## list_months

```python
list_months(self: Any)
```

List all months in the queue.

---

## load_queue

```python
load_queue(self: Any)
```

Load queue data from file.

---

## mark_failed

```python
mark_failed(self: Any, filepath: str)
```

Mark a file as failed.

---

## mark_file_failed

```python
mark_file_failed(self: Any, filepath: str)
```

Mark a file as failed.

---

## mark_file_processed

```python
mark_file_processed(self: Any, filepath: str)
```

Mark a file as processed.

---

## mark_file_skipped

```python
mark_file_skipped(self: Any, filepath: str)
```

Mark a file as skipped.

---

## mark_month_complete

```python
mark_month_complete(self: Any, month: str, location: Any)
```

Mark a month/location as complete.

---

## mark_processed

```python
mark_processed(self: Any, filepath: str)
```

Mark a file as processed.

---

## mark_skipped

```python
mark_skipped(self: Any, filepath: str)
```

Mark a file as skipped.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---
