# shm_manager API Reference

> **Source**: `src/thegent/infra/shm_manager.py`

## SHMManager

Python wrapper for the high-performance Rust SHM mesh.

### Methods

#### SHMManager.**init**

```python
__init__(self: Any, shm_path: Any)
```

---

#### SHMManager.award_xp

```python
award_xp(self: Any, amount: int)
```

---

#### SHMManager.get_health_score

```python
get_health_score(self: Any)
```

---

#### SHMManager.get_provider_metrics

```python
get_provider_metrics(self: Any, provider: str)
```

---

#### SHMManager.get_router_metrics

```python
get_router_metrics(self: Any)
```

---

#### SHMManager.get_xp_state

```python
get_xp_state(self: Any)
```

---

#### SHMManager.record_failure

```python
record_failure(self: Any, target: str, category: int)
```

---

#### SHMManager.record_resource_usage

```python
record_resource_usage(self: Any, pid: int, cpu_percent: float, memory_kb: int)
```

---

#### SHMManager.set_health_score

```python
set_health_score(self: Any, score: float)
```

---

#### SHMManager.update_provider_metrics

```python
update_provider_metrics(self: Any, provider: str, request_count: int, success_count: int, latency_ms: int)
```

---

#### SHMManager.update_router_metrics

```python
update_router_metrics(self: Any, lifecycle_inc: int, thegent_inc: int, changes_inc: int, hysteresis_inc: int)
```

---

---

## award_xp

```python
award_xp(self: Any, amount: int)
```

---

## get_health_score

```python
get_health_score(self: Any) -> float
```

---

## get_provider_metrics

```python
get_provider_metrics(self: Any, provider: str) -> Any
```

---

## get_router_metrics

```python
get_router_metrics(self: Any) -> Any
```

---

## get_xp_state

```python
get_xp_state(self: Any) -> Any
```

---

## record_failure

```python
record_failure(self: Any, target: str, category: int)
```

---

## record_resource_usage

```python
record_resource_usage(self: Any, pid: int, cpu_percent: float, memory_kb: int)
```

---

## set_health_score

```python
set_health_score(self: Any, score: float)
```

---

## update_provider_metrics

```python
update_provider_metrics(self: Any, provider: str, request_count: int, success_count: int, latency_ms: int)
```

---

## update_router_metrics

```python
update_router_metrics(self: Any, lifecycle_inc: int, thegent_inc: int, changes_inc: int, hysteresis_inc: int)
```

---
