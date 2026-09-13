# guardrails API Reference

> **Source**: `src/thegent/security/guardrails.py`

Comprehensive security guardrails for AI agents.

Implements multiple layers of protection:

- Command validation and sanitization
- Input/output filtering
- Rate limiting
- Token optimization
- Secret management
- Invariant enforcement
- Context window management

---

## CommandValidator

Validates and sanitizes commands before execution.

### Methods

#### CommandValidator.sanitize_path

```python
sanitize_path(path: str)
```

Sanitize file path.

**Returns**: (is_valid, sanitized_path_or_error)

---

#### CommandValidator.validate_command

```python
validate_command(cmd: Any)
```

Validate command safety.

**Returns**: (is_valid, error_message)

---

---

## Guardrails

Main guardrails orchestrator.

### Methods

#### Guardrails.**init**

```python
__init__(self: Any)
```

---

#### Guardrails.check_invariant

```python
check_invariant(self: Any, invariant_name: str, value: Any)
```

Check system invariant.

**Parameters**:

- `invariant_name`: Name of invariant to check
- `value`: Value to check against invariant

**Returns**: (is_valid, error_message)

---

#### Guardrails.optimize_context

```python
optimize_context(self: Any, context: str, max_tokens: Any)
```

Optimize context for token usage.

---

#### Guardrails.validate_and_sanitize_command

```python
validate_and_sanitize_command(self: Any, cmd: Any, operation_type: str)
```

Validate command and check rate limits.

**Returns**: (is_allowed, sanitized_command_or_error, error_message)

---

---

## RateLimit

Rate limit configuration.

### Methods

#### RateLimit.check

```python
check(self: Any)
```

Check if rate limit is exceeded.

---

#### RateLimit.reset

```python
reset(self: Any)
```

Reset rate limit.

---

---

## RateLimiter

Rate limiter for operations.

### Methods

#### RateLimiter.**init**

```python
__init__(self: Any)
```

---

#### RateLimiter.add_limit

```python
add_limit(self: Any, key: str, max_calls: int, window_seconds: int)
```

Add a rate limit.

---

#### RateLimiter.check

```python
check(self: Any, key: str)
```

Check if operation is allowed.

---

#### RateLimiter.reset

```python
reset(self: Any, key: str)
```

Reset rate limit for key.

---

---

## SecretManager

Manages secrets using environment variables.

### Methods

#### SecretManager.get_secret

```python
get_secret(name: str, default: Any)
```

Get secret from environment variable.

---

#### SecretManager.mask_secret

```python
mask_secret(value: str)
```

Mask secret value for logging.

---

#### SecretManager.validate_secret_present

```python
validate_secret_present(name: str)
```

Check if secret is present.

---

---

## SecurityInvariant

System invariants that must always hold true.

---

## TokenOptimizer

Optimizes token usage through context management.

### Methods

#### TokenOptimizer.compress_context

```python
compress_context(context: str, max_tokens: int)
```

Compress context to fit within token limit.

---

#### TokenOptimizer.estimate_tokens

```python
estimate_tokens(text: str)
```

Estimate token count (rough: ~4 chars per token).

---

#### TokenOptimizer.optimize_prompt

```python
optimize_prompt(prompt: str, max_tokens: Any)
```

Optimize prompt by removing secrets and compressing.

---

#### TokenOptimizer.remove_secrets

```python
remove_secrets(text: str)
```

Remove secrets from text (replace with variables).

---

---

## add_limit

```python
add_limit(self: Any, key: str, max_calls: int, window_seconds: int)
```

Add a rate limit.

---

## check

```python
check(self: Any, key: str)
```

Check if operation is allowed.

---

## check_invariant

```python
check_invariant(self: Any, invariant_name: str, value: Any)
```

Check system invariant.

**Parameters**:

- `invariant_name`: Name of invariant to check
- `value`: Value to check against invariant

**Returns**: (is_valid, error_message)

---

## check_rate_limit

```python
check_rate_limit(operation_type: str)
```

Public API: Check if operation is within rate limit.

---

## compress_context

```python
compress_context(context: str, max_tokens: int)
```

Compress context to fit within token limit.

---

## estimate_tokens

```python
estimate_tokens(text: str)
```

Estimate token count (rough: ~4 chars per token).

---

## get_secret

```python
get_secret(name: str, default: Any)
```

Get secret from environment variable.

---

## mask_secret

```python
mask_secret(value: str)
```

Mask secret value for logging.

---

## optimize_context

```python
optimize_context(self: Any, context: str, max_tokens: Any)
```

Optimize context for token usage.

---

## optimize_prompt

```python
optimize_prompt(prompt: str, max_tokens: Any)
```

Optimize prompt by removing secrets and compressing.

---

## remove_secrets

```python
remove_secrets(text: str)
```

Remove secrets from text (replace with variables).

---

## reset

```python
reset(self: Any, key: str)
```

Reset rate limit for key.

---

## sanitize_path

```python
sanitize_path(path: str)
```

Sanitize file path.

**Returns**: (is_valid, sanitized_path_or_error)

---

## validate_and_sanitize_command

```python
validate_and_sanitize_command(self: Any, cmd: Any, operation_type: str)
```

Validate command and check rate limits.

**Returns**: (is_allowed, sanitized_command_or_error, error_message)

---

## validate_command

```python
validate_command(cmd: Any)
```

Validate command safety.

**Returns**: (is_valid, error_message)

---

## validate_secret_present

```python
validate_secret_present(name: str)
```

Check if secret is present.

---
