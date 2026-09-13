# adapters API Reference

> **Source**: `src/thegent/contracts/adapters.py`

Output adapter protocol and scaffolding for provider-specific normalization.

Adapters convert copilot/gemini/codex/claude (and other) outputs into
CanonicalStructuredMessage for orchestration pipelines.

---

## AdapterResult

Result of adapter normalization.

---

## GenericOutputAdapter

Default adapter using output_parser.extract_condensed for all providers.

### Methods

#### GenericOutputAdapter.**init**

```python
__init__(self: Any, provider: str)
```

---

#### GenericOutputAdapter.normalize

```python
normalize(self: Any, raw: Any, context: Any)
```

---

#### GenericOutputAdapter.provider

```python
provider(self: Any)
```

---

---

## OutputAdapter

Protocol for provider output adapters.

Each provider (copilot, gemini, codex, claude, etc.) should implement
an adapter that normalizes raw output into CanonicalStructuredMessage.

**Inherits from**: `Protocol`

### Methods

#### OutputAdapter.normalize

```python
normalize(self: Any, raw: Any, context: Any)
```

Normalize raw provider output to CSM.

**Parameters**:

- `raw`: Raw stdout string or parsed dict from provider.
- `context`: Optional context (run_id, chunk_id, etc.).

**Returns**: AdapterResult with CSM and confidence.

---

#### OutputAdapter.provider

```python
provider(self: Any)
```

Provider identifier (e.g. copilot, gemini, codex, claude).

---

---

## XMLOutputAdapter

Base adapter for XML-structured agent outputs.

### Methods

#### XMLOutputAdapter.**init**

```python
__init__(self: Any, provider_name: str)
```

---

#### XMLOutputAdapter.normalize

```python
normalize(self: Any, raw: Any, context: Any)
```

---

#### XMLOutputAdapter.provider

```python
provider(self: Any)
```

---

---

## get_adapter

```python
get_adapter(provider: str)
```

Get adapter for provider, or None if not registered.

---

## get_tag

---

## normalize

```python
normalize(self: Any, raw: Any, context: Any) -> AdapterResult
```

---

## normalize_output

```python
normalize_output(provider: str, raw: Any, context: Any, allow_fallback: bool)
```

Normalize provider output via registered adapter, or fallback to plain extraction.

If no adapter is registered or if adapter fails and allow_fallback is True,
returns a best-effort CSM.

---

## provider

```python
provider(self: Any) -> str
```

---

## register_adapter

```python
register_adapter(provider: str, adapter: OutputAdapter)
```

Register an output adapter for a provider.

---
