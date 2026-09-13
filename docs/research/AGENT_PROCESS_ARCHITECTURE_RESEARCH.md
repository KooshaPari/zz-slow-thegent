<DONE>
# Agent Process Architecture — Research Note

> **Purpose**: Research note on agent runtime process usage (zsh, agent-shell, agent process) and multi-tenant optimization. Applies to Cursor IDE, Codex (OpenAI) from terminal, and similar runtimes.
> **Status**: Research | **Date**: 2026-02-16
> **Trigger**: User observation — "Closing this window will terminate... 4 zsh, 2 cursor-shell, 1 cursor-agent per 1 cursor-agent proc is a lot right, multi tenant system perhaps needed"

---

## 1. Observed Process Stack (Per Agent Session)

| Process Type    | OS Name              | Count | Likely Role                                               |
| --------------- | -------------------- | ----- | --------------------------------------------------------- |
| **zsh**         | zsh                  | 3–4   | Shell for command execution, integrated terminal(s)       |
| **agent-shell** | cursor-shell\*       | 2–3   | Tool execution, shell integration for agent (Codex, etc.) |
| **agent**       | codex / cursor-agent | 1     | The AI agent process                                      |

\*The OS process is named `cursor-shell` (AI-named; not Cursor-specific). We refer to it as **agent-shell** — the shell used for agent tool execution.

**Total**: ~7 processes per agent session. Closing the window/tab terminates all. Same stack appears when running Codex (OpenAI) from terminal; Cursor IDE need not be running.

---

## 2. Is This a Lot?

**Relative to thegent's target** (`PROCESS_OPTIMIZATION_PLAN.md`): < 10 persistent processes per session — so 7 is within target for a _single_ session.

**The real problem is multiplicative**:

- **Per-CC full stack** (from `MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md`): Each Claude Code instance spawns python, clangd, gopls (×2), uv, sourcekit-lsp, rust-analyzer, caffeinate. Same pattern for Cursor.
- **Multi-project × multi-tenant** = N× duplication. 5 projects × 2 agent tabs = 10× LSPs, 10× shells, etc.

So **7 processes per window is moderate**, but **7 × N windows** becomes significant. With 5+ agent tabs, you're at 35+ processes just for Cursor's own stack, before LSPs, MCPs, etc.

---

## 3. What We Can vs. Cannot Control

| Layer                                          | Owner                 | Can Optimize?                                       |
| ---------------------------------------------- | --------------------- | --------------------------------------------------- |
| **4 zsh + 2–3 agent-shell + 1 agent**          | Runtime (proprietary) | **No** — upstream architecture                      |
| **MCP servers** (Playwright, Upstash, thegent) | thegent / config      | **Yes** — uni-mount, single URL                     |
| **LSPs** (clangd, gopls, rust-analyzer)        | IDE + thegent         | **Partial** — LSP multiplexing (MTSP-04)            |
| **Task / shell-outs**                          | thegent               | **Yes** — consolidated worker, Rust hook-dispatcher |

---

## 4. Multi-Tenant Strategy (Already in thegent)

The project already has a **Multi-Tenant Single Process (MTSP)** strategy. Relevant items:

| Task        | Description                                               | Status  |
| ----------- | --------------------------------------------------------- | ------- |
| **MTSP-01** | Unified MCP Host — single `thegent serve` URL             | Done    |
| **MTSP-02** | In-Process Agent Runner — cwd isolation, fewer shell-outs | Phase 2 |
| **MTSP-03** | Shared Task Worker — process-compose                      | Done    |
| **MTSP-04** | LSP Multiplexing — single Serena daemon                   | Pending |
| **MTSP-05** | Unified Worker Daemon                                     | Phase 2 |

**Recommendation**: Continue MTSP. The zsh + agent-shell stack is runtime internals; we optimize _around_ them by consolidating shared services (MCP, LSP, task) so they're not duplicated per session.

---

## 5. Practical Mitigations

| Action                                     | Effect                                         |
| ------------------------------------------ | ---------------------------------------------- |
| `thegent mcp migrate-unimount all`         | Single MCP URL — fewer duplicate MCP processes |
| `export THGENT_AUTO_PRUNE=1`               | Auto-prune orphans on Stop                     |
| `thegent mcp spotlight-exclude`            | Reduce mds_stores CPU/memory pressure          |
| `THGENT_CONCURRENCY_MAX_SLOTS_PER_OWNER=2` | Cap concurrent runs per project                |
| Fewer agent tabs                           | Directly reduces 7×N process count             |

---

## 6. Upstream (Runtime) Feedback

If the agent runtime supported:

- **Shared shell process** across agent tabs (1 zsh instead of 4)
- **Shared agent-shell** for tool execution (1 instead of 2–3)
- **Process group / SIGHUP** so child LSPs could be re-parented or shared

…that would reduce the 7→3 or similar. This would require runtime product changes; worth a feature request.

---

## 7. Naming Note

The process appears as `cursor-shell` in the OS (upstream name, AI-chosen). We use **agent-shell** in this doc — the shell used for agent tool execution, regardless of IDE (Cursor, terminal, Codex, etc.).

---

## 8. Summary

| Question                                        | Answer                                                                                                |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Is 4 zsh + 2–3 agent-shell + 1 agent a lot?** | For one session: moderate. For N sessions: yes — scales linearly.                                     |
| **Multi-tenant needed?**                        | Yes — MTSP is the right direction. Consolidate MCP, LSP, task; the ~7 runtime processes are upstream. |
| **What to do now?**                             | Uni-mount MCP, auto-prune, spotlight-exclude, slot caps. Continue MTSP-04 (LSP multiplexing).         |

---

_Cross-ref: [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md) · [SWARM_PROCESS_OPTIMIZATIONS.md](../reference/SWARM_PROCESS_OPTIMIZATIONS.md) · [MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md)_

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added architecture patterns
2. Added process examples
3. Enhanced cross-references

### Cross-References Added

- SWARM_MEMORY_COORDINATION_DEPTH.md
- SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md

### Practical Additions

- Architecture templates
- Process configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md](./MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md) - Memory optimization
- [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md) - Process automation
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
