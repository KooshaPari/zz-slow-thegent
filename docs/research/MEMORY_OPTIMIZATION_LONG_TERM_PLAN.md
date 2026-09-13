<DONE>
# Memory Optimization — Long-Term Plan

> **Purpose**: Long-term optimizations for memory issues in multi-agent, multi-session local swarms.
> **Status**: Plan | **Date**: 2026-02-16
> **Context**: Investigation found redundant Node tooling (LSP triplet per session), cc-status bloat, and Spotlight thrashing.

---

## 1. Investigation Findings (Summary)

| Finding                 | Root Cause                                                                                              | Impact                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| **Redundant tooling**   | Each active agent session (Claude Code, Cursor) spawns its own triplet: LSP + Type Checker + MCP runner | 11 sessions → 20+ Node procs → 1–2 GB each    |
| **cc-status bloat**     | Multiple cc-status instances (Claude Code internals) with high RSS                                      | Significant memory contribution               |
| **Spotlight thrashing** | mds_stores indexes high-I/O dirs: ~/.thegent, .claude, node_modules                                     | CPU spikes, memory pressure                   |
| **Per-CC full stack**   | Each Claude Code (cc) process spawns its own full LSP/tool stack; closing tab terminates all            | Multi-project × multi-tenant = N× duplication |

### 1.1 Per-CC Process Stack (Tab Close = All Die)

**Observed processes per Claude Code instance** (closing tab terminates):

| Process            | Role                   |
| ------------------ | ---------------------- |
| python, python3.12 | Python runtime         |
| claude             | Agent                  |
| clangd             | C/C++ LSP              |
| caffeinate         | macOS keep-awake       |
| gopls (×2)         | Go LSP                 |
| uv                 | Python package manager |
| sourcekit-lsp      | Swift LSP              |
| rust-analyzer      | Rust LSP               |

**Multi-project, multi-tenant**: Each project/tenant with an open CC tab = full stack. 5 projects × 2 tenants = 10× clangd, 10× gopls, etc. Process count scales linearly with (projects × tenants × IDE instances).

---

## 2. Long-Term Optimization Roadmap

### 2.1 Redundant Tooling (LSP Triplet per Session)

**Goal**: Reduce per-session Node process count from ~3 to near-zero for shared services.

| Optimization                   | Description                                                                | Effort           | Impact                        |
| ------------------------------ | -------------------------------------------------------------------------- | ---------------- | ----------------------------- |
| **LSP multiplexing (MTSP-04)** | Single persistent Serena daemon for all sessions; no per-session LSP spawn | 15–25 tool calls | High — eliminates N×LSP       |
| **Uni-mount MCP**              | Single thegent URL; no duplicate Playwright/Upstash/context7 per session   | Done             | Medium — reduces MCP count    |
| **Session cap + warning**      | Warn when sessions > 5; suggest prune; optional hard cap                   | 2–3 tool calls   | Medium — prevents runaway     |
| **Type checker sharing**       | Single tsserver/pyright for workspace; IDE extension config                | IDE-dependent    | High — research needed        |
| **Process group + SIGHUP**     | Spawn LSPs in same process group; parent exit sends SIGHUP                 | IDE change       | High — requires Cursor/Claude |

**Priority**: LSP multiplexing (MTSP-04) and session cap are highest leverage. Type checker sharing is IDE-specific.

---

### 2.2 cc-status Bloat

**Goal**: Reduce cc-status memory footprint and instance count.

| Optimization                     | Description                                                  | Effort          | Impact  |
| -------------------------------- | ------------------------------------------------------------ | --------------- | ------- |
| **cc-status in prune patterns**  | Already in prune; ensure aggressive when threshold low       | Done            | —       |
| **cc-status-specific threshold** | Lower threshold for cc-status-only prune (e.g. >3 instances) | 4–6 tool calls  | Medium  |
| **Memory-based prune trigger**   | Prune when `mem_available_mb < 512` regardless of count      | 6–8 tool calls  | High    |
| **RSS-aware prune**              | Prefer killing highest-RSS cc-status first                   | 8–12 tool calls | Medium  |
| **Upstream feedback**            | Report to Claude Code team; may be fixable in product        | External        | Unknown |

**Priority**: Memory-based prune trigger (needs macOS vm_stat fix first). cc-status-specific logic as follow-up.

---

### 2.3 Spotlight Thrashing

**Goal**: Prevent mds_stores from indexing heavy dev dirs.

| Optimization                   | Description                                                                 | Effort         | Impact |
| ------------------------------ | --------------------------------------------------------------------------- | -------------- | ------ |
| **spotlight-exclude command**  | `thegent mcp spotlight-exclude` — exclude ~/.thegent, .claude, node_modules | Done           | High   |
| **Spotlight exclude in setup** | Run `thegent mcp spotlight-exclude` during `task setup`                     | 1–2 tool calls | High   |
| **Auto-exclude on first run**  | SessionStart hook: if dirs not excluded, run once                           | 4–6 tool calls | Medium |
| **.noindex in templates**      | Add .noindex to .gitignore for new projects; create in .thegent             | 2–3 tool calls | Low    |
| **mdutil -E for volume**       | Full reindex after exclude (optional; user-initiated)                       | Doc only       | Low    |

**Priority**: Add to `task setup` immediately. Auto-exclude on first run as Phase 2.

---

## 3. Phased Implementation

### Phase 1: Immediate (This Week)

| Task                                                | Owner   | Status |
| --------------------------------------------------- | ------- | ------ |
| Spotlight exclude in `task setup`                   | thegent | ✓ Done |
| Session-start warning (>5 sessions → suggest prune) | thegent | ✓ Done |
| Document findings in SWARM_PROCESS_OPTIMIZATIONS    | thegent | ✓ Done |

### Phase 2: Structural (Next 2–4 Weeks)

| Task                                         | Owner   | Status |
| -------------------------------------------- | ------- | ------ |
| macOS vm_stat in load_based_limits           | thegent | ✓ Done |
| Memory-based prune trigger                   | thegent | ✓ Done |
| cc-status-specific prune (lower threshold)   | thegent | ✓ Done |
| Auto spotlight-exclude on first SessionStart | thegent | ✓ Done |

### Phase 3: MTSP (1–2 Months)

| Task                                    | Owner   | Status  |
| --------------------------------------- | ------- | ------- |
| LSP multiplexing (MTSP-04)              | thegent | Pending |
| Periodic prune daemon (launchd/systemd) | thegent | ✓ Done  |
| Orphan-by-ppid (smarter prune)          | thegent | ✓ Done  |

### Phase 4: Ecosystem (Ongoing)

| Task                          | Owner         | Status   |
| ----------------------------- | ------------- | -------- |
| Type checker sharing research | Research      | Pending  |
| Process group / SIGHUP (IDE)  | Cursor/Claude | External |
| cc-status upstream feedback   | Community     | External |

---

## 4. Configuration Additions

```yaml
# Memory optimization (add to config / .env)
THGENT_AUTO_PRUNE=1
THGENT_AUTO_PRUNE_THRESHOLD=12          # Orphan count; lower for cc-status-heavy
THGENT_AUTO_PRUNE_COOLDOWN=300
THGENT_AUTO_PRUNE_MEMORY_THRESHOLD_MB=512  # Future: prune when avail < this
THGENT_SESSION_WARN_THRESHOLD=5         # Warn on run if sessions > this
THGENT_SPOTLIGHT_EXCLUDE_ON_SETUP=1     # Run spotlight-exclude during setup
```

---

## 5. Metrics & Verification

| Metric                       | Current (11 sessions)    | Target                     |
| ---------------------------- | ------------------------ | -------------------------- |
| Node process count           | 20+                      | < 10 (with MTSP)           |
| cc-status instances          | Multiple, high RSS       | 0–1 per active Claude Code |
| mds_stores CPU               | Spikes during agent runs | Minimal (excluded dirs)    |
| Total memory (agent-related) | 10–20+ GB                | < 6 GB                     |

---

## 6. Cross-References

| Doc                                                                                   | Relevance                        |
| ------------------------------------------------------------------------------------- | -------------------------------- |
| [SWARM_PROCESS_OPTIMIZATIONS](../reference/SWARM_PROCESS_OPTIMIZATIONS.md)            | User-facing quick reference      |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md) | Full research, triggers, roadmap |
| [PROCESS_OPTIMIZATION_PLAN](../plans/PROCESS_OPTIMIZATION_PLAN.md)                    | MTSP, tool migration             |

---

## 7. Implementation Roadmap

### 7.1 Detailed Phase Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEMORY OPTIMIZATION IMPLEMENTATION ROADMAP                  │
└─────────────────────────────────────────────────────────────────────────────┘

    PHASE 1: IMMEDIATE (Week 1-2)
    ═══════════════════════════════
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Task                              │ Status    │ Effort    │ Impact  │
    ├───────────────────────────────────┼───────────┼───────────┼─────────┤
    │ Spotlight exclude in task setup   │ ✓ Done   │ 1-2      │ High    │
    │ Session-start warning (>5)        │ ✓ Done   │ 2-3      │ Medium  │
    │ Document findings                 │ ✓ Done   │ 1-2      │ High    │
    └─────────────────────────────────────────────────────────────────────┘

    PHASE 2: STRUCTURAL (Week 3-6)
    ═════════════════════════════════
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Task                              │ Status    │ Effort    │ Impact  │
    ├───────────────────────────────────┼───────────┼───────────┼─────────┤
    │ macOS vm_stat sampling            │ ✓ Done   │ 4-6      │ High    │
    │ Memory-based prune trigger        │ ✓ Done   │ 6-8      │ High    │
    │ cc-status-specific prune          │ ✓ Done   │ 4-6      │ Medium  │
    │ Auto spotlight-exclude hook       │ ✓ Done   │ 4-6      │ Medium  │
    └─────────────────────────────────────────────────────────────────────┘

    PHASE 3: MTSP (Month 1-2)
    ════════════════════════════════════
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Task                              │ Status    │ Effort    │ Impact  │
    ├───────────────────────────────────┼───────────┼───────────┼─────────┤
    │ LSP multiplexing (MTSP-04)       │ Pending   │ 15-25    │ High    │
    │ Periodic prune daemon             │ ✓ Done   │ 10-15    │ Medium  │
    │ Orphan-by-ppid smarter prune      │ ✓ Done   │ 8-12     │ High    │
    │ Per-project session dir           │ Pending   │ 6-10     │ Medium  │
    └─────────────────────────────────────────────────────────────────────┘

    PHASE 4: ECOSYSTEM (Ongoing)
    ════════════════════════════════════
    ┌─────────────────────────────────────────────────────────────────────┐
    │ Task                              │ Owner     │ Status    │ Notes  │
    ├───────────────────────────────────┼───────────┼───────────┼─────────┤
    │ Type checker sharing research     │ Research  │ Pending   │ IDE    │
    │ Process group / SIGHUP           │ Cursor/CC │ External  │ IDE    │
    │ cc-status upstream feedback       │ Community │ External  │ App    │
    └─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Milestone Timeline

```
    Week 1     Week 2     Week 4     Week 6     Month 1     Month 2
       │          │          │          │           │            │
       ▼          ▼          ▼          ▼           ▼            ▼
    ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────────┐  ┌─────────┐
    │ M1  │──►│ M2  │──►│ M3  │──►│ M4  │──►│   M5    │──►│   M6    │
    └─────┘   └─────┘   └─────┘   └─────┘   └─────────┘  └─────────┘
       │          │          │          │           │            │
       │          │          │          │           │            │
    Setup+    Memory-    Prune      MTSP       Type        Process
    Warning    based      daemon    design     checker      group
               trigger   (Phase2)   starts    research    (IDE)

    M1: Setup complete, documentation
    M2: Memory-based triggers active
    M3: Prune daemon running
    M4: Design review, MTSP-04 spec
    M5: Type checker sharing researched
    M6: IDE integration (external)
```

### 7.3 Resource Allocation

| Resource              | Phase 1 | Phase 2       | Phase 3          | Phase 4      |
| --------------------- | ------- | ------------- | ---------------- | ------------ |
| Developer hours       | 10-15   | 25-35         | 50-70            | 20-30        |
| Testing effort        | Low     | Medium        | High             | Medium       |
| External dependencies | None    | macOS vm_stat | IDE (Cursor/CC)  | Type checker |
| Infrastructure        | None    | None          | Redis (optional) | None         |

### 7.4 Success Criteria

| Metric                  | Baseline | Phase 2 Target | Phase 3 Target |
| ----------------------- | -------- | -------------- | -------------- |
| Node process count      | 20+      | 15             | < 10           |
| cc-status memory        | High RSS | Moderate       | Minimal        |
| Memory available (idle) | < 4 GB   | > 6 GB         | > 8 GB         |
| Prune accuracy          | 80%      | 90%            | 95%            |

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Implementation roadmap (§7)

| Section | Added Content                                                                |
| ------- | ---------------------------------------------------------------------------- |
| §7.1    | Detailed Phase Breakdown table with tasks, status, effort, impact            |
| §7.2    | Milestone Timeline (M1-M6 with dates and deliverables)                       |
| §7.3    | Resource Allocation (developer hours, testing, dependencies, infrastructure) |
| §7.4    | Success Criteria (baseline vs targets for key metrics)                       |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SWARM_COMPLETE.md](./SWARM_COMPLETE.md) - Swarm guide
- [SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md](./SYSTEM_RESOURCES_FD_CPU_DEEP_RESEARCH.md) - System resources
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
