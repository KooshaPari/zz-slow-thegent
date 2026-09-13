<DONE>
# OpenRouter Proxy Audit — 2026-02-20

Audit of `src/thegent/cliproxy_adapter.py` and supporting routing files for full OpenRouter
compatibility. Produced by deep code inspection of the proxy stack and cross-referencing
OpenRouter API documentation.

---

## Current State Assessment

### Architecture Overview

The proxy stack consists of:

1. **`cliproxy_adapter.py`** — A Starlette ASGI app that sits between harness clients (Codex,
   Claude Code) and the CLIProxyAPIPlus backend. Handles path rewriting, `/v1/responses`
   translation, WebSocket bridging, and `/v1/models` enrichment.

2. **`agents/cliproxy_manager.py`** — Lifecycle management for CLIProxyAPIPlus. Injects API keys
   into the CLIProxy YAML config and manages process startup. Contains the provider definitions
   lookup path `_FACTORY_PROVIDER_PATTERNS` that includes an `"openrouter"` entry.

3. **`routing/harness_model_mapping.py`** — Maps Codex/alias model IDs to backend model IDs. Only
   contains MiniMax/GLM/Kilo/Roo aliases; no OpenRouter-specific mappings.

4. **`routing/model_metadata.py`** — Static metadata registry. Contains no OpenRouter models
   (e.g., `openrouter/anthropic/claude-sonnet-4-20250514`, `google/gemini-2.0-flash-001`).

5. **`routing/litellm_router.py`** — LiteLLM Router wrapper. The `_get_api_key_env()` function has
   no entry for `"openrouter"`, so the key lookup falls through to
   `f"{provider.upper()}_API_KEY"` → `OPENROUTER_API_KEY`, which is correct by coincidence.

6. **`agents/cliproxy_data/provider_definitions.json`** — Defines OpenRouter with:
   - `base_url`: `https://openrouter.ai/api/v1`
   - `base_url_env`: `THGENT_OPENROUTER_BASE_URL`
   - `model`: `google/gemini-2.0-flash-001`
   - Login URL and instructions for `OPENROUTER_API_KEY`

### What the Proxy Currently Handles

- Transparent proxying of all `GET`, `POST`, `OPTIONS` on `/v1/*` to the CLIProxyAPIPlus backend.
- `/v1/responses` → `/v1/chat/completions` translation (Codex Responses API compatibility).
- WebSocket `/v1/responses` → HTTP SSE bridge.
- `/v1/models` response enrichment: converts OpenAI `{"data": [...]}` to Codex
  `{"models": [...]}` format with full metadata schema.
- Header passthrough: all incoming headers except `host` and `content-length` are forwarded as-is.

### How Authentication Headers Are Currently Passed Through

In `_proxy_request()` (line 294–296):
```python
headers = dict(request.headers)
headers.pop("host", None)
headers.pop("content-length", None)
```
The `Authorization: Bearer sk-or-...` header from the incoming request is forwarded verbatim. No
headers are added by the proxy layer. There is no code anywhere in `cliproxy_adapter.py` that
injects `HTTP-Referer` or `X-Title`.

In `_proxy_stream()` (line 381):
```python
async with httpx.AsyncClient(timeout=120.0) as client:
    async with client.stream("POST", url, content=body, headers=headers) as resp:
```
Same pattern: headers forwarded as-is.

In `websocket_responses_handler()` (line 661):
```python
headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
```
WebSocket-originating requests strip ALL incoming headers and only send `Content-Type` and
`Accept`. The `Authorization` header from the WebSocket client is NOT forwarded to the backend.

### How the /v1/models Endpoint Currently Works

1. The adapter forwards `GET /v1/models` to CLIProxyAPIPlus backend.
2. `_transform_models_response()` converts the response from OpenAI format
   (`{"data": [...], "object": "list"}`) to Codex format (`{"models": [...]}`).
3. Each model object is enriched with Codex-required metadata fields (`slug`, `shell_type`,
   `context_window`, `supported_reasoning_levels`, etc.).
4. Model metadata is looked up via `get_model_metadata(mid)` which checks the static
   `MODEL_METADATA` dict in `routing/model_metadata.py`.
5. For `provider/model-name` format IDs, the code strips the provider prefix and retries:
   ```python
   if not meta and "/" in mid:
       meta = get_model_metadata(mid.split("/", 1)[1])
   ```
6. An `x-models-etag` header (SHA256 of sorted model IDs) is returned.

### How Model IDs Are Transformed/Translated

- `_map_model_for_backend()` calls `resolve_model_for_backend()` in `harness_model_mapping.py`.
- The mapping table `CODEX_TO_BACKEND_MODEL` only contains MiniMax, GLM, Kilo, and Roo aliases.
- OpenRouter model IDs (`google/gemini-2.0-flash-001`, `anthropic/claude-sonnet-4-20250514`,
  `openai/gpt-4o`, etc.) pass through without transformation — the function returns the input
  unchanged if not in the table.
- In `clode_main.py`, OpenRouter is configured with a single default model:
  `anthropic/claude-sonnet-4-20250514` as `ANTHROPIC_MODEL` env var. The actual OpenRouter model
  ID format (`provider/model-name`) is correctly represented here.
- `MODEL_METADATA` in `model_metadata.py` has zero OpenRouter model entries.

---

## Issues Found

### Issue 1 — Missing `HTTP-Referer` and `X-Title` Headers

**Severity**: P1 (missing feature — OpenRouter attributes usage to apps via these headers)

**Description**: OpenRouter uses `HTTP-Referer` (your app URL) and `X-Title` (your app name) to
attribute API usage and display it in the OpenRouter dashboard. Without them, requests still work
but appear as unattributed traffic. Some OpenRouter rate-limiting and analytics features may
degrade. OpenRouter documentation explicitly states these are "recommended" for apps sending
requests.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_proxy_request()` lines 294–296,
`_proxy_stream()` lines 359–380

**Fix**: Inject attribution headers into all outbound requests to OpenRouter backends. The proxy
needs to detect when the backend URL points to `openrouter.ai` and add:
```python
if "openrouter.ai" in backend_url:
    headers["HTTP-Referer"] = "https://thegent.dev"
    headers["X-Title"] = "thegent"
```
This must be applied in both `_proxy_request()` and `_proxy_stream()`.

---

### Issue 2 — WebSocket Handler Drops Authorization Header

**Severity**: P0 (blocks basic function for WebSocket path to OpenRouter)

**Description**: In `websocket_responses_handler()` (line 661), when forwarding the translated
chat completions request to the backend, the headers dict is constructed from scratch:
```python
headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
```
The `Authorization: Bearer sk-or-...` header from the WebSocket client connection is completely
dropped. For OpenRouter, which requires `Authorization: Bearer <key>`, this means every
WebSocket-originated request will fail with 401 Unauthorized.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `websocket_responses_handler()` line 661

**Fix**: Extract and forward the authorization header from the WebSocket headers:
```python
ws_auth = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
if ws_auth:
    headers["Authorization"] = ws_auth
```

---

### Issue 3 — No OpenRouter Model Entries in `MODEL_METADATA`

**Severity**: P1 (models will have unknown context windows; Codex "Model metadata not found")

**Description**: `routing/model_metadata.py` has no entries for any OpenRouter model IDs. When
OpenRouter returns a model list (e.g., `google/gemini-2.0-flash-001`,
`anthropic/claude-sonnet-4-20250514`, `openai/gpt-4o`), `_transform_models_response()` attempts
metadata lookup and falls back to `context_window: 128000` for all models. This is harmless for
most models, but Codex CLI may display "Model metadata not found" warnings. Also, the `display_name`
field will just be the slug, not a human-readable name.

**File/Line**: `src/thegent/routing/model_metadata.py` — `MODEL_METADATA` dict (entire file)

**Fix**: Add OpenRouter-routed model entries. Since OpenRouter uses `provider/model-name` format,
the primary models to add are:
```python
"anthropic/claude-sonnet-4-20250514": {
    "context_window": 200000,
    "cost_per_mtok": 3.00,
    "provider": "openrouter",
    "backend": "proxy",
},
"google/gemini-2.0-flash-001": {
    "context_window": 1000000,
    "cost_per_mtok": 0.15,
    "provider": "openrouter",
    "backend": "proxy",
},
"openai/gpt-4o": {
    "context_window": 128000,
    "cost_per_mtok": 2.50,
    "provider": "openrouter",
    "backend": "proxy",
},
```
The provider definitions JSON shows `google/gemini-2.0-flash-001` as the default model, so this
entry is the minimum required.

---

### Issue 4 — `_backend_path()` Incorrectly Strips `/v1` Prefix When Backend Is OpenRouter

**Severity**: P0 (blocks basic function — wrong URL constructed for OpenRouter)

**Description**: `_backend_path()` (line 535–540) checks if the backend base URL ends with `/v1`
and if so strips the `/v1` prefix from the request path:
```python
def _backend_path(backend_url: str, request_path: str) -> str:
    base = backend_url.rstrip("/")
    if base.endswith("/v1") and request_path.startswith("/v1/"):
        return request_path[4:]  # /v1/responses -> /responses
    return request_path
```
OpenRouter's base URL is `https://openrouter.ai/api/v1`. When this is the backend URL,
`base.endswith("/v1")` is `True`, so `/v1/chat/completions` becomes `/chat/completions`. The
final URL would be `https://openrouter.ai/api/v1/chat/completions` — which is correct in this
case.

However, when `_proxy_stream()` constructs the URL for streaming (line 371–373):
```python
if transform_responses:
    url = f"{backend_url.rstrip('/')}/chat/completions"
else:
    url = f"{backend_url.rstrip('/')}{path}" if path.startswith("/") else ...
```
For the `transform_responses=True` path (used by `/v1/responses`), the URL is hardcoded as
`{backend}/chat/completions` — which generates `https://openrouter.ai/api/v1/chat/completions`.
This is correct.

For the non-transform streaming path (`/v1/chat/completions`), `_backend_path()` returns
`/chat/completions` which is appended to the base URL correctly.

**Conclusion**: The path logic is actually correct for OpenRouter's `https://openrouter.ai/api/v1`
base URL. This is not a bug. However, if a user sets `backend_url` to `https://openrouter.ai/api`
(without `/v1`), the path would not be stripped. This edge case is handled by the `else` branch
which returns the path unchanged.

**Revised Severity**: Not a bug. No fix needed.

---

### Issue 5 — `verify=False` in `_proxy_request()` Disables TLS Verification

**Severity**: P1 (security concern — disables certificate validation for all backend calls)

**Description**: In `_proxy_request()` line 308:
```python
async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
```
`verify=False` disables TLS certificate validation. For the CLIProxy backend on localhost, this is
irrelevant. But the code comment implies this was added to handle the local proxy. If OpenRouter's
base URL (`https://openrouter.ai/api/v1`) were ever used directly as `backend_url`, this would
silently skip TLS verification for an external HTTPS endpoint. In the current architecture,
`backend_url` is always `http://127.0.0.1:<port>/v1` (the local CLIProxyAPIPlus), so the
production risk is minimal — but `_proxy_stream()` at line 380 does NOT have `verify=False`,
creating an inconsistency.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_proxy_request()` line 308

**Fix**: Remove `verify=False` from `_proxy_request()` to be consistent with `_proxy_stream()`.
If the CLIProxy backend requires no-verify for some reason, use `verify=False` only when
`backend_url` starts with `http://` (non-TLS).

---

### Issue 6 — `usage.total_cost` Not Extracted from OpenRouter Responses

**Severity**: P1 (cost tracking is broken for OpenRouter — `total_cost` field is ignored)

**Description**: OpenRouter returns `usage.total_cost` in USD in every non-streaming completion
response. In streaming responses, OpenRouter also returns `usage.total_cost` in the final SSE
chunk (when `stream_options: {include_usage: true}` is set, or in the terminal chunk by default).

The proxy's `_extract_usage()` function (line 85–87):
```python
def _extract_usage(chunk: dict[str, Any]) -> dict[str, Any] | None:
    return chunk.get("usage") or None
```
This extracts the entire `usage` object, which includes `total_cost` if OpenRouter sends it.
However, `_ResponsesStreamState.closing_events()` (line 244–250) only reads
`prompt_tokens`/`completion_tokens` from the usage dict and emits them in the `response.completed`
event:
```python
usage = self._usage or {}
prompt_tokens = usage.get("prompt_tokens", 0)
completion_tokens = usage.get("completion_tokens", 0)
```
The `total_cost` value from OpenRouter is silently discarded. The cost tracking infrastructure in
`routing/cost_tracker.py` is never informed of the actual cost.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_ResponsesStreamState.closing_events()` lines
190–250; `_extract_usage()` line 85–87

**Fix**: Thread `usage.total_cost` through to the cost tracker. After extracting usage:
```python
total_cost = usage.get("total_cost")
if total_cost is not None:
    # Record actual OpenRouter cost
    from thegent.routing.cost_tracker import get_cost_tracker

    tracker = get_cost_tracker()
    tracker.record_cost(total_cost, model=self.model)
```
This requires `_ResponsesStreamState` to have access to the model name (already stored as
`self.model`) and a reference to or import of the cost tracker.

---

### Issue 7 — OpenRouter-Specific Fields (`transforms`, `provider`) Not Forwarded in Request Transform

**Severity**: P2 (nice-to-have — advanced OpenRouter routing and transforms not usable)

**Description**: OpenRouter supports two non-standard request fields:
- `transforms`: Middleware transforms list (e.g., `["middle-out"]` for context window compression)
- `provider`: Provider routing preferences object with `order`, `allow_fallbacks`, `require_parameters`

When the adapter translates `/v1/responses` to `/v1/chat/completions` via
`_responses_to_chat_completions()` (line 56–72) or the equivalent in
`litellm_responses_handler.py`, these fields from the original request body are not forwarded.
The transforms are:
```python
return {
    "model": mapped_model,
    "messages": messages,
    "stream": body.get("stream", False),
    "temperature": body.get("temperature"),
    "max_tokens": body.get("max_output_tokens") or body.get("max_tokens"),
}
```
Any `transforms` or `provider` fields in the client request are dropped.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_responses_to_chat_completions()` lines 56–72;
`src/thegent/routing/litellm_responses_handler.py` — `_responses_to_chat_completions()` lines 74–102

**Fix**: Pass through OpenRouter-specific fields when translating:
```python
result = {
    "model": mapped_model,
    "messages": messages,
    "stream": body.get("stream", False),
}
for opt_field in (
    "temperature",
    "top_p",
    "top_k",
    "frequency_penalty",
    "presence_penalty",
    "repetition_penalty",
    "min_p",
    "top_a",
    "seed",
    "max_tokens",
    "transforms",
    "provider",
    "route",
    "plugins",
):
    val = body.get(opt_field)
    if val is not None:
        result[opt_field] = val
max_tokens = body.get("max_output_tokens") or body.get("max_tokens")
if max_tokens is not None:
    result["max_tokens"] = max_tokens
```

---

### Issue 8 — OpenRouter's Actual Model Used in Response Not Propagated Back

**Severity**: P2 (OpenRouter may route to a different model than requested; this difference is invisible)

**Description**: OpenRouter returns a `model` field in the response body that reflects the actual
model used (which may differ from the requested model when fallbacks occur). The streaming handler
ignores this field:
- In `_proxy_stream()`, the `stream()` generator never reads the `model` field from individual SSE
  chunks.
- `_ResponsesStreamState` is initialized with `model=model` (the requested model from the request
  body, line 377) and this value is baked into all emitted Responses API events.
- If OpenRouter routes to a fallback model, the `response.completed` event will show the wrong
  model name.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_proxy_stream()` stream generator lines 375–430

**Fix**: Extract the `model` field from the first SSE chunk and update `state.model` before
emitting preamble events:
```python
actual_model = obj.get("model") or model  # obj is the parsed SSE chunk
if not preamble_emitted:
    state.model = actual_model  # Update before preamble
```

---

### Issue 9 — OpenRouter Error Format Not Handled

**Severity**: P1 (OpenRouter errors are structured differently; they may be misinterpreted)

**Description**: OpenRouter returns errors in this format:
```json
{
  "error": {
    "message": "...",
    "type": "...",
    "param": null,
    "code": 429,
    "metadata": {"provider_name": "Anthropic", "raw": {...}}
  }
}
```
The `code` field is the HTTP status code inside the error object (not standard OpenAI which uses
`code` as a string error code). The `metadata` field contains upstream provider error details.

The current proxy returns backend errors directly (line 382–386 in `_proxy_stream()`):
```python
if resp.status_code != 200:
    err_body = await resp.aread()
    _log.warning("backend stream error %s: %s", resp.status_code, err_body[:200])
    yield f'data: {{"error":{{"message":"Backend {resp.status_code}"}}}}\n\n'.encode()
    return
```
This swallows the actual OpenRouter error body and replaces it with a generic message, losing
the `metadata.provider_name` and `metadata.raw` context that would help debug upstream failures.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_proxy_stream()` stream generator lines 382–386

**Fix**: Forward the actual error body from OpenRouter instead of replacing it:
```python
if resp.status_code != 200:
    err_body = await resp.aread()
    _log.warning("backend stream error %s: %s", resp.status_code, err_body[:200])
    # Try to parse and forward the actual error rather than replacing it
    try:
        err_obj = json.loads(err_body)
        yield f"data: {json.dumps(err_obj)}\n\n".encode()
    except (json.JSONDecodeError, ValueError):
        yield f'data: {{"error":{{"message":"Backend {resp.status_code}: {err_body[:100].decode(errors=\"replace\")}"}}}}\n\n'.encode()
    return
```

---

### Issue 10 — OpenRouter Not in `provider_types.py` or `litellm_router.py` Provider Mappings

**Severity**: P1 (LiteLLM router path is broken for OpenRouter when `use_litellm_router=True`)

**Description**: `routing/provider_types.py` classifies providers into execution paths:
```python
NATIVE_CLI_PROVIDERS = frozenset({"codex", "claude", "opencode"})
API_KEY_PROVIDERS = frozenset({"minimax", "nim", "glm", "kilo", "zen"})
LOGIN_AUTH_PROVIDERS = frozenset({"antigravity", "cursor", "kiro", "gemini", "copilot"})
```
`"openrouter"` appears in none of these. `get_execution_path("openrouter")` returns
`ExecutionPath.CLIPROXY_API` by default (the final `return` in the function), which routes it
through `http://localhost:8317/v1`. This is actually correct — OpenRouter goes through CLIProxy.

However, in `litellm_router.py`, `_get_api_key_env()`:
```python
mapping = {
    "minimax": "MINIMAX_API_KEY",
    "nim": "NVIDIA_API_KEY",
    "glm": "ZHIPU_API_KEY",
    "kilo": "KILO_API_KEY",
}
return mapping.get(provider, f"{provider.upper()}_API_KEY")
```
For `"openrouter"`, this correctly returns `"OPENROUTER_API_KEY"` via the fallback. But in
`_route_to_litellm_config()`, the provider mapping for LiteLLM model string construction:
```python
provider_mapping = {
    "gemini": "gemini",
    "claude": "anthropic",
    "minimax": "minimax",
    "glm": "zhipu",
}
litellm_provider = provider_mapping.get(provider, provider)
```
For `"openrouter"`, `litellm_provider` would be `"openrouter"` and the litellm model string would
be `"openrouter/google/gemini-2.0-flash-001"` — which is the correct LiteLLM format for OpenRouter
models. This is coincidentally correct.

**Conclusion**: The LiteLLM router path is accidentally correct for OpenRouter because the
fallback behaviors align. However, there is no explicit OpenRouter entry in `API_KEY_PROVIDERS`,
meaning OpenRouter-routed requests via LiteLLM go through CLIProxy instead of directly to
`https://openrouter.ai/api/v1`. This is actually the intended architecture (CLIProxy as the
universal gateway), but if direct OpenRouter access were ever needed without CLIProxy, this would
be a gap.

**Revised Action**: Add `"openrouter"` to `API_KEY_PROVIDERS` in `provider_types.py` and add an
explicit `"openrouter": "openai"` entry in the LiteLLM provider mapping (LiteLLM's OpenRouter
provider is `openrouter`, not `openai`). Document the explicit routing decision.

---

### Issue 11 — `/v1/responses` Path Hardcoded in Non-Transform Stream URL

**Severity**: P1 (wrong URL for Responses-API streaming to OpenRouter)

**Description**: In `_proxy_stream()` (line 371):
```python
if transform_responses:
    url = f"{backend_url.rstrip('/')}/chat/completions"
```
When `transform_responses=True` (i.e., the client called `/v1/responses`), the URL is constructed
as `{backend}/chat/completions`. If `backend_url` is `http://127.0.0.1:8317/v1`, this produces
`http://127.0.0.1:8317/v1/chat/completions` — correct.

But note there is an asymmetry with `_proxy_request()` which uses `_backend_path()` for path
rewriting. `_proxy_stream()` does NOT use `_backend_path()` and instead hardcodes `/chat/completions`
appended directly to the backend URL when transforming. This means the transform path bypasses the
path-normalization logic entirely. For a backend that is OpenRouter directly
(`https://openrouter.ai/api/v1`), this produces the correct
`https://openrouter.ai/api/v1/chat/completions`. For a backend without `/v1` suffix, it would
produce a broken URL.

**File/Line**: `src/thegent/cliproxy_adapter.py` — `_proxy_stream()` line 371

**Fix**: Use the same `_backend_path()` logic or append `/v1/chat/completions` only when the
backend URL does not already end with `/v1`:
```python
if transform_responses:
    base = backend_url.rstrip("/")
    if base.endswith("/v1"):
        url = f"{base}/chat/completions"
    else:
        url = f"{base}/v1/chat/completions"
```
This matches what `_backend_path()` does and makes the two code paths consistent.

---

### Issue 12 — OpenRouter `/v1/responses` Endpoint Does Not Exist

**Severity**: P0 (by design but must be documented) — OpenRouter only supports `/v1/chat/completions`

**Description**: OpenRouter does not implement the OpenAI Responses API (`/v1/responses`). It only
supports `/v1/chat/completions`. The adapter handles this correctly for HTTP requests via
`_responses_to_chat_completions()` and for WebSocket via the WS→SSE bridge. However, the non-LiteLLM
path in `proxy_handler()` at line 594–602 always sends Responses API requests to the backend as
`/chat/completions`:
```python
if path == "/v1/responses":
    return await _proxy_stream(
        body, req_headers, backend, "/chat/completions", transform_responses=True, model=req_model
    )
```
This is already handled correctly. No fix needed for the path routing. The issue is purely
documentation: OpenRouter support requires the adapter layer be active.

---

### Issue 13 — OpenRouter WebSocket Path Is Effectively Unsupported

**Severity**: P1 (WebSocket `/v1/responses` to OpenRouter will fail due to Issue 2 — auth header dropped)

**Description**: When Codex CLI uses WebSocket for `/v1/responses` and the backend resolves to
OpenRouter via CLIProxyAPIPlus, the WebSocket handler (`websocket_responses_handler()`) makes HTTP
requests to the CLIProxy backend. CLIProxy then forwards to OpenRouter using the API key in its
YAML config. In this architecture, the authorization header problem in Issue 2 is mitigated because
CLIProxy handles the OpenRouter authentication independently.

However, when `use_litellm=True` and the LiteLLM WebSocket handler is used
(`handle_responses_websocket()` in `litellm_responses_handler.py`), the LiteLLM router picks up
the API key from the environment (`OPENROUTER_API_KEY`). No authorization header from the client
is used; LiteLLM uses its own configured credentials.

**Conclusion**: Issue 2 only fully bites if the proxy is used as a direct pass-through to OpenRouter
without going through CLIProxyAPIPlus. In the production architecture, CLIProxy owns the OpenRouter
key and Issue 2's impact is limited to the case where a client sends `Authorization: Bearer sk-or-...`
and expects it to reach OpenRouter. Issue 2 still needs fixing for direct-proxy use cases.

---

## Checklist of Changes Needed (Priority Order)

### P0 — Blocking Issues

| # | File | Change |
|---|------|--------|
| 1 | `cliproxy_adapter.py` line 661 | Fix WebSocket handler to forward `Authorization` header to backend HTTP calls |
| 2 | `routing/model_metadata.py` | Add OpenRouter default model (`google/gemini-2.0-flash-001`) and any commonly-used OpenRouter models with accurate context windows |

### P1 — Missing Features / Broken Behavior

| # | File | Change |
|---|------|--------|
| 3 | `cliproxy_adapter.py` lines 294–296, 380 | Inject `HTTP-Referer` and `X-Title` headers when backend URL contains `openrouter.ai` |
| 4 | `cliproxy_adapter.py` lines 382–386 | Forward actual OpenRouter error body instead of replacing with generic message |
| 5 | `cliproxy_adapter.py` lines 190–250 | Thread `usage.total_cost` from OpenRouter into cost tracker after extracting usage |
| 6 | `cliproxy_adapter.py` line 308 | Remove `verify=False` from `_proxy_request()` (inconsistency with `_proxy_stream()`) |
| 7 | `routing/provider_types.py` | Add `"openrouter"` to `API_KEY_PROVIDERS` frozenset with explicit documentation |
| 8 | `routing/litellm_router.py` | Add explicit `"openrouter": "openrouter"` to provider mapping in `_route_to_litellm_config()` |
| 9 | `cliproxy_adapter.py` line 371 | Make transform stream URL consistent with `_backend_path()` logic |

### P2 — Nice-to-Have

| # | File | Change |
|---|------|--------|
| 10 | `cliproxy_adapter.py` lines 56–72 | Forward `transforms`, `provider`, `route` OpenRouter-specific fields in `_responses_to_chat_completions()` |
| 11 | `routing/litellm_responses_handler.py` lines 74–102 | Same: forward OpenRouter fields in the LiteLLM path's `_responses_to_chat_completions()` |
| 12 | `cliproxy_adapter.py` lines 375–430 | Extract actual model from SSE chunks and update `state.model` before emitting preamble events |
| 13 | `routing/harness_model_mapping.py` | Add OpenRouter model ID aliases to `CODEX_TO_BACKEND_MODEL` for any OpenRouter models exposed via Codex |

---

## Summary

The proxy passes `Authorization: Bearer sk-or-...` headers through correctly in the HTTP path
(P0 concern is only in the WebSocket path — Issue 2). There are no hardcoded `openai.com`
references in `cliproxy_adapter.py`. The `/v1/models` transformation handles `provider/model-name`
format IDs via the strip-prefix fallback but lacks actual metadata for OpenRouter models. The
`transforms` and `provider` routing fields are dropped during Responses API translation. OpenRouter
error bodies are replaced with generic messages, losing provider-specific debug context. The biggest
gaps are: (1) WebSocket drops auth header, (2) no model metadata for OpenRouter models, (3) missing
attribution headers, (4) `usage.total_cost` is discarded.

The architecture is sound for OpenRouter support: CLIProxyAPIPlus manages the OpenRouter API key
via its YAML config, the adapter translates Responses API to chat completions, and the path
rewriting correctly maps to `https://openrouter.ai/api/v1/chat/completions`. The P0 and P1 issues
above are the delta between "partially works" and "full OpenRouter support."
