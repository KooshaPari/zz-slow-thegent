<DONE>
# FastMCP Implementation Guide for thegent

**Date:** 2026-02-14 | **Updated**: 2026-02-17
**Purpose:** Consolidated extraction of all implementable items, patterns, and design decisions from FastMCP research documents.
**Status:** Implementation Guide | **P3 Polish**: Summary table, cross-links, next actions added
**Related**:

- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - MCP parity audit
- [MCP_TOOL_OPTIMIZATION_PLAN.md](../plans/MCP_TOOL_OPTIMIZATION_PLAN.md) - MCP tool optimization
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream

---

## Document Summary

| Aspect                      | Details                                                                    |
| --------------------------- | -------------------------------------------------------------------------- |
| **Document Type**           | Implementation guide                                                       |
| **Lines**                   | ~1,332 lines                                                               |
| **Sections**                | 10+ sections covering FastMCP features, patterns, implementation           |
| **Status**                  | Guide complete, ready for implementation                                   |
| **Key Features**            | Elicitation API, Context API, Task mode, Tool patterns, Storage/EventStore |
| **Implementation Priority** | High (core MCP functionality)                                              |
| **Performance Targets**     | <50ms tool execution (p95), <100ms elicitation response                    |
| **BACKLOG Items**           | 5 items extracted (see Next Actions)                                       |

---

## Next Actions (WORK_STREAM IDs)

| ID                           | Action                                                                    | Priority | Depends                 | Status  |
| ---------------------------- | ------------------------------------------------------------------------- | -------- | ----------------------- | ------- |
| `fastmcp-elicitation-api`    | Implement FastMCP elicitation API (structured input, single/multi-select) | P1       | -                       | BACKLOG |
| `fastmcp-context-api`        | Implement FastMCP Context API (foreground/background modes)               | P1       | -                       | BACKLOG |
| `fastmcp-task-mode`          | Implement FastMCP task mode (background execution)                        | P1       | fastmcp-context-api     | BACKLOG |
| `fastmcp-storage-eventstore` | Implement FastMCP Storage/EventStore integration                          | P2       | fastmcp-context-api     | BACKLOG |
| `fastmcp-tool-patterns`      | Implement FastMCP tool patterns (error handling, retry, validation)       | P2       | fastmcp-elicitation-api | BACKLOG |

**See Also**: [WORK_STREAM.md](../reference/WORK_STREAM.md) for full backlog

---

## 1. Elicitation & Context API

### Key Findings

- FastMCP provides a unified Context interface for user interaction in both foreground (request) and background (task) modes
- Elicitation supports structured responses (primitives, Pydantic models, multi-select)
- Context logging delegates to MCP client for real-time visibility

### Implementable Items

#### 1.1 User Input Elicitation

**Description:** Request structured user input within tool execution
**Implementation:**

```python
from fastmcp.dependencies import CurrentContext


@mcp.tool()
async def configure_agent(ctx: Context = CurrentContext()) -> str:
    # Single value
    result = await ctx.elicit("Working directory?", response_type=str)
    if isinstance(result, AcceptedElicitation):
        return f"Using: {result.data}"
    elif isinstance(result, DeclinedElicitation):
        return "User declined configuration"
    elif isinstance(result, CancelledElicitation):
        return "User cancelled"
```

**Use cases for thegent:**

- Ask for agent configuration parameters
- Elicit prompt refinement options
- Request deployment approval before critical operations

#### 1.2 Single-Select and Multi-Select Options

**Description:** Present categorical choices to user
**Implementation:**

```python
# Single-select with key mapping
config_options = {
    "dev": {"title": "Development (local, no auth)"},
    "prod": {"title": "Production (cloud, auth required)"},
}
result = await ctx.elicit("Environment?", response_type=config_options)
selected_env = result.data  # "dev" or "prod"

# Multi-select array
options = ["email", "slack", "webhook"]
result = await ctx.elicit("Notifications?", response_type=options)
selected = result.data  # ["email", "slack"] etc.
```

**Use cases for thegent:**

- Select which agents to run in parallel
- Choose notification channels for task completion
- Filter resources by deployment region

#### 1.3 Structured Data Input

**Description:** Request complex structured data with validation
**Implementation:**

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

**Use cases for thegent:**

- Request agent parameters with validation
- Elicit deployment configuration
- Capture pipeline execution settings

### Patterns

**Pattern 1: Optional Elicitation with Fallback**

```python
result = await ctx.elicit("Feature flag?", response_type=str)
if isinstance(result, AcceptedElicitation):
    flag_value = result.data
else:
    flag_value = "default"  # Fallback if user declines/cancels
```

**Pattern 2: Conditional Elicitation Chain**

```python
env_result = await ctx.elicit("Environment?", response_type=["dev", "prod"])
if env_result.data == "prod":
    approval = await ctx.elicit("Confirm production?", response_type=["yes", "no"])
    if approval.data != "yes":
        return "Deployment cancelled"
```

### Design Decisions

**Decision 1:** Use `CurrentContext()` dependency for all context injection
**Rationale:** Enables transparent resolution in both sync and async contexts, handles task background mode with Redis access token restoration

**Decision 2:** Always check response type explicitly (AcceptedElicitation, DeclinedElicitation, CancelledElicitation)
**Rationale:** Prevents silent failures; explicit handling ensures user intent is honored

---

## 2. Logging & Client Messaging

### Key Findings

- All logging methods (`info`, `debug`, `error`, `warning`) delegate to `ctx.log()`
- Messages route to connected MCP client in real-time
- Supports structured logging with `extra` metadata

### Implementable Items

#### 2.1 Contextual Logging

**Description:** Send real-time updates to client during tool execution
**Implementation:**

```python
@mcp.tool()
async def long_task(ctx: Context = CurrentContext()) -> str:
    await ctx.info("Starting...")
    await ctx.debug("Internal state: initializing")
    try:
        result = perform_work()
        await ctx.info(f"Completed: {result}")
    except Exception as e:
        await ctx.error(f"Failed: {e}")
        raise
    return result
```

**Use cases for thegent:**

- Report orchestration progress in `thegent_run`
- Log agent startup/shutdown events
- Surface internal errors to client for debugging

#### 2.2 Structured Logging with Metadata

**Description:** Attach structured metadata to log entries
**Implementation:**

```python
await ctx.info(
    "Agent spawned",
    logger_name="thegent.orchestration",
    extra={
        "agent_id": agent.id,
        "agent_name": agent.name,
        "config": agent.config.dict(),
    },
)
```

**Use cases for thegent:**

- Log agent execution metrics (duration, memory, tokens)
- Attach session context (session_id, user_id)
- Record resource allocation details

### Patterns

**Pattern 1: Try-Finally Logging for Cleanup**

```python
await ctx.info("Starting operation...")
try:
    result = await do_work()
finally:
    await ctx.info("Cleaning up...")
```

**Pattern 2: Progressive Log Levels**

```python
await ctx.debug(f"Parsed input: {parsed}")
await ctx.info(f"Processing {len(items)} items")
for item in items:
    await ctx.debug(f"Item {item.id}: {item.status}")
```

---

## 3. Progress Reporting & Tasks

### Key Findings

- Progress reporting works in both foreground and background (Docket) modes
- TaskConfig modes control sync vs. async execution
- asyncio.to_thread enables long-running sync code in async context

### Implementable Items

#### 3.1 Progress Reporting

**Description:** Report incremental progress to client during long-running operations
**Implementation:**

```python
@mcp.tool()
async def thegent_run(
    agents: list[str],
    ctx: Context = CurrentContext(),
    progress: ProgressLike = Progress(),
) -> dict:
    agents_list = await list_agents()
    await progress.set_total(len(agents_list))

    results = []
    for i, agent in enumerate(agents_list):
        await progress.set_message(f"Running {agent.name}...")
        result = await execute_agent(agent)
        results.append(result)
        await progress.increment()

    return {"results": results}
```

**Use cases for thegent:**

- Report multi-agent execution progress
- Show pipeline stage completion
- Track long-running transformations

#### 3.2 Task Mode Configuration

**Description:** Define sync/async execution policy for tools
**Implementation:**

```python
from fastmcp.dependencies import TaskConfig

@mcp.tool(task=TaskConfig(mode="optional", poll_interval=timedelta(seconds=5)))
async def thegent_run(...) -> dict:
    # Client can choose sync or async
    # If async, client polls every 5 seconds
    ...

@mcp.tool(task=TaskConfig(mode="required", poll_interval=timedelta(seconds=2)))
async def expensive_transform(...) -> dict:
    # Client MUST use async mode
    ...

@mcp.tool(task=TaskConfig(mode="forbidden"))
async def quick_lookup(...) -> str:
    # Client cannot use async mode
    ...
```

**Use cases for thegent:**

- `thegent_run`: required or optional depending on client timeout
- Agent execution: required (can exceed HTTP timeout)
- Quick lookups (ps, list_agents): forbidden

#### 3.3 Sync Code in Async Handler (asyncio.to_thread)

**Description:** Execute blocking I/O or sync libraries in threadpool
**Implementation:**

```python
@mcp.tool(task=TaskConfig(mode="optional"))
async def thegent_run(agents: list[str], ctx: Context = CurrentContext()) -> dict:
    # If agents use sync libraries (e.g., subprocess, synchronous DB)
    def run_impl():
        results = []
        for agent in agents:
            result = agent.run()  # Sync, blocking
            results.append(result)
        return {"results": results}

    # Execute in threadpool, don't block event loop
    return await asyncio.to_thread(run_impl)
```

**Use cases for thegent:**

- Execute agents that use subprocess or blocking APIs
- Call synchronous orchestration libraries
- Integrate legacy sync codebase

### Patterns

**Pattern 1: Progress with Checkpoints**

```python
total = sum(agent.estimated_cost for agent in agents)
await progress.set_total(int(total))

for agent in agents:
    await progress.set_message(f"Executing {agent.name}...")
    await execute_agent(agent)
    await progress.increment(int(agent.estimated_cost))
```

**Pattern 2: Task-aware Error Handling**

```python
@mcp.tool(task=TaskConfig(mode="optional"))
async def risky_operation(...) -> dict:
    try:
        result = await do_risky_work()
    except asyncio.TimeoutError:
        await ctx.error("Timeout; client should use task mode")
        raise
    return result
```

### Design Decisions

**Decision 1:** Use `TaskConfig(mode="required")` for `thegent_run`
**Rationale:** Long-running agent execution typically exceeds HTTP timeout; task mode ensures client polls reliably

**Decision 2:** Set `poll_interval=timedelta(seconds=5)` for `thegent_run`
**Rationale:** 5-second granularity balances responsiveness and client load; configurable per deployment

---

## 4. Transforms & Component Exposure

### Key Findings

- Transforms are applied after provider aggregation and can namespace/modify all components
- ResourcesAsTools and PromptsAsTools bridge resources/prompts for tool-only clients
- Namespace transform prefixes all tool names (useful for multi-provider aggregation)

### Implementable Items

#### 4.1 Namespace Transform for Multi-Provider Aggregation

**Description:** Prefix all tools from a provider to avoid naming collisions
**Implementation:**

```python
from fastmcp import FastMCP
from fastmcp.server.transforms import Namespace

main = FastMCP("MainServer")

# Sub-provider for agents
agents_server = FastMCP("AgentServer")


@agents_server.tool()
async def execute() -> str:
    return "exec result"


# Sub-provider for models
models_server = FastMCP("ModelsServer")


@models_server.tool()
async def list_models() -> list[str]:
    return ["gpt-4", "claude"]


# Mount with namespaces
main.add_provider(FastMCPProvider(agents_server).add_transform(Namespace("agents")))
main.add_provider(FastMCPProvider(models_server).add_transform(Namespace("models")))

# Client sees: agents_execute, models_list_models
```

**Use cases for thegent:**

- Organize orchestration tools (thegent_run, thegent_ps → orch_run, orch_ps)
- Separate agent management from execution
- Multi-deployment scenarios (prod_run, staging_run)

#### 4.2 Tool Transform for Schema/Description Overrides

**Description:** Override individual tool metadata without code changes
**Implementation:**

```python
from fastmcp.server.transforms import ToolTransform

server = FastMCP("Server")


@server.tool()
async def thegent_run(agents: list[str]) -> dict:
    """Original description"""
    ...


# Override schema
transform = ToolTransform(
    {
        "thegent_run": {
            "description": "Execute agents in parallel with timeout=600s",
            "input_schema": {
                "properties": {
                    "agents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 10,
                    }
                }
            },
        }
    }
)
server.add_transform(transform)
```

**Use cases for thegent:**

- Document constraints (max agents, timeout bounds) without code changes
- Update tool descriptions based on deployment context
- Add examples to tool schemas

#### 4.3 ResourcesAsTools for Tool-Only Clients

**Description:** Expose resources as tools for clients lacking resource support
**Implementation:**

```python
from fastmcp.server.transforms import ResourcesAsTools

mcp = FastMCP("ThegentServer")


@mcp.resource()
async def thegent_session_logs(session_id: str) -> str:
    """Retrieve session execution logs"""
    return fetch_logs(session_id)


# Add transform to expose as tools
mcp.add_transform(ResourcesAsTools(mcp))

# Clients now see:
# - list_resources tool: returns all resources + templates
# - read_resource tool: reads resource by URI
```

**Use cases for thegent:**

- Expose session/execution logs as resources
- Allow tool-only clients to read thegent metadata
- Bridge resource-based APIs to tool-only integrations

#### 4.4 PromptsAsTools for Tool-Only Clients

**Description:** Expose prompts as tools for clients lacking prompt support
**Implementation:**

```python
from fastmcp.server.transforms import PromptsAsTools

mcp = FastMCP("ThegentServer")


@mcp.prompt()
async def thegent_run_agent(agent_name: str, instructions: str) -> str:
    """Prompt template for running an agent"""
    return f"Run agent {agent_name} with:\n{instructions}"


mcp.add_transform(PromptsAsTools(mcp))

# Clients now see:
# - list_prompts tool: returns all prompts
# - get_prompt tool: renders prompt with args
```

**Use cases for thegent:**

- Expose prompt templates as callable tools
- Allow CLI/tool-only clients to invoke prompts
- Simplify LLM integration for certain clients

### Patterns

**Pattern 1: Multi-Server Aggregation with Namespaces**

```python
main = FastMCP("Main")
for role in ["agents", "models", "integrations"]:
    provider = FastMCPProvider(create_server_for_role(role))
    provider.add_transform(Namespace(role))
    main.add_provider(provider)
```

**Pattern 2: Conditional Resource-to-Tool Bridge**

```python
if client_supports_resources():
    # Expose via resources
    pass
else:
    # Use ResourcesAsTools transform
    mcp.add_transform(ResourcesAsTools(mcp))
```

### Design Decisions

**Decision 1:** Use Namespace transforms at provider level, not server level
**Rationale:** Isolates namespacing to mount point; allows same server used in multiple contexts with different prefixes

**Decision 2:** ResourcesAsTools/PromptsAsTools are late-stage transforms
**Rationale:** Applied after provider aggregation, ensuring consistent behavior across tool generation

---

## 5. Storage Backends & EventStore

### Key Findings

- FastMCP supports pluggable storage: MemoryStore (default), DiskStore (single-server), RedisStore (distributed)
- EventStore enables SSE polling resumability for long-running operations
- FernetEncryptionWrapper required for production OAuth
- PrefixCollectionsWrapper enables multi-tenant isolation

### Implementable Items

#### 5.1 Development Setup (In-Memory)

**Description:** Configure thegent for local development with in-memory storage
**Implementation:**

```python
from fastmcp import FastMCP
from fastmcp.server.event_store import EventStore

mcp = FastMCP("ThegentDev")

# Default: EventStore with MemoryStore (in-memory)
app = mcp.http_app(
    event_store=EventStore(),
    transport="streamable-http",
    retry_interval=2000,
)

# Cache: MemoryStore (default, no config needed)
# Suitable for local dev, single process
```

**Use cases:**

- Local development
- Testing and CI/CD
- Single-process deployments

#### 5.2 Single-Server Production (Disk)

**Description:** Configure thegent for single-server production with persistent disk cache
**Implementation:**

```python
from fastmcp.server.middleware.caching import ResponseCachingMiddleware, CallToolSettings
from key_value.aio.stores.disk import DiskStore

cache_store = DiskStore(directory="/var/cache/thegent")
event_store = EventStore(storage=DiskStore(directory="/var/lib/thegent/events"))

mcp.add_middleware(
    ResponseCachingMiddleware(
        cache_storage=cache_store,
        call_tool_settings=CallToolSettings(
            included_tools=["thegent_ps", "thegent_list_agents", "thegent_list_droids", "thegent_list_models"], ttl=30
        ),
    )
)

app = mcp.http_app(
    event_store=event_store,
    transport="streamable-http",
    retry_interval=2000,
)
```

**Use cases:**

- Single-server production
- Data persistence across restarts
- Moderate caching needs

**Config Variables:**

```bash
THEGENT_CACHE_STORAGE=disk:/var/cache/thegent
FASTMCP_EVENT_STORE_PATH=/var/lib/thegent/events
```

#### 5.3 Distributed Production (Redis)

**Description:** Configure thegent for distributed/multi-server with Redis backend
**Implementation:**

```python
from key_value.aio.stores.redis import RedisStore
from fastmcp.server.middleware.caching import ResponseCachingMiddleware, CallToolSettings

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
cache_store = RedisStore(url=redis_url)
event_store = EventStore(storage=RedisStore(url=redis_url))

mcp.add_middleware(
    ResponseCachingMiddleware(
        cache_storage=cache_store,
        call_tool_settings=CallToolSettings(
            included_tools=["thegent_ps", "thegent_list_agents", "thegent_list_droids", "thegent_list_models"], ttl=30
        ),
    )
)

app = mcp.http_app(
    event_store=event_store,
    transport="streamable-http",
    retry_interval=2000,
)
```

**Use cases:**

- Multi-server deployments
- Kubernetes/container orchestration
- High availability

**Config Variables:**

```bash
REDIS_URL=redis://redis.prod.internal:6379/0
THEGENT_CACHE_STORAGE=redis://redis.prod.internal:6379/1
FASTMCP_DOCKET_URL=redis://redis.prod.internal:6379/2
```

#### 5.4 EventStore with TTL Configuration

**Description:** Set event retention policy for long-running operations
**Implementation:**

```python
from fastmcp.server.event_store import EventStore

# Retain events for 1 hour, max 200 per stream
event_store = EventStore(
    storage=RedisStore(url="redis://localhost"),
    max_events_per_stream=200,
    ttl=3600,  # seconds
)

app = mcp.http_app(
    event_store=event_store,
    transport="streamable-http",
    retry_interval=2000,
)
```

**Use cases:**

- Balance resumability vs. storage cost
- Prevent indefinite event accumulation
- Configure based on expected operation duration

#### 5.5 Multi-Tenant Isolation

**Description:** Namespace cache/event storage per tenant
**Implementation:**

```python
from key_value.aio.wrappers.prefix_collections import PrefixCollectionsWrapper
from key_value.aio.stores.redis import RedisStore


def get_tenant_cache(tenant_id: str):
    base_store = RedisStore(url="redis://localhost")
    return PrefixCollectionsWrapper(key_value=base_store, prefix=f"tenant:{tenant_id}")


# Per-request
tenant_cache = get_tenant_cache(request.tenant_id)
middleware = ResponseCachingMiddleware(cache_storage=tenant_cache)
```

**Use cases:**

- SaaS deployments with multiple tenants
- Namespace isolation in shared infrastructure
- Data privacy compliance

### Patterns

**Pattern 1: Backend Auto-Selection**

```python
storage_url = os.environ.get("THEGENT_CACHE_STORAGE", "memory")
if storage_url == "memory":
    cache_store = MemoryStore()
elif storage_url.startswith("disk:"):
    cache_store = DiskStore(directory=storage_url[5:])
elif storage_url.startswith("redis://"):
    cache_store = RedisStore(url=storage_url)
else:
    raise ValueError(f"Unknown storage: {storage_url}")
```

**Pattern 2: Event Store with Graceful Degradation**

```python
event_store = None
try:
    if os.environ.get("REDIS_URL"):
        event_store = EventStore(storage=RedisStore(url=os.environ["REDIS_URL"]))
except Exception as e:
    logger.warning(f"Failed to init Redis EventStore: {e}; using in-memory")
    event_store = EventStore()  # Fallback to in-memory
```

### Design Decisions

**Decision 1:** Default to MemoryStore for development, require explicit Redis for production
**Rationale:** Zero setup for dev, safe default; production must opt-in to distributed storage

**Decision 2:** Use separate Redis instances/databases for cache, events, and Docket tasks
**Rationale:** Isolation prevents cache eviction from affecting task state; independent TTL policies per data type

**Decision 3:** Set `max_events_per_stream=200, ttl=3600` for EventStore
**Rationale:** Balances resumability (1-hour window) with storage cost; 200 events supports typical long-running tasks

---

## 6. Sampling & Telemetry

### Key Findings

- `ctx.sample()` delegates to client's sampling provider (Claude, etc.)
- `result_type` enables structured output with Pydantic validation
- Fallback handler (e.g., OpenAISamplingHandler) for clients lacking sampling
- `get_tracer()` provides OpenTelemetry span context
- opentelemetry-instrument auto-instruments without code changes

### Implementable Items

#### 6.1 Basic Sampling

**Description:** Invoke LLM sampling via client (usually Claude)
**Implementation:**

```python
@mcp.tool()
async def thegent_analyze_output(output: str, ctx: Context = CurrentContext()) -> str:
    result = await ctx.sample(f"Analyze this output for errors:\n\n{output}")
    return result.text or ""
```

**Use cases for thegent:**

- Analyze agent execution output
- Validate generated code
- Summarize logs and metrics

#### 6.2 Structured Sampling with Validation

**Description:** Request structured LLM output with Pydantic validation
**Implementation:**

```python
from pydantic import BaseModel


class ExecutionSummary(BaseModel):
    status: str  # "success", "partial", "failed"
    agent_count: int
    errors: list[str]
    recommendations: str


@mcp.tool()
async def thegent_summarize_run(session_id: str, ctx: Context = CurrentContext()) -> ExecutionSummary:
    logs = await fetch_session_logs(session_id)

    result = await ctx.sample(f"Summarize this thegent run:\n{logs}", result_type=ExecutionSummary)

    # result.result is ExecutionSummary (validated)
    return result.result
```

**Use cases for thegent:**

- Parse agent output into structured config
- Extract metrics from execution logs
- Generate typed recommendations

#### 6.3 Sampling Fallback Handler

**Description:** Use fallback LLM when client lacks sampling capability
**Implementation:**

```python
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler

mcp = FastMCP(
    name="ThegentServer",
    sampling_handler=OpenAISamplingHandler(api_key=os.environ["OPENAI_API_KEY"], default_model="gpt-4o-mini"),
    sampling_handler_behavior="fallback",  # Use only when client doesn't support
)
```

**Use cases:**

- Offline operation (client lacks Claude)
- Cost-sensitive deployments (OpenAI fallback)
- Development/testing without client

#### 6.4 Prompt Suggestion via Sampling

**Description:** Refine user prompts using LLM
**Implementation:**

```python
@mcp.tool()
async def thegent_suggest_prompt(raw_prompt: str, ctx: Context = CurrentContext()) -> str:
    result = await ctx.sample(
        f"Refine this prompt for clarity and completeness:\n\n{raw_prompt}",
        result_type=str,
    )
    return result.text or raw_prompt
```

**Use cases for thegent:**

- Help users write better agent instructions
- Suggest system prompts for models
- Auto-enhance prompt templates

#### 6.5 Custom Tracing with get_tracer()

**Description:** Add custom OpenTelemetry spans to track execution phases
**Implementation:**

```python
from fastmcp.telemetry import get_tracer


@mcp.tool()
async def thegent_run(agents: list[str], ctx: Context = CurrentContext()) -> dict:
    tracer = get_tracer()

    # Phase 1: Parse & validate
    with tracer.start_as_current_span("parse_agents") as span:
        span.set_attribute("agent.count", len(agents))
        agents_list = await list_agents()
        parsed = [a for a in agents_list if a.name in agents]

    # Phase 2: Execute
    with tracer.start_as_current_span("execute_agents") as span:
        span.set_attribute("execution.count", len(parsed))
        results = []
        for agent in parsed:
            with tracer.start_as_current_span("execute", attributes={"agent.name": agent.name}):
                result = await execute_agent(agent)
                results.append(result)

    return {"results": results}
```

**Use cases:**

- Debug execution bottlenecks
- Monitor agent execution phases
- Export traces to observability platform

#### 6.6 OpenTelemetry Auto-Instrumentation

**Description:** Enable automatic trace export without code changes
**Implementation:**

**Installation:**

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
```

**Startup:**

```bash
export OTEL_SERVICE_NAME=thegent-mcp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
opentelemetry-instrument python -m thegent.main serve --host 127.0.0.1 --port 3847
```

**Docker Compose (for local Jaeger):**

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "4317:4317" # OTLP gRPC
      - "16686:16686" # Jaeger UI

  thegent:
    build: .
    environment:
      OTEL_SERVICE_NAME: thegent-mcp
      OTEL_EXPORTER_OTLP_ENDPOINT: http://jaeger:4317
    command: opentelemetry-instrument python -m thegent.main serve --host 0.0.0.0 --port 3847
    depends_on:
      - jaeger
```

**Auto-generated spans:**

```
- tools/call {name}  # e.g., tools/call thegent_run
- resources/read {uri}
- prompts/get {name}
```

**View traces:**

```
Open http://localhost:16686 in browser
```

### Patterns

**Pattern 1: Sampling with Fallback and Retry**

```python
try:
    result = await ctx.sample(prompt, result_type=ResultType)
    if result.result is None:
        return default_value
    return result.result
except Exception as e:
    await ctx.error(f"Sampling failed: {e}")
    return default_value
```

**Pattern 2: Multi-Phase Tracing**

```python
tracer = get_tracer()
phases = ["validate", "execute", "summarize"]
for phase in phases:
    with tracer.start_as_current_span(phase) as span:
        span.set_attribute("phase", phase)
        await execute_phase(phase)
```

**Pattern 3: Sampling for Dynamic Configuration**

```python
class ConfigUpdate(BaseModel):
    max_agents: int
    timeout_secs: int
    log_level: str


@mcp.tool()
async def suggest_config(current_config: dict, ctx: Context = CurrentContext()) -> ConfigUpdate:
    result = await ctx.sample(f"Suggest improvements to this config:\n{current_config}", result_type=ConfigUpdate)
    return result.result
```

### Design Decisions

**Decision 1:** Use `sampling_handler_behavior="fallback"` for production
**Rationale:** Prefers client's native sampling (Claude); only falls back if unavailable

**Decision 2:** Enable opentelemetry-instrument in production, disable in development
**Rationale:** Production traces exported to APM; dev uses console/file logging

**Decision 3:** Custom spans track user-visible phases (parse, execute, summarize)
**Rationale:** Aligns with operational understanding of thegent execution

---

## 7. Middleware Pipeline

### Key Findings

- Middleware executes in order added (first added = outermost)
- ResponseCachingMiddleware supports fine-grained caching per operation
- RateLimitingMiddleware protects against abuse
- ResponseLimitingMiddleware prevents context overflow

### Implementable Items

#### 7.1 Middleware Execution Order

**Description:** Configure middleware stack in correct order
**Implementation:**

```python
# Order: outermost first (executed first)
mcp.add_middleware(ErrorHandlingMiddleware())  # 1st (outermost)
mcp.add_middleware(RateLimitingMiddleware(...))  # 2nd
mcp.add_middleware(TimingMiddleware())  # 3rd
mcp.add_middleware(ResponseCachingMiddleware(...))  # 4th
mcp.add_middleware(ResponseLimitingMiddleware(...))  # 5th
mcp.add_middleware(LoggingMiddleware())  # 6th (innermost)
```

**Recommended order for thegent:**

```python
mcp.add_middleware(ErrorHandlingMiddleware())
mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=10, burst_capacity=20))
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(ResponseCachingMiddleware(...))
mcp.add_middleware(ResponseLimitingMiddleware(max_size=500_000))
mcp.add_middleware(LoggingMiddleware())
```

**Use cases:**

- Error handling first (outermost) to catch all failures
- Rate limiting second to stop abuse early
- Timing and logging innermost to measure actual work

#### 7.2 Response Caching Middleware

**Description:** Cache responses from read-heavy tools
**Implementation:**

```python
from fastmcp.server.middleware.caching import (
    ResponseCachingMiddleware,
    CallToolSettings,
    ListToolsSettings,
)
from key_value.aio.stores.redis import RedisStore

cache_store = RedisStore(url="redis://localhost")

mcp.add_middleware(
    ResponseCachingMiddleware(
        cache_storage=cache_store,
        list_tools_settings=ListToolsSettings(ttl=30),
        call_tool_settings=CallToolSettings(
            included_tools=[
                "thegent_ps",
                "thegent_list_agents",
                "thegent_list_droids",
                "thegent_list_models",
            ],
            ttl=30,
        ),
    )
)
```

**Use cases for thegent:**

- Cache `list_agents`, `list_droids`, `list_models` (stable, expensive)
- Cache `ps` output (session list, rarely changes)
- 30-second TTL balances freshness and load

#### 7.3 Rate Limiting Middleware

**Description:** Protect thegent_run from abuse
**Implementation:**

```python
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware

mcp.add_middleware(
    RateLimitingMiddleware(
        max_requests_per_second=10.0,
        burst_capacity=20,
    )
)
```

**Use cases:**

- Prevent runaway `thegent_run` invocations
- Protect shared infrastructure
- Manage concurrent execution load

**Tuning:**

- `max_requests_per_second=10`: 10 concurrent thegent_run calls
- `burst_capacity=20`: Allow brief spike to 20 concurrent

#### 7.4 Response Limiting Middleware

**Description:** Prevent large responses from exceeding context limits
**Implementation:**

```python
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware

# Limit all responses to 500KB
mcp.add_middleware(ResponseLimitingMiddleware(max_size=500_000))

# Or limit specific tools
mcp.add_middleware(ResponseLimitingMiddleware(max_size=500_000, tools=["thegent_logs", "thegent_run"]))
```

**Use cases:**

- Prevent `thegent_logs` from returning terabytes of logs
- Protect Claude context window
- Graceful truncation vs. error

#### 7.5 Custom Middleware for thegent_run Logging

**Description:** Add audit trail for critical operations
**Implementation:**

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext


class AuditMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        args = context.message.arguments

        if tool_name == "thegent_run":
            import json

            await ctx.info(
                f"Audit: thegent_run invoked",
                extra={
                    "tool": tool_name,
                    "agents": args.get("agents", []),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        result = await call_next(context)
        return result


mcp.add_middleware(AuditMiddleware())
```

**Use cases:**

- Log all `thegent_run` invocations
- Track who ran what and when
- Compliance and debugging

### Patterns

**Pattern 1: Conditional Caching**

```python
call_tool_settings = CallToolSettings(
    included_tools=[
        "thegent_ps",  # List, rarely changes
        "thegent_list_agents",  # Expensive query
    ],
    excluded_tools=[
        "thegent_run",  # Stateful, never cache
    ],
    ttl=30,
)
```

**Pattern 2: Per-Client Rate Limiting**

```python
def get_client_id(context):
    # Extract user/tenant from auth context
    return context.fastmcp_context.client_id if context.fastmcp_context else "anonymous"


mcp.add_middleware(
    RateLimitingMiddleware(
        max_requests_per_second=10,
        client_id_func=get_client_id,
    )
)
```

### Design Decisions

**Decision 1:** Order: ErrorHandling → RateLimiting → Timing → Caching → ResponseLimiting → Logging
**Rationale:** Errors handled first; rate limit before caching; logging innermost for accurate timing

**Decision 2:** Cache `list_*` and `ps` with 30-second TTL
**Rationale:** Stable data, significant query cost; 30s balances freshness and server load

**Decision 3:** Never cache `thegent_run` responses
**Rationale:** Execution is stateful and non-deterministic; caching violates user expectations

---

## 8. HTTP Deployment & EventStore

### Key Findings

- EventStore enables SSE polling resumability for long HTTP operations
- `ctx.close_sse_stream()` breaks connection to avoid load balancer timeouts
- Streamable HTTP transport recommended for long-running tools
- HTTP app supports stateless (horizontal scaling) and stateful modes

### Implementable Items

#### 8.1 Streamable HTTP with EventStore

**Description:** Deploy thegent over HTTP with resumable long-running operations
**Implementation:**

```python
from fastmcp import FastMCP
from fastmcp.server.event_store import EventStore
from key_value.aio.stores.redis import RedisStore

mcp = FastMCP("ThegentServer")

# Configure EventStore for resumability
event_store = EventStore(storage=RedisStore(url="redis://localhost"), max_events_per_stream=200, ttl=3600)

# Create HTTP app
app = mcp.http_app(
    path="/mcp",
    transport="streamable-http",
    event_store=event_store,
    retry_interval=2000,  # Client reconnects after 2s
)
```

**Use cases:**

- Long-running `thegent_run` operations (>30s)
- HTTP deployments with load balancers
- Browser-based clients with reconnection

#### 8.2 Close SSE Stream Pattern for Load Balancer Timeouts

**Description:** Prevent 30s load balancer timeout during long operations
**Implementation:**

```python
@mcp.tool()
async def thegent_run(agents: list[str], ctx: Context = CurrentContext()) -> dict:
    agents_list = await list_agents()
    results = []

    for i, agent in enumerate(agents_list):
        await ctx.report_progress(i, len(agents_list), f"Running {agent.name}...")
        result = await execute_agent(agent)
        results.append(result)

        # Close connection every 30 iterations to reset LB timeout
        if i % 30 == 0 and i > 0:
            await ctx.close_sse_stream()

    return {"results": results}
```

**Behavior:**

1. Close connection after 30 iterations
2. Client receives 200 OK, reconnects
3. Client resumes from last event in EventStore
4. Seamless from client perspective

**Use cases:**

- Protect against 30-60s load balancer timeouts
- Keep long-running operations resumable
- Support network interruptions gracefully

#### 8.3 Stateless HTTP for Horizontal Scaling

**Description:** Deploy multiple thegent instances behind load balancer
**Implementation:**

```python
app = mcp.http_app(
    path="/mcp",
    transport="streamable-http",
    event_store=EventStore(storage=RedisStore(url="redis://shared")),
    stateless_http=True,
)
```

**Key difference:**

- `stateless_http=True`: New transport per request; all state in Redis
- `stateless_http=False` (default): Session affinity; single transport per session

**Use cases:**

- Kubernetes deployments
- Multiple replicas behind load balancer
- Auto-scaling scenarios

#### 8.4 Pure SSE Transport (Server-Sent Events)

**Description:** Alternative streamable transport without polling overhead
**Implementation:**

```python
app = mcp.http_app(
    path="/mcp/sse",
    transport="sse",  # Pure SSE, no polling
    event_store=event_store,
)
```

**Trade-offs:**

- **SSE:** Lower latency, simpler client; requires long-lived connection
- **Streamable HTTP:** More robust to network interruptions; slight polling overhead

### Patterns

**Pattern 1: Graceful Degradation (HTTP app initialization)**

```python
import os
from fastmcp.server.event_store import EventStore
from key_value.aio.stores.redis import RedisStore

redis_url = os.environ.get("REDIS_URL")
if redis_url:
    event_store = EventStore(storage=RedisStore(url=redis_url))
    transport = "streamable-http"
else:
    event_store = EventStore()  # In-memory, single-process
    transport = "http"  # Fallback to simple HTTP

app = mcp.http_app(
    path="/mcp",
    transport=transport,
    event_store=event_store if transport == "streamable-http" else None,
    retry_interval=2000,
)
```

**Pattern 2: Checkpoint-based Stream Closing**

```python
STREAM_CLOSE_INTERVAL = 30  # iterations


@mcp.tool()
async def thegent_run(agents: list[str], ctx: Context = CurrentContext()) -> dict:
    for i, agent in enumerate(agents):
        result = await execute_agent(agent)

        if i % STREAM_CLOSE_INTERVAL == 0 and i > 0:
            try:
                await ctx.close_sse_stream()
            except Exception as e:
                await ctx.debug(f"Failed to close SSE stream: {e}")
                # Ignore; stream close is optional
```

### Design Decisions

**Decision 1:** Use `transport="streamable-http"` with Redis EventStore for production
**Rationale:** Supports long operations, resumable from interruptions, scales horizontally

**Decision 2:** Close SSE stream every 30 iterations
**Rationale:** Common LB timeout is 30-60s; checkpoint every 30 iterations ensures headroom

**Decision 3:** `stateless_http=True` for Kubernetes, `False` for traditional servers
**Rationale:** Kubernetes uses dynamic IPs; stateless avoids session affinity config

---

## Summary: thegent MCP Server Configuration

### Complete Middleware & Storage Setup

```python
from fastmcp import FastMCP
from fastmcp.server.middleware.caching import ResponseCachingMiddleware, CallToolSettings
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
from fastmcp.server.event_store import EventStore
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from key_value.aio.stores.redis import RedisStore
import os

# Initialize storage backends
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
cache_store = RedisStore(url=redis_url)
event_store = EventStore(storage=RedisStore(url=redis_url))

# Create server with sampling fallback
mcp = FastMCP(
    name="ThegentServer",
    sampling_handler=OpenAISamplingHandler(api_key=os.environ.get("OPENAI_API_KEY"), default_model="gpt-4o-mini"),
    sampling_handler_behavior="fallback",
)

# Middleware pipeline (outermost first)
mcp.add_middleware(ErrorHandlingMiddleware())
mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=10.0, burst_capacity=20))
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(
    ResponseCachingMiddleware(
        cache_storage=cache_store,
        call_tool_settings=CallToolSettings(
            included_tools=[
                "thegent_ps",
                "thegent_list_agents",
                "thegent_list_droids",
                "thegent_list_models",
            ],
            ttl=30,
        ),
    )
)
mcp.add_middleware(ResponseLimitingMiddleware(max_size=500_000))
mcp.add_middleware(LoggingMiddleware())

# HTTP deployment
app = mcp.http_app(
    path="/mcp",
    transport="streamable-http",
    event_store=event_store,
    retry_interval=2000,
    stateless_http=os.environ.get("DEPLOYMENT_MODE") == "kubernetes",
)
```

### Tool Implementation Checklist

- **User Interaction:** Use `ctx.elicit()` for configuration, approval, choices
- **Logging:** Use `ctx.info()`, `ctx.debug()`, `ctx.error()` for real-time updates
- **Progress:** Use `Progress()` dependency and `ctx.report_progress()` for long operations
- **Tasks:** Use `TaskConfig(mode="optional")` for `thegent_run`; `asyncio.to_thread()` for sync code
- **Sampling:** Use `ctx.sample()` for analysis; `result_type` for structured output
- **Tracing:** Use `get_tracer()` for custom spans; enable opentelemetry-instrument in production
- **Graceful Shutdown:** Use `ctx.close_sse_stream()` every 30 iterations
- **Storage:** Use Redis for production; MemoryStore for dev

---

## 10. Failure Modes & Error Handling

### 10.1 Failure Modes

| Failure Mode                   | Impact                           | Mitigation                                                   |
| ------------------------------ | -------------------------------- | ------------------------------------------------------------ |
| **Elicitation timeout**        | User doesn't respond, tool hangs | Set timeout, fallback to default, return DeclinedElicitation |
| **Context unavailable**        | Tool called without context      | Graceful degradation, log warning, use default behavior      |
| **Storage backend failure**    | EventStore unavailable           | Fallback to MemoryStore, retry with exponential backoff      |
| **Task mode failure**          | Background task crashes          | Error logging, task status update, client notification       |
| **Progress reporting failure** | Progress updates lost            | Non-blocking, continue execution, log error                  |
| **SSE stream closed**          | Client disconnected              | Graceful shutdown, cleanup resources, save state             |

### 10.2 Error Handling Patterns

**Pattern 1: Elicitation with Timeout**

```python
try:
    result = await asyncio.wait_for(ctx.elicit("Confirm?", response_type=bool), timeout=30.0)
except asyncio.TimeoutError:
    await ctx.warning("No response, using default")
    result = False
```

**Pattern 2: Storage Fallback**

```python
try:
    await event_store.append(event)
except StorageError:
    await ctx.warning("Storage unavailable, using memory fallback")
    memory_store.append(event)
```

**Pattern 3: Task Error Recovery**

```python
@mcp.tool(task_config=TaskConfig(mode="optional"))
async def long_task(ctx: Context = CurrentContext()) -> dict:
    try:
        return await execute_long_operation()
    except Exception as e:
        await ctx.error(f"Task failed: {e}")
        await ctx.report_task_status("failed", error=str(e))
        raise
```

### 10.3 Validation

**Pre-flight Checks:**

- Verify context is available before elicitation
- Validate storage backend connectivity
- Check task mode compatibility

**Post-action Verification:**

- Confirm elicitation result is valid
- Verify storage write succeeded
- Validate task completion status

**Performance Targets:**

- Elicitation response: <100ms (p95)
- Tool execution: <50ms (p95)
- Storage write: <10ms (p95)

---

## References

1. **Elicitation & Context:** https://gofastmcp.com/servers/elicitation, https://gofastmcp.com/servers/context
2. **Progress & Tasks:** https://gofastmcp.com/servers/progress, https://gofastmcp.com/servers/tasks
3. **Transforms & Deployment:** https://gofastmcp.com/servers/transforms, https://gofastmcp.com/deployment/http
4. **Storage:** https://gofastmcp.com/servers/storage-backends
5. **Sampling & Telemetry:** https://gofastmcp.com/servers/sampling, https://gofastmcp.com/servers/telemetry
6. **Middleware:** https://gofastmcp.com/servers/middleware

---

## See Also

- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - MCP parity audit
- [MCP_TOOL_OPTIMIZATION_PLAN.md](../plans/MCP_TOOL_OPTIMIZATION_PLAN.md) - MCP tool optimization plan
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (5 BACKLOG items)
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

## EXTENSION_SUMMARY

### 9. Advanced Authentication Patterns

#### 9.1 OAuth 2.1 Provider Integration

FastMCP supports OAuth 2.1 for enterprise authentication with multiple providers. This is critical for multi-tenant deployments.

```python
from fastmcp.server.auth import AuthMiddleware, BearerTokenValidator
from fastmcp.server.auth.providers.github import GitHubProvider
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

# GitHub OAuth for development teams
auth_provider = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    redirect_uri=os.environ["GITHUB_REDIRECT_URI"],
    client_storage=FernetEncryptionWrapper(
        key_value=RedisStore(url=os.environ["REDIS_URL"]), fernet=Fernet(os.environ["STORAGE_ENCRYPTION_KEY"])
    ),
)

# Bearer token validation for service-to-service
token_validator = BearerTokenValidator(
    token_header="Authorization", token_prefix="Bearer", validate_token=lambda token: token in valid_tokens
)

mcp.add_middleware(AuthMiddleware(auth_provider=auth_provider, token_validator=token_validator))
```

**Cross-reference:** See `FASTMCP_SPEC_DEEP_DIVE.md` Section 13 for OAuth adoption checklist. See `hooks/security-pipeline.sh` for security enforcement patterns.

#### 9.2 Multi-Tenant Isolation with Scopes

```python
from fastmcp.server.auth import TenantAwareAuth


def extract_tenant(context):
    """Extract tenant ID from request context."""
    token = context.request.headers.get("X-Tenant-ID")
    return token if token else "default"


mcp.add_middleware(
    TenantAwareAuth(
        tenant_extractor=extract_tenant,
        tenant_scopes={
            "tenant-a": {"tools": ["read"], "resources": ["sessions"]},
            "tenant-b": {"tools": ["read", "write"], "resources": ["all"]},
        },
    )
)
```

**Use cases:**

- SaaS deployments with tenant isolation
- Enterprise multi-team environments
- Compliance with data residency requirements

### 10. Testing Strategies

#### 10.1 Unit Testing Tools

```python
import pytest
from fastmcp import FastMCP
from fastmcp.server.dependencies import Depends


@pytest.fixture
def mcp_server():
    """Create test server with tools."""
    mcp = FastMCP("TestServer")

    @mcp.tool()
    async def test_tool(value: int) -> int:
        return value * 2

    return mcp


@pytest.mark.asyncio
async def test_tool_execution(mcp_server):
    """Test tool returns expected output."""
    result = await mcp_server.tools["test_tool"].run(value=5)
    assert result == 10
```

**Cross-reference:** See `tests/test_unit_mcp_tools.py` for existing tool tests. See `docs/guides/TESTING.md` for testing patterns.

#### 10.2 Integration Testing with MCP Client

```python
import asyncio
from fastmcp import Client


@pytest.mark.asyncio
async def test_elicitation_flow():
    """Test elicitation via MCP client."""
    async with Client(mcp) as client:
        # Mock elicitation response
        result = await client.call_tool("thegent_run", {"agents": ["test-agent"]})
        assert result.content[0].text == "expected output"
```

**Use cases:**

- End-to-end tool testing
- Context behavior verification
- Middleware interaction testing

### 11. Performance Optimization

#### 11.1 Connection Pooling for HTTP Clients

```python
from httpx import AsyncClient, Limits, Timeout

http_client = AsyncClient(
    limits=Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0), timeout=Timeout(10.0)
)

# Use with HTTP transport
app = mcp.http_app(transport="streamable-http", http_client=http_client)
```

**Cross-reference:** See `docs/reference/PERFORMANCE_OPTIMIZATION.md` for runtime optimization patterns.

#### 11.2 Async Tool Batching

```python
from fastmcp.server.tools import ToolBatch


async def batched_agent_execution(agents: list[str], batch_size: int = 5) -> list[dict]:
    """Execute agents in batches to control concurrency."""
    results = []

    for i in range(0, len(agents), batch_size):
        batch = agents[i : i + batch_size]
        batch_results = await asyncio.gather(*[execute_agent(a) for a in batch], return_exceptions=True)
        results.extend(batch_results)

    return results
```

**Configuration:**

| Parameter      | Value | Rationale                          |
| -------------- | ----- | ---------------------------------- |
| batch_size     | 5-10  | Balance throughput and rate limits |
| max_concurrent | 20    | Prevent resource exhaustion        |
| retry_delay    | 1.0   | Exponential backoff base           |

### 12. Cross-Document References

| Reference                                    | Purpose                                    |
| -------------------------------------------- | ------------------------------------------ |
| `FASTMCP_SPEC_DEEP_DIVE.md`                  | Full specification details, SEP compliance |
| `FASTMCP_MIDDLEWARE.md`                      | Middleware pipeline configuration          |
| `FASTMCP_STORAGE_EVENTSTORE.md`              | Storage backend selection                  |
| `FASTMCP_TRANSFORMS_DEPLOYMENT.md`           | Transform patterns and HTTP deployment     |
| `FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md`     | Client compatibility and gaps              |
| `docs/guides/TESTING.md`                     | Testing strategies and patterns            |
| `docs/reference/PERFORMANCE_OPTIMIZATION.md` | Runtime optimization                       |
| `hooks/security-pipeline.sh`                 | Security enforcement hooks                 |

---

**Document Version:** 1.1
**Last Extended:** 2026-02-17
**Extension Author:** Worker Droid
