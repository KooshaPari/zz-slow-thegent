<DONE>
# Swarm Optimization, Management & Scheduling — Deep Research

> **Purpose**: Deep dive into optimization, management, and scheduling systems relevant to multi-agent, multi-tenant, multi-project local swarms.
> **Status**: Research | **Date**: 2026-02-16
> **Related**: [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md), [PHASE_5_SCALE_ROBUSTNESS_DEPTH](../reference/PHASE_5_SCALE_ROBUSTNESS_DEPTH.md), [SWARM_MEMORY_COORDINATION_DEPTH](../reference/SWARM_MEMORY_COORDINATION_DEPTH.md)

---

## How to Use This Doc

- **Theory**: Part I (§1–8) — scheduling disciplines, load balancing, OS schedulers.
- **thegent mapping**: Part II (§9–14) — how current code maps to theory; gaps.
- **Industry systems**: Part III (§15–22) — job schedulers, orchestrators, workload managers.
- **Algorithms & optimization**: Part IV (§23–30) — bin packing, fair queuing, work stealing.
- **Roadmap**: Part V (§31–35) — phased enhancements for thegent.

---

## Table of Contents

| §                                      | Section                                                          |
| -------------------------------------- | ---------------------------------------------------------------- |
| **Part I: Scheduling Theory**          |                                                                  |
| 1                                      | Scheduling Fundamentals                                          |
| 2                                      | OS Scheduler Types (Long / Medium / Short-Term)                  |
| 3                                      | Scheduling Disciplines & Algorithms                              |
| 4                                      | Load Balancing: Static vs Dynamic                                |
| 5                                      | Work-Conserving vs Non-Work-Conserving                           |
| 6                                      | Fairness, Starvation, and Deadlines                              |
| 7                                      | Real-Time and Soft Real-Time                                     |
| 8                                      | Scheduling Optimization Problems (Makespan, Flow-Shop, Job-Shop) |
| **Part II: thegent Mapping**           |                                                                  |
| 9                                      | Current thegent Scheduling & Control                             |
| 10                                     | ConcurrencyController Deep Dive                                  |
| 11                                     | HysteresisController and Anti-Thrashing                          |
| 12                                     | ResourceSnapshot and Limit Gates                                 |
| 13                                     | Gaps vs Theory                                                   |
| 14                                     | DAG-Based Task Scheduling (thegent DAG)                          |
| **Part III: Industry Systems**         |                                                                  |
| 15                                     | Job Schedulers (Slurm, PBS, SGE, HTCondor)                       |
| 16                                     | Process Supervisors (supervisord, systemd, launchd)              |
| 17                                     | Container Orchestrators (Kubernetes, Docker Swarm)               |
| 18                                     | Workload Managers (IBM WLM, Mesos)                               |
| 19                                     | Task Queues (Celery, RQ, BullMQ)                                 |
| 20                                     | Event-Driven and Reactive Schedulers                             |
| 21                                     | Multi-Agent Task Allocation (Academic)                           |
| 22                                     | AI/LLM-Specific: Token Buckets, Rate Limiters                    |
| **Part IV: Algorithms & Optimization** |                                                                  |
| 23                                     | Bin Packing and Resource Allocation                              |
| 24                                     | Fair Queuing (WFQ, DRR, Deficit Round-Robin)                     |
| 25                                     | Work Stealing and Work Sharing                                   |
| 26                                     | Priority Inversion and Priority Inheritance                      |
| 27                                     | Admission Control and Backpressure                               |
| 28                                     | Gang Scheduling and Coscheduling                                 |
| 29                                     | Predictive and Adaptive Scheduling                               |
| 30                                     | Metaheuristics (Genetic, Simulated Annealing)                    |
| **Part V: Roadmap for thegent**        |                                                                  |
| 31                                     | Phase 1: Enhance Current Controllers                             |
| 32                                     | Phase 2: Add Scheduling Disciplines                              |
| 33                                     | Phase 3: Distributed Scheduling (Redis)                          |
| 34                                     | Phase 4: Advanced Optimization                                   |
| 35                                     | Cross-References & Bibliography                                  |

---

## Part I: Scheduling Theory

### 1. Scheduling Fundamentals

**Scheduling** is the action of assigning resources to perform tasks. Resources may be processors, network links, memory, or I/O devices. Tasks may be threads, processes, or data flows.

**Goals** (often conflicting):

| Goal                 | Description                                    |
| -------------------- | ---------------------------------------------- |
| **Fairness**         | Equal or proportional resource share per party |
| **Throughput**       | Maximize work completed per time unit          |
| **Latency**          | Minimize time from ready to first output       |
| **Response time**    | Minimize wait until execution starts           |
| **Deadline meeting** | Real-time: meet hard/soft deadlines            |

**Scheduler**: The mechanism that performs scheduling. May be centralized (master) or distributed.

---

### 2. OS Scheduler Types (Long / Medium / Short-Term)

| Type                      | Frequency     | Role                                                                                                               |
| ------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Long-term (admission)** | Infrequent    | Decides which jobs enter the ready queue; controls degree of multiprogramming; balances I/O-bound vs CPU-bound mix |
| **Medium-term**           | Periodic      | Swaps processes in/out of memory; frees RAM; may perform demand paging                                             |
| **Short-term (CPU)**      | Very frequent | Picks next process to run; preemptive or cooperative; time-slice based                                             |

**thegent relevance**: ConcurrencyController acts as a **long-term admission scheduler** — it decides whether a new agent run may start (`acquire()`). It does not schedule CPU time (OS does that) but **admission** of concurrent runs.

---

### 3. Scheduling Disciplines & Algorithms

| Algorithm                         | Description                     | Pros                            | Cons                                       |
| --------------------------------- | ------------------------------- | ------------------------------- | ------------------------------------------ |
| **FCFS/FIFO**                     | First come, first served        | Simple, no starvation           | Convoy effect; poor latency for short jobs |
| **Round-Robin**                   | Fixed time slice per process    | Fair, good response time        | Overhead; deadlines rarely met             |
| **Priority**                      | Fixed or dynamic priority       | Deadlines via high priority     | Starvation of low priority                 |
| **Shortest Job First (SJF)**      | Shortest estimated time first   | Max throughput                  | Needs estimates; starvation of long jobs   |
| **Earliest Deadline First (EDF)** | Schedule by deadline            | Optimal for real-time           | Needs deadlines; complex                   |
| **Multilevel Feedback Queue**     | Multiple queues; promote/demote | Balances latency and throughput | Complex tuning                             |
| **Fair Queuing**                  | Proportional share              | Fairness                        | Overhead                                   |
| **Proportional Fair**             | Balance throughput and fairness | Used in wireless                | Channel-dependent                          |

**thegent relevance**: Current logic is **priority-like** (critical lane gets 2× slots) and **threshold-based** (gates block when near capacity). No explicit FCFS, RR, or EDF.

---

### 4. Load Balancing: Static vs Dynamic

| Type        | Knowledge                         | Communication       | Use Case                          |
| ----------- | --------------------------------- | ------------------- | --------------------------------- |
| **Static**  | Assumed task sizes, arrival times | None at runtime     | Homogeneous workloads             |
| **Dynamic** | Current load per node             | Continuous exchange | Heterogeneous, variable workloads |

**Static methods**: Round-robin, hash-based, power-of-two-choices (pick 2 random, choose better).

**Dynamic methods**: Least connections, least response time, work stealing, master-worker.

**thegent relevance**: ConcurrencyController is **dynamic** — it samples FD, memory, load at `acquire()` time. No static pre-assignment.

---

### 5. Work-Conserving vs Non-Work-Conserving

| Type                    | Behavior                                                     |
| ----------------------- | ------------------------------------------------------------ |
| **Work-conserving**     | Never leaves resources idle if work is ready                 |
| **Non-work-conserving** | May idle despite pending work (e.g. for fairness, deadlines) |

**thegent relevance**: Current design is work-conserving — if a slot is free and gates allow, `acquire()` returns true. No explicit "hold back for fairness" logic.

---

### 6. Fairness, Starvation, and Deadlines

- **Starvation**: A task never gets resources. Mitigations: aging, priority boost, fair queuing.
- **Fairness**: Max-min fairness, proportional fairness, equal share.
- **Deadlines**: Hard (must meet) vs soft (best effort). EDF for hard real-time.

**thegent relevance**: Critical lane (2× slots) can starve standard lane under load. No deadline model for agent runs.

---

### 7. Real-Time and Soft Real-Time

| Class              | Guarantee                       | Example           |
| ------------------ | ------------------------------- | ----------------- |
| **Hard real-time** | Missed deadline = failure       | Avionics, medical |
| **Soft real-time** | Best effort; occasional miss OK | Video, gaming     |
| **Best-effort**    | No deadline                     | Batch, web        |

**thegent relevance**: Agent runs are best-effort. No real-time guarantees. Optional: soft deadlines for "finish within N minutes" (future).

---

### 8. Scheduling Optimization Problems (Makespan, Flow-Shop, Job-Shop)

| Problem       | Description                         | Complexity |
| ------------- | ----------------------------------- | ---------- |
| **Makespan**  | Minimize total completion time      | NP-hard    |
| **Flow-shop** | n jobs, m stations, fixed order     | NP-hard    |
| **Job-shop**  | n jobs, m machines, arbitrary order | NP-hard    |
| **Open-shop** | n jobs, m stations, free order      | NP-hard    |

**thegent relevance**: DAG sync and task ordering (MTSP, process-compose) resemble job-shop — tasks have dependencies; optimal ordering is hard. Heuristics (topological sort, critical path) used.

---

## Part II: thegent Mapping

### 9. Current thegent Scheduling & Control

| Component                 | Location                    | Role                                       |
| ------------------------- | --------------------------- | ------------------------------------------ |
| **ConcurrencyController** | `execution.py`              | Admission control for agent runs           |
| **HysteresisController**  | `load_based_limits.py`      | Anti-thrashing; dwell time                 |
| **ResourceSnapshot**      | `load_based_limits.py`      | FD, memory, load sample                    |
| **compute_dynamic_limit** | `load_based_limits.py`      | Gate-based slot calculation                |
| **LimitGateConfig**       | `load_based_limits.py`      | Thresholds per resource                    |
| **Gardener spawn limits** | `gardener-spawn-manager.sh` | Disk-based backpressure                    |
| **Load thresholds**       | `config.py`                 | Spike (10), surge (20) for traffic shaping |

---

### 10. ConcurrencyController Deep Dive

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

---

### 11. HysteresisController and Anti-Thrashing

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

---

### 12. ResourceSnapshot and Limit Gates

**Gates** (from `LimitGateConfig`):

| Gate       | Metric              | Block When        |
| ---------- | ------------------- | ----------------- |
| **FD**     | fd_used / fd_limit  | ≥ 75% utilization |
| **Memory** | mem_available_mb    | < 256 MB          |
| **Load**   | load_1m / cpu_count | ≥ 1.5 per CPU     |

**Slot calculation**:

- `cpu_slots = min(max, cpu_count * 2)` (base)
- `fd_slots` = headroom / 50 FDs per slot
- `mem_slots` = (available - 256) / 128 MB per slot
- `load_slots` = scaled down as load approaches 1.5× CPU

**Effective limit** = min(cpu, fd, mem, load), clamped to [min_slots, max_slots].

**macOS gap**: `_get_memory_mb()` uses `/proc/meminfo` (Linux only). macOS needs `vm_stat` (see SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH §11).

---

### 13. Gaps vs Theory

| Theory / System            | thegent Status        | Gap                           |
| -------------------------- | --------------------- | ----------------------------- |
| **Admission control**      | ConcurrencyController | ✓ Present                     |
| **Dynamic load balancing** | Resource sampling     | ✓ Present                     |
| **Hysteresis**             | HysteresisController  | ✓ Present                     |
| **Priority scheduling**    | Critical lane 2×      | Partial; no general priority  |
| **Fair queuing**           | None                  | No proportional share         |
| **Work stealing**          | None                  | Single machine; no steal      |
| **Deadline scheduling**    | None                  | No EDF or deadlines           |
| **Per-tenant limits**      | None                  | Global only                   |
| **Distributed scheduling** | None                  | Single node                   |
| **Job queue**              | run_registry          | Log only; no queue discipline |
| **Preemption**             | None                  | No pause/resume of runs       |

---

### 14. DAG-Based Task Scheduling (thegent DAG)

**Current**: `dag sync`, `dag run` — topological order, run next-ready tasks.

**Pattern**: Job-shop-like — tasks have dependencies; run when predecessors complete.

**Possible enhancements**:

- **Critical path**: Prioritize tasks on longest path.
- **Resource-aware**: Don't start task if gates would be exceeded.
- **Earliest start time (EST)**: Schedule by EST from topological sort.
- **Batch scheduling**: Group independent tasks; run in parallel up to limit.

---

## Part III: Industry Systems

### 15. Job Schedulers (Slurm, PBS, SGE, HTCondor)

| System                    | Domain       | Features                                  |
| ------------------------- | ------------ | ----------------------------------------- |
| **Slurm**                 | HPC clusters | Partition, QoS, fairshare, backfill       |
| **PBS Pro**               | HPC          | Job arrays, dependencies, reservations    |
| **SGE (Sun Grid Engine)** | HPC          | Queues, parallel jobs                     |
| **HTCondor**              | Distributed  | Matchmaking, DAG workflows, checkpointing |

**Concepts**:

- **Partitions**: Group of nodes; jobs request partition.
- **QoS**: Quality of service; limits, priorities.
- **Fairshare**: Historical usage affects priority.
- **Backfill**: Run small jobs in gaps to improve utilization.

**thegent relevance**: Local swarms don't need full HPC scheduler. Concepts: partitions → projects; QoS → lanes; fairshare → future.

---

### 16. Process Supervisors (supervisord, systemd, launchd)

| System          | Role                                                    |
| --------------- | ------------------------------------------------------- |
| **supervisord** | Process groups; restart on crash; stdout/stderr capture |
| **systemd**     | Service lifecycle; timers; cgroups                      |
| **launchd**     | macOS; daemons; periodic jobs                           |

**thegent relevance**: `thegent mcp service install` (launchd/systemd) for persistent MCP. process-compose for multi-process. Prune targets orphan processes, not supervised ones.

---

### 17. Container Orchestrators (Kubernetes, Docker Swarm)

| System           | Scheduling                                                |
| ---------------- | --------------------------------------------------------- |
| **Kubernetes**   | kube-scheduler: bin packing, affinity, taints/tolerations |
| **Docker Swarm** | Spread, binpack strategies                                |

**Kubernetes scheduler**: Filters (feasible nodes) → Scores (prefer best) → Bind. Extensible via scheduler framework.

**thegent relevance**: Cloud agents may run in K8s. Local thegent is single-node; no pod scheduling. Future: thegent as K8s controller for agent pods.

---

### 18. Workload Managers (IBM WLM, Mesos)

| System                   | Role                                                           |
| ------------------------ | -------------------------------------------------------------- |
| **IBM Workload Manager** | Policy-based CPU, memory, I/O allocation                       |
| **Apache Mesos**         | Resource offers; frameworks (Marathon, Chronos) accept/decline |

**Mesos**: Two-level scheduling. Mesos offers resources; framework decides which tasks to run. Dominant resource fairness (DRF).

**thegent relevance**: DRF could inform multi-tenant fairness. Not implemented.

---

### 19. Task Queues (Celery, RQ, BullMQ)

| System     | Backend         | Features                            |
| ---------- | --------------- | ----------------------------------- |
| **Celery** | Redis, RabbitMQ | Task routing, retries, rate limits  |
| **RQ**     | Redis           | Simple; Python                      |
| **BullMQ** | Redis           | Node.js; priorities, delays, repeat |

**Concepts**: Producer enqueues; workers consume. Priorities, rate limits, retries.

**thegent relevance**: run_registry is not a queue. Could add Redis-backed queue for deferred runs (future).

---

### 20. Event-Driven and Reactive Schedulers

**Reactive**: React to events (task done, resource free) rather than polling.

**Examples**: Rx, reactive streams, async/await with event loop.

**thegent relevance**: Hook system is event-driven (Stop, PostToolUse). ConcurrencyController is poll-based (sample at acquire). Could add event-driven scale-down when run completes.

---

### 21. Multi-Agent Task Allocation (Academic)

**Taxonomy**:

- **Contract net**: Auction; manager offers task; bidders respond.
- **Market-based**: Prices; agents buy/sell tasks.
- **Coalition formation**: Agents form teams for tasks.
- **Stigmergy**: Environment-mediated (pheromones); see SWARM_MEMORY_COORDINATION_DEPTH.

**thegent relevance**: Stigmergy via WORK_STREAM; gardener spawns incorporator. No contract net or market. Future: task auction for distributed agents.

---

### 22. AI/LLM-Specific: Token Buckets, Rate Limiters

| Mechanism               | Use                                |
| ----------------------- | ---------------------------------- |
| **Token bucket**        | Smooth burst; refill rate          |
| **Leaky bucket**        | Strict rate                        |
| **Sliding window**      | Limit per window                   |
| **Provider throttling** | OpenAI, Anthropic per-model limits |

**thegent relevance**: ConcurrencyController gates process count, not API calls. Provider rate limits are separate (cliproxy, cost governance). Could add token-bucket for API calls.

---

## Part IV: Algorithms & Optimization

### 23. Bin Packing and Resource Allocation

**Problem**: Pack items (tasks) into bins (nodes/slots) to minimize bins or maximize utilization.

**Variants**: First-fit, best-fit, worst-fit. Online vs offline.

**thegent relevance**: `compute_dynamic_limit` effectively does "how many more items fit" given FD/mem/load. Not explicit bin packing; more like capacity check.

---

### 24. Fair Queuing (WFQ, DRR, Deficit Round-Robin)

| Algorithm                         | Idea                                    |
| --------------------------------- | --------------------------------------- |
| **Weighted Fair Queuing (WFQ)**   | Virtual finish time; proportional share |
| **Deficit Round-Robin (DRR)**     | Quantum per flow; deficit carries over  |
| **Start-Time Fair Queuing (SFQ)** | Virtual start time                      |

**thegent relevance**: No fair queuing. All runs in same lane treated equally (FCFS). Critical lane gets 2× — simple priority, not WFQ.

---

### 25. Work Stealing and Work Sharing

**Work stealing**: Idle worker steals from busy worker's queue.

**Work sharing**: Overloaded worker pushes to idle.

**thegent relevance**: Single machine; no steal. Future: distributed agents could steal tasks from overloaded nodes.

---

### 26. Priority Inversion and Priority Inheritance

**Priority inversion**: Low-priority task holds lock; high-priority waits.

**Priority inheritance**: Low-priority task inherits high priority while holding lock.

**thegent relevance**: ConcurrencyController has no locks on slots (check-then-act). Possible inversion if critical lane starved by many standard runs — mitigation: critical gets 2×.

---

### 27. Admission Control and Backpressure

**Admission control**: Reject or delay new work when system overloaded.

**Backpressure**: Propagate "slow down" signal upstream.

**thegent relevance**: `acquire()` returning false is admission control. Load thresholds (spike, surge) trigger traffic shaping. No explicit backpressure to IDE or caller beyond "cannot start."

---

### 28. Gang Scheduling and Coscheduling

**Gang scheduling**: Related processes run together (all or nothing).

**Coscheduling**: Interacting processes scheduled to avoid blocking each other.

**thegent relevance**: DAG tasks may have dependencies; no gang semantics. process-compose runs service groups together.

---

### 29. Predictive and Adaptive Scheduling

**Predictive**: Use history to estimate task duration; schedule accordingly.

**Adaptive**: Adjust based on observed behavior (e.g. HysteresisController).

**thegent relevance**: HysteresisController is adaptive. No predictive scheduling (no task duration estimates).

---

### 30. Metaheuristics (Genetic, Simulated Annealing)

**Use**: NP-hard scheduling (job-shop, flow-shop). Genetic algorithms, simulated annealing, tabu search for near-optimal solutions.

**thegent relevance**: DAG ordering could use heuristics. Not implemented. Overkill for current scale.

---

## Part V: Roadmap for thegent

### 31. Phase 1: Enhance Current Controllers

| Task                    | Description                      | Effort         |
| ----------------------- | -------------------------------- | -------------- |
| macOS vm_stat           | Fix `_get_memory_mb()` for macOS | 4–6 tool calls |
| Configurable hysteresis | Expose upper/lower/dwell via env | 2–3 tool calls |
| Per-gate logging        | Log which gate limited slots     | 2–3 tool calls |
| Critical lane guarantee | Reserve min slots for critical   | 4–6 tool calls |

---

### 32. Phase 2: Add Scheduling Disciplines

| Task                   | Description                            | Effort           |
| ---------------------- | -------------------------------------- | ---------------- |
| Priority queue         | Per-run priority; schedule by priority | 10–15 tool calls |
| Fair-share placeholder | Per-owner usage tracking               | 15–20 tool calls |
| Soft deadlines         | Optional "finish by" for runs          | 8–12 tool calls  |
| FCFS within lane       | Explicit queue order                   | 4–6 tool calls   |

---

### 33. Phase 3: Distributed Scheduling (Redis)

| Task                     | Description                       | Effort           |
| ------------------------ | --------------------------------- | ---------------- |
| Redis-backed limit       | Distributed ConcurrencyController | 15–25 tool calls |
| Redlock for acquire      | Distributed mutex                 | 8–12 tool calls  |
| Cross-instance run count | Aggregate running across nodes    | 10–15 tool calls |
| Partition by swarm_id    | Per-swarm limits                  | 6–10 tool calls  |

---

### 34. Phase 4: Advanced Optimization

| Task                        | Description                    | Effort           |
| --------------------------- | ------------------------------ | ---------------- |
| Token bucket for API        | Rate limit per provider        | 10–15 tool calls |
| DAG critical path           | Prioritize critical-path tasks | 15–20 tool calls |
| Work stealing (distributed) | Steal from overloaded node     | 25–40 tool calls |
| Predictive scaling          | Use run duration history       | 20–30 tool calls |

---

### 35. Cross-References & Bibliography

| Doc                                                                                             | Relevance                                           |
| ----------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)           | Prune, triggers, discovery                          |
| [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md) | Retry, backoff, circuit breaker, bulkhead, fairness |
| [PHASE_5_SCALE_ROBUSTNESS_DEPTH](../reference/PHASE_5_SCALE_ROBUSTNESS_DEPTH.md)                | Redis, adaptive concurrency                         |
| [SWARM_MEMORY_COORDINATION_DEPTH](../reference/SWARM_MEMORY_COORDINATION_DEPTH.md)              | Blackboard, stigmergy                               |
| [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md)                              | MTSP, process consolidation                         |
| Wikipedia: Scheduling (computing)                                                               | OS schedulers, disciplines                          |
| Wikipedia: Load balancing (computing)                                                           | Static/dynamic, work stealing                       |

---

## 36. Scheduler Comparison Matrix

### 36.1 Algorithm Comparison

| Algorithm       | Complexity | Fairness        | Latency        | Deadlines  | Starvation | Use Case          |
| --------------- | ---------- | --------------- | -------------- | ---------- | ---------- | ----------------- |
| **FCFS**        | O(1)       | Low             | Poor (convoy)  | No         | No         | Batch jobs        |
| **Round-Robin** | O(1)       | High            | Good           | No         | No         | Time-sharing      |
| **Priority**    | O(log n)   | Low             | Variable       | No         | Yes        | Real-time         |
| **SJF**         | O(n log n) | Low             | Best for short | No         | Yes        | Interactive       |
| **EDF**         | O(n)       | Medium          | Optimal        | Yes (hard) | No         | Hard real-time    |
| **MLFQ**        | O(n log k) | High            | Good           | Soft       | No         | General-purpose   |
| **WFQ**         | O(log n)   | High (weighted) | Good           | Soft       | No         | Network QoS       |
| **DRR**         | O(1)       | High            | Good           | Soft       | No         | Packet scheduling |

### 36.2 Industry System Comparison

| System          | Type               | Scalability   | Fairness    | Distributed | Persistence | thegent Fit         |
| --------------- | ------------------ | ------------- | ----------- | ----------- | ----------- | ------------------- |
| **Slurm**       | Job scheduler      | 100K+ nodes   | Fairshare   | Yes         | Checkpoint  | Low (HPC focus)     |
| **Kubernetes**  | Orchestrator       | 10K+ nodes    | Pod QoS     | Yes         | Etcd        | Medium (heavy)      |
| **Celery**      | Task queue         | 1000s workers | Rate limits | Optional    | Redis       | High                |
| **systemd**     | Init/supervisor    | Single node   | No          | No          | No          | Low (not for tasks) |
| **supervisord** | Process supervisor | Single node   | No          | No          | PID file    | Medium              |
| **Mesos**       | Resource manager   | 10K+ nodes    | DRF         | Yes         | Zookeeper   | Low (complex)       |
| **HTCondor**    | Distributed batch  | 1000s nodes   | Claim types | Yes         | Checkpoint  | Low (batch)         |
| **Rancher**     | K8s manager        | Large         | Yes         | Yes         | Etcd        | Medium              |

### 36.3 thegent Controller Mapping

| Component             | Algorithm                       | Configurable | Extensions                 |
| --------------------- | ------------------------------- | ------------ | -------------------------- |
| ConcurrencyController | Threshold-based admission       | Yes          | Priority lanes, fair-share |
| HysteresisController  | Hysteresis (up/down thresholds) | Yes          | Adaptive thresholds        |
| ResourceSnapshot      | Sampling-based                  | Yes          | More metrics               |
| DAG Scheduler         | Topological sort                | No           | Critical path, batch       |
| load_based_limits     | Min-limit (CPU/FD/Mem)          | Yes          | Thread count, ports        |

### 36.4 Selection Decision Matrix

| Requirement                | Recommended                 | Alternative     |
| -------------------------- | --------------------------- | --------------- |
| Single-node, few tasks     | systemd                     | supervisord     |
| Multi-worker, Redis-backed | Celery + RQ                 | BullMQ          |
| Container orchestration    | Kubernetes                  | Docker Swarm    |
| HPC cluster                | Slurm                       | PBS Pro         |
| Agent scheduling (thegent) | ConcurrencyController + DAG | Extend with WFQ |
| Real-time tasks            | EDF + Priority              | MLFQ            |

---

## 37. Practical Implementation Checklist

### 37.1 Phase 1: Quick Wins

- [ ] Fix macOS vm_stat sampling
- [ ] Expose hysteresis parameters via env
- [ ] Add per-gate logging
- [ ] Implement critical lane reservation

### 37.2 Phase 2: Scheduling Disciplines

- [ ] Add priority queue for runs
- [ ] Implement FCFS ordering within lanes
- [ ] Add per-owner usage tracking
- [ ] Support soft deadlines

### 37.3 Phase 3: Distributed

- [ ] Redis-backed concurrency limits
- [ ] Redlock for atomic acquire
- [ ] Cross-instance run aggregation
- [ ] Per-swarm partitioning

### 37.4 Phase 4: Advanced

- [ ] Token bucket for API rate limits
- [ ] DAG critical-path prioritization
- [ ] Distributed work stealing
- [ ] Predictive scaling

---

## Document Changelog

| Date       | Change                                                                             |
| ---------- | ---------------------------------------------------------------------------------- |
| 2026-02-16 | Initial: scheduling theory, thegent mapping, industry systems, algorithms, roadmap |
| 2026-02-17 | Extended: Scheduler comparison matrix (§36), Implementation checklist (§37)        |

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Scheduler comparison matrix (§36), Practical implementation checklist (§37)

| Section | Added Content                                                                  |
| ------- | ------------------------------------------------------------------------------ |
| §36.1   | Algorithm Comparison Matrix (FCFS, RR, Priority, SJF, EDF, MLFQ, WFQ, DRR)     |
| §36.2   | Industry System Comparison (Slurm, K8s, Celery, systemd, etc.)                 |
| §36.3   | thegent Controller Mapping (ConcurrencyController, HysteresisController, etc.) |
| §36.4   | Selection Decision Matrix by requirement                                       |
| §37     | Practical Implementation Checklist for Phases 1-4                              |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SWARM_COMPLETE.md](./SWARM_COMPLETE.md) - Swarm guide
- [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md) - Process automation
- [SWARM_RESEARCH_INDEX.md](./SWARM_RESEARCH_INDEX.md) - Swarm research index
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
