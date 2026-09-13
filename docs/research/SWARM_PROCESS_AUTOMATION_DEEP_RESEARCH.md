<DONE>
# Swarm Process Automation — Deep Research & Plan

> **Purpose**: Research and plan for automatic process pruning and long-term optimizations for multi-agent, multi-tenant, multi-project local swarms.
> **Status**: Research | **Date**: 2026-02-16
> **Related**: [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md), [SWARM_PROCESS_OPTIMIZATIONS](../reference/SWARM_PROCESS_OPTIMIZATIONS.md), [SWARM_MEMORY_COORDINATION_DEPTH](../reference/SWARM_MEMORY_COORDINATION_DEPTH.md)

---

## How to Use This Doc

- **Quick reference**: [SWARM_PROCESS_OPTIMIZATIONS](../reference/SWARM_PROCESS_OPTIMIZATIONS.md) — user-facing setup.
- **Implementation**: Sections 5–7, 17 — roadmap, config, dependency DAG.
- **Deep dive**: Sections 9–16 — architecture, algorithms, platform details.
- **Wider scope**: Part II (§20–26) — platforms, resources, deployment models.
- **Operational**: Part III (§27–30) — edge cases, security, failure modes.
- **Optimization & scheduling**: [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) — scheduling theory, load balancing, industry systems, thegent mapping.

---

## Table of Contents

| §                                      | Section                                                       |
| -------------------------------------- | ------------------------------------------------------------- |
| 1                                      | Executive Summary                                             |
| 2                                      | Current State Analysis                                        |
| 3                                      | Automation Taxonomy                                           |
| 4                                      | Multi-Agent / Multi-Tenant / Multi-Project Deep Dive          |
| 5                                      | Long-Term Optimization Roadmap                                |
| 6                                      | Trigger Design                                                |
| 7                                      | Configuration Schema                                          |
| 8                                      | Cross-References                                              |
| 9                                      | Orphan Process Theory (External Research)                     |
| 10                                     | Discovery Architecture (Codebase Deep Dive)                   |
| 11                                     | macOS Memory Sampling (Technical Spec)                        |
| 12                                     | Periodic Prune: launchd / systemd                             |
| 13                                     | Failure Modes & Safety                                        |
| 14                                     | IDE Hook Flow (Touchpoint Deep Dive)                          |
| 15                                     | Alternative Strategies (Beyond Prune)                         |
| 16                                     | Process Tree: Orphan-by-PPID Algorithm                        |
| 17                                     | Implementation Dependency DAG                                 |
| 18                                     | Quantitative Targets                                          |
| **Part II: Wider Scope**               |                                                               |
| 20                                     | Platform Ecosystem (Zed, Windsurf, Cline, Continue, OpenCode) |
| 21                                     | Resource Types Beyond CPU/Memory                              |
| 22                                     | Dev Containers & Remote Development                           |
| 23                                     | Industry Tools & Patterns                                     |
| 24                                     | Multi-Machine & Distributed Swarms                            |
| 25                                     | Cloud vs Local Tradeoffs                                      |
| 26                                     | Compliance & Audit                                            |
| **Part III: Deeper Dimensions**        |                                                               |
| 27                                     | Per-Platform Edge Cases                                       |
| 28                                     | Security Implications                                         |
| 29                                     | Failure Mode Taxonomy                                         |
| 30                                     | Adjacent Research & Standards                                 |
| 31                                     | Appendix: Process Patterns                                    |
| **Part IV: Optimization & Scheduling** |                                                               |
| 32                                     | Optimization & Scheduling Deep Research (Companion Doc)       |
| 33                                     | Smart & Robust Strategies (Companion Doc)                     |

---

## 1. Executive Summary

**Question**: Can redundant process pruning (and similar) be automated rather than manual? What other long-term optimizations ensure multi-agent, multi-tenant, multi-project local swarms work smoothly?

**Answer**: Yes—pruning can be automated via Stop hooks (implemented). Deeper automation requires: (a) multiple trigger types beyond Stop, (b) per-project isolation and resource partitioning, (c) structural process consolidation (MTSP), and (d) cross-platform resource sampling.

---

## 2. Current State Analysis

### 2.1 What Exists Today

| Capability                | Location                    | Trigger              | Notes                                                    |
| ------------------------- | --------------------------- | -------------------- | -------------------------------------------------------- |
| **Auto-prune**            | `prune-orphans-stop.sh`     | Stop                 | Opt-in via `THGENT_AUTO_PRUNE=1`; threshold + cooldown   |
| **Manual prune**          | `thegent mcp prune`         | CLI                  | Patterns: LSPs, MCP servers, cc-status, bun, deno        |
| **Load thresholds**       | `config.py`                 | Session start        | `load_spike_threshold` (10), `load_surge_threshold` (20) |
| **ConcurrencyController** | `execution.py`              | `acquire()`          | FD/Mem/CPU gates when `load_based=True`                  |
| **ResourceSnapshot**      | `load_based_limits.py`      | `sample_resources()` | FD, memory, load avg; **Linux** `/proc/meminfo` only     |
| **HysteresisController**  | `load_based_limits.py`      | `get_limit()`        | Prevents thrashing; dwell time 30s                       |
| **Gardener spawn limits** | `gardener-spawn-manager.sh` | Spawn                | `GARDENER_MIN_USAGE_PERCENT=15` (disk)                   |
| **Session scoping**       | `cli_impl.py`               | Run                  | `session_dir / owner_key` = `user:projectname`           |

### 2.2 Gaps Identified

| Gap                                | Impact                                                                                                     | Severity |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------- |
| **Session dir is global**          | `~/.cache/thegent/sessions` — all projects share; no per-project isolation of session state                | Medium   |
| ~~macOS memory sampling~~          | ~~vm_stat fallback missing~~ → **Done**: `load_based_limits` + `prune-orphans-stop` use `vm_stat` on macOS | —        |
| ~~No orphan-by-ppid~~              | ~~Prune only counts by pattern~~ → **Done**: orphan-by-ppid filters true orphans                           | —        |
| ~~Single trigger type~~            | ~~Stop only~~ → **Done**: Stop + Periodic + memory-based + cc-status thresholds                            | —        |
| **No per-project resource limits** | `ConcurrencyController` is global; no cgroup/ulimit per project                                            | Low      |
| **Process isolation**              | No sandbox; agents run in host process (SANDBOXING_DESIGN.md)                                              | Low      |

### 2.3 Process Optimization Plan (MTSP) — Already Planned

From [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md):

- **MTSP-01**: Unified MCP host (done)
- **MTSP-02**: In-process agent runner (ACE-style)
- **MTSP-03**: Shared task worker (process-compose)
- **MTSP-04**: LSP multiplexing (single Serena daemon)
- **MTSP-05**: Unified worker daemon
- **MTSP-06–08**: Persistent Python pool, in-process tools, Rust governance scanner

---

## 3. Automation Taxonomy

### 3.1 Trigger Types

| Trigger          | When                    | Use Case                                 | Implemented               |
| ---------------- | ----------------------- | ---------------------------------------- | ------------------------- |
| **Stop**         | Session end (IDE Stop)  | Prune after session ends                 | ✓ Yes                     |
| **SessionEnd**   | After Stop hooks        | `session-cleanup.sh`; could add prune    | Partial                   |
| **Periodic**     | Cron/launchd/timer      | Background prune every N min             | ✓ Yes (`prune-periodic`)  |
| **Idle**         | No output for N seconds | Hook-dispatcher timeout; not prune       | No                        |
| **Threshold**    | Memory/FD > X           | Resource-based prune trigger             | ✓ Yes (memory, cc-status) |
| **SessionStart** | Before new run          | Warn if session count > 5; suggest prune | ✓ Yes                     |

### 3.2 What Can Be Automated vs Manual

| Action                          | Current                                | Automation Options                    | Recommendation                        |
| ------------------------------- | -------------------------------------- | ------------------------------------- | ------------------------------------- |
| **Prune orphans**               | Manual `thegent mcp prune`             | Stop hook (done), Periodic, Threshold | Stop + optional Periodic              |
| **Spotlight exclude**           | Manual `thegent mcp spotlight-exclude` | `task setup` or first-run             | ✓ Done (setup + opt-in SessionStart)  |
| **Uni-mount MCP**               | Manual `migrate-unimount`              | First install / `mcp install`         | Add to install flow                   |
| **Session limit warning**       | None                                   | SessionStart or `run` pre-check       | ✓ Done (run/bg warn when > threshold) |
| **Resource-based backpressure** | ConcurrencyController                  | Already in `acquire()`                | Extend to prune trigger               |

---

## 4. Multi-Agent / Multi-Tenant / Multi-Project Deep Dive

### 4.1 Session Isolation

| Dimension             | Current                                        | Target                                              |
| --------------------- | ---------------------------------------------- | --------------------------------------------------- |
| **Owner**             | `user:projectname` or `user:projectname:scope` | Same                                                |
| **Base dir**          | `~/.cache/thegent/sessions` (global)           | Option: `PROJECT_DIR/.thegent/sessions` per-project |
| **Run registry**      | `run_registry.jsonl` per owner scope           | Same                                                |
| **Discovered agents** | `discovered/ppid_{ppid}.json`                  | Same                                                |

**Per-project session dir** (optional): `THGENT_SESSION_DIR=./.thegent/sessions` would put sessions under project root. Enables isolation when multiple projects are open but increases risk of `.git` clutter if not ignored.

### 4.2 Process Isolation

| Level        | Current                        | Options                                                   |
| ------------ | ------------------------------ | --------------------------------------------------------- |
| **Process**  | None                           | Docker (SANDBOXING_DESIGN Phase 2), Firecracker (Phase 3) |
| **Resource** | ConcurrencyController (global) | cgroups (Linux), resource limits (ulimit)                 |
| **Tenant**   | Policy federation (WP-13001)   | Phase 13 tenant boundary tests                            |

### 4.3 Orphan Detection

**Current**: Count processes matching `(node|bun|deno|cc-status)` + LSP/MCP patterns.

**Enhanced**: Process tree traversal — mark as orphan if `ppid` is not in process list (parent dead). Requires:

- `ps -eo pid,ppid` → build parent map
- For each candidate: walk up to root; if root is init (1) and no Cursor/Claude/Codex ancestor, treat as orphan

**Risk**: False positives (e.g. user closed terminal). Mitigation: only prune when count > threshold.

### 4.4 macOS Memory Sampling

`load_based_limits.py` uses `/proc/meminfo` (Linux). For macOS, parse `vm_stat` — see [§11 macOS Memory Sampling](#11-macos-memory-sampling-technical-spec) for full implementation.

---

## 5. Long-Term Optimization Roadmap

### Phase 1: Immediate (Done + Small Enhancements)

| Task                                                    | Status | Effort |
| ------------------------------------------------------- | ------ | ------ |
| Auto-prune on Stop                                      | ✓ Done | —      |
| Config options (auto_prune, threshold, cooldown)        | ✓ Done | —      |
| Documentation (SWARM_PROCESS_OPTIMIZATIONS)             | ✓ Done | —      |
| **Spotlight exclude in setup**                          | ✓ Done | —      |
| **Session-start warning** (>5 sessions → suggest prune) | ✓ Done | —      |

### Phase 2: Structural Depth (Next)

| Task                           | Description                               | Effort          |
| ------------------------------ | ----------------------------------------- | --------------- |
| **macOS memory sampling**      | Add `vm_stat` path in `_get_memory_mb()`  | ✓ Done          |
| **Memory-based prune trigger** | Prune when `mem_available_mb < threshold` | ✓ Done          |
| **Periodic prune daemon**      | launchd (macOS) / systemd timer (Linux)   | ✓ Done          |
| **Orphan-by-ppid**             | Prune only processes whose parent is dead | ✓ Done          |
| **Per-project session dir**    | `THGENT_SESSION_DIR=./.thegent/sessions`  | 6–10 tool calls |

### Phase 3: MTSP (Process Optimization Plan)

| Task                        | Description               | Effort           |
| --------------------------- | ------------------------- | ---------------- |
| **LSP multiplexing**        | Single Serena daemon      | 15–25 tool calls |
| **Shared task worker**      | process-compose           | 10–15 tool calls |
| **In-process agent runner** | ACE-style cwd isolation   | 20–30 tool calls |
| **Unified worker daemon**   | Consolidate task/perl/env | 15–20 tool calls |

### Phase 4: Enterprise (Future)

| Task                         | Description               | Effort           |
| ---------------------------- | ------------------------- | ---------------- |
| **cgroups per project**      | Linux resource limits     | 15–25 tool calls |
| **Docker runner**            | SANDBOXING_DESIGN Phase 2 | 25–40 tool calls |
| **Kernel-level persistence** | macOS/Linux native APIs   | Research         |

---

## 6. Trigger Design: When to Prune

| Strategy             | Trigger                  | Pros                      | Cons                                      |
| -------------------- | ------------------------ | ------------------------- | ----------------------------------------- |
| **Stop-only**        | Every Stop               | Simple, no daemon         | May miss orphans if no Stop for long time |
| **Stop + Threshold** | Stop when count > N      | Balanced                  | Current                                   |
| **Stop + Periodic**  | Stop + cron every 15 min | Catches long-idle orphans | Extra process                             |
| **Stop + Memory**    | Stop when mem_avail < X  | Resource-aware            | Needs macOS fix                           |
| **All**              | Stop + Periodic + Memory | Most robust               | Most complex                              |

**Recommendation**: Stop + Threshold (current). Add Periodic as opt-in (`THGENT_AUTO_PRUNE_PERIODIC=1`, interval 15 min) for heavy users.

---

## 7. Configuration Schema (Proposed)

```yaml
# THGENT_AUTO_PRUNE=1
# THGENT_AUTO_PRUNE_THRESHOLD=12
# THGENT_AUTO_PRUNE_COOLDOWN=300
# THGENT_AUTO_PRUNE_PERIODIC=0          # Future: cron/launchd
# THGENT_AUTO_PRUNE_PERIODIC_INTERVAL=900
# THGENT_AUTO_PRUNE_MEMORY_THRESHOLD_MB=512  # Future: prune when avail < this
# THGENT_SESSION_WARN_THRESHOLD=5       # Warn on run/start if sessions > this
# THGENT_SESSION_DIR=                   # Empty = default; ./.thegent/sessions = per-project
```

---

## 8. Cross-References

| Doc                                                                                             | Relevance                                                                    |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md)                              | MTSP roadmap                                                                 |
| [SWARM_PROCESS_OPTIMIZATIONS](../reference/SWARM_PROCESS_OPTIMIZATIONS.md)                      | User-facing quick reference                                                  |
| [SWARM_MEMORY_COORDINATION_DEPTH](../reference/SWARM_MEMORY_COORDINATION_DEPTH.md)              | Blackboard, stigmergy                                                        |
| [MULTI_SWARM_HIERARCHY_DEPTH](../reference/MULTI_SWARM_HIERARCHY_DEPTH.md)                      | Swarms of swarms                                                             |
| [PHASE_5_SCALE_ROBUSTNESS_DEPTH](../reference/PHASE_5_SCALE_ROBUSTNESS_DEPTH.md)                | Redis, adaptive concurrency                                                  |
| [SANDBOXING_DESIGN](../governance/SANDBOXING_DESIGN.md)                                         | Process isolation                                                            |
| [phase13-tenant-boundary-test-matrix.md](./phase13-tenant-boundary-test-matrix.md)              | Tenant isolation                                                             |
| [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) | Scheduling theory, load balancing, industry systems                          |
| [MEMORY_OPTIMIZATION_LONG_TERM_PLAN](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md)                   | LSP triplet, cc-status bloat, Spotlight; phased roadmap                      |
| [SMART_ROBUST_STRATEGIES_RESEARCH](./SMART_ROBUST_STRATEGIES_RESEARCH.md)                       | Process lifecycle, LSP multiplexing, child death handling, decision matrices |
| [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)             | FD, CPU, threads, ports; sampling; limits; per-process metrics               |
| [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md) | Retry, backoff, jitter, circuit breaker, bulkhead, fairness                  |

---

## 9. Orphan Process Theory (External Research)

### 9.1 Definition (Wikipedia)

An **orphan process** is one whose parent has terminated; the kernel re-parents it to init (PID 1) or a subreaper. Orphans waste resources; solutions include:

| Technique         | Description                                                 | Applicability     |
| ----------------- | ----------------------------------------------------------- | ----------------- |
| **Expiration**    | Allot time; kill if not done; process may request extension | LSPs, MCP servers |
| **Reincarnation** | Periodically locate parents; kill if parent dead            | Discovery + prune |
| **Termination**   | Kill orphan (most common)                                   | Current prune     |

### 9.2 Process Group & SIGHUP

- **Session leader** (shell): when it exits, SIGHUP is sent to all jobs in the process group.
- **Job control**: `nohup`, `disown` prevent SIGHUP; processes can become orphans.
- **Implication**: LSPs/MCPs spawned by Cursor/Claude Code may survive parent exit if not in same process group or if parent doesn't propagate SIGHUP.

### 9.3 Subreaper (Linux 3.4+)

`prctl(PR_SET_CHILD_SUBREAPER)` lets a process (e.g. Cursor) become the subreaper for its descendants. Orphans are reparented to it, not init. Enables Cursor to clean up children on exit—but only if Cursor uses it.

---

## 10. Discovery Architecture (Codebase Deep Dive)

### 10.1 scan_agent_processes (discovery.py)

- **Input**: `ps -eo pid,ppid,command`
- **Filter**: cursor-agent, claude-code, codex by command string
- **Output**: Registers `ppid_{ppid}.json` in `discovered/`
- **Key**: Uses PPID as session key; each agent process gets one file

### 10.2 list_discovered_agents

- Reads `discovered/ppid_*.json`
- **Stale cleanup**: If `_is_pid_running(ppid)` is False, **unlinks** the file
- **Implication**: Discovery already removes dead-agent metadata; prune targets the _processes_ (LSPs, MCPs) that outlive the agent

### 10.3 \_is_triggered_by_agent_process

- Walks **parent chain** via `ps -p $pid -o ppid=`
- Stops at PID 1 or when command matches cursor-agent/claude/codex
- **Pattern**: Same traversal needed for orphan-by-ppid—walk up from candidate LSP; if no Cursor/Claude/Codex ancestor, it's orphaned

### 10.4 \_get_process_cwd

- Uses `lsof -p $pid -a -d cwd -Fn` for cwd
- **macOS/Linux**: lsof works on both

---

## 11. macOS Memory Sampling (Technical Spec)

### 11.1 Current Gap

`load_based_limits._get_memory_mb()`:

- Linux: `/proc/meminfo` → `MemAvailable` (kB)
- macOS: `FileNotFoundError` → fallback `512.0` MB (conservative, wrong)

### 11.2 vm_stat (macOS)

```
Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                              12345.
Pages active:                            67890.
Pages inactive:                         11111.
Pages speculative:                        2222.
...
```

- **Page size**: 4 KB (4096 bytes)
- **Available** ≈ `free + inactive` (inactive can be reclaimed)
- **Formula**: `(pages_free + pages_inactive) * 4096 / (1024*1024)` = available MB

### 11.3 Implementation Sketch

```python
def _get_memory_mb_macos() -> tuple[float, float]:
    rss_mb = 0.0  # from resource.getrusage (existing)
    available_mb = 0.0
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=2)
        if out.returncode != 0:
            return rss_mb, 512.0
        free = inactive = 0
        for line in out.stdout.splitlines():
            if "Pages free:" in line:
                free = int(line.split(":")[1].strip().rstrip("."))
            elif "Pages inactive:" in line:
                inactive = int(line.split(":")[1].strip().rstrip("."))
        available_mb = (free + inactive) * 4096 / (1024 * 1024)
    except Exception:
        available_mb = 512.0
    return rss_mb, available_mb
```

---

## 12. Periodic Prune: launchd / systemd

### 12.1 Existing Patterns

- **MCP service**: `mcp_manage.py` → `~/Library/LaunchAgents/com.thegent.mcp.plist`
- **Proxy**: `cliproxy_manager.py` → `_PROXY_PLIST_LABEL.plist`
- **RunAtLoad**: true for services; for periodic, use `StartInterval` or `StartCalendarInterval`

### 12.2 launchd Periodic Plist (macOS)

```xml
<key>StartInterval</key>
<integer>900</integer>  <!-- 15 min -->
<!-- OR -->
<key>StartCalendarInterval</key>
<dict>
  <key>Minute</key><integer>0</integer>
  <key>Hour</key><integer>*</integer>
</dict>
```

- **ProgramArguments**: `["/usr/bin/env", "thegent", "mcp", "prune", "--force"]`
- **EnvironmentVariables**: `THGENT_AUTO_PRUNE=1`
- **Label**: `com.thegent.prune-periodic`

### 12.3 systemd Timer (Linux)

- `thegent-prune.timer`: `OnUnitInactiveSec=15min`
- `thegent-prune.service`: `ExecStart=thegent mcp prune --force`

---

## 13. Failure Modes & Safety

### 13.1 Prune Kills Wrong Process

| Scenario                   | Likelihood | Mitigation                                              |
| -------------------------- | ---------- | ------------------------------------------------------- |
| Active LSP for open file   | Low        | Patterns are specific; active sessions have recent Stop |
| User's manual node process | Medium     | Pattern whitelist; avoid generic "node"                 |
| MCP server mid-request     | Low        | Cooldown; prune on Stop (session ended)                 |

### 13.2 Risk Registry Mapping

| Risk                                   | Relevance                                                      |
| -------------------------------------- | -------------------------------------------------------------- |
| **R-002** Adaptive Scaling Oscillation | Hysteresis in ConcurrencyController; prune cooldown is similar |
| **R-010** Governance Policy Drift      | Prune patterns could drift; version patterns in config         |
| **R-012** Multi-Agent Deadlock         | Prune doesn't cause deadlock; reduces resource contention      |

### 13.3 Audit Trail

- **Current**: Prune runs silently (advisory, exit 0)
- **Enhancement**: Log to `.thegent/sessions/prune.log` or `run_registry` with `action: prune`, `killed_count`, `timestamp`

---

## 14. IDE Hook Flow (Touchpoint Deep Dive)

### 14.1 When Stop Fires

| Platform        | Stop Trigger                       | Hook Path                        |
| --------------- | ---------------------------------- | -------------------------------- |
| **Cursor**      | User stops agent / closes composer | `.cursor/hooks` or project hooks |
| **Claude Code** | Session end, wrapper exit          | `~/.claude/hooks`                |
| **Codex**       | AfterAgent, session end            | Codex-specific                   |

### 14.2 Hook Dispatcher (Rust)

- **Mode.Stop**: Runs 12 hooks in parallel with idle timeout (180s), max 600s
- **prune-orphans-stop.sh**: One of 12; runs in parallel
- **Env**: `PROJECT_DIR`, `SESSION_ID`, `CWD`, `HEAD_SHA` from dispatcher

### 14.3 Headless / No Stop

- **Gardener**, **thegent run**, **thegent bg**: No IDE; no Stop hook
- **Implication**: Periodic prune catches orphans from headless runs

---

## 15. Alternative Strategies (Beyond Prune)

### 15.1 Prevention > Cure

| Strategy             | Description                                             | Effort     |
| -------------------- | ------------------------------------------------------- | ---------- |
| **LSP multiplexing** | One Serena for all; no per-session LSP                  | MTSP-04    |
| **Uni-mount MCP**    | Single thegent URL; no duplicate Playwright/Upstash     | Done       |
| **Process group**    | Spawn LSPs in same process group; SIGHUP on parent exit | IDE change |

### 15.2 Expiration (Wikipedia)

- Give each LSP/MCP a TTL; extend on activity
- **Complexity**: Requires tracking per-process last-activity; not in current design

### 15.3 Reincarnation (Wikipedia)

- Periodically: for each candidate, check if parent exists
- **Implementation**: Orphan-by-ppid (Section 4.3) is this

---

## 16. Process Tree: Orphan-by-PPID Algorithm

```
1. ps -eo pid,ppid,command → build pid_set, parent_map
2. For each process P matching (node|bun|deno) + LSP/MCP pattern:
   a. Walk parent chain: p = P, then p = parent_map[p] until p not in pid_set or p == 1
   b. If we reach 1 (init) without finding Cursor/Claude/Codex in chain → ORPHAN
   c. If Cursor/Claude/Codex in chain → KEEP (has living parent)
3. Prune only ORPHAN set
```

**Refinement**: "Cursor/Claude/Codex" = process whose command contains cursor-agent, claude, codex. Reuse `_is_triggered_by_agent_process` logic in reverse (walk up, not down).

---

## 17. Implementation Dependency DAG

```
                    ┌─────────────────────┐
                    │ macOS vm_stat fix   │
                    │ (load_based_limits) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Memory-based prune  │
                    │ trigger (optional)  │
                    └─────────────────────┘

┌─────────────────┐     ┌─────────────────────┐
│ Orphan-by-ppid  │     │ Periodic prune      │
│ (discovery.py   │     │ (launchd plist /    │
│  + mcp_prune)   │     │  systemd timer)     │
└────────┬────────┘     └──────────┬──────────┘
         │                         │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │ Prune audit log         │
         │ (.thegent/prune.log)    │
         └────────────────────────┘

Independent: Session-start warning, Spotlight in setup, Per-project session dir
```

**Critical path**: macOS vm_stat → memory-based trigger (enables resource-aware prune).
**Parallel**: Orphan-by-ppid, Periodic prune, Audit log.

---

## 18. Quantitative Targets (from PROCESS_OPTIMIZATION_PLAN)

- **Process count**: Target < 10 persistent processes per session
- **Latency**: Reduce hook overhead by > 50%
- **Stability**: Eliminate "tab termination" side effects via persistent daemons

---

# Part II: Wider Scope

## 20. Platform Ecosystem (Zed, Windsurf, Cline, Continue, OpenCode)

### 20.1 Platform Matrix

| Platform        | Type        | Hook System                         | MCP | Process Model          | Prune Relevance          |
| --------------- | ----------- | ----------------------------------- | --- | ---------------------- | ------------------------ |
| **Claude Code** | CLI         | 15 events                           | ✓   | Subprocess per session | Stop, SessionEnd         |
| **Codex**       | CLI         | notify only                         | ✓   | Subprocess             | No Stop; periodic needed |
| **Cursor**      | IDE         | .cursor/hooks                       | ✓   | Extension host + agent | Stop on composer close   |
| **Windsurf**    | IDE         | .windsurfrules, .windsurf/workflows | ✓   | Similar to Cursor      | Same LSP/MCP bloat       |
| **Cline**       | VS Code ext | MCP, rules                          | ✓   | Extension host         | Same patterns            |
| **Continue**    | VS Code ext | MCP                                 | ✓   | Extension host         | Same patterns            |
| **OpenCode**    | CLI         | Zen                                 | ✓   | Subprocess             | Similar to Codex         |
| **Zed**         | Editor      | AI features                         | ?   | Native                 | May have own LSP model   |
| **Augment**     | CLI + IDE   | auggie, Context Engine              | ✓   | auggie --print         | Remote agents possible   |

### 20.2 Cross-Platform Prune Strategy

- **Patterns**: LSP/MCP patterns (pyright, tsserver, playwright, etc.) are **runtime-agnostic** — same regardless of which IDE spawned them.
- **Discovery**: `scan_agent_processes` today targets cursor-agent, claude, codex. Extend to: `windsurf`, `cline`, `auggie`, `opencode`.
- **Hook availability**: Only Claude Code + Cursor (via thegent) have Stop hooks. Codex, Windsurf, Cline, Continue may not fire Stop → **periodic prune is essential** for multi-platform.

### 20.3 Rules/Skills Locations by Platform

| Platform    | Rules                | Skills                 |
| ----------- | -------------------- | ---------------------- |
| Cursor      | .cursor/rules/\*.mdc | .cursor/skills-cursor/ |
| Windsurf    | .windsurfrules       | .windsurf/skills/      |
| Claude Code | CLAUDE.md, skills    | skills/                |
| Codex       | .codex/skills/       | SKILL.md               |
| thegent     | agents/, skills/     | skills/                |

---

## 21. Resource Types Beyond CPU/Memory

### 21.1 Disk

| Resource         | Current                            | Gap                       | Automation           |
| ---------------- | ---------------------------------- | ------------------------- | -------------------- |
| **Disk free**    | `GARDENER_MIN_USAGE_PERCENT` (15%) | Gardener only             | Prune when disk < X% |
| **node_modules** | —                                  | Bloat across projects     | npkill-style cleanup |
| **Cache dirs**   | —                                  | .cache, .claude, .thegent | Periodic vacuum      |

**npkill** (9k GitHub): Find and remove node_modules; frees disk. Could integrate: `thegent mcp vacuum` — optional cleanup of stale node_modules in inactive projects.

### 21.2 Network

| Resource            | Relevance                | Automation                |
| ------------------- | ------------------------ | ------------------------- |
| **MCP connections** | Each client = connection | Connection pooling (MTSP) |
| **API rate limits** | Provider throttling      | ConcurrencyController     |
| **Bandwidth**       | Remote dev, cloud        | Not yet modeled           |

### 21.3 GPU

| Resource           | Relevance            | Automation                   |
| ------------------ | -------------------- | ---------------------------- |
| **VRAM**           | NIM, local LLMs      | Not in ConcurrencyController |
| **CUDA processes** | Orphan GPU processes | Extend prune patterns        |

**NIM (NVIDIA)**: Self-hosted LLM on GPU. Orphan GPU processes could leak VRAM; prune patterns could include `nvidia-smi`-detected orphaned processes.

### 21.4 Battery (Laptops)

- **Relevance**: Aggressive pruning when on battery to extend life.
- **macOS**: `pmset -g batt`; `ioreg -r -d 1 -n AppleSmartBattery`
- **Automation**: `THGENT_AGGRESSIVE_PRUNE_ON_BATTERY=1` — lower threshold, shorter cooldown.

---

## 22. Dev Containers & Remote Development

### 22.1 Dev Container Model

- **devcontainer.json**: Defines container for development; extensions run inside container.
- **Implication**: LSPs, MCP servers run **inside container**; process tree is container-scoped.
- **Prune**: Must run **inside** container (same PID namespace). `thegent mcp prune` in devcontainer = prunes container processes only.

### 22.2 Remote SSH / Tunnels

- **Remote - SSH**: VS Code connects to remote host; extensions run remotely.
- **Remote - Tunnels**: Similar; tunnel host runs tools.
- **Implication**: Prune runs on **remote host**; session_dir, discovered agents are remote. No change to prune logic; execution context differs.

### 22.3 Kubernetes Attach

- **Dev Containers extension**: Can attach to a container in a Kubernetes cluster.
- **Implication**: Prune targets pod/container processes; multi-tenant at cluster level.

### 22.4 Design Principle

**Prune is local to execution context.** Whether native, Docker, SSH, or K8s — run prune where the agent processes run.

---

## 23. Industry Tools & Patterns

### 23.1 Process Cleanup Tools

| Tool              | Purpose              | Overlap with Prune                  |
| ----------------- | -------------------- | ----------------------------------- |
| **npkill**        | Remove node_modules  | Disk; different from process kill   |
| **npx kill-port** | Kill process on port | Port-based; we use pattern-based    |
| **pkill**         | Kill by name         | Generic; we use curated patterns    |
| **supervisord**   | Process supervisor   | Restart; we terminate orphans       |
| **systemd**       | Service manager      | Lifecycle; we don't manage services |

### 23.2 Agent-Specific

| Tool                | Purpose                                               |
| ------------------- | ----------------------------------------------------- |
| **cipher**          | Memory layer for Cursor, Codex, Windsurf, Cline       |
| **memory-bank-mcp** | Remote memory for Cline/Cursor/Windsurf               |
| **rulebook-ai**     | Consistent rules across Codex, Cursor, Windsurf       |
| **ruler**           | Apply rules to Claude, Codex, Cursor, Aider, Windsurf |

**Insight**: Ecosystem is converging on **cross-platform rules + memory**. Prune is orthogonal — resource hygiene, not context.

### 23.3 MCP Ecosystem

- **1mcpserver**: MCP of MCPs; remote discovery.
- **kubernetes-mcp-server**: K8s/OpenShift.
- **Uni-mount**: Single thegent URL reduces duplicate MCP servers; prune cleans up stragglers.

---

## 24. Multi-Machine & Distributed Swarms

### 24.1 Single-Machine Assumption

Current prune, discovery, ConcurrencyController assume **one machine**. Session dir, run_registry, discovered agents are local.

### 24.2 Distributed Future (WP-5004)

- **Redis**: Distributed state; multiple thegent instances.
- **Partitioning**: By Swarm_ID; each swarm has own Redis partition.
- **Prune**: Each instance prunes **its own host**. No cross-machine prune (processes are host-local).

### 24.3 Hybrid: Local + Remote Agents

- **Augment Remote Agents**: Cloud execution.
- **thegent serve HTTP**: Remote MCP.
- **Implication**: Remote agents don't spawn local LSPs; prune stays local. Remote side may need its own prune policy.

---

## 25. Cloud vs Local Tradeoffs

| Dimension             | Local                     | Cloud                  |
| --------------------- | ------------------------- | ---------------------- |
| **Process isolation** | Shared host               | VM/container per run   |
| **Prune relevance**   | High (orphans accumulate) | Lower (ephemeral)      |
| **Resource limits**   | ConcurrencyController     | Provider quotas        |
| **Cost**              | Hardware                  | Per-token, per-request |
| **Latency**           | Low                       | Network RTT            |
| **Privacy**           | Data stays local          | Data leaves            |

**Recommendation**: Prune is **local-first**. Cloud runs are ephemeral; orchestration (Kubernetes, serverless) handles lifecycle.

**Part II summary**: Prune patterns are platform-agnostic; periodic prune is essential for Codex/Windsurf/Cline. Extend to disk (npkill), GPU, battery. Dev Containers and remote dev require prune in the same execution context. Multi-machine = per-host prune.

---

## 26. Compliance & Audit

### 26.1 Audit Trail for Prune

| Requirement         | Implementation                                          |
| ------------------- | ------------------------------------------------------- |
| **What was killed** | Log PID, command, timestamp                             |
| **Why**             | Threshold exceeded, cooldown passed                     |
| **Who**             | THGENT_OWNER_TAG or session_id                          |
| **Retention**       | Append to `.thegent/sessions/prune.log` or run_registry |

### 26.2 Compliance Context

- **SOC2**: Audit trail for destructive actions.
- **GDPR**: Prune doesn't touch PII; low relevance.
- **Internal policy**: Some orgs require approval before killing processes; prune should be **opt-in** (THGENT_AUTO_PRUNE=1).

### 26.3 Reversibility

- **Prune is irreversible**: Process is killed.
- **Mitigation**: LSPs restart on next IDE interaction; MCP servers reconnect. User impact is transient.

---

# Part III: Deeper Dimensions

## 27. Per-Platform Edge Cases

### 27.1 Cursor

| Edge Case                | Description                   | Mitigation                               |
| ------------------------ | ----------------------------- | ---------------------------------------- |
| **Background agent**     | Isolated VM, separate branch  | May spawn LSPs in different process tree |
| **Multi-root workspace** | Several folders in one window | PROJECT_DIR may be ambiguous             |
| **Extension host crash** | LSPs orphaned                 | Periodic prune catches                   |

### 27.2 Codex

| Edge Case               | Description                   | Mitigation               |
| ----------------------- | ----------------------------- | ------------------------ |
| **No Stop hook**        | Session end doesn't fire Stop | Periodic prune essential |
| **codex exec -**        | Stdin prompt; single-turn     | Fewer orphans per run    |
| **Notify (AfterAgent)** | JSON to external cmd          | Could trigger prune      |

### 27.3 Claude Code

| Edge Case          | Description         | Mitigation                        |
| ------------------ | ------------------- | --------------------------------- |
| **Agent teams**    | Multiple teammates  | More concurrent LSPs              |
| **Subagent spawn** | Bash, Explore, Plan | Each may spawn tools              |
| **Resume**         | --resume SESSION_ID | Old session's children may linger |

### 27.4 Headless (thegent run, gardener)

| Edge Case          | Description                | Mitigation            |
| ------------------ | -------------------------- | --------------------- |
| **No IDE**         | No Stop from Cursor/Claude | Periodic + SessionEnd |
| **tmux sessions**  | Long-lived                 | Orphans accumulate    |
| **Gardener spawn** | Many parallel agents       | High process churn    |

---

## 28. Security Implications

### 28.1 Prune as Privilege Escalation Vector

- **Risk**: Malicious actor sets THGENT_AUTO_PRUNE=1, manipulates threshold to kill critical processes.
- **Mitigation**: Prune only kills **known patterns** (whitelist); no generic `killall node`.
- **Trust boundary**: Prune runs in user context; same privilege as thegent. Sandbox (SANDBOXING_DESIGN) would isolate.

### 28.2 Process Injection

- **Risk**: Attacker names process to match pattern (e.g. symlink or exec with pyright-langserver in path).
- **Mitigation**: Match full command line; avoid substring-only. Validate path.

### 28.3 Audit Log Tampering

- **Risk**: Attacker modifies prune.log to hide activity.
- **Mitigation**: Append-only; consider hash chain or write to immutable store.

---

## 29. Failure Mode Taxonomy

### 29.1 Prune Failures

| ID   | Mode                | Description                           | Detection                       | Recovery                        |
| ---- | ------------------- | ------------------------------------- | ------------------------------- | ------------------------------- |
| F-P1 | False positive      | Killed active LSP                     | User reports broken completions | Restart IDE; LSP respawns       |
| F-P2 | False negative      | Missed orphan                         | Process count stays high        | Lower threshold; orphan-by-ppid |
| F-P3 | Cooldown starvation | Never prune (always in cooldown)      | Count never drops               | Reduce cooldown                 |
| F-P4 | Pattern drift       | New LSP not in list                   | Orphans accumulate              | Update pattern list             |
| F-P5 | Cross-platform      | Platform-specific process not matched | Platform-specific bloat         | Add platform patterns           |

### 29.2 Integration Failures

| ID   | Mode                | Description                               | Detection               | Recovery                 |
| ---- | ------------------- | ----------------------------------------- | ----------------------- | ------------------------ |
| F-I1 | Hook not fired      | Stop never runs (Codex, etc.)             | No prune on session end | Periodic prune           |
| F-I2 | Env not inherited   | THGENT_AUTO_PRUNE not set in hook context | Prune never runs        | Document env setup       |
| F-I3 | thegent not in PATH | Hook can't exec thegent                   | Prune fails silently    | Install thegent globally |

---

## 30. Adjacent Research & Standards

### 30.1 Dev Container Specification

- **containers.dev**: Open spec for dev containers.
- **Relevance**: Prune in devcontainer = same logic, different execution context.
- **Features**: Dev container Features could include "thegent prune" as optional install.

### 30.2 MCP Protocol

- **Transport**: STDIO vs HTTP; HTTP enables remote.
- **Relevance**: Remote MCP = no local LSP for that server; prune still targets local runtimes.

### 30.3 Process Supervision Standards

- **systemd**: Service lifecycle; not for ad-hoc agent processes.
- **supervisord**: Process groups; could manage LSP pool (MTSP-04).
- **Kubernetes**: Pod lifecycle; ephemeral containers.

### 30.4 Academic / Industry

- **Orphan process** (Wikipedia): Expiration, Reincarnation, Termination.
- **Stigmergy** (SWARM_MEMORY): Environment-mediated coordination; prune is environmental cleanup.
- **Load balancing**: ConcurrencyController mirrors load-balancer scaling logic.

**Part III summary**: Each platform has distinct edge cases (Cursor background agent, Codex no Stop, Claude teams). Security: whitelist patterns, full command match, append-only audit. Failure taxonomy (F-P1–F-P5, F-I1–F-I3) guides detection and recovery.

---

## 31. Appendix: Process Patterns (Prune)

Current patterns in `mcp_prune` and `prune-orphans-stop.sh`:

```
pyright-langserver
typescript-language-server
tsserver.js
@playwright/mcp
context7-mcp
cc-status
octocode-mcp
next-devtools-mcp
sequential-thinking
```

Runtimes: `node`, `npm`, `bun`, `deno`.

### 31.1 Per-CC Stack (Multi-Project, Multi-Tenant)

**Not in prune patterns** (IDE-managed; tab close terminates): python, clangd, gopls, uv, sourcekit-lsp, rust-analyzer, caffeinate. Each Claude Code instance spawns its own full stack. **Multi-project × multi-tenant** = process count scales linearly. LSP multiplexing (MTSP-04) and shared daemons are the long-term fix.

---

## 32. Optimization & Scheduling Deep Research (Companion Doc)

For a comprehensive deep dive into **optimization, management, and scheduling systems** — scheduling theory (OS schedulers, disciplines, load balancing), thegent mapping (ConcurrencyController, HysteresisController, limit gates), industry systems (Slurm, Kubernetes, Celery, Mesos), and algorithms (bin packing, fair queuing, work stealing) — see:

**[SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md)**

That document covers:

- **Part I**: Scheduling fundamentals, OS scheduler types, disciplines (FCFS, RR, EDF, multilevel feedback), static vs dynamic load balancing.
- **Part II**: Current thegent scheduling (ConcurrencyController, HysteresisController, ResourceSnapshot), gaps vs theory.
- **Part III**: Job schedulers (Slurm, PBS, HTCondor), supervisors (supervisord, systemd), orchestrators (Kubernetes), task queues (Celery, RQ), multi-agent allocation.
- **Part IV**: Bin packing, fair queuing (WFQ, DRR), work stealing, admission control, gang scheduling.
- **Part V**: Phased roadmap for thegent (enhance controllers, add disciplines, distributed scheduling, advanced optimization).

---

## 33. Coordination Flowcharts

### 33.1 Multi-Agent Session Coordination Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-AGENT COORDINATION FLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌─────────────────┐
                           │   User Request  │
                           └────────┬────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────┐
                    │     Hook Dispatcher (Stop)        │
                    │  ┌───────────────────────────┐  │
                    │  │ 1. prune-orphans-stop   │  │
                    │  │ 2. session-cleanup      │  │
                    │  │ 3. memory-check         │  │
                    │  │ 4. threshold-evaluate   │  │
                    │  └───────────────────────────┘  │
                    └────────────────┬────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Threshold-based │  │  Memory-based  │  │  Periodic-based │
    │  Prune Trigger  │  │  Prune Trigger │  │  Prune Trigger  │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                      │                      │
             ▼                      ▼                      ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    ORPHAN DETECTION ENGINE                   │
    │  ┌─────────────────────────────────────────────────────┐  │
    │  │  1. ps -eo pid,ppid,command → parent_map           │  │
    │  │  2. For each candidate (node,bun,deno,LSP,MCP):     │  │
    │  │     a. Walk parent chain up to root                  │  │
    │  │     b. If reaches init(1) without Cursor/Claude     │  │
    │  │        → ORPHAN (mark for prune)                     │  │
    │  │     c. If Cursor/Claude/Codex in chain → KEEP       │  │
    │  └─────────────────────────────────────────────────────┘  │
    └─────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   Kill Decision Matrix  │
                    │  ┌───────────────────┐ │
                    │  │ • RSS-aware: Kill  │ │
                    │  │   highest RSS     │ │
                    │  │ • Age-aware: Kill │ │
                    │  │   longest idle   │ │
                    │  │ • Graceful:      │ │
                    │  │   SIGTERM first  │ │
                    │  └───────────────────┘ │
                    └─────────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Audit Log     │
                         │ (.thegent/      │
                         │  prune.log)     │
                         └─────────────────┘
```

### 33.2 Process Lifecycle State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROCESS LIFECYCLE STATE MACHINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
    │  NEW    │────►│ RUNNING │────►│  STOP   │────►│REAPED  │
    │         │     │         │     │(SIGTERM)│     │         │
    └─────────┘     └────┬────┘     └────┬────┘     └─────────┘
                          │                │
                          │                │ (timeout)
                          │                ▼
                          │         ┌─────────────┐
                          │         │   KILLED   │
                          │         │ (SIGKILL)  │
                          │         └─────────────┘
                          │                │
                          ▼                ▼
                   ┌─────────────┐   ┌─────────────┐
                   │  ORPHANED  │   │   ZOMBIE   │
                   │ (reparented│   │ (parent not│
                   │   to init) │   │  reaped)   │
                   └─────────────┘   └─────────────┘
```

### 33.3 ConcurrencyController Admission Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  CONCURRENCYCONTROLLER ADMISSION FLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

                           ┌───────────────────┐
                           │ acquire(lane)     │
                           └─────────┬─────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │ sample_resources() → Snapshot   │
                    │ • FD count                      │
                    │ • Memory available              │
                    │ • Load average                 │
                    └─────────────────┬──────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │ compute_dynamic_limit(snapshot) │
                    │ • FD slots = headroom/50        │
                    │ • Mem slots = (avail-256)/128  │
                    │ • Load slots = scaled          │
                    └─────────────────┬──────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │ HysteresisController.get_limit()│
                    │ • upper_threshold=0.8          │
                    │ • lower_threshold=0.4           │
                    │ • dwell_time=30s               │
                    └─────────────────┬──────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │ running_count < effective_limit?│
                    └───────────────┬────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
             ┌────────────┐               ┌────────────┐
             │   TRUE     │               │   FALSE    │
             │ acquire()  │               │   BLOCK    │
             │  succeeds  │               │ (wait/retry│
             └────────────┘               └────────────┘
```

---

## Document Changelog

| Date       | Change                                                                                                                                         |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-02-16 | Initial research; auto-prune, orphan theory, discovery, macOS vm_stat, launchd/systemd                                                         |
| 2026-02-16 | Part II: Platform ecosystem, resources, Dev Containers, industry tools, multi-machine, compliance                                              |
| 2026-02-16 | Part III: Per-platform edge cases, security, failure taxonomy, adjacent research                                                               |
| 2026-02-16 | Polish: How to use, cross-refs, terminology, changelog                                                                                         |
| 2026-02-16 | Polish: TOC links, quick-ref table, Dev Container terminology                                                                                  |
| 2026-02-16 | Part IV: Optimization & scheduling deep research (companion doc)                                                                               |
| 2026-02-17 | Extended: Coordination flowcharts (§33) - Multi-Agent Coordination Flow, Process Lifecycle State Machine, ConcurrencyController Admission Flow |

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Coordination flowcharts (§33)

| Section | Added Content                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------ |
| §33.1   | Multi-Agent Coordination Flowchart showing Stop hook → Orphan Detection → Kill Decision → Audit        |
| §33.2   | Process Lifecycle State Machine (NEW→RUNNING→STOP→REAPED, with ORPHANED/ZOMBIE branches)               |
| §33.3   | ConcurrencyController Admission Flow (sample_resources → compute_dynamic_limit → hysteresis → acquire) |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SWARM_COMPLETE.md](./SWARM_COMPLETE.md) - Swarm guide
- [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) - Scheduling research
- [SWARM_RESEARCH_INDEX.md](./SWARM_RESEARCH_INDEX.md) - Swarm research index
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
