# Session Scratch Board & Optimization Plan

> **Status:** Aligned with [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md). Tool shims consolidated → **thegent-shims** (Rust), not ultra-shim (Go).
> **Sprawl:** [RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md](../research/RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md)

---

## Current objectives

- [x] Resolve `rg -E` encoding conflict error
- [x] Fix slow `grep -r` performance (flag collision with `ripgrep -r`)
- [x] Optimize `git` and `find` via high-performance shims (`gix`, `fd`)
- [x] Enhance `thegent doctor` with Provider Success Matrix & Headless Runs
- [ ] Implement proactive `doctor --fix` for detected environment issues
- [ ] **Consolidate tool acceleration → thegent-shims (Rust)** — _was_ "unified Go ultra-shim"; see [FULL_SHELL_TO_RUST](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) Phase 0–2 (thegent-shims for git, grep, find, agent)

---

## Issues identified

| Issue               | Impact             | Status      | Fix / mitigation                                                                               |
| ------------------- | ------------------ | ----------- | ---------------------------------------------------------------------------------------------- |
| `grep -r` collision | 5m+ search times   | Done        | grep-wrapper.sh / install shim strip `-r` for rg; **target:** thegent-shims find/grep          |
| `rg -E` conflict    | CLI noise / errors | Done        | grep-wrapper.sh + install shim strip `-E`; **target:** thegent-shims                           |
| Multi-bin overhead  | Slow startup       | In progress | **thegent-shims** (Rust) single binary for git, grep, find, agent — Phase 2 FULL_SHELL_TO_RUST |
| Provider drift      | Unclear health     | Done        | `thegent doctor` provider success matrix                                                       |

---

## Speed & conciseness (aligned with plans)

| Goal                    | Current / plan                                                                                                                                                                                                                                                                   |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Unified shims**       | Shell wrappers in hooks/lib; install.py generates bash shims. **Target:** [FULL_SHELL_TO_RUST](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) Phase 2: **thegent-shims** (Rust) for git, grep, find, codex/copilot/dex/claude/cursor. Replaces ultra-shim (Go) and bash shims. |
| **Proactive health**    | Expand `thegent doctor` to check shim versions and binary availability.                                                                                                                                                                                                          |
| **Headless preflights** | Ensure `clode` and `dex` are ready before long tasks.                                                                                                                                                                                                                            |
| **MCP acceleration**    | Expose gix/fd/rg via MCP to bypass CLI/shell; optional after thegent-hooks/thegent-shims.                                                                                                                                                                                        |

---

## Best practices & agent UX

1. **Zero-overhead shims:** Prefer Rust (thegent-shims). Bash subshell ~20–50 ms/call; Rust single binary avoids that. See [RUST_GO_MIGRATION_PLAN](../migration/RUST_GO_MIGRATION_PLAN.md), [COMPREHENSIVE_PERFORMANCE_ANALYSIS](../migration/COMPREHENSIVE_PERFORMANCE_ANALYSIS.md).
2. **Context-aware diagnostics:** `thegent doctor` should check "Does it work?" (e.g. 1-token test prompt), not only "Is it installed?".
3. **Safe path resolution:** Shims must resolve real binary from a PATH that excludes the shim dir to avoid recursion. See install.py agent accelerators and [FULL_SHELL_TO_RUST](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) §2.4.
4. **Intelligent fallbacks:** If gix fails, fall back to git transparently so the agent never stalls.

---

## BACKLOG items (for WORK_STREAM)

| ID                        | Title                                                                         | Source                                 | Priority |
| ------------------------- | ----------------------------------------------------------------------------- | -------------------------------------- | -------- |
| scratch-doctor-fix        | Implement proactive `doctor --fix` for detected issues                        | scratchpad/session_review.md           | P2       |
| scratch-thegent-shims     | Ship thegent-shims (Rust) for git/grep/find/agent; Phase 2 FULL_SHELL_TO_RUST | FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md | P1       |
| scratch-doctor-shim-check | thegent doctor: check shim version and binary availability                    | scratchpad/session_review.md           | P2       |

---

## Deprecated / superseded

- **ultra-shim (Go):** Superseded by **thegent-shims (Rust)**. See [FULL_SHELL_TO_RUST](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md), [ULTRA_SHIM_FORK_FAILURE_FIX](../plans/ULTRA_SHIM_FORK_FAILURE_FIX.md). Do not add new work to ultra-shim.

---

## Ongoing snippets

- _2026-02-16:_ Optimized `find` to handle glob patterns in install shim; validated 7 providers in doctor.
- _2026-02-17:_ Scratchpad aligned with FULL_SHELL_TO_RUST; BACKLOG items added; ultra-shim marked superseded by thegent-shims.

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
