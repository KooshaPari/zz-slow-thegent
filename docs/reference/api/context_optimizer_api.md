# context_optimizer API Reference

> **Source**: `src/thegent/security/context_optimizer.py`

Context and token optimization for LLM interactions.

Implements strategies to reduce token usage while maintaining context quality.

---

## ContextOptimizer

Optimizes context for LLM interactions.

### Methods

#### ContextOptimizer.**init**

```python
__init__(self: Any, max_tokens: Any, target_tokens: Any)
```

---

#### ContextOptimizer.compress_whitespace

```python
compress_whitespace(self: Any, text: str)
```

Compress excessive whitespace.

---

#### ContextOptimizer.estimate_tokens

```python
estimate_tokens(self: Any, text: str)
```

Estimate token count.

---

#### ContextOptimizer.optimize

```python
optimize(self: Any, context: str, remove_secrets: bool)
```

Optimize context for token usage.

**Parameters**:

- `context`: Original context
- `remove_secrets`: Whether to remove secrets

**Returns**: Optimized context

---

#### ContextOptimizer.optimize_prompt

```python
optimize_prompt(self: Any, prompt: str, system_prompt: Any)
```

Optimize prompt and system prompt separately.

**Returns**: (optimized_prompt, optimized_system_prompt)

---

#### ContextOptimizer.remove_secrets

```python
remove_secrets(self: Any, text: str)
```

Remove secrets and replace with variable names.

---

#### ContextOptimizer.truncate_smart

```python
truncate_smart(self: Any, text: str, max_tokens: int)
```

Smart truncation keeping important parts.

---

---

## compress_whitespace

```python
compress_whitespace(self: Any, text: str)
```

Compress excessive whitespace.

---

## estimate_tokens

```python
estimate_tokens(self: Any, text: str)
```

Estimate token count.

---

## optimize

```python
optimize(self: Any, context: str, remove_secrets: bool)
```

Optimize context for token usage.

**Parameters**:

- `context`: Original context
- `remove_secrets`: Whether to remove secrets

**Returns**: Optimized context

---

## optimize_context

```python
optimize_context(context: str, max_tokens: Any, remove_secrets: bool)
```

Public API: Optimize context.

---

## optimize_prompt

```python
optimize_prompt(self: Any, prompt: str, system_prompt: Any)
```

Optimize prompt and system prompt separately.

**Returns**: (optimized_prompt, optimized_system_prompt)

---

## remove_secrets

```python
remove_secrets(self: Any, text: str)
```

Remove secrets and replace with variable names.

---

## truncate_smart

```python
truncate_smart(self: Any, text: str, max_tokens: int)
```

Smart truncation keeping important parts.

---
