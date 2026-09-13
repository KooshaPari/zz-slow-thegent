# lock_free API Reference

> **Source**: `src/thegent/orchestration/lock_free.py`

WP-21003: Lock-Free Agent State Transitions.

MTSP-13/14: Use atomic versioned state to allow high-concurrency multi-tenant access
without traditional mutex locking overhead.

---

## AtomicState

A versioned state object for lock-free transitions.

---

## LockFreeStateManager

Manages agent state transitions using Compare-And-Swap (CAS) principles.

### Methods

#### LockFreeStateManager.**init**

```python
__init__(self: Any)
```

---

#### LockFreeStateManager.compare_and_swap

```python
compare_and_swap(self: Any, key: str, expected_version: int, new_value: Any)
```

Perform a lock-free transition.

Returns True if transition successful (version matched), False otherwise.

---

#### LockFreeStateManager.get_state

```python
get_state(self: Any, key: str)
```

Get the current versioned state.

---

#### LockFreeStateManager.set_state

```python
set_state(self: Any, key: str, value: Any)
```

Set state with a new version.

---

---

## compare_and_swap

```python
compare_and_swap(self: Any, key: str, expected_version: int, new_value: Any)
```

Perform a lock-free transition.

Returns True if transition successful (version matched), False otherwise.

---

## get_state

```python
get_state(self: Any, key: str)
```

Get the current versioned state.

---

## set_state

```python
set_state(self: Any, key: str, value: Any)
```

Set state with a new version.

---
