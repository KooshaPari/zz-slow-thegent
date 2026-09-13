<DONE>
# Harness Parity Matrix — 2026-02-20

> **Purpose**: Comprehensive feature parity comparison of thegent against all major AI coding agent harnesses.
> **Scope**: 8 harnesses, 7 dimensions, 50+ feature rows.
> **Primary output**: Gap analysis + 20 WL items (WL-100 to WL-119).
> **Sources**: docs/context/claude-code.md, docs/context/codex.md, docs/context/gemini-cli.md, docs/context/ante.md, docs/research/AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md, src/thegent/ source analysis, web research 2026-02-20.

---

## 1. Executive Summary

thegent is the most sophisticated governance and orchestration layer among all harnesses evaluated. It uniquely combines multi-provider routing (Pareto router, LiteLLM), lifecycle hooks, federated policy enforcement, HITL approval workflows, and cross-session agent memory. Its competitive strengths are governance depth, provider breadth, and agent coordination.

**Top 5 gaps relative to competitors:**

1. **No native TUI** — thegent lacks an integrated terminal UI. All major competitors (Claude Code, Codex, ANTE, OpenCode, Gemini CLI) ship rich ratatui/Bubble-Tea TUIs with inline diffs, approval dialogs, and progress streaming. thegent has a TUI framework (Phase 2-3 complete) but no fully wired interactive agent session surface.

2. **No first-class programmatic SDK** — Codex ships `@openai/codex-sdk` (TypeScript), Claude Code ships a Python SDK, ANTE exposes a daemon protocol. thegent has no published SDK; integration requires knowing internal Python APIs.

3. **Skills system is skeletal** — Claude Code, ANTE, OpenCode, and Codex all implement agent-skills (SKILL.md/SKILL.json reusable workflows). thegent has a `skills/` module but no skills discovery, invocation, or agent-skills spec compatibility.

4. **No background/async execution with continuation** — Codex `codex exec --ephemeral`, Claude Code `--bg`, and Antigravity all support async background runs with session IDs for later polling. thegent has `thegent bg` but it is not exposed as a stable API surface for external integrations.

5. **No diff review UI** — Codex App Server streams unified diffs; Claude Code shows side-by-side diffs; ANTE has diff panes. thegent approval flow (WL-019 HITLApprovalWorkflow) operates on metadata without rendering actual file diffs to the user.

---

## 2. Harness Profiles

### 2.1 Claude Code CLI (Anthropic)

The reference harness for deep coding workflows. Ships as a native binary (Rust-like) + npm package. Key differentiators: 7-parallel subagent spawning, CLAUDE.md project memory, rich hooks system (PreToolUse/PostToolUse/Stop/SessionStart), full MCP client support, session resume (`-c`/`--resume`), streaming JSON output (`--output-format stream-json`). Enterprise via Anthropic Console with policy overlays. Hooks are shell scripts registered in `.claude/settings.json`. Extensible via skills and slash commands. No MCP server mode; no programmatic SDK (subprocess only). Model locked to Anthropic Claude family.

### 2.2 Codex CLI (OpenAI)

Rust binary + TypeScript shim + `@openai/codex-sdk` programmatic SDK. Unique for its App Server protocol — a bidirectional JSON-RPC daemon over stdio that powers VS Code, JetBrains, Xcode, macOS desktop, and web integrations from a single backend. Platform-native sandboxing (Linux Landlock+seccomp, macOS profiles, Windows token restriction). Fine-grained approval policies (untrusted/on-failure/on-request/never). MCP server mode (2 tools, prototype). Structured output via JSON Schema. Image input (local + URL). Skills via SKILL.md. Thread persistence with fork/rollback. Exclusively uses Responses API — cannot use Chat Completions without a proxy. No hooks system.

### 2.3 Gemini CLI (Google)

Open-source (Apache 2.0) Node.js CLI by Google. Three auth methods: OAuth, API key, Vertex AI. Built-in Google Search grounding (not just web search — uses Google's proprietary grounding API). MCP client (stdio, SSE, HTTP transports). No MCP server mode. YOLO mode for full auto-approval. Sandboxed mode isolates tool execution. Rich hooks system for lifecycle customization. Free tier: 1,000 req/day. Weekly release cadence. No session resume, no programmatic SDK, no background execution.

### 2.4 ANTE (Antigravity Labs)

Native Rust, lightweight, minimal-dependency terminal agent. Client-daemon architecture (ratatui TUI + headless daemon). Provider-agnostic via trait interface (Anthropic, OpenAI, Gemini, Grok, OpenRouter, local llama.cpp). Skills system (user + project level). Sub-agent spawning via `Task` tool. Long-term memory with semantic search and context compaction. HITL approval at session level. No MCP server mode. No hooks system per se; governance via session-level policies. Preview state; macOS + Linux only.

### 2.5 Factory Droid

Commercial closed-source agent from Factory.ai. Tiered autonomy model (read-only, low, medium, high). Integrates Chrome DevTools, linters, unit tests, type checkers for self-validation. JSON event streams, session persistence, audit logging. Terminal-Bench #1 ranked agent. Model-agnostic (can use Opus for planning, GPT-5 for execution). Unix philosophy: bash/make integration. `droid exec -f prompt.md --auto high` pattern. Invoked by thegent via `DroidRunner`. No hooks, no MCP, no programmatic SDK.

### 2.6 Aider

Python-based, open-source (Apache 2.0). Deep git integration — every change auto-committed with descriptive messages. Codebase map (ctags-based repo-map) for large project understanding. Multi-file editing in one changeset. `--architect` mode (planning), `--ask` mode (Q&A), `--code` mode (implementation). Auto-lint and auto-test after every change. Supports 100+ LLMs via litellm. No TUI (terminal-only line-mode). No MCP (third-party `aider-desk` adds MCP server). No session resume (stateless). No background execution. No hooks. Strong git-native workflow.

### 2.7 OpenCode

Go-based, open-source terminal agent (70k+ GitHub stars). Bubble Tea TUI. Multi-session with SQLite persistence. 75+ LLM providers (Anthropic, OpenAI, Gemini, local). LSP integration (12+ language servers: Rust, TypeScript, Python, Swift, Terraform). Plugin system via `.opencode/` directory. Custom agents with model + tool-access scoping (plan agent, general agent). Desktop app + VS Code extension + IDE extension. Non-interactive mode. No MCP (as of Feb 2026). No hooks. No background execution.

### 2.8 thegent

Python/Rust polyglot platform. The only harness that is primarily an _orchestration and governance layer_ rather than a single-agent executor. Key capabilities: Pareto router (cost/latency multi-objective routing), LiteLLM router (11+ providers), CLIProxy (Cursor, Codex, Claude Code, ANTE), federated policy engine (EU-AI-Act/US-SEC compliance), HITLApprovalWorkflow, cross-session memory (Supermemory + local), agent registry (TF-IDF capability matching), swarm coordination (multi-agent with RedLock), MCP server (FastMCP, port 3847), hooks system (lifecycle hook dispatcher, YAML config), work stream management, TUI compositor framework, session management (`thegent ps/status/wait`), background execution (`thegent bg`), plan loop (`thegent plan loop`). Wraps Claude Code, Codex, Gemini, ANTE, Factory Droid, OpenCode, Cursor as sub-harnesses.

---

## 3. Full Parity Matrix

Legend: **✓** = Full support | **~** = Partial / limited | **✗** = Missing | **?** = Unknown / unverified

### 3.1 Core Execution

| Feature                             | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| ----------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| Single-turn prompt exec             |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |
| Multi-turn conversation/session     |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |
| Streaming output                    |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✗   |    ✓     |      ✓      |
| Background/async execution          |      ✓      |   ✓   |     ✗      |  ✓   |       ✗       |   ✗   |    ✗     |      ~      |
| Session resume/continue             |      ✓      |   ✓   |     ✗      |  ✓   |       ~       |   ✗   |    ✓     |      ~      |
| Parallel execution (multi-instance) |      ✓      |   ✓   |     ✗      |  ✓   |       ✗       |   ✓   |    ✗     |      ✓      |
| JSON/structured output mode         |      ✓      |   ✓   |     ~      |  ~   |       ✓       |   ✗   |    ~     |      ✓      |
| Stdin piping support                |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |
| Max-turns / budget control          |      ✓      |   ✓   |     ✗      |  ✓   |       ✓       |   ✗   |    ✗     |      ✓      |
| Non-interactive/headless mode       |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |

### 3.2 Tool Use / Environment

| Feature                         | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| ------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| File read/write tools           |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |
| Shell command execution         |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |
| Web search                      |      ✓      |   ✓   |     ✓      |  ~   |       ✗       |   ✗   |    ✗     |      ✓      |
| MCP client (consume tools)      |      ✓      |   ✓   |     ✓      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| MCP server mode (expose tools)  |      ✗      |   ~   |     ✗      |  ✗   |       ✗       |   ~   |    ✗     |      ✓      |
| Browser/Playwright automation   |      ✗      |   ✗   |     ✗      |  ✗   |       ~       |   ✗   |    ✗     |      ✓      |
| Image/vision input              |      ✓      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ~      |
| Audio input                     |      ✗      |   ~   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✗      |
| Structured output (JSON schema) |      ~      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Git native integration          |      ✓      |   ~   |     ~      |  ~   |       ~       |   ✓   |    ~     |      ✓      |
| LSP integration                 |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✓     |      ~      |
| Dynamic client tools            |      ✗      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✗      |

### 3.3 Agent Orchestration

| Feature                           | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| --------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| Sub-agent dispatch                |      ✓      |   ~   |     ✗      |  ✓   |       ✗       |   ✗   |    ✓     |      ✓      |
| Multi-agent swarm coordination    |      ✗      |   ~   |     ✗      |  ~   |       ✗       |   ✗   |    ✗     |      ✓      |
| Agent registry / capability index |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Plan → execute workflow           |      ✓      |   ~   |     ✗      |  ✓   |       ✓       |   ~   |    ✓     |      ✓      |
| DAG task execution                |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| HITL (human-in-the-loop) approval |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ~   |    ✓     |      ✓      |
| Agent memory (cross-session)      |      ✓      |   ~   |     ✗      |  ✓   |       ~       |   ✗   |    ✓     |      ✓      |
| Thread fork/rollback              |      ✗      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✗      |
| Code review mode                  |      ✗      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ~     |      ✗      |
| Skills / reusable procedures      |      ✓      |   ✓   |     ✓      |  ✓   |       ✗       |   ✗   |    ✓     |      ~      |
| Project memory (CLAUDE.md style)  |      ✓      |   ~   |     ~      |  ✓   |       ✗       |   ✗   |    ✓     |      ~      |
| Context compaction/summarization  |      ✓      |   ✓   |     ✗      |  ✓   |       ✗       |   ✗   |    ✗     |      ✗      |

### 3.4 Routing and Models

| Feature                               | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| ------------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| Multi-provider support                |      ~      |   ~   |     ~      |  ✓   |       ~       |   ✓   |    ✓     |      ✓      |
| Model switching per task              |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✓   |    ✓     |      ✓      |
| Cost-aware routing                    |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Latency-aware routing                 |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Proxy support (LiteLLM / custom)      |      ~      |   ✓   |     ✗      |  ✗   |       ✗       |   ✓   |    ✓     |      ✓      |
| Rate limit handling / circuit breaker |      ✓      |   ✓   |     ~      |  ✓   |       ✗       |   ~   |    ✗     |      ✓      |
| Semantic cache                        |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Pareto / multi-objective routing      |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Local / offline model support         |      ✗      |   ✗   |     ✗      |  ✓   |       ✗       |   ✓   |    ✓     |      ~      |
| Model reasoning effort control        |      ✓      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ~      |
| Fallback chain / redundancy           |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |

### 3.5 Security and Governance

| Feature                                 | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| --------------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| Sandbox / process isolation             |      ✓      |   ✓   |     ✓      |  ~   |       ✓       |   ✗   |    ✗     |      ✓      |
| Tool approval policy (per-tool)         |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ~   |    ✓     |      ✓      |
| Audit logging (tamper-evident)          |      ~      |   ~   |     ✗      |  ✗   |       ✓       |   ✗   |    ✗     |      ✓      |
| Compliance evidence (MAIF artifacts)    |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Secret scanning                         |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| GDPR / data retention policy            |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Federated policy enforcement            |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Constitutional / rule enforcement       |      ✓      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Policy override event auditing          |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Approval for file writes (fine-grained) |      ✓      |   ✓   |     ✓      |  ✓   |       ✓       |   ✗   |    ~     |      ✓      |

### 3.6 Developer Experience

| Feature                          | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| -------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| TUI (interactive terminal UI)    |      ✓      |   ✓   |     ✓      |  ✓   |       ~       |   ✗   |    ✓     |      ~      |
| Inline diff review / approval UI |      ✓      |   ✓   |     ✓      |  ✓   |       ✗       |   ✗   |    ✓     |      ✗      |
| IDE integration                  |      ✓      |   ✓   |     ✗      |  ✗   |       ✓       |   ~   |    ✓     |      ~      |
| CLI completions (zsh/bash/fish)  |      ✓      |   ✓   |     ✓      |  ~   |       ✗       |   ✗   |    ✓     |      ~      |
| Help system (contextual)         |      ✓      |   ✓   |     ✓      |  ✓   |       ~       |   ✓   |    ✓     |      ✓      |
| Progress indicators / spinners   |      ✓      |   ✓   |     ✓      |  ✓   |       ~       |   ✗   |    ✓     |      ✓      |
| Hooks / lifecycle events         |      ✓      |   ✗   |     ✓      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Plugin / skill system            |      ✓      |   ✓   |     ✓      |  ✓   |       ✗       |   ✗   |    ✓     |      ~      |
| Programmatic SDK                 |      ~      |   ✓   |     ✗      |  ✗   |       ✗       |   ✓   |    ~     |      ✗      |
| App server / embedding protocol  |      ✗      |   ✓   |     ✗      |  ~   |       ✗       |   ✗   |    ✗     |      ✗      |
| Diff-streamed output             |      ✓      |   ✓   |     ✗      |  ✓   |       ✗       |   ✓   |    ✓     |      ✗      |
| Context window status display    |      ✓      |   ✓   |     ✗      |  ✓   |       ✗       |   ✓   |    ✓     |      ✗      |
| Session list / inspect CLI       |      ✓      |   ✓   |     ✗      |  ✓   |       ✗       |   ✗   |    ✓     |      ✓      |

### 3.7 Deployment and Enterprise

| Feature                            | Claude Code | Codex | Gemini CLI | ANTE | Factory Droid | Aider | OpenCode | **thegent** |
| ---------------------------------- | :---------: | :---: | :--------: | :--: | :-----------: | :---: | :------: | :---------: |
| Windows support                    |      ✓      |   ✓   |     ~      |  ✗   |       ✗       |   ✓   |    ✓     |      ✓      |
| Docker support                     |      ~      |   ~   |     ~      |  ✗   |       ✓       |   ✓   |    ~     |      ~      |
| Multi-project tenancy              |      ✓      |   ✓   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Team / org management              |      ✓      |   ✓   |     ✓      |  ✗   |       ✓       |   ✗   |    ✗     |      ✓      |
| SSO / enterprise auth              |      ✓      |   ✓   |     ✓      |  ✗   |       ✓       |   ✗   |    ✗     |      ~      |
| Cost tracking / budget enforcement |      ✓      |   ~   |     ~      |  ✗   |       ✓       |   ✗   |    ✗     |      ✓      |
| Self-hosted deployment             |      ✗      |   ✗   |     ✓      |  ✓   |       ✗       |   ✓   |    ✓     |      ✓      |
| Benchmarking / eval mode           |      ✗      |   ✗   |     ✗      |  ✗   |       ✓       |   ✗   |    ✗     |      ~      |
| Auto-install / doctor CLI          |      ✓      |   ✓   |     ✓      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |
| Cross-platform rules sync          |      ✗      |   ✗   |     ✗      |  ✗   |       ✗       |   ✗   |    ✗     |      ✓      |

---

## 4. Gap Analysis — Missing in thegent (Ranked by Priority)

### Priority 1: High Impact, Moderate Effort

**G-01: Inline Diff Review UI**
All major interactive harnesses (Claude Code, Codex App Server, ANTE, OpenCode, Gemini CLI) render file diffs inline before approval. thegent's HITL workflow (WL-019) approves operations by metadata only — the approver never sees the actual patch. This blocks adoption for any workflow where humans review changes before commit.

- **Gap size**: 7/8 harnesses have it; thegent does not.
- **Proposed**: WL-100 — Diff renderer in TUI compositor + HITL approval event includes unified diff payload.

**G-02: Skills / Agent-Skills Spec Compatibility**
Claude Code, Codex (SKILL.md), ANTE, Gemini CLI, and OpenCode all implement skills — reusable instruction modules loadable from project `.codex/skills/`, `.ante/skills/`, `.claude/commands/`. thegent has a `skills/` module but no agent-facing discovery or invocation (`activate_skill` tool) and no SKILL.md/SKILL.json compatibility.

- **Gap size**: 5/8 harnesses have full skills; thegent has partial.
- **Proposed**: WL-101 — Skills discovery + invocation (SKILL.md spec compatible).

**G-03: First-Class Programmatic SDK**
Codex ships `@openai/codex-sdk`. Aider exposes a Python API. Claude Code is invocable via subprocess with well-defined JSONL protocol. thegent has no published SDK — external tools must know internal Python module structure.

- **Gap size**: Blocks ISV and CI/CD integrations.
- **Proposed**: WL-102 — `thegent-sdk` Python package with typed RunThread, RunResult, StreamEvent types.

**G-04: Context Compaction / Auto-Summarization**
Claude Code, Codex, and ANTE all implement context compaction — when conversation history approaches token limits, they summarize older turns to keep within budget. thegent has no equivalent; long agent sessions grow unbounded or fail with context overflow.

- **Gap size**: 3/8 harnesses have it; directly impacts agent session longevity.
- **Proposed**: WL-103 — Context compaction layer in agent runner (triggered at 80% context fill).

**G-05: App Server / Embedding Protocol**
Codex App Server (JSON-RPC over stdio) enables VS Code, JetBrains, Xcode, and web integrations from a single backend. No other harness has an equivalent. thegent has no embedding protocol; IDE integration requires direct Python API calls.

- **Gap size**: Unique to Codex but strategically important.
- **Proposed**: WL-104 — thegent embedding protocol (lightweight JSON-RPC stdio daemon mode).

### Priority 2: High Impact, Lower Effort

**G-06: Dynamic Client Tools**
Codex App Server allows clients to register their own tools that the model can invoke; execution is routed back to the client. thegent has no equivalent — all tools are server-side MCP tools.

- **Proposed**: WL-105 — Dynamic tool registration in MCP server (client-provided tool specs in session init).

**G-07: Thread Fork / Rollback**
Codex supports forking a thread at any turn (creating an alternate timeline) and rolling back N turns without reverting file changes. Useful for experimentation and recovery. thegent has no equivalent.

- **Proposed**: WL-106 — Session fork + turn rollback in SessionManager.

**G-08: Code Review Mode (Separate from Coding Mode)**
Codex has a dedicated `review/start` method (via App Server) that runs a code review turn without executing changes. Claude Code lacks this; OpenCode has a "plan agent" variant. thegent has no dedicated review mode.

- **Proposed**: WL-107 — `thegent review "..."` command invoking read-only agent turn with structured review output.

**G-09: Context Window Display**
Claude Code, Codex, ANTE, Aider, and OpenCode all display current context window utilization to the user (tokens used / max). thegent has no context budget display in TUI or CLI output.

- **Proposed**: WL-108 — Context budget indicator in TUI status bar and `--json` output.

**G-10: LSP Integration**
OpenCode is the only harness with deep LSP integration (12+ language servers). This enables symbol lookup, diagnostics, and hover-info as tool inputs. thegent has a `lsp/` module and `shared_lsp_manager.py` but no agent-facing LSP tool.

- **Proposed**: WL-109 — LSP tool in MCP server (diagnostics, symbol lookup, hover) backed by existing shared_lsp_manager.

### Priority 3: Moderate Impact, Moderate Effort

**G-11: Session Resume (Stable External API)**
`thegent bg -C <session_id>` exists but is fragile and undocumented. Claude Code (`--resume <id>`), Codex (`codex resume <id>`), and OpenCode all provide stable session resume. thegent needs a stable `thegent resume <session_id>` surface with documented semantics.

- **Proposed**: WL-110 — `thegent resume <session_id>` with stable session state contract.

**G-12: Agent-Skills MCP Tool**
Claude Code and ANTE expose skills as MCP tools (the model calls `activate_skill("deploy")` which runs the skill). thegent's MCP server does not expose skill invocation.

- **Proposed**: WL-111 — `thegent_activate_skill` MCP tool wired to skills discovery module.

**G-13: Reasoning Effort / Extended Thinking Control**
Claude Code (`extendedThinking`), Codex (`model_reasoning_effort: minimal|low|medium|high|xhigh`), and ANTE all expose reasoning effort as a first-class configuration. thegent routes to models that support reasoning but does not expose effort control as a unified parameter.

- **Proposed**: WL-112 — Unified `reasoning_effort` parameter in RunOptions forwarded to provider-specific controls.

**G-14: Structured Output (JSON Schema) for Agent Turns**
Codex supports `--output-schema schema.json` to constrain agent final output to a JSON schema (strict mode via Responses API). Claude Code has partial support. thegent has no equivalent for constraining agent output shape.

- **Proposed**: WL-113 — `--output-schema` support in `thegent run` forwarded to underlying harness.

**G-15: Image Input in Agent Sessions**
Claude Code and Codex both support image input (local files, URLs) to agent turns. thegent passes images to underlying models via provider API but does not expose this as a first-class CLI argument in agent session invocation.

- **Proposed**: WL-114 — `--image <path>` flag in `thegent run` with forwarding to image-capable harnesses.

**G-16: Benchmarking / Eval Harness**
Factory Droid (Terminal-Bench #1), and ANTE have built-in eval modes. thegent has benchmark scripts (`scripts/benchmark-quality-gate-rust.sh`) but no agent-facing benchmark runner.

- **Proposed**: WL-115 — `thegent bench run --suite <name> --harness <name>` for cross-harness benchmarking.

### Priority 4: Lower Impact or Longer Effort

**G-17: Audio Input**
Codex has partial audio input support (`include: ["item.input_audio.transcript"]` in Responses API). No other harness supports this. thegent has no audio input support.

- **Proposed**: WL-116 — Audio transcript input passthrough for Codex-backed sessions.

**G-18: IDE Extension (Native)**
Claude Code, Codex (VS Code + JetBrains + Xcode), OpenCode (VS Code + Cursor), Factory Droid all ship IDE extensions. thegent has no native IDE extension (only MCP server that IDEs can connect to).

- **Proposed**: WL-117 — VS Code extension for thegent (MCP client + session management UI).

**G-19: Free / No-API-Key Tier**
Gemini CLI offers 1,000 free requests/day with Google OAuth. OpenCode supports local Ollama. ANTE supports local llama.cpp. thegent requires API keys for all operations (no free tier, no local model).

- **Proposed**: WL-118 — Local model support in runner (Ollama-backed provider) for zero-cost execution.

**G-20: Google Search Grounding**
Gemini CLI uniquely provides Google Search grounding — not just web search, but Google's proprietary Search API result injection into the model context. thegent uses DuckDuckGo + web scraping. No equivalent for Google grounding.

- **Proposed**: WL-119 — Google Search grounding provider via Gemini API passthrough.

---

## 5. Competitive Advantages (thegent Leads)

These are features thegent has that no other harness (or only one) provides:

| Advantage                          | Description                                                                      | Competitors               |
| ---------------------------------- | -------------------------------------------------------------------------------- | ------------------------- |
| **Pareto multi-objective routing** | Simultaneous cost + latency + quality optimization across providers              | None                      |
| **Federated policy enforcement**   | 3-level namespace hierarchy, EU-AI-Act/US-SEC jurisdiction profiles, arbitration | None                      |
| **MAIF compliance artifacts**      | Tamper-evident audit evidence for AI governance                                  | None                      |
| **Multi-agent swarm w/ RedLock**   | Distributed concurrent agents with atomic coordination                           | None                      |
| **Agent capability registry**      | TF-IDF-based capability matching, auto-agent selection                           | None                      |
| **DAG task execution**             | Dependency-ordered task graphs with DagPrioritizer (Kahn + CPM)                  | None                      |
| **Work stream management**         | Canonical WORK_STREAM.md with claim/complete lifecycle                           | None                      |
| **Cross-harness orchestration**    | Wraps Claude Code + Codex + Gemini + ANTE + Droid + Cursor                       | None                      |
| **Semantic cache**                 | Embedding-based response caching (avoids duplicate LLM calls)                    | None                      |
| **Policy override event auditing** | Every policy override is logged with justification                               | None                      |
| **Context-aware model selection**  | Tag router + task router selects model based on task semantic tags               | None                      |
| **Secret scanning in hooks**       | Gitleaks integrated into stop hook                                               | None                      |
| **Cross-session memory synthesis** | Supermemory + local garden with semantic retrieval                               | ANTE (partial)            |
| **MCP server mode**                | Exposes tools to external MCP clients (port 3847)                                | Codex (2-tool prototype)  |
| **Browser/Playwright tool**        | Full browser automation via Playwright MCP server                                | None                      |
| **HITL approval workflow**         | `thegent govern approve/reject` with full audit trail                            | Codex (partial, no audit) |

---

## 6. Implementation Roadmap

Ordered by impact/effort ratio for closing competitive gaps.

### Sprint 1 (1-2 weeks): Quick Impact

1. **WL-108** — Context budget indicator (TUI + JSON output) — 2-4h
2. **WL-112** — Unified reasoning_effort parameter — 4-8h
3. **WL-113** — --output-schema for agent turns — 4-8h
4. **WL-114** — --image flag in thegent run — 4-8h
5. **WL-110** — thegent resume <session_id> stable API — 4-8h

### Sprint 2 (2-4 weeks): Parity Closure

6. **WL-101** — Skills discovery + SKILL.md spec compatibility — 1-2d
7. **WL-103** — Context compaction layer — 2-3d
8. **WL-107** — thegent review command (read-only agent mode) — 1-2d
9. **WL-106** — Session fork + rollback — 2-3d
10. **WL-109** — LSP tool in MCP server — 2-3d

### Sprint 3 (4-8 weeks): SDK and Protocol

11. **WL-102** — thegent-sdk Python package — 1-2w
12. **WL-104** — Embedding protocol (JSON-RPC stdio daemon) — 2-3w
13. **WL-105** — Dynamic client tool registration — 1-2w
14. **WL-111** — thegent_activate_skill MCP tool — 3-5d
15. **WL-100** — Diff renderer in TUI + HITL diff payload — 1-2w

### Sprint 4 (8-12 weeks): Ecosystem Expansion

16. **WL-115** — Cross-harness benchmarking suite — 1-2w
17. **WL-118** — Ollama local model provider — 1-2w
18. **WL-117** — VS Code extension — 3-4w
19. **WL-116** — Audio input passthrough — 3-5d
20. **WL-119** — Google Search grounding — 3-5d

---

## 7. Proposed WL Items (WL-100 through WL-119)

See `docs/reference/WORK_STREAM.md` for canonical item entries. Items below are summarized for quick reference.

| ID     | Title                                                     | Priority | Effort   | Blocked By |
| ------ | --------------------------------------------------------- | -------- | -------- | ---------- |
| WL-100 | Diff renderer in TUI + HITL diff payload                  | P1       | M (3-5d) | none       |
| WL-101 | Skills discovery + SKILL.md spec compatibility            | P1       | M (1-2d) | none       |
| WL-102 | thegent-sdk Python package (typed public API)             | P1       | L (1-2w) | none       |
| WL-103 | Context compaction layer in agent runner                  | P1       | M (2-3d) | none       |
| WL-104 | Embedding protocol — JSON-RPC stdio daemon mode           | P1       | L (2-3w) | WL-102     |
| WL-105 | Dynamic client tool registration in MCP server            | P2       | M (1-2d) | none       |
| WL-106 | Session fork + turn rollback in SessionManager            | P2       | M (2-3d) | WL-110     |
| WL-107 | thegent review — read-only agent turn + structured output | P2       | S (1-2d) | none       |
| WL-108 | Context budget indicator (TUI status bar + JSON output)   | P2       | S (2-4h) | none       |
| WL-109 | LSP tool in MCP server (diagnostics, symbol, hover)       | P2       | M (2-3d) | none       |
| WL-110 | thegent resume — stable session resume API                | P2       | S (4-8h) | none       |
| WL-111 | thegent_activate_skill MCP tool wired to skills module    | P2       | S (3-5d) | WL-101     |
| WL-112 | Unified reasoning_effort parameter in RunOptions          | P2       | S (4-8h) | none       |
| WL-113 | --output-schema support in thegent run                    | P2       | S (4-8h) | none       |
| WL-114 | --image flag in thegent run (image-capable harnesses)     | P2       | S (4-8h) | none       |
| WL-115 | Cross-harness benchmarking suite (thegent bench)          | P3       | M (1-2w) | none       |
| WL-116 | Audio transcript input passthrough for Codex sessions     | P3       | S (3-5d) | none       |
| WL-117 | VS Code extension for thegent (MCP client + session UI)   | P3       | L (3-4w) | WL-104     |
| WL-118 | Ollama local model provider (zero-cost execution)         | P3       | M (1-2w) | none       |
| WL-119 | Google Search grounding via Gemini API passthrough        | P3       | S (3-5d) | none       |

---

## Sources

- `docs/context/claude-code.md` — Claude Code CLI context (fetched 2026-02-20)
- `docs/context/codex.md` — Codex harness context (fetched 2026-02-20, source analysis)
- `docs/context/gemini-cli.md` — Gemini CLI context (fetched 2026-02-20)
- `docs/context/ante.md` — ANTE context (fetched 2026-02-20)
- `docs/research/CODEX_HARNESS_RESEARCH_2026-02-20.md` — 18-section Codex analysis
- `docs/research/AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md` — OpenCode/kilo/roo research
- `src/thegent/agents/droid.py` — Factory Droid runner source
- `src/thegent/routing/` — 30+ routing module analysis
- `src/thegent/hooks/hook-config.yaml` — Hooks configuration
- `src/thegent/mcp/` — MCP server analysis
- Web research: [Aider docs](https://aider.chat/docs/), [OpenCode GitHub](https://github.com/opencode-ai/opencode), [Factory Droid](https://factory.ai/news/terminal-bench), 2026-02-20
