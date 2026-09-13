# breaker API Reference

> **Source**: `src/thegent/hooks/breaker.py`

Implement breaker-check/record/reset subcommands (circuit breaker).

---

## BreakerSubcommands

Circuit breaker subcommands.

### Methods

#### BreakerSubcommands.**init**

```python
__init__(self: Any)
```

Initialize breaker subcommands.

---

#### BreakerSubcommands.check

```python
check(self: Any, breaker_id: str)
```

Check circuit breaker status.

**Parameters**:

- `breaker_id`: Breaker identifier

**Returns**: Breaker status

---

#### BreakerSubcommands.record

```python
record(self: Any, breaker_id: str, success: bool)
```

Record breaker event.

**Parameters**:

- `breaker_id`: Breaker identifier
- `success`: Whether operation succeeded

---

#### BreakerSubcommands.reset

```python
reset(self: Any, breaker_id: str)
```

Reset circuit breaker.

**Parameters**:

- `breaker_id`: Breaker identifier

---

---

## check

```python
check(self: Any, breaker_id: str)
```

Check circuit breaker status.

**Parameters**:

- `breaker_id`: Breaker identifier

**Returns**: Breaker status

---

## record

```python
record(self: Any, breaker_id: str, success: bool)
```

Record breaker event.

**Parameters**:

- `breaker_id`: Breaker identifier
- `success`: Whether operation succeeded

---

## reset

```python
reset(self: Any, breaker_id: str)
```

Reset circuit breaker.

**Parameters**:

- `breaker_id`: Breaker identifier

---
