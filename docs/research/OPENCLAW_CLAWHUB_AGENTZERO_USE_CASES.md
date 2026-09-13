<DONE>
# OpenClaw, ClawHub, Agent Zero — Use Cases for thegent

**Purpose:** Research OpenClaw, ClawHub, and Agent Zero for potential integration with thegent's governance/orchestration slice.

**Date:** 2026-02-16
**Status:** Research
**References:** [OpenClaw](https://github.com/openclaw/openclaw), [ClawHub](https://clawhub.ai), [Agent Zero](https://www.agent-zero.ai)

---

## 1. System Overview

| System         | Focus                 | Key Capabilities                                                                                                                |
| -------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **OpenClaw**   | Personal AI assistant | Multi-channel (WhatsApp, Telegram, Slack, Discord, etc.); Gateway WS control plane; Pi agent; SKILL.md skills; ClawHub registry |
| **ClawHub**    | Skill registry        | Publish/browse AgentSkills; versioned like npm; vector search; `npx clawhub install <skill>`                                    |
| **Agent Zero** | Agentic framework     | Multi-agent (superior/subordinate); MCP server+client; SKILL.md; computer-as-tool; memory/RAG; Docker                           |

---

## 2. thegent's Slice (Context)

thegent is an **MCP server + agent hook system** for governing AI agent lifecycle and quality:

- Hooks at lifecycle events (session start, tool use, stop)
- Policy enforcement (cost caps, quality gates, security)
- Pareto routing, spec traceability, workflow triggers
- CLI-driven, terminal-focused orchestration
- MCP tools: `thegent_do_next`, `thegent_run`, `thegent_memory_add`, etc.

---

## 3. Overlap Analysis

### 3.1 Skills (SKILL.md)

- **OpenClaw / Agent Zero:** Both use SKILL.md standard (compatible with Claude Code, Codex, Cursor).
- **thegent:** Uses SKILL.md in `skills/agent-orchestra/`, `skills/sitback-agent/`.
- **ClawHub:** Registry for OpenClaw skills; format may align with SKILL.md.

### 3.2 MCP

- **Agent Zero:** MCP server + client; can connect to external MCP servers as tools.
- **thegent:** MCP server exposing workflow/governance tools.
- **Overlap:** Agent Zero can consume thegent MCP tools.

### 3.3 Orchestration

- **Agent Zero:** Hierarchical (superior/subordinate); task delegation.
- **thegent:** WORK_STREAM + DAG; governance + cost routing.
- **Different models:** Complementary — Agent Zero executes; thegent governs.

---

## 4. Use Cases for thegent

### 4.1 ClawHub — Skill Discovery / Publishing

**Idea:** Publish thegent skills to ClawHub; optionally pull skills from ClawHub.

| Action                                                  | Effort | Value                                         |
| ------------------------------------------------------- | ------ | --------------------------------------------- |
| Publish `agent-orchestra`, `sitback-agent` to ClawHub   | Low    | Discoverability for OpenClaw/Agent Zero users |
| Add `thegent skill install clawhub:<name>` (or similar) | Medium | Pull community skills into thegent            |
| Verify ClawHub skill format vs thegent SKILL.md         | Low    | Prerequisite for above                        |

**Next steps:**

1. Inspect ClawHub skill bundle format (e.g. `npx clawhub install sonoscli` output).
2. Compare with `skills/agent-orchestra/SKILL.md` structure.
3. If compatible, document publish flow; consider CLI integration.

### 4.2 Agent Zero — MCP Integration

**Idea:** Agent Zero connects to thegent MCP server; uses workflow tools.

| thegent MCP Tool                | Agent Zero Use                            |
| ------------------------------- | ----------------------------------------- |
| `thegent_do_next`               | Get next actionable item from WORK_STREAM |
| `thegent_run` / `thegent_bg`    | Execute task via thegent routing          |
| `thegent_memory_add`            | Record observations into audit log        |
| `thegent_memory_scrape_session` | Ingest user prompts/intents               |

**Flow:**

```
Agent Zero agent
  → connects to thegent MCP (thegent serve)
  → calls thegent_do_next
  → receives prompt_suggestion
  → calls thegent_run with suggestion
  → or executes locally and reports via thegent_memory_add
```

**Next steps:**

1. Document "Agent Zero + thegent" setup in `docs/guides/` or `docs/reference/`.
2. Provide example Agent Zero config to add thegent MCP server.
3. Optional: Add Agent Zero to `docs/reference/TOUCHPOINT_INTEGRATION_DEEP_DIVE.md`.

### 4.3 OpenClaw — Limited Direct Use

**Idea:** OpenClaw Pi agent could call thegent for governance.

| Consideration  | Assessment                                          |
| -------------- | --------------------------------------------------- |
| OpenClaw focus | Consumer channels (WhatsApp, Telegram); not dev/CLI |
| thegent focus  | Governance, hooks, Pareto routing                   |
| Overlap        | Low — different surfaces                            |

**Verdict:** No strong use case. OpenClaw users wanting thegent-style governance would need custom integration; not a natural fit.

---

## 5. What Doesn't Fit thegent's Slice

| Feature                | Why                                                      |
| ---------------------- | -------------------------------------------------------- |
| OpenClaw multi-channel | thegent is CLI/terminal, not messaging                   |
| Agent Zero subagents   | thegent uses WORK_STREAM + DAG, not superior/subordinate |
| OpenClaw Gateway       | thegent has its own MCP server                           |
| Agent Zero memory/RAG  | thegent has `thegent_memory_*`; different design         |

---

## 6. Implementation Checklist

| Task                                                    | File / Location                     | Priority |
| ------------------------------------------------------- | ----------------------------------- | -------- |
| Verify ClawHub skill format                             | Manual inspection                   | P1       |
| Document Agent Zero + thegent MCP setup                 | `docs/guides/` or `docs/reference/` | P1       |
| Publish agent-orchestra to ClawHub (if format OK)       | clawhub.ai                          | P2       |
| Add ClawHub skill install path to thegent (optional)    | `commands/` or `cli_impl.py`        | P3       |
| Update TOUCHPOINT_INTEGRATION_DEEP_DIVE with Agent Zero | `docs/reference/`                   | P3       |

---

## 7. Related Research

- **OpenClaw/Agent Zero as main agent:** `docs/research/OPENCLAW_AGENTZERO_AS_MAIN_AGENT_RESEARCH.md` — Using OpenClaw or Agent Zero as thegent's primary sitback runtime for easier session chat and robustness.

---

## 8. References

- OpenClaw: https://github.com/openclaw/openclaw
- OpenClaw docs: https://docs.openclaw.ai
- ClawHub: https://clawhub.ai
- Agent Zero: https://github.com/agent0ai/agent-zero
- Agent Zero docs: https://www.agent-zero.ai/p/docs/get-started/
- thegent MCP: `src/thegent/mcp_*.py`, `thegent serve`
- thegent skills: `skills/agent-orchestra/`, `skills/sitback-agent/`

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added use case patterns
2. Added implementation examples
3. Enhanced cross-references

### Cross-References Added

- OPENCLAW_AGENTZERO_AS_MAIN_AGENT_RESEARCH.md
- SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md

### Practical Additions

- Use case templates
- Configuration examples

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [OPENCLAW_AGENTZERO_AS_MAIN_AGENT_RESEARCH.md](./OPENCLAW_AGENTZERO_AS_MAIN_AGENT_RESEARCH.md) - Main agent research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
