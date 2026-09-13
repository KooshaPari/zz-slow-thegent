# Swarm Process Optimizations (Multi-Agent / Multi-Tenant / Multi-Project)

Local process optimizations for running multi-agent, multi-tenant, and multi-project swarms smoothly without manual intervention.

**TL;DR:** Set `THGENT_AUTO_PRUNE=1`, run `thegent mcp migrate-unimount all` once, and `thegent mcp spotlight-exclude` per heavy project.

---

## Contents

1. [Automatic Pruning](#1-automatic-pruning-opt-in) — Opt-in auto-prune on Stop
2. [Load-Based Traffic Shaping](#2-load-based-traffic-shaping-wp-5002) — Session thresholds
3. [Spotlight Exclusions](#3-spotlight-exclusions) — Reduce indexer CPU
4. [Uni-Mount MCP](#4-uni-mount-mcp-avoid-duplicate-servers) — Single thegent URL
5. [Gardener Spawn Limits](#5-gardener-spawn-limits) — Disk-based backpressure
6. [Quick Reference](#6-quick-reference-multi-agent-setup) — Setup checklist
7. [Deep Research](#7-deep-research--roadmap) — Full research & roadmap

---

## 1. Automatic Pruning (Opt-In)

**Problem:** Redundant Node.js processes accumulate across sessions and projects:

- **LSP triplet per session**: Each agent session (Claude Code, Cursor) spawns its own LSP + Type Checker + MCP runner. 11 sessions → 20+ Node procs → 1–2 GB each.
- **cc-status bloat**: Multiple cc-status instances (Claude Code internals) with high RSS.
- **Orphan accumulation**: Processes survive session end; manual prune required.

**Solution:** Enable auto-prune on Stop. When orphan process count exceeds a threshold, `thegent mcp prune --force` runs automatically.

### Enabling

```bash
export THGENT_AUTO_PRUNE=1
```

Optional tuning:

| Variable                                | Default | Description                                                                        |
| --------------------------------------- | ------- | ---------------------------------------------------------------------------------- |
| `THGENT_AUTO_PRUNE`                     | 0       | Set to 1 to enable                                                                 |
| `THGENT_AUTO_PRUNE_THRESHOLD`           | 12      | Orphan count above which to prune                                                  |
| `THGENT_AUTO_PRUNE_COOLDOWN`            | 300     | Seconds between prune runs (debounce)                                              |
| `THGENT_AUTO_PRUNE_COOLDOWN_JITTER`     | 30      | Random delay 0–N s before prune (avoids thundering herd)                           |
| `THGENT_PRUNE_GRACE_PERIOD`             | 2       | Seconds to wait after SIGTERM before SIGKILL (graceful shutdown)                   |
| `THGENT_AUTO_PRUNE_MEMORY_THRESHOLD_MB` | 0       | Prune when available memory < this MB (0=disabled)                                 |
| `THGENT_AUTO_PRUNE_CC_STATUS_THRESHOLD` | 3       | Prune when cc-status instances >= this                                             |
| `THGENT_AUTO_PRUNE_PERIODIC_INTERVAL`   | 900     | Periodic prune interval (seconds; used by prune-periodic daemon)                   |
| `THGENT_PRUNE_ORPHAN_BY_PPID`           | 1       | Only kill true orphans (parent chain reaches init); 0 = legacy (kill all matching) |
| `THGENT_PRUNE_SORT_BY`                  | rss     | Sort candidates: rss \| fd \| cpu \| none (kill highest first)                     |
| `THGENT_PRUNE_SORT_ORDER`               | desc    | desc = highest first, asc = lowest first                                           |

Add to `.env` or your shell profile so Cursor/Claude Code inherits it.

### Behavior

- **Stop hook:** `prune-orphans-stop.sh` runs on every Stop
- **Count:** When node/bun/deno processes matching LSP/MCP patterns exceed threshold
- **Memory:** When `THGENT_AUTO_PRUNE_MEMORY_THRESHOLD_MB` is set and available memory < threshold
- **Cooldown:** Skips if last prune was within `THGENT_AUTO_PRUNE_COOLDOWN`
- **Advisory:** Always exits 0; does not block Stop pipeline

### Orphan-by-PPID (Smarter Pruning)

By default, prune only kills **true orphans**: processes whose parent chain reaches init (PID 1) without finding Cursor/Claude/Codex. This avoids killing LSPs/MCPs that are still attached to an active agent tab.

- **Enabled (default):** `THGENT_PRUNE_ORPHAN_BY_PPID=1` — only kill orphans
- **Legacy:** `THGENT_PRUNE_ORPHAN_BY_PPID=0` — kill all matching processes (aggressive)

### Manual Pruning

```bash
thegent mcp prune --dry-run   # Show what would be killed
thegent mcp prune --force     # Kill without confirmation
```

### Periodic Prune Daemon

When Stop doesn't fire (headless runs, Codex), orphans accumulate. Install a periodic daemon:

```bash
thegent mcp prune-periodic install
thegent mcp prune-periodic start
```

- **macOS**: launchd job, runs every 15 min (or `THGENT_AUTO_PRUNE_PERIODIC_INTERVAL` seconds)
- **Linux**: systemd user timer

---

## 2. Load-Based Traffic Shaping (WP-5002)

When sessions exceed thresholds, thegent applies backpressure:

| Threshold | Config                        | Default | Behavior            |
| --------- | ----------------------------- | ------- | ------------------- |
| **Spike** | `THGENT_LOAD_SPIKE_THRESHOLD` | 10      | Traffic shaping     |
| **Surge** | `THGENT_LOAD_SURGE_THRESHOLD` | 20      | Safe-mode activates |

### Per-Owner Slot Cap (Bulkhead)

Limit concurrent runs per owner (project/cwd) to prevent one project from monopolizing slots:

| Variable                                 | Default | Description                    |
| ---------------------------------------- | ------- | ------------------------------ |
| `THGENT_CONCURRENCY_MAX_SLOTS_PER_OWNER` | 0       | Per-owner slot cap; 0=disabled |

Example: `THGENT_CONCURRENCY_MAX_SLOTS_PER_OWNER=2` — each owner (e.g. project dir) can run at most 2 sessions; additional runs are blocked until one completes.

---

## 3. Spotlight Exclusions

**Problem:** mds_stores indexes high-I/O dirs (~/.thegent, .claude, node_modules), causing CPU spikes and memory pressure during agent runs.

**Solution:** Run once per project or when adding new projects. Also:

- Runs automatically during `task setup` (macOS)
- Opt-in: `THGENT_SPOTLIGHT_EXCLUDE_ON_SESSION_START=1` — runs on first SessionStart (macOS)

```bash
thegent mcp spotlight-exclude
```

---

## 4. Uni-Mount MCP (Avoid Duplicate Servers)

Multiple MCP entries (e.g. Playwright, Upstash) can cause handshake errors and duplicate processes.

**Solution:** Migrate to single thegent URL:

```bash
thegent mcp migrate-unimount all
```

---

## 5. Gardener Spawn Limits

The gardener spawn manager stops spawning when disk usage exceeds a threshold:

| Variable                     | Default | Description                                                  |
| ---------------------------- | ------- | ------------------------------------------------------------ |
| `GARDENER_MIN_USAGE_PERCENT` | 15      | Stop spawning when <15% disk free                            |
| `GARDENER_SPAWN_BACKOFF_SEC` | 0       | Seconds to wait before each spawn (backoff between attempts) |

---

## 6. Quick Reference: Multi-Agent Setup

| Step | Command / Config                               | When                     |
| ---- | ---------------------------------------------- | ------------------------ |
| 1    | `export THGENT_AUTO_PRUNE=1` (add to `.env`)   | One-time                 |
| 2    | `thegent mcp migrate-unimount all`             | One-time                 |
| 3    | `thegent mcp spotlight-exclude`                | Per heavy project        |
| 4    | `thegent mcp prune-periodic install` + `start` | Optional: headless/Codex |
| 5    | `thegent mcp prune --force`                    | When memory is high      |

```bash
# Add to .env
export THGENT_AUTO_PRUNE=1
export THGENT_AUTO_PRUNE_THRESHOLD=12

# One-time setup
thegent mcp migrate-unimount all

# Per heavy project
thegent mcp spotlight-exclude

# Optional: periodic prune (headless/Codex)
thegent mcp prune-periodic install && thegent mcp prune-periodic start

# Manual prune when needed
thegent mcp prune --force
```

---

## 7. Deep Research & Roadmap

**Index**: [SWARM_RESEARCH_INDEX.md](../research/SWARM_RESEARCH_INDEX.md) — master index for all swarm/resource research.

For a comprehensive research and phased plan (automation taxonomy, multi-tenant isolation, macOS memory sampling, orphan-by-ppid, MTSP alignment, platform ecosystem, failure modes), see:

**[SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](../research/SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)**

For a deep dive into **optimization, management, and scheduling systems** (scheduling theory, load balancing, ConcurrencyController mapping, industry systems like Slurm/Kubernetes/Celery, algorithms), see:

**[SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md](../research/SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md)**

For **long-term memory optimizations** (LSP triplet reduction, cc-status bloat, Spotlight thrashing, phased roadmap), see:

**[MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md](../research/MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md)**

For **smart & robust strategies** (process lifecycle, LSP multiplexing, child death handling, decision matrices), see:

**[SMART_ROBUST_STRATEGIES_RESEARCH.md](../research/SMART_ROBUST_STRATEGIES_RESEARCH.md)**

For **FD, CPU, threads, ports** (resource sampling, limits, per-process metrics, Activity Monitor–style), see:

**[SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md](../research/SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md)**

For **advanced resilience** (retry, exponential backoff, jitter, circuit breaker, bulkhead, fairness), see:

**[ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md](../research/ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md)**

For **MCP tool retry policy** (when we retry, circuit breaker, backoff), see:

**[MCP_RETRY_POLICY.md](./MCP_RETRY_POLICY.md)**

---

_Cross-ref: [SWARM_MEMORY_COORDINATION_DEPTH.md](./SWARM_MEMORY_COORDINATION_DEPTH.md) · [UNIFIED_WORK_STREAM_DESIGN.md](./UNIFIED_WORK_STREAM_DESIGN.md) · [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md)_

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
