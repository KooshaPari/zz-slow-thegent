<DONE>
# FastMCP Complete — Comprehensive Implementation Guide

> **Status**: Complete | **Version**: 1.0 | **Date**: 2026-02-16
> **Related**:
>
> - [MCP Full Parity & FastMCP Audit](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md)
> - [Multi-Platform Parity Master Plan](../plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md)
> - [MCP Tool Optimization Plan](../plans/MCP_TOOL_OPTIMIZATION_PLAN.md)
> - [FastMCP Documentation](https://gofastmcp.com)

## Overview

This document consolidates all FastMCP research into a single comprehensive guide covering implementation patterns, transport spec usage, middleware, storage, progress/tasks, transforms, and client compatibility. It provides complete breadth (all FastMCP features) and depth (implementation details, code examples, best practices) for production-ready MCP server development.

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [FastMCP Architecture](#2-fastmcp-architecture)
3. [Core Components](#3-core-components)
4. [Elicitation & Context API](#4-elicitation--context-api)
5. [Progress & Tasks](#5-progress--tasks)
6. [Middleware System](#6-middleware-system)
7. [Storage Backends](#7-storage-backends)
8. [Transforms & Providers](#8-transforms--providers)
9. [Transport & Protocols](#9-transport--protocols)
10. [Client Compatibility](#10-client-compatibility)
11. [Implementation Patterns](#11-implementation-patterns)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Executive Summary

### 1.1 What is FastMCP?

**FastMCP** is a Pythonic framework for building MCP (Model Context Protocol) servers. It provides:

- **Declarative API**: Decorators for tools, resources, prompts
- **Context Management**: Elicitation, progress, logging, sampling
- **Middleware Pipeline**: Caching, rate limiting, error handling
- **Multiple Transports**: STDIO, HTTP, SSE
- **Provider System**: Local, filesystem, proxy, skills, OpenAPI

### 1.2 Key Features

| Feature              | Status  | thegent Usage                             |
| -------------------- | ------- | ----------------------------------------- |
| **Tools**            | ✅ Full | 30+ tools (thegent_run, thegent_bg, etc.) |
| **Resources**        | ✅ Full | thegent://sessions, thegent://dag, etc.   |
| **Elicitation**      | ✅ Full | ctx.elicit() for user input               |
| **Progress**         | ✅ Full | ctx.report_progress()                     |
| **Background Tasks** | ✅ Full | TaskConfig for async execution            |
| **Middleware**       | ✅ Full | Caching, rate limiting, timing            |
| **Transforms**       | ✅ Full | Namespace, tool, resource transforms      |
| **Storage**          | ✅ Full | Memory, disk, Redis backends              |
| **HTTP Transport**   | ✅ Full | Streamable HTTP server                    |

### 1.3 Source Documents

This consolidated guide synthesizes content from:

- `FASTMCP_IMPLEMENTATION_GUIDE.md` (Implementation patterns, 1500+ lines)
- `FASTMCP_SPEC_DEEP_DIVE.md` (Spec reference, 600+ lines)
- `FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md` (Feature matrix, gaps)
- `FASTMCP_MIDDLEWARE.md` (Middleware patterns)
- `FASTMCP_STORAGE_EVENTSTORE.md` (Storage backends)
- `FASTMCP_PROGRESS_TASKS.md` (Progress & tasks API)
- `FASTMCP_TRANSFORMS_DEPLOYMENT.md` (Transforms)
- `FASTMCP_SAMPLING_TELEMETRY.md` (Sampling & telemetry)
- `FASTMCP_ELICITATION_CONTEXT.md` (Elicitation patterns)
- `MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md` (Parity audit, 800+ lines)

---

## 2. FastMCP Architecture

### 2.1 Server Model

```
┌─────────────────────────────────────────────────────────────┐
│                    FastMCP Server                            │
├─────────────────────────────────────────────────────────────┤
│  Components:                                                │
│    • Tools (@mcp.tool)                                       │
│    • Resources (@mcp.resource)                               │
│    • Resource Templates (RFC 6570)                           │
│    • Prompts (@mcp.prompt)                                   │
│                                                              │
│  Context API:                                                │
│    • ctx.elicit() - User input                               │
│    • ctx.sample() - LLM completion                           │
│    • ctx.report_progress() - Progress updates                │
│    • ctx.log() - Logging                                     │
│    • ctx.get_state() - State management                      │
│                                                              │
│  Pipeline:                                                   │
│    Middleware → Transforms → Providers → Client              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Flow

**List Operations** (Pure Function Pattern):

```
Provider → [Provider Transforms] → [Server Transforms] → Client
```

**Get Operations** (Middleware Pattern):

```
Client → [Server Transforms] → [Provider Transforms] → Provider → [Reverse Mapping] → Client
```

### 2.3 Transport Options

| Transport           | Spec   | Use Case                | thegent            |
| ------------------- | ------ | ----------------------- | ------------------ |
| **STDIO**           | Core   | Local development, CLI  | ✅ Default         |
| **Streamable HTTP** | Core   | Remote, web integration | ✅ `thegent serve` |
| **SSE**             | Legacy | Legacy clients          | ⚠️ Deprecated      |

---

## 3. Core Components

### 3.1 Tools

**Basic Tool Definition**:

```python
from fastmcp import FastMCP

mcp = FastMCP("thegent")


@mcp.tool()
def thegent_run(command: str, cwd: str | None = None) -> str:
    """Run a command."""
    # Implementation
    return result
```

**Tool with Annotations**:

```python
@mcp.tool(readOnlyHint=True, timeout=30, tags=["execution"])
def thegent_status() -> dict:
    """Get thegent status."""
    return {"status": "running"}
```

**Tool with Structured Output**:

```python
from pydantic import BaseModel


class RunResult(BaseModel):
    returncode: int
    stdout: str
    stderr: str


@mcp.tool()
def thegent_run(command: str) -> RunResult:
    """Run command with structured output."""
    # Implementation
    return RunResult(returncode=0, stdout="...", stderr="")
```

**ToolResult Pattern**:

```python
from fastmcp import ToolResult


@mcp.tool()
def thegent_run(command: str) -> ToolResult:
    """Run command with metadata."""
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True)
    execution_time = time.time() - start_time

    return ToolResult(
        content=f"Command executed: {result.returncode}",
        structured_content={
            "returncode": result.returncode,
            "stdout": result.stdout.decode(),
            "stderr": result.stderr.decode(),
        },
        meta={"execution_time_ms": execution_time * 1000},
    )
```

### 3.2 Resources

**Basic Resource**:

```python
@mcp.resource("thegent://sessions")
def list_sessions() -> list[dict]:
    """List all sessions."""
    return [{"id": "123", "status": "running"}]


@mcp.resource("thegent://session/{id}/meta")
def get_session_meta(id: str) -> dict:
    """Get session metadata."""
    return {"id": id, "status": "running"}
```

**Resource with Templates** (RFC 6570):

```python
@mcp.resource("thegent://session/{id}/meta{?include_contract}")
def get_session_meta(id: str, include_contract: bool = False) -> dict:
    """Get session metadata with optional contract."""
    meta = {"id": id, "status": "running"}
    if include_contract:
        meta["contract"] = get_contract(id)
    return meta
```

### 3.3 Prompts

```python
@mcp.prompt()
def agent_prompt(agent_type: str) -> str:
    """Get agent prompt template."""
    templates = {"planner": "You are a planning agent...", "executor": "You are an execution agent..."}
    return templates.get(agent_type, "Default prompt")
```

---

## 4. Elicitation & Context API

### 4.1 User Input Elicitation

**Basic Elicitation**:

```python
from fastmcp.dependencies import CurrentContext
from fastmcp import AcceptedElicitation, DeclinedElicitation, CancelledElicitation


@mcp.tool()
async def configure_agent(ctx: CurrentContext = CurrentContext()) -> str:
    """Configure agent with user input."""
    result = await ctx.elicit("Working directory?", response_type=str)

    if isinstance(result, AcceptedElicitation):
        return f"Using: {result.data}"
    elif isinstance(result, DeclinedElicitation):
        return "User declined configuration"
    elif isinstance(result, CancelledElicitation):
        return "User cancelled"
```

**Single-Select Options**:

```python
config_options = {
    "dev": {"title": "Development (local, no auth)"},
    "prod": {"title": "Production (cloud, auth required)"},
}

result = await ctx.elicit("Environment?", response_type=config_options)
selected_env = result.data  # "dev" or "prod"
```

**Multi-Select Options**:

```python
options = ["email", "slack", "webhook"]
result = await ctx.elicit("Notifications?", response_type=options)
selected = result.data  # ["email", "slack"] etc.
```

**Structured Data Input**:

```python
from pydantic import BaseModel


class AgentConfig(BaseModel):
    name: str
    timeout_secs: int
    retry_count: int


result = await ctx.elicit("Configure the agent", response_type=AgentConfig)
if isinstance(result, AcceptedElicitation):
    config: AgentConfig = result.data
    await spawn_agent(config)
```

### 4.2 Context Patterns

**Pattern 1: Optional Elicitation with Fallback**:

```python
result = await ctx.elicit("Feature flag?", response_type=str)
if isinstance(result, AcceptedElicitation):
    flag_value = result.data
else:
    flag_value = "default"  # Fallback if user declines/cancels
```

**Pattern 2: Conditional Elicitation Chain**:

```python
env_result = await ctx.elicit("Environment?", response_type=["dev", "prod"])
if isinstance(env_result, AcceptedElicitation):
    if env_result.data == "prod":
        # Additional elicitation for production
        auth_result = await ctx.elicit("Auth method?", response_type=["oauth", "api_key"])
```

### 4.3 Logging

**Contextual Logging**:

```python
@mcp.tool()
async def thegent_run(ctx: CurrentContext = CurrentContext(), command: str) -> str:
    """Run command with logging."""
    await ctx.log("info", f"Executing: {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True)
        await ctx.log("info", f"Completed: {result.returncode}")
        return result.stdout.decode()
    except Exception as e:
        await ctx.log("error", f"Failed: {e}")
        raise
```

**Structured Logging**:

```python
await ctx.log(
    "info",
    "Command executed",
    metadata={"command": command, "returncode": result.returncode, "execution_time_ms": execution_time},
)
```

---

## 5. Progress & Tasks

### 5.1 Progress Reporting

**Basic Progress**:

```python
@mcp.tool()
async def long_running_task(ctx: CurrentContext = CurrentContext()) -> str:
    """Long-running task with progress."""
    total_steps = 100

    for i in range(total_steps):
        # Do work
        await ctx.report_progress(i, total_steps, f"Step {i}/{total_steps}")
        await asyncio.sleep(0.1)

    return "Completed"
```

**Progress Dependency**:

```python
from fastmcp.dependencies import Progress


@mcp.tool()
async def my_tool(progress: ProgressLike = Progress()) -> str:
    """Tool with progress dependency."""
    await progress.set_total(100)

    for i in range(100):
        await progress.increment()
        await progress.set_message(f"Processing {i}/100")
        # Do work

    return "Done"
```

### 5.2 Background Tasks

**Task Configuration**:

```python
from fastmcp import TaskConfig
from datetime import timedelta


@mcp.tool(task=TaskConfig(mode="optional", poll_interval=timedelta(seconds=5)))
async def thegent_run(command: str) -> dict:
    """Run command as background task."""
    # Implementation
    return {"task_id": "123", "status": "running"}
```

**Task Modes**:

- **`forbidden`**: No task support; returns error if requested
- **`optional`**: Sync or task; client chooses (recommended)
- **`required`**: Must use task; returns error if not

**Sync Code in Async Handler**:

```python
@mcp.tool(task=TaskConfig(mode="optional"))
async def thegent_run(command: str) -> dict:
    """Run sync code in async handler."""

    def run_impl():
        # Sync implementation
        return subprocess.run(command, shell=True, capture_output=True)

    return await asyncio.to_thread(run_impl)
```

---

## 6. Middleware System

### 6.1 Middleware Order

Middleware executes in **order added**. First added = outermost (runs first in, last out).

```python
mcp.add_middleware(ErrorHandlingMiddleware())  # 1st in, last out
mcp.add_middleware(RateLimitingMiddleware())  # 2nd in, 2nd out
mcp.add_middleware(TimingMiddleware())  # 3rd in, first out
mcp.add_middleware(LoggingMiddleware())  # 4th in, first out
```

**Recommended Order**: ErrorHandling → RateLimiting → Timing → Logging

### 6.2 Response Caching Middleware

```python
from fastmcp.server.middleware.caching import (
    ResponseCachingMiddleware,
    CallToolSettings,
    ListToolsSettings,
    ReadResourceSettings,
)

mcp.add_middleware(
    ResponseCachingMiddleware(
        list_tools_settings=ListToolsSettings(ttl=30),
        call_tool_settings=CallToolSettings(included_tools=["thegent_ps", "thegent_list_agents"], ttl=60),
        read_resource_settings=ReadResourceSettings(enabled=False),
    )
)
```

**Settings Classes**:

- `ListToolsSettings`: Cache `tools/list` responses
- `CallToolSettings`: Cache specific tool calls
- `ListResourcesSettings`: Cache `resources/list` responses
- `ReadResourceSettings`: Cache `resources/read` responses
- `ListPromptsSettings`: Cache `prompts/list` responses
- `GetPromptSettings`: Cache `prompts/get` responses

**Per-Settings Options**:

- `included_*` / `excluded_*`: Whitelist or blacklist
- `ttl`: Time-to-live in seconds
- `enabled`: Enable/disable caching

### 6.3 Rate Limiting Middleware

```python
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware

mcp.add_middleware(RateLimitingMiddleware(calls_per_minute=60, calls_per_hour=1000))
```

**Options**:

- `calls_per_minute`: Per-minute limit
- `calls_per_hour`: Per-hour limit
- `key_func`: Custom key function for rate limiting

### 6.4 Custom Middleware

```python
from fastmcp.server.middleware import Middleware


class TimingMiddleware(Middleware):
    """Add execution time to tool results."""

    async def on_call_tool(self, tool_name: str, arguments: dict, call_next):
        start_time = time.time()
        result = await call_next()
        execution_time = time.time() - start_time

        if isinstance(result, ToolResult):
            result.meta["execution_time_ms"] = execution_time * 1000

        return result
```

---

## 7. Storage Backends

### 7.1 Memory Store (Default)

```python
from key_value.aio.stores.memory import MemoryStore

cache_store = MemoryStore()
```

- **Use Case**: Development, single-process
- **Persistence**: Data lost on restart
- **Setup**: No setup required

### 7.2 Disk Store

```python
from key_value.aio.stores.disk import DiskStore

middleware = ResponseCachingMiddleware(cache_storage=DiskStore(directory="/var/cache/fastmcp"))
```

- **Use Case**: Single-server production
- **Persistence**: Data persists across restarts
- **Limitation**: Not suitable for distributed deployments

### 7.3 Redis Store

```python
from key_value.aio.stores.redis import RedisStore

middleware = ResponseCachingMiddleware(cache_storage=RedisStore(host="redis.example.com", port=6379))
```

- **Use Case**: Distributed production, multi-server deployments
- **Persistence**: Shared across servers
- **Features**: Built-in TTL support

### 7.4 Encryption Wrapper (OAuth)

```python
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet

key = Fernet.generate_key()
encrypted_store = FernetEncryptionWrapper(DiskStore(directory="/var/lib/fastmcp/oauth"), key=key)
```

---

## 8. Transforms & Providers

### 8.1 Namespace Transform

**Multi-Provider Aggregation**:

```python
from fastmcp.server.transforms import NamespaceTransform

# Aggregate multiple providers under namespaces
mcp.add_transform(NamespaceTransform(namespace="thegent", provider=thegent_provider))

mcp.add_transform(NamespaceTransform(namespace="external", provider=external_provider))

# Tools become: thegent:run, external:search
```

### 8.2 Tool Transform

**Schema/Description Overrides**:

```python
from fastmcp.server.transforms import ToolTransform

mcp.add_transform(
    ToolTransform(
        tool_name="thegent_run",
        description="Run a command (enhanced)",
        schema_overrides={
            "properties": {"command": {"description": "Command to execute", "pattern": "^[a-zA-Z0-9_\\-]+"}}
        },
    )
)
```

### 8.3 ResourcesAsTools Transform

**Expose Resources to Tool-Only Clients**:

```python
from fastmcp.server.transforms import ResourcesAsTools

mcp.add_transform(ResourcesAsTools())
```

Converts resources like `thegent://sessions` into tools like `thegent_read_resource_sessions`.

### 8.4 PromptsAsTools Transform

**Expose Prompts to Tool-Only Clients**:

```python
from fastmcp.server.transforms import PromptsAsTools

mcp.add_transform(PromptsAsTools())
```

---

## 9. Transport & Protocols

### 9.1 STDIO Transport (Default)

```python
# Default for local development
mcp.run()
```

- **Use Case**: Local development, CLI tools
- **Clients**: Claude Code, Cursor, Codex (local)

### 9.2 HTTP Transport

```python
from fastmcp import FastMCP

mcp = FastMCP("thegent")

# Run HTTP server
mcp.run(transport="http", host="0.0.0.0", port=3847)
```

- **Use Case**: Remote access, web integration
- **Clients**: Claude Code, Cursor (remote)
- **Features**: Streamable HTTP, SSE support

### 9.3 SSE Polling (EventStore)

```python
from fastmcp.server.event_store import EventStore

event_store = EventStore(storage=RedisStore(...))

# Server sends events
await event_store.publish("tools/list_changed", {"tool": "thegent_run"})

# Client polls with Last-Event-ID
# Server responds with events since Last-Event-ID
```

---

## 10. Client Compatibility

### 10.1 Client Support Matrix

| Feature              | Claude Code | Cursor | Codex | Notes                    |
| -------------------- | ----------- | ------ | ----- | ------------------------ |
| **STDIO**            | ✅          | ✅     | ✅    | All support              |
| **HTTP**             | ✅          | ✅     | ⚠️    | Codex: local only        |
| **Elicitation**      | ⚠️          | ⚠️     | ⚠️    | May not be supported     |
| **Progress**         | ✅          | ✅     | ⚠️    | Codex: unknown           |
| **Background Tasks** | ⚠️          | ⚠️     | ⚠️    | SEP-1686 support unclear |
| **Sampling**         | ⚠️          | ⚠️     | ⚠️    | Requires handler         |

### 10.2 Elicitation Support

**Critical for Blocking UX**:

- Elicitation lets tools pause and request user input
- Protocol-native way to implement "blocking" behavior
- **Client Requirement**: Must implement elicitation handler

**Verification**:

```python
# Test tool that uses elicitation
@mcp.tool()
async def test_elicitation(ctx: CurrentContext = CurrentContext()) -> str:
    result = await ctx.elicit("Test?", response_type=str)
    return f"Result: {result}"
```

**If client doesn't support**: `ctx.elicit()` raises error

### 10.3 Background Tasks Support

**SEP-1686**: Background Tasks specification

**Client Requirements**:

- Implement `tasks/list` endpoint
- Implement `tasks/get` endpoint
- Poll task status

**Verification**:

```python
@mcp.tool(task=TaskConfig(mode="required"))
async def test_task() -> dict:
    return {"task_id": "123"}
```

---

## 11. Implementation Patterns

### 11.1 Tool with Dependency Injection

```python
from fastmcp.dependencies import Depends


def get_default_cwd() -> str:
    """Get default working directory."""
    return os.getcwd()


@mcp.tool()
def thegent_run(command: str, cwd: str = Depends(get_default_cwd)) -> str:
    """Run command with dependency injection."""
    return subprocess.run(command, cwd=cwd, shell=True, capture_output=True).stdout.decode()
```

### 11.2 Error Handling Pattern

```python
from fastmcp import ToolResult


@mcp.tool()
async def thegent_run(command: str) -> ToolResult:
    """Run command with error handling."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True)
        return ToolResult(
            content=f"Command executed: {result.returncode}",
            structured_content={"returncode": result.returncode, "stdout": result.stdout.decode()},
        )
    except Exception as e:
        return ToolResult(content=f"Error: {e}", structured_content={"error": str(e)}, meta={"error": True})
```

### 11.3 Resource with Template Pattern

```python
@mcp.resource("thegent://session/{id}/meta{?include_contract,include_logs}")
def get_session_meta(id: str, include_contract: bool = False, include_logs: bool = False) -> dict:
    """Get session metadata with optional parameters."""
    meta = {"id": id, "status": "running"}

    if include_contract:
        meta["contract"] = get_contract(id)

    if include_logs:
        meta["logs"] = get_logs(id)

    return meta
```

---

## 12. Best Practices

### 12.1 Tool Design

1. **Use Type Hints**: Enables automatic schema generation
2. **Provide Descriptions**: Clear docstrings for tools
3. **Use ToolResult**: Include metadata, structured content
4. **Handle Errors**: Graceful error handling
5. **Use Annotations**: `readOnlyHint`, `timeout`, `tags`

### 12.2 Middleware Order

1. **Error Handling**: Outermost (catches all errors)
2. **Rate Limiting**: Before expensive operations
3. **Timing**: Measure execution time
4. **Logging**: Innermost (logs everything)

### 12.3 Caching Strategy

1. **Cache Read-Heavy Tools**: `thegent_ps`, `thegent_list_agents`
2. **Cache List Operations**: `tools/list`, `resources/list`
3. **Don't Cache Writes**: `thegent_run`, `thegent_bg`
4. **Use Appropriate TTL**: 30s for lists, 60s for reads

### 12.4 Progress Reporting

1. **Report Frequently**: Update every 1-5 seconds
2. **Include Messages**: Descriptive progress messages
3. **Set Total**: Always set total when known
4. **Handle Cancellation**: Check for cancellation signals

---

## 13. Troubleshooting

### 13.1 Common Issues

**Issue**: Elicitation not working

- **Solution**: Verify client supports elicitation
- **Solution**: Check elicitation handler implementation
- **Solution**: Use fallback pattern if not supported

**Issue**: Progress not updating

- **Solution**: Verify client supports progress
- **Solution**: Check progress handler implementation
- **Solution**: Use logging as fallback

**Issue**: Background tasks not working

- **Solution**: Verify client supports SEP-1686
- **Solution**: Check task endpoints implementation
- **Solution**: Use sync mode as fallback

**Issue**: Caching not working

- **Solution**: Check storage backend configuration
- **Solution**: Verify middleware order
- **Solution**: Check TTL settings

### 13.2 Debugging

**Enable Debug Logging**:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

**Check Middleware Execution**:

```python
class DebugMiddleware(Middleware):
    async def on_call_tool(self, tool_name: str, arguments: dict, call_next):
        print(f"Calling tool: {tool_name}")
        result = await call_next()
        print(f"Tool result: {result}")
        return result
```

---

## References

- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Specification](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [MCP Full Parity & FastMCP Audit](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md)
- [Multi-Platform Parity Master Plan](../plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md)
- [MCP Tool Optimization Plan](../plans/MCP_TOOL_OPTIMIZATION_PLAN.md)

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Implementation guide
- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - Parity audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

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

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

## FastMCP Deployment Gates

| Gate               | Pass Criteria                                            | Verification Command                                    | Blocker if Fails             |
| ------------------ | -------------------------------------------------------- | ------------------------------------------------------- | ---------------------------- |
| Interface parity   | Required tools, resources, and prompts are discoverable  | `python -m pytest tests/mcp/test_parity.py -q`          | Missing protocol surface     |
| Contract stability | Core tool schemas unchanged or migration documented      | `python -m pytest tests/mcp/test_tool_contracts.py -q`  | Breaking client integrations |
| Transport health   | SSE/HTTP endpoint answers MCP initialize/list calls      | `curl -fsS http://localhost:8000/mcp/health`            | Server not reachable         |
| Security baseline  | Auth, CORS, and rate limits enabled in production config | `python -m pytest tests/mcp/test_security_config.py -q` | Unsafe external exposure     |
| Observability      | Structured logs and error counters emitted per request   | `python -m pytest tests/mcp/test_observability.py -q`   | Blind incident response      |

- Deploy only when all five gates pass in the same CI run.
- Require rollback artifact (`last-known-good` image/tag) before promoting to production.
- Freeze deploy if error-rate canary exceeds `2%` for `10` consecutive minutes.

## FastMCP Incident Triage

- **1) Classify impact**: mark `SEV-1` for total tool outage, `SEV-2` for partial degradation, `SEV-3` for single-tool faults.
- **2) Confirm blast radius**: check failed methods (`initialize`, `list_tools`, `call_tool`) and affected clients.
- **3) Stabilize first**: rollback to last-known-good release if initialization failure persists beyond `5` minutes.
- **4) Isolate layer**: verify transport (network/ingress), then auth/config, then tool runtime exceptions.
- **5) Capture evidence**: save request IDs, error signatures, deploy SHA, and first-failure timestamp.
- **6) Recover safely**: canary patched build to `10%` traffic for `15` minutes before full restore.
- **7) Close out**: publish incident note with root cause, mitigation, and one preventive action with owner/date.

| Signal                       | Immediate Action                                | Escalation Trigger                        |
| ---------------------------- | ----------------------------------------------- | ----------------------------------------- |
| `initialize` failures >20%   | Roll back and restart MCP service               | Continues >5 minutes after rollback       |
| `call_tool` timeout p95 >15s | Reduce concurrency and disable heavy tools      | Two consecutive 5-minute windows breached |
| Auth failures spike          | Rotate credentials and validate issuer/audience | Any production tenant fully blocked       |
| Error budget burn >10%/hour  | Halt deploys and open incident channel          | Burn persists for 30 minutes              |

## Tool Registration Checklist

- Confirm each tool has a stable name, description, and explicit input schema.
- Fail startup if duplicate tool names or missing required schema fields are detected.
- Verify registration order is deterministic and `list_tools` output is identical across restarts.
- Run a startup smoke call for every registered tool and block deploy on any failure.
- Record tool version/hash in logs to correlate runtime failures with registry changes.

## Runtime Failure Modes

- **Tool timeout**: long-running handler exceeds request deadline and returns transport timeout.
- **Schema mismatch**: runtime payload violates declared schema and is rejected before execution.
- **Registration drift**: expected tool is absent or renamed, causing client lookup failures.
- **Dependency outage**: downstream API/database failure propagates as tool execution errors.
- **Concurrency saturation**: worker pool exhaustion leads to queue growth and elevated p95 latency.

## Observability Hooks

- Emit `request_id`, `tool_name`, `tenant`, `status_code`, and latency in every request log line.
- Increment counters for `initialize`, `list_tools`, and `call_tool` success/failure paths; alert on missing metric streams.
- Record p50/p95/p99 latency and timeout counts per tool every minute, with a deploy SHA tag.
- Capture structured error events with exception class, normalized message, and first-seen timestamp.
- Add a `health/ready` probe that verifies tool registry load and one lightweight tool invocation.

## Rollout Abort Conditions

- Abort canary if `initialize` error rate exceeds `1%` for `5` consecutive minutes.
- Abort rollout if any tenant has `call_tool` failure rate above `3%` in two back-to-back windows.
- Abort immediately on schema/contract mismatch detected between server `list_tools` and pinned client manifest.
- Abort if p95 `call_tool` latency regresses by `>50%` versus pre-rollout baseline for `10` minutes.
- Abort if error budget burn exceeds `15%` per hour after rollout start; roll back to last-known-good artifact.

## Transport Health Checks

- Verify liveness and readiness before protocol checks: `curl -fsS http://localhost:8000/health && curl -fsS http://localhost:8000/ready`.
- Confirm MCP transport endpoint responds: `curl -i http://localhost:8000/mcp/health`.
- Smoke-test initialize/list path via tests: `python -m pytest tests/mcp/test_transport_health.py -q`.
- Watch transport errors in real time during canary: `rg -n "initialize|list_tools|timeout|connection reset" logs/mcp*.log`.

## Registration Drift Checks

- Snapshot current registry output: `curl -fsS http://localhost:8000/mcp/list_tools | jq -S . > /tmp/list_tools.current.json`.
- Diff against pinned manifest: `diff -u config/mcp/list_tools.manifest.json /tmp/list_tools.current.json`.
- Detect duplicate or missing tool names fast: `jq -r '.tools[].name' /tmp/list_tools.current.json | sort | uniq -cd`.
- Enforce drift guard in CI: `python -m pytest tests/mcp/test_registration_drift.py -q`.

## Tool Timeout Budgeting

- Set hard per-call timeout defaults in config and commit them: `rg -n "timeout|deadline" config/`.
- Fail fast on regressions with timeout-focused tests: `python -m pytest tests/mcp -k timeout -q`.
- Track live timeout pressure during canary: `rg -n "timeout|deadline exceeded" logs/mcp*.log | tail -n 50`.
- Recalculate per-tool budget weekly from p95 latency and enforce in CI docs/checklists.

## Operator Recovery Steps

- Declare incident scope and freeze deploys: `echo "SEV-2 MCP degradation"`.
- Verify transport and registry quickly: `curl -fsS http://localhost:8000/ready && curl -fsS http://localhost:8000/mcp/list_tools | jq '.tools|length'`.
- Roll back to last-known-good artifact if initialize/call failures persist for 5 minutes.
- Restart service and confirm recovery path: `systemctl restart thegent-mcp && python -m pytest tests/mcp/test_transport_health.py -q`.
- Capture closure evidence for postmortem: `date -u && git rev-parse HEAD && rg -n "error|timeout" logs/mcp*.log | tail -n 100`.

## Handler Reliability Checks

- Run focused handler tests before deploy: `python -m pytest tests/mcp -k "handler and (success or timeout or schema)" -q`.
- Smoke-test each critical tool path manually: `python -m pytest tests/mcp/test_tool_smoke.py -q`.
- Fail release on fresh handler exceptions: `rg -n "Unhandled|Traceback|handler failed" logs/mcp*.log | tail -n 50`.
- Re-verify after restart to catch warmup issues: `systemctl restart thegent-mcp && python -m pytest tests/mcp/test_tool_smoke.py -q`.

## Runtime Escalation Path

- **T+0–5 min**: On-call operator triages, freezes deploys, and captures failing request IDs.
- **T+5–10 min**: Service owner joins; roll back to last-known-good if error rate remains elevated.
- **T+10–20 min**: Platform/SRE joins for infra checks; run `curl -fsS http://localhost:8000/ready` and transport smoke tests.
- **T+20+ min**: Escalate to incident commander, open status comms, and assign owner/date for corrective action.

## Service Restart Checklist

- Freeze deploys and announce restart window in the incident channel.
- Capture baseline before restart: `date -u && systemctl status thegent-mcp --no-pager | head -n 20`.
- Restart cleanly: `systemctl restart thegent-mcp`.
- Confirm process recovery: `systemctl is-active thegent-mcp && systemctl status thegent-mcp --no-pager | head -n 20`.
- Unfreeze deploys only after probes and one MCP smoke call succeed.

## Health Probe Commands

- Liveness: `curl -fsS http://localhost:8000/health`.
- Readiness: `curl -fsS http://localhost:8000/ready`.
- MCP endpoint check: `curl -fsS http://localhost:8000/mcp/health`.
- Tool registry sanity: `curl -fsS http://localhost:8000/mcp/list_tools | jq '.tools | length'`.
- Quick error tail after restart: `journalctl -u thegent-mcp -n 100 --no-pager | rg -n "error|timeout|exception"`.

## Schema Compatibility Checks

- Pin and diff tool schemas before rollout: `curl -fsS http://localhost:8000/mcp/list_tools | jq -S '.tools[] | {name,inputSchema}' > /tmp/schemas.current.json && diff -u config/mcp/schemas.pinned.json /tmp/schemas.current.json`.
- Run contract/parity tests together: `python -m pytest tests/mcp/test_tool_contracts.py tests/mcp/test_parity.py -q`.
- Block promotion if any required field changed without migration notes in release docs.

## Service Recovery Timeline

- **T+0–3 min:** Freeze deploys, capture scope, and run probes: `curl -fsS http://localhost:8000/health && curl -fsS http://localhost:8000/ready`.
- **T+3–8 min:** If failures persist, restart service and validate registry: `systemctl restart thegent-mcp && curl -fsS http://localhost:8000/mcp/list_tools | jq '.tools|length'`.
- **T+8–15 min:** If still degraded, roll back to last-known-good artifact and rerun transport smoke: `python -m pytest tests/mcp/test_transport_health.py -q`.

## Recovery Escalation Thresholds

- Escalate to service owner if `initialize`/`call_tool` failures stay above `1%` for `5` minutes.
- Escalate to platform/SRE if readiness fails `3` checks in a row: `for i in 1 2 3; do curl -fsS http://localhost:8000/ready || true; sleep 20; done`.
- Escalate to incident commander immediately on schema drift: `curl -fsS http://localhost:8000/mcp/list_tools | jq -S . > /tmp/live.json && diff -u config/mcp/list_tools.manifest.json /tmp/live.json`.

## Post-Incident Checklist

- Record closure evidence: `date -u && git rev-parse HEAD && journalctl -u thegent-mcp -n 150 --no-pager | tail -n 80`.
- Confirm recovery guardrails: `python -m pytest tests/mcp/test_transport_health.py tests/mcp/test_registration_drift.py -q`.
- Publish follow-ups with owner/date and rollback decision in the incident doc before unfreezing deploys.

## Tool Contract Guardrails

- Generate current tool contract snapshot: `curl -fsS http://localhost:8000/mcp/list_tools | jq -S '.tools[] | {name,inputSchema}' > /tmp/tool-contracts.current.json`.
- Compare against pinned contract baseline: `diff -u config/mcp/tool-contracts.pinned.json /tmp/tool-contracts.current.json`.
- Gate merges with focused contract test: `python -m pytest tests/mcp/test_tool_contracts.py -q`.
- Require release note + owner approval before promoting any schema/name change.

## Runtime Dependency Checks

- Verify required runtime libs at startup: `python -m pip check`.
- Assert key binaries are present and versioned: `python --version && jq --version && curl --version | head -n 1`.
- Run dependency health smoke before deploy: `python -m pytest tests/mcp/test_transport_health.py -q`.
- Fail deployment if any check fails; capture evidence in incident/release log.

## Throughput Guardrails

- Enforce worker and queue caps before rollout: `rg -n "max_workers|max_concurrency|queue" config/`.
- Gate deployment on latency and timeout tests: `python -m pytest tests/mcp -k "latency or timeout or concurrency" -q`.
- Watch live saturation indicators during canary: `rg -n "queue|backlog|p95|p99|timeout" logs/mcp*.log | tail -n 80`.
- Pause promotion if p95 grows `>30%` over baseline for `10` minutes; reduce concurrency and retest.

## Fallback-Free Failure Policy

- Treat any tool error as terminal for the request; do not retry through alternate handlers or legacy paths.
- Fail fast on drift or schema mismatches: `python -m pytest tests/mcp/test_registration_drift.py tests/mcp/test_tool_contracts.py -q`.
- Block merge when fallback patterns appear: `rg -n "except: pass|except Exception|fallback|legacy|compat" thegent/`.
- Require explicit rollback or fix-forward decision in incident notes before resuming deploys.
