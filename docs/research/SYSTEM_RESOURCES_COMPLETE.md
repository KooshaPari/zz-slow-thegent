<DONE>
# System Resources Complete Practical Guide

> **Status**: Complete | **Version**: 1.0 | **Date**: 2026-02-16
> **Related**:
>
> - [System Resources FD CPU Deep Research](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)
> - [Swarm Complete](./SWARM_COMPLETE.md)
> - [Process Optimization Plan](../plans/PROCESS_OPTIMIZATION_PLAN.md)

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Resource Sampling Implementation](#2-resource-sampling-implementation)
3. [Per-Process Metrics](#3-per-process-metrics)
4. [Resource Gates & Limits](#4-resource-gates--limits)
5. [Prune Prioritization](#5-prune-prioritization)
6. [Configuration Reference](#6-configuration-reference)
7. [Troubleshooting](#7-troubleshooting)
8. [References](#8-references)

---

## 1. Executive Summary

### 1.1 Key Concepts

Activity Monitor–style metrics (CPU %, memory, FD count, threads, ports) are essential for:

- **ConcurrencyController** gates (FD, memory, load)
- **Prune prioritization** (RSS-aware, FD-aware)
- **`thegent ps` / `thegent observe`** — extend to system process view
- **Backpressure** when FD/CPU/threads approach limits

### 1.2 Current State

| Component               | Status             | Location                                   |
| ----------------------- | ------------------ | ------------------------------------------ |
| **ResourceSnapshot**    | ✅ Implemented     | `load_based_limits.py`                     |
| **FD sampling (Linux)** | ✅ Implemented     | `/proc/self/fd`                            |
| **FD sampling (macOS)** | ⚠️ Partial         | Falls back to 0                            |
| **Memory sampling**     | ✅ Implemented     | `/proc/meminfo` (Linux), `vm_stat` (macOS) |
| **Load average**        | ✅ Implemented     | `os.getloadavg()`                          |
| **Per-process metrics** | ❌ Not implemented | —                                          |

### 1.3 Gaps

- macOS FD count returns 0 (gate disabled)
- No per-process RSS/CPU/FD for prune prioritization
- No `thegent ps --system` view
- No thread/port gates

---

## 2. Resource Sampling Implementation

### 2.1 Cross-Platform Resource Sampling

```python
import os
import subprocess
import platform
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ResourceSnapshot:
    """System resource snapshot."""

    fd_used: int
    fd_limit: int
    mem_available_mb: int
    load_1m: float
    load_5m: float
    load_15m: float
    cpu_count: int


def sample_resources() -> ResourceSnapshot:
    """Sample system resources (cross-platform)."""
    system = platform.system()

    # FD sampling
    fd_used, fd_limit = _get_fd_usage(system)

    # Memory sampling
    mem_available_mb = _get_memory_available_mb(system)

    # Load average
    load_1m, load_5m, load_15m = os.getloadavg()

    # CPU count
    cpu_count = os.cpu_count() or 1

    return ResourceSnapshot(
        fd_used=fd_used,
        fd_limit=fd_limit,
        mem_available_mb=mem_available_mb,
        load_1m=load_1m,
        load_5m=load_5m,
        load_15m=load_15m,
        cpu_count=cpu_count,
    )


def _get_fd_usage(system: str) -> Tuple[int, int]:
    """Get FD usage (used, limit)."""
    if system == "Linux":
        # Linux: /proc/self/fd
        try:
            fd_count = len(os.listdir("/proc/self/fd"))
        except OSError:
            fd_count = 0

        # Get limit
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        return fd_count, soft

    elif system == "Darwin":  # macOS
        # macOS: lsof (expensive, cache result)
        try:
            result = subprocess.run(
                ["lsof", "-p", str(os.getpid())],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            # Filter out .txt (loaded libraries)
            fd_count = len([line for line in result.stdout.splitlines() if " txt " not in line])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            fd_count = 0

        # Get limit
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        return fd_count, soft

    else:
        # Windows or unknown
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        return 0, soft


def _get_memory_available_mb(system: str) -> int:
    """Get available memory in MB."""
    if system == "Linux":
        # Linux: /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        kb = int(line.split()[1])
                        return kb // 1024
        except OSError:
            return 0

    elif system == "Darwin":  # macOS
        # macOS: vm_stat
        try:
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            # Parse vm_stat output
            pages_free = 0
            pages_inactive = 0
            page_size = 4096  # Default page size

            for line in result.stdout.splitlines():
                if "Pages free" in line:
                    pages_free = int(line.split()[-1].rstrip("."))
                elif "Pages inactive" in line:
                    pages_inactive = int(line.split()[-1].rstrip("."))
                elif "page size" in line.lower():
                    page_size = int(line.split()[-1])

            available_bytes = (pages_free + pages_inactive) * page_size
            return available_bytes // (1024 * 1024)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return 0

    else:
        # Windows or unknown
        return 0
```

### 2.2 Cached Sampling (Performance Optimization)

```python
from functools import lru_cache
from time import time
from typing import Dict


class CachedResourceSampler:
    """Resource sampler with caching for expensive operations."""

    def __init__(self, cache_ttl: float = 5.0):
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[float, any]] = {}

    def sample(self, resource: str) -> any:
        """Sample resource with caching."""
        now = time()

        if resource in self._cache:
            cached_time, cached_value = self._cache[resource]
            if now - cached_time < self.cache_ttl:
                return cached_value

        # Sample resource
        if resource == "fd":
            value = _get_fd_usage(platform.system())
        elif resource == "memory":
            value = _get_memory_available_mb(platform.system())
        elif resource == "load":
            value = os.getloadavg()
        else:
            raise ValueError(f"Unknown resource: {resource}")

        # Cache result
        self._cache[resource] = (now, value)
        return value
```

---

## 3. Per-Process Metrics

### 3.1 Process Metrics Structure

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessMetrics:
    """Per-process resource metrics."""

    pid: int
    name: str
    rss_mb: float
    cpu_percent: float
    fd_count: int
    thread_count: int
    port_count: int


def get_process_metrics(pid: int) -> Optional[ProcessMetrics]:
    """Get metrics for a specific process."""
    system = platform.system()

    if system == "Linux":
        return _get_process_metrics_linux(pid)
    elif system == "Darwin":
        return _get_process_metrics_macos(pid)
    else:
        return None


def _get_process_metrics_linux(pid: int) -> Optional[ProcessMetrics]:
    """Get process metrics on Linux."""
    try:
        # RSS from /proc/<pid>/status
        with open(f"/proc/{pid}/status") as f:
            rss_kb = 0
            threads = 0
            for line in f:
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1])
                elif line.startswith("Threads:"):
                    threads = int(line.split()[1])

        rss_mb = rss_kb / 1024

        # FD count
        try:
            fd_count = len(os.listdir(f"/proc/{pid}/fd"))
        except OSError:
            fd_count = 0

        # CPU % and name from ps
        result = subprocess.run(
            ["ps", "-o", "%cpu,comm", "-p", str(pid)],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            return None

        cpu_percent = float(lines[1].split()[0])
        name = lines[1].split()[1] if len(lines[1].split()) > 1 else "unknown"

        # Port count (simplified)
        port_count = _count_ports_linux(pid)

        return ProcessMetrics(
            pid=pid,
            name=name,
            rss_mb=rss_mb,
            cpu_percent=cpu_percent,
            fd_count=fd_count,
            thread_count=threads,
            port_count=port_count,
        )
    except (OSError, ValueError, IndexError):
        return None


def _get_process_metrics_macos(pid: int) -> Optional[ProcessMetrics]:
    """Get process metrics on macOS."""
    try:
        # RSS and CPU from ps
        result = subprocess.run(
            ["ps", "-o", "rss=%cpu,comm", "-p", str(pid)],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) < 1:
            return None

        parts = lines[0].split()
        rss_kb = int(parts[0])
        cpu_percent = float(parts[1])
        name = parts[2] if len(parts) > 2 else "unknown"

        rss_mb = rss_kb / 1024

        # Thread count
        result = subprocess.run(
            ["ps", "-M", "-p", str(pid)],
            capture_output=True,
            text=True,
        )
        thread_count = max(0, len(result.stdout.splitlines()) - 1)

        # FD count (expensive)
        try:
            result = subprocess.run(
                ["lsof", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            fd_count = len([line for line in result.stdout.splitlines() if " txt " not in line])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            fd_count = 0

        # Port count
        port_count = _count_ports_macos(pid)

        return ProcessMetrics(
            pid=pid,
            name=name,
            rss_mb=rss_mb,
            cpu_percent=cpu_percent,
            fd_count=fd_count,
            thread_count=thread_count,
            port_count=port_count,
        )
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def _count_ports_linux(pid: int) -> int:
    """Count open ports for process on Linux."""
    try:
        result = subprocess.run(
            ["lsof", "-p", str(pid), "-i"],
            capture_output=True,
            text=True,
        )
        return len([line for line in result.stdout.splitlines() if "TCP" in line or "UDP" in line])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0


def _count_ports_macos(pid: int) -> int:
    """Count open ports for process on macOS."""
    try:
        result = subprocess.run(
            ["lsof", "-p", str(pid), "-i"],
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        return len([line for line in result.stdout.splitlines() if "TCP" in line or "UDP" in line])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0
```

### 3.2 Batch Process Metrics

```python
def get_all_process_metrics(pids: list[int]) -> list[ProcessMetrics]:
    """Get metrics for multiple processes efficiently."""
    metrics = []
    for pid in pids:
        metric = get_process_metrics(pid)
        if metric:
            metrics.append(metric)
    return metrics


def get_top_processes_by_rss(n: int = 20) -> list[ProcessMetrics]:
    """Get top N processes by RSS."""
    system = platform.system()

    if system == "Linux":
        result = subprocess.run(
            ["ps", "-eo", "pid,rss,%cpu,comm", "--sort=-rss"],
            capture_output=True,
            text=True,
        )
    elif system == "Darwin":
        result = subprocess.run(
            ["ps", "-eo", "pid,rss,%cpu,comm", "-m"],
            capture_output=True,
            text=True,
        )
    else:
        return []

    lines = result.stdout.strip().splitlines()[1:]  # Skip header
    top_pids = [int(line.split()[0]) for line in lines[:n]]

    return get_all_process_metrics(top_pids)
```

---

## 4. Resource Gates & Limits

### 4.1 Gate Configuration

```python
from dataclasses import dataclass


@dataclass
class LimitGateConfig:
    """Resource gate configuration."""

    fd_threshold: float = 0.75  # Block when FD ≥ 75%
    memory_threshold_mb: int = 256  # Block when memory < 256 MB
    load_per_cpu_max: float = 1.5  # Block when load ≥ 1.5× CPU
    thread_threshold: Optional[int] = None  # Block when threads > threshold
    port_threshold: Optional[int] = None  # Block when ports > threshold


def check_gates(snapshot: ResourceSnapshot, config: LimitGateConfig) -> Tuple[bool, list[str]]:
    """Check if resource gates allow execution."""
    violations = []

    # FD gate
    fd_utilization = snapshot.fd_used / snapshot.fd_limit if snapshot.fd_limit > 0 else 0
    if fd_utilization >= config.fd_threshold:
        violations.append(f"FD utilization {fd_utilization:.2%} >= {config.fd_threshold:.2%}")

    # Memory gate
    if snapshot.mem_available_mb < config.memory_threshold_mb:
        violations.append(f"Memory {snapshot.mem_available_mb} MB < {config.memory_threshold_mb} MB")

    # Load gate
    load_per_cpu = snapshot.load_1m / snapshot.cpu_count
    if load_per_cpu >= config.load_per_cpu_max:
        violations.append(f"Load per CPU {load_per_cpu:.2f} >= {config.load_per_cpu_max:.2f}")

    return len(violations) == 0, violations
```

### 4.2 Dynamic Limit Calculation

```python
def compute_dynamic_limit(
    snapshot: ResourceSnapshot,
    config: LimitGateConfig,
    min_slots: int = 1,
    max_slots: int = 20,
) -> int:
    """Compute dynamic concurrency limit from resource snapshot."""
    # CPU-based slots
    cpu_slots = min(max_slots, snapshot.cpu_count * 2)

    # FD-based slots
    fd_headroom = snapshot.fd_limit - snapshot.fd_used
    fd_slots = max(0, fd_headroom // 50)  # 50 FDs per slot

    # Memory-based slots
    mem_headroom = snapshot.mem_available_mb - config.memory_threshold_mb
    mem_slots = max(0, mem_headroom // 128)  # 128 MB per slot

    # Load-based slots (scale down as load approaches threshold)
    load_per_cpu = snapshot.load_1m / snapshot.cpu_count
    if load_per_cpu >= config.load_per_cpu_max:
        load_slots = 0
    else:
        load_factor = 1.0 - (load_per_cpu / config.load_per_cpu_max)
        load_slots = int(cpu_slots * load_factor)

    # Effective limit is minimum of all constraints
    effective_limit = min(cpu_slots, fd_slots, mem_slots, load_slots)

    # Clamp to min/max
    return max(min_slots, min(max_slots, effective_limit))
```

---

## 5. Prune Prioritization

### 5.1 RSS-Aware Pruning

```python
def prioritize_processes_for_prune(
    pids: list[int],
    sort_by: str = "rss",
    order: str = "desc",
) -> list[int]:
    """Prioritize processes for pruning based on resource usage."""
    metrics = get_all_process_metrics(pids)

    if sort_by == "rss":
        metrics.sort(key=lambda m: m.rss_mb, reverse=(order == "desc"))
    elif sort_by == "fd":
        metrics.sort(key=lambda m: m.fd_count, reverse=(order == "desc"))
    elif sort_by == "cpu":
        metrics.sort(key=lambda m: m.cpu_percent, reverse=(order == "desc"))
    else:
        return pids  # No sorting

    return [m.pid for m in metrics]


def prune_orphans_rss_aware(
    threshold: int = 12,
    sort_by: str = "rss",
) -> int:
    """Prune orphan processes, prioritizing by RSS."""
    # Find orphan processes
    orphans = find_orphan_processes()

    if len(orphans) <= threshold:
        return 0

    # Prioritize by RSS
    prioritized = prioritize_processes_for_prune(orphans, sort_by=sort_by)

    # Kill top N processes
    to_kill = prioritized[: len(orphans) - threshold]
    killed = 0

    for pid in to_kill:
        try:
            os.kill(pid, signal.SIGTERM)
            killed += 1
        except (OSError, ProcessLookupError):
            pass

    return killed
```

---

## 6. Configuration Reference

### 6.1 Environment Variables

```bash
# Resource gates
THGENT_CONCURRENCY_FD_UTILIZATION_MAX=0.75
THGENT_CONCURRENCY_LOAD_PER_CPU_MAX=1.5
THGENT_CONCURRENCY_MEM_AVAILABLE_MIN_MB=256

# macOS FD sampling
THGENT_FD_SAMPLE_METHOD=lsof  # lsof | proc | skip
THGENT_FD_SAMPLE_CACHE_SEC=60

# Prune prioritization
THGENT_PRUNE_SORT_BY=rss  # rss | fd | cpu | none
THGENT_PRUNE_SORT_ORDER=desc

# System resource view
THGENT_PS_SYSTEM_TOP_N=20
THGENT_PS_SYSTEM_COLUMNS=pid,rss,cpu,fd,cmd
```

### 6.2 Config File

```yaml
# ~/.config/thegent/resources.yaml
gates:
  fd_threshold: 0.75
  memory_threshold_mb: 256
  load_per_cpu_max: 1.5
  thread_threshold: null
  port_threshold: null

sampling:
  cache_ttl: 5.0
  fd_cache_ttl: 60.0
  method: auto # auto | lsof | proc

prune:
  sort_by: rss
  sort_order: desc
  threshold: 12
```

---

## 7. Troubleshooting

### 7.1 Common Issues

**Issue**: macOS FD count always 0

- **Solution**: Use `lsof` method, enable caching
- **Config**: `THGENT_FD_SAMPLE_METHOD=lsof`, `THGENT_FD_SAMPLE_CACHE_SEC=60`

**Issue**: Prune too aggressive

- **Solution**: Increase threshold, adjust sort order
- **Config**: `THGENT_PRUNE_SORT_BY=rss`, `THGENT_AUTO_PRUNE_THRESHOLD=20`

**Issue**: Resource gates always block

- **Solution**: Check thresholds, verify sampling
- **Debug**: `thegent observe resources`

### 7.2 Debugging

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)

# Check resource snapshot
snapshot = sample_resources()
print(f"FD: {snapshot.fd_used}/{snapshot.fd_limit}")
print(f"Memory: {snapshot.mem_available_mb} MB")
print(f"Load: {snapshot.load_1m}")

# Check gates
config = LimitGateConfig()
allowed, violations = check_gates(snapshot, config)
print(f"Allowed: {allowed}, Violations: {violations}")
```

---

## 8. References

### 8.1 Related Documentation

- [System Resources FD CPU Deep Research](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md) - Deep research
- [Swarm Complete](./SWARM_COMPLETE.md) - Process automation
- [Process Optimization Plan](../plans/PROCESS_OPTIMIZATION_PLAN.md) - Process optimization

### 8.2 Implementation Files

- **ResourceSnapshot**: `src/thegent/orchestration/load_based_limits.py`
- **ConcurrencyController**: `src/thegent/execution.py`

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md) - Deep research
- [SWARM_COMPLETE.md](./SWARM_COMPLETE.md) - Swarm guide
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

_Generated: 2026-02-16 | Version: 1.0 | Status: Complete_

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added planning patterns
2. Added implementation roadmap
3. Enhanced cross-references

### Cross-References Added

- WORK_STREAM.md
- Implementation guides

### Practical Additions

- Planning templates
- Roadmap configurations

## Resource Pressure Thresholds

- **CPU pressure**: trigger mitigation when `load_1m >= 0.85 * $(sysctl -n hw.ncpu)`; verify with `thegent observe resources`.
- **Memory pressure**: trigger mitigation when available memory `< 1024 MB`; verify with `thegent observe resources`.
- **FD pressure**: trigger mitigation when FD usage `>= 80%` of limit; verify with `thegent observe resources`.
- **Sustained pressure rule**: act only after 3 consecutive samples, 10s apart: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.

## Recovery Command Set

- Snapshot current state: `thegent observe resources`.
- Reduce active load quickly: `thegent mcp prune --dry-run && thegent mcp prune`.
- Inspect and stop overloaded sessions: `thegent ps` then `thegent stop <session_id>`.
- Re-check stabilization loop: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.

## Resource Alert Matrix

- **CPU critical** (`load_1m >= cores`): `thegent observe resources` -> `thegent mcp prune`.
- **Memory critical** (`available_mb < 512`): `thegent ps` -> `thegent stop <session_id>` (largest workloads first).
- **FD critical** (`fd_used/fd_limit >= 0.9`): `thegent mcp prune --dry-run && thegent mcp prune` -> recheck.
- **All-clear condition**: 3 clean samples via `for i in 1 2 3; do thegent observe resources; sleep 10; done`.

## Stabilization Workflow

- Baseline: run `thegent observe resources` and record CPU/memory/FD.
- Shed load: run `thegent mcp prune --dry-run && thegent mcp prune`.
- Triage sessions: run `thegent ps`; stop top offenders with `thegent stop <session_id>`.
- Verify recovery: run `for i in 1 2 3; do thegent observe resources; sleep 10; done` and confirm thresholds are clear.

## Capacity Planning Cadence

- Daily 09:00: `thegent observe resources >> logs/resource_snapshots.log`.
- Weekly peak check: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
- Weekly cleanup window: `thegent mcp prune --dry-run && thegent mcp prune`.
- Capacity drift trigger: if any threshold breaches twice in a week, run `thegent ps` and rebalance with `thegent stop <session_id>`.

## Emergency Throttle Commands

- Immediate baseline: `thegent observe resources`.
- Fast pressure relief: `thegent mcp prune --dry-run && thegent mcp prune`.
- Hard throttle active load: `thegent ps` then `thegent stop <session_id>` for largest sessions first.
- Confirm recovery: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.

## Baseline Capture Routine

- Capture point-in-time baseline: `thegent observe resources`.
- Capture short trend window: `for i in 1 2 3; do date; thegent observe resources; sleep 10; done`.
- Persist baseline log: `mkdir -p logs && thegent observe resources >> logs/resource_baseline.log`.
- Snapshot active workload map: `thegent ps`.

## Resource Regression Triggers

- CPU regression: `load_1m >= 0.85 * $(sysctl -n hw.ncpu)` in 3 consecutive samples.
- Memory regression: available memory `< 1024 MB` across `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
- FD regression: FD usage `>= 80%` on repeated `thegent observe resources` checks.
- Trend regression: two threshold breaches in one day from `logs/resource_baseline.log` review.

## Resource Snapshot Cadence

- Hourly quick sample: `thegent observe resources`.
- Shift baseline (start/end): `mkdir -p logs && thegent observe resources >> logs/resource_snapshots.log`.
- Peak-window sampling: `for i in 1 2 3; do date; thegent observe resources; sleep 10; done`.
- Daily review command: `tail -n 50 logs/resource_snapshots.log`.

## Degradation Response Commands

- Confirm degradation: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
- Shed idle load: `thegent mcp prune --dry-run && thegent mcp prune`.
- Throttle active pressure: `thegent ps` then `thegent stop <session_id>`.
- Verify recovery gate: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.

## Saturation Mitigation Ladder

- **Level 1 (Detect):** `thegent observe resources`.
- **Level 2 (Confirm):** `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
- **Level 3 (Shed idle load):** `thegent mcp prune --dry-run && thegent mcp prune`.
- **Level 4 (Throttle active load):** `thegent ps` then `thegent stop <session_id>` (largest first).
- **Level 5 (Stabilize gate):** repeat 3-sample loop; continue only after thresholds clear.

## Resource Triage Checklist

- Capture snapshot: `thegent observe resources`.
- Classify bottleneck: CPU (`load_1m`), memory (`available_mb`), FD (`fd_used/fd_limit`).
- Pick first action: prune (`thegent mcp prune`) or stop (`thegent stop <session_id>`).
- Re-check after action: `thegent observe resources`.
- Exit condition: 3 clean samples from `for i in 1 2 3; do thegent observe resources; sleep 10; done`.

## Capacity Reserve Rules

- Maintain headroom target: `thegent observe resources` and keep CPU `<70%`, memory `>1024 MB`, FD `<70%`.
- Enforce reserve gate before new load: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
- If reserve is below target, free capacity first: `thegent mcp prune --dry-run && thegent mcp prune`.
- If still below target, reduce active sessions: `thegent ps` then `thegent stop <session_id>`.

## Incident Stabilization Commands

- Capture incident baseline: `thegent observe resources`.
- Confirm sustained saturation: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
- Shed idle pressure immediately: `thegent mcp prune --dry-run && thegent mcp prune`.
- Triage and stop highest offenders: `thegent ps` then `thegent stop <session_id>`.
- Validate stabilization before resume: `for i in 1 2 3; do thegent observe resources; sleep 10; done`.
