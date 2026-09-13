# Performance Tuning Guide

This guide covers the performance optimizations implemented in thegent.

## Overview

The following performance features are available:

| Feature           | Module              | Purpose                                  |
| ----------------- | ------------------- | ---------------------------------------- |
| Multi-Level Cache | `thegent.cache`     | Reduce API calls, improve response time  |
| Dynamic Scaling   | `thegent.scaling`   | Adaptive concurrency control             |
| Shell Timeout     | `thegent.shell`     | Configurable command timeouts with retry |
| Process Cleanup   | `thegent.process`   | Prevent resource leaks                   |
| Teammate System   | `thegent.teammates` | Parallel task delegation                 |

## Caching

### L1 Memory Cache

Fast in-memory cache with TTL:

```python
from thegent.cache import L1MemoryCache

cache = L1MemoryCache(ttl=60.0, max_size=1000)
cache.set("key", {"data": "value"})
result = cache.get("key")
```

### L2 Disk Cache

Persistent SQLite-backed cache:

```python
from thegent.cache import L2DiskCache

cache = L2DiskCache(cache_dir=".cache/l2", ttl=3600.0)
cache.set("key", {"data": "value"})
result = cache.get("key")
```

### Tiered Cache

Combined L1 + L2 with automatic promotion:

```python
from thegent.cache import TieredCache

cache = TieredCache(l1_ttl=60.0, l2_ttl=3600.0)
cache.set("key", "value")  # Sets in both tiers
result = cache.get("key")  # Checks L1, then L2, promotes to L1
```

### Cache Statistics

```python
stats = cache.stats()
# {"l1": {"hits": 100, "misses": 10, "hit_rate": 0.91}, "l2": {...}}
```

## Dynamic Scaling

### Resource Monitoring

```python
from thegent.scaling import ResourceMonitor

monitor = ResourceMonitor()
sample = monitor.sample()

print(f"CPU: {sample.cpu_percent}%")
print(f"Memory: {sample.memory_percent}%")
print(f"Pressure: {sample.pressure_score}")
```

### Dynamic Concurrency

```python
from thegent.scaling import DynamicLimiter

limiter = DynamicLimiter(min_limit=1, max_limit=100, initial_limit=10)

# Adjusts automatically based on system pressure
limiter.acquire()
print(f"Current limit: {limiter.current_limit}")
```

## Shell Execution

### Configurable Timeouts

```python
from thegent.shell import ShellExecutor, ShellConfig

config = ShellConfig(
    default_timeout=300.0,  # 5 minutes
    max_retries=3,
)

executor = ShellExecutor(config)
result = executor.run("npm test", timeout=600.0)

if result.success:
    print(result.stdout)
else:
    print(f"Failed: {result.error_message}")
```

### Retry with Backoff

```python
config = ShellConfig(max_retries=3, retry_base_delay=1.0, retry_exponential_base=2.0)
# Delays: 1s, 2s, 4s
```

## Teammate Delegation

### Discover Teammates

```python
from thegent.teammates import TeammateRegistry

registry = TeammateRegistry(agents_dir="agents")
teammates = registry.discover()

for t in teammates:
    print(f"{t.id}: {t.name} ({t.priority})")
```

### Delegate Tasks

```python
from thegent.teammates import Delegate, DelegationRequest

delegate = Delegate(registry)
result = delegate.delegate(
    DelegationRequest(teammate_id="coder", task="Refactor the authentication module", priority="HIGH", timeout=300.0)
)

print(f"Task ID: {result.id}")
print(f"Status: {result.status}")
```

## Performance Targets

| Metric                 | Target |
| ---------------------- | ------ |
| L1 cache hit latency   | <10ms  |
| Cache hit rate         | >60%   |
| Shell timeout success  | >80%   |
| Delegation latency P50 | <100ms |
| Memory per idle agent  | <2MB   |

## Benchmarking

Run Terminal-Bench validation:

```bash
python benchmark/tbench_validate.py --compare --swarm
```

Results saved to `benchmark/results/`.
