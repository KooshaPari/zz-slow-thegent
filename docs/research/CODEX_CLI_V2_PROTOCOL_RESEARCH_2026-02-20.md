<DONE>
# Codex CLI v2 API Protocol Research

**Date:** 2026-02-20
**Version researched:** rust-v0.104.0 (installed 2026-02-20 via Homebrew at `/opt/homebrew/bin/codex`)
**Symptom:** All models fail with "reconnecting" and "no model metadata" errors after upgrading from prior version.
**Binary string artifacts found:** `"dynamic tool calls require api v2"`, `"expectedTurnId must not be empty"`, `"thread has no persisted rollout"`, `"sessionConfigured"` notification type.

---

## Executive Summary

Codex CLI 0.104.0 hardwires **`WireApi::Responses`** as the only supported upstream wire protocol. The `"chat"` wire API (i.e., `/v1/chat/completions`) was **fully removed** as of February 2026 (deprecation began early 2025; hard removal was February 1, 2026). The binary no longer contains a chat-completions path at all — the deserializer for `wire_api` explicitly rejects `"chat"` with an error message directing users to `"responses"`. Any proxy that only speaks `/v1/chat/completions` will fail silently or cause the "reconnecting" + "no model metadata" loop.

The Codex CLI now only calls:

1. **`POST /v1/responses`** — for all inference (HTTP SSE streaming or non-streaming)
2. **`GET /v1/models`** — for model discovery (with strict response schema requirements)
3. **`WebSocket ws://…/v1/responses`** — for streaming when `supports_websockets: true` in provider config (OpenAI built-in has this enabled)

---

## 1. The Breaking Change: `wire_api = "chat"` Removal

### What happened

The `WireApi` Rust enum in `codex-rs/core/src/model_provider_info.rs` previously had two variants: `Chat` and `Responses`. As of early February 2026, the `Chat` variant was **removed entirely**. The deserialization code now rejects the string `"chat"` with:

```
Support for the "chat" wire API is deprecated and will soon be removed.
Update your model provider definition in config.toml to use wire_api = "responses".
```

After removal (now), it is a hard parse error. Any proxy that was previously auto-detected as `wire_api = "chat"` (the old default when omitted) is now broken.

### Built-in OpenAI provider

The `create_openai_provider()` function now configures:

```rust
ModelProviderInfo {
    wire_api: WireApi::Responses,   // hardcoded — only valid value
    base_url: env("OPENAI_BASE_URL").unwrap_or("https://api.openai.com/v1"),
    supports_websockets: true,       // enables WebSocket streaming
    requires_openai_auth: true,
    // ...
}
```

**`supports_websockets: true` on the OpenAI provider means Codex will attempt a WebSocket connection to `/v1/responses` instead of HTTP SSE when using the built-in OpenAI provider.** For a proxy that only handles HTTP, this is an additional breaking point.

### Config precedence for custom proxies

If a user sets `OPENAI_BASE_URL=http://proxy:port`, Codex uses that URL with the same `WireApi::Responses` and `supports_websockets: true`. This means the proxy at `http://proxy:port` must support BOTH:

- `POST /v1/responses` (HTTP, non-streaming)
- `POST /v1/responses` (HTTP SSE streaming, `stream: true`)
- `WebSocket /v1/responses` (WebSocket streaming) — **if proxy is the OpenAI provider**

For a custom `model_provider` definition in config.toml with `wire_api = "responses"` and no `supports_websockets`, only HTTP is used.

---

## 2. Upstream HTTP Endpoints Called by Codex 0.104.0

### 2a. Model List — `GET /v1/models`

Called on startup and periodically for cache invalidation.

**Request:**

```
GET /v1/models HTTP/1.1
Authorization: Bearer <token>
codex-cli-version: <version>
```

**Required response format (strict):**

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-5.2-codex",
      "object": "model",
      "created": 1700000000,
      "owned_by": "openai",
      "context_window": 128000,
      "max_completion_tokens": 8192
    }
  ]
}
```

**Critical requirements (0.103+ changes):**

- The key MUST be `"data"` (not `"models"`) — OpenAI-standard format
- `"object": "list"` MUST be present at the top level
- **`x-models-etag` response header** — SHA256 of sorted model IDs. Codex 0.104.0 uses this for ETag-based caching. Without it, the model list is re-fetched on every request, and the cache never becomes valid
- `"no model metadata"` error: Codex expects each model entry to have sufficient metadata. If `context_window` or similar fields are missing, Codex logs the "no model metadata for model X" error and may refuse to use the model
- **Version 0.103 removed `remote_models` feature flag**: Previously a feature flag prevented fetching remote model metadata when disabled; now it is always fetched and the local metadata MUST match (or the response must include it)
- **Version 0.104 change**: Model identification now relies on **response headers** (not response body model slug). Specifically, Codex reads the `x-model` or similar response header to identify which model responded, not the `model` field in the response body. This matters for downgrade detection

**What "no model metadata" means in practice:**
The Codex binary has a built-in static list of models it knows about (gpt-5, gpt-5.2-codex, gpt-5.3-codex, etc.). When the proxy returns a model ID via `/v1/models` that is NOT in Codex's built-in metadata table, Codex shows "no model metadata for X" and falls into the reconnecting loop, because it cannot construct a valid inference request without knowing the context window and capabilities of the model.

### 2b. Inference — `POST /v1/responses`

This is the ONLY inference endpoint. The proxy MUST implement it.

**Request body:**

```json
{
  "model": "gpt-5.2-codex",
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Write hello world in Python"
        }
      ]
    }
  ],
  "stream": true,
  "max_output_tokens": 8192,
  "reasoning": {
    "effort": "medium",
    "summary": "auto"
  },
  "tools": [
    {
      "type": "function",
      "name": "shell",
      "description": "...",
      "parameters": { ... }
    }
  ],
  "previous_response_id": "resp_abc123",
  "instructions": "You are a coding assistant."
}
```

**Key differences from Chat Completions:**

- `input` array (not `messages`) with typed content items (`input_text`, `input_image`, `input_file`)
- `max_output_tokens` (not `max_tokens`)
- `reasoning.effort` for o-series/codex models
- `previous_response_id` for stateful conversation chaining (server-side history)
- `instructions` for system-level guidance (replaces `system` role message)

**Non-streaming response (stream: false):**

```json
{
  "id": "resp_67ccfcdd16748190a91872c75d38539e09e4d4aac714747c",
  "object": "response",
  "created_at": 1740000000,
  "status": "completed",
  "model": "gpt-5.2-codex",
  "output": [
    {
      "id": "msg_abc",
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Here is hello world in Python..."
        }
      ],
      "status": "completed"
    }
  ],
  "usage": {
    "input_tokens": 120,
    "output_tokens": 50,
    "total_tokens": 170
  }
}
```

### 2c. Streaming Response Format (HTTP SSE)

When `stream: true`, the response is `Content-Type: text/event-stream` with Server-Sent Events.

**Complete ordered event sequence:**

```
data: {"type":"response.created","response":{"id":"resp_abc","object":"response","status":"in_progress","model":"gpt-5.2-codex","output":[],"created_at":1740000000}}

data: {"type":"response.in_progress","response":{"id":"resp_abc","object":"response","status":"in_progress","model":"gpt-5.2-codex","output":[]}}

data: {"type":"response.output_item.added","output_index":0,"item":{"id":"item_xyz","type":"message","role":"assistant","content":[],"status":"in_progress"}}

data: {"type":"response.content_part.added","item_id":"item_xyz","output_index":0,"content_index":0,"part":{"type":"output_text","text":""}}

data: {"type":"response.output_text.delta","item_id":"item_xyz","output_index":0,"content_index":0,"delta":"Hello","sequence_number":1}

data: {"type":"response.output_text.delta","item_id":"item_xyz","output_index":0,"content_index":0,"delta":", world","sequence_number":2}

data: {"type":"response.output_text.done","item_id":"item_xyz","output_index":0,"content_index":0,"text":"Hello, world"}

data: {"type":"response.content_part.done","item_id":"item_xyz","output_index":0,"content_index":0,"part":{"type":"output_text","text":"Hello, world"}}

data: {"type":"response.output_item.done","output_index":0,"item":{"id":"item_xyz","type":"message","role":"assistant","content":[{"type":"output_text","text":"Hello, world"}],"status":"completed"}}

data: {"type":"response.completed","response":{"id":"resp_abc","object":"response","status":"completed","model":"gpt-5.2-codex","output":[...],"usage":{"input_tokens":10,"output_tokens":3,"total_tokens":13}}}
```

**Full event type catalog:**

- `response.created` — Response object with `status: "in_progress"`
- `response.in_progress` — Heartbeat while processing
- `response.output_item.added` — New output item (message, function_call, reasoning)
- `response.content_part.added` — New content part within an output item
- `response.output_text.delta` — Text token delta with `sequence_number`
- `response.output_text.annotation.added` — Citation/annotation
- `response.output_text.done` — Complete text for a part
- `response.reasoning_text.delta` — Reasoning token (o-series models)
- `response.reasoning_text.done` — Complete reasoning text
- `response.refusal.delta` — Refusal text delta
- `response.refusal.done` — Complete refusal
- `response.function_call_arguments.delta` — Tool call argument streaming
- `response.function_call_arguments.done` — Complete tool call args
- `response.content_part.done` — Content part completed
- `response.output_item.done` — Output item completed
- `response.completed` — Full response object with final output and usage
- `response.failed` — Error response
- `response.incomplete` — Response cut off (max tokens, content filter, etc.)
- `error` — Protocol-level error

**Critical proxy requirement:** The proxy MUST emit `response.created` as the FIRST event with a valid `response.id`. Codex tracks this ID and uses it for `previous_response_id` in subsequent turns. Without a valid response ID, conversation chaining breaks.

---

## 3. WebSocket Protocol for `/v1/responses`

### 3a. When WebSocket is used

WebSocket is used when the **model provider config** has `supports_websockets: true`. The built-in OpenAI provider has this enabled. Custom proxies defined in config.toml do NOT have it by default. This means:

- If using `OPENAI_BASE_URL` to point to the proxy → WebSocket is attempted
- If using a custom `[model_providers.proxy]` section without `supports_websockets` → HTTP SSE is used

### 3b. WebSocket connection

```
GET /v1/responses HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: ...
codex-cli-version: <version>
Authorization: Bearer <token>
```

### 3c. WebSocket message format

The WebSocket protocol is **NOT** JSON-RPC. It is the same SSE event payload format sent as WebSocket text frames.

**Client sends (single JSON message per request):**

```json
{
  "model": "gpt-5.2-codex",
  "input": [...],
  "stream": true,
  "max_output_tokens": 8192,
  "tools": [...],
  "previous_response_id": "resp_abc"
}
```

**Server sends (one JSON message per event frame):**

```json
{"type": "response.created", "response": {...}}
{"type": "response.output_text.delta", "item_id": "...", "delta": "Hello", "sequence_number": 1}
...
{"type": "response.completed", "response": {...}}
```

**Connection lifecycle:** After `response.completed` is sent, the connection stays open for subsequent requests. The client sends a new request JSON frame; the server responds with a new stream of events. This is a persistent connection, not request-response.

### 3d. `sessionConfigured` notification (found in binary strings)

The `sessionConfigured` notification (type `"codex/event/session_configured"` in app-server v2 protocol) is an **internal app-server protocol notification** sent from the Codex app-server to its attached UI clients (TUI, IDE plugins, etc.) — NOT from the upstream model API to Codex.

This string appearing in the binary relates to the **Codex app-server** (the JSON-RPC 2.0 server that Codex itself exposes to IDE plugins). It is NOT part of the upstream OpenAI API protocol. Specifically:

- The app-server sends `"codex/event/session_configured"` to connected clients after the session is fully configured
- Clients can opt out via `optOutNotificationMethods: ["codex/event/session_configured"]` in `initialize.params.capabilities`
- This is triggered during Codex's internal initialization, NOT during upstream API calls

**Relevance to proxy:** This notification fires internally. If the proxy disrupts Codex's ability to connect to the upstream API, Codex may fail before ever emitting `sessionConfigured` to its clients — causing IDE plugins to show "reconnecting."

### 3e. `expectedTurnId` (found in binary strings)

This is part of the **app-server v2 protocol** for the `turn/steer` method:

```json
{
  "method": "turn/steer",
  "id": 5,
  "params": {
    "threadId": "thr_abc",
    "expectedTurnId": "turn_xyz",   // MUST match active turn's ID
    "input": [...]
  }
}
```

`expectedTurnId` is a concurrency guard: it ensures the `turn/steer` call operates on the correct in-flight turn and prevents race conditions. The error `"expectedTurnId must not be empty"` means the client sent `turn/steer` without providing the required turn ID — it is a validation error in the app-server, not an upstream API error.

**Relevance to proxy:** Not directly proxy-related. This error indicates the IDE plugin (cursor, VSCode extension, etc.) is sending malformed `turn/steer` requests to the Codex app-server. Could appear if the app-server is in a broken state due to the upstream proxy failure.

### 3f. `"thread has no persisted rollout"` / `"dynamic tool calls require api v2"`

**`"thread has no persisted rollout"`**: The Codex app-server persists dynamic tools in "thread rollout metadata." When a thread is resumed and the persisted state is missing (expired or never created because the prior request failed), this error appears. It is a consequence of the upstream proxy failure — the initial request never completed, so no rollout was persisted.

**`"dynamic tool calls require api v2"`**: Dynamic tools (injected at `thread/start` via `capabilities.experimentalApi: true`) require the app-server v2 API. If Codex is running in a degraded mode because the upstream connection failed, it may not have initialized the v2 path, causing this error when an IDE plugin attempts to use dynamic tools.

**Root cause chain:** Proxy incompatibility → upstream request fails → no response ID returned → session state never initialized → app-server v2 features fail → IDE plugins show "reconnecting" and the error strings above.

---

## 4. Version-by-Version Changelog (0.99 → 0.104)

### rust-v0.99.0

- Removed `remote_models` feature flag — model metadata is now ALWAYS fetched from the upstream `/v1/models` endpoint. Previously the flag could suppress this and use only local defaults. Now if `/v1/models` doesn't return proper metadata, Codex has no fallback.

### rust-v0.100.0 / v0.101.0

- App-server WebSocket transport reintroduced with split inbound/outbound architecture
- `js_repl` runtime with persistent state across tool calls
- Multiple simultaneous rate limits support
- Memory management slash commands

### rust-v0.102.0

- `model/rerouted` notification for detecting model reroutes
- Structured network approval handling
- App-server fuzzy file search with explicit session-complete signaling

### rust-v0.103.0 (2026-02-17)

- App listing responses include richer app details
- Commit co-author attribution improvements

### rust-v0.104.0 (2026-02-18) — **CURRENT BREAKING VERSION**

- Added `WS_PROXY`/`WSS_PROXY` environment support for WebSocket proxying
- App-server v2 emits thread archive/unarchive notifications
- Command approvals now carry distinct approval IDs for multiple approvals
- **Safety-check model identification now uses response HEADERS, not response body model slug** — proxy must set `x-model` or equivalent header, or the model field in response headers, correctly
- Fixed `Ctrl+C`/`Ctrl+D` during resume/fork workflows
- ETag/reasoning metadata parity for WebSocket

---

## 5. What Our Proxy (`cliproxy_adapter.py`) Currently Does

### What works

- Accepts `POST /v1/responses` and translates to `POST /v1/chat/completions` on the backend
- Translates Responses API input format to Chat Completions messages
- Transforms Chat Completions SSE back to Responses API events (partially)
- Handles `GET /v1/models` with `_transform_models_response()` (adds `"object": "list"` wrapping, `x-models-etag` header)
- WebSocket `/v1/responses` bridge: receives WS frame, POSTs to backend chat completions, sends responses back as WS frames

### What is broken or incomplete

**Problem 1: Streaming event sequence is missing required leading events**

The proxy emits only `response.output_item.added` deltas and a final `response.completed`. It does NOT emit:

- `response.created` (CRITICAL — Codex needs the response ID from this event)
- `response.in_progress`
- `response.content_part.added`
- `response.output_text.delta` (with `sequence_number` and `item_id`)
- `response.output_text.done`
- `response.content_part.done`
- `response.output_item.done`

The `_chat_completions_to_responses()` function wraps every token delta in a `response.output_item.added` event, which is wrong — `response.output_item.added` is emitted ONCE when a new output item begins, not once per token. Token-level streaming uses `response.output_text.delta`.

**Problem 2: Missing `response.created` with response ID**

`response.created` MUST be the first event and MUST contain a `response.id`. Without this:

- Codex cannot chain conversations with `previous_response_id`
- After 0.99 removed `remote_models` flag, Codex may rely on the response ID to track model association
- The "reconnecting" loop may be triggered by the absence of this initialization event

**Problem 3: Model metadata format for `/v1/models` may be missing Codex-specific fields**

Codex 0.104.0 checks for specific fields in model objects. Missing fields cause "no model metadata." Required fields per model object:

```json
{
  "id": "model-id",
  "object": "model",
  "context_window": 128000,
  "max_completion_tokens": 16384,
  "supports_reasoning": false,
  "owned_by": "openai"
}
```

The proxy's `model_metadata.py` has `gpt-5-mini` listed with `context_window: 128000` and `max_completion_tokens: 8192` — these may be the right fields but must match what Codex 0.104.0 expects. Missing `supports_reasoning` may cause issues for o-series model detection.

**Problem 4: Safety-check model header not set (0.104.0 change)**

0.104.0 now reads model identification from the **response header** (`x-model` or `openai-model` header), not from the response body. The proxy currently does not set this header. Without it, Codex may fail its safety-check downgrade logic.

**Problem 5: WebSocket streaming event format**

The WebSocket handler at line 442 sends:

```python
await websocket.send_json({"type": "response.completed"})
```

But Codex expects `response.completed` to include the full response object:

```json
{"type": "response.completed", "response": {"id": "...", "output": [...], "usage": {...}}}
```

Without the `response` object inside `response.completed`, Codex does not receive usage data and may not properly close the turn.

---

## 6. Recommended Fix Approach

### Priority 1 (Critical — fix the "reconnecting" loop)

**Fix the SSE streaming event sequence to emit the proper event series:**

The proxy must emit the following minimal valid sequence for a text response:

```python
import uuid, time, json


def make_responses_stream(model: str, content_chunks):
    resp_id = f"resp_{uuid.uuid4().hex}"
    item_id = f"item_{uuid.uuid4().hex}"
    now = int(time.time())

    # 1. response.created
    yield f"data: {json.dumps({'type': 'response.created', 'response': {'id': resp_id, 'object': 'response', 'created_at': now, 'status': 'in_progress', 'model': model, 'output': []}})}\n\n"

    # 2. response.output_item.added (once, at start of message)
    yield f"data: {json.dumps({'type': 'response.output_item.added', 'output_index': 0, 'item': {'id': item_id, 'type': 'message', 'role': 'assistant', 'content': [], 'status': 'in_progress'}})}\n\n"

    # 3. response.content_part.added (once)
    yield f"data: {json.dumps({'type': 'response.content_part.added', 'item_id': item_id, 'output_index': 0, 'content_index': 0, 'part': {'type': 'output_text', 'text': ''}})}\n\n"

    # 4. response.output_text.delta (one per token chunk)
    full_text = ""
    for i, chunk in enumerate(content_chunks, 1):
        full_text += chunk
        yield f"data: {json.dumps({'type': 'response.output_text.delta', 'item_id': item_id, 'output_index': 0, 'content_index': 0, 'delta': chunk, 'sequence_number': i})}\n\n"

    # 5. response.output_text.done
    yield f"data: {json.dumps({'type': 'response.output_text.done', 'item_id': item_id, 'output_index': 0, 'content_index': 0, 'text': full_text})}\n\n"

    # 6. response.content_part.done
    yield f"data: {json.dumps({'type': 'response.content_part.done', 'item_id': item_id, 'output_index': 0, 'content_index': 0, 'part': {'type': 'output_text', 'text': full_text}})}\n\n"

    # 7. response.output_item.done
    yield f"data: {json.dumps({'type': 'response.output_item.done', 'output_index': 0, 'item': {'id': item_id, 'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': full_text}], 'status': 'completed'}})}\n\n"

    # 8. response.completed (with full response object)
    yield f"data: {json.dumps({'type': 'response.completed', 'response': {'id': resp_id, 'object': 'response', 'created_at': now, 'status': 'completed', 'model': model, 'output': [{'id': item_id, 'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': full_text}], 'status': 'completed'}], 'usage': {'input_tokens': 0, 'output_tokens': len(full_text.split()), 'total_tokens': len(full_text.split())}}})}\n\n"
```

### Priority 2 (Model metadata)

**Add the required model header in streaming responses:**

```python
headers = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "openai-model": model_name,  # 0.104.0 reads model from header, not body
    "x-request-id": request_id,
}
```

**Ensure `/v1/models` returns Codex-recognized model IDs:**

The model IDs returned by `/v1/models` MUST match what Codex's built-in metadata table contains (gpt-5, gpt-5-mini, gpt-5.2-codex, gpt-5.3-codex, gpt-5.3-codex-spark, etc.) — or the model must have full metadata in the response. Since Codex 0.99 removed the fallback flag, unknown models will always show "no model metadata."

**Recommendation:** The `/v1/models` response should alias all proxy models to one of the Codex-known IDs, OR the model entries must include the full metadata fields Codex needs.

### Priority 3 (WebSocket)

**Fix WebSocket `response.completed` to include the full response object** (see Priority 1 for format).

**Option: Disable WebSocket for custom proxy providers.** If the proxy is configured via `[model_providers.proxy]` in config.toml (not via `OPENAI_BASE_URL`), it defaults to `supports_websockets: false`, using HTTP SSE instead. This is the safer path for proxy compatibility.

If the user is using `OPENAI_BASE_URL`, Codex uses the built-in OpenAI provider config with `supports_websockets: true`. In this case, the proxy MUST handle WebSocket or the user must switch to a config.toml custom provider definition.

### Priority 4 (Non-streaming response object)

**Fix non-streaming responses to include a valid `id` and `object: "response"` field:**

```json
{
  "id": "resp_<uuid>",
  "object": "response",
  "created_at": 1740000000,
  "status": "completed",
  "model": "gpt-5.2-codex",
  "output": [
    {
      "id": "item_<uuid>",
      "type": "message",
      "role": "assistant",
      "content": [{ "type": "output_text", "text": "..." }],
      "status": "completed"
    }
  ],
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "total_tokens": 150
  }
}
```

---

## 7. Protocol Summary Table

| Endpoint        | Method    | Purpose          | Notes                                                                    |
| --------------- | --------- | ---------------- | ------------------------------------------------------------------------ |
| `/v1/models`    | GET       | Model discovery  | Must return `{"object":"list","data":[...]}` with `x-models-etag` header |
| `/v1/responses` | POST      | Inference (HTTP) | Accepts Responses API format; returns SSE stream or full response object |
| `/v1/responses` | WebSocket | Inference (WS)   | Same format over WebSocket frames; persistent connection                 |

| Wire format              | Used when                                    |
| ------------------------ | -------------------------------------------- |
| `wire_api = "responses"` | **Always** (only valid value as of Feb 2026) |
| `wire_api = "chat"`      | **REMOVED** — hard error                     |

| Event                         | Required | Notes                               |
| ----------------------------- | -------- | ----------------------------------- |
| `response.created`            | **Yes**  | First event; contains `response.id` |
| `response.output_item.added`  | Yes      | Once per output item                |
| `response.content_part.added` | Yes      | Once per content part               |
| `response.output_text.delta`  | Yes      | Per token; needs `sequence_number`  |
| `response.output_text.done`   | Yes      | Completes text part                 |
| `response.content_part.done`  | Yes      | Completes content part              |
| `response.output_item.done`   | Yes      | Completes output item               |
| `response.completed`          | **Yes**  | Must include full response object   |

---

## 8. Sources

- [Codex Changelog](https://developers.openai.com/codex/changelog/)
- [Codex Configuration Reference](https://developers.openai.com/codex/config-reference/)
- [Codex Advanced Configuration](https://developers.openai.com/codex/config-advanced/)
- [Codex Sample Configuration](https://developers.openai.com/codex/config-sample/)
- [Codex App Server Protocol](https://developers.openai.com/codex/app-server/)
- [openai/codex Releases](https://github.com/openai/codex/releases)
- [rust-v0.104.0 Release](https://newreleases.io/project/github/openai/codex/release/rust-v0.104.0)
- [Codex model_provider_info.rs source](https://github.com/openai/codex/blob/main/codex-rs/core/src/model_provider_info.rs)
- [Deprecating chat/completions Discussion](https://github.com/openai/codex/discussions/7782)
- [Jan/llama.cpp compatibility issue](https://github.com/janhq/jan/issues/7413)
- [Config.toml Updated Keys issue](https://github.com/openai/codex/issues/2760)
- [LiteLLM Responses API](https://docs.litellm.ai/docs/providers/openai/responses_api)
- [Kong AI Gateway Codex guide](https://developer.konghq.com/how-to/use-codex-with-ai-gateway/)
- [Nexus Router Codex integration](https://nexusrouter.com/docs/usage/openai-codex-integration)
- [aiproxy Codex setup](https://aiproxy.dev/docs/agent-setup/codex)
- [DeepWiki Codex architecture](https://deepwiki.com/openai/codex/5.2-command-execution-pipeline)
- [OpenAI Agents SDK Streaming](https://openai.github.io/openai-agents-python/streaming/)
- [Releasebot openai/codex](https://releasebot.io/updates/openai/codex)
