<DONE>
# FastMCP Progress & Tasks API Summary

Extracted from FastMCP 3.0 source (gofastmcp.com/servers/progress, gofastmcp.com/servers/tasks) and `fastmcp` package in thegent venv.

---

## (a) `ctx.report_progress` Signature

```python
async def report_progress(
    self, progress: float, total: float | None = None, message: str | None = None
) -> None:
```

**Usage:**

```python
await ctx.report_progress(i, 100, f"Step {i}/100")
```

**Behavior:** Foreground = MCP progress notification; Background = Docket Redis update.

---

## (b) Progress Dependency API

```python
from fastmcp.dependencies import Progress
```

**Protocol (ProgressLike):** `current`, `total`, `message` (props); `set_total()`, `increment()`, `set_message()` (async).

**Usage:**

```python
@mcp.tool()
async def my_tool(progress: ProgressLike = Progress()) -> str:
    await progress.set_total(100)
    await progress.increment()
    await progress.set_message("Working...")
```

---

## (c) TaskConfig Modes

```python
TaskMode = Literal["forbidden", "optional", "required"]
TaskConfig(mode="optional", poll_interval=timedelta(seconds=5))
```

| Mode      | Behavior                             |
| --------- | ------------------------------------ |
| forbidden | No task support; -32601 if requested |
| optional  | Sync or task; client chooses         |
| required  | Must use task; -32601 if not         |

---

## (d) asyncio.to_thread Pattern for Sync run_impl

FastMCP uses `call_sync_fn_in_threadpool` (anyio.to_thread.run_sync). Stdlib equivalent:

```python
@mcp.tool(task=TaskConfig(mode="optional"))
async def thegent_run(...) -> dict:
    return await asyncio.to_thread(run_impl, ...)
```

---

## References

- https://gofastmcp.com/servers/progress
- https://gofastmcp.com/servers/tasks

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added progress tracking patterns
2. Added task implementation examples
3. Enhanced cross-references

### Cross-References Added

- FASTMCP_IMPLEMENTATION_GUIDE.md
- FASTMCP_SPEC_DEEP_DIVE.md

### Practical Additions

- Progress callback templates
- Task configuration examples

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
