<DONE>
# FastMCP ASGI Uni-Mount System Plan

**Purpose:** Consolidate multiple MCP servers into a single FastMCP monolith using ASGI mounting and Uvicorn integration.

**Status:** Audit complete; implementation plan actionable.

**Last updated:** 2026-02-17

---

## 1. Executive Summary

FastMCP provides native support for mounting ASGI-compatible servers, enabling true uni-mount (single process) instead of multi-process process-compose.

| Approach            | Process Count              | Use Case                       |
| ------------------- | -------------------------- | ------------------------------ |
| **process-compose** | N+1 (parent + MCP servers) | Legacy, backward compatibility |
| **FastMCP mount**   | 1 (single monolith)        | Recommended for production     |
| **HTTP proxy**      | 2+ (thegent + MCP servers) | Remote/multi-tenant            |

### Key Findings

1. **FastMCP `mount()` supports ASGI apps directly** - Any Starlette/FastAPI/FastMCP app can be mounted
2. **Uvicorn runs the monolith** - Single uvicorn process hosts all mounted servers
3. **Namespace isolation** - Mounted tools are prefixed (e.g., `browser_*`, `serena_*`)
4. **Session affinity optional** - `stateless_http=True` for horizontal scaling

---

## 2. Current State Analysis

### 2.1 Existing Mount Infrastructure

```python
# mcp_server.py - lifespan startup
from fastmcp.server import create_proxy

# HTTP-based mounts (flyto, serena URL)
proxy = create_proxy(flyto_url, name="flyto")
mcp_app.mount(proxy, namespace="browser")

# Subprocess-based mounts (playwright, octocode, etc.)
config = {"mcpServers": {"default": {"command": "uvx", "args": ["package"]}}}
proxy = create_proxy(config, name="octocode")
mcp_app.mount(proxy, namespace="octocode")
```

### 2.2 ASGI/HTTP Support

```python
# mcp_server.py
def http_app(stateless_http: bool = True):
    """Return ASGI app with EventStore."""
    app = mcp.http_app(
        event_store=_get_event_store(),
        retry_interval=2000,
        transport="http",
        stateless_http=stateless_http,
    )
    if hasattr(app, "add_middleware"):
        app.add_middleware(BearerAuthMiddleware)
    return app


def run(host=None, port=None, reload=False):
    """Start with uvicorn."""
    import uvicorn

    app = http_app(stateless_http=True)
    uvicorn.run(app, host=host, port=port, lifespan="on")
```

---

## 3. Uni-Mount Architecture

### 3.1 Single Monolith (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                     uvicorn (1 process)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐  │
│  │              FastMCP Server (thegent)                 │  │
│  │  - thegent tools (run, bg, ps, etc.)                │  │
│  │  - Bearer auth middleware                            │  │
│  │  - EventStore for SSE resumption                    │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │  MOUNTED ASGI APPS (namespace isolation)            │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │    playwright-mcp (ASGI app)                  │  │  │
│  │  │    → tools: browser_*                         │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │    serena-mcp (ASGI app)                     │  │  │
│  │  │    → tools: serena_*                          │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │    octocode-mcp (ASGI app)                   │  │  │
│  │  │    → tools: octocode_*                        │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 ASGI-Compatible Server Patterns

#### Pattern A: FastMCP → FastMCP (Direct Mount)

```python
# For servers using FastMCP
from fastmcp import FastMCP

# Server code
other_mcp = FastMCP("OtherServer")


@other_mcp.tool()
def other_tool(x: int) -> int:
    return x * 2


# Mount in thegent
from fastmcp.server.asgi import mount_asgi

mounted = mount_asgi(other_mcp, namespace="other")
mcp_app.mount(mounted, namespace="other")
```

#### Pattern B: Starlette/FastAPI → Mount

```python
# For ASGI apps using Starlette
from starlette.applications import Starlette
from starlette.routing import Route
from fastmcp.server.asgi import mount_asgi


async def homepage(request):
    return PlainTextResponse("Hello")


app = Starlette(routes=[Route("/", homepage)])

# Mount in thegent
mounted = mount_asgi(app, namespace="web")
mcp_app.mount(mounted, namespace="web")
```

#### Pattern C: HTTP Proxy (Non-ASGI Servers)

```python
# For non-ASGI MCP servers (stdio-based)
from fastmcp.server import create_proxy

config = {
    "mcpServers": {
        "legacy": {
            "command": "python",
            "args": ["-m", "legacy_mcp_server"],
        }
    }
}
proxy = create_proxy(config, name="legacy")
mcp_app.mount(proxy, namespace="legacy")
```

---

## 4. Implementation Plan

### 4.1 Phase 1: ASGI Mount Support (Core)

| Task                                                   | Effort | Deps          |
| ------------------------------------------------------ | ------ | ------------- |
| Add `mount_asgi()` helper for FastMCP→FastMCP mounting | Small  | —             |
| Add `mount_starlette()` helper for ASGI apps           | Small  | —             |
| Update lifespan to support ASGI mounting               | Medium | mount helpers |
| Document ASGI mounting patterns                        | Small  | —             |

### 4.2 Phase 2: Uvicorn Configuration

| Task                                     | Effort | Notes                       |
| ---------------------------------------- | ------ | --------------------------- |
| Configure uvicorn workers for production | Small  | `workers=CPU_COUNT`         |
| Add graceful shutdown handling           | Small  | `timeout_graceful_shutdown` |
| Configure log level and format           | Small  | —                           |
| Add health check endpoint                | Small  | —                           |

### 4.3 Phase 3: Server Consolidation

| Task                             | Effort | Notes                                |
| -------------------------------- | ------ | ------------------------------------ |
| Migrate playwright to ASGI mount | Medium | Requires playwright-mcp ASGI support |
| Migrate serena to ASGI mount     | Medium | Serena has HTTP transport            |
| Migrate octocode to ASGI mount   | Medium | octocode-mcp ASGI support            |
| Add namespace conflict detection | Small  | —                                    |

---

## 5. Configuration

### 5.1 Environment Variables

```bash
# Enable ASGI mounting
THGENT_ASGI_MOUNT=1

# Mount specific servers (space-separated)
THGENT_MOUNTS="browser:playwright serena:serena octocode:octocode"

# Uvicorn config
THGENT_UVICORN_WORKERS=4
THGENT_UVICORN_TIMEOUT=30
THGENT_UVICORN_LOG_LEVEL=info
```

### 5.2 Settings Schema

```python
# config.py
class ThegentSettings:
    asgi_mount: bool = Field(
        False,
        description="Enable ASGI mounting for uni-mount (single process)",
    )
    mounts: dict[str, str] = Field(
        default_factory=dict,
        description="Namespace → server mapping for ASGI mounts",
    )
    uvicorn_workers: int = Field(
        0,  # 0 = CPU count
        description="Number of uvicorn workers (0 = auto)",
    )
    uvicorn_timeout: int = Field(
        30,
        description="Graceful shutdown timeout (seconds)",
    )
```

---

## 6. Benefits

### 6.1 Process Reduction

| Before (process-compose) | After (ASGI mount)   |
| ------------------------ | -------------------- |
| process-compose (1)      | uvicorn (1)          |
| thegent MCP (1)          | thegent + mounts (1) |
| playwright MCP (1)       | —                    |
| serena MCP (1)           | —                    |
| octocode MCP (1)         | —                    |
| **Total: 5**             | **Total: 1**         |

### 6.2 Performance Benefits

1. **Zero IPC overhead** - All tools in same process
2. **Shared event loop** - Async operations share thread pool
3. **Memory efficiency** - No duplicate Python interpreters
4. **Faster startup** - Single process initialization

### 6.3 Operational Benefits

1. **Simpler debugging** - Single process to trace
2. **Unified logging** - All logs from one source
3. **Single port** - One HTTP endpoint for all tools
4. **Atomic updates** - Deploy all tools together

---

## 7. Limitations & Mitigations

| Limitation                      | Impact | Mitigation                              |
| ------------------------------- | ------ | --------------------------------------- |
| Server crashes affect all tools | High   | Process supervision for critical mounts |
| Memory pressure scales          | Medium | Per-mount resource limits               |
| No isolation between mounts     | Medium | Namespaces prevent tool collision       |
| ASGI required for direct mount  | Medium | Use HTTP proxy for non-ASGI servers     |

---

## 8. Migration Path

### 8.1 Current State (process-compose)

```yaml
# process-compose.yaml
processes:
  thegent:
    command: thegent serve
  playwright:
    command: npx @playwright/mcp
  serena:
    command: serena start-mcp-server
  octocode:
    command: npx octocode-mcp
```

### 8.2 Target State (ASGI mount)

```bash
# Single command
thegent serve --asgi-mount

# Or with specific mounts
thegent serve --asgi-mount --mounts "browser:playwright serena:serena octocode:octocode"
```

### 8.3 Rollback

```bash
# Fallback to process-compose
thegent mcp up
```

---

## 9. Verification Checklist

- [ ] ASGI mounting works for FastMCP servers
- [ ] ASGI mounting works for Starlette/FastAPI apps
- [ ] HTTP proxy mounting works for stdio-based servers
- [ ] Namespace isolation prevents tool conflicts
- [ ] Single uvicorn process hosts all mounts
- [ ] EventStore works with mounted servers
- [ ] Bearer auth applies to mounted tools
- [ ] Graceful shutdown works correctly
- [ ] Process count reduced to 1 (from N+1)
- [ ] Performance benchmarks show improvement

---

## 10. References

| Source                  | URL                                                    | Key Content                    |
| ----------------------- | ------------------------------------------------------ | ------------------------------ |
| FastMCP ASGI Mount      | [asgi.md](https://gofastmcp.com/servers/asgi.md)       | mount_asgi, mount_starlette    |
| FastMCP HTTP Deployment | [http.md](https://gofastmcp.com/deployment/http.md)    | uvicorn, stateless, EventStore |
| FastMCP Proxies         | [proxies.md](https://gofastmcp.com/servers/proxies.md) | create_proxy, config patterns  |
| Starlette ASGI          | [starlette.io](https://www.starlette.io/applications/) | ASGI app patterns              |
| Uvicorn                 | [uvicorn.org](https://www.uvicorn.org/)                | Server configuration           |

---

## 11. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added §3:** Uni-mount architecture diagrams and patterns
2. **Added §4:** Implementation plan with phases
3. **Added §5:** Configuration schema (env vars, settings)
4. **Added §6:** Benefits analysis (process reduction, performance)
5. **Added §7:** Limitations and mitigations
6. **Added §8:** Migration path from process-compose
7. **Added §9:** Verification checklist

### Key Insights

1. **FastMCP's `mount()` can directly host ASGI apps** - No proxy needed for compatible servers
2. **Uvicorn runs everything in single process** - Dramatic simplification
3. **Namespace isolation is automatic** - Mounted tools are prefixed
4. **Process count reduces from N+1 to 1** - Major resource savings

### Cross-References Added

- docs/research/MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md
- src/thegent/mcp_server.py (lifespan, http_app, run)
- docs/research/FASTMCP_IMPLEMENTATION_GUIDE.md

---

## See Also

- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - Full FastMCP feature audit
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Implementation patterns
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
