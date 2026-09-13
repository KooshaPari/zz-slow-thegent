# state_shm API Reference

> **Source**: `src/thegent/native/state_shm.py`

BKM-05: State-SHM -- CircuitBreaker + XP tracker in memory-mapped Rust.

This module provides `CircuitBreakerShm` and `XpTracker`, backed by the
`thegent_shm` PyO3 Rust extension when available. When the native extension
is not compiled/installed, a pure-Python in-process fallback is used so that
all callers continue to work without any code change.

Usage::

    from thegent.native.state_shm import CircuitBreakerShm, XpTracker

    shm_path = session_dir / "state.shm"
    cb  = CircuitBreakerShm(shm_path)
    xp  = XpTracker(shm_path)

    cb.record_failure("gpt-4o", category="model")
    if cb.is_open("gpt-4o", category="model"):
        ...  # circuit open, skip

    xp.award(100)
    level = xp.level

Environment variables:
THGENT_USE_NATIVE_SHM=0 Force pure-Python fallback even if extension available.

Native extension layout (crates/thegent-shm):
SHMInterface.record_failure(target, category_int)
SHMInterface.is_open(target, category_int, threshold, window_s, recovery_s)
SHMInterface.award_xp(amount)
SHMInterface.get_xp_state() -&gt; {"total_xp": int, "level": int} | None
SHMInterface.set_level(level)
SHMInterface.set_health_score(score)
SHMInterface.get_health_score()

---

## CircuitBreakerShm

Circuit breaker state backed by memory-mapped Rust SHM or pure-Python fallback.

States (mirroring Rust enum):
CLOSED (0) -- normal, requests flow through
OPEN (1) -- too many failures, requests blocked
HALF_OPEN (2)-- recovery window, one trial allowed

When the native extension is available, state is persisted to a memory-mapped
file at `path` (created automatically, size determined by Rust crate constants).
Multiple Python processes sharing the same `path` share state without locks.

When native is unavailable, state lives in process memory only (no cross-process
sharing) and is lost on restart -- identical semantics to the existing
`CircuitBreakerRegistry` but without file I/O.

### Methods

#### CircuitBreakerShm.**init**

```python
__init__(self: Any, path: Any, threshold: int, window_s: float, recovery_s: float)
```

---

#### CircuitBreakerShm.get_health_score

```python
get_health_score(self: Any)
```

Read global health score from SHM. Returns 0.0 on fallback or error.

---

#### CircuitBreakerShm.is_native

```python
is_native(self: Any)
```

True when backed by the Rust memory-mapped extension.

---

#### CircuitBreakerShm.is_open

```python
is_open(self: Any, target: str, category: str)
```

Return True when the circuit is OPEN (requests should be blocked).

Returns False when CLOSED (normal) or HALF_OPEN (trial allowed).

---

#### CircuitBreakerShm.record_failure

```python
record_failure(self: Any, target: str, category: str)
```

Record one failure event for `target` in `category`.

Increments the failure counter in the SHM region (or in-process dict).
Thread-safe via Rust atomics when native; GIL-protected when fallback.

---

#### CircuitBreakerShm.record_success

```python
record_success(self: Any, target: str, category: str)
```

Record a success -- clears the fallback window for target.

The native Rust SHM does not track successes independently (the sliding
window expires naturally); this method is a no-op on the native path and
clears the fallback store for the given target.

---

#### CircuitBreakerShm.set_health_score

```python
set_health_score(self: Any, score: float)
```

Write a global health score [0.0, 1.0] to SHM (native only, no-op on fallback).

---

#### CircuitBreakerShm.should_allow

```python
should_allow(self: Any, target: str, category: str)
```

Return True when the circuit is CLOSED or HALF_OPEN (request may proceed).

---

#### CircuitBreakerShm.state_int

```python
state_int(self: Any, target: str, category: str)
```

Return integer state code (CLOSED=0, OPEN=1, HALF_OPEN=2).

HALF_OPEN is approximated: if `is_open` returns False but failures
were recently at threshold, state is CLOSED (trial allowed).

---

---

## XpTracker

Experience points / level tracker backed by memory-mapped Rust SHM or pure-Python.

Provides a persistent XP accumulator: `award(amount)` increments total_xp and
recomputes `level` (1000 XP per level). When native, the value is persisted
across process restarts via the mmap'd file.

### Methods

#### XpTracker.**init**

```python
__init__(self: Any, path: Any)
```

---

#### XpTracker.award

```python
award(self: Any, amount: int)
```

Add `amount` XP. Level is recomputed automatically.

---

#### XpTracker.is_native

```python
is_native(self: Any)
```

True when backed by the Rust memory-mapped extension.

---

#### XpTracker.level

```python
level(self: Any)
```

Current level (1-based; increments every XP_PER_LEVEL points).

---

#### XpTracker.set_level

```python
set_level(self: Any, level: int)
```

Directly override level (useful for migration/seeding).

---

#### XpTracker.state

```python
state(self: Any)
```

Return `{"total_xp": int, "level": int}`.

---

#### XpTracker.total_xp

```python
total_xp(self: Any)
```

Total accumulated XP.

---

---

## \_PurePythonBreakerStore

In-process dict-backed circuit breaker state (fallback when native unavailable).

### Methods

#### \_PurePythonBreakerStore.**init**

```python
__init__(self: Any)
```

---

#### \_PurePythonBreakerStore.clear

```python
clear(self: Any, target: Any)
```

---

#### \_PurePythonBreakerStore.is_open

```python
is_open(self: Any, target: str, category: str, threshold: int, window_s: float, recovery_s: float)
```

---

#### \_PurePythonBreakerStore.record_failure

```python
record_failure(self: Any, target: str, category: str)
```

---

---

## \_PurePythonXpStore

In-process dict-backed XP/level state (fallback when native unavailable).

### Methods

#### \_PurePythonXpStore.**init**

```python
__init__(self: Any)
```

---

#### \_PurePythonXpStore.award

```python
award(self: Any, amount: int)
```

---

#### \_PurePythonXpStore.state

```python
state(self: Any)
```

---

---

## award

```python
award(self: Any, amount: int)
```

Add `amount` XP. Level is recomputed automatically.

---

## clear

```python
clear(self: Any, target: Any) -> None
```

---

## get_health_score

```python
get_health_score(self: Any)
```

Read global health score from SHM. Returns 0.0 on fallback or error.

---

## is_native

```python
is_native(self: Any)
```

True when backed by the Rust memory-mapped extension.

---

## is_native_available

Return True if the Rust thegent_shm extension is loaded and usable.

---

## is_open

```python
is_open(self: Any, target: str, category: str)
```

Return True when the circuit is OPEN (requests should be blocked).

Returns False when CLOSED (normal) or HALF_OPEN (trial allowed).

---

## level

```python
level(self: Any)
```

Current level (1-based; increments every XP_PER_LEVEL points).

---

## open_shm

```python
open_shm(path: Any)
```

Open (or create) an SHM region and return (CircuitBreakerShm, XpTracker).

Both objects share the same backing file so the Rust crate's single
`SHMInterface` layout is used for all regions (breakers + XP + health).

Example::

    cb, xp = open_shm(session_dir / "state.shm")
    cb.record_failure("claude-3-opus", category="model")
    xp.award(50)

---

## record_failure

```python
record_failure(self: Any, target: str, category: str)
```

Record one failure event for `target` in `category`.

Increments the failure counter in the SHM region (or in-process dict).
Thread-safe via Rust atomics when native; GIL-protected when fallback.

---

## record_success

```python
record_success(self: Any, target: str, category: str)
```

Record a success -- clears the fallback window for target.

The native Rust SHM does not track successes independently (the sliding
window expires naturally); this method is a no-op on the native path and
clears the fallback store for the given target.

---

## set_health_score

```python
set_health_score(self: Any, score: float)
```

Write a global health score [0.0, 1.0] to SHM (native only, no-op on fallback).

---

## set_level

```python
set_level(self: Any, level: int)
```

Directly override level (useful for migration/seeding).

---

## should_allow

```python
should_allow(self: Any, target: str, category: str)
```

Return True when the circuit is CLOSED or HALF_OPEN (request may proceed).

---

## state

```python
state(self: Any)
```

Return `{"total_xp": int, "level": int}`.

---

## state_int

```python
state_int(self: Any, target: str, category: str)
```

Return integer state code (CLOSED=0, OPEN=1, HALF_OPEN=2).

HALF_OPEN is approximated: if `is_open` returns False but failures
were recently at threshold, state is CLOSED (trial allowed).

---

## total_xp

```python
total_xp(self: Any)
```

Total accumulated XP.

---
