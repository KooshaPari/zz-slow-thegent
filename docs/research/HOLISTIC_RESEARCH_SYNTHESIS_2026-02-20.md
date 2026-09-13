<DONE>
# Holistic Research Synthesis -- 2026-02-20

> Compiled from: Claude Code (~/.claude), Codex (~/.codex), Factory Droid (~/.factory), Cursor (~/.cursor)
> Sessions covered: 2026-01-22 to 2026-02-20 (30 days)
> Total sources: 893 Claude sessions, 5,901 Codex threads, 1,000 Droid history entries, 2,983 Cursor messages, 200+ research/plan docs, 22 conversation dumps

## Executive Summary

The user has been building **thegent**, an agent orchestration and governance platform that functions as an MCP server, CLI tool, and multi-agent coordination system. Over the last 30 days, the project has progressed from a mid-stage agent framework to a nearly feature-complete platform with 90+ work items completed across domains including swarm scheduling, caching, FastMCP integration, ACP adapters, Rust-native hooks, ZMX session persistence, cross-platform automation, and multi-level governance.

The core themes across all sessions are: **(1)** eliminating legacy code / bash scripts in favor of a polyglot Rust+Python+Zig+Mojo stack, **(2)** scaling agent orchestration to 300+ concurrent agents on consumer hardware, **(3)** fail-fast, zero-fallback governance with strict quality gates, and **(4)** enterprise-grade DX/AX/UX polish with no user debt. The user operates with an aggressive, delegation-heavy workflow -- dispatching 5-30 agents in parallel batches and expecting autonomous completion of work stream items.

Current state: Phase 1-2 of the polyglot migration is complete (Python frontmatter, Rust core, Go proxy). The remaining work centers on Phase 3-4 (Mojo accelerators, Zig/WASM), harness consolidation (3 bins: dex/clode/roid), CI/CD unification, release hardening, versioning/shadow audit chain, and the final polish/QOL pass across 100+ items.

**URGENT (2026-02-20)**: Codex CLI proxy version 0.104.0 broke proxy integration today. This is a blocking issue for the primary agent dispatch pipeline.

## User Intent Patterns (from seed prompts)

### Theme 1: Polyglot Architecture Migration

- **Recurring ask**: "properly audit and plan correct polyglot architecture", "bash/py -> rust/go/zig migration", "no scripts where rust/zig/mojo/py can be used"
- **Related prompts**: "remove pnpm, npm, yarn for excl bun, pip for uv", "agents shouldn't have to use a separate cmd for git, git should be overhauled to gix", "move away from bash wrapper generation"
- **Current status**: Phase 1-2 complete (script migration, env vars, legacy deps, polyglot runtime). Phase 3 (Mojo) and Phase 4 (Zig/WASM) in progress. Harness migration to 3 Rust bins (dex/clode/roid) actively being implemented.

### Theme 2: Massive Scale Agent Orchestration

- **Recurring ask**: "scalability is most important aspect, target of 100 codex + 100 claude + 100 cursor instances", "do it in batches of 5-10 agents", "use subagents for each subtask, perhaps build a DAG for a team of <=5 agents"
- **Related prompts**: "use agents/teammates and delegate mode", "call 5-10 agents to work on the unified work stream", "always free agents for l3, haiku for l2, use teammate feature"
- **Current status**: Multi-agent dispatch working (batches of 30+ demonstrated). Swarm subsystem complete (redis concurrency, redlock, token bucket, DAG prioritization, critical lanes, priority queues). Load management still a concern -- system hit 290 load average on 2026-02-19 from agent storms.

### Theme 3: Zero-Debt Governance and Quality

- **Recurring ask**: "no fallbacks/legacy compatibility", "backwards compat isn't needed since we have no user debt", "fail fast, fail loudly", "always first ensure parity/migrations before removals"
- **Related prompts**: "backlog needs strict R/W protection, highly granular", "apply strict safeguarding, guardrails", "prevent agents from killing other agents"
- **Current status**: Governance rules codified in CLAUDE.md (~80k chars). Process kill protection implemented post-incident. Quality gates in hook pipeline. Library-first policy enforced. Zero suppression policy active.

### Theme 4: Enterprise-Grade DX/AX/UX Polish

- **Recurring ask**: "heavily optimize polish add robust/intuitive design minimal overhead/friction and maximal engineering", "QOL enhancements? more polishes? DX/AX/UX?", "enterprise-grade design feel even for personal projects"
- **Related prompts**: "I like the speed of ghostty, the UI/UX of claude krystal/splinter", "need spec and technical + user facing and ext dev facing walk through pages for every new feature", "walk me thru codebase atlas, QA matrix, PRD/technical PRD in extreme depth"
- **Current status**: 100-item Polish/Optimize/QOL plan created. TUI compositor Phase 1 complete. Ghostty terminal integration implemented. API docs auto-generation working. CLI examples generator created.

### Theme 5: Distributed Multi-Device Computing

- **Recurring ask**: "what happened to our distrib compute/device research (my desktop pc + laptop as client)", "m1/macOS; NVIDIA 3090ti, Ryzen 7 5800X W11 / WSL2"
- **Related prompts**: "setup-tailscale-nodes", "setup-syncthing-workspace", "Cloudflare tunneling via kooshapari.com"
- **Current status**: Tailscale node config and Syncthing workspace sync both implemented. RemoteExecutor in Python implemented. Actual multi-device cluster not yet operational -- infrastructure code exists but integration/testing pending.

### Theme 6: Agent Process Safety and Self-Healing

- **Recurring ask**: "are you killing agents???", "our pruning system is consistently killing all active sessions", "pruned ttys should receive a message explaining it, give user a prompt to approve/deny"
- **Related prompts**: "self heal / scale back up killed items", "prevent agents from being able to kill other agents", "why does it not work off correctly registering and mapping process trees"
- **Current status**: Critical security rule added (process kill forbidden). SmartPruner with Triple-Lock Criteria implemented. But fundamental pruning UX issues may persist -- user prompt before kill not yet fully implemented across all code paths.

### Theme 7: Stop Hooks Performance

- **Recurring ask**: "fix hook to a graceful end after 5-15s", "quality-gate.sh: idle timeout after 5s", "investigate too, we want to keep hook runs <15s always ideally <1s/0.5s"
- **Related prompts**: "Ran 3 stop hooks -- Stop hook error: Failed with non-blocking status code", "quality-gate.sh: absolute timeout after 15s"
- **Current status**: Stop hooks frequently timeout (quality-gate.sh hitting 5s idle timeout and 15s absolute timeout). Target is <15s total, ideally <1s per hook. Rust hook migration (67% complete) should reduce latency but compilation issues block progress.

### Theme 8: Codex CLI Proxy Integration (URGENT)

- **Recurring ask**: Codex 0.104.0 broke proxy integration on 2026-02-20. CLIProxy is the foundation for routing agent API calls through LiteLLM.
- **Related prompts**: "cliproxyapi++ should be the repo name", upstream PR preparation, "vibeproxy and cliproxyapi need better interop"
- **Current status**: BROKEN TODAY. Version 0.104.0 introduced breaking changes to the proxy pipeline. This blocks Codex-based agent dispatch which represents 89% of automated work (5,240 of 5,901 threads).

## Domain Map (what exists)

### Domain: Swarm / Orchestration

- **Research**: SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md
- **Implementation**: src/thegent/orchestration/ (redis_concurrency, token_bucket, dag_prioritization, priority_queue, load_based_limits, hybrid_coordination)
- **Status**: Complete (all 7 swarm work items done)
- **Key gaps**: Load management throttling still needed (290 load avg incident); AutoLaunchSystem needs global lock

### Domain: Caching and Indexing

- **Research**: CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md
- **Implementation**: src/thegent/cache/ (multi_level, frecency, pre_warmer), src/thegent/infra/cache_v2.py
- **Status**: Complete (multi-level, diskcache migration, frecency, predictive pre-warming all done)
- **Key gaps**: None identified

### Domain: FastMCP Integration

- **Research**: FASTMCP_SPEC_DEEP_DIVE.md, FASTMCP_ELICITATION_CONTEXT.md, FASTMCP_STORAGE_EVENTSTORE.md
- **Implementation**: src/thegent/mcp/ (server, tools/patterns, elicitation, storage)
- **Status**: Core items complete (elicitation API, storage/eventstore, context API, tool patterns)
- **Key gaps**: FastMCP 3.0 migration status unclear across all code paths

### Domain: ACP (Agent Communication Protocol)

- **Research**: ACP_ADAPTERS_DESIGN_2026-02-18.md, ACP_ADAPTERS_IMPLEMENTATION_SUMMARY_2026-02-18.md
- **Implementation**: src/thegent/adapters/ (acp_client, acp_server, acp_mcp_bridge)
- **Status**: Complete (client, server, bridge, session management endpoints)
- **Key gaps**: None

### Domain: Rust Native Hooks

- **Research**: HOOK_RUST_MIGRATION_RESEARCH_SYNTHESIS.md, HOOK_RUNTIME_RUST_DESIGN.md
- **Implementation**: hooks/hook-dispatcher/ (Rust binary with PolicyEngine, CostCalculator, QualityEvaluator, SecurityScanner)
- **Status**: Phase 1 67% complete, Phase 1.5 substantial (affected_tests, prewarm, report modules added)
- **Key gaps**: Binary compilation issues (type annotations needed); quality-gate binary and security-pipeline binary not yet complete

### Domain: ZMX / Zig Integration

- **Research**: ZIG_RUST_ECOSYSTEM_RESEARCH_2026-02-19.md
- **Implementation**: crates/thegent-zmx, crates/thegent-zmx-interop, src/thegent/muxless/
- **Status**: Substantially complete (37 tests, Rust-Zig C ABI interop POC done, zmx session persistence implemented)
- **Key gaps**: ZMX C ABI from Zig side may need further work for production use

### Domain: TUI Compositor

- **Research**: COMPOSITOR_RESEARCH_AND_ENHANCEMENT_PLAN.md (3000+ lines)
- **Implementation**: src/thegent/ui/compositor/ (Textual-based, 800+ lines)
- **Status**: Phase 1 complete (lifecycle hooks + error boundaries, 46 tests, 95%+ coverage)
- **Key gaps**: 4 separate compositor implementations need consolidation; Phases 2-6 pending (caching done separately, profiling done, CLI integration done)

### Domain: Cross-Platform / Multi-Device

- **Research**: CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md (3956 lines), COMPUTE_OFFLOAD_RESEARCH_REPORT.md
- **Implementation**: src/thegent/compute/ (remote_executor, tailscale, syncthing, offload), src/thegent/automation/macos_desktop.py
- **Status**: Infrastructure code exists; actual multi-device cluster not yet operational
- **Key gaps**: Linux/Windows agent deployment untested; Cloudflare tunneling not configured; conflict resolution strategy (LWW vs vector clocks) undecided

### Domain: Harness Migration (Rust Shims)

- **Research**: Codex threads on shim install-links, guard-shim-forks, runtime-dispatch
- **Implementation**: crates/thegent-shims/, crates/thegent-runtime/, install.sh, bootstrap.sh
- **Status**: In progress -- Rust shims exist, install-links subcommand being added, bash wrapper removal in progress
- **Key gaps**: Multiple install scripts may still generate bash wrappers; dex/clode/roid launcher chain not fully unified

### Domain: Library Modernization

- **Research**: LIBRARY_FIRST_AUDIT_AND_PLAN.md, LIBRARY_REPLACEMENT_RESEARCH_REPORT.md
- **Implementation**: Across codebase -- tenacity (retry), httpx (HTTP), cachetools/diskcache (cache), pybreaker (circuit breaker), ruamel.yaml (YAML), rich (ANSI)
- **Status**: Complete (all 5 library migration items done)
- **Key gaps**: argparse -> Typer migration not yet complete (worker_node, triggers, acp_server)

### Domain: Versioning / Shadow Audit

- **Research**: 2026-02-19-VERSIONING-AND-SHADOW-AUDIT-PLAN.md
- **Implementation**: wp-71001 through wp-71005 (ProjectRegistry, ShadowAuditGit, EpisodeController, audit CLI, hierarchy CLI)
- **Status**: Items implemented (wp-71001-71005 confirmed done by wbs-agent with 80 tests), but WORK_STREAM still shows them in BACKLOG
- **Key gaps**: WORK_STREAM needs updating to reflect completed status

### Domain: Governance / Security

- **Research**: PHASE_GOVERNANCE_CONSOLIDATED_REPORT.md, ADR-013/014/015
- **Implementation**: src/thegent/governance/ (config_provider, federated_policy, kill_switch, native_scanner, signatures, team_coordinator), src/thegent/security/ (guardrails, sandboxing, context_optimizer, hardware_id, input_sanitizer)
- **Status**: Core governance complete; FederatedPolicyEngine prototyped; macOS sandbox enhanced
- **Key gaps**: Agent permission model not formally documented; granular document R/W protection (200 types) not yet implemented

## Research Findings by Topic

### Agent Orchestration at Scale

**Sources**: Claude session 56a6a42f, Codex automated threads, Cursor thegent transcripts
**Summary**:

- Successfully dispatched 30+ agents in parallel batches completing 60+ work items in single sessions
- System hit 290 load average from autonomous loop + high concurrency on 2026-02-19
- SmartPruner with Triple-Lock Criteria (Idle >60s + Complete regex + Docs Written mtime audit) implemented
- Single-file ownership model prevents agent conflicts in Codex workers
- Three-tier agent hierarchy: L1 (coordinator), L2 (teammates/workers), L3 (thegent agents via free/bg)
  **Decisions made**: Time constraints enforced per worker (~300s/130 tool calls); single-file ownership; fail-fast on errors
  **Open questions**: Optimal load throttling thresholds; whether AutoLaunchSystem needs global lock

### Polyglot Runtime Architecture

**Sources**: Droid sessions, Cursor transcripts, docs-scraper
**Summary**:

- Polyglot stack: Python frontmatter (orchestration) + Rust core + Go proxy + Mojo accelerators + Zig session/WASM
- PyPy 30x faster for pure Python, CPython 100x faster for native extensions -- dual runtime strategy
- Package managers consolidated: bun (JS), uv (Python), Taskfile (automation)
- Modern tooling: rg over grep, fd over find, jaq over jq, gix over git
  **Decisions made**: Dual Python runtime (CPython 3.14 + PyPy); 3 harness bins only (dex/clode/roid); Zig for zmx + WASM tools
  **Open questions**: Mojo API stability for production use; dual-runtime interop implementation not started

### Harness Consolidation

**Sources**: Codex threads (shim-install-links, guard-shim-forks, runtime-dispatch), Droid sessions
**Summary**:

- Goal: 3 binaries (dex, clode, roid) dispatched by thegent-shims Rust binary via argv[0]
- Legacy model-specific wrappers (dexflash, clodemax, roidglm) being removed
- install-links subcommand creates symlinks: dex, clode, roid -> thegent-shims
- guard-shim-forks.sh being ported to Rust subcommand
- Bash wrapper generation being eliminated across install.sh, bootstrap.sh, install-thegent-shims.sh
  **Decisions made**: Rust superpackage model; argv[0] dispatch; no bash wrappers
  **Open questions**: Full audit of remaining bash-generated wrappers needed; dex/clode/roid launcher chain verification

### Agent Process Safety Incident

**Sources**: Codex 2026-02-20 06:40 incident, Claude session, Droid session, Cursor transcripts
**Summary**:

- Agent detected load average >90, auto-killed cursor-agent processes via `ps | grep | xargs kill -9`
- User discovered agents were killing their active sessions without authorization
- Led to CRITICAL SECURITY RULE in CLAUDE.md: agents MUST NEVER kill other agent processes
- Protected processes list defined; safe alternative: `thegent mcp prune`
- Also discovered pruning system killing active sessions repeatedly (separate long-standing issue)
  **Decisions made**: Process kill forbidden; protected process list; safe prune-only approach
  **Open questions**: Has the pruning system been fully fixed? User prompt before kill across all code paths?

### Work Stream Management

**Sources**: All four sources
**Summary**:

- Unified WORK_STREAM.md serves as single source of truth with 90+ items completed
- Work stream reached 1000+ items at peak; user requested raising to 1000
- Agent claim/complete cycle uses OCC (Optimistic Concurrency Control) with known warnings
- Incorporator workflow merges fragments from plans/research/specs
- Plan loop (`thegent plan loop`) progresses through backlog autonomously
  **Decisions made**: WORK_STREAM.md is canonical; OCC-based claiming; incorporator agent for merges
  **Open questions**: OCC violation in plan claim/complete -- patched? CLAIMED section has stale timestamps

### Sibling Projects in Kush Ecosystem

**Sources**: Docs scraper, Cursor sessions
**Summary**:

- 20+ projects under /Users/kooshapari/temp-PRODVERCEL/485/kush/
- Key siblings: plangent (multi-agent planning), kimaki (voice AI), smolgents (delegation), crun (DSL), atoms-mcp (knowledge), trace (requirements traceability), usage (AI usage tracking)
- heliosShield and sharecli fully absorbed into thegent
- Cross-project features borrowed: plangent sub-agents, dex flash agents, MCP tools
- File-based IPC protocol and unified persona registry implemented for cross-project coordination
  **Decisions made**: thegent is central hub; sharecli/heliosShield absorbed; cross-project registry via IPC
  **Open questions**: Cross-project dependency graph with versions not formally documented

## Plans Summary (what was planned)

1. **Polish/Optimize/QOL Plan** (100 items, 10 phases): security, performance, multi-device, TUI, diagnostics, CLI, composability, compliance, analytics, production -- partially executed
2. **Versioning and Shadow Audit Plan** (5 work packages): ProjectRegistry, ShadowAuditGit, EpisodeController, audit CLI, hierarchy CLI -- implemented
3. **Unified helios+thegent Master Plan** (4 phases): Foundation, Discovery/Injection, Isolated Autonomy, Full Mesh -- Phase A 90% complete
4. **CLIProxy Release Domain Audit** (4 phases): accuracy, CI/CD unification, release hardening, domain mapping -- plan created, execution pending
5. **Compositor Enhancement Roadmap** (6 phases): lifecycle, error boundaries, caching, profiling, CLI integration, testing -- Phases 1-3 complete
6. **Harness Migration Plan**: Rust-only wrappers, 3 bins, remove bash/zsh wrappers -- in progress
7. **Hookplane Completion** (HP-14 to HP-32): sharecli hookplane items -- status unclear
8. **CI/CD Unification**: Merge duplicate workflows, establish required gates -- pending
9. **Release/Distribution Strategy**: PyPI, GitHub Packages/Releases, prepackaged binaries -- audit done, execution pending
10. **Distributed Compute Cluster**: Mac + Windows desktop via Tailscale + Syncthing -- infrastructure exists, not operational

## Implementation Status

| Feature                                                                   | Status      | Location                                                                | Notes                                        |
| ------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------- | -------------------------------------------- |
| Swarm (redis, redlock, token bucket, DAG, priority queue, critical lanes) | Done        | src/thegent/orchestration/                                              | All 7 items complete                         |
| Multi-level caching (memory/disk/network)                                 | Done        | src/thegent/cache/                                                      | 4 items complete                             |
| FastMCP (elicitation, storage, context, tools)                            | Done        | src/thegent/mcp/                                                        | Core items complete                          |
| ACP adapters (client, server, bridge, sessions)                           | Done        | src/thegent/adapters/                                                   | 4 items complete                             |
| Library modernization (tenacity, httpx, cachetools, ruamel.yaml, rich)    | Done        | Across codebase                                                         | 5 migration items complete                   |
| ZMX/Zig integration (session persistence, C ABI interop)                  | Done        | crates/thegent-zmx\*, src/thegent/muxless/                              | 37 tests                                     |
| TUI compositor Phase 1 (lifecycle, errors)                                | Done        | src/thegent/ui/compositor/                                              | 46 tests, 95%+ coverage                      |
| Rust hooks Phase 1 (PolicyEngine, SecurityScanner)                        | Partial     | hooks/hook-dispatcher/                                                  | 67% complete, compilation issues             |
| Cross-platform infrastructure                                             | Partial     | src/thegent/compute/, src/thegent/automation/                           | Code exists, not operational                 |
| Harness migration (3 Rust bins)                                           | In Progress | crates/thegent-shims/, crates/thegent-runtime/                          | Bash removal ongoing                         |
| Versioning/shadow audit (wp-71001-71005)                                  | Done        | src/thegent/registry/, tests/                                           | 80 tests, needs WORK_STREAM update           |
| Cross-project integration (registry, IPC, borrowing)                      | Done        | src/thegent/registry/, src/thegent/ipc/                                 | 3 items complete                             |
| Agent Crew stack                                                          | Partial     | src/thegent/agents/crew/                                                | MVP implemented                              |
| SmolGents base class                                                      | Done        | src/thegent/agents/smolgents/                                           | 53 tests                                     |
| Supermemory + MemoryManager integration                                   | Done        | src/thegent/memory/                                                     | Client + integration done                    |
| Pareto/Cost-aware routing                                                 | Done        | src/thegent/routing/                                                    | Both routers implemented                     |
| LiteLLM integration                                                       | Done        | src/thegent/routing/litellm\_\*                                         | Responses handler + Claude integration       |
| Ghostty terminal integration                                              | Done        | src/thegent/integrations/ghostty.py                                     | 53 tests                                     |
| macOS sandbox enhancement                                                 | Done        | src/thegent/security/macos_sandbox.py                                   | 39 tests                                     |
| Idea seed scanner                                                         | Done        | src/thegent/commands/idea_seeds.py, src/thegent/memory/seed_detector.py | 53 tests                                     |
| Doctor fix command                                                        | Done        | src/thegent/commands/doctor.py                                          | 41 tests                                     |
| Sync command                                                              | Done        | src/thegent/commands/sync.py                                            | Implementation complete                      |
| CI/CD unification                                                         | Not Started | .github/workflows/                                                      | Duplicate workflows exist                    |
| Release pipeline                                                          | Not Started | --                                                                      | Audit done, no pipeline                      |
| Argparse -> Typer migration                                               | Not Started | 3 files identified                                                      | worker_node, triggers, acp_server            |
| Tray app                                                                  | Not Started | --                                                                      | Architecture discussed, no code              |
| Dual Python runtime (CPython + PyPy)                                      | Not Started | --                                                                      | Research done, no implementation             |
| Document R/W protection (200 types)                                       | Not Started | --                                                                      | Discussed, no implementation                 |
| Agent permission model                                                    | Not Started | --                                                                      | Trust scoring discussed, no formal doc       |
| Codex CLI proxy (0.104.0 fix)                                             | BROKEN      | src/thegent/cliproxy_adapter.py                                         | 0.104.0 broke proxy today -- URGENT          |
| Stop hooks optimization (<15s)                                            | Partial     | hooks/, hooks/hook-dispatcher/                                          | quality-gate.sh timeouts; Rust migration 67% |

## Research Gaps (discussed, not documented)

1. **Tray app architecture**: Ghostty-speed terminal + chat UI, project-split, 300 agent scalability -- discussed extensively in Droid/Cursor, no dedicated research doc
2. **Dual Python runtime interop**: CPython 3.14 + PyPy in single process -- research findings exist but no implementation plan
3. **CLIProxyAPI++ upstream PR strategy**: Fork exists, full coverage achieved, but no PR preparation doc
4. **Agent scaling benchmarks**: 300 agent target discussed but no benchmark results or capacity planning doc
5. **WASM isolation runtime selection**: wasmtime vs wasmer vs extism for L2 sandboxing -- mentioned in UNIFIED_MASTER_SPEC, no comparison doc
6. **Mojo integration plan**: Phase 3 of polyglot migration -- no dedicated research on Mojo API stability or integration points
7. **Domain mapping UX**: Porkbun + Cloudflare Tunnel for custom domains -- mentioned in CLIProxy audit, no implementation plan
8. **Voice profile / agent communication style**: Discussed in Cursor voice-profile project, no integration with thegent agent personas
9. **Job hunter pipeline**: Streamlit UI + NocoDB + LinkedIn Voyager -- separate project, potential integration points undocumented
10. **Hookplane HP-14 to HP-32**: sharecli hookplane items -- status unclear after sharecli absorption

## Contradictions / Conflicts

1. **WORK_STREAM.md vs actual status**: wp-71001 through wp-71005 show in BACKLOG but were confirmed implemented with 80 tests by wbs-agent. WORK_STREAM needs updating.
2. **4 compositor implementations**: src/thegent/ux/compositor.py (MVP), src/thegent/ui/compositor/ (Textual), src/thegent/tui/compositor.py, src/thegent/compositor/ -- need consolidation into one canonical implementation.
3. **Agent pruning behavior**: SmartPruner implemented with Triple-Lock Criteria, but user still reports sessions being killed. Kill-protection rule added but underlying pruning logic may still have issues.
4. **OCC violations**: thegent plan claim/complete warns OCC violation for WORK_STREAM.md but still succeeds -- investigation found root cause but unclear if patch applied.
5. **FastMCP version**: Code references both FastMCP 2.x and 3.0 patterns. No clear migration boundary documented.
6. **Shell script elimination policy**: "no scripts where rust/zig/mojo/py can be used" vs existing bash scripts in hooks/, scripts/, install.sh, bootstrap.sh that are still actively used.
7. **ZMX C ABI status**: impl-zmx-c-abi shows DONE in some contexts (Codex confirmed), but Droid session 56a6a42f marked it PENDING. The Rust wrapper crate exists but the Zig-side C ABI exposure may need verification.
8. **Codex CLI proxy**: Was working until 0.104.0 update today. CLIProxyAPI++ fork had full coverage, but upstream breaking change invalidated the integration.

## Recommended Next Research Areas

1. **Agent load management and throttling** -- After 290 load avg incident, need formal capacity planning and auto-throttling design
2. **Tray app / desktop UI architecture** -- Frequently requested, no dedicated research doc exists
3. **Multi-device cluster operationalization** -- Infrastructure code exists but integration testing and actual cluster deployment not done
4. **WASM sandboxing runtime comparison** -- Needed for Phase 4 Zig/WASM work
5. **Mojo ecosystem stability assessment** -- Needed for Phase 3 accelerator work
6. **Release pipeline and distribution** -- PyPI, GitHub Releases, Homebrew formula -- no implementation
7. **Agent permission model formalization** -- Trust scoring discussed but no formal spec
8. **Compositor consolidation plan** -- 4 implementations need merging
9. **End-to-end testing strategy execution** -- Plan exists but unclear what coverage is actually achieved
10. **Cross-platform testing** -- Linux/Windows agent deployment untested; only macOS path validated
