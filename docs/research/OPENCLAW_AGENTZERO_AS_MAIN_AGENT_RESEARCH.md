<DONE>
# OpenClaw / Agent Zero as Main Agent — Research

**Purpose:** Evaluate OpenClaw or Agent Zero as thegent's primary agent runtime so that chatting with sessions and advanced sitback (dashboard, never-idle, gardening) becomes easier and more robust.

**Date:** 2026-02-16
**Status:** Research
**Related:** `docs/plans/2026-02-15-thegent-sitback-design.md`, `docs/research/OPENCLAW_CLAWHUB_AGENTZERO_USE_CASES.md`

---

## 1. Current State

### 1.1 Sitback Today

| Component        | Implementation                                                                                        |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| **Runtime**      | Claude Code (via `clode`) or Codex (via `--dex`)                                                      |
| **Launch**       | `thegent sitback` → `_run_sitback_claude` / `_run_sitback_codex`                                      |
| **Skill**        | `skills/sitback-agent/SKILL.md` → `~/.claude/skills/sitback-agent`                                    |
| **MCP**          | `thegent serve` (prerequisite); tools: `thegent_sitback_dashboard`, `thegent_run`, `thegent_bg`, etc. |
| **Chat surface** | Claude Code IDE or Codex IDE                                                                          |

### 1.2 Pain Points (Implied)

- **IDE lock-in:** Claude Code / Codex are vendor-specific; crashes lose context
- **Session fragmentation:** Multiple Claude Code instances; no unified chat across sessions
- **Setup complexity:** clode shim, codex, MCP, skill install, provider auth
- **Robustness:** IDE can hang or crash; no always-on gateway

---

## 2. Proposed: OpenClaw or Agent Zero as Main Agent

**Idea:** Replace Claude Code / Codex as the sitback runtime with OpenClaw or Agent Zero. User chats via Web UI or CLI; the agent connects to thegent MCP and runs sitback skill.

### 2.1 Capability Mapping

| Sitback capability | Claude Code / Codex | OpenClaw                                  | Agent Zero            |
| ------------------ | ------------------- | ----------------------------------------- | --------------------- |
| **Chat interface** | IDE chat            | WebChat, CLI (`openclaw agent --message`) | Web UI, terminal      |
| **MCP client**     | Native (stdio/HTTP) | Pi agent → MCP?                           | Native (MCP client)   |
| **Skill loading**  | `~/.claude/skills/` | OpenClaw skills (ClawHub)                 | SKILL.md (compatible) |
| **Tool calling**   | Full                | Pi agent tool streaming                   | Full                  |
| **Always-on**      | No (IDE session)    | Yes (Gateway daemon)                      | Yes (Docker/process)  |
| **Session chat**   | Per-IDE             | Gateway sessions                          | Per-chat              |
| **Multi-channel**  | No                  | WhatsApp, Telegram, WebChat, etc.         | No (Web + terminal)   |

### 2.2 OpenClaw as Main Agent

**Architecture:**

```
User → OpenClaw WebChat / openclaw agent --message "status"
         ↓
OpenClaw Gateway (ws://127.0.0.1:18789)
         ↓
Pi agent (RPC) + sitback skill
         ↓
thegent MCP (thegent serve) — thegent_sitback_dashboard, thegent_run, etc.
```

**Pros:**

- WebChat = unified chat; no IDE
- Gateway = always-on; survives IDE crashes
- Multi-channel (optional): WhatsApp, Telegram for "status" from phone
- `openclaw agent --message "garden"` = simple CLI
- ClawHub = skill discovery

**Cons:**

- OpenClaw is Node/TypeScript; thegent is Python
- Pi agent tool-calling semantics may differ from Claude Code
- Skill format: OpenClaw skills vs thegent SKILL.md — need adapter
- OpenClaw sessions ≠ thegent run_registry sessions; mapping required

**Gaps to close:**

1. Pi agent must call thegent MCP tools (HTTP/stdio).
2. Sitback skill must be adapted for OpenClaw skill format.
3. `thegent sitback` → `openclaw gateway` + `openclaw agent` (or equivalent).

### 2.3 Agent Zero as Main Agent

**Architecture:**

```
User → Agent Zero Web UI / terminal
         ↓
Agent Zero (Python, Docker)
         ↓
MCP client → thegent MCP (thegent serve)
         ↓
Sitback skill (SKILL.md) loaded into Agent Zero
```

**Pros:**

- MCP client native; well-documented
- SKILL.md compatible (same format as thegent)
- Python stack; closer to thegent
- Docker = portable, reproducible
- Web UI = chat; terminal = streaming

**Cons:**

- Agent Zero is general-purpose; sitback is specialized (dashboard, never-idle, gardening)
- May need custom system prompt / skill to enforce sitback behavior
- Agent Zero subagents ≠ thegent sessions; different coordination model

**Gaps to close:**

1. Agent Zero MCP config: add thegent server URL.
2. Sitback skill: ensure SKILL.md works in Agent Zero context.
3. `thegent sitback` → launch Agent Zero with sitback skill + thegent MCP.

---

## 3. Comparison: OpenClaw vs Agent Zero

| Criterion               | OpenClaw                                        | Agent Zero                                      |
| ----------------------- | ----------------------------------------------- | ----------------------------------------------- |
| **Skill format**        | OpenClaw-specific; may need adapter             | SKILL.md (compatible)                           |
| **MCP**                 | Pi agent; MCP support TBD                       | MCP client native                               |
| **Stack**               | Node/TS                                         | Python                                          |
| **Always-on**           | Gateway daemon                                  | Docker/process                                  |
| **Chat**                | WebChat, multi-channel                          | Web UI, terminal                                |
| **Sitback fit**         | Gateway + skills; good for "chat with sessions" | MCP + skills; good for tool-heavy orchestration |
| **Effort to integrate** | Medium–high (skill adapter, Pi↔MCP)            | Low–medium (MCP config, skill load)             |

**Recommendation:** Agent Zero is the lower-friction path (MCP native, SKILL.md compatible). OpenClaw offers richer UX (multi-channel, WebChat) but requires more integration work.

---

## 4. Implementation Path

### 4.1 Phase 1: Agent Zero as Optional Sitback Runtime

1. **Document** Agent Zero + thegent MCP setup.
2. **Add** `thegent sitback --agent-zero` (or `--runtime agent-zero`):
   - Ensure `thegent serve` running
   - Launch Agent Zero with thegent MCP URL + sitback skill path
   - User chats via Agent Zero Web UI
3. **Validate** sitback skill in Agent Zero (dashboard, never-idle, gardening).

### 4.2 Phase 2: OpenClaw as Optional Runtime (If Desired)

1. **Verify** OpenClaw Pi agent MCP client support.
2. **Adapt** sitback skill for OpenClaw format (or bridge).
3. **Add** `thegent sitback --openclaw`:
   - Ensure OpenClaw Gateway running
   - Ensure thegent MCP reachable from Gateway
   - Load sitback skill into Pi agent

### 4.3 Phase 3: Unified "Chat with Sessions"

Both runtimes could support:

- **Session list** — `thegent_sitback_dashboard` → sessions, terminals, cockpit
- **Send to session** — `thegent_run`, `thegent_bg`, `thegent_loop_takeover`
- **Wait on session** — `thegent_wait`
- **Gardening** — `thegent_do_next`, `thegent govern go health`, etc.

"Chatting with sessions" = user says "status" → dashboard; "run X" → thegent_run; "garden" → gardening loop.

---

## 5. Risks and Mitigations

| Risk                                      | Mitigation                                                                  |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| Agent Zero doesn't follow never-idle loop | Strengthen skill instructions; add periodic trigger                         |
| OpenClaw Pi agent tool semantics differ   | Test tool calls; add adapter if needed                                      |
| Session model mismatch                    | thegent sessions = run_registry; map to OpenClaw/Agent Zero chat sessions   |
| User prefers Claude Code                  | Keep `thegent sitback` default as Claude Code; add `--agent-zero` as opt-in |

---

## 6. Use Case Diagrams

### 6.1 Agent Zero Integration Architecture

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

### 6.2 OpenClaw Integration Architecture

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

### 6.3 Unified "Chat with Sessions" Flow

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

### 6.4 Runtime Selection Decision Tree

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

## 7. References

- OpenClaw: https://github.com/openclaw/openclaw
- OpenClaw Pi agent: https://docs.openclaw.ai/concepts/agent
- Agent Zero: https://github.com/agent0ai/agent-zero
- Agent Zero MCP: https://www.agent-zero.ai/p/docs/get-started/
- thegent sitback design: `docs/plans/2026-02-15-thegent-sitback-design.md`
- thegent MCP: `src/thegent/mcp_server.py`, `src/thegent/mcp_sitback.py`

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Use case diagrams (§6)

| Section | Added Content                                                                               |
| ------- | ------------------------------------------------------------------------------------------- |
| §6.1    | Agent Zero + thegent Integration Architecture (Docker container, MCP client, sitback skill) |
| §6.2    | OpenClaw + thegent Integration Architecture (Gateway, Pi agent, sitback bridge adapter)     |
| §6.3    | Unified "Chat with Sessions" Flow (natural language → intent → session orchestrator)        |
| §6.4    | Runtime Selection Decision Tree (--runtime flag, Docker config, fallback)                   |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [OPENCLAW_CLAWHUB_AGENTZERO_USE_CASES.md](./OPENCLAW_CLAWHUB_AGENTZERO_USE_CASES.md) - Use cases
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
