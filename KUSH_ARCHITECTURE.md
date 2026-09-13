# KUSH ECOSYSTEM ARCHITECTURE

## Full System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              KUSH ECOSYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐ │
│  │   USAGE     │     │   4SGM     │     │    CIV     │     │  PARPOUR   │ │
│  │ (AI Usage   │     │ (Python    │     │ (Simulation│     │  (Spec-    │ │
│  │  Tracker)   │     │  Workspace)│     │  + Policy) │     │   First    │ │
│  └─────────────┘     └─────────────┘     └─────────────┘     │  Planning)  │ │
│        │                   │                   │                   └─────────────┘ │
│        │                   │                   │                         │       │
│        ▼                   ▼                   ▼                         ▼       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         THEGENT (Core)                                 │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐  │   │
│  │  │ Orchestr│  │Governance│  │Planning │  │ Execution│  │ Agents │  │   │
│  │  │  ation  │  │          │  │         │  │          │  │        │  │   │
│  │  └─────────┘  └──────────┘  └─────────┘  └──────────┘  └────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                    ┌─────────────────┼─────────────────┐                         │
│                    ▼                 ▼                 ▼                         │
│           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│           │  AGENTAPI++ │  │  CLIPROXY++ │  │TOKENLEDGER │               │
│           │  (HTTP API  │  │  (LLM Proxy │  │ (Cost      │               │
│           │  for Agents)│  │   + Router) │  │  Tracking) │               │
│           └──────────────┘  └──────────────┘  └──────────────┘               │
│                    │                 │                 │                         │
│                    └─────────────────┼─────────────────┘                         │
│                                      ▼                                          │
│                           ┌──────────────┐                                     │
│                           │   EXTERNAL   │                                     │
│                           │   LLM        │                                     │
│                           │   PROVIDERS  │                                     │
│                           │ (OpenAI,     │                                     │
│                           │  Anthropic,  │                                     │
│                           │  Google, AWS)│                                     │
│                           └──────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Catalog

| Project                | Type             | Purpose                                       | Location                    |
| ---------------------- | ---------------- | --------------------------------------------- | --------------------------- |
| **thegent**            | Core             | Agent orchestration, governance, execution    | `~/kush/thegent`            |
| **agentapi++**         | HTTP API         | Control Claude, Cursor, Aider, Codex via HTTP | `~/kush/agentapi++`         |
| **cliproxy++**         | LLM Proxy        | Multi-provider routing, rate limiting         | `~/kush/cliproxy++`         |
| **tokenledger**        | Cost Tracking    | Token usage, cost analysis                    | `~/kush/tokenledger`        |
| **4sgm**               | Python Workspace | Python tooling, docs, QA                      | `~/kush/4sgm`               |
| **civ**                | Simulation       | Deterministic sim, policy-driven              | `~/kush/civ`                |
| **parpour**            | Planning         | Spec-first planning, architecture             | `~/kush/parpour`            |
| **usage**              | Usage Tracker    | AI usage with native OS integration           | `~/kush/usage`              |
| **pheno-sdk**          | SDK              | Python SDK with credential management         | `~/kush/pheno-sdk`          |
| **heliosHarness**      | Research         | Multi-agent research, command packaging       | `~/kush/heliosHarness`      |
| **helios_router_data** | Data             | Router analytics, Pareto dashboard            | `~/kush/helios_router_data` |
| **bloc**               | CLI              | Line counting, code visualization             | `~/kush/bloc`               |

---

## Data Flow

```
User/CLI
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  THEGENT                                                                  │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐ │
│  │ CLI     │───▶│ Orchestratr │───▶│  Execution │───▶│   Results    │ │
│  │ Commands│    │ ion Engine  │    │   Engine   │    │              │ │
│  └─────────┘    └─────────────┘    └─────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │                                    │
         │  ┌─────────────┐                  │
         ├─▶│  Governance │                  │
         │  │  (policies, │                  │
         │  │   quotas)   │                  │
         │  └─────────────┘                  │
         │                                    │
         ▼                                    ▼
┌──────────────────────┐         ┌──────────────────────────────────────────┐
│   TOKENLEDGER       │         │            CLIPROXY++                   │
│   ┌──────────────┐  │         │   ┌────────────┐   ┌───────────────┐  │
│   │ Cost Tracking│◀─┼─────────┼───│  Router   │───│  Providers    │  │
│   │ + Usage      │  │         │   │  (routing)│   │  (OpenAI,    │  │
│   └──────────────┘  │         │   └────────────┘   │   Anthropic,  │  │
└──────────────────────┘         │                    │   AWS, etc)   │  │
                                └────────────────────┴───────────────┘  │
                                             │                          │
                                             ▼                          │
                                ┌──────────────────────────────┐        │
                                │       EXTERNAL APIs         │        │
                                │   OpenAI, Anthropic,       │        │
                                │   Google, AWS Bedrock       │        │
                                └──────────────────────────────┘        │
```

---

## API Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│  (thegent CLI, MCP Tools, External Apps)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENTAPI++                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  HTTP Server (port 3284)                                            │  │
│  │  - /v1/chat/completions  ──▶  Agent Control (Claude, Cursor, etc)  │  │
│  │  - /api/v0/agents       ──▶  Agent Management                      │  │
│  │  - /messages            ──▶  Conversation History                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ (LLM Requests)
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIPROXY++                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  OpenAI-Compatible API (port 8317)                                  │  │
│  │  - /v1/chat/completions  ──▶  Router → Provider                   │  │
│  │  - /v1/models           ──▶  Model Listing                       │  │
│  │  - /health              ──▶  Health Check                         │  │
│  │  - /metrics             ──▶  Prometheus Metrics                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│         │                                                                    │
│         │ (Provider Requests)                                              │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  PROVIDER ABSTRACTION                                                │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │  │
│  │  │ OpenAI  │ │Anthropic│ │ Google  │ │  AWS    │ │   Ollama    │   │  │
│  │  │         │ │         │ │ Gemini  │ │Bedrock  │ │  (Local)    │   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Integrations

### thegent → cliproxy++

```python
# thegent config
llm:
  provider: cliproxy
  base_url: http://localhost:8317/v1
  api_key: ${CLIPROXY_API_KEY}
```

### thegent → tokenledger

```python
# Usage tracking
from thegent.integrations.token_ledger import track_usage

track_usage(model="gpt-4o", tokens=1000, cost=0.03)
```

### thegent → agentapi++

```python
# MCP server
mcp:
  servers:
    agentapi:
      command: agentapi
      args: ["server", "--", "claude"]
```

---

## Legacy/Archived Projects

| Project                    | Status      | Notes               |
| -------------------------- | ----------- | ------------------- |
| `cliproxyapi-refactor`     | 🔴 Archived | Old refactor branch |
| `cliproxyapi-circular-fix` | 🔴 Archived | Fix branch          |
| `4sgm-refactor`            | 🔴 Archived | Old refactor        |
| `4sgm-updates`             | 🔴 Archived | Old updates         |
| `agentapi`                 | ✅ Merged   | Into agentapi++     |
| `cliproxy-plusplus`        | ✅ Merged   | SDK into cliproxy++ |

---

## Current Git Status

```
~/kush/
├── thegent/           ✅ main (59 commits ahead)
├── agentapi++/        ✅ main (merged from agentapi)
├── cliproxy++/        ✅ main
├── tokenledger/       ✅ main (GitHub created)
├── 4sgm/             ✅ main
├── civ/               ✅ main
├── parpour/           ✅ main
├── pheno-sdk/         ✅ main
├── heliosHarness/     ✅ main
├── usage/             ✅ main
├── bloc/              ✅ main
└── rsrch/            ✅ main
```

---

## Summary

The Kush ecosystem is a **multi-repo system** for AI agent orchestration:

1. **thegent** - Central orchestration engine
2. **agentapi++** - HTTP API to control external agents
3. **cliproxy++** - Unified LLM proxy with multi-provider routing
4. **tokenledger** - Cost tracking and optimization
5. **4sgm/civ/parpour** - Supporting infrastructure (docs, simulation, planning)
6. **usage** - End-user usage tracking

All connected via HTTP APIs and internal integrations.
