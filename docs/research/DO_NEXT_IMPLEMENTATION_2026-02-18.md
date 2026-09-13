<DONE>
# do_next_impl and wait_next_impl Implementation (2026-02-18)

## Problem

`thegent plan wait-next` was returning a "mocked" `example-task` instead of real work items from `WORK_STREAM.md`, despite the file containing claimed tasks.

**Root Cause**: The functions `do_next_impl` and `wait_next_impl` were imported in `src/thegent/cli.py` and `src/thegent/mcp_server.py`, but their definitions were missing from `src/thegent/cli_impl.py`.

## Solution

Implemented both functions in `src/thegent/cli_impl.py`:

### `do_next_impl(cd: Path | None = None, limit: int = 5) -> dict[str, Any]`

**Functionality:**

- Parses `docs/reference/WORK_STREAM.md`
- Reads BACKLOG section (table format)
- Filters out items in CLAIMED section
- Checks dependencies (Depends column) - only returns items whose dependencies are in COMPLETED
- Sorts by priority (P1 < P2 < P3)
- Returns top N items (limit parameter)

**Returns:**

```python
{
    "next_items": [
        {
            "id": "task-id",
            "description": "Task description",
            "source": "Source document",
            "priority": "P1",
            "prompt_suggestion": "Complete task-id: Task description",
        }
    ],
    "count": 3,
    "sources_checked": ["WORK_STREAM.md"],
    "empty_reason": None,  # or reason string if no items
}
```

**Fallback Behavior:**

- If `WORK_STREAM.md` doesn't exist, falls back to `tasks/example-task.md` (for backward compatibility)
- If neither exists, returns error

### `wait_next_impl(cd: Path | None = None, poll_interval: float = 2.0, timeout: float = 0.0, sources: tuple[str, ...] = ("do_next",)) -> dict[str, Any]`

**Functionality:**

- Continuously calls `do_next_impl` at specified `poll_interval`
- Blocks until a work item is found or `timeout` is reached
- Returns first available work item

**Returns:**

```python
{
    "action": {
        "id": "task-id",
        "description": "Task description",
        "source": "Source document",
        "prompt_suggestion": "Complete task-id: Task description",
    },
    "elapsed_s": 2.5,
    "poll_count": 2,
    "timeout": False,
}
```

**Timeout Behavior:**

- If `timeout > 0` and elapsed time >= timeout, returns `{"action": None, "timeout": True}`
- If `timeout = 0` (default), waits indefinitely

### Helper Functions

**`_parse_work_stream_md(work_stream_path: Path) -> dict[str, Any]`**

- Parses WORK_STREAM.md markdown file
- Extracts BACKLOG, CLAIMED, and COMPLETED sections
- Returns structured data

**`_check_dependencies_satisfied(item: dict[str, Any], completed: set[str], claimed: set[str]) -> bool`**

- Checks if all dependencies for an item are satisfied
- Dependencies must be in COMPLETED (not just CLAIMED)

**`_priority_sort_key(priority: str) -> int`**

- Converts priority string (P1, P2, P3) to sortable integer
- Lower number = higher priority

### Wrapper Functions

**`work_stream_claim_impl(item_id: str, agent_id: str, cd: Path | None = None) -> dict[str, Any]`**

- Wrapper around `WorkStreamManager.claim()`
- Moves item from BACKLOG to CLAIMED

**`work_stream_complete_impl(item_id: str, agent_id: str, cd: Path | None = None) -> dict[str, Any]`**

- Wrapper around `WorkStreamManager.complete()`
- Moves item from CLAIMED to COMPLETED

**`incorporate_impl(cd: Path | None = None) -> dict[str, Any]`**

- Placeholder for merging fragments from 02-UNIFIED-WBS into WORK_STREAM.md
- Returns stub response (full implementation pending)

## Testing

**Test Command:**

```bash
uv run python -c "import json; from thegent.cli_impl import do_next_impl; result = do_next_impl(limit=3); print(json.dumps(result, indent=2))"
```

**Result:**
✅ Successfully returns real work items from WORK_STREAM.md:

- Parses BACKLOG section correctly
- Filters out CLAIMED items
- Checks dependencies
- Sorts by priority
- Generates prompt_suggestion

## Integration Points

**CLI Commands:**

- `thegent plan do-next` → calls `do_next_impl()`
- `thegent plan wait-next` → calls `wait_next_impl()`
- `thegent plan get-next` → calls `do_next_impl(limit=1)`
- `thegent plan loop` → calls `do_next_impl()` in loop

**MCP Tools:**

- `thegent_do_next` → calls `do_next_impl()`
- `thegent_plan_wait_next` → calls `wait_next_impl()`

## Files Modified

1. **`src/thegent/cli_impl.py`**
   - Added `do_next_impl()` function
   - Added `wait_next_impl()` function
   - Added helper functions: `_parse_work_stream_md()`, `_check_dependencies_satisfied()`, `_priority_sort_key()`
   - Added wrapper functions: `work_stream_claim_impl()`, `work_stream_complete_impl()`, `incorporate_impl()`

## Verification

✅ `thegent plan wait-next` now returns real work items instead of `example-task`
✅ `thegent plan do-next` returns multiple items from WORK_STREAM.md
✅ Dependencies are checked correctly
✅ Priority sorting works (P1 items appear first)
✅ Fallback to example-task works if WORK_STREAM.md doesn't exist

## Next Steps

1. ✅ Implement `do_next_impl` and `wait_next_impl` - **DONE**
2. ⏳ Implement full `incorporate_impl()` to merge from 02-UNIFIED-WBS.md
3. ⏳ Add support for other sources (PLAN_STATUS, FR_TRACKER, escalation queue) as mentioned in docstrings
4. ⏳ Add caching for WORK_STREAM.md parsing (performance optimization)

---

_Implementation Date: 2026-02-18_
_Status: ✅ Complete and tested_
