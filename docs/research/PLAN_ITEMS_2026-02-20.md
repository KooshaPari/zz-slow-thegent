<DONE>
# Plan Items -- 2026-02-20
> Derived from holistic research synthesis across all agent sessions (Claude Code, Codex, Factory Droid, Cursor)
> Sources: 893 Claude sessions, 5,901 Codex threads, 1,000 Droid entries, 2,983 Cursor messages, 200+ docs

---

## CRITICAL (Blocking / Broken Today)

### PI-001: Fix Codex CLI Proxy 0.104.0 Breakage

- **Source**: Team-lead escalation (2026-02-20), Codex proxy threads, CLIProxyAPI++ fork
- **Description**: Codex 0.104.0 broke the CLI proxy integration today. This blocks Codex-based agent dispatch which represents 89% of automated work (5,240 of 5,901 threads are thegent-dispatched Codex workers). Investigate breaking changes in 0.104.0. Fix `src/thegent/cliproxy_adapter.py` and related proxy routing code. If upstream is unfixable, pin to 0.103.x and document.
- **Depends on**: None
- **Effort**: S-M (diagnosis may be quick, fix depends on root cause)
- **Research needed**: Y -- diff 0.103.x vs 0.104.0 breaking changes

### PI-002: Agent Pruning UX Fix (Stops Killing Active Sessions)

- **Source**: Droid sessions (repeated user complaints), Cursor transcripts, Claude CRITICAL SECURITY RULE
- **Description**: The pruning system is consistently killing active agent sessions and terminal processes without user consent. This is the highest-friction bug across all sessions. Audit ALL prune code paths (not just SmartPruner). Ensure Triple-Lock Criteria (Idle >60s + Complete regex + Docs Written mtime audit) applies universally. Implement user prompt (AppleScript on macOS) before any process termination. Add `--dry-run` as default for all prune operations. Verify the CRITICAL SECURITY RULE (agents must NEVER kill other agent processes) is enforced in code, not just documentation.
- **Depends on**: None
- **Effort**: M
- **Research needed**: N (SmartPruner exists, need code path audit)

### PI-003: Fix WORK_STREAM.md Stale State

- **Source**: Cross-source analysis (wbs-agent confirmed wp-71001-71005 done with 80 tests, WORK_STREAM shows BACKLOG)
- **Description**: WORK_STREAM.md is the single source of truth for all agents. It currently shows stale state: wp-71001 through wp-71005 are in BACKLOG but confirmed implemented. CLAIMED section has unevaluated `$(date)` template syntax from 2026-02-17/18. Fix: move wp-71001-71005 to COMPLETED, clean CLAIMED timestamps, verify no other stale items.
- **Depends on**: None
- **Effort**: S
- **Research needed**: N

### PI-004: Stop Hooks Optimization (<15s Target)

- **Source**: Claude sessions (quality-gate.sh timeout errors), Cursor transcripts
- **Description**: Stop hooks are timing out: quality-gate.sh hits 5s idle timeout and 15s absolute timeout. User target is <15s total, ideally <1s per hook. Immediate fix: optimize quality-gate.sh to complete within 5s (reduce scope, parallelize checks, cache results). Longer-term: complete Rust hook migration which benchmarks at <1ms per hook. Fix hook dispatcher to handle timeouts gracefully without STOP error codes.
- **Depends on**: None
- **Effort**: M
- **Research needed**: N (performance bottlenecks in quality-gate.sh need profiling)

---

## HIGH (Major Architectural / Blocking Soon)

### PI-005: Agent Load Management and Auto-Throttling

- **Source**: Claude session 2026-02-19 (290 load avg incident), Droid session (agent explosion)
- **Description**: System hit 290 load average from autonomous agent loop + high concurrency. AutoLaunchSystem needs: global lock to prevent agent storms, capacity thresholds (warn >20, throttle >50, hard stop >80), integration with ConcurrencyController per-gate logging, load-based backoff in `thegent plan loop`. This directly affects the 300-agent scalability target.
- **Depends on**: None
- **Effort**: M
- **Research needed**: Y -- benchmark at 10/50/100/200 agents

### PI-006: Complete Harness Migration to 3 Rust Bins

- **Source**: Codex threads (shim-install-links, guard-shim-forks, runtime-dispatch), Droid sessions
- **Description**: Finalize dex/clode/roid Rust shim architecture. Complete install-links subcommand in thegent-shims. Port guard-shim-forks.sh to Rust. Audit and remove ALL remaining bash wrapper generation from install.sh, bootstrap.sh, install-thegent-shims.sh. Verify end-to-end: `thegent install` -> symlinks -> dex/clode/roid dispatch via argv[0]. This unblocks CI/CD, release pipeline, and shell elimination.
- **Depends on**: None
- **Effort**: M
- **Research needed**: N (design complete)

### PI-007: Rust Hooks Phase 1 Completion

- **Source**: docs-scraper (HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS), Claude dumps
- **Description**: Currently 67% complete. Fix type annotation issues in hooks/hook-dispatcher/src/main.rs blocking compilation. Complete quality-gate binary and security-pipeline binary. Run integration tests to verify Rust hooks match Bash behavior. Benchmark: target <1ms per hook. This directly feeds PI-004 (stop hooks optimization).
- **Depends on**: None
- **Effort**: M
- **Research needed**: N

### PI-008: OCC Violation Resolution

- **Source**: Codex OCC investigation threads, docs-scraper dumps
- **Description**: `thegent plan claim` and `thegent plan complete` warn OCC violation for WORK_STREAM.md but still succeed. Root cause found (timestamp comparison issue) but patch may not be applied. Fix: apply patch, verify claim/complete cycle under concurrent agent access (critical for 300-agent target), add integration test.
- **Depends on**: None
- **Effort**: S
- **Research needed**: N (root cause known)

### PI-009: CI/CD Unification and Release Pipeline

- **Source**: Codex CI/CD audit, docs-scraper (CLIPROXY_RELEASE audit), Droid sessions
- **Description**: Merge duplicate CI workflows (build.yml deleted, ci.yml exists, release.yml untracked). Establish required vs advisory gates. Create release pipeline: PyPI, GitHub Releases, prepackaged binaries, Homebrew formula. Wire into `thegent release` command. Multi-platform binary builds (macOS arm64/x86, Linux x86).
- **Depends on**: PI-006 (harness bins stable)
- **Effort**: L
- **Research needed**: Y -- GitHub Actions matrix for multi-platform Rust+Python builds

### PI-010: FastMCP 3.0 Full Migration

- **Source**: Droid research (FastMCP 3.0 released Feb 2026), docs-scraper
- **Description**: Code references both FastMCP 2.x and 3.0 patterns with no clear boundary. Audit all FastMCP usage. Migrate remaining 2.x to 3.0. Document breaking changes. Verify all MCP tools work under 3.0. This affects the MCP server which is the primary agent interface.
- **Depends on**: None
- **Effort**: M
- **Research needed**: Y -- identify all 2.x patterns, map 3.0 equivalents

### PI-011: Compositor Consolidation (4 -> 1)

- **Source**: All four scraper sources (4 implementations found)
- **Description**: Consolidate: src/thegent/ux/compositor.py (MVP), src/thegent/ui/compositor/ (Textual, canonical), src/thegent/tui/compositor.py, src/thegent/compositor/. Merge into single canonical Textual-based implementation at src/thegent/ui/compositor/. Redirect imports. Remove dead code. Preserve all tests (46+ across implementations).
- **Depends on**: None
- **Effort**: M
- **Research needed**: N

---

## MEDIUM (Polish / Optimization / Near-term)

### PI-012: Argparse -> Typer Migration (3 files)

- **Source**: Codex library modernization audit
- **Description**: Migrate remaining argparse CLI entrypoints to Typer: src/thegent/infra/worker_node.py, src/thegent/governance/triggers.py, src/thegent/adapters/acp_server.py. Library-first policy mandates Typer for all CLIs.
- **Depends on**: None
- **Effort**: S
- **Research needed**: N

### PI-013: Shell Script Elimination (Remaining)

- **Source**: Droid sessions ("no scripts where rust/zig/mojo/py can be used")
- **Description**: Audit and port remaining shell scripts: guard-shim-forks.sh (Rust -- in progress), install-thegent-shims.sh, scripts/bootstrap.sh, scripts/guard-shim-forks.sh, scripts/install-thegent-shims.sh, scripts/install.sh. Keep only a truly minimal POSIX bootstrapper for initial install.
- **Depends on**: PI-006 (harness Rust bins)
- **Effort**: M
- **Research needed**: N

### PI-014: ZMX C ABI Status Verification

- **Source**: Droid session 56a6a42f (marked PENDING), Codex (marked DONE), docs-scraper (ambiguous)
- **Description**: impl-zmx-c-abi status is contradictory across sources. Rust wrapper crate (crates/thegent-zmx) exists with tests. Verify: does the Zig-side C ABI exposure actually exist? Can Rust call zmx list/attach/capture via C FFI? If gaps exist, implement them. If complete, update all tracking docs to DONE.
- **Depends on**: None
- **Effort**: S
- **Research needed**: N (verification only)

### PI-015: Tray App Architecture Research

- **Source**: Droid sessions (extensive), Cursor transcripts
- **Description**: Write dedicated TRAY_APP_ARCHITECTURE_RESEARCH.md. Requirements: Ghostty-speed terminal rendering, claude krystal/splinter-like chat UI, per-project split, 300 agent monitoring dashboard, system tray integration (macOS + Linux + Windows). Evaluate: Tauri vs Electron vs native. Output: ADR + implementation plan.
- **Depends on**: None
- **Effort**: M (research only)
- **Research needed**: Y

### PI-016: Multi-Device Cluster Operationalization

- **Source**: Cursor sessions, docs-scraper (compute offload research)
- **Description**: Operationalize existing Tailscale/Syncthing infrastructure code. Set up M1 Mac <-> RTX 3090 desktop connection. Test agent dispatch to remote device. Resolve conflict strategy (LWW vs vector clocks). Configure Cloudflare tunnel for kooshapari.com domain mapping.
- **Depends on**: PI-005 (load management must work before distributing load)
- **Effort**: L
- **Research needed**: Y

### PI-017: E2E Test Strategy Execution

- **Source**: All sources (100% coverage target, actual coverage unclear)
- **Description**: Assess actual E2E coverage across thegent. Target: 100% unit, 100% integration, 100% E2E (agent-only project mandate). Identify untested paths. Write missing tests by priority. Set up coverage reporting in CI.
- **Depends on**: PI-009 (CI pipeline)
- **Effort**: L
- **Research needed**: N

### PI-018: Document R/W Protection System

- **Source**: Droid sessions ("backlog needs strict R/W protection... 200 types")
- **Description**: Design granular document R/W protection via MCP tools. Define document type taxonomy (200 types). Implement per-agent read/write permissions. Integrate with governance policy engine and FederatedPolicyEngine.
- **Depends on**: None
- **Effort**: L
- **Research needed**: Y

---

## LOW (Future / Research Needed)

### PI-019: Mojo Accelerator Integration (Polyglot Phase 3)

- **Source**: Droid sessions, docs-scraper (polyglot migration status)
- **Description**: Research Mojo API stability for production use. Identify acceleration targets (pure Python hot paths). Implement first Mojo accelerator module. Integrate with dual-runtime strategy.
- **Depends on**: PI-006 (stable build system)
- **Effort**: L
- **Research needed**: Y -- Mojo 2026 stability, integration patterns

### PI-020: WASM Isolation for L2 Agents (Polyglot Phase 4)

- **Source**: UNIFIED_MASTER_SPEC.md, docs-scraper
- **Description**: Evaluate WASM runtimes (wasmtime, wasmer, extism) for L2 agent sandboxing. POC with Zig-compiled WASM in sandbox. Define security boundaries.
- **Depends on**: PI-019
- **Effort**: L
- **Research needed**: Y

### PI-021: Dual Python Runtime (CPython 3.14 + PyPy)

- **Source**: Droid sessions (PyPy 30x faster pure Python, CPython 100x faster native extensions)
- **Description**: Design CPython+PyPy dual-runtime with process boundary and IPC. PyPy for orchestration logic; CPython for native extension paths. Define selective routing.
- **Depends on**: PI-019
- **Effort**: L
- **Research needed**: Y

### PI-022: Agent Permission Model Formalization

- **Source**: Cursor transcripts, docs-scraper (trust scoring discussed)
- **Description**: Formal agent permission model: trust levels, capability grants, escalation paths. Integrate with governance + FederatedPolicyEngine.
- **Depends on**: PI-018
- **Effort**: M
- **Research needed**: Y

### PI-023: Cross-Platform Testing (Linux/Windows)

- **Source**: All sources (only macOS path validated)
- **Description**: Set up Linux and Windows CI/test. Test agent deployment, harness installation, sandbox profiles, distributed compute on non-macOS. Fix platform-specific issues.
- **Depends on**: PI-009, PI-016
- **Effort**: L
- **Research needed**: Y

---

## Work Stream Items to Add

| ID     | Title                                        | Priority | Depends        |
| ------ | -------------------------------------------- | -------- | -------------- |
| pi-001 | Fix Codex CLI proxy 0.104.0 breakage         | CRITICAL | -              |
| pi-002 | Agent pruning UX fix (stop killing sessions) | CRITICAL | -              |
| pi-003 | Fix WORK_STREAM.md stale state               | CRITICAL | -              |
| pi-004 | Stop hooks optimization (<15s)               | CRITICAL | -              |
| pi-005 | Agent load management auto-throttling        | HIGH     | -              |
| pi-006 | Complete harness migration to 3 Rust bins    | HIGH     | -              |
| pi-007 | Rust hooks Phase 1 completion                | HIGH     | -              |
| pi-008 | OCC violation resolution                     | HIGH     | -              |
| pi-009 | CI/CD unification and release pipeline       | HIGH     | pi-006         |
| pi-010 | FastMCP 3.0 full migration                   | HIGH     | -              |
| pi-011 | Compositor consolidation (4 -> 1)            | HIGH     | -              |
| pi-012 | Argparse -> Typer migration (3 files)        | MEDIUM   | -              |
| pi-013 | Shell script elimination (remaining)         | MEDIUM   | pi-006         |
| pi-014 | ZMX C ABI status verification                | MEDIUM   | -              |
| pi-015 | Tray app architecture research               | MEDIUM   | -              |
| pi-016 | Multi-device cluster operationalization      | MEDIUM   | pi-005         |
| pi-017 | E2E test strategy execution                  | MEDIUM   | pi-009         |
| pi-018 | Document R/W protection system               | MEDIUM   | -              |
| pi-019 | Mojo accelerator integration (Phase 3)       | LOW      | pi-006         |
| pi-020 | WASM isolation for L2 agents (Phase 4)       | LOW      | pi-019         |
| pi-021 | Dual Python runtime (CPython + PyPy)         | LOW      | pi-019         |
| pi-022 | Agent permission model formalization         | LOW      | pi-018         |
| pi-023 | Cross-platform testing (Linux/Windows)       | LOW      | pi-009, pi-016 |

## Research Docs to Write

1. **CODEX_0104_PROXY_BREAKAGE_POSTMORTEM.md** -- Root cause, fix, prevention for proxy version breakage
2. **AGENT_CAPACITY_PLANNING.md** -- Benchmarks at 10/50/100/200/300 agents, throttling thresholds
3. **TRAY_APP_ARCHITECTURE_RESEARCH.md** -- Tauri/Electron/native comparison, 300-agent monitoring
4. **RELEASE_DISTRIBUTION_STRATEGY.md** -- PyPI, GitHub Releases, Homebrew, multi-platform builds
5. **STOP_HOOKS_PERFORMANCE_ANALYSIS.md** -- Per-hook timing breakdown, optimization targets
6. **WASM_SANDBOXING_RUNTIME_COMPARISON.md** -- wasmtime vs wasmer vs extism
7. **MOJO_INTEGRATION_FEASIBILITY.md** -- API stability, hot path targets
8. **AGENT_PERMISSION_MODEL.md** -- Trust levels, capability grants, escalation
9. **DUAL_PYTHON_RUNTIME_DESIGN.md** -- CPython+PyPy interop, IPC, selective routing
10. **COMPOSITOR_CONSOLIDATION_PLAN.md** -- Merge strategy for 4 implementations
11. **MULTI_DEVICE_CONFLICT_RESOLUTION.md** -- LWW vs vector clocks, Cloudflare tunnel
12. **CROSS_PLATFORM_DEPLOYMENT_TESTING.md** -- Linux/Windows test matrix, WSL2 patterns
