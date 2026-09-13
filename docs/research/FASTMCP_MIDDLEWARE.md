<DONE>
# FastMCP Middleware

**Source:** gofastmcp.com/servers/middleware
**Date:** 2026-02-14
**Purpose:** Extract add_middleware order, ResponseCachingMiddleware, RateLimitingMiddleware, on_call_tool hook for thegent_run.

---

## 1. add_middleware Order

Middleware executes in **order added**. First added = outermost (runs first in, last out).

```python
mcp.add_middleware(ErrorHandlingMiddleware())  # 1st in, last out
mcp.add_middleware(RateLimitingMiddleware())  # 2nd in, 2nd out
mcp.add_middleware(TimingMiddleware())  # 3rd in, first out
mcp.add_middleware(LoggingMiddleware())  # 4th in, first out
```

**Recommended order:** ErrorHandling → RateLimiting → Timing → Logging (first added = outermost).

---

## 2. ResponseCachingMiddleware

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
        call_tool_settings=CallToolSettings(included_tools=["expensive_tool"]),
        read_resource_settings=ReadResourceSettings(enabled=False),
    )
)
```

### Settings Classes

| Settings Class | Configures |
|----------------|------------|
| ListToolsSettings | on_list_tools caching |
| CallToolSettings | on_call_tool caching |
| ListResourcesSettings | on_list_resources caching |
| ReadResourceSettings | on_read_resource caching |
| ListPromptsSettings | on_list_prompts caching |
| GetPromptSettings | on_get_prompt caching |

### Per-settings options

- `included_*` / `excluded_*` — Whitelist or blacklist
- `ttl` — Time-to-live in seconds
- `enabled` — Enable/disable caching for this operation

### thegent mapping

- `ListToolsSettings(ttl=30)` — cache tools/list
- `CallToolSettings(included_tools=["thegent_ps", "thegent_list_agents", "thegent_list_droids", "thegent_list_models"])` — cache read-heavy tools
- `ReadResourceSettings` — cache thegent://sessions, thegent://session/{id}/meta

### Storage for persistence

```python
from key_value.aio.stores.disk import DiskStore

mcp.add_middleware(ResponseCachingMiddleware(cache_storage=DiskStore(directory="cache")))
```

---

## 3. RateLimitingMiddleware

```python
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware

mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=10.0, burst_capacity=20))
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| max_requests_per_second | float | 10.0 | Sustained request rate |
| burst_capacity | int | 20 | Maximum burst size |
| client_id_func | Callable | None | Custom client identification |

**thegent:** `max_requests_per_second=10`, `burst_capacity=20` to protect thegent_run from abuse.

---

## 4. on_call_tool Hook

```python
async def on_call_tool(self, context: MiddlewareContext, call_next):
    tool_name = context.message.name
    args = context.message.arguments
    result = await call_next(context)
    return result
```

### MiddlewareContext

| Attribute | Type | Description |
|-----------|------|-------------|
| method | str | MCP method (e.g. "tools/call") |
| message.name | str | Tool name |
| message.arguments | dict | Tool arguments |
| fastmcp_context | Context | FastMCP context (if available) |

### thegent_run hook

Use `on_call_tool` to:
- Log `thegent_run` invocations
- Rate-limit or throttle thegent_run specifically
- Enrich ToolResult with metadata

---

## 5. ResponseLimitingMiddleware

```python
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware

mcp.add_middleware(ResponseLimitingMiddleware(max_size=500_000))
```

For `thegent_logs` — limit response size to avoid context overflow.

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_size | 1_000_000 | Max response size in bytes |
| tools | None | Limit only these tools (None = all) |

---

## 6. Built-in Middleware Summary

| Middleware | Purpose |
|------------|---------|
| ErrorHandlingMiddleware | Centralized error logging |
| RateLimitingMiddleware | Token bucket rate limit |
| TimingMiddleware | Execution duration |
| LoggingMiddleware | Request/response logging |
| StructuredLoggingMiddleware | JSON logs |
| ResponseCachingMiddleware | Cache tool/resource/prompt calls |
| ResponseLimitingMiddleware | Truncate large responses |
| PingMiddleware | Keep connections alive |

---

## 7. thegent Production Pipeline

```python
mcp.add_middleware(ErrorHandlingMiddleware())
mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=10, burst_capacity=20))
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(
    ResponseCachingMiddleware(
        call_tool_settings=CallToolSettings(
            included_tools=["thegent_ps", "thegent_list_agents", "thegent_list_droids", "thegent_list_models"], ttl=30
        )
    )
)
mcp.add_middleware(ResponseLimitingMiddleware(max_size=500_000))
mcp.add_middleware(LoggingMiddleware())
```

---

## EXTENSION_SUMMARY

### 8. Middleware Composition Patterns

#### 8.1 Conditional Middleware Application

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext
from functools import wraps


def conditional_middleware(condition: callable):
    """Apply middleware only when condition is met."""

    def decorator(middleware_class):
        class ConditionalMiddleware(middleware_class):
            async def on_call_tool(self, context: MiddlewareContext, call_next):
                if condition(context):
                    return await super().on_call_tool(context, call_next)
                return await call_next(context)

        return ConditionalMiddleware

    return decorator


# Usage: Apply rate limiting only in production
@conditional_middleware(lambda ctx: os.environ.get("ENV") == "production")
class ProductionRateLimiting(RateLimitingMiddleware):
    max_requests_per_second = 5.0
```

**Cross-reference:** See `FASTMCP_IMPLEMENTATION_GUIDE.md` Section 7 for middleware order patterns.

#### 8.2 Middleware Chaining with Priority

```python
from enum import IntEnum, auto


class MiddlewarePriority(IntEnum):
    SECURITY = auto()  # First: Auth, rate limiting
    RELIABILITY = auto()  # Second: Retries, circuit breaker
    PERFORMANCE = auto()  # Third: Caching, compression
    OBSERVABILITY = auto()  # Last: Logging, metrics


def add_with_priority(mcp, middleware, priority: MiddlewarePriority):
    """Add middleware with explicit priority ordering."""
    mcp.add_middleware(middleware)
    # Priority handled by middleware registry
```

### 9. Custom Middleware Examples

#### 9.1 Circuit Breaker Middleware

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext


class CircuitBreakerMiddleware(Middleware):
    """Prevent cascade failures with circuit breaker pattern."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = {}
        self.circuit_open = {}

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name

        if self._is_circuit_open(tool_name):
            raise ServiceUnavailableError(f"Circuit open for {tool_name}")

        try:
            result = await call_next(context)
            self._record_success(tool_name)
            return result
        except Exception as e:
            self._record_failure(tool_name)
            raise

    def _is_circuit_open(self, tool_name: str) -> bool:
        return self.circuit_open.get(tool_name, False)

    def _record_success(self, tool_name: str):
        self.failure_count[tool_name] = 0

    def _record_failure(self, tool_name: str):
        self.failure_count[tool_name] = self.failure_count.get(tool_name, 0) + 1
        if self.failure_count[tool_name] >= self.failure_threshold:
            self.circuit_open[tool_name] = True
            # Schedule recovery
            asyncio.create_task(self._open_circuit(tool_name))

    async def _open_circuit(self, tool_name: str):
        await asyncio.sleep(self.recovery_timeout)
        self.circuit_open[tool_name] = False
        self.failure_count[tool_name] = 0
```

**Use cases:**
- External API protection
- Database connection failure handling
- Rate limit recovery

#### 9.2 Metrics Collection Middleware

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext
import time


class MetricsMiddleware(Middleware):
    """Collect execution metrics for observability."""

    def __init__(self, metrics_handler: callable):
        self.metrics = {}
        self.metrics_handler = metrics_handler

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        start_time = time.perf_counter()

        try:
            result = await call_next(context)
            duration = time.perf_counter() - start_time
            self._record_metrics(tool_name, duration, success=True)
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            self._record_metrics(tool_name, duration, success=False)
            raise

    def _record_metrics(self, tool_name: str, duration: float, success: bool):
        key = f"tool:{tool_name}"
        if key not in self.metrics:
            self.metrics[key] = {"calls": 0, "failures": 0, "total_duration": 0.0}
        self.metrics[key]["calls"] += 1
        self.metrics[key]["total_duration"] += duration
        if not success:
            self.metrics[key]["failures"] += 1
        # Send to metrics handler
        self.metrics_handler(self.metrics[key])
```

**Cross-reference:** See `src/thegent/observability/otel_instrumentation.py` for OpenTelemetry integration.

### 10. Cross-Document References

| Reference | Purpose |
|-----------|---------|
| `FASTMCP_IMPLEMENTATION_GUIDE.md` | Full middleware pipeline examples |
| `FASTMCP_SPEC_DEEP_DIVE.md` | Middleware specification compliance |
| `FASTMCP_STORAGE_EVENTSTORE.md` | Storage middleware patterns |
| `src/thegent/observability/otel_instrumentation.py` | Telemetry middleware |
| `hooks/quality-gate.sh` | Quality enforcement middleware |

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Main implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification deep dive
- [FASTMCP_STORAGE_EVENTSTORE.md](./FASTMCP_STORAGE_EVENTSTORE.md) - Storage patterns
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Document Version:** 1.1
**Last Extended:** 2026-02-17
**Extension Author:** Worker Droid
