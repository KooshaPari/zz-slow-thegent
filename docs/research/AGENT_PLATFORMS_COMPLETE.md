<DONE>
# Agent Platforms Complete Research & Integration Guide

<DONE>

> **Status**: Complete | **Version**: 1.0 | **Date**: 2026-02-16
> **Related**:
>
> - [Provider Setup Guide](../guides/PROVIDER_SETUP_GUIDE.md)
> - [Agent Access and Optimization Audit Plan](./AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md)
> - [Unified System Application Plan](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)
> - [Sitback Design Plan](../plans/2026-02-15-thegent-sitback-design.md)

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [CLI-Based Agent Platforms](#2-cli-based-agent-platforms)
3. [OpenClaw & Agent Zero Evaluation](#3-openclaw--agent-zero-evaluation)
4. [Integration Use Cases](#4-integration-use-cases)
5. [Comparison Matrix](#5-comparison-matrix)
6. [Implementation Strategies](#6-implementation-strategies)
7. [Architecture Diagrams](#7-architecture-diagrams)
8. [Decision Framework](#8-decision-framework)
9. [Migration Paths](#9-migration-paths)
10. [References](#10-references)

---

## 1. Executive Summary

### 1.1 Scope

This document consolidates research on:

- **CLI-based agent platforms**: kilo, roo, OpenCode, Zen, Claude Code, Codex, Cursor Agent
- **Alternative runtimes**: OpenClaw, Agent Zero as potential sitback runtimes
- **Integration strategies**: How these platforms integrate with thegent's MCP server and governance system

### 1.2 Key Findings

**CLI Platforms**:

- kilo, roo: OSS platforms with CLI tools, AI proxies, and agent harnesses
- OpenCode: OSS agent with Zen model routing layer
- All support OpenAI-compatible APIs for CLIProxy integration

**Alternative Runtimes**:

- **Agent Zero**: Lower-friction path (MCP native, SKILL.md compatible, Python stack)
- **OpenClaw**: Richer UX (multi-channel, WebChat) but higher integration effort

**Integration Opportunities**:

- ClawHub: Skill discovery and publishing
- Agent Zero: MCP client integration for workflow tools
- OpenClaw: Limited direct use (consumer-focused, not dev/CLI)

### 1.3 Recommendations

1. **OpenCode + CLIProxy**: Document config for using CLIProxy as OpenCode backend
2. **Agent Zero as Sitback Runtime**: Lower-friction alternative to Claude Code/Codex
3. **ClawHub Publishing**: Publish thegent skills to ClawHub for discoverability
4. **MCP Integration**: Document Agent Zero + thegent MCP setup

---

## 2. CLI-Based Agent Platforms

### 2.1 Platform Overview

| Platform         | Type         | CLI              | AI Proxy             | OSS Harness | MCP Support |
| ---------------- | ------------ | ---------------- | -------------------- | ----------- | ----------- |
| **kilo**         | OSS Platform | `kilo auth`      | `api.kilo.ai/v1`     | ✓           | —           |
| **roo**          | OSS Platform | `roo auth login` | `api.roocode.com/v1` | ✓           | —           |
| **OpenCode**     | OSS Agent    | `opencode`       | Zen, multi-provider  | ✓           | ✓           |
| **Claude Code**  | OSS Agent    | `claude`         | Anthropic            | ✓           | ✓           |
| **Codex**        | OSS Agent    | `codex`          | OpenAI               | ✓           | ✓ (adapter) |
| **Cursor Agent** | IDE Agent    | IDE              | cursor-api           | Partial     | ✓           |

### 2.2 kilo (Kilo.ai)

**Architecture**:

- **AI Proxy**: `https://api.kilo.ai/v1` — OpenAI-compatible model API
- **OSS Harness**: CLI + agent runner (like Claude Code, Codex) — runs agents with tools
- **CLI**: `kilo auth` — interactive wizard
- **Credentials**: `~/.kilocode/cli/` or `~/.kilo/token.json`
- **thegent Integration**: Provider via CLIProxyAPIPlus; `thegent run kilo "..."`; `thegent cliproxy login kilo`
- **Features**: Model catalog, agent routing; harness provides search and tool execution

**Usage**:

```bash
# Login
thegent cliproxy login kilo

# Run agent
thegent run kilo "Build a REST API"
```

### 2.3 roo (Roo Code Cloud)

**Architecture**:

- **AI Proxy**: `https://api.roocode.com/v1` — OpenAI-compatible model API
- **OSS Harness**: CLI + agent runner — runs agents with tools
- **CLI**: `roo auth login` — OAuth flow
- **Credentials**: `~/.config/roo/credentials.json`
- **thegent Integration**: Provider via CLIProxyAPIPlus; `thegent run roo "..."`; `thegent cliproxy login roo`
- **Features**: Model catalog, agent routing; harness provides search and tool execution

**Usage**:

```bash
# Login
thegent cliproxy login roo

# Run agent
thegent run roo "Refactor this code"
```

### 2.4 OpenCode (opencode.ai)

**Architecture**:

- **Type**: OSS AI coding agent (terminal, IDE, desktop)
- **CLI**: `opencode` — `npm install -g opencode`; similar to Claude Code
- **Zen**: Curated free/paid models for coding agents; pay-per-request; works with any agent
- **Config**: `.opencode/` — commands, instructions, plugins, prompts, tools
- **ECC Support**: everything-claude-code has `.opencode/` plugin (v1.3.0); 12 agents, 24 commands, 16 skills
- **API**: OpenCode SDK; server on port 4096; supports Anthropic, OpenAI, Google, etc.

**OpenCode Zen**:

- Handpicked models for coding agents
- Transparent pricing
- Can be used with OpenCode or any agent
- Zen is a **model routing layer**, not a separate CLI

**thegent Integration**:

```bash
# Configure OpenCode to use CLIProxy
export OPENAI_BASE_URL=http://127.0.0.1:8317/v1
export OPENAI_API_KEY=sk-dummy

# Run OpenCode (will use CLIProxy providers)
opencode
```

### 2.5 Claude Code

**Architecture**:

- **CLI**: `claude` — Anthropic
- **Tools**: read_file, write, edit, grep, glob, bash, MCP
- **Config**: `~/.claude/`, `.claude/`; plugins, skills, hooks, rules
- **MCP**: Native support (stdio/HTTP)
- **thegent Integration**: Via `clode` shim; `thegent sitback` uses Claude Code

**Usage**:

```bash
# Run sitback with Claude Code
thegent sitback

# Or explicitly
thegent sitback --runtime claude
```

### 2.6 Codex (OpenAI)

**Architecture**:

- **CLI**: `codex exec`, `codex run` — OpenAI Codex CLI
- **API**: Responses API (HTTP + WebSocket); Chat Completions fallback
- **thegent**: CodexProxyRunner; adapter bridges Responses ↔ Chat for CLIProxy
- **Tools**: Server-side tool execution; sandbox modes (workspace-write, full-auto)
- **MCP**: Via adapter

**Usage**:

```bash
# Run sitback with Codex
thegent sitback --dex

# Or explicitly
thegent sitback --runtime codex
```

### 2.7 Cursor Agent

**Architecture**:

- **Context**: Cursor IDE built-in agent
- **API**: cursor-api (wisdgod) — OpenAI-compatible; `/v1/models`, chat
- **Tools**: @codebase, semantic search, terminal, edit
- **thegent**: CursorApiRunner; routes to cursor-api when configured
- **MCP**: Partial support

**Usage**:

```bash
# Configure cursor-api
export CURSOR_API_URL=http://127.0.0.1:8080

# Use via Cursor IDE
# (Built into IDE, not CLI-driven)
```

### 2.8 OpenCode Zen + CLIProxyAPI Integration

**Goal**: Enable OpenCode Zen (and OpenCode generally) to use CLIProxyAPIPlus as a backend, so users can route OpenCode through thegent's proxy (minimax, glm, kilo, roo, antigravity, etc.) instead of or in addition to Zen's native models.

**Current Architecture**:

```
OpenCode CLI → OpenCode SDK (port 4096) → Zen / Anthropic / OpenAI / ...
thegent      → CLIProxyAPIPlus (port 8317) → minimax, glm, kilo, roo, ...
```

**Integration Options**:

| Option                          | Description                                                                                      | Effort                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------- |
| **A. OpenCode custom provider** | Configure OpenCode to use `OPENAI_BASE_URL=http://127.0.0.1:8317/v1` + `OPENAI_API_KEY=sk-dummy` | Low — config only           |
| **B. Zen bypass**               | Use OpenCode with custom provider URL pointing to CLIProxy; Zen becomes optional                 | Low                         |
| **C. CLIProxy Zen block**       | Add Zen as a provider block in CLIProxy config (if Zen exposes OpenAI-compatible API)            | Medium — depends on Zen API |
| **D. thegent OpenCode runner**  | thegent `run opencode "..."` that launches OpenCode with env pointing to proxy                   | Medium                      |

**Recommended: Option A (Config)**

```bash
# 1. Start CLIProxy
thegent cliproxy start
# or: THGENT_CLIPROXY_ADAPTER=1 thegent mcp up

# 2. Configure OpenCode to use CLIProxy
export OPENAI_BASE_URL=http://127.0.0.1:8317/v1
export OPENAI_API_KEY=sk-dummy

# 3. Run OpenCode (will use CLIProxy providers)
opencode
```

Or via OpenCode config (`.opencode/opencode.json` or equivalent) — add provider with `base_url: http://127.0.0.1:8317/v1`.

**GoZen Relevance**:

- **GoZen** (dopejs/GoZen) — Multi-CLI switcher for Claude Code, Codex, OpenCode with API proxy auto-failover
- Supports: `zen --cli opencode` — Launch OpenCode
- Provider config with `base_url` — Can point to CLIProxy
- Scenario routing (think, image, longContext, webSearch)

**Action**: Document GoZen + CLIProxy as alternative to manual env; or add thegent-specific zen profile.

---

## 3. OpenClaw & Agent Zero Evaluation

### 3.1 Current State (Sitback)

| Component        | Implementation                                                                                        |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| **Runtime**      | Claude Code (via `clode`) or Codex (via `--dex`)                                                      |
| **Launch**       | `thegent sitback` → `_run_sitback_claude` / `_run_sitback_codex`                                      |
| **Skill**        | `skills/sitback-agent/SKILL.md` → `~/.claude/skills/sitback-agent`                                    |
| **MCP**          | `thegent serve` (prerequisite); tools: `thegent_sitback_dashboard`, `thegent_run`, `thegent_bg`, etc. |
| **Chat surface** | Claude Code IDE or Codex IDE                                                                          |

**Pain Points**:

- **IDE lock-in**: Claude Code / Codex are vendor-specific; crashes lose context
- **Session fragmentation**: Multiple Claude Code instances; no unified chat across sessions
- **Setup complexity**: clode shim, codex, MCP, skill install, provider auth
- **Robustness**: IDE can hang or crash; no always-on gateway

### 3.2 Proposed: OpenClaw or Agent Zero as Main Agent

**Idea**: Replace Claude Code / Codex as the sitback runtime with OpenClaw or Agent Zero. User chats via Web UI or CLI; the agent connects to thegent MCP and runs sitback skill.

### 3.3 Capability Mapping

| Sitback capability | Claude Code / Codex | OpenClaw                                  | Agent Zero            |
| ------------------ | ------------------- | ----------------------------------------- | --------------------- |
| **Chat interface** | IDE chat            | WebChat, CLI (`openclaw agent --message`) | Web UI, terminal      |
| **MCP client**     | Native (stdio/HTTP) | Pi agent → MCP?                           | Native (MCP client)   |
| **Skill loading**  | `~/.claude/skills/` | OpenClaw skills (ClawHub)                 | SKILL.md (compatible) |
| **Tool calling**   | Full                | Pi agent tool streaming                   | Full                  |
| **Always-on**      | No (IDE session)    | Yes (Gateway daemon)                      | Yes (Docker/process)  |
| **Session chat**   | Per-IDE             | Gateway sessions                          | Per-chat              |
| **Multi-channel**  | No                  | WhatsApp, Telegram, WebChat, etc.         | No (Web + terminal)   |

### 3.4 OpenClaw as Main Agent

**Architecture**:

```
User → OpenClaw WebChat / openclaw agent --message "status"
         ↓
OpenClaw Gateway (ws://127.0.0.1:18789)
         ↓
Pi agent (RPC) + sitback skill
         ↓
thegent MCP (thegent serve) — thegent_sitback_dashboard, thegent_run, etc.
```

**Pros**:

- WebChat = unified chat; no IDE
- Gateway = always-on; survives IDE crashes
- Multi-channel (optional): WhatsApp, Telegram for "status" from phone
- `openclaw agent --message "garden"` = simple CLI
- ClawHub = skill discovery

**Cons**:

- OpenClaw is Node/TypeScript; thegent is Python
- Pi agent tool-calling semantics may differ from Claude Code
- Skill format: OpenClaw skills vs thegent SKILL.md — need adapter
- OpenClaw sessions ≠ thegent run_registry sessions; mapping required

**Gaps to close**:

1. Pi agent must call thegent MCP tools (HTTP/stdio).
2. Sitback skill must be adapted for OpenClaw skill format.
3. `thegent sitback` → `openclaw gateway` + `openclaw agent` (or equivalent).

### 3.5 Agent Zero as Main Agent

**Architecture**:

```
User → Agent Zero Web UI / terminal
         ↓
Agent Zero (Python, Docker)
         ↓
MCP client → thegent MCP (thegent serve)
         ↓
Sitback skill (SKILL.md) loaded into Agent Zero
```

**Pros**:

- MCP client native; well-documented
- SKILL.md compatible (same format as thegent)
- Python stack; closer to thegent
- Docker = portable, reproducible
- Web UI = chat; terminal = streaming

**Cons**:

- Agent Zero is general-purpose; sitback is specialized (dashboard, never-idle, gardening)
- May need custom system prompt / skill to enforce sitback behavior
- Agent Zero subagents ≠ thegent sessions; different coordination model

**Gaps to close**:

1. Agent Zero MCP config: add thegent server URL.
2. Sitback skill: ensure SKILL.md works in Agent Zero context.
3. `thegent sitback` → launch Agent Zero with sitback skill + thegent MCP.

### 3.6 Comparison: OpenClaw vs Agent Zero

| Criterion               | OpenClaw                                        | Agent Zero                                      |
| ----------------------- | ----------------------------------------------- | ----------------------------------------------- |
| **Skill format**        | OpenClaw-specific; may need adapter             | SKILL.md (compatible)                           |
| **MCP**                 | Pi agent; MCP support TBD                       | MCP client native                               |
| **Stack**               | Node/TS                                         | Python                                          |
| **Always-on**           | Gateway daemon                                  | Docker/process                                  |
| **Chat**                | WebChat, multi-channel                          | Web UI, terminal                                |
| **Sitback fit**         | Gateway + skills; good for "chat with sessions" | MCP + skills; good for tool-heavy orchestration |
| **Effort to integrate** | Medium–high (skill adapter, Pi↔MCP)            | Low–medium (MCP config, skill load)             |

**Recommendation**: Agent Zero is the lower-friction path (MCP native, SKILL.md compatible). OpenClaw offers richer UX (multi-channel, WebChat) but requires more integration work.

---

## 4. Integration Use Cases

### 4.1 ClawHub — Skill Discovery / Publishing

**Idea**: Publish thegent skills to ClawHub; optionally pull skills from ClawHub.

| Action                                                  | Effort | Value                                         |
| ------------------------------------------------------- | ------ | --------------------------------------------- |
| Publish `agent-orchestra`, `sitback-agent` to ClawHub   | Low    | Discoverability for OpenClaw/Agent Zero users |
| Add `thegent skill install clawhub:<name>` (or similar) | Medium | Pull community skills into thegent            |
| Verify ClawHub skill format vs thegent SKILL.md         | Low    | Prerequisite for above                        |

**Next steps**:

1. Inspect ClawHub skill bundle format (e.g. `npx clawhub install sonoscli` output).
2. Compare with `skills/agent-orchestra/SKILL.md` structure.
3. If compatible, document publish flow; consider CLI integration.

### 4.2 Agent Zero — MCP Integration

**Idea**: Agent Zero connects to thegent MCP server; uses workflow tools.

| thegent MCP Tool                | Agent Zero Use                            |
| ------------------------------- | ----------------------------------------- |
| `thegent_do_next`               | Get next actionable item from WORK_STREAM |
| `thegent_run` / `thegent_bg`    | Execute task via thegent routing          |
| `thegent_memory_add`            | Record observations into audit log        |
| `thegent_memory_scrape_session` | Ingest user prompts/intents               |

**Flow**:

```
Agent Zero agent
  → connects to thegent MCP (thegent serve)
  → calls thegent_do_next
  → receives prompt_suggestion
  → calls thegent_run with suggestion
  → or executes locally and reports via thegent_memory_add
```

**Next steps**:

1. Document "Agent Zero + thegent" setup in `docs/guides/` or `docs/reference/`.
2. Provide example Agent Zero config to add thegent MCP server.
3. Optional: Add Agent Zero to `docs/reference/TOUCHPOINT_INTEGRATION_DEEP_DIVE.md`.

### 4.3 OpenClaw — Limited Direct Use

**Idea**: OpenClaw Pi agent could call thegent for governance.

| Consideration  | Assessment                                          |
| -------------- | --------------------------------------------------- |
| OpenClaw focus | Consumer channels (WhatsApp, Telegram); not dev/CLI |
| thegent focus  | Governance, hooks, Pareto routing                   |
| Overlap        | Low — different surfaces                            |

**Verdict**: No strong use case. OpenClaw users wanting thegent-style governance would need custom integration; not a natural fit.

### 4.4 What Doesn't Fit thegent's Slice

| Feature                | Why                                                      |
| ---------------------- | -------------------------------------------------------- |
| OpenClaw multi-channel | thegent is CLI/terminal, not messaging                   |
| Agent Zero subagents   | thegent uses WORK_STREAM + DAG, not superior/subordinate |
| OpenClaw Gateway       | thegent has its own MCP server                           |
| Agent Zero memory/RAG  | thegent has `thegent_memory_*`; different design         |

---

## 5. Comparison Matrix

### 5.1 Cross-Platform Parity Matrix

| Feature         | Claude Code | Codex       | Cursor     | OpenCode   | kilo        | roo             |
| --------------- | ----------- | ----------- | ---------- | ---------- | ----------- | --------------- |
| AI proxy        | Anthropic   | OpenAI      | cursor-api | Zen, multi | api.kilo.ai | api.roocode.com |
| OSS harness     | ✓           | ✓           | Partial    | ✓          | ✓           | ✓               |
| CLI             | ✓           | ✓           | IDE        | ✓          | ✓           | ✓               |
| MCP             | ✓           | ✓           | ✓          | ✓          | —           | —               |
| CLIProxy        | ✓           | ✓ (adapter) | —          | Proposed   | ✓           | ✓               |
| Zen             | —           | —           | —          | ✓          | —           | —               |
| Session parsing | ✓           | ✓           | ✓          | ✓          | —           | —               |

### 5.2 Runtime Comparison for Sitback

| Criterion              | Claude Code | Codex    | Agent Zero       | OpenClaw               |
| ---------------------- | ----------- | -------- | ---------------- | ---------------------- |
| **Chat interface**     | IDE         | IDE      | Web UI, terminal | WebChat, multi-channel |
| **MCP support**        | Native      | Adapter  | Native           | TBD                    |
| **Skill format**       | SKILL.md    | SKILL.md | SKILL.md         | OpenClaw-specific      |
| **Always-on**          | No          | No       | Yes              | Yes                    |
| **Stack**              | Python      | Python   | Python           | Node/TS                |
| **Setup complexity**   | Medium      | Medium   | Low–medium       | Medium–high            |
| **Integration effort** | Low         | Low      | Low–medium       | Medium–high            |

---

## 6. Implementation Strategies

### 6.1 Phase 1: Agent Zero as Optional Sitback Runtime

1. **Document** Agent Zero + thegent MCP setup.
2. **Add** `thegent sitback --agent-zero` (or `--runtime agent-zero`):
   - Ensure `thegent serve` running
   - Launch Agent Zero with thegent MCP URL + sitback skill path
   - User chats via Agent Zero Web UI
3. **Validate** sitback skill in Agent Zero (dashboard, never-idle, gardening).

### 6.2 Phase 2: OpenClaw as Optional Runtime (If Desired)

1. **Verify** OpenClaw Pi agent MCP client support.
2. **Adapt** sitback skill for OpenClaw format (or bridge).
3. **Add** `thegent sitback --openclaw`:
   - Ensure OpenClaw Gateway running
   - Ensure thegent MCP reachable from Gateway
   - Load sitback skill into Pi agent

### 6.3 Phase 3: Unified "Chat with Sessions"

Both runtimes could support:

- **Session list** — `thegent_sitback_dashboard` → sessions, terminals, cockpit
- **Send to session** — `thegent_run`, `thegent_bg`, `thegent_loop_takeover`
- **Wait on session** — `thegent_wait`
- **Gardening** — `thegent_do_next`, `thegent govern go health`, etc.

"Chatting with sessions" = user says "status" → dashboard; "run X" → thegent_run; "garden" → gardening loop.

### 6.4 Implementation Tasks

| Task                                                      | Effort            | Owner |
| --------------------------------------------------------- | ----------------- | ----- |
| Document OpenCode + CLIProxy in PROVIDER_SETUP_GUIDE      | 1–2 edits         | —     |
| Add OpenCode Zen section: when to use Zen vs CLIProxy     | 1–2 edits         | —     |
| Document Agent Zero + thegent MCP setup                   | 2–4 edits         | —     |
| Add `thegent sitback --agent-zero` command                | 8–12 tool calls   | —     |
| Verify ClawHub skill format compatibility                 | Manual inspection | —     |
| Publish agent-orchestra to ClawHub (if format OK)         | clawhub.ai        | —     |
| Optional: thegent opencode runner (launch with proxy env) | 8–12 tool calls   | —     |
| Optional: GoZen profile for thegent/CLIProxy              | 2–4 edits         | —     |

---

## 7. Architecture Diagrams

### 7.1 Agent Zero + thegent Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT ZERO + THEGENT INTEGRATION                          │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                              ┌──────────────────┐
    │    User          │                              │   thegent        │
    │  (Browser/Term)  │                              │   MCP Server     │
    └────────┬─────────┘                              │   (port 3847)    │
             │                                        └─────────┬────────┘
             │                                                  │
             │                                          ┌───────┴───────┐
             │                                          │               │
             ▼                                          ▼               ▼
    ┌──────────────────┐                    ┌─────────────────────────────┐
    │  Agent Zero      │                    │   thegent_sitback_dashboard │
    │  Docker Container │                    │   thegent_run              │
    │  ┌────────────┐ │                    │   thegent_bg               │
    │  │ MCP Client  │ │◄──────────────────│   thegent_loop_takeover    │
    │  │ (config)    │ │                    │   thegent_do_next         │
    │  └────────────┘ │                    │   ...                     │
    │         │       │                    └─────────────────────────────┘
    │         │       │
    │         ▼       │
    │  ┌────────────┐ │
    │  │  Sitback    │ │
    │  │  Skill      │ │                    ┌─────────────────────────────┐
    │  │ (SKILL.md)  │ │                    │   run_registry.jsonl       │
    │  └────────────┘ │                    │   WORK_STREAM.md           │
    │         │       │                    │   session artifacts         │
    │         │       │                    └─────────────────────────────┘
    └─────────┼───────┘
              │
              │ HTTP/RPC
              │
              ▼
    ┌──────────────────┐
    │  Agent Zero      │
    │  Web UI / CLI    │
    └──────────────────┘
```

### 7.2 OpenClaw + thegent Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPENCLAW + THEGENT INTEGRATION                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                              ┌──────────────────┐
    │    User          │                              │   thegent        │
    │  (WebChat/CLI)   │                              │   MCP Server     │
    └────────┬─────────┘                              └─────────┬────────┘
             │                                                  │
             │ HTTP/WS                                           │
             │ (ws://127.0.0.1:18789)                           │
             │                                                  │
             ▼                                                  │
    ┌──────────────────┐                    ┌─────────────────────────────┐
    │  OpenClaw        │                    │   thegent MCP Tools         │
    │  Gateway Daemon  │                    │   (same as Agent Zero)      │
    │  ┌────────────┐ │◄──────────────────┐                             │
    │  │ Pi Agent   │ │                   │                             │
    │  │ (RPC)      │ │                   │                             │
    │  └────────────┘ │                   └─────────────────────────────┘
    │         │       │
    │         │       │                    ┌─────────────────────────────┐
    │         ▼       │                    │   ClawHub Skills           │
    │  ┌────────────┐ │                    │   Sitback Bridge           │
    │  │ Sitback    │ │                    │   (OpenClaw format)       │
    │  │ Bridge     │ │                    └─────────────────────────────┘
    │  │ (Adapter)  │ │
    │  └────────────┘ │
    │         │       │
    └─────────┼───────┘
              │
              │ MCP (HTTP/WS)
              │
              ▼
    ┌──────────────────┐
    │  thegent MCP     │
    │  (thegent serve) │
    └──────────────────┘
```

### 7.3 Unified "Chat with Sessions" Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED CHAT WITH SESSIONS FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────┐
    │                         USER INTERACTION                               │
    └──────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  "status"   │ │  "run X"   │ │  "garden"  │
            └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                   │               │               │
                   ▼               ▼               ▼
            ┌─────────────────────────────────────────────────────────────┐
            │              NATURAL LANGUAGE INTERPRETER                    │
            │  ┌─────────────────────────────────────────────────────┐   │
            │  │ Intent: {session_list, run_task, gardening, etc.}  │   │
            │  └─────────────────────────────────────────────────────┘   │
            └───────────────────────────┬─────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │ thegent_     │   │ thegent_run │   │ thegent_    │
            │ sitback_     │   │ --prompt    │   │ do_next     │
            │ dashboard    │   │ "X" --bg   │   │             │
            └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
                   │                 │                 │
                   └─────────────────┼─────────────────┘
                                     │
                                     ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                    SESSION ORCHESTRATOR                     │
            │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │
            │  │ sessions  │ │ terminals │ │  cockpit  │ │  agents   │ │
            │  │ list      │ │  attach   │ │  view     │ │  control  │ │
            │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ │
            └─────────────────────────────────────────────────────────────┘
```

### 7.4 Runtime Selection Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RUNTIME SELECTION DECISION TREE                           │
└─────────────────────────────────────────────────────────────────────────────┘

                            ┌─────────────────┐
                            │ User runs       │
                            │ "thegent        │
                            │  sitback"       │
                            └────────┬────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │ --runtime flag? │                │
                    └────────────────┘                │
                             │                       │
              ┌──────────────┼──────────────┐       │
              │ agent-zero    │ openclaw      │ clode │ codex
              └──────────────┴──────────────┘       │
                             │                       │
                             ▼                       ▼
                    ┌─────────────────┐   ┌─────────────────┐
                    │ Docker + MCP    │   │ Native IDE      │
                    │ config exists?  │   │ (Claude/Codex)  │
                    └────────┬────────┘   └────────┬────────┘
                             │                     │
              ┌──────────────┼──────────────┐       │
              │ YES          │ NO            │       │
              └──────────────┴──────────────┘       │
                             │                       │
                             ▼                       ▼
                    ┌─────────────────┐   ┌─────────────────┐
                    │ Launch Agent    │   │ Fallback to     │
                    │ Zero container  │   │ default (clode) │
                    │ with sitback    │   │                 │
                    │ skill           │   │                 │
                    └─────────────────┘   └─────────────────┘
```

---

## 8. Decision Framework

### 8.1 When to Use Each Platform

**Use kilo/roo when**:

- You need model catalog and routing
- You want OSS harness with agent execution
- You prefer OpenAI-compatible API

**Use OpenCode when**:

- You want Zen model routing layer
- You need `.opencode/` config flexibility
- You want ECC plugin compatibility

**Use Agent Zero when**:

- You want always-on sitback runtime
- You prefer MCP-native integration
- You want SKILL.md compatibility
- You prefer Python stack

**Use OpenClaw when**:

- You want multi-channel support (WhatsApp, Telegram)
- You want WebChat interface
- You need Gateway daemon for always-on

**Use Claude Code/Codex when**:

- You prefer IDE-based chat
- You want native MCP support
- You're comfortable with vendor-specific tools

### 8.2 Integration Priority

1. **High Priority**: Agent Zero + thegent MCP (low-friction, native support)
2. **Medium Priority**: OpenCode + CLIProxy (config-based, easy)
3. **Low Priority**: OpenClaw + thegent (higher effort, limited use case)
4. **Ongoing**: ClawHub skill publishing (discoverability)

---

## 9. Migration Paths

### 9.1 From Claude Code/Codex to Agent Zero

**Steps**:

1. Install Agent Zero (Docker or local)
2. Configure Agent Zero MCP client to point to `thegent serve`
3. Copy sitback skill to Agent Zero skills directory
4. Test `thegent sitback --agent-zero`
5. Gradually migrate workflows

**Rollback**: Keep `thegent sitback` default as Claude Code; `--agent-zero` is opt-in

### 9.2 From OpenCode Zen to CLIProxy

**Steps**:

1. Start `thegent cliproxy start`
2. Set `OPENAI_BASE_URL=http://127.0.0.1:8317/v1`
3. Set `OPENAI_API_KEY=sk-dummy`
4. Run `opencode` (will use CLIProxy)
5. Verify provider routing

**Rollback**: Unset env vars; OpenCode falls back to Zen

### 9.3 Publishing Skills to ClawHub

**Steps**:

1. Verify ClawHub skill format compatibility
2. Package thegent skill (agent-orchestra, sitback-agent)
3. Publish to ClawHub via `npx clawhub publish`
4. Document in thegent docs
5. Optional: Add `thegent skill install clawhub:<name>`

---

## 10. References

### 10.1 Platform Documentation

- **kilo**: https://kilo.ai
- **roo**: https://roocode.com
- **OpenCode**: https://opencode.ai
- **OpenClaw**: https://github.com/openclaw/openclaw
- **ClawHub**: https://clawhub.ai
- **Agent Zero**: https://github.com/agent0ai/agent-zero
- **Agent Zero Docs**: https://www.agent-zero.ai/p/docs/get-started/

### 10.2 Related thegent Documentation

- [Provider Setup Guide](../guides/PROVIDER_SETUP_GUIDE.md) - kilo, roo, CLIProxy login
- [Agent Access and Optimization Audit Plan](./AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) - File/web/batch audit
- [Codex Minimax CLIProxy Research](./CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md) - Codex + CLIProxy adapter
- [Unified System Application Plan](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md) - TUI/compositor research
- [Sitback Design Plan](../plans/2026-02-15-thegent-sitback-design.md) - Sitback architecture

### 10.3 Implementation Files

- **thegent MCP**: `src/thegent/mcp_server.py`, `src/thegent/mcp_sitback.py`
- **thegent skills**: `skills/agent-orchestra/`, `skills/sitback-agent/`
- **CLIProxy**: `src/thegent/cli_proxy.py`
- **Agent runners**: `src/thegent/runners/`

---

## 11. Summary

### 11.1 Key Takeaways

1. **CLI Platforms**: kilo, roo, OpenCode all support OpenAI-compatible APIs for CLIProxy integration
2. **Alternative Runtimes**: Agent Zero offers lower-friction path; OpenClaw offers richer UX
3. **Integration**: Agent Zero MCP integration is highest priority; ClawHub publishing is ongoing
4. **Migration**: Gradual migration paths exist; rollback options maintained

### 11.2 Next Steps

1. Document Agent Zero + thegent MCP setup
2. Add `thegent sitback --agent-zero` command
3. Document OpenCode + CLIProxy configuration
4. Verify ClawHub skill format compatibility
5. Publish thegent skills to ClawHub

### 11.3 Impact

- **Reliability**: Agent Zero always-on runtime improves sitback robustness
- **Flexibility**: OpenCode + CLIProxy enables provider routing
- **Discoverability**: ClawHub publishing increases skill visibility
- **Integration**: MCP-native support simplifies workflow integration

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md](./AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) - Audit plan
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

_Generated: 2026-02-16 | Version: 1.0 | Status: Complete_

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md](./AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md) - Platform research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

## Platform Selection Criteria

| Criterion            | Prefer Agent Zero               | Prefer OpenCode + CLIProxy         | Prefer OpenClaw/ClawHub          |
| -------------------- | ------------------------------- | ---------------------------------- | -------------------------------- |
| Runtime reliability  | Always-on autonomous sessions   | Strong when proxy is stable        | Depends on desktop/browser stack |
| Integration priority | Native MCP workflows            | OpenAI-compatible provider routing | Skill distribution and discovery |
| Setup effort         | Moderate (runtime + MCP config) | Low (env vars + proxy endpoint)    | Moderate-high (UX + packaging)   |
| Best fit             | Sitback automation              | Multi-provider CLI execution       | Team-facing skill sharing        |

## Adoption Sequence

- Start with Agent Zero + thegent MCP for durable, always-on sitback runs.
- Add OpenCode + CLIProxy for provider routing and model flexibility.
- Publish core skills to ClawHub after format and metadata validation.
- Keep Claude Code as default until Agent Zero path is fully verified in daily workflows.

## Platform Capability Baseline

| Capability                  | Agent Zero                           | OpenCode + CLIProxy                         | OpenClaw/ClawHub                          |
| --------------------------- | ------------------------------------ | ------------------------------------------- | ----------------------------------------- |
| Always-on execution         | Strong baseline (persistent runtime) | Session-based baseline                      | Varies by host UX/runtime                 |
| MCP workflow fit            | Native-first baseline                | Works via proxy + API compatibility         | Strong for skill consumption/distribution |
| Provider/model routing      | Limited relative flexibility         | Strong baseline (OpenAI-compatible routing) | Medium; depends on configured backend     |
| Operational maturity target | Long-running sitback automation      | Multi-provider CLI operations               | Team skill catalog and reuse              |

## Integration Cost Bands

| Platform path                 | Initial setup cost | Ongoing ops cost | Recommended use point                          |
| ----------------------------- | ------------------ | ---------------- | ---------------------------------------------- |
| Agent Zero + thegent MCP      | Medium             | Low-Medium       | First for reliability-critical autonomous runs |
| OpenCode + CLIProxy           | Low                | Medium           | Add when provider switching is a priority      |
| OpenClaw + ClawHub publishing | Medium-High        | Medium           | Add after core skills are stable and reusable  |

## Vendor Lock-In Signals

- **API portability**: Count OpenAI-only endpoints and proprietary SDK assumptions; fewer assumptions means easier platform exit.
- **Workflow coupling**: Flag hard dependencies on platform-specific runtimes, auth flows, and skill packaging formats.
- **Data gravity**: Compare where prompts, logs, evals, and skill metadata live; exportable storage reduces migration risk.
- **Ops dependencies**: Track critical automations tied to one vendor dashboard or CLI and prioritize neutral interfaces.

## Exit Strategy Checklist

- Maintain a tested second provider path for core agent flows (auth, model calls, tool routing).
- Keep prompts, skills, and policies in repo-controlled formats with conversion scripts where needed.
- Run quarterly migration drills: replay a representative workload on an alternate stack and record gaps.
- Require export coverage for logs, traces, and eval artifacts before expanding vendor-specific features.
- Define rollback thresholds (cost, latency, incident rate, policy changes) that trigger planned migration.

## Platform Onboarding Checklist

- Define target workflow first (autonomous runtime vs provider routing vs skill distribution) and pick Agent Zero, OpenCode + CLIProxy, or OpenClaw/ClawHub accordingly.
- Validate a same-task benchmark across at least two platforms (startup time, tool success rate, operator effort) before standardizing.
- Complete environment readiness gates: auth, MCP/tool connectivity, logging export path, and fallback provider route.
- Run a 1-week pilot with explicit SLOs (success %, median latency, incident count) and require documented rollback steps.
- Promote to default only after runbook, ownership, and cost guardrails are approved.

## Decommission Procedure

- Trigger decommission when rollback thresholds are exceeded (cost, latency, incident rate, policy/compliance change).
- Freeze new feature work on the platform and snapshot critical artifacts (prompts, skills, logs, configs, credential mappings).
- Execute migration cutover in phases: shadow run, limited production slice, then full traffic transfer with daily verification.
- Revoke platform secrets/tokens, remove scheduled jobs/webhooks, and archive dashboards with retention metadata.
- Publish a closure report comparing pre/post KPIs, unresolved gaps, and ownership handoff for the replacement stack.

## Platform SLA Expectations

| SLA dimension            | Agent Zero + thegent MCP                  | OpenCode + CLIProxy                               | OpenClaw/ClawHub                                        |
| ------------------------ | ----------------------------------------- | ------------------------------------------------- | ------------------------------------------------------- |
| Uptime target            | Highest for always-on automation (≥99.9%) | High if proxy/provider redundancy exists (≥99.5%) | Medium-high; depends on host runtime (≥99.0%)           |
| Failover requirement     | Local runtime restart + MCP health checks | Secondary provider route + proxy fallback         | Alternate access path for skill retrieval and execution |
| Incident response target | P1 acknowledgment ≤15 min                 | P1 acknowledgment ≤30 min                         | P1 acknowledgment ≤30 min                               |
| Best workload match      | Reliability-critical autonomous runs      | Multi-provider CLI workloads                      | Skill catalog/distribution workflows                    |

## Portability Verification Steps

- Run the same scripted task on all three paths and compare success rate, median latency, and operator interventions.
- Validate config portability by moving prompts, skills, and policy files without manual rewrites.
- Exercise failover: force primary-path failure and confirm secondary execution within the SLA response window.
- Export logs/traces/artifacts from each platform and verify replayability in a neutral analysis workflow.
- Record blocking deltas (auth, tool compatibility, packaging) and require mitigation owners before defaulting a platform.

## Platform Compliance Checks

- Run a weekly control sweep: access reviews, data-retention policy checks, and audit-log export validation.
- Gate releases on a compliance checklist pass (security controls, policy mappings, incident runbook freshness).
- Require monthly evidence bundles (config snapshots, control test output, exception register) in versioned storage.
- Escalate any failed control within one business day with owner, mitigation, and re-test date.

## Lifecycle Exit Signals

- Trigger exit review after two consecutive SLA misses or repeated P1 incidents in a 30-day window.
- Initiate migration planning when total platform cost exceeds forecast by >20% for two billing cycles.
- Open an exit track immediately for material policy/legal changes that break required compliance posture.
- Start cutover when portability drills fail twice without remediation closure by the committed deadline.

## Platform Change Approval Gates

- Require a written change brief (scope, risk, rollback, owner) before any platform switch enters implementation.
- Enforce a three-check gate: security/compliance sign-off, SRE runbook readiness, and successful portability drill evidence.
- Block production cutover unless pilot SLOs are met for 7 consecutive days with no unresolved Sev-1/Sev-2 incidents.
- Approve only with dated go/no-go notes and explicit rollback trigger thresholds captured in the release record.

## Retirement Readiness Signals

- Mark a platform retirement-ready only after 100% of critical workflows run successfully on the replacement path for 14 days.
- Confirm secret/token revocation plan, data export completion, and audit-log retention mapping before shutdown scheduling.
- Require zero open high-severity defects tagged to the retirement scope and named owners for all medium-severity items.
- Execute a final dry-run decommission checklist and archive signed completion evidence before disabling the old platform.
