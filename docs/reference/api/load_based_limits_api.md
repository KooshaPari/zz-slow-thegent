# load_based_limits API Reference

> **Source**: `src/thegent/orchestration/load_based_limits.py`

WP-5001: Load-based concurrency limits (FD, memory, CPU, load average).

Replaces fixed max_concurrency with dynamic, resource-aware limits that scale
as a load balancer: allow more slots when system headroom exists, throttle when
gates are near capacity.

BKM-04: When THGENT_USE_NATIVE_RESOURCES=1, uses thegent-resources Rust binary
instead of psutil. Set THGENT_RESOURCES_BIN to override path.

---

## HysteresisController

WP-Y6: Prevents thrashing by using upper/lower thresholds and dwell time.

### Methods

#### HysteresisController.**init**

```python
__init__(self: Any, upper_threshold: float, lower_threshold: float, dwell_time_s: int)
```

---

#### HysteresisController.get_limit

```python
get_limit(self: Any, current_limit: int, running_count: int, target_limit: int)
```

Apply hysteresis to determine the new limit.

Returns the new limit (either changed or held).

---

---

## LimitGateConfig

Configuration for each resource gate. Thresholds are 0.0–1.0 (utilization).

Uses resource-based limits with safety buffers:

- Minimum buffer: 5% (hard limit, prevents crashes)
- Discretionary buffer: 15% (soft limit, allows scaling)
- No fixed concurrent limit - scales with available resources

### Methods

#### LimitGateConfig.from_dict

```python
from_dict(cls: Any, d: Any)
```

Build config from dict (e.g. settings). Supports concurrency\_ prefix.

---

---

## ResourceSnapshot

Current system resource usage for limit calculation.

---

## compute_dynamic_limit

```python
compute_dynamic_limit(snapshot: ResourceSnapshot, config: Any, running_count: int)
```

Compute max concurrent slots from resource gates. Resource-based scaling:

- No fixed limit - scales with available resources
- 5% minimum buffer (hard limit, prevents crashes)
- 15% discretionary buffer (soft limit, allows scaling)
- Uses CPU, memory, FD, and load average

Returns (effective_limit, gate_details).

---

## from_dict

```python
from_dict(cls: Any, d: Any)
```

Build config from dict (e.g. settings). Supports concurrency\_ prefix.

---

## get_limit

```python
get_limit(self: Any, current_limit: int, running_count: int, target_limit: int)
```

Apply hysteresis to determine the new limit.

Returns the new limit (either changed or held).

---

## sample_resources

Sample current system resources. Cross-platform where possible.

Uses thegent-resources Rust binary when THGENT_USE_NATIVE_RESOURCES=1;
otherwise falls back to Python (lsof/vm_stat on macOS, /proc on Linux).

---
