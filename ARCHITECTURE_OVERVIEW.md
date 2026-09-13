# thegent Architecture Overview

**Version:** 1.0
**Date:** 2026-03-30
**Status:** Active Development
**Audience:** Developers, Operators, Platform Architects

---

## Table of Contents

1. [What is thegent?](#what-is-thegent)
2. [Key Differentiators](#key-differentiators)
3. [High-Level Architecture](#high-level-architecture)
4. [Core Components](#core-components)
5. [Agent Orchestration System](#agent-orchestration-system)
6. [Memory & Knowledge Management](#memory--knowledge-management)
7. [Model Control Protocol (MCP) Integration](#model-control-protocol-mcp-integration)
8. [Key Dependencies & Integrations](#key-dependencies--integrations)
9. [Execution Modes & Coordination](#execution-modes--coordination)
10. [When to Use thegent vs Alternatives](#when-to-use-thegent-vs-alternatives)
11. [Integration Patterns](#integration-patterns)
12. [Future Roadmap](#future-roadmap)

---

## What is thegent?

**thegent** is a **unified multi-agent orchestration platform** designed to coordinate autonomous agents across multiple AI providers, platforms, and execution contexts. It abstracts away provider-specific differences (Claude, Gemini, Codex, Cursor, Copilot, and others) and provides a harmonious, enterprise-grade orchestration layer.

### Core Purpose

thegent solves the fragmentation problem: each AI platform (Claude Code, Cursor, Codex, etc.) has its own execution model, configuration format, and memory system. thegent consolidates these into:

- **Universal Agent Registry** — One canonical list of all available agents
- **Provider-Agnostic Routing** — Automatic failover, cost optimization, and smart fallback chains
- **Unified Memory Layer** — Persistent knowledge that agents share across sessions and platforms
- **MCP Gateway** — Model Control Protocol tools available to any agent
- **Autonomous Governance** — Self-healing documentation (the "Gardener" agent)

### Problem Statement

Before thegent:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Claude Code │  │   Cursor    │  │   Codex     │  │  Copilot    │
│   (Rules)   │  │  (Rules)    │  │  (Prompts)  │  │  (Settings) │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │
       └────────────────┼────────────────┼────────────────┘
                        │
              (Fragmented, Manual Sync)
                        │
       ┌────────────────┼────────────────┐
       │                │                │
    No Standard      Each Needs      Custom
   Shared Memory     Own Config      Hooks
```

After thegent:

```
┌────────────────────────────────────────────────────────────┐
│                 thegent Unified Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ Agent        │  │ Memory &     │  │ MCP Tools      │   │
│  │ Registry     │  │ Knowledge    │  │ (File I/O,     │   │
│  │              │  │ Store        │  │  Git, Shell)   │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
└────────────────────────────────────────────────────────────┘
       │                │                │
   ┌───┴────┬───────┬───┴──┬───────┬────┴───┬────────┐
   │         │       │      │       │        │        │
Claude Code Cursor Codex Copilot Claude Gemini Etc.
   │         │       │      │       │        │        │
   ├─ Auto Failover ──────────────────────────────────┤
   ├─ Cost-Aware Routing ─────────────────────────────┤
   ├─ Persistent Session Memory ──────────────────────┤
   └─ Unified Logging & Governance ───────────────────┘
```

---

## Key Differentiators

### 1. **Multi-Provider Orchestration**

| Feature | thegent | heliosCLI | phenotype-infrakit |
|---------|---------|-----------|-------------------|
| Multi-agent coordination | ✅ (core) | ⚠️ (harness only) | ❌ |
| Provider fallback chains | ✅ | ❌ | ❌ |
| Cost-aware routing | ✅ (via LiteLLM) | ❌ | ❌ |
| Agent registry | ✅ (canonical) | ⚠️ (helpers only) | ❌ |
| **Scope** | **Agent orchestration** | **Development harness** | **Shared Rust libs** |

### 2. **Harmonious Experience (HAX)**

thegent implements the **Harmonious Agent Experience (HAX)** initiative:
- **Same rules work everywhere**: `$defer`, `$block`, `$idea` syntax works in Claude Code, Cursor, Codex, Copilot
- **One memory**: Cloud-scale knowledge graph (Supermemory.ai) shared across all platforms
- **Unified routing**: Intelligent multi-provider routing with LiteLLM

### 3. **Enterprise-Grade Resilience**

- **Failure Classification**: Distinguishes rate limits, transient failures, and usage limits
- **Exponential Backoff Retry**: Configurable retry chains with intelligent backoff
- **Fallback State Machine**: Automatic provider failover when one is exhausted
- **Telemetry & Drift Detection**: Monitors agent health and semantic drift

### 4. **Self-Healing Governance**

The **Gardener Agent** automatically:
- Synthesizes session history into `CLAUDE.md`, `ADR.md`, `PRD.md`
- Updates specs with latest decisions and work items
- Maintains documentation debt near zero
- Runs on a background schedule

---

## High-Level Architecture

### System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                  thegent Orchestration Layer                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             Unified Agent Interface                      │   │
│  │  Abstracts: Provider types, CLI variations, API changes  │   │
│  └──────────┬───────────────────────────────────────────────┘   │
│             │                                                    │
│  ┌──────────▼────────────────────────────────────────────────┐   │
│  │           Agent Routing & Orchestration                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │  Classifier  │  │   Fallback   │  │     Cost     │    │   │
│  │  │  (Failure)   │  │  State Mach. │  │   Router     │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └──────────┬───────────────────────────────────────────────┘   │
│             │                                                    │
│  ┌──────────▼────────────────────────────────────────────────┐   │
│  │      Memory, Config, Execution Management                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │  Memory      │  │  Config      │  │  Execution   │    │   │
│  │  │  Store       │  │  Manager     │  │  Modes       │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └──────────┬───────────────────────────────────────────────┘   │
│             │                                                    │
│  ┌──────────▼────────────────────────────────────────────────┐   │
│  │         MCP Tools & Integrations                         │   │
│  │  File I/O, Git, Shell, Subprocess, Tool Detection       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        │                 │                 │
        │                 │                 │
    ┌───▼──┐          ┌───▼──┐         ┌───▼──┐
    │Claude│          │Cursor│         │Codex │  (etc.)
    │ Code │          │Rules │         │Proxy │
    └──────┘          └──────┘         └──────┘
```

### Layered Design (Hexagonal Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    Ports (Interfaces)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Inbound:    │  │ Agent Port   │  │ Memory Port  │       │
│  │ - CLI       │  │ - Runner     │  │ - Store      │       │
│  │ - MCP       │  │ - Registry   │  │ - Sync       │       │
│  │ - HTTP API  │  │ - Retry      │  │              │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────────┐
│                    Domain (Core Logic)                        │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Agent Routing | Failure Classification | Fallback   │    │
│  │  State Machine | Cost Optimization | Execution Modes │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────────┐
│               Adapters (Implementations)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ DirectAgent  │  │ CodexProxy   │  │ CursorAPI    │        │
│  │ Runner       │  │ Runner       │  │ Runner       │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ FileMemory   │  │ GraphMemory  │  │ PostgresCache│        │
│  │ Store        │  │ (Supermemory)│  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Agent Runners

Abstracts different agent execution backends.

```rust
// thegent-runtime/src/main.rs
pub trait AgentRunner: Send + Sync {
    async fn run(
        &self,
        prompt: String,
        cwd: Option<PathBuf>,
        mode: ExecutionMode,
        timeout: Duration,
        streaming: bool,
    ) -> Result<RunResult>;
}

pub struct RunResult {
    pub exit_code: i32,
    pub stdout: String,
    pub stderr: String,
    pub timed_out: bool,
}
```

**Implementations:**
- **DirectAgentRunner**: Native CLI (claude-agent, cursor-agent, gemini, copilot)
- **CodexProxyRunner**: CLIProxyAPIPlus proxy (minimax, glm, antigravity, cliproxy)
- **CursorApiRunner**: wisdgod cursor-api HTTP backend
- **DroidRunner**: Factory droids via `droid exec`

### 2. Agent Registry

Canonical registry of all available agents with name resolution and fallback chains.

```python
# src/thegent_platform.py
class AgentRegistry:
    def get_runner(agent_name: str) -> AgentRunner:
        # Resolve aliases, return appropriate runner

    def get_fallback_agents(primary: str) -> List[str]:
        # Return fallback chain (e.g., claude -> gemini -> codex)

    def list_agents() -> List[AgentMetadata]:
        # Return all registered agents with capabilities
```

**Canonical Agents:**
- Direct: `claude`, `gemini`, `codex`, `cursor-agent`, `copilot`
- Proxy: `minimax`, `glm`, `antigravity`, `cliproxy`, `roo`, `kilo`
- Factory: `droid` (droids via Factory)

### 3. Failure Classification & Retry

Classifies failures and applies intelligent retry strategies.

```python
class FailureKind(Enum):
    RATE_LIMIT       # 429, too-many-requests
    TRANSIENT        # 502, 503, 504, reconnecting
    USAGE_LIMIT      # quota, subscription, billing exhaustion
    UNKNOWN          # other errors

class RetryStrategy:
    max_attempts: int = 4
    min_wait: Duration = 2s
    max_wait: Duration = 60s
    retry_on: List[FailureKind] = [RATE_LIMIT, TRANSIENT]
    backoff_multiplier: float = 2.0  # exponential
```

### 4. Fallback State Machine

Automatically falls back to alternative providers when one is exhausted.

```
┌─────────────────┐
│   Start with    │
│  Primary Agent  │
└────────┬────────┘
         │
    ┌────▼──────────┐
    │ Run with Retry│
    │(up to N times)│
    └────┬───────┬──┘
         │       │
         │       │ Max retries reached
         │       │
    ┌────▼───┐   ┌──────────────┬─────────────┐
    │Success │   │ Failure Type │             │
    │Return  │   ├─ Rate Limit  │ Usage Limit │
    └────────┘   │ + Transient  │ or Other    │
                 │ = Retry      │ = Fallback  │
                 └──────┬───────┴─────────┬───┘
                        │                 │
                   ┌────▼──────────┐  ┌───▼──────────┐
                   │More Agents?   │  │No More Agents│
                   └────┬────┬─────┘  └───┬──────────┘
                        │    │            │
                    Yes │    │ No     ┌───▼──────┐
                   ┌────▼────▼─┐      │ Error    │
                   │Try Next   │      │Return    │
                   │Provider   │      └──────────┘
                   └───┬───────┘
                       │
                  ┌────▼──────────┐
                  │(Loop back to  │
                  │ Run with Retry)
                  └───────────────┘
```

### 5. Execution Modes

Defines multi-agent execution patterns for swarms.

| Mode | Min Agents | Streaming | Coordination | Use Case |
|------|-----------|-----------|-------------|----------|
| **SOLO** | 1 | ✅ | None | Single agent, direct invocation |
| **SEQUENTIAL_DELEGATION** | 2+ | ✅ | Chain of agents; one feeds output to next | Refining output through multiple passes |
| **PARALLEL_CONSENSUS** | 2+ | ❌ | Run all in parallel; vote on best output | Quality consensus, cross-validation |
| **REVIEW_LOOP** | 2 | ✅ | Worker + Reviewer; iterate until accepted | Self-review, iterative refinement |
| **ARBITRATION_QUORUM** | 3+ | ❌ | Weighted voting; expert arbiters | Complex decisions requiring expert judgment |

---

## Agent Orchestration System

### Multi-Agent Coordination Protocol

thegent defines a **Cross-Platform Agent Coordination Protocol** for swarms.

```
┌─────────────────────────────────────────────────────────────┐
│         Multi-Agent Coordination (WP-9003)                 │
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │   Voting   │    │ Broadcast  │    │ Task Sync  │       │
│  │   • Rank   │    │ • Announce │    │ • Assign   │       │
│  │   • Weight │    │ • Updates  │    │ • Status   │       │
│  │   • Decide │    │ • ACK/NACK │    │ • Depend.  │       │
│  └────────────┘    └────────────┘    └────────────┘       │
│                                                             │
│  Via: Queue (JSONL), Messaging (NATS), Shared State       │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- **Voting**: Agents rank options; weighted voting determines winner
- **Broadcast**: Coordinated announcements; async acknowledgment
- **Task Sync**: Assign work packages; agents report status/completion

### Session Persistence

Sessions survive across platform switches and reboots.

```
Session Storage:
├── .thegent/
│   ├── sessions/
│   │   └── {session-id}.json         # Session metadata
│   ├── memory/
│   │   ├── local/
│   │   │   └── {key}.jsonl           # File-based memory
│   │   └── graph/                    # Supermemory.ai
│   ├── prompt_queue.jsonl             # Unified prompt queue
│   └── telemetry/
│       └── {date}.jsonl               # Agent runs, errors
```

**Session Recovery:**
1. Agent detects `THEGENT_SESSION_ID` env var or prompt contains `$resume <id>`
2. Loads session state from `.thegent/sessions/{id}.json`
3. Restores memory context from local store and/or Supermemory
4. Resumes execution from last checkpoint

---

## Memory & Knowledge Management

### Three-Tier Memory Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Tier 1: Short-Term (Context Window)                    │
│  • Current conversation / session                        │
│  • TTL: Single agent run                                │
│  • Storage: Process memory, stdin/stdout                │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│  Tier 2: Medium-Term (Local Knowledge)                   │
│  • Session memory, worklogs, audit logs                 │
│  • TTL: Days to weeks                                    │
│  • Storage: `.thegent/memory/local/` (JSONL files)       │
│  • Providers: FileMemoryStore, DiskCache                │
└────────────────┬─────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│  Tier 3: Long-Term (Knowledge Graph)                     │
│  • Cross-session insights, decisions, learned patterns   │
│  • TTL: Indefinite (months to years)                     │
│  • Storage: Supermemory.ai (cloud graph DB)              │
│  • Features: Semantic search, entity extraction, decay   │
└──────────────────────────────────────────────────────────┘
```

### The Gardener Agent

Background agent that synthesizes knowledge into specs.

```
Gardener Loop:
┌──────────────────────┐
│ Scan audit logs &    │
│ session history      │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ Extract decisions,   │
│ ADRs, tasks, issues  │
└──────────┬───────────┘
           │
┌──────────▼───────────────────────┐
│ Synthesize into:                 │
│ • CLAUDE.md (rules, hooks)       │
│ • ADR.md (decisions)             │
│ • PRD.md (user stories)          │
│ • FUNCTIONAL_REQUIREMENTS.md     │
└──────────┬───────────────────────┘
           │
┌──────────▼───────────┐
│ Commit & Announce    │
│ documentation update │
└──────────────────────┘
```

**Benefits:**
- Zero documentation debt
- Decisions auditable and traceable
- New agents onboard with full context
- Policy drift detection

---

## Model Control Protocol (MCP) Integration

### MCP Tools Available to Agents

thegent exposes tools via MCP so agents can interact with the orchestration layer.

```python
# Tools available via MCP
@mcp_tool("thegent/queue/read")
def read_queue_item(queue_id: str) -> QueueItem:
    """Read next item from unified queue"""


@mcp_tool("thegent/queue/write")
def write_queue_item(item: QueueItem) -> str:
    """Write item to queue for processing"""


@mcp_tool("thegent/memory/get")
def get_memory(key: str) -> Any:
    """Retrieve from shared memory store"""


@mcp_tool("thegent/memory/set")
def set_memory(key: str, value: Any, ttl: Optional[int] = None):
    """Store in shared memory with optional TTL"""


@mcp_tool("thegent/agent/invoke")
def invoke_agent(agent: str, prompt: str, timeout: Duration) -> RunResult:
    """Invoke another agent (for swarm coordination)"""


@mcp_tool("thegent/exec/stream-subprocess")
def stream_subprocess(cmd: str, cwd: Path) -> Iterator[str]:
    """Stream subprocess output in real-time"""
```

### Unified Runtime Dispatch

**thegent-runtime** is a single, high-performance Rust binary that consolidates all tool shims.

```
thegent-runtime (Dispatch Binary)
├── find      → builtin find(1)
├── grep      → builtin grep(1) / ripgrep
├── git       → git wrapper with caching
├── cat       → file reader
├── ls        → directory lister
├── subprocess → streaming executor
└── ... (30+ tools)

Size: <5 MB (stripped, LTO)
Latency: <10ms tool dispatch overhead
```

**Why Dispatch?**
- Reduces process spawn overhead (one binary vs many)
- Enables unified error handling and caching
- Allows atomic operations (prevent TOCTTOU races)
- Central telemetry collection point

---

## Key Dependencies & Integrations

### Core Library Stack

```toml
# Orchestration & Async Runtime
tokio = "1.40"           # async runtime
async-trait = "0.1"      # async trait support

# CLI & Configuration
typer = "^0.12"          # CLI framework
pydantic = "^2.9"        # validation
pydantic-settings = "^2.3"  # environment config
rich = "^13.0"           # beautiful output

# Agent & Provider Integration
tenacity = "^8.3"        # retry logic
pybreaker = "^1.4"       # circuit breaker
litellm = "^1.5"         # multi-provider routing
httpx = "^0.27"          # async HTTP

# Memory & Persistence
diskcache = "^5.6"       # local persistent cache
sqlalchemy = "^2.0"      # ORM (PostgreSQL backend)
supermemory-sdk = "latest"  # knowledge graph

# Process Management
process-compose = "latest"  # process orchestrator
nats-py = "^2.5"         # NATS messaging
temporalio = "^1.4"      # temporal workflows

# MCP & Agent Protocols
fastmcp = "^0.11"        # MCP server framework
crewai = "latest"        # agent coordination
langgraph = "^0.1"       # agent graphs
```

### External Integrations

| Service | Purpose | Criticality | Fallback |
|---------|---------|-------------|----------|
| **Supermemory.ai** | Knowledge graph, semantic search | Medium | Local JSONL + SQLite |
| **LiteLLM** | Multi-provider routing, cost optimization | High | Direct provider calls |
| **NATS** | Inter-agent messaging | Low | JSONL queue (slower) |
| **Temporal.io** | Workflow orchestration | Low | Simple state machine |
| **PostgreSQL** | Persistent cache, telemetry | Medium | SQLite fallback |
| **Sentry / DataDog** | Error tracking, telemetry | Low | File-based logging |

---

## Execution Modes & Coordination

### Unified Queue System

All pending work (prompts, tasks, ideas) flows through a single unified queue.

```
Unified Queue: .thegent/prompt_queue.jsonl

Entry format:
{
  "id": "uuid",
  "source": "claude-code|cursor|codex|mcp|cli",
  "type": "prompt|task|idea|test",
  "timestamp": "2026-03-30T10:15:30Z",
  "content": "...",
  "tags": ["urgent", "cross-repo", "experimental"],
  "routing": {
    "preferred_agent": "claude",
    "fallback_chain": ["gemini", "codex"],
    "timeout": 300,
    "execution_mode": "SOLO"
  },
  "state": "pending|running|completed|failed",
  "metadata": {
    "project": "phenotype-infrakit",
    "branch": "feat/architecture-overview",
    "cwd": "/path/to/repo"
  }
}

Queue Operations:
├── queue scan       # Discover pending work
├── queue list       # Show months/categories
├── queue next       # Get next item
├── queue process    # Execute item
└── queue status     # Show stats
```

---

## When to Use thegent vs Alternatives

### Comparison Table

| Feature | thegent | heliosCLI | phenotype-infrakit |
|---------|---------|-----------|-------------------|
| Multi-agent swarms | ✅✅✅ | ⚠️ | ❌ |
| Provider failover | ✅✅✅ | ❌ | ❌ |
| Cost routing | ✅✅✅ | ❌ | ❌ |
| Memory layer | ✅✅ | ⚠️ | ❌ |
| Dev harness | ⚠️ | ✅✅✅ | ❌ |
| Process management | ⚠️ | ✅✅ | ❌ |
| Shared libraries | ⚠️ | ❌ | ✅✅✅ |
| Error handling | ✅ | ✅ | ✅✅ |
| Policy engine | ❌ | ❌ | ✅✅ |
| Local development | ⚠️ | ✅✅✅ | ❌ |

---

## Integration Patterns

### 1. **thegent + heliosCLI + phenotype-infrakit**

Optimal three-repo integration:

```
┌──────────────────────────────────────────────────────┐
│      User Terminal (Claude Code, Cursor)             │
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼─────────────┐
        │   thegent (Top Level)    │
        │  • Agent orchestration   │
        │  • Unified queue         │
        │  • Memory management     │
        │  • Cross-platform rules  │
        └────────────┬─────────────┘
                     │
        ┌────────────▼─────────────────────────┐
        │   heliosCLI (Harness Layer)          │
        │  • TUI & batch mode                 │
        │  • Process startup/cleanup           │
        │  • Sandboxing & isolation            │
        │  • Benchmarking                      │
        └────────────┬─────────────────────────┘
                     │
        ┌────────────▼──────────────────────────┐
        │ phenotype-infrakit (Library Layer)    │
        │  • Shared error types                │
        │  • Port interfaces (hexagonal)       │
        │  • Policy engine, state machines     │
        │  • Trait definitions                 │
        └──────────────────────────────────────┘
```

### 2. **Using thegent as a Library**

Import thegent into custom projects:

```python
from thegent_platform import AgentRegistry, FallbackStateMachine
from thegent.memory import MemoryStore
from thegent.mcp import MCPToolRegistry

# Integrate into your app
registry = AgentRegistry.load()
fsm = FallbackStateMachine(agents=registry.list_agents())

result = fsm.execute(
    prompt="Analyze this file",
    primary_agent="claude",
    fallback_chain=["gemini", "codex"],
    timeout=300,
    mode=ExecutionMode.SEQUENTIAL_DELEGATION,
)
```

### 3. **thegent in CI/CD Pipelines**

Queue-based integration with GitHub Actions:

```yaml
# .github/workflows/agentic-review.yml
name: Agentic Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Queue PR for review
        run: |
          thegent queue write \
            --type "task" \
            --content "Review PR #${{ github.event.pull_request.number }}" \
            --source "github-actions" \
            --preferred-agent "claude" \
            --routing-mode "REVIEW_LOOP"

      - name: Wait for review completion
        run: thegent queue wait --id ${{ steps.queue.outputs.id }} --timeout 600
```

---

## Future Roadmap

### Phase 1: Foundation (Q2 2026)

- [x] Agent registry & runner abstraction
- [x] Failure classification & retry
- [x] Fallback state machine
- [ ] Unified queue with TUI
- [ ] Memory layer (local + cloud)

### Phase 2: Autonomy (Q3 2026)

- [ ] Gardener agent (autonomous synthesis)
- [ ] Multi-agent coordination protocol
- [ ] Session persistence & recovery
- [ ] Cost-aware routing (LiteLLM integration)
- [ ] Semantic validation layer

### Phase 3: Enterprise (Q4 2026)

- [ ] Distributed execution (multi-machine)
- [ ] Audit and compliance logging
- [ ] Advanced telemetry (drift detection)
- [ ] Policy enforcement engine
- [ ] Chaos testing & resilience

### Phase 4: Next-Gen (2027+)

- [ ] Self-optimizing agent network
- [ ] Federated learning across teams
- [ ] Synthetic data generation for training
- [ ] Market-driven resource allocation
- [ ] Emergent behavior detection

---

## Summary

**thegent** is the orchestration backbone of the Phenotype ecosystem. It unifies fragmented agent capabilities into a harmonious, enterprise-grade platform.

**Key Strengths:**
1. Multi-provider abstraction eliminates lock-in
2. Intelligent fallback chains ensure reliability
3. Unified memory enables cross-session learning
4. Self-healing governance reduces maintenance burden
5. Queue-based architecture scales to 50+ agents

**When to choose:**
- Multi-agent coordination ➜ Use thegent
- Local development ➜ Use heliosCLI
- Shared infrastructure ➜ Use phenotype-infrakit

**Next Steps:**
1. Review PRD.md for detailed user stories
2. Check PLAN.md for implementation roadmap
3. Explore src/thegent/ for concrete examples
4. Read ADR.md for architectural decisions

---

**References:**
- PRD.md — Product requirements and user stories
- PLAN.md — Phased implementation roadmap
- FUNCTIONAL_REQUIREMENTS.md — Specification details
- ADR.md — Architecture decision records
- src/ — Source code organized by domain
- crates/ — Rust components (runtime, cache, git, etc.)

---

*Document Generated: 2026-03-30*
*Status: Active Development*
*Audience: Developers, Architects, Operators*
