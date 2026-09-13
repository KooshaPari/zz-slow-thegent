<DONE>
# FastMCP Elicitation & Context API Summary

> **Source:** FastMCP Python implementation (aligns with [gofastmcp.com/servers/elicitation](https://gofastmcp.com/servers/elicitation) and [gofastmcp.com/servers/context](https://gofastmcp.com/servers/context)). Extracted from `fastmcp.server.context`, `fastmcp.server.elicitation`, `fastmcp.server.dependencies`, and `mcp.server.elicitation`.

---

## (a) `ctx.elicit` Signature and Response Types

### Signature (overloads)

```python
async def elicit(
    self,
    message: str,
    response_type: type[T] | list[str] | dict[str, dict[str, str]] | list[list[str]] | list[dict[str, dict[str, str]]] | None = None,
) -> (
    AcceptedElicitation[T]
    | AcceptedElicitation[dict[str, Any]]
    | AcceptedElicitation[str]
    | AcceptedElicitation[list[str]]
    | DeclinedElicitation
    | CancelledElicitation
)
```

### Overloads by `response_type`

| `response_type`                                              | Return type                                        |
| ------------------------------------------------------------ | -------------------------------------------------- |
| `None`                                                       | `AcceptedElicitation[dict[str, Any]]` (empty dict) |
| `type[T]` (e.g. `str`, `int`, `MyModel`)                     | `AcceptedElicitation[T]`                           |
| `list[str]` (single-select options)                          | `AcceptedElicitation[str]`                         |
| `dict[str, dict[str, str]]` (key → title mapping)            | `AcceptedElicitation[str]` (selected key)          |
| `list[list[str]]` (multi-select)                             | `AcceptedElicitation[list[str]]`                   |
| `list[dict[str, dict[str, str]]]` (multi-select with titles) | `AcceptedElicitation[list[str]]`                   |

### Behavior

- Sends an elicitation request to the MCP client and awaits the response.
- Works in both **request** and **background task** contexts (SEP-1686).
- For primitives, generates an object schema with a single `"value"` field; response is unwrapped to the primitive.
- For `response_type=None`, schema is an empty object; client must send `{}` to accept.

---

## (b) `AcceptedElicitation` / `DeclinedElicitation` / `CancelledElicitation`

### FastMCP (high-level)

```python
# fastmcp.server.elicitation
class AcceptedElicitation(BaseModel, Generic[T]):
    """Result when user accepts the elicitation."""

    action: Literal["accept"] = "accept"
    data: T
```

### MCP base (low-level)

```python
# mcp.server.elicitation
class AcceptedElicitation(BaseModel, Generic[ElicitSchemaModelT]):
    action: Literal["accept"] = "accept"
    data: ElicitSchemaModelT


class DeclinedElicitation(BaseModel):
    """Result when user declines the elicitation."""

    action: Literal["decline"] = "decline"


class CancelledElicitation(BaseModel):
    """Result when user cancels the elicitation."""

    action: Literal["cancel"] = "cancel"
```

### Usage

```python
result = await ctx.elicit("Working directory?", response_type=str)
if isinstance(result, AcceptedElicitation):
    cwd = result.data
elif isinstance(result, DeclinedElicitation):
    # user declined
    ...
elif isinstance(result, CancelledElicitation):
    # user cancelled
    ...
```

---

## (c) `ctx.info` / `ctx.debug` / `ctx.error`

All delegate to `ctx.log()` and send messages to the connected MCP client.

### Signatures

```python
async def debug(
    self,
    message: str,
    logger_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None

async def info(
    self,
    message: str,
    logger_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None

async def warning(
    self,
    message: str,
    logger_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None

async def error(
    self,
    message: str,
    logger_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None
```

### Base `log` method

```python
async def log(
    self,
    message: str,
    level: LoggingLevel | None = None,  # "debug" | "info" | "notice" | "warning" | "error" | "critical" | "alert" | "emergency"
    logger_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None
```

---

## (d) `CurrentContext()`

### Signature

```python
def CurrentContext() -> Context
```

### Purpose

Dependency that resolves to the active FastMCP `Context` for the current MCP operation (tool, resource, or prompt call).

### Resolution

- **Foreground (request) mode:** Returns the active context from `_current_context`.
- **Background (Docket worker) mode:** Builds a task-aware `Context` with `task_id` and restores access token from Redis.

### Usage

```python
from fastmcp.dependencies import CurrentContext


@mcp.tool()
async def my_tool(ctx: Context = CurrentContext()) -> str:
    await ctx.info("Processing...")
    result = await ctx.elicit("Need input?", response_type=str)
    return result.data if isinstance(result, AcceptedElicitation) else "declined"
```

### Raises

`RuntimeError` if no active context (e.g. outside a request handler or before session registration in a background task).

---

## Quick Reference

| API                                  | Purpose                                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `ctx.elicit(message, response_type)` | Request user input; returns `AcceptedElicitation[T]` \| `DeclinedElicitation` \| `CancelledElicitation` |
| `ctx.info(msg)`                      | Send INFO log to client                                                                                 |
| `ctx.debug(msg)`                     | Send DEBUG log to client                                                                                |
| `ctx.error(msg)`                     | Send ERROR log to client                                                                                |
| `ctx.warning(msg)`                   | Send WARNING log to client                                                                              |
| `CurrentContext()`                   | Dependency for injecting `Context` into tools/resources/prompts                                         |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added elicitation patterns
2. Added context management examples
3. Enhanced cross-references

### Cross-References Added

- FASTMCP_MIDDLEWARE.md
- FASTMCP_TRANSFORMS_DEPLOYMENT.md

### Practical Additions

- Elicitation templates
- Context handling examples

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Main implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification deep dive
- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - Parity audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
