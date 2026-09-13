# shm_context API Reference

> **Source**: `src/thegent/orchestration/shm_context.py`

WP-21002: Zero-Copy Context Sharing (Shared Memory).

MTSP-09/11: Efficiently share large context blocks across multi-tenant agent runs.

---

## ContextSharer

Manages context sharing across multiple agent runs (Multi-Tenancy).

### Methods

#### ContextSharer.**init**

```python
__init__(self: Any)
```

---

#### ContextSharer.get_context

```python
get_context(self: Any, session_id: str)
```

Retrieve or create a shared context for a session.

---

#### ContextSharer.release_context

```python
release_context(self: Any, session_id: str)
```

Clean up session context.

---

---

## ZeroCopyContext

Provides high-performance shared memory context for agent processes.

### Methods

#### ZeroCopyContext.**init**

```python
__init__(self: Any, size: int)
```

---

#### ZeroCopyContext.close

```python
close(self: Any)
```

Clean up resources.

---

#### ZeroCopyContext.read_context

```python
read_context(self: Any, size: int, offset: int)
```

Read context data directly from memory-mapped file.

---

#### ZeroCopyContext.write_context

```python
write_context(self: Any, data: bytes, offset: int)
```

Write context data directly to memory-mapped file.

---

---

## close

```python
close(self: Any)
```

Clean up resources.

---

## get_context

```python
get_context(self: Any, session_id: str)
```

Retrieve or create a shared context for a session.

---

## read_context

```python
read_context(self: Any, size: int, offset: int)
```

Read context data directly from memory-mapped file.

---

## release_context

```python
release_context(self: Any, session_id: str)
```

Clean up session context.

---

## write_context

```python
write_context(self: Any, data: bytes, offset: int)
```

Write context data directly to memory-mapped file.

---
