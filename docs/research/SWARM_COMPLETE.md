<DONE>
# Swarm Management Complete Research & Implementation Guide

> **Status**: Complete | **Version**: 1.0 | **Date**: 2026-02-16
> **Related**:
> - [Swarm Process Optimizations](../reference/SWARM_PROCESS_OPTIMIZATIONS.md)
> - [Process Optimization Plan](../plans/PROCESS_OPTIMIZATION_PLAN.md)
> - [System Resources Research](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)
> - [Advanced Strategies Research](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md)

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scheduling Theory & Fundamentals](#2-scheduling-theory--fundamentals)
3. [thegent Scheduling Architecture](#3-thegent-scheduling-architecture)
4. [Process Automation & Pruning](#4-process-automation--pruning)
5. [Resource Management](#5-resource-management)
6. [Industry Systems & Patterns](#6-industry-systems--patterns)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Configuration Reference](#8-configuration-reference)
9. [Troubleshooting](#9-troubleshooting)
10. [References](#10-references)

---

## 1. Executive Summary

### 1.1 Scope

This document consolidates research on swarm management for multi-agent, multi-tenant, multi-project local swarms, covering:
- **Scheduling theory**: OS schedulers, load balancing, fairness, deadlines
- **Process automation**: Orphan detection, pruning triggers, resource-based backpressure
- **Resource management**: FD, memory, CPU gates, hysteresis, dynamic limits
- **Industry patterns**: Job schedulers, orchestrators, task queues, work stealing

### 1.2 Key Concepts

**Scheduling**:
- **Long-term (admission)**: ConcurrencyController decides whether new agent run may start
- **Dynamic load balancing**: Resource sampling at `acquire()` time
- **Hysteresis**: Anti-thrashing with dwell time (30s)

**Process Automation**:
- **Auto-prune**: Stop hooks, periodic timers, memory-based triggers
- **Orphan detection**: Process tree traversal (orphan-by-ppid)
- **Resource gates**: FD, memory, load average thresholds

**Resource Management**:
- **Gates**: Block when FD ≥ 75%, memory < 256 MB, load ≥ 1.5× CPU
- **Dynamic limits**: Compute slots from resource headroom
- **Hysteresis**: Prevent rapid oscillation near thresholds

### 1.3 Current State

| Component | Status | Location |
|-----------|--------|----------|
| **Auto-prune** | ✅ Implemented | `prune-orphans-stop.sh` |
| **ConcurrencyController** | ✅ Implemented | `execution.py` |
| **ResourceSnapshot** | ✅ Implemented | `load_based_limits.py` |
| **HysteresisController** | ✅ Implemented | `load_based_limits.py` |
| **Periodic prune** | ✅ Implemented | `prune-periodic` (launchd/systemd) |
| **Orphan-by-ppid** | ✅ Implemented | Process tree traversal |
| **macOS memory sampling** | ✅ Implemented | `vm_stat` fallback |

### 1.4 Gaps & Future Work

| Gap | Impact | Priority |
|-----|--------|----------|
| **Per-project resource limits** | No cgroup/ulimit per project | Low |
| **Fair queuing** | No proportional share | Medium |
| **Work stealing** | Single machine only | Low |
| **Deadline scheduling** | No EDF or deadlines | Low |
| **Distributed scheduling** | Single node only | Low |

---

## 2. Scheduling Theory & Fundamentals

### 2.1 Scheduling Fundamentals

**Scheduling** is the action of assigning resources to perform tasks. Resources may be processors, network links, memory, or I/O devices. Tasks may be threads, processes, or data flows.

**Goals** (often conflicting):

| Goal | Description |
|------|-------------|
| **Fairness** | Equal or proportional resource share per party |
| **Throughput** | Maximize work completed per time unit |
| **Latency** | Minimize time from ready to first output |
| **Response time** | Minimize wait until execution starts |
| **Deadline meeting** | Real-time: meet hard/soft deadlines |

**Scheduler**: The mechanism that performs scheduling. May be centralized (master) or distributed.

### 2.2 OS Scheduler Types

| Type | Frequency | Role |
|------|-----------|------|
| **Long-term (admission)** | Infrequent | Decides which jobs enter the ready queue; controls degree of multiprogramming; balances I/O-bound vs CPU-bound mix |
| **Medium-term** | Periodic | Swaps processes in/out of memory; frees RAM; may perform demand paging |
| **Short-term (CPU)** | Very frequent | Picks next process to run; preemptive or cooperative; time-slice based |

**thegent relevance**: ConcurrencyController acts as a **long-term admission scheduler** — it decides whether a new agent run may start (`acquire()`). It does not schedule CPU time (OS does that) but **admission** of concurrent runs.

### 2.3 Scheduling Disciplines & Algorithms

| Algorithm | Description | Pros | Cons |
|-----------|-------------|------|------|
| **FCFS/FIFO** | First come, first served | Simple, no starvation | Convoy effect; poor latency for short jobs |
| **Round-Robin** | Fixed time slice per process | Fair, good response time | Overhead; deadlines rarely met |
| **Priority** | Fixed or dynamic priority | Deadlines via high priority | Starvation of low priority |
| **Shortest Job First (SJF)** | Shortest estimated time first | Max throughput | Needs estimates; starvation of long jobs |
| **Earliest Deadline First (EDF)** | Schedule by deadline | Optimal for real-time | Needs deadlines; complex |
| **Multilevel Feedback Queue** | Multiple queues; promote/demote | Balances latency and throughput | Complex tuning |
| **Fair Queuing** | Proportional share | Fairness | Overhead |
| **Proportional Fair** | Balance throughput and fairness | Used in wireless | Channel-dependent |

**thegent relevance**: Current logic is **priority-like** (critical lane gets 2× slots) and **threshold-based** (gates block when near capacity). No explicit FCFS, RR, or EDF.

### 2.4 Load Balancing: Static vs Dynamic

| Type | Knowledge | Communication | Use Case |
|------|-----------|---------------|----------|
| **Static** | Assumed task sizes, arrival times | None at runtime | Homogeneous workloads |
| **Dynamic** | Current load per node | Continuous exchange | Heterogeneous, variable workloads |

**Static methods**: Round-robin, hash-based, power-of-two-choices (pick 2 random, choose better).

**Dynamic methods**: Least connections, least response time, work stealing, master-worker.

**thegent relevance**: ConcurrencyController is **dynamic** — it samples FD, memory, load at `acquire()` time. No static pre-assignment.

### 2.5 Work-Conserving vs Non-Work-Conserving

| Type | Behavior |
|------|----------|
| **Work-conserving** | Never leaves resources idle if work is ready |
| **Non-work-conserving** | May idle despite pending work (e.g. for fairness, deadlines) |

**thegent relevance**: Current design is work-conserving — if a slot is free and gates allow, `acquire()` returns true. No explicit "hold back for fairness" logic.

### 2.6 Fairness, Starvation, and Deadlines

- **Starvation**: A task never gets resources. Mitigations: aging, priority boost, fair queuing.
- **Fairness**: Max-min fairness, proportional fairness, equal share.
- **Deadlines**: Hard (must meet) vs soft (best effort). EDF for hard real-time.

**thegent relevance**: Critical lane (2× slots) can starve standard lane under load. No deadline model for agent runs.

---

## 3. thegent Scheduling Architecture

### 3.1 Current Components

| Component | Location | Role |
|-----------|----------|------|
| **ConcurrencyController** | `execution.py` | Admission control for agent runs |
| **HysteresisController** | `load_based_limits.py` | Anti-thrashing; dwell time |
| **ResourceSnapshot** | `load_based_limits.py` | FD, memory, load sample |
| **compute_dynamic_limit** | `load_based_limits.py` | Gate-based slot calculation |
| **LimitGateConfig** | `load_based_limits.py` | Thresholds per resource |
| **Gardener spawn limits** | `gardener-spawn-manager.sh` | Disk-based backpressure |
| **Load thresholds** | `config.py` | Spike (10), surge (20) for traffic shaping |

### 3.2 ConcurrencyController Deep Dive

**Design**: WP-5001 — adaptive concurrency with load-based limits.

**Flow**:
1. `acquire(lane)` called before starting a run.
2. Count running sessions via `ps_impl(all=True)`.
3. If `load_based=False`: fixed limit (standard) or 2× (critical).
4. If `load_based=True`:
   - `sample_resources()` → ResourceSnapshot
   - `compute_dynamic_limit(snapshot, config, running_count)` → target_limit
   - `HysteresisController.get_limit(current, running, target)` → effective limit
   - `running_count < limit` → acquire succeeds

**Lanes**: `standard` and `critical`. Critical gets up to 2× slots (reserved for recovery, overrides).

**Gaps**:
- No per-project or per-tenant limits.
- No priority queue (FCFS within lane).
- No deadline or EDF.
- Single-machine only.

### 3.3 HysteresisController and Anti-Thrashing

**Design**: WP-Y6 — upper/lower thresholds + dwell time.

**Parameters**:
- `upper_threshold=0.8`: Scale UP when utilization > 80%.
- `lower_threshold=0.4`: Scale DOWN when utilization < 40%.
- `dwell_time_s=30`: Minimum time between limit changes.

**Logic**:
- If `now - last_scale_time < dwell_time_s` → HOLD (no change).
- If `utilization > 0.8` and `target > current` → Scale UP.
- If `utilization < 0.4` and `target < current` → Scale DOWN.
- Else → HOLD (dead zone).

**Prevents**: Rapid oscillation when load hovers near threshold (e.g. 8/10 slots → 9 → 8 → 9).

### 3.4 ResourceSnapshot and Limit Gates

**Gates** (from `LimitGateConfig`):

| Gate | Metric | Block When |
|------|--------|------------|
| **FD** | fd_used / fd_limit | ≥ 75% utilization |
| **Memory** | mem_available_mb | < 256 MB |
| **Load** | load_1m / cpu_count | ≥ 1.5 per CPU |

**Slot calculation**:
- `cpu_slots = min(max, cpu_count * 2)` (base)
- `fd_slots` = headroom / 50 FDs per slot
- `mem_slots` = (available - 256) / 128 MB per slot
- `load_slots` = scaled down as load approaches 1.5× CPU

**Effective limit** = min(cpu, fd, mem, load), clamped to [min_slots, max_slots].

**macOS support**: `_get_memory_mb()` uses `vm_stat` on macOS (fallback from `/proc/meminfo`).

### 3.5 Gaps vs Theory

| Theory / System | thegent Status | Gap |
|-----------------|----------------|------|
| **Admission control** | ConcurrencyController | ✓ Present |
| **Dynamic load balancing** | Resource sampling | ✓ Present |
| **Hysteresis** | HysteresisController | ✓ Present |
| **Priority scheduling** | Critical lane 2× | Partial; no general priority |
| **Fair queuing** | None | No proportional share |
| **Work stealing** | None | Single machine; no steal |
| **Deadline scheduling** | None | No EDF or deadlines |
| **Per-tenant limits** | None | Global only |
| **Distributed scheduling** | None | Single node |
| **Job queue** | run_registry | Log only; no queue discipline |
| **Preemption** | None | No pause/resume of runs |

---

## 4. Process Automation & Pruning

### 4.1 Current State

| Capability | Location | Trigger | Notes |
|------------|----------|---------|-------|
| **Auto-prune** | `prune-orphans-stop.sh` | Stop | Opt-in via `THGENT_AUTO_PRUNE=1`; threshold + cooldown |
| **Manual prune** | `thegent mcp prune` | CLI | Patterns: LSPs, MCP servers, cc-status, bun, deno |
| **Load thresholds** | `config.py` | Session start | `load_spike_threshold` (10), `load_surge_threshold` (20) |
| **ConcurrencyController** | `execution.py` | `acquire()` | FD/Mem/CPU gates when `load_based=True` |
| **ResourceSnapshot** | `load_based_limits.py` | `sample_resources()` | FD, memory, load avg; macOS `vm_stat` |
| **HysteresisController** | `load_based_limits.py` | `get_limit()` | Prevents thrashing; dwell time 30s |
| **Gardener spawn limits** | `gardener-spawn-manager.sh` | Spawn | `GARDENER_MIN_USAGE_PERCENT=15` (disk) |
| **Session scoping** | `cli_impl.py` | Run | `session_dir / owner_key` = `user:projectname` |

### 4.2 Automation Taxonomy

**Trigger Types**:

| Trigger | When | Use Case | Implemented |
|---------|------|----------|-------------|
| **Stop** | Session end (IDE Stop) | Prune after session ends | ✓ Yes |
| **SessionEnd** | After Stop hooks | `session-cleanup.sh`; could add prune | Partial |
| **Periodic** | Cron/launchd/timer | Background prune every N min | ✓ Yes (`prune-periodic`) |
| **Idle** | No output for N seconds | Hook-dispatcher timeout; not prune | No |
| **Threshold** | Memory/FD > X | Resource-based prune trigger | ✓ Yes (memory, cc-status) |
| **SessionStart** | Before new run | Warn if session count > 5; suggest prune | ✓ Yes |

### 4.3 Orphan Detection

**Current**: Count processes matching `(node|bun|deno|cc-status)` + LSP/MCP patterns.

**Enhanced**: Process tree traversal — mark as orphan if `ppid` is not in process list (parent dead). Requires:

- `ps -eo pid,ppid` → build parent map
- For each candidate: walk up to root; if root is init (1) and no Cursor/Claude/Codex ancestor, treat as orphan

**Risk**: False positives (e.g. user closed terminal). Mitigation: only prune when count > threshold.

**Implementation**: `orphan-by-ppid` filters true orphans by checking process tree.

### 4.4 Pruning Strategies

| Strategy | Trigger | Pros | Cons |
|----------|---------|------|------|
| **Stop-only** | Every Stop | Simple, no daemon | May miss orphans if no Stop for long time |
| **Stop + Threshold** | Stop when count > N | Balanced | Current |
| **Stop + Periodic** | Stop + cron every 15 min | Catches long-idle orphans | Extra process |
| **Stop + Memory** | Stop when mem_avail < X | Resource-aware | Needs macOS fix |
| **All** | Stop + Periodic + Memory | Most robust | Most complex |

**Recommendation**: Stop + Threshold (current). Add Periodic as opt-in (`THGENT_AUTO_PRUNE_PERIODIC=1`, interval 15 min) for heavy users.

### 4.5 Multi-Agent / Multi-Tenant / Multi-Project

**Session Isolation**:

| Dimension | Current | Target |
|-----------|---------|--------|
| **Owner** | `user:projectname` or `user:projectname:scope` | Same |
| **Base dir** | `~/.cache/thegent/sessions` (global) | Option: `PROJECT_DIR/.thegent/sessions` per-project |
| **Run registry** | `run_registry.jsonl` per owner scope | Same |
| **Discovered agents** | `discovered/ppid_{ppid}.json` | Same |

**Per-project session dir** (optional): `THGENT_SESSION_DIR=./.thegent/sessions` would put sessions under project root. Enables isolation when multiple projects are open but increases risk of `.git` clutter if not ignored.

**Process Isolation**:

| Level | Current | Options |
|-------|---------|---------|
| **Process** | None | Docker (SANDBOXING_DESIGN Phase 2), Firecracker (Phase 3) |
| **Resource** | ConcurrencyController (global) | cgroups (Linux), resource limits (ulimit) |
| **Tenant** | Policy federation (WP-13001) | Phase 13 tenant boundary tests |

---

## 5. Resource Management

### 5.1 Resource Gates

**Gates** (from `LimitGateConfig`):

| Gate | Metric | Block When |
|------|--------|------------|
| **FD** | fd_used / fd_limit | ≥ 75% utilization |
| **Memory** | mem_available_mb | < 256 MB |
| **Load** | load_1m / cpu_count | ≥ 1.5 per CPU |

**Slot Calculation**:
```python
cpu_slots = min(max, cpu_count * 2)  # Base
fd_slots = headroom / 50  # FDs per slot
mem_slots = (available - 256) / 128  # MB per slot
load_slots = scaled_down_as_load_approaches_1.5x_cpu
effective_limit = min(cpu, fd, mem, load)
```

### 5.2 Dynamic Limits

**Flow**:
1. `sample_resources()` → ResourceSnapshot
2. `compute_dynamic_limit(snapshot, config, running_count)` → target_limit
3. `HysteresisController.get_limit(current, running, target)` → effective limit
4. `running_count < limit` → acquire succeeds

**Hysteresis Parameters**:
- `upper_threshold=0.8`: Scale UP when utilization > 80%
- `lower_threshold=0.4`: Scale DOWN when utilization < 40%
- `dwell_time_s=30`: Minimum time between limit changes

### 5.3 Platform-Specific Resource Sampling

**Linux**:
- Memory: `/proc/meminfo` → `MemAvailable`
- FD: `/proc/sys/fs/file-nr` → `fd_used / fd_limit`
- Load: `/proc/loadavg` → `load_1m`

**macOS**:
- Memory: `vm_stat` → parse `Pages free`, `Pages inactive`
- FD: `sysctl kern.num_files` → `fd_used / fd_limit`
- Load: `sysctl vm.loadavg` → `load_1m`

**Implementation**: `load_based_limits.py` uses platform detection and fallback to `vm_stat` on macOS.

---

## 6. Industry Systems & Patterns

### 6.1 Job Schedulers

| System | Domain | Features |
|--------|--------|----------|
| **Slurm** | HPC clusters | Partition, QoS, fairshare, backfill |
| **PBS Pro** | HPC | Job arrays, dependencies, reservations |
| **SGE (Sun Grid Engine)** | HPC | Queues, parallel jobs |
| **HTCondor** | Distributed | Matchmaking, DAG workflows, checkpointing |

**Concepts**:
- **Partition**: Logical grouping of nodes
- **QoS**: Quality of Service (limits, priorities)
- **Fairshare**: Proportional resource allocation
- **Backfill**: Schedule small jobs in gaps

### 6.2 Process Supervisors

| System | Domain | Features |
|--------|--------|----------|
| **supervisord** | Process management | Process groups, event listeners |
| **systemd** | Linux init | Units, dependencies, timers |
| **launchd** | macOS init | Plists, keep-alive, timers |

**thegent relevance**: Periodic prune uses launchd (macOS) / systemd (Linux) timers.

### 6.3 Container Orchestrators

| System | Domain | Features |
|--------|--------|----------|
| **Kubernetes** | Container orchestration | Pods, services, deployments, autoscaling |
| **Docker Swarm** | Container orchestration | Services, stacks, scaling |

**Concepts**:
- **Pod**: Smallest deployable unit (1+ containers)
- **Service**: Stable network endpoint
- **Deployment**: Desired state management
- **Autoscaling**: HPA (Horizontal Pod Autoscaler)

### 6.4 Task Queues

| System | Domain | Features |
|--------|--------|----------|
| **Celery** | Distributed task queue | Brokers (Redis, RabbitMQ), workers, routing |
| **RQ** | Simple task queue | Redis-backed, simple API |
| **BullMQ** | Node.js task queue | Redis-backed, job priorities, delays |

**Concepts**:
- **Broker**: Message queue (Redis, RabbitMQ)
- **Worker**: Process that executes tasks
- **Routing**: Task → queue → worker

### 6.5 Algorithms & Optimization

**Bin Packing**: Pack items into bins (minimize bins). Used in resource allocation.

**Fair Queuing**:
- **WFQ (Weighted Fair Queuing)**: Proportional share per flow
- **DRR (Deficit Round-Robin)**: Fair queuing with deficit tracking
- **Deficit Round-Robin**: Simple fair queuing

**Work Stealing**: Idle workers steal tasks from busy workers. Used in parallel computing.

**Priority Inversion**: Low-priority task holds resource needed by high-priority task. Mitigation: Priority inheritance.

**Admission Control**: Decide whether to accept new work. Used in ConcurrencyController.

**Backpressure**: Slow down producers when consumers are overloaded. Used in resource gates.

---

## 7. Implementation Roadmap

### 7.1 Phase 1: Immediate (Done + Small Enhancements)

| Task | Status | Effort |
|------|--------|--------|
| Auto-prune on Stop | ✓ Done | — |
| Config options (auto_prune, threshold, cooldown) | ✓ Done | — |
| Documentation (SWARM_PROCESS_OPTIMIZATIONS) | ✓ Done | — |
| Spotlight exclude in setup | ✓ Done | — |
| Session-start warning (>5 sessions → suggest prune) | ✓ Done | — |

### 7.2 Phase 2: Structural Depth (Done)

| Task | Description | Status |
|------|-------------|--------|
| macOS memory sampling | Add `vm_stat` path in `_get_memory_mb()` | ✓ Done |
| Memory-based prune trigger | Prune when `mem_available_mb < threshold` | ✓ Done |
| Periodic prune daemon | launchd (macOS) / systemd timer (Linux) | ✓ Done |
| Orphan-by-ppid | Prune only processes whose parent is dead | ✓ Done |
| Per-project session dir | `THGENT_SESSION_DIR=./.thegent/sessions` | ⏳ Pending |

### 7.3 Phase 3: MTSP (Process Optimization Plan)

| Task | Description | Effort |
|------|-------------|--------|
| LSP multiplexing | Single Serena daemon | 15–25 tool calls |
| Shared task worker | process-compose | 10–15 tool calls |
| In-process agent runner | ACE-style cwd isolation | 20–30 tool calls |
| Unified worker daemon | Consolidate task/perl/env | 15–20 tool calls |

### 7.4 Phase 4: Enterprise (Future)

| Task | Description | Effort |
|------|-------------|--------|
| cgroups per project | Linux resource limits | 15–25 tool calls |
| Docker runner | SANDBOXING_DESIGN Phase 2 | 25–40 tool calls |
| Fair queuing | Proportional share per tenant | 20–30 tool calls |
| Work stealing | Multi-machine task distribution | 30–50 tool calls |
| Deadline scheduling | EDF for agent runs | 25–35 tool calls |

---

## 8. Configuration Reference

### 8.1 Environment Variables

```bash
# Auto-prune configuration
THGENT_AUTO_PRUNE=1                    # Enable auto-prune on Stop
THGENT_AUTO_PRUNE_THRESHOLD=12         # Prune when count > this
THGENT_AUTO_PRUNE_COOLDOWN=300         # Seconds between prunes
THGENT_AUTO_PRUNE_PERIODIC=0           # Enable periodic prune (future)
THGENT_AUTO_PRUNE_PERIODIC_INTERVAL=900  # Seconds between periodic prunes
THGENT_AUTO_PRUNE_MEMORY_THRESHOLD_MB=512  # Prune when avail < this

# Session configuration
THGENT_SESSION_WARN_THRESHOLD=5        # Warn on run/start if sessions > this
THGENT_SESSION_DIR=                    # Empty = default; ./.thegent/sessions = per-project

# Load-based limits
THGENT_LOAD_BASED_LIMITS=1             # Enable dynamic limits
THGENT_HYSTERESIS_DWELL_TIME=30        # Seconds between limit changes
THGENT_HYSTERESIS_UPPER_THRESHOLD=0.8  # Scale UP when utilization > this
THGENT_HYSTERESIS_LOWER_THRESHOLD=0.4  # Scale DOWN when utilization < this
```

### 8.2 Config File (`config.py`)

```python
# Load thresholds
load_spike_threshold = 10  # Warn when load > this
load_surge_threshold = 20  # Block when load > this

# Resource gates
LimitGateConfig(
    fd_threshold=0.75,  # Block when FD ≥ 75%
    memory_threshold_mb=256,  # Block when memory < 256 MB
    load_threshold=1.5,  # Block when load ≥ 1.5× CPU
)
```

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue**: Auto-prune not running
- **Check**: `THGENT_AUTO_PRUNE=1` set?
- **Check**: Threshold exceeded? (`THGENT_AUTO_PRUNE_THRESHOLD`)
- **Check**: Cooldown active? (`THGENT_AUTO_PRUNE_COOLDOWN`)

**Issue**: Too many sessions running
- **Check**: `thegent mcp prune` manually
- **Check**: `THGENT_SESSION_WARN_THRESHOLD` set appropriately
- **Check**: Resource gates blocking? (`THGENT_LOAD_BASED_LIMITS`)

**Issue**: Resource gates too aggressive
- **Check**: `LimitGateConfig` thresholds
- **Check**: Hysteresis parameters (`THGENT_HYSTERESIS_*`)
- **Check**: Resource sampling working? (`sample_resources()`)

**Issue**: macOS memory sampling failing
- **Check**: `vm_stat` available? (`which vm_stat`)
- **Check**: `load_based_limits.py` using `vm_stat` fallback?

### 9.2 Debugging

**Enable debug logging**:
```bash
export THGENT_DEBUG=1
export THGENT_LOG_LEVEL=DEBUG
```

**Check resource sampling**:
```python
from thegent.load_based_limits import sample_resources

snapshot = sample_resources()
print(snapshot)
```

**Check ConcurrencyController**:
```python
from thegent.execution import ConcurrencyController

controller = ConcurrencyController()
result = controller.acquire("standard")
print(result)
```

---

## 10. References

### 10.1 Related Documentation

- [Swarm Process Optimizations](../reference/SWARM_PROCESS_OPTIMIZATIONS.md) - User-facing quick reference
- [Process Optimization Plan](../plans/PROCESS_OPTIMIZATION_PLAN.md) - MTSP roadmap
- [System Resources Research](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md) - FD, CPU, threads, ports
- [Advanced Strategies Research](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md) - Retry, backoff, circuit breaker
- [Smart Robust Strategies Research](./SMART_ROBUST_STRATEGIES_RESEARCH.md) - Process lifecycle, LSP multiplexing
- [Memory Optimization Plan](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md) - LSP triplet, cc-status bloat

### 10.2 Implementation Files

- **ConcurrencyController**: `src/thegent/execution.py`
- **ResourceSnapshot**: `src/thegent/load_based_limits.py`
- **HysteresisController**: `src/thegent/load_based_limits.py`
- **Auto-prune**: `hooks/prune-orphans-stop.sh`
- **Periodic prune**: `hooks/prune-periodic.sh`

### 10.3 External Resources

- **Slurm**: https://slurm.schedmd.com/
- **Kubernetes**: https://kubernetes.io/
- **Celery**: https://docs.celeryproject.org/
- **Fair Queuing**: https://en.wikipedia.org/wiki/Fair_queuing
- **Work Stealing**: https://en.wikipedia.org/wiki/Work_stealing

---

## 11. Summary

### 11.1 Key Takeaways

1. **Scheduling**: ConcurrencyController acts as long-term admission scheduler with dynamic load balancing
2. **Process Automation**: Auto-prune via Stop hooks, periodic timers, memory-based triggers
3. **Resource Management**: FD, memory, load gates with hysteresis to prevent thrashing
4. **Industry Patterns**: Job schedulers, orchestrators, task queues provide reference architectures

### 11.2 Next Steps

1. Implement per-project session dir (`THGENT_SESSION_DIR`)
2. Add fair queuing for proportional share per tenant
3. Implement LSP multiplexing (single Serena daemon)
4. Add cgroups per project (Linux resource limits)

### 11.3 Impact

- **Reliability**: Auto-prune prevents orphan process accumulation
- **Efficiency**: Dynamic limits optimize resource utilization
- **Stability**: Hysteresis prevents rapid oscillation
- **Scalability**: Resource gates prevent system overload

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SWARM_RESEARCH_INDEX.md](./SWARM_RESEARCH_INDEX.md) - Swarm research index
- [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md) - Process automation
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

*Generated: 2026-02-16 | Version: 1.0 | Status: Complete*

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

## Lane Assignment Rules

- Assign one owner per lane and record explicit deliverable + deadline before execution starts.
- Keep lanes independent by interface contract; block cross-lane edits unless a dependency handoff is agreed.
- Cap active lanes to current resource budget; queue overflow lanes instead of parallelizing blindly.
- Rebalance only at checkpoints (not continuously) using objective signals: blocked status, idle owner, or SLA risk.

## Swarm Completion Signals

- Every lane reports `Done` with: artifact path, validation command, and pass/fail result.
- All planned lanes are either completed or formally deferred with owner, reason, and next review date.
- Integration checks pass once on the merged surface (not just per-lane local checks).
- Final swarm closeout includes a concise summary of outcomes, known risks, and follow-up actions.

## Swarm Bottleneck Indicators

- Queue age exceeds one checkpoint interval for any high-priority lane without progress.
- One owner holds multiple dependency-critical tasks while other owners are idle.
- Rework rate rises (same file/component touched repeatedly across two or more handoffs).
- Validation latency dominates execution time (tests/review wait > implementation time).

## Lane Rebalancing Triggers

- Trigger when a critical lane is blocked for one full checkpoint and an unblocked owner is available.
- Trigger when lane cycle time is >2x swarm median for two consecutive checkpoints.
- Trigger when downstream lanes are starved by a single upstream dependency owner.
- Trigger when SLA/ship date risk appears and scope can be split without breaking interface contracts.

## Concurrency Ceiling Rules

- Set `max_active_lanes = min(ready_owners, dependency_frontier, resource_budget)` at each checkpoint.
- Never start a new lane when any ceiling is red (CPU/memory/load/test queue); queue it for next checkpoint.
- Reserve one lane-equivalent for integration/unblock work; do not consume 100% capacity with feature lanes.
- Increase ceiling by +1 only after one full checkpoint with stable validation latency and zero rollback events.

## Completion Handoff Protocol

- Handoff packet is mandatory: objective, touched paths, test command/result, open risks, and rollback note.
- Receiver must acknowledge ownership and restate first action before the sender closes the lane.
- Mark lane `Complete` only after receiver reproduces validation on their branch or merged surface.
- If acknowledgment or reproduction misses one checkpoint, auto-escalate to swarm lead for reassignment.

## Task Dependency Gate

- A task may start only when all declared upstream dependencies are marked `Done` with artifact path and validation evidence.
- If any dependency is `Blocked` or missing evidence, keep the task in `Queued` and assign a single unblock owner.
- At each checkpoint, re-validate dependency status before new lane activation; do not bypass for schedule pressure.
- Record every gate decision in the swarm log with task ID, dependency IDs, timestamp, and approver.

## Wave Shutdown Criteria

- End the wave only when all in-scope tasks are `Done` or explicitly deferred with owner and next checkpoint date.
- Require one final integration pass on merged scope with command + result captured in the closeout note.
- Confirm no unresolved `Critical`/`High` blockers remain; otherwise continue wave in reduced unblock mode.
- Publish a shutdown summary including completed tasks, deferred tasks, residual risks, and first actions for next wave.

## Lane Starvation Signals

- No commit, handoff, or status change for one checkpoint on a lane with ready dependencies.
- Two or more downstream lanes wait on one upstream owner for a full checkpoint.
- Lane queue age exceeds 2x swarm median while at least one owner is idle.
- Repeated unblock pings (>2) occur without a concrete next action or ETA.

## Recovery Dispatch Order

- Dispatch 1: Assign a temporary unblock owner to the highest-impact blocked upstream lane.
- Dispatch 2: Move one idle owner to the oldest starved downstream lane with ready inputs.
- Dispatch 3: Split oversized tasks (>1 checkpoint estimate) into atomic subtasks and re-queue immediately.
- Dispatch 4: Reserve one lane for integration risk burn-down before starting new feature lanes.

## Escalation Ownership Map

- Lane Owner: owns execution and must escalate `Blocked` status within one checkpoint with blocker, impact, and needed decision.
- Swarm Lead: triages all escalations, assigns unblock owner, and sets due time for resolution or reassignment.
- Domain Reviewer: provides binding technical decision on interface/quality disputes within the same checkpoint.
- Program Owner: resolves scope/SLA conflicts and approves defer/split actions when lead cannot clear risk.

## Lane Cooldown Policy

- After lane handoff or completion, enforce one checkpoint cooldown before assigning that owner another critical lane.
- During cooldown, owner may only do review, docs, or unblock support; no new dependency-critical coding starts.
- Cooldown ends early only if swarm lead records emergency override with reason, risk, and rollback owner.
- Repeated overrides in two consecutive checkpoints trigger automatic capacity reduction by one active lane.

## Lane Handoff Readiness

- Handoff only when acceptance criteria are met and lane status is `Ready for Handoff`.
- Attach required packet: changed paths, validation command/output, and known risk notes.
- Receiver must acknowledge ownership in the same checkpoint with first executable step.
- If acknowledgement is missing by next checkpoint, lane auto-reverts to sender and is escalated.

## Swarm Exit Checklist

- Confirm every in-scope lane is `Done` or deferred with owner, reason, and next checkpoint date.
- Run one final integration validation on merged scope and record command plus result.
- Publish residual risks with severity, owner, and explicit mitigation/rollback action.
- Close swarm only after lead posts final summary and next-wave first actions.

## Lane Timeout Policy

- Define a per-lane timeout at lane start (default: one checkpoint for blocked work, two checkpoints for active work).
- If no verifiable progress artifact appears before timeout, lane status changes to `Timed Out` automatically.
- On timeout, swarm lead must reassign owner or split scope within the same checkpoint.
- Timed-out lanes cannot return to `Active` until a new owner, next action, and deadline are recorded.

## Escalation Acknowledgement Rules

- Every escalation must be acknowledged by the assigned decision owner within the same checkpoint.
- Acknowledgement must include: decision owner, decision ETA, and immediate containment action.
- If acknowledgement is missing by checkpoint close, auto-page swarm lead and program owner.
- Unacknowledged escalations block new lane starts in the affected dependency chain until acknowledged.
