# context API Reference

> **Source**: `src/thegent/orchestration/context.py`

Context management and semantic compression for thegent (WP-5001).

---

## ContextCompressor

WP-5001: Manages L1-L4 memory tiers and triggers semantic compression.

### Methods

#### ContextCompressor.**init**

```python
__init__(self: Any, session_dir: Path, threshold_pct: float)
```

---

#### ContextCompressor.generate_continuity_packet

```python
generate_continuity_packet(self: Any, intent: str, decisions: list[str], risks: list[str], context_files: list[Path])
```

Create a compressed essence of progress for handoffs.

---

#### ContextCompressor.prune_context

```python
prune_context(self: Any, conversation: list[dict[(str, Any)]])
```

WP-5001: Priority-based pruning of conversation history.

---

#### ContextCompressor.should_compress

```python
should_compress(self: Any, current_tokens: int, max_tokens: int)
```

True if current token usage exceeds threshold.

---

---

## generate_continuity_packet

```python
generate_continuity_packet(self: Any, intent: str, decisions: list[str], risks: list[str], context_files: list[Path])
```

Create a compressed essence of progress for handoffs.

---

## prune_context

```python
prune_context(self: Any, conversation: list[dict[(str, Any)]])
```

WP-5001: Priority-based pruning of conversation history.

---

## should_compress

```python
should_compress(self: Any, current_tokens: int, max_tokens: int)
```

True if current token usage exceeds threshold.

---
