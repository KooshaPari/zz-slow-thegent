<DONE>
# Smart & Robust Process Strategies — Research & Plan

> **Purpose**: Research and plan for smarter, more robust process management strategies for multi-agent, multi-tenant, multi-project local swarms.
> **Status**: Research | **Date**: 2026-02-16
> **Related**: [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md), [MEMORY_OPTIMIZATION_LONG_TERM_PLAN](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md), [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md)

---

## 1. Executive Summary

This document synthesizes external research and industry patterns into **smart and robust strategies** for thegent's process lifecycle, orphan management, LSP multiplexing, and multi-tenant isolation. It provides:

- **Process lifecycle theory** (zombie vs orphan vs daemon; parent-child contract)
- **Child death handling** (PR_SET_PDEATHSIG, pipes, subreaper)
- **LSP multiplexing** (lspx, lsp-mux, lsplex — per-project shared servers)
- **thegent-specific roadmap** with phased strategies and decision matrices

---

## 2. Process Lifecycle: Parent-Child Contract (External Research)

### 2.1 Core Model

Process relationships are a **kernel-managed family tree with obligations**:

| Concept    | Definition                                                              | thegent Relevance                                             |
| ---------- | ----------------------------------------------------------------------- | ------------------------------------------------------------- |
| **Zombie** | Child has exited; parent has not reaped exit status via `wait*()`       | LSP/MCP parents that don't reap → process table pressure      |
| **Orphan** | Parent exited; child still running; kernel re-parents to init/subreaper | Our prune targets — LSPs/MCPs whose Cursor/Claude parent died |
| **Daemon** | Intentionally detached; supervised by service manager                   | `thegent serve`, prune-periodic, process-compose              |

**Key insight**: Zombie is a **cleanup failure**; orphan is an **ownership change**; daemon is a **service design choice**. Classify first, then act.

### 2.2 Production Debugging Playbook (from thelinuxcode.com)

| Step                            | Command / Action                                          |
| ------------------------------- | --------------------------------------------------------- |
| 1. Find suspicious states       | `ps -eo pid,ppid,stat,tty,etime,cmd \| rg 'service-name'` |
| 2. Inspect parent-child tree    | `pstree -pal`                                             |
| 3. Per-process kernel view      | `cat /proc/<pid>/status`, `cat /proc/<pid>/stat`          |
| 4. Trace wait/reap behavior     | `strace -f -p <pid> -e trace=wait4,waitid`                |
| 5. Validate service supervision | `systemctl status`, `journalctl -u <unit>`                |
| 6. Container PID 1 check        | Use init shim (tini) if app is PID 1 and spawns children  |

### 2.3 Strategies for Robust Child Management

| Strategy                          | Description                                                                                             | Applicability to thegent                   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **SIGCHLD + drain loop**          | Parent installs SIGCHLD handler; drains all exited children with `waitpid(-1, WNOHANG)` until none left | thegent subprocess spawns (run, bg, hooks) |
| **Shutdown path drains children** | Before parent exits, explicitly wait for all registered child PIDs                                      | MCP server, process-compose                |
| **One child manager component**   | Centralize spawn, timeout, signal, wait semantics                                                       | `execution.py`, `cli_impl.py`              |
| **pidfd-based management**        | Linux 5.3+ `pidfd_open` for race-resistant lifecycle                                                    | Future: replace PID-based tracking         |

---

## 3. Ensuring Child Dies When Parent Exits

### 3.1 Linux: PR_SET_PDEATHSIG

```c
prctl(PR_SET_PDEATHSIG, SIGHUP);  // Child receives SIGHUP when parent dies
```

- **Effect**: Kernel sends signal to child when parent terminates.
- **Portability**: Linux-only.
- **Use case**: LSP/MCP processes spawned by Cursor/Claude could use this so they self-terminate when IDE tab closes — **requires IDE/vendor change**.

### 3.2 Cross-Platform: Pipe-Based Detection

```python
# Parent writes to pipe; child reads. When parent exits, pipe closes → EOF.
read_end, write_end = os.pipe()
pid = os.fork()
if pid == 0:
    os.close(write_end)
    while True:
        try:
            os.read(read_end, 1024)  # Blocks until EOF
        except EOFError:
            sys.exit(0)  # Parent hung up
```

- **Effect**: Child detects parent death via pipe EOF.
- **Portability**: POSIX.
- **Use case**: thegent-spawned workers (e.g. subagent processes) — we control spawn, so we can add this.

### 3.3 Process Group + SIGHUP

- **Session leader** (shell) exit sends SIGHUP to all jobs in process group.
- **nohup / disown** prevent SIGHUP; processes can become orphans.
- **Implication**: LSPs spawned by Cursor may survive if not in same process group or if parent doesn't propagate SIGHUP.
- **Fix**: IDE would need to spawn LSPs in same process group — **external (Cursor/Claude)**.

### 3.4 Subreaper (PR_SET_CHILD_SUBREAPER)

- **Effect**: Process becomes subreaper; orphans of its descendants are reparented to it, not init.
- **Use case**: Cursor/Claude could set this so they adopt and clean up LSP children on exit — **requires IDE change**.

---

## 4. LSP Multiplexing — Industry Patterns

### 4.1 Problem

Each IDE instance (or each project tab) spawns its own LSP process. Multi-project × multi-tenant = N× pyright, N× tsserver, N× clangd.

### 4.2 Existing Solutions

| Project                 | Language        | Approach                                | Key Features                                                                                |
| ----------------------- | --------------- | --------------------------------------- | ------------------------------------------------------------------------------------------- |
| **lspx** (thefrontside) | TypeScript/Deno | Multiplexer + supervisor + shell        | Combines multiple LSPs (ts, tailwind, eslint) into one connection; restarts failed servers  |
| **lsp-mux** (mrvnmyr)   | Go              | Per-project, per-language shared server | Unix socket; first client spawns server; others connect; 10min linger after last disconnect |
| **lsplex** (joaotavora) | C++             | Experimental proxy/multiplexer          | Archive; minimal                                                                            |

### 4.3 lsp-mux Architecture (Most Relevant)

```
Editor 1 ─┐
Editor 2 ─┼─► lsp-mux (proxy) ─► Single LSP process (per project + language)
Editor 3 ─┘
```

- **Project detection**: Search upward for `.lspmux` file; use that dir as project tag.
- **Socket placement**: `$XDG_RUNTIME_DIR/lsp-mux` or `~/.cache/lsp-mux`.
- **Linger**: Server stays alive 10min after last client disconnect (configurable).
- **Caveat**: Server-initiated requests (e.g. `workspace/configuration`) routed to primary client.

### 4.4 thegent Mapping (MTSP-04)

| lsp-mux concept            | thegent equivalent                                                |
| -------------------------- | ----------------------------------------------------------------- |
| `.lspmux` marker           | `PROJECT_DIR` from session / cwd                                  |
| Per-project + per-language | `(project_root, language)` key                                    |
| Unix socket                | `~/.cache/thegent/lsp-sockets/<hash>.sock`                        |
| Linger 10min               | `THGENT_LSP_LINGER_SEC`                                           |
| Serena (uvx)               | Primary target — replace per-call `uvx serena` with shared daemon |

**Strategy**: Implement or integrate an lsp-mux–style proxy for Serena. thegent `serve` could host it, or we wrap `lsp-mux` / `lspx` for stdio LSPs.

---

## 5. Multi-Tenant Resource Isolation

### 5.1 cgroups (Linux)

- **memory controller**: Limit RSS per cgroup.
- **cpu controller**: Throttle or limit CPU.
- **pids controller**: Limit process count.

**Use case**: Per-project or per-tenant cgroups so one runaway agent doesn't starve others. Requires root or user cgroups v2.

### 5.2 ulimit

- **Process count**: `ulimit -u` (max user processes).
- **Memory**: `ulimit -v` (virtual memory), `ulimit -m` (RSS) — often disabled.

**Use case**: thegent could set ulimits before spawning agent subprocesses — limited; doesn't isolate between projects.

### 5.3 thegent Today

- **ConcurrencyController**: Global limit; no per-project partitioning.
- **Gardener**: Disk-based backpressure (`GARDENER_MIN_USAGE_PERCENT`).
- **Gap**: No per-project memory or process caps.

---

## 6. Smart Prune Strategies (Beyond Current)

### 6.1 Current (Implemented)

- Orphan-by-ppid: Only kill if parent chain reaches init.
- Memory-based trigger: Prune when `mem_available < threshold`.
- cc-status-specific threshold: Lower bar for cc-status.
- Periodic daemon: launchd/systemd every 15min.

### 6.2 Enhanced Strategies

| Strategy                   | Description                                                         | Effort          | Impact                                   |
| -------------------------- | ------------------------------------------------------------------- | --------------- | ---------------------------------------- |
| **RSS-aware prune**        | Sort candidates by RSS; kill highest first when over threshold      | 8–12 tool calls | Medium — frees more memory per kill      |
| **Age-based decay**        | Prefer killing processes with longest `etime` (idle longer)         | 4–6 tool calls  | Medium — reduces risk of killing active  |
| **Graceful SIGTERM first** | Send SIGTERM; wait 2–5s; SIGKILL only if still alive                | 2–4 tool calls  | Low — cleaner shutdown                   |
| **Zombie detection**       | Count zombies (`stat=Z`); alert or trigger parent restart           | 6–8 tool calls  | Medium — different problem than orphans  |
| **Process group kill**     | When killing parent, use `kill(-pgid, SIGTERM)` to kill whole group | 4–6 tool calls  | Medium — avoids orphaned children of LSP |

### 6.3 Graceful Shutdown Sequence (SIGTERM → SIGKILL)

```
1. Send SIGTERM to process (or process group: kill(-pgid, SIGTERM))
2. Wait grace_period (e.g. 2–5s)
3. If still alive: send SIGKILL
4. Ignore ESRCH (process may have exited between check and kill)
```

| Phase    | Signal  | Wait | Rationale                                |
| -------- | ------- | ---- | ---------------------------------------- |
| Graceful | SIGTERM | 2–5s | LSP can flush buffers, close connections |
| Forced   | SIGKILL | 0    | No response to SIGTERM → assume hung     |

**Process group kill**: `kill(-pgid, SIGTERM)` ensures child LSPs (e.g. tsserver, pyright) are terminated with parent; avoids new orphans.

### 6.4 Failure Mode Mitigations

| Risk                                       | Mitigation                                           |
| ------------------------------------------ | ---------------------------------------------------- |
| False positive (kill active LSP)           | Orphan-by-ppid; age-based decay; dry-run             |
| Prune during heavy load                    | Cooldown; memory threshold only when critical        |
| Race (process exits between scan and kill) | `kill(pid, 0)` check before kill; ignore ESRCH       |
| Zombie buildup                             | Separate zombie count; recommend parent restart      |
| Orphaned children of killed LSP            | Process group kill; or recursive kill children first |

### 6.5 Prune Strategy Selection Matrix

| Scenario            | Preferred Strategy                                   |
| ------------------- | ---------------------------------------------------- |
| Memory critical     | RSS-aware; kill highest first                        |
| Many idle processes | Age-based; kill longest etime                        |
| Mixed load          | RSS + age hybrid (weighted score)                    |
| cc-status bloat     | Lower threshold for cc-status; kill first            |
| Zombie accumulation | Separate path; alert; don't prune (parent must reap) |

---

## 7. Decision Matrices

### 7.1 When to Use Which Process Model

| Lifetime         | Recommended Model                | thegent Example                   |
| ---------------- | -------------------------------- | --------------------------------- |
| Seconds          | Child with strict wait/timeout   | Hook subprocess, single tool call |
| Minutes to hours | Supervisor-managed worker        | `thegent run`, `thegent bg`       |
| Long-lived       | Foreground under service manager | `thegent serve`, prune-periodic   |
| Variable         | Explicit job manager             | DAG tasks, gardener               |

### 7.2 LSP Multiplexing: Build vs Integrate

| Option                  | Pros                              | Cons                                      |
| ----------------------- | --------------------------------- | ----------------------------------------- |
| **Integrate lsp-mux**   | Proven; Go; per-project sockets   | May need fork for Serena; stdio vs socket |
| **Integrate lspx**      | Multi-LSP; supervisor; Deno       | Deno dependency; different architecture   |
| **Build minimal proxy** | Full control; Python/Node in-tree | 15–25 tool calls; maintenance             |
| **Upstream Serena**     | Serena adds multiplexing          | External; timeline unknown                |

**Recommendation**: Phase 1 — Evaluate lsp-mux for Serena (stdio→socket adapter). Phase 2 — If mismatch, build minimal thegent-lsp-proxy.

### 7.3 Child Death Handling: Where to Apply

| Spawner             | PR_SET_PDEATHSIG    | Pipe                   | Subreaper             |
| ------------------- | ------------------- | ---------------------- | --------------------- |
| Cursor/Claude (LSP) | IDE change          | N/A                    | IDE change            |
| thegent run/bg      | N/A (we are parent) | Optional for subagents | Possible in executor  |
| thegent serve (MCP) | For mounted tools   | For subprocess tools   | For MCP subprocesses  |
| process-compose     | N/A                 | N/A                    | Use `is_daemon: true` |

---

## 8. Phased Roadmap

### Phase 1: Quick Wins (1–2 weeks)

| Task                | Description                                         | Effort |
| ------------------- | --------------------------------------------------- | ------ |
| RSS-aware prune     | Kill highest-RSS orphans first                      | 8–12   |
| Graceful SIGTERM    | SIGTERM → wait → SIGKILL                            | 2–4    |
| Zombie count metric | Report zombie count in `thegent ps` / prune dry-run | 4–6    |

### Phase 2: Structural (2–4 weeks)

| Task                    | Description                                          | Effort |
| ----------------------- | ---------------------------------------------------- | ------ |
| LSP multiplexing POC    | Evaluate lsp-mux + Serena; document integration path | 10–15  |
| Pipe-based child death  | Add to thegent-spawned subagents (optional)          | 6–10   |
| Per-project session dir | `THGENT_SESSION_DIR=./.thegent/sessions`             | 6–10   |

### Phase 3: MTSP (1–2 months)

| Task                      | Description                                       | Effort |
| ------------------------- | ------------------------------------------------- | ------ |
| Serena multiplexing       | Implement or integrate; single daemon per project | 15–25  |
| Per-project cgroups       | Optional; Linux; user cgroups v2                  | 15–20  |
| Centralized child manager | One component for spawn/timeout/signal/wait       | 20–30  |

### Phase 4: Ecosystem (Ongoing)

| Task                        | Owner         | Notes                |
| --------------------------- | ------------- | -------------------- |
| PR_SET_PDEATHSIG for LSP    | Cursor/Claude | Upstream request     |
| Subreaper for IDE           | Cursor/Claude | Upstream request     |
| Type checker sharing        | Research      | IDE extension config |
| cc-status upstream feedback | Community     | Anthropic            |

---

## 9. Cross-References

| Doc                                                                                             | Relevance                                                   |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)           | Full automation taxonomy, triggers, platform details        |
| [MEMORY_OPTIMIZATION_LONG_TERM_PLAN](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md)                   | LSP triplet, cc-status, Spotlight; phased status            |
| [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) | Scheduling theory, load balancing, industry systems         |
| [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)             | FD, CPU, threads, ports; sampling; Activity Monitor mapping |
| [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md) | Retry, backoff, jitter, circuit breaker, bulkhead, fairness |
| [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md)                              | MTSP roadmap, tool migration                                |
| [SWARM_PROCESS_OPTIMIZATIONS](../reference/SWARM_PROCESS_OPTIMIZATIONS.md)                      | User-facing quick reference                                 |

---

## 10. Bibliography & Sources

| Source                                                                                                                                               | Topic                                               |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| [thelinuxcode.com: Zombie vs Orphan vs Daemon](https://thelinuxcode.com/zombie-vs-orphan-vs-daemon-processes-a-practical-production-guide-for-2026/) | Process lifecycle, production playbook, debugging   |
| [tech-champion.com: Child process dies when parent exits](https://tech-champion.com/linux/how-to-ensure-a-child-process-dies-when-its-parent-exits/) | PR_SET_PDEATHSIG, pipe-based detection              |
| [man7.org: prctl(2)](https://man7.org/linux/man-pages/man2/prctl.2.html)                                                                             | PR_SET_PDEATHSIG, PR_SET_CHILD_SUBREAPER            |
| [github.com/thefrontside/lspx](https://github.com/thefrontside/lspx)                                                                                 | LSP multiplexer, supervisor, multi-LSP merge        |
| [github.com/mrvnmyr/lsp-mux](https://github.com/mrvnmyr/lsp-mux)                                                                                     | Per-project, per-language LSP sharing; Unix sockets |

---

## 11. Strategy Implementation Checklist

### 11.1 Process Lifecycle Checklist

- [ ] **Zombie Detection**
  - [ ] Add zombie count to `thegent ps` output
  - [ ] Alert when zombie count > 0 for > 30s
  - [ ] Document parent processes causing zombies

- [ ] **Orphan Detection**
  - [ ] Verify orphan-by-ppid is working correctly
  - [ ] Test parent chain traversal for edge cases
  - [ ] Add logging for orphan detection decisions

- [ ] **Daemon Management**
  - [ ] Document all daemon processes (thegent serve, prune-periodic)
  - [ ] Add health checks for daemons
  - [ ] Implement restart policies

### 11.2 Prune Strategy Checklist

- [ ] **RSS-Aware Pruning**
  - [ ] Collect RSS for all candidate processes
  - [ ] Sort candidates by RSS (highest first)
  - [ ] Test that highest-RSS processes are pruned first
  - [ ] Verify memory is freed correctly

- [ ] **Age-Based Pruning**
  - [ ] Collect process elapsed time (`etime`)
  - [ ] Implement decay scoring (longer idle = higher priority)
  - [ ] Balance RSS vs age in prune decision

- [ ] **Graceful Shutdown**
  - [ ] Implement SIGTERM before SIGKILL
  - [ ] Add configurable grace period (default 3s)
  - [ ] Handle SIGTERM acknowledgment
  - [ ] Verify processes terminate cleanly

- [ ] **Process Group Kill**
  - [ ] Identify process groups for LSP/MCP candidates
  - [ ] Use `kill(-pgid, SIGTERM)` for group termination
  - [ ] Verify children are terminated with parent
  - [ ] Handle partial failures

### 11.3 LSP Multiplexing Checklist

- [ ] **Research Phase**
  - [ ] Evaluate lsp-mux for Serena compatibility
  - [ ] Test lsp-mux with TypeScript LSP
  - [ ] Document integration requirements
  - [ ] Assess maintenance burden

- [ ] **POC Phase**
  - [ ] Create minimal POC with Serena
  - [ ] Verify stdio-to-socket adaptation works
  - [ ] Test connection pooling
  - [ ] Measure memory savings

- [ ] **Implementation Phase**
  - [ ] Implement thegent-lsp-proxy (if needed)
  - [ ] Add configuration for per-project sockets
  - [ ] Implement linger timeout
  - [ ] Add monitoring for socket connections

### 11.4 Child Death Handling Checklist

- [ ] **PR_SET_PDEATHSIG (Linux)**
  - [ ] Research IDE support for PDEATHSIG
  - [ ] Document requirements for Cursor/Claude
  - [ ] Create upstream request

- [ ] **Pipe-Based Detection**
  - [ ] Design pipe architecture for thegent subprocesses
  - [ ] Implement EOF detection
  - [ ] Add pipe cleanup on parent exit

- [ ] **Subreaper Pattern**
  - [ ] Evaluate subreaper for thegent serve
  - [ ] Implement subreaper for MCP subprocesses
  - [ ] Document adoption behavior

### 11.5 Resource Isolation Checklist

- [ ] **cgroups (Linux)**
  - [ ] Research user cgroups v2 setup
  - [ ] Implement per-project cgroup creation
  - [ ] Add memory and PID limits
  - [ ] Test isolation between projects

- [ ] **ulimit**
  - [ ] Set ulimits before spawning agent subprocesses
  - [ ] Document ulimit configuration
  - [ ] Test that limits are enforced

---

## 12. Quick Reference Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SMART PRUNE DECISION TREE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────────────────────────┐
    │     Prune Triggered               │
    └─────────────────┬─────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Memory  │ │ Count   │ │ Periodic│
    │ Critical│ │ Threshold│ │ Timer   │
    └────┬────┘ └────┬────┘ └────┬────┘
         │            │            │
         ▼            ▼            ▼
    ┌─────────────────────────────────────────────────┐
    │              ORPHAN DETECTION                   │
    │  Walk parent chain: Cursor/Claude/Codex found?  │
    └────────────────────┬────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │ YES                 │ NO (ORPHAN)
              ▼                     ▼
         ┌─────────┐         ┌─────────────────┐
         │ KEEP    │         │ CANDIDATE FOR   │
         │ (has    │         │ PRUNE           │
         │ parent) │         └────────┬────────┘
         └─────────┘                  │
                                      ▼
                         ┌───────────────────────┐
                         │ SORT BY PRIORITY       │
                         │ 1. RSS (highest first)│
                         │ 2. Age (longest idle) │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ PRUNE SEQUENCE         │
                         │ 1. SIGTERM to process │
                         │ 2. Wait grace_period  │
                         │ 3. SIGKILL if alive   │
                         │ 4. Log to prune.log    │
                         └───────────────────────┘
```

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Strategy implementation checklist (§11), Quick reference decision tree (§12)

| Section | Added Content                                                                          |
| ------- | -------------------------------------------------------------------------------------- |
| §11.1   | Process Lifecycle Checklist (Zombie, Orphan, Daemon)                                   |
| §11.2   | Prune Strategy Checklist (RSS-aware, Age-based, Graceful Shutdown, Process Group Kill) |
| §11.3   | LSP Multiplexing Checklist (Research, POC, Implementation)                             |
| §11.4   | Child Death Handling Checklist (PR_SET_PDEATHSIG, Pipe, Subreaper)                     |
| §11.5   | Resource Isolation Checklist (cgroups, ulimit)                                         |
| §12     | Quick Reference Decision Tree for smart prune decisions                                |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md) - Process automation
- [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md) - Resilience research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
