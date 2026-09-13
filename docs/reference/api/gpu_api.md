# gpu API Reference

> **Source**: `src/thegent/resources/gpu.py`

GPU utilization monitoring for thegent resource management.

---

## GpuInfo

Information about a single GPU device.

---

## GpuMonitor

Monitors GPU utilization using pynvml or nvidia-smi fallback.

Tries pynvml (nvidia-ml-py) first for efficiency; falls back to
parsing `nvidia-smi --query-gpu` CSV output if pynvml is absent.
When no GPU hardware is detected, all methods return empty/zero values
rather than raising.

### Methods

#### GpuMonitor.get_gpus

```python
get_gpus(self: Any)
```

Return a list of GpuInfo for every detected GPU.

Tries pynvml first; falls back to nvidia-smi subprocess.
Returns an empty list when no GPUs are detected or no tooling
is available — never raises for "no GPU" conditions.

---

#### GpuMonitor.get_total_utilization

```python
get_total_utilization(self: Any)
```

Return average GPU utilization across all GPUs (0.0 if none).

---

#### GpuMonitor.is_available

```python
is_available(self: Any)
```

Return True if GPU monitoring is possible on this machine.

Checks pynvml first, then falls back to probing nvidia-smi.

---

---

## GpuMonitorError

Raised when GPU monitoring fails unexpectedly.

**Inherits from**: `Exception`

---

## get_gpus

```python
get_gpus(self: Any)
```

Return a list of GpuInfo for every detected GPU.

Tries pynvml first; falls back to nvidia-smi subprocess.
Returns an empty list when no GPUs are detected or no tooling
is available — never raises for "no GPU" conditions.

**Raises**:

- `GpuMonitorError`: On unexpected errors during data collection.

---

## get_total_utilization

```python
get_total_utilization(self: Any)
```

Return average GPU utilization across all GPUs (0.0 if none).

---

## is_available

```python
is_available(self: Any)
```

Return True if GPU monitoring is possible on this machine.

Checks pynvml first, then falls back to probing nvidia-smi.

---
