# breakers API Reference

> **Source**: `src/thegent/governance/breakers.py`

WP-5005: Usage spike circuit breakers.

---

## CircuitBreaker

Breaks the flow when usage spikes are detected.

### Methods

#### CircuitBreaker.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### CircuitBreaker.check_spike

```python
check_spike(self: Any, current_batch_cost: float)
```

Check if the current cost batch causes a spike.

---

#### CircuitBreaker.is_tripped

```python
is_tripped(self: Any)
```

Return True if any active breaker is tripped.

---

#### CircuitBreaker.trip

```python
trip(self: Any, reason: str, value: float)
```

Trip the circuit breaker.

---

---

## check_spike

```python
check_spike(self: Any, current_batch_cost: float)
```

Check if the current cost batch causes a spike.

---

## is_tripped

```python
is_tripped(self: Any)
```

Return True if any active breaker is tripped.

---

## trip

```python
trip(self: Any, reason: str, value: float)
```

Trip the circuit breaker.

---
