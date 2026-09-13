<DONE>
# Advanced Resource Management System

**Date**: 2026-02-19
**Status**: Implemented

## Overview

Comprehensive resource management system with extended indices, prediction, harness modeling, and bottleneck detection. Replaces fixed concurrent limits with dynamic, resource-aware scaling.

## Key Features

### 1. Extended Resource Indices

Beyond CPU, memory, FD, and load average:

- **Network I/O**: Bytes sent/received, connection count, TCP/UDP/Unix sockets, established connections
- **Disk I/O**: Read/write bytes, I/O wait time
- **Process Tracking**: System-wide process count, **child process count**, **zombie process detection**
- **Thread Tracking**: Active threads, blocked threads, thread counts per process
- **Socket Tracking**: TCP, UDP, Unix sockets, established connections
- **System Metrics**: Context switches, interrupts, page faults
- **Swap Usage**: Used/total swap memory
- **Cache Hit Rates**: Approximate page cache efficiency
- **GPU** (if available): Memory usage, utilization
- **Leak Detection**: Memory leaks, FD leaks, child process leaks, thread leaks, socket leaks

### 2. Prediction Engine (with Leak Detection)

**ResourcePredictionEngine** forecasts future resource needs:

- Historical pattern analysis (1000+ snapshots)
- Trend-based forecasting (linear regression)
- Anomaly detection (3-sigma rule)
- **Automatic leak detection** (memory, FD, child processes, threads, sockets)
- Confidence scoring

**Leak Detection**:

- Tracks resource growth rates over time windows
- Detects memory leaks (>10MB/hour), FD leaks (>1 FD/hour), child process leaks (>0.1 proc/hour)
- Severity classification: none, low, medium, high, critical
- Integrated into `ExtendedResourceSnapshot.leak_metrics`

**Usage**:

```python
from thegent.orchestration.resource_management import ResourcePredictionEngine, sample_extended_resources

engine = ResourcePredictionEngine()
snapshot = sample_extended_resources()
engine.record(snapshot)  # Automatically detects leaks from history

prediction = engine.predict_next_interval(60)  # Next 60 seconds
anomalies = engine.detect_anomalies(snapshot)

# Check leak metrics
if snapshot.leak_metrics.memory_leak_detected:
    print(f"Memory leak detected: {snapshot.leak_metrics.memory_leak_rate_mb_per_hour:.2f} MB/hour")
if snapshot.leak_metrics.fd_leak_detected:
    print(f"FD leak detected: {snapshot.leak_metrics.fd_leak_rate_per_hour:.2f} FD/hour")
print(f"Leak severity: {snapshot.leak_metrics.leak_severity}")
```

### 3. Harness Card System (Enhanced with Statistical Distributions)

**HarnessCard** models individual harness types with **statistical distributions** for all resources:

- **Statistical Distributions**: min, avg, peak, stddev, p50, p95, p99 for every resource
- **Resource Types Tracked**:
  - Memory (base + per-session)
  - File descriptors (base + per-session)
  - CPU (base + per-session)
  - **Child processes** (base + per-session)
  - **Threads** (base + per-session)
  - **Sockets** (base + per-session)
  - Network bytes per request
  - Network connections per session
  - Latency (p50/p95/p99)
- **Leak Rates**: Memory leaks, FD leaks, child process leaks, thread leaks, socket leaks
- Isolation vs multi-harness efficiency
- Historical usage patterns (1000+ samples)

**Harness Profiles** (with statistical distributions):

- **codex**:
  - Memory: 256MB base (min:200, peak:400, p95:350), 128MB/session (min:100, peak:200, p95:170)
  - FD: 20 base (min:15, peak:35, p95:30), 10/session (min:8, peak:18, p95:15)
  - Child processes: 1 base, 0.5/session
  - Threads: 8 base, 4/session
  - Leak rates: 0.5MB/h memory, 0.05 FD/h

- **claude**:
  - Memory: 512MB base (min:400, peak:800, p95:700), 256MB/session (min:200, peak:450, p95:380)
  - FD: 30 base (min:25, peak:50, p95:42), 15/session (min:12, peak:28, p95:23)
  - Child processes: 2 base, 1/session
  - Threads: 12 base, 6/session
  - Leak rates: 1.0MB/h memory, 0.1 FD/h

- **droid**:
  - Memory: 128MB base (min:100, peak:200, p95:170), 64MB/session (min:50, peak:120, p95:95)
  - FD: 15 base (min:10, peak:25, p95:22), 5/session (min:3, peak:12, p95:9)
  - Child processes: 0 base, 0/session
  - Threads: 5 base, 2/session
  - Leak rates: 0.2MB/h memory, 0.02 FD/h

- **cursor-agent**:
  - Memory: 384MB base (min:300, peak:600, p95:520), 192MB/session (min:150, peak:350, p95:280)
  - FD: 25 base (min:20, peak:45, p95:38), 12/session (min:10, peak:22, p95:18)
  - Child processes: 1 base, 0.5/session
  - Threads: 10 base, 5/session
  - Sockets: 12 base, 6/session
  - Leak rates: 0.8MB/h memory, 0.08 FD/h

**Usage**:

```python
from thegent.orchestration.resource_management import create_harness_cards

cards = create_harness_cards()
cursor_card = cards["cursor-agent"]

# Estimate with statistical distributions
estimated = cursor_card.estimate_resources(
    session_count=10,
    isolated=False,
    use_p95=True,  # Use p95 for conservative planning
)

# Returns comprehensive dictionary with min/avg/peak/p95 for all resources:
# {
#   "memory_mb": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "fd_count": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "cpu_percent": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "child_process_count": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "thread_count": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "socket_count": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "network_bytes": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "network_connections": {"min": ..., "avg": ..., "peak": ..., "p95": ...},
#   "estimated_latency_p95_ms": ...,
#   "leak_rates": {
#     "memory_mb_per_hour": ...,
#     "fd_per_hour": ...,
#     "child_process_per_hour": ...
#   }
# }
```

**Key Features**:

- **Statistical Modeling**: All resources modeled with distributions, not single values
- **Comprehensive Tracking**: Child processes, threads, sockets, network connections
- **Leak Detection**: Built-in leak rate tracking and detection
- **Conservative Planning**: Use `use_p95=True` for p95-based capacity planning
- **Peak Planning**: Use `use_peak=True` for worst-case scenario planning

### 4. Bottleneck Detection

**BottleneckDetector** identifies slow points:

- Agent loop timing analysis (p95/p99 tail latency)
- Resource contention detection (FD, memory, CPU)
- Harness-specific contention
- Optimization suggestions

**Usage**:

```python
from thegent.orchestration.resource_management import BottleneckDetector

detector = BottleneckDetector()
detector.record_loop_timing("agent_loop_1", duration_ms=5000)
slow_points = detector.identify_slow_points()
contentions = detector.detect_resource_contention(snapshot, harness_cards)
```

### 5. Speculative Execution Strategies

**SpeculativeStrategies** for multi-provider racing:

- **RACE_FIRST**: Use first result (lowest latency)
- **RACE_BEST**: Use best quality result
- **ADAPTIVE_TIMEOUT**: Adjust timeout based on historical performance
- **COST_QUALITY_TRADEOFF**: Balance cost vs quality within budget
- **EARLY_TERMINATION**: Terminate slow providers early

**Usage**:

```python
from thegent.orchestration.speculative_strategies import (
    SpeculativeStrategy,
    SpeculativeConfig,
    select_speculative_providers,
)

config = SpeculativeConfig(
    strategy=SpeculativeStrategy.COST_QUALITY_TRADEOFF,
    cost_budget_usd=0.01,
)
providers = select_speculative_providers(["free", "claude", "gemini"], config.strategy)
```

### 6. Work Chunking

**WorkChunking** for resource-aware parallelization:

- Dynamic chunk sizing based on available resources
- Optimal parallelism calculation
- Memory and FD-aware chunking
- Adaptive rebalancing

**Usage**:

```python
from thegent.orchestration.work_chunking import compute_optimal_chunk_size, chunk_work_items

chunk_size, num_chunks = compute_optimal_chunk_size(
    total_items=1000,
    available_resources={"mem_available_mb": 2048, "fd_available": 200},
)
chunks = chunk_work_items(items, chunk_size)
```

## Integration

### ConcurrencyController Enhancement

The `ConcurrencyController` now uses:

1. **Extended resources** for limit calculation
2. **Harness card modeling** for harness-specific limits
3. **Prediction engine** for trend-based adjustments
4. **Bottleneck detection** for contention-aware limits

**Example**:

```python
cc = ConcurrencyController(session_dir, use_load_based=True)
if cc.acquire(lane="standard", harness_type="codex"):
    # Slot acquired with codex-specific resource modeling
    pass

bottlenecks = cc.get_bottlenecks()
# Returns: {"slow_points": [...], "resource_contention": [...]}
```

## Resource Buffers

- **5% Minimum Buffer**: Hard limit prevents crashes (95% utilization max)
- **15% Discretionary Buffer**: Soft limit allows scaling (85% utilization warning)

## Benefits

1. **No Fixed Limits**: Scales with available resources
2. **Harness-Aware**: Models codex/claude/droid usage profiles
3. **Predictive**: Forecasts future needs, prevents overload
4. **Bottleneck-Aware**: Detects and mitigates contention
5. **Speculative**: Multi-provider racing for optimal results
6. **Chunked**: Resource-aware work parallelization

## Future Enhancements

- GPU utilization tracking (nvidia-ml-py integration)
- Network bandwidth monitoring
- Disk I/O queue depth
- Per-harness historical learning
- Machine learning-based prediction
- Distributed resource coordination

## Files Created

- `src/thegent/orchestration/resource_management.py` - Core resource management
- `src/thegent/orchestration/speculative_strategies.py` - Speculative execution
- `src/thegent/orchestration/work_chunking.py` - Work chunking
- `docs/research/ADVANCED_RESOURCE_MANAGEMENT_SYSTEM.md` - This document

## References

- WP-5001: Speculative Execution Mode
- WP-5002: Burst Load Classification
- heliosShield harness integration patterns
- Existing bottleneck analysis in `planning/simulation.py`
