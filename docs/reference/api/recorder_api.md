# recorder API Reference

> **Source**: `src/thegent/trace/recorder.py`

TraceRecorder: Async, non-blocking trace recording for agent execution.

Records ToolCallRecord, DecisionRecord events to JSONL files with:

- Async write worker (non-blocking)
- Sensitive data redaction (API keys, passwords)
- Result truncation (>10MB cap)
- File I/O with optional compression
- TTL-based cleanup

---

## RecorderConfig

Configuration for TraceRecorder.

### Methods

---

## RedactionConfig

Configuration for sensitive data redaction.

### Methods

---

## TraceCleanup

TTL-based cleanup of old trace files.

### Methods

#### TraceCleanup.**init**

```python
__init__(self: Any, trace_dir: str, ttl_days: int)
```

Initialize cleanup manager.

**Parameters**:

- `trace_dir`: Directory containing trace files
- `ttl_days`: Keep traces for N days

---

---

## TraceRecorder

Records agent execution traces with async non-blocking writes.

### Methods

#### TraceRecorder.**init**

```python
__init__(self: Any, session_id: str, config: Any)
```

Initialize recorder.

**Parameters**:

- `session_id`: Unique session identifier
- `config`: RecorderConfig for customization

---

#### TraceRecorder.delete_trace

```python
delete_trace(self: Any)
```

Delete the trace file.

---

#### TraceRecorder.get_trace_file_size

```python
get_trace_file_size(self: Any)
```

Get current trace file size in bytes.

---

---

## TruncationConfig

Configuration for result truncation.

---

## delete_trace

```python
delete_trace(self: Any)
```

Delete the trace file.

---

## get_trace_file_size

```python
get_trace_file_size(self: Any)
```

Get current trace file size in bytes.

---
