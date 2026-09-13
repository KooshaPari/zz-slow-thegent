# patterns API Reference

> **Source**: `src/thegent/mcp/tools/patterns.py`

Reusable FastMCP tool patterns using elicitation and Context API.

Provides higher-order decorator patterns for tool authors:

- confirm_before_action: ask user to confirm before executing the wrapped tool
- progress_with_fallback: report progress via ctx.report_progress; fallback on error
- choice_with_retry: present choices via elicit_choice; retry on invalid/None selection
- retry_on_error: retry tool on specified exceptions using tenacity exponential backoff
- ToolAborted: exception raised when user aborts a tool action

Usage example::

    from thegent.mcp_tool_patterns import confirm_before_action, ToolAborted

    @confirm_before_action("Delete session {session_id}?")
    async def thegent_delete_session(session_id: str, ctx=None):
        ...  # only runs if user confirms

# @trace FR-MCP-PATTERNS-001

---

## ToolAborted

Raised when a user aborts a tool action via elicitation.

Tool authors should catch this at the boundary and return an appropriate
ToolResult payload rather than letting it propagate as a tool error.

**Inherits from**: `Exception`

---

## choice_with_retry

```python
choice_with_retry(options: list[str], prompt: str, max_retries: int)
```

Decorator: present choices via elicit_choice and retry on None/invalid selection.

Before calling the wrapped function, this decorator asks the user to
select from `options`. The chosen value is injected into kwargs as
`user_choice`. If the user declines or the response is not in `options`,
up to `max_retries` additional prompts are shown. After exhausting retries,
ToolAborted is raised.

**Parameters**:

- `options`: Non-empty list of string options to present.
- `prompt`: The prompt text shown to the user.
- `max_retries`: Maximum number of re-prompts before aborting. Default 3.

**Returns**: Decorator that wraps an async tool function with interactive choice flow.

**Raises**:

- `ToolAborted`: If user fails to make a valid selection after max_retries.
- `ValueError`: If options list is empty (detected at decoration time).

---

## confirm_before_action

```python
confirm_before_action(action_description: str)
```

Decorator: ask the user to confirm before executing the wrapped tool.

The action_description is a format string that may reference any keyword
arguments of the wrapped function (e.g. "Delete session {session_id}?").
If the user confirms, the wrapped function runs normally. If the user
declines or cancels, ToolAborted is raised instead of calling the function.

The decorator expects the wrapped function to accept a `ctx` keyword
argument (FastMCP Context). If ctx is None or elicitation is unavailable,
the wrapped function runs without confirmation (fail-open behaviour keeps
non-interactive clients working).

**Parameters**:

- `action_description`: Format string describing the action. May reference
  keyword arguments of the wrapped function by name.

**Returns**: Decorator that wraps an async tool function with confirmation flow.

**Raises**:

- `ToolAborted`: If user declines or cancels the confirmation.

---

## decorator

```python
decorator(fn: Callable) -> Callable
```

---

## progress_with_fallback

```python
progress_with_fallback(total_steps: int, fallback_result: Any)
```

Decorator: report progress via ctx.report_progress at each step.

Wraps an async tool function and injects a `report_step` async callable
into the function's kwargs. Tool authors call `await report_step(step, label)`
to emit progress. If ctx or report_progress is unavailable, progress calls
are silently swallowed.

On unexpected exception, returns fallback_result (wrapped in a dict) instead
of raising, so clients receive a degraded but non-error response.

**Parameters**:

- `total_steps`: Denominator for progress fraction (used in report_progress).
- `fallback_result`: Value returned (as `{"result": fallback_result,
"fallback": true}`) when the function raises an unexpected exception.

**Returns**: Decorator that wraps an async tool function with progress reporting.

---

## register_tool_pattern_tools

```python
register_tool_pattern_tools(mcp: Any)
```

Register example tools demonstrating the FastMCP tool patterns.

Registers:

- thegent_delete_session: uses @confirm_before_action
- thegent_bulk_operation: uses @progress_with_fallback

**Parameters**:

- `mcp`: The FastMCP application instance.

---

## retry_on_error

```python
retry_on_error(max_attempts: int, exceptions: tuple[(type[BaseException], Ellipsis)])
```

Decorator: retry tool on specified exceptions with exponential backoff.

Uses tenacity's wait_random_exponential for jitter-aware retries. Only
exceptions in `exceptions` tuple trigger a retry; others propagate
immediately. After `max_attempts` total attempts, the last exception
is re-raised.

**Parameters**:

- `max_attempts`: Total number of attempts (1 = no retry). Default 3.
- `exceptions`: Tuple of exception types that trigger a retry. Default (Exception,).

**Returns**: Decorator that wraps an async tool function with tenacity retry logic.

---
