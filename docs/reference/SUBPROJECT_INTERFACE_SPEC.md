# Sub-Project Interface Specification (Track 4)

**Version:** 1.0
**Date:** 2026-02-22
**Status:** Design
**Change Control:** Required for breaking changes

---

## Overview

This document defines the formal contracts between thegent's four sub-projects. All communication occurs via the **MCP protocol** (Machine Context Protocol) — no direct Python imports across project boundaries.

### Layering Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ USER / EXTERNAL INTEGRATIONS                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ (CLI args, HTTP requests)
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ THEGENT-CLI (Presentation Layer)                                │
│ - Command parsing (typer)                                       │
│ - Output formatting (rich)                                      │
│ - Session management                                            │
│ Port: N/A (client only)                                         │
│ Implements: MCP Client via httpx                                │
└────────────────────────┬────────────────────────────────────────┘
                         │ (MCP calls to http://127.0.0.1:3847)
                         │ Tools: run_agent, list_agents, etc.
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ THEGENT-AGENTS (Orchestration Layer)                            │
│ - Agent runner (strategy pattern)                               │
│ - Memory store (JSONL + SQLite)                                 │
│ - Planning engine (task decomposition)                          │
│ - Team manager (multi-agent coordination)                       │
│ Port: 3847 (MCP Server, stdio or HTTP)                          │
│ Implements: FastMCP server                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ (MCP calls to http://127.0.0.1:3848)
                         │ Tools: 500+ integrations
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ THEGENT-MCP (Integration Layer)                                 │
│ - Tool aggregator (GitHub, Slack, Stripe, OpenAI, etc.)       │
│ - Resource handlers (streaming, large payloads)                 │
│ - Error normalization                                           │
│ Port: 3848 (MCP Server)                                         │
│ Implements: FastMCP server                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ (HTTP/SDK calls to external APIs)
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ EXTERNAL APIS (GitHub, Slack, Stripe, OpenAI, Anthropic, etc.) │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ THEGENT-CORE (Rust/Zig, All Layers)                             │
│ - Python FFI bridge (thegent-ffi crate)                         │
│ - Caching, crypto, discovery, memory, git, file ops            │
│ - Compiled library (no server)                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: CLI ↔ Agents Interface

### Entry Point

**Client:** `thegent-cli`
**Server:** `thegent-agents` (MCP)
**Port:** 3847
**Protocol:** MCP over stdio (default) or HTTP (optional)

### Tools (thegent-cli → thegent-agents)

#### 1. `run_agent`

Execute an agent task with streaming output.

**Request Schema:**
```json
{
  "agent_id": "default",
  "prompt": "Implement a feature that lists files in a directory",
  "context": {
    "model": "claude-opus-4.6",
    "temperature": 1.0,
    "max_tokens": 4096,
    "system_role": "code"
  }
}
```

**Response (streaming, chunked):**
```json
{"type": "chunk", "data": "Analyzing task..."}
{"type": "chunk", "data": "Planning steps..."}
{"type": "chunk", "data": "Executing..."}
{"type": "done", "result": {"success": true, "exit_code": 0}, "timing_ms": 2500}
```

**Pydantic Models:**
```python
from pydantic import BaseModel
from typing import Optional, AsyncIterator


class RunAgentRequest(BaseModel):
    agent_id: str = "default"
    prompt: str
    context: Optional[dict] = None


class AgentChunk(BaseModel):
    type: str  # "chunk" | "done"
    data: Optional[str] = None
    result: Optional[dict] = None
    timing_ms: Optional[int] = None


class AgentSession:
    async def run_agent(self, req: RunAgentRequest) -> AsyncIterator[AgentChunk]:
        """Stream agent output."""
```

**Error Handling:**
```json
{
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent 'xyz' is not registered",
    "context": {
      "requested_agent_id": "xyz",
      "available_agents": ["default", "research", "code", "fix"]
    }
  }
}
```

**Error Codes:**
| Code | Meaning | HTTP |
|------|---------|------|
| `AGENT_NOT_FOUND` | Agent persona does not exist | 404 |
| `INVALID_PROMPT` | Prompt validation failed | 400 |
| `RESOURCE_EXHAUSTED` | Token/time limit exceeded | 429 |
| `INTERNAL_ERROR` | Server error during execution | 500 |
| `MODEL_UNAVAILABLE` | Model not accessible | 503 |

---

#### 2. `list_agents`

List available agent personas.

**Request:** Empty

**Response:**
```json
{
  "agents": [
    {
      "id": "default",
      "name": "Default Agent",
      "description": "General-purpose agent",
      "model": "claude-opus-4.6",
      "enabled": true
    },
    {
      "id": "research",
      "name": "Research Agent",
      "description": "Specialized for research tasks",
      "model": "claude-opus-4.6",
      "enabled": true
    },
    {
      "id": "code",
      "name": "Code Agent",
      "description": "Specialized for coding tasks",
      "model": "claude-opus-4.6",
      "enabled": true
    }
  ]
}
```

---

#### 3. `get_agent_state`

Retrieve current state of a running agent.

**Request:**
```json
{
  "agent_id": "default"
}
```

**Response:**
```json
{
  "agent_id": "default",
  "status": "running",  # "idle" | "running" | "error" | "paused"
  "current_task": "Analyzing codebase structure...",
  "elapsed_ms": 5000,
  "tokens_used": 2345,
  "memory_size_bytes": 102400,
  "last_update": "2026-02-22T15:30:45Z"
}
```

---

#### 4. `stop_agent`

Stop a running agent.

**Request:**
```json
{
  "agent_id": "default"
}
```

**Response:**
```json
{
  "success": true,
  "agent_id": "default",
  "final_status": "stopped",
  "total_time_ms": 15000
}
```

---

#### 5. `query_memory`

Query agent's memory store for past interactions/decisions.

**Request:**
```json
{
  "agent_id": "default",
  "query": "files modified in recent runs",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "timestamp": "2026-02-22T14:30:00Z",
      "type": "decision",
      "content": "Decided to refactor authentication module",
      "confidence": 0.95
    },
    {
      "timestamp": "2026-02-22T14:15:00Z",
      "type": "file_access",
      "content": "Modified /src/auth/handler.py",
      "confidence": 1.0
    }
  ]
}
```

---

#### 6. `add_memory`

Store an item in agent's memory (for agents to remember decisions/learnings).

**Request:**
```json
{
  "agent_id": "default",
  "item": {
    "type": "decision",
    "content": "User prefers short function names over long ones",
    "confidence": 0.8,
    "tags": ["code-style", "user-preference"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "memory_id": "mem_abc123",
  "stored_at": "2026-02-22T15:30:00Z"
}
```

---

### Resources (thegent-cli → thegent-agents)

#### 1. `agents://{agent_id}/state`

Read-only resource returning full agent state (JSON).

**URI:** `agents://default/state`

**Response:**
```json
{
  "agent_id": "default",
  "status": "idle",
  "config": {
    "model": "claude-opus-4.6",
    "temperature": 1.0,
    "max_tokens": 4096
  },
  "stats": {
    "total_runs": 42,
    "avg_tokens_per_run": 2100,
    "success_rate": 0.95
  }
}
```

---

#### 2. `agents://{agent_id}/memory`

Read agent's memory store as list of items.

**URI:** `agents://default/memory`

**Response:**
```json
{
  "count": 127,
  "items": [
    {
      "id": "mem_abc123",
      "timestamp": "2026-02-22T15:30:00Z",
      "type": "decision",
      "content": "...",
      "confidence": 0.95
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 100,
    "has_more": true
  }
}
```

---

### Session State Contract

CLI maintains session state in `~/.thegent/sessions/`:

**File:** `run_registry.jsonl`

Each line is a JSON object:
```json
{
  "timestamp": "2026-02-22T15:30:00Z",
  "session_id": "sess_abc123",
  "agent_id": "default",
  "command": "thegent free 'list files'",
  "status": "success",
  "exit_code": 0,
  "duration_ms": 2500,
  "tokens_used": 1200,
  "context_hash": "sha256:abc123..."
}
```

---

## Part 2: Agents ↔ MCP Interface

### Entry Point

**Client:** `thegent-agents` (when executing agent tasks)
**Server:** `thegent-mcp` (MCP tool aggregator)
**Port:** 3848
**Protocol:** MCP over stdio or HTTP

### Tool Categories (thegent-agents → thegent-mcp)

thegent-mcp exposes ~500 tools across integrations. Agents invoke via standardized tool call pattern.

#### Tool Naming Convention

Tools follow pattern: `{service}/{action}`

Examples:
- `github/list_repos`
- `github/create_issue`
- `slack/send_message`
- `slack/list_channels`
- `stripe/create_charge`
- `openai/create_chat_completion`
- `anthropic/create_message`

#### Agent Tool Invocation Contract

**Pydantic Model:**
```python
from pydantic import BaseModel
from typing import Optional, Any


class ToolCall(BaseModel):
    tool_name: str  # e.g., "github/list_repos"
    args: dict  # Tool-specific arguments
    timeout_sec: Optional[int] = 30


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any  # Tool-specific response
    error: Optional[str] = None
    duration_ms: int

    def to_memory_item(self, agent_id: str) -> "MemoryItem":
        """Convert to persistable memory item."""
```

**Example: GitHub Tool Invocation**

**Request:**
```json
{
  "tool_name": "github/list_repos",
  "args": {
    "owner": "anthropic",
    "type": "public"
  },
  "timeout_sec": 30
}
```

**Response:**
```json
{
  "success": true,
  "output": [
    {
      "name": "anthropic-sdk-python",
      "url": "https://github.com/anthropic-ai/anthropic-sdk-python",
      "stars": 12345,
      "language": "Python"
    },
    {
      "name": "anthropic-sdk-go",
      "url": "https://github.com/anthropic-ai/anthropic-sdk-go",
      "stars": 5432,
      "language": "Go"
    }
  ],
  "duration_ms": 450
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Authentication failed: Invalid GitHub token",
  "duration_ms": 120
}
```

---

### Memory Persistence (Agents ← All Tools)

After every tool invocation, agents persist result to memory:

**File:** `~/.thegent/sessions/run_registry.jsonl`

```json
{
  "timestamp": "2026-02-22T15:30:00Z",
  "session_id": "sess_abc123",
  "agent_id": "default",
  "event_type": "tool_invocation",
  "payload": {
    "tool_name": "github/list_repos",
    "args": {"owner": "anthropic"},
    "result": {
      "success": true,
      "output": [...],
      "duration_ms": 450
    }
  },
  "context_hash": "sha256:..."
}
```

---

### Tool Registry (thegent-mcp)

thegent-mcp maintains a registry of all available tools. Agents query registry before invocation:

**Registry Lookup:**
```python
class ToolRegistry:
    def list_tools(self) -> List[ToolMetadata]:
        """All available tools."""

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Metadata for a specific tool."""

    def get_tools_by_category(self, category: str) -> List[ToolMetadata]:
        """All tools in a category (e.g., "github")."""


class ToolMetadata(BaseModel):
    name: str  # e.g., "github/list_repos"
    description: str
    category: str  # e.g., "github"
    requires_auth: bool
    args_schema: dict  # JSON Schema
```

---

## Part 3: Shared Modules (Read-Only Access)

All sub-projects have **read-only** access to shared modules. No modifications allowed.

### Shared Module List

| Module | Purpose | Status |
|--------|---------|--------|
| `thegent.config` | Configuration (env, secrets, settings) | Immutable |
| `thegent.contracts` | Domain models (Agent, Task, etc.) | Immutable |
| `thegent.models` | Pydantic models (Input/Output) | Immutable |
| `thegent.exit_codes` | Exit codes for CLI | Immutable |
| `thegent.observability` | Logging, tracing, metrics | Append-only |
| `thegent.execution` | Execution primitives | Immutable |
| `thegent.routing` | Model routing | Immutable |

### Access Pattern

```python
# ✅ ALLOWED: Read from shared modules
from thegent.config import TheGentConfig
from thegent.contracts import AgentTask
from thegent.models import OutputModel

# ❌ FORBIDDEN: Import across sub-projects
from thegent.agents import AgentRunner  # CLI cannot do this
from thegent.cli import CLIOutput  # Agents cannot do this

# ✅ ALLOWED: Call via MCP protocol instead
await cli_client.run_agent(prompt)  # CLI uses MCP to invoke agents
```

---

## Part 4: Configuration & Credentials

All sub-projects use unified config system at `~/.thegent/config.toml`:

### Config Structure

```toml
# Core
[core]
model = "claude-opus-4.6"
temperature = 1.0
max_tokens = 4096

# Agents
[agents]
memory_dir = "~/.thegent/sessions"
default_agent = "default"
timeout_sec = 300

# Integrations (Credentials)
[integrations.github]
token = "${GITHUB_TOKEN}"  # From env or secrets

[integrations.slack]
token = "${SLACK_BOT_TOKEN}"

[integrations.stripe]
api_key = "${STRIPE_API_KEY}"

[integrations.openai]
api_key = "${OPENAI_API_KEY}"

[integrations.anthropic]
api_key = "${ANTHROPIC_API_KEY}"

# MCP Servers
[mcp_servers]
agents_host = "127.0.0.1"
agents_port = 3847
mcp_host = "127.0.0.1"
mcp_port = 3848
```

### Credential Access

```python
# Any sub-project can read (but not write)
from thegent.config import TheGentConfig

config = TheGentConfig()

# ✅ Read credentials
github_token = config.get_integration_secret("github", "token")
slack_token = config.get_integration_secret("slack", "token")

# ❌ Never hardcode or modify
os.environ["GITHUB_TOKEN"] = "..."  # FORBIDDEN
config.integrations.github.token = "..."  # FORBIDDEN
```

---

## Part 5: Error Handling & Back-Pressure

### Standard Error Format

All sub-projects return errors in this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "context": {
      "detail1": "value1",
      "detail2": "value2"
    },
    "timestamp": "2026-02-22T15:30:00Z",
    "trace_id": "trace_abc123"
  }
}
```

### Error Codes (Global)

| Code | Meaning | Sub-Project | HTTP |
|------|---------|-------------|------|
| `AGENT_NOT_FOUND` | Unknown agent | agents | 404 |
| `TOOL_NOT_FOUND` | Unknown tool | mcp | 404 |
| `INVALID_ARGS` | Bad arguments | any | 400 |
| `AUTHENTICATION_FAILED` | Auth required/failed | mcp, agents | 401 |
| `PERMISSION_DENIED` | Insufficient perms | any | 403 |
| `RESOURCE_EXHAUSTED` | Token/rate limit | agents, mcp | 429 |
| `TIMEOUT` | Operation timeout | agents, mcp | 504 |
| `INTERNAL_ERROR` | Server error | any | 500 |
| `UNAVAILABLE` | Service down | any | 503 |

### Back-Pressure

If agents invoke MCP too rapidly, mcp-server returns `RESOURCE_EXHAUSTED`:

```json
{
  "error": {
    "code": "RESOURCE_EXHAUSTED",
    "message": "Rate limit exceeded: 100 requests/min",
    "context": {
      "limit": 100,
      "window_sec": 60,
      "retry_after_sec": 5
    }
  }
}
```

Agents must implement exponential backoff:

```python
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
)
async def invoke_tool(tool_name: str, args: dict) -> ToolResult:
    """Invoke tool with exponential backoff on rate limit."""
    # ...
```

---

## Part 6: Testing Contracts

### Contract Tests (Per Sub-Project)

Each sub-project must pass contract tests verifying it conforms to interface spec.

**File:** `tests/contracts/test_mcp_interface.py`

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agents_server_mcp_contract():
    """Agents server conforms to MCP protocol spec."""
    async with AsyncClient() as client:
        # Test tool registration
        tools = await client.get("http://127.0.0.1:3847/tools")
        assert "run_agent" in [t["name"] for t in tools["tools"]]

        # Test error format
        resp = await client.post(
            "http://127.0.0.1:3847/tools/run_agent", json={"agent_id": "nonexistent", "prompt": "test"}
        )
        assert resp.status_code in [400, 404, 500]
        data = resp.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]


@pytest.mark.asyncio
async def test_mcp_server_tool_response_format():
    """MCP server tool responses match contract."""
    async with AsyncClient() as client:
        # Tool response should have success + output or error
        resp = await client.post("http://127.0.0.1:3848/tools/github/list_repos", json={"owner": "anthropic"})
        data = resp.json()

        if resp.status_code == 200:
            assert "success" in data
            assert "output" in data or "error" in data
        else:
            assert "error" in data
```

---

## Part 7: Backwards Compatibility

### Deprecation Policy

When changing an interface:

1. **Announce** in CHANGELOG.md (1 week minimum)
2. **Support old + new** for 2 weeks (dual API)
3. **Migrate** all clients (enforce in tests)
4. **Remove old API** (major version bump)

### Example: Adding Required Field

Old request:
```json
{"agent_id": "default", "prompt": "..."}
```

New request (with optional field):
```json
{"agent_id": "default", "prompt": "...", "timeout_sec": 30}
```

**During transition (both accepted):**
```python
class RunAgentRequest(BaseModel):
    agent_id: str
    prompt: str
    timeout_sec: int = 30  # New field, optional, has default
```

**After migration (field required):**
```python
class RunAgentRequest(BaseModel):
    agent_id: str
    prompt: str
    timeout_sec: int  # Now required
```

---

## Part 8: Performance & SLO

### Service Level Objectives

| Operation | Target | SLO |
|-----------|--------|-----|
| `list_agents` | <50ms | 99.5% |
| `run_agent` (initiation) | <200ms | 99% |
| Tool invocation (thegent-mcp) | <2s (p99) | 99% |
| Agent context retrieval | <100ms | 99.5% |
| Memory query | <500ms (p99) | 99% |

### Benchmarking

Each sub-project includes performance tests:

```python
# sub-projects/thegent-cli/tests/performance/test_startup.py

import pytest
import time


def test_cli_startup_time():
    """CLI startup should be <250ms."""
    start = time.time()
    # Import and initialize
    from thegent_cli.apps.main import app

    elapsed_ms = (time.time() - start) * 1000

    assert elapsed_ms < 250, f"Startup took {elapsed_ms}ms (target: 250ms)"


def test_agents_server_list_agents():
    """list_agents should respond in <50ms."""
    # ...
```

---

## Summary

| Interface | Protocol | Port | Blocking | Purpose |
|-----------|----------|------|----------|---------|
| **CLI → Agents** | MCP (stdio/HTTP) | 3847 | No (async) | Agent execution |
| **Agents → MCP** | MCP (stdio/HTTP) | 3848 | No (async) | Tool invocation |
| **Shared modules** | Direct import | N/A | N/A | Configuration, models |
| **Session state** | JSONL files | N/A | N/A | Audit log, memory |

All interfaces are **versioned**, **tested**, and **monitored** for compliance.

---

**End of Interface Specification**
