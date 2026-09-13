<DONE>
# FastMCP Features & MCP Transport Spec Gaps

**Purpose:** Deep research on FastMCP capabilities and MCP transport spec implementation gaps in clients (Codex, Cursor, Claude Code). Informs thegent MCP server design and potential client patches.

**Context:** Another agent is implementing the queue pending/blocking plan (`docs/research/CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md`). This doc supports that work by ensuring we maximize MCP features and identify client-side gaps.

---

## 1. FastMCP Feature Matrix

### 1.1 Server-Side Features

| Feature                  | FastMCP Support      | MCP Spec / SEP  | thegent Usage                                 |
| ------------------------ | -------------------- | --------------- | --------------------------------------------- |
| **Tools**                | ✓ Full               | Core            | 30+ tools (thegent_run, thegent_bg, etc.)     |
| **Resources**            | ✓ Full               | Core            | thegent://sessions, thegent://dag, etc.       |
| **Resource Templates**   | ✓ Full               | Core            | thegent://session/{id}/meta                   |
| **Prompts**              | ✓ Full               | Core            | Not yet used                                  |
| **Elicitation**          | ✓ Full               | SEP-1330        | ctx.elicit() for cwd/owner disambiguation     |
| **Background Tasks**     | ✓ Full (tasks extra) | SEP-1686        | Not yet used                                  |
| **Progress**             | ✓ Full               | Core            | ctx.report_progress()                         |
| **Sampling**             | ✓ Full               | Core + SEP-1577 | Server can request LLM completion from client |
| **Logging**              | ✓ Full               | Core            | ctx.log()                                     |
| **Notifications**        | ✓ Full               | Core            | tools/list_changed, resources/list_changed    |
| **HTTP Transport**       | ✓ Streamable HTTP    | Core            | thegent serve                                 |
| **SSE Polling**          | ✓ SEP-1699           | SEP-1699        | EventStore + close_sse_stream()               |
| **OAuth**                | ✓ Full               | OAuth 2.1       | Auth0, GitHub, Google, etc.                   |
| **Bearer Auth**          | ✓ Full               | —               | G-FM-01                                       |
| **Middleware**           | ✓ Full               | —               | Caching, rate limit, timing, error handling   |
| **Tag Filtering**        | ✓ Full               | —               | include_tags, exclude_tags                    |
| **Pagination**           | ✓ Full               | —               | list operations                               |
| **Custom Routes**        | ✓ Full               | —               | /health                                       |
| **Lifespans**            | ✓ Full               | —               | Startup/shutdown                              |
| **Dependency Injection** | ✓ Full               | —               | Depends(), CurrentContext                     |

### 1.2 Client-Side Features (FastMCP Client)

| Feature           | Handler Required    | Use Case                         |
| ----------------- | ------------------- | -------------------------------- |
| **Elicitation**   | elicitation_handler | User input during tool execution |
| **Sampling**      | sampling_handler    | Server requests LLM completion   |
| **Progress**      | progress_handler    | Long-running operation updates   |
| **Logging**       | log_handler         | Server log messages              |
| **Notifications** | message_handler     | tools/list_changed, etc.         |
| **Tasks**         | Built-in            | Start/poll background tasks      |

---

## 2. MCP Transport Spec & SEPs

### 2.1 Core Transports

| Transport           | Spec   | FastMCP            | Client Support                     |
| ------------------- | ------ | ------------------ | ---------------------------------- |
| **STDIO**           | Core   | ✓ Default          | Claude Code, Cursor, Codex (local) |
| **Streamable HTTP** | Core   | ✓ Default for HTTP | Claude Code, Cursor (remote)       |
| **SSE**             | Legacy | ✓ Deprecated       | Some clients                       |

### 2.2 Key SEPs (Specification Enhancement Proposals)

| SEP      | Title                           | FastMCP       | Client Gaps                                  |
| -------- | ------------------------------- | ------------- | -------------------------------------------- |
| **1686** | Background Tasks                | ✓ tasks extra | **Codex/Cursor/Claude Code: unknown**        |
| **1699** | SSE Polling (server disconnect) | ✓ EventStore  | Client must send Last-Event-ID               |
| **1330** | Elicitation enum schema         | ✓ Full        | **Claude Code: may not support elicitation** |
| **1577** | Sampling with tools             | ✓ Full        | Client must implement sampling_handler       |
| **1036** | URL-mode elicitation            | —             | Out-of-band secure elicitation               |

### 2.3 Elicitation (Critical for Blocking UX)

Elicitation lets a tool **pause** and request structured user input. This is the protocol-native way to implement "blocking" behavior:

```
Tool runs → ctx.elicit("Approve deploy?", response_type=["yes","no"]) → Client shows UI → User responds → Tool continues
```

**Client requirements:**

- Client must implement elicitation handler
- If client doesn't support: `ctx.elicit()` raises error

**Known client support:**

- **Claude Code:** Unclear. May not forward elicitation to user.
- **Cursor:** Unclear.
- **Codex:** Unclear. User said "codex is OSS" — if so, we can patch.

---

## 3. Client Implementation Gaps (Research Needed)

### 3.1 Verification Checklist

For each client (Codex, Cursor, Claude Code), verify:

| Capability           | How to Verify                                                      | Patch Strategy                             |
| -------------------- | ------------------------------------------------------------------ | ------------------------------------------ |
| **Elicitation**      | Call tool that uses ctx.elicit(); check if user sees prompt        | Add elicitation handler; show modal/inline |
| **Progress**         | Call long-running tool; check for progress updates                 | Add progress_handler; show progress bar    |
| **Sampling**         | Call tool that uses ctx.sample(); check if LLM is invoked          | Add sampling_handler; route to model       |
| **Background Tasks** | Call tool with task=True; check task ID + poll                     | Implement tasks/list, tasks/get            |
| **Notifications**    | Register tools; change server tool list; check if client refreshes | Add message_handler for list_changed       |
| **Streamable HTTP**  | Connect via HTTP; check session handling                           | Ensure mcp-session-id, cookies             |

### 3.2 Codex / Cursor-Agent

**Note:** "Codex" may refer to:

- Anthropic Codex (if OSS — repo not found at github.com/anthropics/codex)
- Cursor's agent (cursor-agent)
- Another MCP client

**If Codex is OSS:** Locate repo, audit MCP client implementation, identify gaps (elicitation, tasks, progress), create patch/fork.

### 3.3 Claude Code

- Uses STDIO or HTTP for MCP
- Hooks: UserPromptSubmit, Stop, SessionStart, etc.
- **Elicitation:** Claude Code connects to MCP via its internal client. If that client doesn't implement elicitation, tools that call `ctx.elicit()` will fail. Need to test.
- **Workaround:** Queue pending/blocking plan uses hooks, not MCP elicitation. So we don't depend on client elicitation for that flow.

---

## 4. FastMCP Features to Adopt in thegent

### 4.1 Already Used

- Tools, Resources, Elicitation (cwd/owner)
- HTTP transport, middleware, Bearer auth
- fastmcp[tasks] dependency

### 4.2 High-Value Additions

| Feature              | Benefit                                                    | Effort |
| -------------------- | ---------------------------------------------------------- | ------ |
| **Prompts**          | Reusable slash commands (e.g. /thegent_next_thing)         | Small  |
| **Background Tasks** | Long runs (quality gate, DAG) return task ID; client polls | Medium |
| **Progress**         | ctx.report_progress() in long tools (dag run, quality)     | Small  |
| **Sampling**         | Server requests LLM for routing/classification             | Medium |
| **Notifications**    | tools/list_changed when DAG updates                        | Small  |

### 4.3 Queue/Blocking Integration

The queue pending/blocking plan uses **hooks**, not MCP. But we can add MCP tools to support it:

| Tool                    | Purpose                                                       |
| ----------------------- | ------------------------------------------------------------- |
| `thegent_queue_add`     | Add prompt to pending queue (alternative to $defer in prompt) |
| `thegent_queue_list`    | List pending prompts                                          |
| `thegent_queue_resolve` | Resolve blocked item (alternative to CLI)                     |
| `thegent_escalate_add`  | Add to escalation queue ($block)                              |

These tools give the agent a programmatic way to queue/resolve without relying on prompt flags.

---

## 5. Transport Spec Gaps: Patch Priorities

If Codex (or target client) is OSS and lacks:

| Gap               | Priority | Patch Scope                                          |
| ----------------- | -------- | ---------------------------------------------------- |
| **Elicitation**   | P0       | Add elicitation handler; show UI for server requests |
| **Progress**      | P1       | Add progress_handler; display progress               |
| **Tasks**         | P2       | Implement tasks/list, tasks/get, task execution      |
| **Notifications** | P3       | Handle list_changed; refresh tool cache              |
| **Sampling**      | P2       | Add sampling_handler; route to configured LLM        |

---

## 6. Action Items

1. **Locate Codex OSS repo** — Confirm repo URL; audit MCP client.
2. **Test elicitation** — Run thegent tool that elicits (e.g. thegent_run with ambiguous cwd) in Claude Code, Cursor, Codex; document behavior.
3. **Add queue MCP tools** — thegent_queue_add, thegent_queue_list, thegent_queue_resolve for the pending/blocking flow.
4. **Add progress to long tools** — thegent_dag_run, quality-related tools.
5. **Evaluate background tasks** — For DAG run, quality-a-r; return task ID for async execution.

---

## 7. References

- **[FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md)** — Full FastMCP spec deep dive (tools, context, elicitation, sampling, tasks, transforms, middleware)
- [FastMCP Docs](https://gofastmcp.com)
- [MCP Specification](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [MCP SEPs](https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/seps)
- [FastMCP Claude Code Integration](https://gofastmcp.com/integrations/claude-code.md)
- [FastMCP Elicitation](https://gofastmcp.com/servers/elicitation.md)
- [FastMCP Background Tasks](https://gofastmcp.com/servers/tasks.md)
- [Queue Pending/Blocking Plan](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md)

---

## EXTENSION_SUMMARY

### 8. Gap Mitigation Strategies

#### 8.1 Elicitation Fallback Patterns

When clients don't support elicitation, implement fallback via alternative mechanisms:

```python
from enum import Enum


class ElicitationFallbackStrategy(Enum):
    """Strategies for clients without elicitation support."""

    ERROR = "error"  # Raise error
    DEFAULT = "default"  # Use default values
    QUEUE = "queue"  # Queue for later processing
    PROMPT = "prompt"  # Use CLI prompt


async def elicit_with_fallback(
    ctx: Context,
    message: str,
    response_type: type,
    fallback_strategy: ElicitationFallbackStrategy = ElicitationFallbackStrategy.DEFAULT,
) -> any:
    """Elicit with fallback for unsupported clients."""
    try:
        return await ctx.elicit(message, response_type)
    except NotImplementedError:
        # Client doesn't support elicitation
        if fallback_strategy == ElicitationFallbackStrategy.ERROR:
            raise ClientElicitationError("Elicitation not supported")
        elif fallback_strategy == ElicitationFallbackStrategy.DEFAULT:
            return get_default_for_type(response_type)
        elif fallback_strategy == ElicitationFallbackStrategy.QUEUE:
            await ctx.info("Queuing for later processing")
            return QueuedRequest(message=message, response_type=response_type)
        elif fallback_strategy == ElicitationFallbackStrategy.PROMPT:
            return await cli_prompt(message, response_type)
```

**Cross-reference:** See `FASTMCP_IMPLEMENTATION_GUIDE.md` Section 1 for elicitation patterns.

#### 8.2 Progress Reporting Without Client Support

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator


class FallbackProgressReporter:
    """Progress reporter that works without client support."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self._total = 0
        self._current = 0

    async def report(self, current: int, total: int, message: str = ""):
        """Report progress; falls back to logging if client doesn't support."""
        try:
            await self.ctx.report_progress(current, total, message)
        except NotImplementedError:
            # Client doesn't support progress, log instead
            percent = (current / total * 100) if total else 0
            await self.ctx.info(f"Progress: {percent:.1f}% - {message}")


@asynccontextmanager
async def track_progress(
    ctx: Context, total: int, message: str = "Processing"
) -> AsyncIterator[FallbackProgressReporter]:
    """Track progress with automatic cleanup."""
    reporter = FallbackProgressReporter(ctx)
    await reporter.report(0, total, f"{message} starting")
    try:
        yield reporter
    finally:
        await reporter.report(total, total, f"{message} complete")
```

### 9. Feature Adoption Roadmap

#### 9.1 Priority Matrix

| Feature            | Client Support        | Priority | Implementation Effort | Risk   |
| ------------------ | --------------------- | -------- | --------------------- | ------ |
| Elicitation        | Claude Code (partial) | P0       | Medium                | Low    |
| Progress Reporting | All clients           | P0       | Low                   | Low    |
| Background Tasks   | Unknown               | P1       | High                  | Medium |
| Sampling           | Claude Code           | P1       | Medium                | Low    |
| Notifications      | Unknown               | P2       | Medium                | Medium |
| OAuth              | All clients           | P2       | High                  | Low    |

#### 9.2 Implementation Timeline

| Phase   | Timeline | Features                                |
| ------- | -------- | --------------------------------------- |
| Phase 1 | Week 1-2 | Progress reporting, fallback patterns   |
| Phase 2 | Week 3-4 | Elicitation fallback, queue integration |
| Phase 3 | Week 5-6 | Background tasks evaluation             |
| Phase 4 | Week 7-8 | Notifications, comprehensive testing    |

### 10. Cross-Document References

| Reference                               | Purpose                      |
| --------------------------------------- | ---------------------------- |
| `FASTMCP_IMPLEMENTATION_GUIDE.md`       | Full implementation patterns |
| `FASTMCP_SPEC_DEEP_DIVE.md`             | Specification compliance     |
| `FASTMCP_MIDDLEWARE.md`                 | Client-agnostic middleware   |
| `FASTMCP_TRANSFORMS_DEPLOYMENT.md`      | Deployment considerations    |
| `CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md` | Queue/pending integration    |
| `docs/guides/TESTING.md`                | Client compatibility testing |

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Main implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification deep dive
- [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) - Queue/pending integration
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Document Version:** 1.1
**Last Extended:** 2026-02-17
**Extension Author:** Worker Droid
