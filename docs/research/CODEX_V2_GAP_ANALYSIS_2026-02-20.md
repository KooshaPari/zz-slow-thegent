<DONE>
# Codex CLI 0.104.0 — v2 Protocol Gap Analysis

**Date:** 2026-02-20
**Status:** Draft
**Scope:** What our proxy currently returns vs what Codex CLI 0.104.0 requires.

---

## Executive Summary

Codex CLI 0.104.0 broke because it migrated from the Responses API (HTTP SSE) to a stateful **JSON-RPC 2.0 over WebSocket** protocol (v2). Our proxy has:

1. A correct `/v1/responses` HTTP POST handler (adapter path).
2. A basic `/v1/responses/ws` WebSocket handler that speaks a single-turn, single-message protocol.
3. A `/v1/models` endpoint that returns a `{"models": [...]}` shape (transformed from CLIProxy's `{"data": [...]}`).

What we are **missing**:

1. The correct WebSocket **endpoint path** — codex 0.104.0 connects to `/v1/responses` (no `/ws` suffix) over the `ws://` scheme, not `/v1/responses/ws`.
2. A full **JSON-RPC 2.0 session protocol** on that WebSocket: `session_configured` notification, multi-turn `response.create` / `response.append` calls, `thread/`, `turn/`, and `item/` lifecycle events.
3. Required **response fields** that trigger "reconnecting" and "no model metadata" errors.
4. The `x-models-etag` response header on `/v1/models`.

Each gap is detailed below.

---

## Architecture: Two Proxy Paths

The codebase has two independent paths that serve Codex. Understanding both is critical.

### Path A — Adapter (primary, `THGENT_CLIPROXY_ADAPTER=1`)

```
Codex CLI
    |
    v
cliproxy_adapter.py  (Starlette, port 8317)
    |-- WebSocketRoute("/v1/responses",  websocket_responses_handler)
    |-- Route("/{path:path}", proxy_handler)
            |
            v
CLIProxyAPIPlus  (port 8318, backend)
```

- WebSocket path is `/v1/responses` (correct path).
- Bridges WS → HTTP SSE to the CLIProxy backend.
- Models endpoint transforms `{"data": [...]}` → `{"models": [...]}`.

### Path B — MCP Server (secondary, `http_app()`)

```
Codex CLI
    |
    v
mcp/server.py  (FastMCP / Starlette, port 3847)
    |-- POST /v1/responses        → litellm_responses_handler.handle_responses_request
    |-- WS   /v1/responses/ws     → litellm_responses_handler.handle_responses_websocket
```

- WebSocket path is `/v1/responses/ws` — wrong suffix, codex will not connect.
- No `/v1/models` endpoint is registered here at all.

---

## Gap 1 — WebSocket Path Mismatch (MCP Server path)

### What we have

`mcp/server.py` registers the WebSocket at:
```
/v1/responses/ws
```

### What Codex 0.104.0 expects

From binary string analysis:
- Codex opens `ws://<host>/v1/responses` (no `/ws` suffix).
- It then sends JSON-RPC 2.0 `method: "response.create"` frames on that connection.

The **adapter path** (`cliproxy_adapter.py`) uses:
```python
WebSocketRoute("/v1/responses", websocket_responses_handler)
```
which is **correct**. The MCP server path is the one that is wrong.

### Fix

In `mcp/server.py`, change:
```python
cast("Any", app).add_websocket_route(
    "/v1/responses/ws",
    handle_responses_websocket,
)
```
to:
```python
cast("Any", app).add_websocket_route(
    "/v1/responses",
    handle_responses_websocket,
)
```

---

## Gap 2 — JSON-RPC 2.0 Session Protocol (Both Paths)

### What we have

Both `litellm_responses_handler.handle_responses_websocket` and `cliproxy_adapter.websocket_responses_handler` implement a **single-turn, single-message** protocol:

1. `await websocket.receive_json()` — reads one message.
2. Routes it as a completion.
3. Streams back events.
4. Sends `{"type": "response.completed"}`.
5. Closes the socket.

```python
# litellm_responses_handler.py — current WebSocket handler
data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
chat_request = _responses_to_chat_completions(data)
...
async for chunk in router.acompletion(..., stream=True):
    responses_event = _chat_completions_to_responses(chunk_dict)
    if responses_event:
        await websocket.send_json(responses_event)
await websocket.send_json({"type": "response.completed"})
```

### What Codex 0.104.0 expects

Codex 0.104.0 uses JSON-RPC 2.0 over WebSocket as a persistent, multi-turn session. The frames are:

```
Client → Server (method call):
{
  "jsonrpc": "2.0",
  "id": "<request_id>",
  "method": "response.create",
  "params": {
    "model": "...",
    "input": [...],
    "previous_response_id": "<id or null>",
    "stream": true
  }
}

Server → Client (notification, sent immediately on session open):
{
  "jsonrpc": "2.0",
  "method": "session_configured",
  "params": { ... }
}

Server → Client (streaming event notifications):
{"jsonrpc":"2.0","method":"thread/started","params":{"thread_id":"..."}}
{"jsonrpc":"2.0","method":"turn/started","params":{"turn_id":"..."}}
{"jsonrpc":"2.0","method":"item/started","params":{"item_id":"..."}}
{"jsonrpc":"2.0","method":"item/agentMessage/delta","params":{"delta":{"text":"..."}}}
{"jsonrpc":"2.0","method":"item/completed","params":{"item_id":"..."}}
{"jsonrpc":"2.0","method":"turn/completed","params":{"turn_id":"..."}}

Server → Client (JSON-RPC result for the original call):
{
  "jsonrpc": "2.0",
  "id": "<request_id>",
  "result": {
    "response_id": "<id>",
    "status": "completed"
  }
}
```

Key behavioral differences:

| Dimension | Our current implementation | Codex 0.104.0 expects |
|---|---|---|
| Protocol framing | Raw JSON objects | JSON-RPC 2.0 (`jsonrpc`, `id`, `method`, `params`) |
| Session lifecycle | One message per connection | Persistent connection; multiple `response.create` calls |
| On-connect notification | None | `session_configured` notification must be sent immediately |
| Streaming events | `response.output_item.added` | `thread/started`, `turn/started`, `item/started`, `item/agentMessage/delta`, `item/completed`, `turn/completed` |
| Completion signal | `{"type": "response.completed"}` | JSON-RPC result frame with `response_id` field |
| Turn continuity | Not supported | `previous_response_id` links turns; `expectedTurnId must not be empty` error if missing |
| Multi-turn | Not supported | `response.append` method for continuing turns |

### Codex "reconnecting" error root cause

Codex says "reconnecting" when:

1. It opens a WebSocket to `/v1/responses`.
2. Does NOT receive a `session_configured` notification within a short timeout.
3. Closes and retries.

Our handler never sends `session_configured`, so codex reconnects in a loop.

### Codex "thread has no persisted rollout" error root cause

Sent by codex internally when `previous_response_id` is provided but no thread state exists on the server side. Our stateless handler discards `previous_response_id` entirely — we read it from the payload only if present in `input`, which it is not; it is a top-level field.

### Fix outline

Both handlers need to be replaced with a JSON-RPC 2.0 dispatch loop:

```
on_connect:
    send session_configured notification

loop:
    frame = await websocket.receive_json()
    assert frame["jsonrpc"] == "2.0"
    method = frame["method"]

    if method == "response.create":
        run_completion(frame["params"])
        # emit thread/started, turn/started, item events
        # emit JSON-RPC result with response_id

    elif method == "response.append":
        continue_completion(frame["params"])
```

The server must also maintain a minimal thread state (at minimum: a map from `response_id` → last assistant output) to support `previous_response_id` linking.

---

## Gap 3 — Missing Fields in `/v1/responses` HTTP Response

### What we have

Non-streaming response from `litellm_responses_handler.handle_responses_request`:

```json
{
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [{"type": "text", "text": "..."}]
    }
  ]
}
```

### What Codex 0.104.0 expects

The Responses API non-streaming response requires at minimum:

```json
{
  "id": "resp_<uuid>",
  "object": "response",
  "created_at": 1234567890,
  "model": "gpt-5.3-codex",
  "status": "completed",
  "output": [
    {
      "id": "item_<uuid>",
      "type": "message",
      "role": "assistant",
      "status": "completed",
      "content": [{"type": "output_text", "text": "..."}]
    }
  ],
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  }
}
```

Missing fields that cause "no model metadata" or silent failures:

| Field | Missing from our response | Why Codex needs it |
|---|---|---|
| `id` (top-level `resp_*`) | Yes | Used as `previous_response_id` in next turn |
| `object: "response"` | Yes | Codex type-checks this field |
| `created_at` | Yes | Required by Responses API schema |
| `model` | Yes | Echo-back for routing display |
| `status: "completed"` | Yes | Codex state machine checks this |
| `output[].id` (`item_*`) | Yes | Item tracking |
| `output[].status` | Yes | Per-item completion status |
| `content[].type: "output_text"` | Yes (we emit `"text"`) | Codex distinguishes `output_text` from `input_text` |
| `usage` | Yes | Token accounting |

### Fix

Add a `_build_responses_response()` function in `litellm_responses_handler.py` that populates all required fields from the LiteLLM response, using `uuid4()` for `id` and `item_id`, and echoing `model` from the request.

---

## Gap 4 — Streaming Event Format for HTTP SSE

### What we have

`_chat_completions_to_responses()` emits:

```json
{"type": "response.output_item.added", "item": {"type": "message", "role": "assistant", "content": [{"type": "text", "text": "..."}]}}
```

Completion:
```
data: {"type": "response.completed"}
```

### What Codex 0.104.0 expects for Responses API SSE (HTTP path)

Codex 0.104.0 expects the full OpenAI Responses API SSE event stream:

```
data: {"type":"response.created","response":{"id":"resp_...","object":"response","status":"in_progress",...}}

data: {"type":"response.output_item.added","response_id":"resp_...","output_index":0,"item":{"id":"item_...","type":"message","role":"assistant","status":"in_progress","content":[]}}

data: {"type":"response.content_part.added","response_id":"resp_...","item_id":"item_...","output_index":0,"content_index":0,"part":{"type":"output_text","text":""}}

data: {"type":"response.content_part.delta","response_id":"resp_...","item_id":"item_...","output_index":0,"content_index":0,"delta":{"type":"text_delta","text":"Hello"}}

data: {"type":"response.content_part.done","response_id":"resp_...","item_id":"item_...","output_index":0,"content_index":0,"part":{"type":"output_text","text":"Hello..."}}

data: {"type":"response.output_item.done","response_id":"resp_...","output_index":0,"item":{"id":"item_...","type":"message","role":"assistant","status":"completed","content":[...]}}

data: {"type":"response.completed","response":{"id":"resp_...","status":"completed","output":[...],"usage":{...}}}
```

Missing event types: `response.created`, `response.content_part.added`, `response.content_part.delta`, `response.content_part.done`, `response.output_item.done`.
Missing fields in existing events: `response_id`, `output_index`, `item.id`, `item.status`.

---

## Gap 5 — `/v1/models` Response Format

### What we have

The adapter's `_transform_models_response()` transforms `{"data": [...]}` → `{"models": [...]}` and enriches each entry with `context_window`, `context_length`, `max_completion_tokens`, and `slug`. This is the **correct path** (adapter path).

The MCP server (`mcp/server.py`) has **no `/v1/models` HTTP route at all**. The MCP-only path leaves Codex with no model list endpoint.

### What Codex 0.104.0 expects from `/v1/models`

```json
{
  "models": [
    {
      "id": "gpt-5.3-codex",
      "slug": "gpt-5.3-codex",
      "object": "model",
      "created": 1700000000,
      "context_window": 128000,
      "context_length": 128000,
      "max_completion_tokens": 8192,
      "capabilities": {
        "reasoning": true,
        "tool_use": true,
        "vision": false
      }
    }
  ]
}
```

### "no model metadata" error root cause

Codex says "Model metadata for X not found" when a model appears in the `models` list but lacks `context_window` / `context_length` / `max_completion_tokens`. Our adapter path does enrich these from `model_metadata.py`, but only if `get_model_metadata()` returns a result. Models not in `MODEL_METADATA` (e.g., pass-through provider aliases not in the registry) will get no enrichment and trigger the warning.

Additionally, the MCP server path has no `/v1/models` route, so when a client points at the MCP port (3847), any call to `/v1/models` returns 404, which codex treats as a fatal startup error.

### "x-models-etag" header

Codex 0.104.0 sends `If-None-Match: <etag>` on repeated `/v1/models` calls and expects the server to respond with `304 Not Modified` when the model list has not changed. Our server never returns `x-models-etag`, so codex always does a full fetch. This is a performance issue, not a breakage, but it stresses the backend on every agent turn.

### Fix for `/v1/models`

1. Register a `/v1/models` GET route in `mcp/server.py`'s `http_app()`.
2. Return `{"models": [...]}` populated from `MODEL_METADATA`.
3. Add a stable ETag (hash of the model list) and handle `If-None-Match`.

---

## Gap 6 — Missing `model/rerouted` and `account/rateLimits/updated` Events

### What we have

Neither event is emitted anywhere.

### What Codex 0.104.0 expects

These are JSON-RPC notification events sent over the WebSocket by the server proactively:

- `model/rerouted` — sent when the actual model serving the request differs from the requested model (e.g., codex fell back from `gpt-5.3-codex` to `gpt-5.3-codex-spark`). Codex displays this in its UI.
- `account/rateLimits/updated` — sent when rate limit headers are received from the upstream. Codex uses this to throttle itself before hitting 429s.

These are **nice-to-have** for correct behavior but not required for baseline functionality.

---

## Gap 7 — `prefer_websockets` Config Flag Not Honored

### What we have

The adapter checks `settings.use_litellm_router` to decide routing, but there is no `prefer_websockets` setting.

### What Codex 0.104.0 expects

Codex 0.104.0 reads a `prefer_websockets` flag from its own config (not from us). When true, it upgrades all Responses API calls to WebSocket connections instead of HTTP SSE. Our server must therefore handle ALL interaction patterns over WebSocket, not just as a secondary protocol. With `prefer_websockets: true` (which appears to be the default in 0.104.0), a working WebSocket implementation is required for all model calls to succeed.

---

## Current Endpoint Inventory

| Endpoint | Path A (Adapter, port 8317) | Path B (MCP Server, port 3847) |
|---|---|---|
| `GET /v1/models` | Exists, transforms `data`→`models`, enriches metadata | **MISSING** |
| `POST /v1/responses` | Exists, translates to `/v1/chat/completions` | Exists, translates via LiteLLM Router |
| `WS /v1/responses` | Exists (`websocket_responses_handler`) — single-turn, wrong protocol | **MISSING** (registered as `/v1/responses/ws`) |
| `WS /v1/responses/ws` | Not registered | Exists (`handle_responses_websocket`) — wrong path, single-turn |
| `x-models-etag` header | Not returned | Not returned |
| `session_configured` notification | Not sent | Not sent |
| JSON-RPC 2.0 framing | Not implemented | Not implemented |
| `response_id` in responses | Not included | Not included |
| Full SSE event sequence | Partial (`response.output_item.added` only) | Partial (`response.output_item.added` only) |

---

## Priority-Ordered Fix Plan

### P1 — Fix WebSocket to send `session_configured` immediately (stops "reconnecting" loop)

**File:** `src/thegent/cliproxy_adapter.py` — `websocket_responses_handler`
**File:** `src/thegent/routing/litellm_responses_handler.py` — `handle_responses_websocket`

Add immediately after `await websocket.accept()`:
```python
await websocket.send_json(
    {
        "jsonrpc": "2.0",
        "method": "session_configured",
        "params": {
            "model": "",
            "session_id": str(uuid4()),
        },
    }
)
```

This stops the reconnect loop. Codex will wait for the first `response.create` to be handled.

### P2 — Fix WebSocket path in MCP server (stops complete miss for MCP-path clients)

**File:** `src/thegent/mcp/server.py`

Change `/v1/responses/ws` → `/v1/responses` in `add_websocket_route`.

### P3 — Implement JSON-RPC 2.0 dispatch in WebSocket handlers (makes responses work)

Both WebSocket handlers need to parse `frame["method"]` and `frame["id"]` to:
- Dispatch `response.create` to the completion backend.
- Reply with a proper JSON-RPC 2.0 result frame (not just `{"type": "response.completed"}`).
- Include `response_id` in the result for turn linking.

### P4 — Add required fields to HTTP `/v1/responses` response (fixes turn continuity)

**File:** `src/thegent/routing/litellm_responses_handler.py`

Non-streaming response must include `id` (`resp_<uuid>`), `object`, `created_at`, `model`, `status`, and `output[].id` / `output[].status`. The `id` field is the linchpin for `previous_response_id` in multi-turn sessions.

### P5 — Add `/v1/models` to MCP server path (fixes 404 on model discovery)

**File:** `src/thegent/mcp/server.py` — `http_app()`

Add a GET route for `/v1/models` returning `{"models": [...]}` from `MODEL_METADATA`, paralleling what the adapter does.

### P6 — Enrich SSE streaming events to full Responses API event sequence

**File:** `src/thegent/routing/litellm_responses_handler.py`

Replace the single `response.output_item.added` event sequence with: `response.created`, `response.content_part.added`, per-token `response.content_part.delta`, `response.content_part.done`, `response.output_item.done`, and `response.completed` (with full response object including `usage`).

### P7 — Add `x-models-etag` to `/v1/models` responses (performance, not breakage)

Hash the model list content; return as `x-models-etag`. Handle `If-None-Match` with `304 Not Modified`.

### P8 — Emit `model/rerouted` when LiteLLM falls back to a different model

**File:** `src/thegent/routing/litellm_responses_handler.py`

If LiteLLM's router selects a different model than requested, emit a `model/rerouted` JSON-RPC notification on the WebSocket connection.

---

## Minimal Viable Fix (stops breakage, restores basic function)

Implementing P1 + P2 + P3 + P5 will stop the "reconnecting" loop and restore basic single-turn completions. P4 and P6 are required for multi-turn sessions to work correctly. P7 and P8 are polish.

---

## File Map for All Changes

| File | What to change |
|---|---|
| `src/thegent/routing/litellm_responses_handler.py` | `handle_responses_websocket`: add JSON-RPC dispatch + `session_configured`; `handle_responses_request`: add `id`, `object`, `status`, `usage` to response; `_chat_completions_to_responses`: emit full SSE event sequence |
| `src/thegent/cliproxy_adapter.py` | `websocket_responses_handler`: add JSON-RPC dispatch + `session_configured` |
| `src/thegent/mcp/server.py` | Fix WebSocket path (`/ws` suffix → none); add `/v1/models` GET route |
| `src/thegent/routing/model_metadata.py` | Ensure all provider aliases known to CLIProxyAPIPlus are present (prevents "no model metadata" for pass-through aliases) |
