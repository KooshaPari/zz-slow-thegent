<DONE>
# Conversation Dump 2026-02-20 — WL-011 OpenRouter P1 Integration (OR-08 to OR-16)

## Issues Addressed

WL-011: Full OpenRouter feature integration — P1 tasks OR-08 through OR-16 (9 tasks).
P0 blockers (WL-001 through WL-005) were already complete.

---

## Fixes Applied

### OR-08: HTTP-Referer and X-Title Headers

**File:** `src/thegent/cliproxy_adapter.py` lines 27-41, 486-495, 624

Added `_OPENROUTER_REFERER = "https://thegent.dev"`, `_OPENROUTER_TITLE = "thegent"` constants,
`_is_openrouter_backend(url)` helper, and `_inject_openrouter_headers(headers, backend_url)` function.

Called in both `_proxy_request()` (before outbound request) and `_proxy_stream()` (before streaming begins).
Only injects when `"openrouter.ai"` is found in backend URL. Uses `setdefault` so caller-provided
headers are not overwritten.

### OR-09: Forward `transforms` and `provider` fields in Responses API transform

**Files:**

- `src/thegent/cliproxy_adapter.py` lines 81-144 (`_responses_to_chat_completions`)
- `src/thegent/routing/litellm_responses_handler.py` lines 115-174 (`_responses_to_chat_completions`)

Both transform functions now pass through OpenRouter-specific fields: `transforms`, `provider`,
`route`, `plugins`, `reasoning`, `session_id`, `metadata`, `trace`, `models`, `structured_outputs`.

Also extended to forward all standard optional sampling parameters (`top_p`, `top_k`,
`frequency_penalty`, `presence_penalty`, `repetition_penalty`, `min_p`, `top_a`, `seed`,
`stop`, `logprobs`, `top_logprobs`, `logit_bias`, `user`, `response_format`, `tools`,
`tool_choice`, `parallel_tool_calls`, `stream_options`) — only when non-None.

### OR-10: Fix tool call streaming in transform mode

**File:** `src/thegent/routing/litellm_responses_handler.py` lines 184-208 (`_chat_completions_to_responses`)

The `_chat_completions_to_responses` function previously only extracted `delta.content` and returned
`None` on empty content, silently dropping `delta.tool_calls`. Fixed by detecting `tool_calls` in
the delta and emitting a `response.output_item.added` event with `type: "function_call"` carrying
the tool_calls array.

Note: `cliproxy_adapter.py` already had full tool call streaming support (GW-07, `_extract_delta_tool_calls`,
`tool_call_delta_events`, `tool_call_closing_events`). OR-10 fills the gap in the LiteLLM handler path.

### OR-11: Fix OpenRouter error format

**Files:**

- `src/thegent/routing/litellm_responses_handler.py` lines 15-35, 47-79

Extended `_ERROR_STATUS_MAP` with entries for `"insufficient credits"` (402), `"payment required"` (402),
`"no providers"` (503), `"service unavailable"` (503).

Updated `_error_response()` to include `code` (integer HTTP status) in the error body. Also propagates
`metadata` from upstream OpenRouter error objects when available on the exception's `.response.text`.

Updated streaming error payload in `handle_responses_stream` to include `code` field.
Updated WebSocket error send to include `code` field and use `contextlib.suppress` (fixed pre-existing SIM105).

### OR-12: Propagate actual model name from SSE chunks

**Files:**

- `src/thegent/cliproxy_adapter.py` line 673 (already present as GW-09, now labeled OR-12)
- `src/thegent/routing/litellm_responses_handler.py` lines 290-319 (`handle_responses_stream`)
- `src/thegent/routing/litellm_responses_handler.py` lines 248-251 (non-streaming path)

In `handle_responses_stream`: added `actual_model` tracking — reads `chunk.get("model")` from each
SSE chunk; updates `actual_model` when it differs from requested model; emits `actual_model` in the
`response.completed` event.

In `handle_responses_request` (non-streaming): uses `getattr(response, "model", model)` to capture
the actual model from the LiteLLM response object.

### OR-13: Handle OpenRouter-specific HTTP error codes

**File:** `src/thegent/cliproxy_adapter.py` lines 530-553 (classes), 627-746 (`_proxy_stream`)

Added:

- `_NO_RETRY_STATUS_CODES: frozenset = {401, 402, 403, 400}` — hard-stop codes
- `_RETRY_MAX_ATTEMPTS: dict = {408: 1, 502: 3, 503: 3}` — max retry attempts per code
- `InsufficientCreditsError(RuntimeError)` — raised on 402, must not be retried
- `_RetryableStreamError(Exception)` — internal signal for 408/502/503 retry

`_proxy_stream` refactored into `_do_stream(attempt)` (inner async generator for one attempt) and
`stream()` (outer retry loop). On 402: raises `InsufficientCreditsError`, caught in `stream()`,
immediately yields error SSE and returns. On 408/502/503: raises `_RetryableStreamError`, caught in
`stream()`, increments attempt, sleeps `2^attempt` seconds (exponential backoff: 2s, 4s, 8s),
retries up to max attempts.

### OR-14: Include `usage.cost` in `response.completed`

**Files:**

- `src/thegent/cliproxy_adapter.py` lines 354-393 (`_ResponsesStreamState.closing_events`)
- `src/thegent/routing/litellm_responses_handler.py` lines 263-274 (non-streaming path)

In `closing_events()`: builds `usage_block` dict with `input_tokens`, `output_tokens`, `total_tokens`,
plus `cost` when `usage.get("total_cost")` is non-None. Also wires the cost into `get_cost_tracker()`
via `tracker.track(provider="openrouter", model=self.model, ...)`. Cost tracking is best-effort
(wrapped in try/except that only emits debug log on failure — response path never breaks).

In non-streaming `handle_responses_request`: extracts `usage.total_cost` from LiteLLM response object
and includes it as `usage.cost` in the Responses API output when present.

### OR-15: Fix `/v1/models` to include OpenRouter proxy models

**File:** `src/thegent/cliproxy_adapter.py` lines 763-814, 922

Added `_OPENROUTER_PROXY_MODELS` list — 5 canonical OpenRouter model stubs:
`anthropic/claude-opus-4-6`, `anthropic/claude-sonnet-4-6`, `anthropic/claude-haiku-4-5-20251001`,
`openai/gpt-4o`, `google/gemini-2.0-flash-001`.

Added `_inject_openrouter_proxy_models(models)` — merges stubs into model list, skipping any
already present by ID.

Updated `_transform_models_response` signature to accept `inject_openrouter: bool = False`.
Updated `proxy_handler` call site to pass `inject_openrouter=_is_openrouter_backend(backend)`.

### OR-16: Preserve content arrays in Responses transform

**File:** `src/thegent/routing/litellm_responses_handler.py` lines 83-105 (`_responses_input_to_messages`)

The previous implementation in `litellm_responses_handler.py` collapsed content arrays to plain
strings (losing `cache_control`, `image_url`, and other per-block annotations). Fixed by mirroring
`cliproxy_adapter.py`'s approach: iterate content items, preserve dict items as-is, wrap bare strings
as `{"type": "text", "text": str}`.

Note: `cliproxy_adapter.py` already had this correct (GW-04). OR-16 fills the gap in the
LiteLLM handler path.

---

## Additional Cleanup

- Removed dead function `_extract_finish_reason` from `cliproxy_adapter.py` (pyright
  `reportUnusedFunction` — pre-existing, never called anywhere).
- Fixed pre-existing `SIM105` in `litellm_responses_handler.py` WebSocket handler: converted
  `try/except pass` pattern to `contextlib.suppress(Exception)`.

---

## Quality Gates

```
python -m ruff check src/thegent/routing/ src/thegent/cliproxy_adapter.py --fix
# All checks passed!

pyright src/thegent/cliproxy_adapter.py
# 0 errors, 0 warnings, 0 informations
```

---

## Open Questions

1. OR-13 retry logic is in the proxy SSE path only. The `_proxy_request` (non-streaming) path
   does not implement retry for 408/502/503. Should it? Currently 408/502/503 in non-streaming
   mode propagate directly to the caller unchanged.

2. OR-14 cost tracking uses `provider="openrouter"` hardcoded. If the proxy routes to another
   provider via OpenRouter's fallback, the actual provider is in the SSE `"provider"` field but
   is not currently extracted.

3. OR-15 `_OPENROUTER_PROXY_MODELS` list is static. A dynamic fetch from
   `https://openrouter.ai/api/v1/models` at startup would keep it current but adds an external
   dependency at boot time.

---

## Next Steps

- Test with actual OpenRouter API key to confirm OR-13 retry behavior on real 408/502/503 responses.
- Consider OR-15 dynamic model injection via periodic background fetch of OpenRouter model list.
- OR-14 cost value should be verified against OpenRouter `/api/v1/generation?id=<id>` endpoint
  for reconciliation.
