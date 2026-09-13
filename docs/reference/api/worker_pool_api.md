# worker_pool API Reference

> **Source**: `src/thegent/orchestration/worker_pool.py`

MTSP-06: Persistent Python Worker Pool.

Reduces interpreter startup latency by keeping warm processes alive.

---

## PersistentWorkerPool

A pool of persistent Python processes for executing tasks (MTSP-06).

### Methods

#### PersistentWorkerPool.**init**

```python
__init__(self: Any, size: Any)
```

---

#### PersistentWorkerPool.get_instance

```python
get_instance(cls: Any, size: Any)
```

---

#### PersistentWorkerPool.start

```python
start(self: Any)
```

Initialize the process pool.

---

#### PersistentWorkerPool.stop

```python
stop(self: Any)
```

Shut down the pool.

---

---

## get_instance

```python
get_instance(cls: Any, size: Any) -> PersistentWorkerPool
```

---

## get_worker_pool

Helper for dependency injection.

---

## start

```python
start(self: Any)
```

Initialize the process pool.

---

## stop

```python
stop(self: Any)
```

Shut down the pool.

---
