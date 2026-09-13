# cache_v2 API Reference

> **Source**: `src/thegent/infra/cache_v2.py`

Phase 9: Request Coalescing v2 implementation.

Includes Singleflight, inotify cache invalidation, and heat-based LRU.

---

## CacheInvalidator

inotify-based cache invalidation.

### Methods

#### CacheInvalidator.**init**

```python
__init__(self: Any, cache: Any)
```

---

#### CacheInvalidator.stop

```python
stop(self: Any)
```

---

#### CacheInvalidator.watch

```python
watch(self: Any, directory: Path)
```

---

---

## CrossProcessSingleflight

Implementation of Singleflight pattern across processes using file locks.

### Methods

#### CrossProcessSingleflight.**init**

```python
__init__(self: Any, coordination_dir: Path)
```

---

#### CrossProcessSingleflight.do

```python
do(self: Any, key: str, func: Callable[(Any, Any)], ttl: int)
```

Execute func for key, coalescing concurrent calls across processes.

---

---

## Handler

**Inherits from**: `watchdog.events.FileSystemEventHandler`

### Methods

#### Handler.**init**

```python
__init__(self: Any, cache: Any)
```

---

#### Handler.on_modified

```python
on_modified(self: Any, event: Any)
```

---

---

## HeatBasedLRU

LRU cache with heat-based eviction (frequency + decay).

### Methods

#### HeatBasedLRU.**init**

```python
__init__(self: Any, capacity: int, decay_factor: float)
```

---

#### HeatBasedLRU.get

```python
get(self: Any, key: str)
```

---

#### HeatBasedLRU.put

```python
put(self: Any, key: str, value: Any)
```

---

---

## Singleflight

Implementation of Singleflight pattern to prevent duplicate requests.

### Methods

#### Singleflight.**init**

```python
__init__(self: Any)
```

---

#### Singleflight.do

```python
do(self: Any, key: str, func: Callable[(Any, Any)])
```

Execute func for key, coalescing concurrent calls.

---

---

## do

```python
do(self: Any, key: str, func: Callable[(Any, Any)], ttl: int)
```

Execute func for key, coalescing concurrent calls across processes.

---

## get

```python
get(self: Any, key: str) -> Any
```

---

## on_modified

```python
on_modified(self: Any, event: Any)
```

---

## put

```python
put(self: Any, key: str, value: Any)
```

---

## stop

```python
stop(self: Any)
```

---

## watch

```python
watch(self: Any, directory: Path)
```

---
