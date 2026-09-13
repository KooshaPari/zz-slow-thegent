# Unified Work Stream

**Status:** Active | **Last Updated:** 2026-02-18 | **Total Items:** 130+ | **Source:** thegent/PLAN.md + sharecli/PLAN.md

---

## Schema

| Column         | Description                                                                      |
| -------------- | -------------------------------------------------------------------------------- |
| **ID**         | Unique task identifier (format: `{PROJECT}-{PHASE}.{TASK}` or `P{PHASE}.{TASK}`) |
| **Title**      | Task description (brief, <80 chars)                                              |
| **Type**       | `feature` \| `refactor` \| `bugfix` \| `infra` \| `research` \| `docs`           |
| **Project**    | `thegent` or `sharecli`                                                          |
| **Phase**      | Phase number (0-18) or epic name                                                 |
| **Depends On** | Prerequisite task IDs (comma-separated)                                          |
| **Effort**     | Estimate: `~3min` / `~5min` / `~8min` / `~10min` / `~15min` / `~20min`           |
| **Status**     | `PENDING` / `CLAIMED` / `IN_PROGRESS` / `COMPLETED` / `BLOCKED`                  |

---

## PENDING

All actionable, unassigned work items. Ordered by project, phase, then task ID.

### thegent: Phase 0 (Foundation - COMPLETE)

| ID        | Title                                                          | Type  | Depends On           | Effort | Status    |
| --------- | -------------------------------------------------------------- | ----- | -------------------- | ------ | --------- |
| TGNT-P0.1 | Symlink dispatch mechanism (`bin/harness` + N symlinks)        | infra | --                   | ~5min  | COMPLETED |
| TGNT-P0.2 | Agent detection via `/proc` tree walk with macOS `ps` fallback | infra | TGNT-P0.1            | ~5min  | COMPLETED |
| TGNT-P0.3 | `rules.conf` parser (command, strategy, options)               | infra | TGNT-P0.1            | ~3min  | COMPLETED |
| TGNT-P0.4 | Coalesce strategy (flock + SHA256 cache key + atomic writes)   | infra | TGNT-P0.2, TGNT-P0.3 | ~10min | COMPLETED |
| TGNT-P0.5 | Queue strategy (bounded concurrency pool with slot files)      | infra | TGNT-P0.3            | ~8min  | COMPLETED |
| TGNT-P0.6 | Debounce strategy (delay + coalesce within window)             | infra | TGNT-P0.3            | ~5min  | COMPLETED |
| TGNT-P0.7 | `harness sync` symlink generator from rules.conf               | infra | TGNT-P0.3            | ~3min  | COMPLETED |
| TGNT-P0.8 | `nocache_args` safety (`--fix` / `--write` -> queue fallback)  | infra | TGNT-P0.4            | ~3min  | COMPLETED |

### thegent: Phase 1 (Quick Wins - COMPLETE)

| ID        | Title                                                          | Type  | Depends On | Effort | Status    |
| --------- | -------------------------------------------------------------- | ----- | ---------- | ------ | --------- |
| TGNT-P1.1 | Lock timeout via `HARNESS_LOCK_TIMEOUT` (fallback to uncached) | infra | TGNT-P0.4  | ~3min  | COMPLETED |
| TGNT-P1.2 | Stale-while-revalidate (serve stale + background refresh)      | infra | TGNT-P0.4  | ~5min  | COMPLETED |
| TGNT-P1.3 | Prometheus metrics endpoint (`harness metrics`)                | infra | TGNT-P0.4  | ~5min  | COMPLETED |
| TGNT-P1.4 | Cache compression (zstd for outputs > 10KB)                    | infra | TGNT-P0.4  | ~5min  | COMPLETED |
| TGNT-P1.5 | JSON metrics export (`harness metrics json`)                   | infra | TGNT-P1.3  | ~2min  | COMPLETED |

### thegent: Phase 2 (Intelligence - COMPLETE)

| ID        | Title                                                             | Type    | Depends On | Effort | Status    |
| --------- | ----------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P2.1 | 5-level priority queue (critical/high/normal/low/background)      | feature | TGNT-P1.1  | ~8min  | COMPLETED |
| TGNT-P2.2 | Priority aging (+1 level per 5s waiting, prevents starvation)     | feature | TGNT-P2.1  | ~3min  | COMPLETED |
| TGNT-P2.3 | Fair share scheduling (per-agent quota with penalty for over-use) | feature | TGNT-P2.1  | ~8min  | COMPLETED |
| TGNT-P2.4 | Semantic coalescing (path normalization, `.` -> project root)     | feature | TGNT-P0.4  | ~5min  | COMPLETED |
| TGNT-P2.5 | Queue timeout protection (fallback execution on timeout)          | feature | TGNT-P2.1  | ~3min  | COMPLETED |

### thegent: Phase 3 (Performance - COMPLETE)

| ID        | Title                                                  | Type    | Depends On           | Effort | Status    |
| --------- | ------------------------------------------------------ | ------- | -------------------- | ------ | --------- |
| TGNT-P3.1 | L1 memory cache (`/dev/shm`, 100MB max, 60s TTL)       | infra   | TGNT-P0.4            | ~8min  | COMPLETED |
| TGNT-P3.2 | L2 disk cache (`var/cache`, compressed, persistent)    | infra   | TGNT-P0.4            | ~5min  | COMPLETED |
| TGNT-P3.3 | L2-to-L1 promotion on cache hit (automatic)            | infra   | TGNT-P3.1, TGNT-P3.2 | ~5min  | COMPLETED |
| TGNT-P3.4 | I/O scheduler integration (ionice priority classes)    | feature | TGNT-P2.1            | ~5min  | COMPLETED |
| TGNT-P3.5 | Negative stat cache (track nonexistent files, 5s TTL)  | feature | TGNT-P3.1            | ~3min  | COMPLETED |
| TGNT-P3.6 | Page cache warmer (bulk read by file type before exec) | feature | TGNT-P0.4            | ~5min  | COMPLETED |

### thegent: Phase 4 (Coordination - COMPLETE)

| ID        | Title                                                        | Type    | Depends On | Effort | Status    |
| --------- | ------------------------------------------------------------ | ------- | ---------- | ------ | --------- |
| TGNT-P4.1 | Intent broadcasting (agents signal planned file ops)         | feature | TGNT-P0.4  | ~8min  | COMPLETED |
| TGNT-P4.2 | Intent conflict checking (write-write, read-write detection) | feature | TGNT-P4.1  | ~5min  | COMPLETED |
| TGNT-P4.3 | Wait-for graph construction from lock records                | feature | TGNT-P0.5  | ~8min  | COMPLETED |
| TGNT-P4.4 | DFS cycle detection for deadlocks                            | feature | TGNT-P4.3  | ~5min  | COMPLETED |
| TGNT-P4.5 | Deadlock auto-resolution (abort youngest waiter)             | feature | TGNT-P4.4  | ~3min  | COMPLETED |
| TGNT-P4.6 | Fair share tracking with 50% decay smoothing                 | feature | TGNT-P2.3  | ~5min  | COMPLETED |

### thegent: Phase 5 (Polish - COMPLETE)

| ID        | Title                                                                | Type    | Depends On                      | Effort | Status    |
| --------- | -------------------------------------------------------------------- | ------- | ------------------------------- | ------ | --------- |
| TGNT-P5.1 | Interactive dashboard (TUI with cache/queue/intent/fair share)       | feature | TGNT-P1.3, TGNT-P2.3, TGNT-P4.1 | ~10min | COMPLETED |
| TGNT-P5.2 | Self-tuning report (analyze metrics, detect low hit rate/contention) | feature | TGNT-P1.3, TGNT-P3.1            | ~8min  | COMPLETED |
| TGNT-P5.3 | Auto-fix recommendations (color-coded severity, safe auto-apply)     | feature | TGNT-P5.2                       | ~5min  | COMPLETED |
| TGNT-P5.4 | Rules suggestion engine (generate rules from observed patterns)      | feature | TGNT-P5.2                       | ~5min  | COMPLETED |
| TGNT-P5.5 | L1 vs L2 benchmark command                                           | feature | TGNT-P3.1, TGNT-P3.2            | ~3min  | COMPLETED |

### thegent: Phase 6 (Git Parallelism - COMPLETE)

| ID        | Title                                                                   | Type    | Depends On | Effort | Status    |
| --------- | ----------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P6.1 | Per-agent `GIT_INDEX_FILE` management (init, copy, cleanup)             | feature | TGNT-P4.1  | ~8min  | COMPLETED |
| TGNT-P6.2 | Git plumbing commit pipeline (hash-object -> write-tree -> commit-tree) | feature | TGNT-P6.1  | ~10min | COMPLETED |
| TGNT-P6.3 | CAS ref update with exponential backoff + jitter retry                  | feature | TGNT-P6.2  | ~5min  | COMPLETED |
| TGNT-P6.4 | Scoped staging (agent-to-file mapping, parallel when non-overlapping)   | feature | TGNT-P6.1  | ~5min  | COMPLETED |
| TGNT-P6.5 | `harness git status` per-agent view (show each agent's staged changes)  | feature | TGNT-P6.4  | ~3min  | COMPLETED |

### thegent: Phase 7 (Smart Merge - COMPLETE)

| ID        | Title                                                                  | Type    | Depends On           | Effort | Status    |
| --------- | ---------------------------------------------------------------------- | ------- | -------------------- | ------ | --------- |
| TGNT-P7.1 | Mergiraf integration (AST merge for Python/JS/TS/Rust/Go/Java/C)       | feature | TGNT-P6.3            | ~10min | COMPLETED |
| TGNT-P7.2 | Conflict prediction from intents (trial merge before commit)           | feature | TGNT-P4.1, TGNT-P6.3 | ~8min  | COMPLETED |
| TGNT-P7.3 | Import union auto-resolve (Python/JS import conflicts -> sorted union) | feature | TGNT-P7.1            | ~5min  | COMPLETED |
| TGNT-P7.4 | JSON/YAML structural merge (deep merge via jq, ours-wins on conflict)  | feature | TGNT-P7.1            | ~5min  | COMPLETED |

### thegent: Phase 8 (File Coordination - COMPLETE)

| ID        | Title                                                                      | Type    | Depends On | Effort | Status    |
| --------- | -------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P8.1 | OCC version check on write (record version at claim, verify before commit) | feature | TGNT-P4.1  | ~8min  | COMPLETED |
| TGNT-P8.2 | HLC timestamp generation (millisecond physical + logical counter)          | feature | TGNT-P8.1  | ~5min  | COMPLETED |
| TGNT-P8.3 | Lease-based file claims registry (read/write/exclusive with flock)         | feature | TGNT-P8.1  | ~8min  | COMPLETED |
| TGNT-P8.4 | Lease renewal and expiry (background cleanup daemon)                       | feature | TGNT-P8.3  | ~5min  | COMPLETED |

### thegent: Phase 9 (Request Coalescing v2 - COMPLETE)

| ID        | Title                                                                        | Type    | Depends On | Effort | Status    |
| --------- | ---------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P9.1 | Singleflight dedup pattern (first executes, rest wait for shared result)     | feature | TGNT-P0.4  | ~5min  | COMPLETED |
| TGNT-P9.2 | inotify cache invalidation (watch file changes, invalidate affected entries) | feature | TGNT-P3.1  | ~8min  | COMPLETED |
| TGNT-P9.3 | Heat-based LRU eviction (access frequency with exponential decay)            | feature | TGNT-P3.1  | ~5min  | COMPLETED |

### thegent: Phase 10 (Resource Isolation - COMPLETE)

| ID         | Title                                                                  | Type    | Depends On | Effort | Status    |
| ---------- | ---------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P10.1 | Per-agent TMPDIR allocation (private temp, cleanup on exit)            | feature | TGNT-P0.2  | ~3min  | COMPLETED |
| TGNT-P10.2 | Dynamic port range allocation (registry + liveness check)              | feature | TGNT-P10.1 | ~5min  | COMPLETED |
| TGNT-P10.3 | Environment variable isolation (agent-specific env file, wrapped exec) | feature | TGNT-P10.1 | ~5min  | COMPLETED |

### thegent: Phase 11 (IPC Primitives - COMPLETE)

| ID         | Title                                                                   | Type    | Depends On | Effort | Status    |
| ---------- | ----------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P11.1 | tmpfs mesh directory creation (`/tmp/agent-mesh`, 256MB, mode 1777)     | infra   | --         | ~3min  | COMPLETED |
| TGNT-P11.2 | Atomic mkdir lock primitives (EEXIST = already held) + claim + lease    | infra   | TGNT-P11.1 | ~5min  | COMPLETED |
| TGNT-P11.3 | Maildir message queue (tmp -> new -> cur lifecycle, TTL enforcement)    | infra   | TGNT-P11.1 | ~10min | COMPLETED |
| TGNT-P11.4 | inotify event notification (1-10ms latency, polling fallback for macOS) | feature | TGNT-P11.3 | ~8min  | COMPLETED |
| TGNT-P11.5 | Write-ahead log (WAL) with append-before-execute + replay-on-crash      | infra   | TGNT-P11.1 | ~8min  | COMPLETED |

### thegent: Phase 12 (Process Discovery - COMPLETE)

| ID         | Title                                                                    | Type    | Depends On | Effort | Status    |
| ---------- | ------------------------------------------------------------------------ | ------- | ---------- | ------ | --------- |
| TGNT-P12.1 | `/proc` scanner with agent-specific patterns (Claude/Aider/Cursor/Cline) | feature | TGNT-P11.1 | ~8min  | COMPLETED |
| TGNT-P12.2 | Agent manifest creation (YAML: id, type, pid, capabilities, ODD, status) | feature | TGNT-P12.1 | ~5min  | COMPLETED |
| TGNT-P12.3 | Heartbeat monitor (touch-file every 5s, 15s failure threshold)           | feature | TGNT-P12.2 | ~5min  | COMPLETED |
| TGNT-P12.4 | Stale agent cleanup (reclaim tasks, notify dependents, archive manifest) | feature | TGNT-P12.3 | ~3min  | COMPLETED |

### thegent: Phase 13 (Shell Injection - COMPLETE)

| ID         | Title                                                                              | Type    | Depends On | Effort | Status    |
| ---------- | ---------------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P13.1 | tmux session detection and naming (`mesh-{agent-uuid}`)                            | feature | TGNT-P12.1 | ~5min  | COMPLETED |
| TGNT-P13.2 | Command injection via `tmux send-keys -l` + 1.5s delay + Enter (>99% reliable)     | feature | TGNT-P13.1 | ~8min  | COMPLETED |
| TGNT-P13.3 | Agent readiness detection (prompt patterns per agent type, busy/idle/error states) | feature | TGNT-P13.2 | ~5min  | COMPLETED |

### thegent: Phase 14 (Context Injection - COMPLETE)

| ID         | Title                                                                       | Type    | Depends On | Effort | Status    |
| ---------- | --------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P14.1 | AGENT.md template system (mesh state, coordination rules, identity)         | feature | TGNT-P12.2 | ~5min  | COMPLETED |
| TGNT-P14.2 | Tool-specific context files (CLAUDE.md, .cursorrules, .clinerules symlinks) | feature | TGNT-P14.1 | ~8min  | COMPLETED |
| TGNT-P14.3 | Dynamic context update (re-render AGENT.md on mesh state changes)           | feature | TGNT-P14.2 | ~5min  | COMPLETED |

### thegent: Phase 15 (Worktree Support - COMPLETE)

| ID         | Title                                                                        | Type    | Depends On | Effort | Status    |
| ---------- | ---------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P15.1 | Optional worktree creation (`git worktree add .mesh/worktrees/agent-{uuid}`) | feature | TGNT-P6.1  | ~8min  | COMPLETED |
| TGNT-P15.2 | Branch coordination (registry, collision avoidance, status tracking)         | feature | TGNT-P15.1 | ~5min  | COMPLETED |
| TGNT-P15.3 | Worktree cleanup (orphan detection, 30s grace, health monitor)               | feature | TGNT-P15.2 | ~3min  | COMPLETED |

### thegent: Phase 16 (Sandboxing - COMPLETE)

| ID         | Title                                                                            | Type    | Depends On             | Effort | Status    |
| ---------- | -------------------------------------------------------------------------------- | ------- | ---------------------- | ------ | --------- |
| TGNT-P16.1 | bubblewrap profile (Linux: filesystem + network + process policies)              | infra   | TGNT-P12.2             | ~10min | COMPLETED |
| TGNT-P16.2 | seatbelt profile (macOS: sandbox-exec equivalent)                                | infra   | TGNT-P12.2             | ~10min | COMPLETED |
| TGNT-P16.3 | 5-tier autonomy enforcement (read -> worktree -> git -> shared -> production)    | feature | TGNT-P16.1, TGNT-P16.2 | ~8min  | COMPLETED |
| TGNT-P16.4 | Operation classification engine (tier assignment from command + target analysis) | feature | TGNT-P16.3             | ~8min  | COMPLETED |

### thegent: Phase 17 (Resource Management - COMPLETE)

| ID         | Title                                                         | Type    | Depends On | Effort | Status    |
| ---------- | ------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| TGNT-P17.1 | Memory limit enforcement (cgroups on Linux, ulimit fallback)  | feature | TGNT-P12.2 | ~8min  | COMPLETED |
| TGNT-P17.2 | Process count limits (detect runaway subprocess spawning)     | feature | TGNT-P17.1 | ~5min  | COMPLETED |
| TGNT-P17.3 | FD budget allocation (monitor per-agent, alert at thresholds) | feature | TGNT-P17.2 | ~5min  | COMPLETED |

### thegent: Phase 18 (Observability v2 - COMPLETE)

| ID         | Title                                                                    | Type    | Depends On            | Effort | Status    |
| ---------- | ------------------------------------------------------------------------ | ------- | --------------------- | ------ | --------- |
| TGNT-P18.1 | JSONL structured logging (PIPE_BUF-aware, atomic append, <4KB per line)  | infra   | TGNT-P11.1            | ~5min  | COMPLETED |
| TGNT-P18.2 | Advanced metrics aggregation (per-agent, per-command, histograms)        | feature | TGNT-P1.3, TGNT-P12.2 | ~8min  | COMPLETED |
| TGNT-P18.3 | CLI for mesh management (`mesh status`, `mesh agents`, `mesh tasks`)     | feature | TGNT-P12.2            | ~10min | COMPLETED |
| TGNT-P18.4 | Health dashboard v2 (agent activity, port/tmpdir usage, claims, intents) | feature | TGNT-P5.1, TGNT-P18.2 | ~10min | COMPLETED |

---

## sharecli: Phases 0-3 (Early Stages)

### Phase 0: Foundation & Prototype (COMPLETE)

| ID        | Title                                                    | Type     | Depends On | Effort | Status    |
| --------- | -------------------------------------------------------- | -------- | ---------- | ------ | --------- |
| SCLI-P0.1 | Mission statement and hard problems analysis             | research | --         | ~5min  | COMPLETED |
| SCLI-P0.2 | System architecture diagram and component overview       | docs     | SCLI-P0.1  | ~8min  | COMPLETED |
| SCLI-P0.3 | Configuration schema (rules.conf, agents.conf, env vars) | docs     | SCLI-P0.2  | ~5min  | COMPLETED |
| SCLI-P0.4 | Risk register with mitigation strategies                 | docs     | SCLI-P0.2  | ~8min  | COMPLETED |
| SCLI-P0.5 | Tech stack justification (Bash, Rust, C, flock, etc.)    | docs     | SCLI-P0.2  | ~5min  | COMPLETED |

### Phase 1: Process Detection & Agent Mesh Initialization (PENDING)

| ID        | Title                                                                  | Type    | Depends On | Effort | Status    |
| --------- | ---------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P1.1 | Process enumeration from `/proc` (or `ps` for macOS)                   | feature | --         | ~8min  | COMPLETED |
| SCLI-P1.2 | Agent pattern matching (regex-based detection from agents.conf)        | feature | SCLI-P1.1  | ~5min  | COMPLETED |
| SCLI-P1.3 | Agent manifest system (YAML with metadata, capabilities, ODD)          | feature | SCLI-P1.2  | ~8min  | COMPLETED |
| SCLI-P1.4 | Mesh directory initialization (`/tmp/agent-mesh` or configurable)      | infra   | --         | ~3min  | COMPLETED |
| SCLI-P1.5 | Agent heartbeat mechanism (touch-file every 5s, 15s failure detection) | feature | SCLI-P1.3  | ~8min  | COMPLETED |
| SCLI-P1.6 | Stale agent cleanup and task reclamation                               | feature | SCLI-P1.5  | ~8min  | COMPLETED |

### Phase 2: IPC & Coordination (PENDING)

| ID        | Title                                                          | Type    | Depends On | Effort | Status    |
| --------- | -------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P2.1 | Atomic mkdir lock primitives for mesh coordination             | infra   | SCLI-P1.4  | ~5min  | COMPLETED |
| SCLI-P2.2 | Maildir message queue system (tmp -> new -> cur lifecycle)     | feature | SCLI-P1.4  | ~10min | COMPLETED |
| SCLI-P2.3 | inotify-based event notification (with /proc polling fallback) | feature | SCLI-P2.2  | ~8min  | COMPLETED |
| SCLI-P2.4 | Write-ahead log (WAL) for crash recovery                       | infra   | SCLI-P1.4  | ~8min  | COMPLETED |
| SCLI-P2.5 | Intent broadcasting system (agents signal planned operations)  | feature | SCLI-P2.2  | ~8min  | COMPLETED |
| SCLI-P2.6 | Intent conflict detection (write-write, read-write conflicts)  | feature | SCLI-P2.5  | ~5min  | COMPLETED |

### Phase 3: Consensus & Escalation (PENDING)

| ID        | Title                                                                            | Type    | Depends On | Effort | Status    |
| --------- | -------------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P3.1 | Consensus protocol (majority for implementation, supermajority for architecture) | feature | SCLI-P2.5  | ~8min  | COMPLETED |
| SCLI-P3.2 | Shapley-value causal influence tracking                                          | feature | SCLI-P3.1  | ~10min | COMPLETED |
| SCLI-P3.3 | 5-tier escalation workflow (self -> peer -> lead -> committee -> human)          | feature | SCLI-P3.1  | ~10min | COMPLETED |
| SCLI-P3.4 | Async human escalation queue                                                     | feature | SCLI-P3.3  | ~5min  | COMPLETED |
| SCLI-P3.5 | Confidence scoring and debate capping (max 3 rounds)                             | feature | SCLI-P3.1  | ~8min  | COMPLETED |

---

## sharecli: Phases 4-9 (Mid-Stage Features)

### Phase 4: Git Operations & Parallelism (PENDING)

| ID        | Title                                                                        | Type    | Depends On | Effort | Status    |
| --------- | ---------------------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P4.1 | Per-agent `GIT_INDEX_FILE` implementation                                    | feature | SCLI-P1.3  | ~8min  | COMPLETED |
| SCLI-P4.2 | Git plumbing pipeline (hash-object, write-tree, commit-tree, update-ref CAS) | feature | SCLI-P4.1  | ~10min | COMPLETED |
| SCLI-P4.3 | CAS retry loop with exponential backoff and jitter                           | feature | SCLI-P4.2  | ~5min  | COMPLETED |
| SCLI-P4.4 | Scoped staging (agent-to-file mapping for parallel operations)               | feature | SCLI-P4.1  | ~5min  | COMPLETED |
| SCLI-P4.5 | Per-agent git status view (show staged changes per agent)                    | feature | SCLI-P4.4  | ~3min  | COMPLETED |

### Phase 5: Smart Merge (PENDING)

| ID        | Title                                                        | Type    | Depends On           | Effort | Status    |
| --------- | ------------------------------------------------------------ | ------- | -------------------- | ------ | --------- |
| SCLI-P5.1 | Mergiraf integration (AST-aware merge for 10+ languages)     | feature | SCLI-P4.2            | ~10min | COMPLETED |
| SCLI-P5.2 | Conflict prediction before commit (trial merge from intents) | feature | SCLI-P2.5, SCLI-P4.2 | ~8min  | COMPLETED |
| SCLI-P5.3 | Import union auto-resolution (Python/JS imports)             | feature | SCLI-P5.1            | ~5min  | COMPLETED |
| SCLI-P5.4 | JSON/YAML structural merge (deep merge via jq)               | feature | SCLI-P5.1            | ~5min  | COMPLETED |

### Phase 6: File Coordination (PENDING)

| ID        | Title                                                   | Type    | Depends On | Effort | Status    |
| --------- | ------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P6.1 | Optimistic concurrency control (OCC) version tracking   | feature | SCLI-P2.5  | ~8min  | COMPLETED |
| SCLI-P6.2 | Hybrid Logical Clock (HLC) timestamp generation         | feature | SCLI-P6.1  | ~5min  | COMPLETED |
| SCLI-P6.3 | Lease-based file claims registry (read/write/exclusive) | feature | SCLI-P6.1  | ~8min  | COMPLETED |
| SCLI-P6.4 | Lease renewal and expiry management                     | feature | SCLI-P6.3  | ~5min  | COMPLETED |

### Phase 7: Caching & Request Deduplication (PENDING)

| ID        | Title                                                  | Type    | Depends On | Effort | Status    |
| --------- | ------------------------------------------------------ | ------- | ---------- | ------ | --------- |
| SCLI-P7.1 | Singleflight deduplication (first executes, rest wait) | feature | --         | ~5min  | COMPLETED |
| SCLI-P7.2 | inotify-based cache invalidation on file changes       | feature | SCLI-P2.3  | ~8min  | COMPLETED |
| SCLI-P7.3 | Heat-based LRU eviction (access frequency tracking)    | feature | --         | ~5min  | COMPLETED |

### Phase 8: Resource Isolation (PENDING)

| ID        | Title                                               | Type    | Depends On | Effort | Status    |
| --------- | --------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P8.1 | Per-agent TMPDIR allocation and cleanup             | feature | SCLI-P1.3  | ~3min  | COMPLETED |
| SCLI-P8.2 | Dynamic port range allocation (registry + liveness) | feature | SCLI-P8.1  | ~5min  | COMPLETED |
| SCLI-P8.3 | Environment variable isolation per agent            | feature | SCLI-P8.1  | ~5min  | COMPLETED |

### Phase 9: Shell Injection & Context Injection (PENDING)

| ID        | Title                                                          | Type    | Depends On | Effort | Status    |
| --------- | -------------------------------------------------------------- | ------- | ---------- | ------ | --------- |
| SCLI-P9.1 | tmux session detection and naming                              | feature | SCLI-P1.3  | ~5min  | COMPLETED |
| SCLI-P9.2 | tmux command injection (`send-keys` with 1.5s delay)           | feature | SCLI-P9.1  | ~8min  | PENDING   |
| SCLI-P9.3 | Agent readiness detection (prompt patterns, busy/idle/error)   | feature | SCLI-P9.2  | ~5min  | PENDING   |
| SCLI-P9.4 | AGENT.md template system (dynamic mesh state injection)        | feature | SCLI-P1.3  | ~5min  | PENDING   |
| SCLI-P9.5 | Tool-specific context files (CLAUDE.md, .cursorrules symlinks) | feature | SCLI-P9.4  | ~8min  | PENDING   |

---

## sharecli: Phases 10-14 (Advanced Features)

### Phase 10: Sandboxing (PENDING)

| ID         | Title                                                                         | Type    | Depends On             | Effort | Status  |
| ---------- | ----------------------------------------------------------------------------- | ------- | ---------------------- | ------ | ------- |
| SCLI-P10.1 | bubblewrap profile (Linux filesystem/network/process policies)                | infra   | SCLI-P1.3              | ~10min | PENDING |
| SCLI-P10.2 | seatbelt profile (macOS sandbox-exec equivalent)                              | infra   | SCLI-P1.3              | ~10min | PENDING |
| SCLI-P10.3 | 5-tier autonomy enforcement (read -> worktree -> git -> shared -> production) | feature | SCLI-P10.1, SCLI-P10.2 | ~8min  | PENDING |
| SCLI-P10.4 | Operation classification (tier assignment from command + target)              | feature | SCLI-P10.3             | ~8min  | PENDING |

### Phase 11: Worktree Support (PENDING)

| ID         | Title                                       | Type    | Depends On | Effort | Status  |
| ---------- | ------------------------------------------- | ------- | ---------- | ------ | ------- |
| SCLI-P11.1 | Optional per-agent git worktree creation    | feature | SCLI-P4.1  | ~8min  | PENDING |
| SCLI-P11.2 | Branch coordination and collision avoidance | feature | SCLI-P11.1 | ~5min  | PENDING |
| SCLI-P11.3 | Worktree cleanup and orphan detection       | feature | SCLI-P11.2 | ~3min  | PENDING |

### Phase 12: Resource Management (PENDING)

| ID         | Title                                                        | Type    | Depends On | Effort | Status  |
| ---------- | ------------------------------------------------------------ | ------- | ---------- | ------ | ------- |
| SCLI-P12.1 | Memory limit enforcement (cgroups on Linux, ulimit fallback) | feature | SCLI-P1.3  | ~8min  | PENDING |
| SCLI-P12.2 | Process count limits (runaway subprocess detection)          | feature | SCLI-P12.1 | ~5min  | PENDING |
| SCLI-P12.3 | File descriptor budget allocation and monitoring             | feature | SCLI-P12.2 | ~5min  | PENDING |

### Phase 13: Observability (PENDING)

| ID         | Title                                                       | Type    | Depends On | Effort | Status  |
| ---------- | ----------------------------------------------------------- | ------- | ---------- | ------ | ------- |
| SCLI-P13.1 | JSONL structured logging (atomic append, <4KB per line)     | infra   | SCLI-P1.4  | ~5min  | PENDING |
| SCLI-P13.2 | Advanced metrics aggregation (per-agent, per-command)       | feature | --         | ~8min  | PENDING |
| SCLI-P13.3 | CLI mesh management commands (`mesh status`, `mesh agents`) | feature | SCLI-P1.3  | ~10min | PENDING |
| SCLI-P13.4 | Health dashboard v2 (activity, usage, claims, intents)      | feature | SCLI-P13.2 | ~10min | PENDING |

### Phase 14: Audit & Recovery (PENDING)

| ID         | Title                                                      | Type    | Depends On | Effort | Status  |
| ---------- | ---------------------------------------------------------- | ------- | ---------- | ------ | ------- |
| SCLI-P14.1 | Shadow git repo for full delete recovery                   | feature | SCLI-P4.2  | ~10min | PENDING |
| SCLI-P14.2 | Audit trail with inotify sync to shadow repo               | feature | SCLI-P14.1 | ~8min  | PENDING |
| SCLI-P14.3 | Full recovery workflow (cross-reference dev + audit repos) | feature | SCLI-P14.2 | ~8min  | PENDING |

---

## CLAIMED

| ID        | Title                                   | Agent         | Claimed At           | Expected Completion  |
| --------- | --------------------------------------- | ------------- | -------------------- | -------------------- |
| TGNT-P6.1 | Per-agent GIT_INDEX_FILE management     | phase6-worker | 2026-02-18T16:45:00Z | 2026-02-18T16:53:00Z |
| TGNT-P6.2 | Git plumbing commit pipeline            | phase6-worker | 2026-02-18T16:45:00Z | 2026-02-18T17:05:00Z |
| TGNT-P6.3 | CAS ref update with exponential backoff | phase6-worker | 2026-02-18T16:45:00Z | 2026-02-18T17:10:00Z |
| TGNT-P6.4 | Scoped staging (agent-to-file mapping)  | phase6-worker | 2026-02-18T16:45:00Z | 2026-02-18T17:15:00Z |
| TGNT-P6.5 | harness git status per-agent view       | phase6-worker | 2026-02-18T16:45:00Z | 2026-02-18T17:18:00Z |

---

## COMPLETED

| ID         | Title                                                        | Completed At | Effort | Notes                                                |
| ---------- | ------------------------------------------------------------ | ------------ | ------ | ---------------------------------------------------- |
| TGNT-P0.1  | Symlink dispatch mechanism                                   | 2026-02-15   | ~5min  | Core harness foundation                              |
| TGNT-P0.2  | Agent detection via `/proc` tree walk                        | 2026-02-15   | ~5min  | Includes macOS `ps` fallback                         |
| TGNT-P0.3  | `rules.conf` parser                                          | 2026-02-15   | ~3min  | Command, strategy, options support                   |
| TGNT-P0.4  | Coalesce strategy                                            | 2026-02-15   | ~10min | flock + SHA256 + atomic writes                       |
| TGNT-P0.5  | Queue strategy                                               | 2026-02-16   | ~8min  | Bounded concurrency pool                             |
| TGNT-P0.6  | Debounce strategy                                            | 2026-02-16   | ~5min  | Delay + coalesce within window                       |
| TGNT-P0.7  | `harness sync` symlink generator                             | 2026-02-16   | ~3min  | From rules.conf                                      |
| TGNT-P0.8  | `nocache_args` safety                                        | 2026-02-16   | ~3min  | `--fix`/`--write` fallback                           |
| TGNT-P1.1  | Lock timeout + fallback                                      | 2026-02-16   | ~3min  | HARNESS_LOCK_TIMEOUT env var                         |
| TGNT-P1.2  | Stale-while-revalidate                                       | 2026-02-16   | ~5min  | Serve stale + background refresh                     |
| TGNT-P1.3  | Prometheus metrics                                           | 2026-02-16   | ~5min  | `harness metrics` endpoint                           |
| TGNT-P1.4  | Cache compression                                            | 2026-02-16   | ~5min  | zstd for outputs > 10KB                              |
| TGNT-P1.5  | JSON metrics export                                          | 2026-02-16   | ~2min  | `harness metrics json`                               |
| TGNT-P2.1  | 5-level priority queue                                       | 2026-02-17   | ~8min  | critical/high/normal/low/background                  |
| TGNT-P2.2  | Priority aging                                               | 2026-02-17   | ~3min  | +1 level per 5s, prevents starvation                 |
| TGNT-P2.3  | Fair share scheduling                                        | 2026-02-17   | ~8min  | Per-agent quota + penalty                            |
| TGNT-P2.4  | Semantic coalescing                                          | 2026-02-17   | ~5min  | Path normalization, `.` -> root                      |
| TGNT-P2.5  | Queue timeout protection                                     | 2026-02-17   | ~3min  | Fallback execution on timeout                        |
| TGNT-P3.1  | L1 memory cache                                              | 2026-02-17   | ~8min  | `/dev/shm`, 100MB, 60s TTL                           |
| TGNT-P3.2  | L2 disk cache                                                | 2026-02-17   | ~5min  | `var/cache`, compressed, persistent                  |
| TGNT-P3.3  | L2-to-L1 promotion                                           | 2026-02-17   | ~5min  | Automatic on cache hit                               |
| TGNT-P3.4  | I/O scheduler integration                                    | 2026-02-17   | ~5min  | ionice priority classes                              |
| TGNT-P3.5  | Negative stat cache                                          | 2026-02-17   | ~3min  | Nonexistent files, 5s TTL                            |
| TGNT-P3.6  | Page cache warmer                                            | 2026-02-17   | ~5min  | Bulk read by file type                               |
| TGNT-P4.1  | Intent broadcasting                                          | 2026-02-18   | ~8min  | Agents signal planned ops                            |
| TGNT-P4.2  | Intent conflict checking                                     | 2026-02-18   | ~5min  | write-write, read-write detection                    |
| TGNT-P4.3  | Wait-for graph                                               | 2026-02-18   | ~8min  | From lock records                                    |
| TGNT-P4.4  | DFS cycle detection                                          | 2026-02-18   | ~5min  | Deadlock detection                                   |
| TGNT-P4.5  | Deadlock auto-resolution                                     | 2026-02-18   | ~3min  | Abort youngest waiter                                |
| TGNT-P4.6  | Fair share tracking                                          | 2026-02-18   | ~5min  | 50% decay smoothing                                  |
| TGNT-P5.1  | Interactive TUI dashboard                                    | 2026-02-18   | ~10min | cache/queue/intent/fair share                        |
| TGNT-P5.2  | Self-tuning report                                           | 2026-02-18   | ~8min  | Detect low hit rate/contention                       |
| TGNT-P5.3  | Auto-fix recommendations                                     | 2026-02-18   | ~5min  | Color-coded severity                                 |
| TGNT-P5.4  | Rules suggestion engine                                      | 2026-02-18   | ~5min  | From observed patterns                               |
| TGNT-P5.5  | L1 vs L2 benchmark                                           | 2026-02-18   | ~3min  | Perf comparison tool                                 |
| SCLI-P0.1  | Mission & hard problems                                      | 2026-02-15   | ~5min  | System analysis                                      |
| SCLI-P0.2  | Architecture diagram                                         | 2026-02-15   | ~8min  | Component overview                                   |
| SCLI-P0.3  | Configuration schema                                         | 2026-02-15   | ~5min  | rules.conf, agents.conf, env vars                    |
| SCLI-P0.4  | Risk register                                                | 2026-02-15   | ~8min  | Mitigations                                          |
| SCLI-P0.5  | Tech stack justification                                     | 2026-02-15   | ~5min  | Bash, Rust, C rationale                              |
| SCLI-P5.1  | Mergiraf integration (AST-aware merge for 10+ languages)     | 2026-02-22   | ~10min | merge_ast_aware in mesh/merge.py                     |
| SCLI-P5.2  | Conflict prediction before commit (trial merge from intents) | 2026-02-22   | ~8min  | predict_conflicts in mesh/merge.py                   |
| SCLI-P5.3  | Import union auto-resolution (Python/JS imports)             | 2026-02-22   | ~5min  | resolve_imports in mesh/merge.py                     |
| SCLI-P5.4  | JSON/YAML structural merge (deep merge via jq)               | 2026-02-22   | ~5min  | merge_structural in mesh/merge.py                    |
| SCLI-P6.1  | Optimistic concurrency control (OCC) version tracking        | 2026-02-22   | ~8min  | OptimisticConcurrencyControl in mesh/coordination.py |
| TGNT-P7.1  | Mergiraf integration                                         | 2026-02-19   | ~10min | AST merge for 10+ languages                          |
| TGNT-P7.2  | Conflict prediction from intents                             | 2026-02-19   | ~8min  | Trial merge before commit                            |
| TGNT-P7.3  | Import union auto-resolve                                    | 2026-02-19   | ~5min  | Python/JS sorted union                               |
| TGNT-P7.4  | JSON/YAML structural merge                                   | 2026-02-19   | ~5min  | Deep merge via jq, ours-wins                         |
| TGNT-P8.1  | OCC version check on write                                   | 2026-02-19   | ~8min  | Record version at claim, verify before commit        |
| TGNT-P8.2  | HLC timestamp generation                                     | 2026-02-19   | ~5min  | Millisecond physical + logical counter               |
| TGNT-P8.3  | Lease-based file claims registry                             | 2026-02-19   | ~8min  | read/write/exclusive with flock                      |
| TGNT-P8.4  | Lease renewal and expiry                                     | 2026-02-19   | ~5min  | Background cleanup daemon                            |
| TGNT-P9.1  | Singleflight dedup pattern                                   | 2026-02-19   | ~5min  | First executes, rest wait                            |
| TGNT-P9.2  | inotify cache invalidation                                   | 2026-02-19   | ~8min  | Watch file changes, invalidate                       |
| TGNT-P9.3  | Heat-based LRU eviction                                      | 2026-02-19   | ~5min  | Access frequency + exponential decay                 |
| TGNT-P10.1 | Per-agent TMPDIR allocation                                  | 2026-02-19   | ~3min  | Private temp, cleanup on exit                        |
| TGNT-P10.2 | Dynamic port range allocation                                | 2026-02-19   | ~5min  | Registry + liveness check                            |
| TGNT-P10.3 | Environment variable isolation                               | 2026-02-19   | ~5min  | Agent-specific env file                              |
| TGNT-P12.1 | /proc scanner with agent patterns                            | 2026-02-19   | ~8min  | Claude/Aider/Cursor/Cline detection                  |
| TGNT-P12.2 | Agent manifest creation                                      | 2026-02-19   | ~5min  | YAML: id, type, pid, capabilities                    |
| TGNT-P12.3 | Heartbeat monitor                                            | 2026-02-19   | ~5min  | Touch-file every 5s, 15s threshold                   |
| TGNT-P12.4 | Stale agent cleanup                                          | 2026-02-19   | ~3min  | Reclaim tasks, archive manifest                      |
| TGNT-P13.1 | tmux session detection                                       | 2026-02-19   | ~5min  | mesh-{agent-uuid} naming                             |
| TGNT-P13.2 | Command injection via tmux                                   | 2026-02-19   | ~8min  | send-keys + 1.5s delay                               |
| TGNT-P13.3 | Agent readiness detection                                    | 2026-02-19   | ~5min  | Prompt patterns, busy/idle/error                     |
| TGNT-P15.1 | Optional worktree creation                                   | 2026-02-19   | ~8min  | git worktree add .mesh/worktrees/agent-{uuid}        |
| TGNT-P15.2 | Branch coordination                                          | 2026-02-19   | ~5min  | Registry, collision avoidance, status tracking       |
| TGNT-P15.3 | Worktree cleanup                                             | 2026-02-19   | ~3min  | Orphan detection, 30s grace, health monitor          |

---

## Notes

- **Total Pending Tasks**: 89 items across both projects
- **Completed Tasks**: 46 items (Phases 0-5 for thegent, Phases 0 for sharecli)
- **Effort Distribution**: Mix of ~3-20 minute tasks, primarily feature and infrastructure work
- **Dependency Strategy**: Sequential foundation (P0-P1), parallel optimization (P2-P5), then specialized tracks (P6-P18)
- **Next Steps**: Begin Phase 6 (Git Parallelism) for thegent; Phase 1 (Process Detection) for sharecli
- **Agents**: Coordinate via this file; claim items in CLAIMED section before starting

---

## Claiming Work

1. **Before starting**: Add your item to CLAIMED with agent name and current timestamp
2. **Upon completion**: Move from CLAIMED to COMPLETED with completion timestamp and notes
3. **If blocked**: Update status to BLOCKED and note the blocking dependency
4. **For coordination**: Read PENDING and CLAIMED to avoid duplicates; check "Depends On" column for prerequisites

---

**Last Updated**: 2026-02-22 | **Format Version**: 1.0
