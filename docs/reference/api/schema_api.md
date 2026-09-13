# schema API Reference

> **Source**: `src/thegent/trace/schema.py`

Trace data model and schema definitions.

Defines JSONL trace format with three core record types:

- ToolCallRecord: Captures tool invocations (bash, read, write, etc.)
- DecisionRecord: Captures LLM decisions (model, routing, parameters)
- SessionRecord: Metadata about a trace session

---

## DecisionRecord

Record of an LLM decision or routing choice.

### Methods

#### DecisionRecord.from_dict

```python
from_dict(data: dict[(str, Any)])
```

Construct from dictionary.

---

#### DecisionRecord.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for JSON serialization.

---

---

## SessionRecord

Metadata about a trace session.

Appears once at the start of each trace file.

### Methods

#### SessionRecord.from_dict

```python
from_dict(data: dict[(str, Any)])
```

Construct from dictionary.

---

#### SessionRecord.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for JSON serialization.

---

---

## ToolCallRecord

Record of a single tool invocation.

### Methods

#### ToolCallRecord.from_dict

```python
from_dict(data: dict[(str, Any)])
```

Construct from dictionary (e.g., JSON parsed).

---

#### ToolCallRecord.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for JSON serialization.

---

---

## TraceFile

JSONL trace file reader/writer with optional compression.

### Methods

#### TraceFile.**init**

```python
__init__(self: Any, path: str, compression: Any)
```

Initialize trace file handler.

**Parameters**:

- `path`: File path for trace
- `compression`: 'gzip', 'zstd', or None for uncompressed

---

#### TraceFile.delete

```python
delete(self: Any)
```

Delete trace file.

---

#### TraceFile.get_file_size

```python
get_file_size(self: Any)
```

Get trace file size in bytes.

---

#### TraceFile.read_records

```python
read_records(self: Any)
```

Read all records from trace file.

---

#### TraceFile.write_record

```python
write_record(self: Any, record: Any)
```

Append a record to the trace file.

---

---

## TraceRecord

Union type for any trace record (ToolCall, Decision, Session).

### Methods

#### TraceRecord.from_dict

```python
from_dict(data: dict[(str, Any)])
```

Infer record type and construct from dictionary.

---

---

## delete

```python
delete(self: Any)
```

Delete trace file.

---

## from_dict

```python
from_dict(data: dict[(str, Any)])
```

Infer record type and construct from dictionary.

---

## get_file_size

```python
get_file_size(self: Any)
```

Get trace file size in bytes.

---

## read_records

```python
read_records(self: Any)
```

Read all records from trace file.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for JSON serialization.

---

## validate_record

```python
validate_record(record: Any)
```

Validate a trace record.

Checks:

- Required fields present
- Types correct
- Timestamps valid ISO 8601

Returns True if valid, False otherwise.

---

## write_record

```python
write_record(self: Any, record: Any)
```

Append a record to the trace file.

---
