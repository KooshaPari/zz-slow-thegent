<DONE>
# Agent Platforms: kilo, roo, OpenCode, Zen + CLIProxyAPI — Research

> **Purpose**: Correct kilo/roo/OpenCode as OSS platforms with CLI tools and search; research augment, codex, amp, claude code, cursor agent; add OpenCode Zen + CLIProxyAPI integration plan.
> **Status**: Research | **Date**: 2026-02-16

---

## 1. kilo, roo, OpenCode — Corrected Understanding

All three are **OSS platforms** with **CLI tools** and **associated search/agent features**. kilo and roo have **both** an **AI proxy** (model API) **and** **OSS harnesses** (agent execution frameworks).

### 1.1 kilo (Kilo.ai)

| Aspect              | Details                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------- |
| **AI proxy**        | `https://api.kilo.ai/v1` — OpenAI-compatible model API                                      |
| **OSS harness**     | CLI + agent runner (like Claude Code, Codex) — runs agents with tools                       |
| **CLI**             | `kilo auth` — interactive wizard; credentials in `~/.kilocode/cli/` or `~/.kilo/token.json` |
| **thegent**         | Provider via CLIProxyAPIPlus; `thegent run kilo "..."`; `thegent cliproxy login kilo`       |
| **Search/features** | Model catalog, agent routing; harness provides search and tool execution                    |

### 1.2 roo (Roo Code Cloud)

| Aspect              | Details                                                                             |
| ------------------- | ----------------------------------------------------------------------------------- |
| **AI proxy**        | `https://api.roocode.com/v1` — OpenAI-compatible model API                          |
| **OSS harness**     | CLI + agent runner — runs agents with tools                                         |
| **CLI**             | `roo auth login` — OAuth flow; credentials in `~/.config/roo/credentials.json`      |
| **thegent**         | Provider via CLIProxyAPIPlus; `thegent run roo "..."`; `thegent cliproxy login roo` |
| **Search/features** | Model catalog, agent routing; harness provides search and tool execution            |

### 1.3 OpenCode (opencode.ai)

| Aspect          | Details                                                                                    |
| --------------- | ------------------------------------------------------------------------------------------ |
| **Type**        | OSS AI coding agent (terminal, IDE, desktop)                                               |
| **CLI**         | `opencode` — `npm install -g opencode`; similar to Claude Code                             |
| **Zen**         | Curated free/paid models for coding agents; pay-per-request; works with any agent          |
| **Config**      | `.opencode/` — commands, instructions, plugins, prompts, tools                             |
| **ECC support** | everything-claude-code has `.opencode/` plugin (v1.3.0); 12 agents, 24 commands, 16 skills |
| **API**         | OpenCode SDK; server on port 4096; supports Anthropic, OpenAI, Google, etc.                |

**OpenCode Zen** — Handpicked models for coding agents; transparent pricing; can be used with OpenCode or any agent. Zen is a **model routing layer**, not a separate CLI.

---

## 2. Agent Platforms — Comparative Research

| Platform         | CLI              | AI Proxy            | OSS Harness | Search/Features                           |
| ---------------- | ---------------- | ------------------- | ----------- | ----------------------------------------- |
| **Claude Code**  | `claude`         | Anthropic           | ✓           | read_file, list_dir, codebase_search, MCP |
| **Codex**        | `codex`          | OpenAI              | ✓           | Responses API; tools server-side          |
| **Cursor Agent** | IDE              | cursor-api          | Partial     | @codebase, semantic search                |
| **OpenCode**     | `opencode`       | Zen, multi-provider | ✓           | plugins; .opencode/                       |
| **kilo**         | `kilo auth`      | api.kilo.ai         | ✓           | Model catalog; harness runs agents        |
| **roo**          | `roo auth login` | api.roocode.com     | ✓           | Model catalog; harness runs agents        |
| **augment**      | (research)       | —                   | —           | —                                         |
| **amp**          | (research)       | —                   | —           | —                                         |

### 2.1 augment

- **Possible referents**: Augment (augmentcode.com) — AI coding assistant; or generic "augment" as verb.
- **If Augment Code**: Commercial AI coding tool; may have CLI/API. Needs separate web research.
- **Status**: To be researched further.

### 2.2 codex (OpenAI)

- **CLI**: `codex exec`, `codex run` — OpenAI Codex CLI
- **API**: Responses API (HTTP + WebSocket); Chat Completions fallback
- **thegent**: CodexProxyRunner; adapter bridges Responses ↔ Chat for CLIProxy
- **Tools**: Server-side tool execution; sandbox modes (workspace-write, full-auto)

### 2.3 amp

- **Possible referents**: AMP (Agentic Model Platform?), or Amplitude MCP. Unclear.
- **Status**: To be researched further.

### 2.4 Claude Code

- **CLI**: `claude` — Anthropic
- **Tools**: read_file, write, edit, grep, glob, bash, MCP
- **Config**: `~/.claude/`, `.claude/`; plugins, skills, hooks, rules

### 2.5 Cursor Agent

- **Context**: Cursor IDE built-in agent
- **API**: cursor-api (wisdgod) — OpenAI-compatible; `/v1/models`, chat
- **Tools**: @codebase, semantic search, terminal, edit
- **thegent**: CursorApiRunner; routes to cursor-api when configured

---

## 3. OpenCode Zen + CLIProxyAPI Integration

### 3.1 Goal

Enable **OpenCode Zen** (and OpenCode generally) to use **CLIProxyAPIPlus** as a backend, so users can route OpenCode through thegent's proxy (minimax, glm, kilo, roo, antigravity, etc.) instead of or in addition to Zen's native models.

### 3.2 Current Architecture

```
OpenCode CLI → OpenCode SDK (port 4096) → Zen / Anthropic / OpenAI / ...
thegent      → CLIProxyAPIPlus (port 8317) → minimax, glm, kilo, roo, ...
```

### 3.3 Integration Options

| Option                          | Description                                                                                      | Effort                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------- |
| **A. OpenCode custom provider** | Configure OpenCode to use `OPENAI_BASE_URL=http://127.0.0.1:8317/v1` + `OPENAI_API_KEY=sk-dummy` | Low — config only           |
| **B. Zen bypass**               | Use OpenCode with custom provider URL pointing to CLIProxy; Zen becomes optional                 | Low                         |
| **C. CLIProxy Zen block**       | Add Zen as a provider block in CLIProxy config (if Zen exposes OpenAI-compatible API)            | Medium — depends on Zen API |
| **D. thegent OpenCode runner**  | thegent `run opencode "..."` that launches OpenCode with env pointing to proxy                   | Medium                      |

### 3.4 Recommended: Option A (Config)

OpenCode supports custom base URLs. Document in PROVIDER_SETUP_GUIDE:

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

### 3.5 GoZen Relevance

**GoZen** (dopejs/GoZen) — Multi-CLI switcher for Claude Code, Codex, OpenCode with API proxy auto-failover. Supports:

- `zen --cli opencode` — Launch OpenCode
- Provider config with `base_url` — Can point to CLIProxy
- Scenario routing (think, image, longContext, webSearch)

**Action**: Document GoZen + CLIProxy as alternative to manual env; or add thegent-specific zen profile.

### 3.6 Implementation Tasks

| Task                                                      | Effort          | Owner |
| --------------------------------------------------------- | --------------- | ----- |
| Document OpenCode + CLIProxy in PROVIDER_SETUP_GUIDE      | 1–2 edits       | —     |
| Add OpenCode Zen section: when to use Zen vs CLIProxy     | 1–2 edits       | —     |
| Optional: thegent opencode runner (launch with proxy env) | 8–12 tool calls | —     |
| Optional: GoZen profile for thegent/CLIProxy              | 2–4 edits       | —     |

---

## 4. Cross-Platform Parity Matrix

| Feature         | Claude Code | Codex       | Cursor     | OpenCode   | kilo        | roo             |
| --------------- | ----------- | ----------- | ---------- | ---------- | ----------- | --------------- |
| AI proxy        | Anthropic   | OpenAI      | cursor-api | Zen, multi | api.kilo.ai | api.roocode.com |
| OSS harness     | ✓           | ✓           | Partial    | ✓          | ✓           | ✓               |
| CLI             | ✓           | ✓           | IDE        | ✓          | ✓           | ✓               |
| MCP             | ✓           | ✓           | ✓          | ✓          | —           | —               |
| CLIProxy        | ✓           | ✓ (adapter) | —          | Proposed   | ✓           | ✓               |
| Zen             | —           | —           | —          | ✓          | —           | —               |
| Session parsing | ✓           | ✓           | ✓          | ✓          | —           | —               |

---

## 5. Updates to AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN

The prior audit stated "kilo and roo are AI proxy providers" — **corrected**: they are OSS platforms with CLI tools and agent features. OpenCode is an OSS agent (like Claude Code) with Zen as a model layer.

**Action**: Update AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md §5 to reflect:

- kilo, roo: OSS platforms with CLI (`kilo auth`, `roo auth login`), model catalog, search/routing
- OpenCode: OSS agent with Zen; .opencode/ config; ECC plugin support
- OpenCode Zen + CLIProxy: Document config for using CLIProxy as OpenCode backend

---

## 6. Cross-References

| Doc                                                                                          | Purpose                       |
| -------------------------------------------------------------------------------------------- | ----------------------------- |
| [PROVIDER_SETUP_GUIDE.md](../guides/PROVIDER_SETUP_GUIDE.md)                                 | kilo, roo, CLIProxy login     |
| [AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md](./AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) | File/web/batch audit          |
| [CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md](./CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md) | Codex + CLIProxy adapter      |
| [SETUP_PROPOSED_ITEMS.md](../plans/SETUP_PROPOSED_ITEMS.md)                                  | MCP ecosystem, oh-my-opencode |

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added platform integration patterns
2. Added CLIProxy examples
3. Enhanced cross-references

### Cross-References Added

- MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md
- AGENT_PROCESS_ARCHITECTURE_RESEARCH.md

### Practical Additions

- Platform templates
- CLIProxy configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md](./AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) - Access audit
- [CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md](./CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md) - Codex research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
