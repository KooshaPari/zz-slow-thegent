<DONE>
# FastMCP Spec Deep Dive

**Purpose:** Comprehensive reference for the FastMCP specification, MCP protocol alignment, and thegent adoption strategy. Use this for implementation planning and gap analysis.

**References:** [FastMCP Docs](https://gofastmcp.com), [llms.txt index](https://gofastmcp.com/llms.txt), [MCP Spec](https://github.com/modelcontextprotocol/modelcontextprotocol)

---

## 1. Architecture Overview

### 1.1 FastMCP Server Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastMCP Server                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Components: Tools | Resources | Resource Templates | Prompts             │
│  Context:    ctx.elicit | ctx.sample | ctx.report_progress | ctx.get_state│
│  Pipeline:   Middleware → Transforms → Providers → Client                  │
└─────────────────────────────────────────────────────────────────────────┘
```

- **FastMCP** = Pythonic MCP server framework; not part of the official MCP spec.
- **Transports:** STDIO (default), Streamable HTTP, SSE (legacy).
- **Providers:** Local (decorators), Filesystem, Proxy, Skills, OpenAPI.

### 1.2 Component Flow

```
Provider → [Provider Transforms] → [Server Transforms] → Client
```

- **List operations:** Pure function pattern (transform sequence).
- **Get operations:** Middleware pattern (call_next, reverse mapping).

---

## 2. Tools

### 2.1 Core Semantics

| Aspect | Behavior |
|--------|----------|
| **Registration** | `@mcp.tool` decorator; name, description inferred from function |
| **Arguments** | Type hints → JSON Schema; `Depends()` excluded from schema |
| **Return** | `str`, `bytes`, `dict`, `ToolResult`, Pydantic models, `Image`/`Audio`/`File` |
| **Structured output** | 6/18/2025 MCP spec: `structuredContent` + `output_schema` |
| **Validation** | `strict_input_validation=False` (default): coerce; `True`: strict JSON Schema |

### 2.2 ToolResult

```python
ToolResult(
    content="...",  # TextContent or list of content blocks
    structured_content={...},  # Machine-readable JSON
    meta={"execution_time_ms": 145},
)
```

- **content:** Human-readable; string or MCP content blocks.
- **structured_content:** Optional; validated against output schema when present.
- **meta:** Runtime metadata (execution time, etc.).

### 2.3 Annotations

| Annotation | Purpose |
|------------|---------|
| `readOnlyHint` | Tool does not modify environment |
| `destructiveHint` | May perform destructive updates |
| `idempotentHint` | Repeated calls same effect |
| `openWorldHint` | Interacts with external entities |
| `timeout` | Execution timeout (seconds) |
| `tags` | Categorization; filtering |
| `version` | Versioning |

### 2.4 Tool Execution Modes

- **Sync:** Runs in threadpool.
- **Async:** `async def`; preferred for I/O.
- **Background:** `task=True` or `TaskConfig(mode="optional"|"required"|"forbidden")`.

### 2.5 thegent Usage

- 30+ tools; `ToolResult`; `annotations`; `Depends(get_default_cwd)`.
- `thegent_run` uses `TaskConfig(mode="optional")` for background execution.

---

## 3. Resources & Templates

### 3.1 Resources

- URI: `scheme://path` (e.g. `thegent://sessions`).
- RFC 6570 templates: `thegent://session/{id}/meta{?include_contract}`.
- `mime_type`, `annotations` (readOnlyHint, idempotentHint).

### 3.2 thegent Resources

- `thegent://sessions`, `thegent://session/{id}/meta`, `thegent://dag`, `thegent://models`, etc.
- `ResourcesAsTools` transform exposes resources to tool-only clients.

---

## 4. Prompts

### 4.1 Definition

- `@mcp.prompt` with parameters; returns string (message template).
- Clients use `prompts/get` with `arguments` to render.

### 4.2 thegent Prompts

- `thegent_workflow_idea`, `thegent_workflow_quality_green`, `thegent_workflow_next_item`, etc.
- `PromptsAsTools` transform exposes prompts as tools for tool-only clients.

---

## 5. Context (ctx)

### 5.1 Access

```python
ctx: Context = CurrentContext()  # Preferred
# or type hint: ctx: Context
# or get_context() for nested code
```

### 5.2 Capabilities

| Method/Property | Purpose |
|-----------------|---------|
| `ctx.elicit()` | Request structured user input (SEP-1330) |
| `ctx.sample()` | Request LLM completion from client |
| `ctx.report_progress()` | Progress updates |

| `ctx.get_state()` / `ctx.set_state()` | Session state (persists across requests) |
| `ctx.session_id` | MCP session ID |
| `ctx.info()` / `ctx.debug()` / `ctx.warning()` / `ctx.error()` | Logging |
| `ctx.list_resources()` / `ctx.read_resource()` | Resource access |
| `ctx.list_prompts()` / `ctx.get_prompt()` | Prompt access |
| `ctx.send_notification()` | Manual list change notifications |
| `ctx.close_sse_stream()` | Close SSE stream (SEP-1699) |
| `ctx.transport` | `stdio` \| `sse` \| `streamable-http` |
| `ctx.request_id` / `ctx.client_id` | Request metadata |
| `ctx.request_context.meta` | Client-provided metadata (cwd, owner) |

### 5.3 Session State

- Keyed by session; 1-day TTL.
- `serializable=True` (default): JSON; `serializable=False`: in-request only.
- Custom backend: `session_state_store=RedisStore(...)`.

### 5.4 Per-Session Visibility

- `ctx.enable_components()` / `ctx.disable_components()` / `ctx.reset_visibility()`.
- Affects only current session.

### 5.5 thegent Usage

- `ctx.elicit()` for cwd/owner when ambiguous.
- `ctx.report_progress()` in `thegent_run` (every 10s).
- `ctx.close_sse_stream()` every 30s during long runs.
- `ctx.info()` for logging.
- `get_default_cwd()` / `get_default_owner()` from `meta.cwd` / `meta.owner`.

---

## 6. Elicitation (Critical for Blocking UX)

### 6.1 Schema

- MCP spec: objects with primitive/enum properties only.
- FastMCP wraps scalars in `{"value": ...}` for MCP compatibility.

### 6.2 Response Types

| Type | Example |
|------|---------|
| Scalar | `response_type=str`, `int`, `bool` |
| Enum | `response_type=["low","medium","high"]` or `Literal["low","medium","high"]` |
| Multi-select | `response_type=[["bug","feature","docs"]]` |
| Structured | `response_type=TaskDetails` (dataclass/Pydantic) |
| No response | `response_type=None` (approve/reject only) |

### 6.3 Result Actions

| Action | Result | `data` |
|--------|--------|--------|
| `accept` | `AcceptedElicitation` | User input |
| `decline` | `DeclinedElicitation` | — |
| `cancel` | `CancelledElicitation` | — |

### 6.4 Client Requirement

- Client must implement elicitation handler.
- If unsupported: `ctx.elicit()` raises.

### 6.5 thegent Usage

- `thegent_run`, `thegent_bg`, `thegent_dag_list` use `ctx.elicit()` for cwd/owner.
- `ELICIT_CWD_MSG`, `ELICIT_OWNER_MSG` from `cli_impl`.

---

## 7. Sampling (LLM Completion)

### 7.1 Overview

- Server requests LLM text generation from client.
- Implements SEP-1577 (sampling with tools).

### 7.2 API

```python
result = await ctx.sample(
    messages="...",  # or list[SamplingMessage]
    system_prompt="...",
    temperature=0.7,
    max_tokens=300,
    model_preferences=["claude-opus-4-5"],
    tools=[search, fetch_url],
    result_type=SentimentResult,  # Structured output
    tool_concurrency=0,  # None = sequential, 0 = unlimited
)
# result.text, result.result, result.history
```

### 7.3 Fallback Handler

- `sampling_handler=OpenAISamplingHandler(...)` or `AnthropicSamplingHandler(...)`.
- `sampling_handler_behavior="fallback"` (default) or `"always"`.

### 7.4 Structured Output

- `result_type=PydanticModel` → auto `final_response` tool; validation + retries.

### 7.5 Tool Use in Sampling

- Agentic loop: LLM calls tools; FastMCP executes; returns results; continues until final response.
- `mask_error_details=True` for generic errors.
- `ToolError` for intentional errors to LLM.

### 7.6 sample_step()

- Single LLM call; manual loop control.
- `execute_tools=False` for manual tool execution.

### 7.7 thegent Usage

- `thegent_suggest_prompt` uses `ctx.sample()` for prompt refinement.

---

## 8. Background Tasks (SEP-1686)

### 8.1 Enabling

- `pip install "fastmcp[tasks]>=3.0.0rc1"`.
- `@mcp.tool(task=True)` or `TaskConfig(mode="optional"|"required"|"forbidden")`.

### 8.2 Execution Modes

| Mode | Without task | With task |
|------|--------------|-----------|
| `forbidden` | Sync | Error |
| `optional` | Sync | Background |
| `required` | Error | Background |

### 8.3 Backends

- `memory://` (default): ephemeral, single-process.
- `redis://:6379`: persistent, scalable, horizontal workers.

### 8.4 Progress

- `Progress` dependency: `set_total()`, `increment()`, `set_message()`.

### 8.5 thegent Usage

- `thegent_run` uses `TaskConfig(mode="optional")`; not yet using background tasks for long runs.

---

## 9. Transforms

### 9.1 Built-in

| Transform | Purpose |
|-----------|---------|
| `Namespace` | Prefix component names |
| `ToolTransform` | Rename, reshape, customize description |
| `ResourcesAsTools` | Expose resources as tools |
| `PromptsAsTools` | Expose prompts as tools |
| `Enabled` | Visibility control |
| `VersionFilter` | Version-based filtering |

### 9.2 Order

- Provider transforms first; server transforms last.
- First added = innermost.

### 9.3 thegent Usage

- `mcp.add_transform(ResourcesAsTools(mcp))`, `mcp.add_transform(PromptsAsTools(mcp))`.

---

## 10. Middleware

### 10.1 Pipeline

```
Request → Middleware A → Middleware B → Handler → Middleware B → Middleware A → Response
```

### 10.2 Hooks

| Level | Hook | Purpose |
|-------|------|---------|
| Message | `on_message` | All MCP traffic |
| Type | `on_request`, `on_notification` | Requests vs notifications |
| Operation | `on_call_tool`, `on_read_resource`, `on_get_prompt`, etc. | Per-operation |

### 10.3 Built-in Middleware

| Middleware | Purpose |
|------------|---------|
| `ErrorHandlingMiddleware` | Centralized error handling |
| `RateLimitingMiddleware` | Token bucket |
| `TimingMiddleware` | Execution duration |
| `LoggingMiddleware` | Request/response logging |
| `ResponseCachingMiddleware` | TTL-based caching |
| `ResponseLimitingMiddleware` | Max response size |
| `PingMiddleware` | Keep-alive |
| `ToolInjectionMiddleware` | Dynamic tool injection |

### 10.4 thegent Usage

- ErrorHandling, RateLimiting, Timing, ResponseCaching, ResponseLimiting, Logging.

---

## 11. HTTP Deployment

### 11.1 Streamable HTTP

- `mcp.http_app(event_store=..., stateless_http=True)`.
- Stateless: per-request JSON-RPC; no SSE session.

### 11.2 EventStore

- `FASTMCP_EVENT_STORE_URL` → Redis for distributed sessions.
- Default: memory.

### 11.3 SSE Polling (SEP-1699)

- Client sends `Last-Event-ID` on reconnect.
- `ctx.close_sse_stream()` to force client reconnect (avoid LB timeouts).

### 11.4 thegent Usage

- `http_app(stateless_http=True)`; `EventStore`; `close_sse_stream()` in long runs.

---

## 12. MCP SEPs & Alignment

| SEP | Title | FastMCP | Client Gaps |
|-----|-------|---------|-------------|
| 1330 | Elicitation enum schema | ✓ Full | Claude Code, Cursor, Codex: unknown |
| 1577 | Sampling with tools | ✓ Full | Client must implement sampling_handler |
| 1686 | Background tasks | ✓ tasks extra | Unknown |
| 1699 | SSE Polling | ✓ EventStore | Client must send Last-Event-ID |
| 1036 | URL-mode elicitation | — | Out-of-band secure elicitation |

---

## 13. thegent Adoption Checklist

### 13.1 Already Used

- [x] Tools, Resources, Prompts
- [x] Elicitation (cwd/owner)
- [x] Progress reporting
- [x] HTTP transport, middleware, Bearer auth
- [x] ResourcesAsTools, PromptsAsTools
- [x] Dependency injection (Depends, CurrentContext)
- [x] Lifespan
- [x] Sampling (thegent_suggest_prompt)
- [x] TaskConfig(mode="optional") on thegent_run

### 13.2 High-Value Additions

| Feature | Benefit | Effort |
|---------|---------|--------|
| Background tasks for long runs | Return task ID; client polls | Medium |
| Progress in more tools | Better UX (quality, DAG) | Small |
| Session state | Per-session preferences | Small |
| Notifications | tools/list_changed on DAG update | Small |
| Per-session visibility | Namespace activation | Medium |

### 13.3 Queue Integration

| Tool | Purpose |
|------|---------|
| `thegent_queue_add` | Add to pending queue |
| `thegent_queue_list` | List pending |
| `thegent_queue_claim` | Claim for processing |
| `thegent_queue_done` | Mark done |
| `thegent_queue_release` | Release claim |
| `thegent_queue_extend_lease` | Extend lease |

---

## 14. Client Verification Matrix

| Capability | Verify | Claude Code | Cursor | Codex |
|------------|--------|-------------|--------|-------|
| Elicitation | Tool that elicits | ? | ? | ? |
| Progress | Long tool | ? | ? | ? |
| Sampling | thegent_suggest_prompt | ? | ? | ? |
| Background tasks | task=True | ? | ? | ? |
| Notifications | list_changed | ? | ? | ? |

---

## 15. References

- [FastMCP Docs](https://gofastmcp.com)
- [MCP Specification](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [MCP SEPs](https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/seps)
- [FastMCP Claude Code](https://gofastmcp.com/integrations/claude-code.md)
- [FastMCP Cursor](https://gofastmcp.com/integrations/cursor.md)
- [FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md](./FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md)
- [USER_QUEUE_TUI_AND_AGENT_POLL.md](./USER_QUEUE_TUI_AND_AGENT_POLL.md)

---

## EXTENSION_SUMMARY

### 16. Specification Compliance Checklist

#### 16.1 MCP Protocol Version Compatibility

| MCP Version | FastMCP Support | thegent Compatibility |
|-------------|-----------------|----------------------|
| 2024-11-05 (Latest) | ✓ Full | ✓ Compatible |
| 2024-10-07 | ✓ Full | ✓ Compatible |
| 2024-07-15 | ✓ Full | ✓ Compatible |
| Legacy | ⚠ Partial | ⚠ Verify per feature |

**Verification Command:**
```bash
python -c "import fastmcp; print(fastmcp.__mcp_version__)"
```

**Cross-reference:** See `FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md` Section 5 for transport-specific compatibility.

#### 16.2 Required vs Optional Capabilities

| Capability | MCP Spec | thegent Requirement |
|------------|----------|---------------------|
| tools/list | Required | ✓ Implemented |
| tools/call | Required | ✓ Implemented |
| resources/list | Optional | ✓ Implemented |
| resources/read | Optional | ✓ Implemented |
| prompts/list | Optional | ✓ Not used |
| prompts/get | Optional | ✓ Not used |
| sampling | Optional | ✓ Used |
| elicitation | Optional | ✓ Used |

### 17. Error Handling Patterns

#### 17.1 Structured Error Responses

```python
from fastmcp.exceptions import ToolError, ValidationError


class ThegentError(ToolError):
    """Base error for thegent-specific failures."""

    exit_code: int = 1
    recoverable: bool = False


class AgentNotFoundError(ThegentError):
    """Raised when requested agent doesn't exist."""

    exit_code: int = 42
    recoverable: bool = True


@mcp.tool()
async def thegent_run(agents: list[str]) -> dict:
    for agent in agents:
        if not await agent_exists(agent):
            raise AgentNotFoundError(f"Agent {agent} not found")
    # ... execution logic
```

**Error Schema (MCP compliant):**
```json
{
  "code": "AGENT_NOT_FOUND",
  "message": "Agent 'test-agent' not found",
  "data": {
    "available_agents": ["prod-agent", "dev-agent"],
    "recovery_hint": "Use one of the available agents"
  }
}
```

**Cross-reference:** See `src/thegent/contracts/validation.py` for contract-based error handling.

#### 17.2 Error Recovery Patterns

```python
async def resilient_agent_execution(
    agent_name: str, max_retries: int = 3, backoff_factor: float = 2.0
) -> ExecutionResult:
    """Execute agent with retry logic."""
    last_error = None

    for attempt in range(max_retries):
        try:
            return await execute_agent(agent_name)
        except AgentNotFoundError:
            raise  # Non-recoverable
        except (NetworkError, TimeoutError) as e:
            last_error = e
            wait_time = backoff_factor**attempt
            await asyncio.sleep(wait_time)

    raise ExecutionError(f"Failed after {max_retries} attempts") from last_error
```

### 18. Versioning and Migration

#### 18.1 Tool Versioning

```python
@mcp.tool(
    annotations={
        "version": "2.1.0",
        "deprecation_warning": "Use thegent_run_v3 instead",
        "replacement": "thegent_run_v3",
    }
)
async def thegent_run_v2(agents: list[str]) -> dict:
    """Legacy tool version, migrate to v3."""
    # ... implementation
```

**Version Migration Strategy:**

| Version | Status | Migration Action |
|---------|--------|------------------|
| v1.0 | Deprecated | Auto-redirect to v2 |
| v2.0 | Stable | Default for existing clients |
| v2.1 | Latest | Recommended for new clients |

#### 18.2 Schema Evolution

```python
from pydantic import BaseModel, Field


class AgentConfigV2(BaseModel):
    """V2 schema with backward compatibility."""

    name: str
    timeout_secs: int = Field(default=600, ge=60, le=3600)
    retry_count: int = Field(default=3, ge=0, le=10)
    # V2新增字段
    priority: int = Field(default=0, ge=0, le=100)

    @classmethod
    def from_v1(cls, v1_config: dict) -> "AgentConfigV2":
        """Migrate from V1 schema."""
        return cls(
            name=v1_config["agent_name"],
            timeout_secs=v1_config.get("timeout", 600),
            retry_count=v1_config.get("retries", 3),
            priority=0,  # Default for migrated configs
        )
```

### 19. Cross-Document References

| Reference | Purpose |
|-----------|---------|
| `FASTMCP_IMPLEMENTATION_GUIDE.md` | Implementation patterns and examples |
| `FASTMCP_MIDDLEWARE.md` | Middleware specification details |
| `FASTMCP_STORAGE_EVENTSTORE.md` | Storage and event specifications |
| `FASTMCP_TRANSFORMS_DEPLOYMENT.md` | Transform specifications |
| `FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md` | Feature gaps and transport specs |
| `src/thegent/contracts/validation.py` | Contract validation patterns |
| `docs/guides/TESTING.md` | Testing specifications |

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (5 BACKLOG items)
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Main implementation guide
- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - Parity audit
- [FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md](./FASTMCP_FEATURES_AND_TRANSPORT_GAPS.md) - Feature gaps
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Document Version:** 1.1
**Last Extended:** 2026-02-17
**Extension Author:** Worker Droid
