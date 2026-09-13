<DONE>
# OpenRouter API Gap Analysis — 2026-02-20

**Scope:** Full gap analysis between the current thegent proxy stack and what OpenRouter
requires/supports. Based on direct code inspection of `src/thegent/cliproxy_adapter.py`,
supporting routing modules, and authoritative OpenRouter API documentation fetched 2026-02-20.

---

## 1. What the Proxy Currently Is

The proxy is a Starlette ASGI app (`cliproxy_adapter.py`) that:

- Listens on port 8317 (thegent MCP/proxy port)
- Forwards `/v1/*` requests to a backend (CLIProxyAPIPlus on port 8318)
- Translates OpenAI Responses API (`/v1/responses`) → Chat Completions (`/v1/chat/completions`)
  when the backend does not natively support `/v1/responses`
- Enriches the `/v1/models` response with Codex-specific metadata fields
- Bridges WebSocket `/v1/responses` connections to HTTP streaming

It is **not** currently configured to route requests to OpenRouter. OpenRouter is referenced in
`cliproxy_manager.py` as a recognized provider pattern and in `clode_main.py` as a backend for
specific model aliases (e.g. `anthropic/claude-sonnet-4-20250514`), but there is no OpenRouter
authentication injection, no OpenRouter-aware model ID normalization, and no forwarding of
OpenRouter-specific request/response fields anywhere in the proxy stack.

---

## 2. OpenRouter API Reference (2026-02-20)

### 2.1 Base URL and Authentication

| Aspect             | OpenRouter Spec                                         |
| ------------------ | ------------------------------------------------------- |
| Base URL           | `https://openrouter.ai/api/v1`                          |
| Auth header        | `Authorization: Bearer <OPENROUTER_API_KEY>` (required) |
| App identification | `HTTP-Referer: <your-app-url>` (optional, for rankings) |
| App name           | `X-Title: <your-app-name>` (optional, for rankings)     |
| Content-Type       | `application/json` (required on POST)                   |

### 2.2 Endpoints

| Endpoint                     | Method | Purpose                                              |
| ---------------------------- | ------ | ---------------------------------------------------- |
| `/api/v1/chat/completions`   | POST   | Primary chat completion (OpenAI-compatible)          |
| `/api/v1/responses`          | POST   | Responses API Beta (OpenAI Responses API-compatible) |
| `/api/v1/models`             | GET    | List available models                                |
| `/api/v1/generation?id=<id>` | GET    | Query generation stats by ID (token counts, cost)    |

### 2.3 `/api/v1/chat/completions` Request Schema

**Standard OpenAI-compatible fields (all optional unless noted):**

| Field                                  | Type             | Notes                                                                                          |
| -------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| `messages`                             | array            | Required. Conversation history.                                                                |
| `model`                                | string           | Required. Use `provider/model-name` format e.g. `openai/gpt-4o`, `anthropic/claude-3.5-sonnet` |
| `stream`                               | boolean          | SSE streaming. Default false.                                                                  |
| `temperature`                          | float 0-2        | Default 1.0                                                                                    |
| `top_p`                                | float 0-1        | Default 1.0                                                                                    |
| `max_tokens` / `max_completion_tokens` | integer          | Output length limit                                                                            |
| `stop`                                 | string or array  | Stop sequences                                                                                 |
| `tools`                                | array            | Function calling (OpenAI-compatible shape)                                                     |
| `tool_choice`                          | string or object | none / auto / required / named function                                                        |
| `parallel_tool_calls`                  | boolean          | Default true                                                                                   |
| `response_format`                      | object           | `text`, `json_object`, `json_schema`, `grammar`, `python`                                      |
| `seed`                                 | integer          | Reproducible sampling                                                                          |
| `frequency_penalty`                    | float -2 to 2    |                                                                                                |
| `presence_penalty`                     | float -2 to 2    |                                                                                                |
| `logit_bias`                           | map              | Token ID to bias (-100 to 100)                                                                 |
| `logprobs`                             | boolean          |                                                                                                |
| `top_logprobs`                         | integer 0-20     | Requires `logprobs: true`                                                                      |
| `stream_options`                       | object           | `include_usage: bool`                                                                          |
| `user`                                 | string           | End-user identifier                                                                            |

**OpenRouter-specific fields (not present in base OpenAI spec):**

| Field                | Type      | Purpose                                                                    |
| -------------------- | --------- | -------------------------------------------------------------------------- |
| `models`             | string[]  | Multi-model routing — try in order                                         |
| `provider`           | object    | Provider routing config (see §2.4)                                         |
| `route`              | string    | `"fallback"` — shorthand for fallback routing                              |
| `plugins`            | array     | `auto-router`, `moderation`, `web`, `file-parser`, `response-healing`      |
| `reasoning`          | object    | Effort + summary verbosity settings                                        |
| `repetition_penalty` | float 0-2 | Non-OpenAI sampling parameter (forwarded to compatible models)             |
| `min_p`              | float 0-1 | Non-OpenAI sampling parameter                                              |
| `top_a`              | float 0-1 | Non-OpenAI sampling parameter                                              |
| `top_k`              | integer   | Non-OpenAI sampling parameter                                              |
| `structured_outputs` | boolean   | JSON schema strict mode                                                    |
| `session_id`         | string    | Request grouping (max 128 chars)                                           |
| `trace`              | object    | `trace_id`, `trace_name`, `span_name`, `generation_name`, `parent_span_id` |
| `metadata`           | object    | Custom key-value string pairs                                              |
| `debug`              | object    | `echo_upstream_body: bool` for debugging upstream body                     |
| `image_config`       | object    | Image generation config                                                    |
| `modalities`         | string[]  | Output types: `text`, `image`                                              |
| `verbosity`          | enum      | `low`, `medium`, `high`, `max`                                             |
| `prediction`         | object    | Predicted output for latency optimization                                  |

### 2.4 Provider Routing Object Schema

```json
{
  "provider": {
    "order": ["Anthropic", "AWS Bedrock"],
    "allow_fallbacks": true,
    "only": ["Anthropic"],
    "ignore": ["Together"],
    "sort": "price",
    "require_parameters": false,
    "data_collection": "allow",
    "zdr": false,
    "quantizations": ["fp16", "bf16"],
    "preferred_min_throughput": 100,
    "preferred_max_latency": 500,
    "max_price": { "prompt": "0.000001", "completion": "0.000002" }
  }
}
```

### 2.5 Model ID Format

OpenRouter model IDs follow `provider/model-name` format:

- `openai/gpt-4o`
- `anthropic/claude-3.5-sonnet`
- `google/gemini-2.0-flash-001`
- `meta-llama/llama-3.1-70b-instruct`
- `deepseek/deepseek-chat`
- `openai/gpt-4o:nitro` (`:nitro` suffix = fastest throughput)
- `openai/gpt-4o:floor` (`:floor` suffix = cheapest price)

### 2.6 `/api/v1/models` Response Schema

```json
{
  "data": [
    {
      "id": "google/gemini-2.0-flash-lite-001",
      "canonical_slug": "google/gemini-2.0-flash-lite-001",
      "name": "Google: Gemini 2.0 Flash Lite",
      "created": 1740506212,
      "description": "...",
      "hugging_face_id": null,
      "context_length": 1048576,
      "architecture": {
        "tokenizer": "Gemini",
        "instruct_type": null,
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"]
      },
      "pricing": {
        "prompt": "0.000000075",
        "completion": "0.0000003",
        "image": "0",
        "request": "0",
        "input_cache_read": "0",
        "input_cache_write": "0",
        "web_search": "0",
        "internal_reasoning": "0"
      },
      "top_provider": {
        "context_length": 1048576,
        "max_completion_tokens": 8192,
        "is_moderated": false
      },
      "per_request_limits": null,
      "supported_parameters": [
        "temperature",
        "top_p",
        "top_k",
        "max_tokens",
        "tools",
        "json_mode",
        "structured_outputs",
        "reasoning"
      ],
      "default_parameters": {
        "temperature": null,
        "top_p": null,
        "frequency_penalty": null
      },
      "expiration_date": null
    }
  ]
}
```

Key schema points vs OpenAI `/v1/models`:

- OpenRouter wraps in `"data"` array (same as OpenAI), NOT `"models"` key (Codex format)
- OpenRouter model objects have 14+ fields vs OpenAI's 4 (`id`, `object`, `created`, `owned_by`)
- OpenRouter adds: `pricing`, `architecture`, `top_provider`, `per_request_limits`, `supported_parameters`, `canonical_slug`, `hugging_face_id`, `default_parameters`, `expiration_date`
- OpenRouter does NOT include `object`, `owned_by` in model entries
- No `x-models-etag` header is documented for the OpenRouter models endpoint

### 2.7 SSE Streaming Format

OpenRouter SSE is OpenAI-compatible with additions:

```
data: {"id":"cmpl-abc","object":"chat.completion.chunk","created":1234567890,
"model":"openai/gpt-4o","provider":"OpenAI","choices":[{"index":0,
"delta":{"content":"Hello"},"finish_reason":null}]}

: OPENROUTER PROCESSING

data: {"id":"cmpl-abc",...,"choices":[{"index":0,"delta":{},"finish_reason":"stop",
"native_finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}

data: [DONE]
```

Additions vs plain OpenAI SSE:

- `"provider"` field on every chunk (e.g. `"OpenAI"`, `"AWS Bedrock"`)
- `"native_finish_reason"` alongside normalized `"finish_reason"`
- SSE comment lines `": OPENROUTER PROCESSING"` (keep-alive, spec says ignore)
- `finish_reason` normalized to: `tool_calls`, `stop`, `length`, `content_filter`, `error`
- Usage stats in final chunk (not a separate chunk; included in the last content chunk)
- Mid-stream error format (when error occurs after 200 OK is sent):
  ```json
  {
    "id": "...",
    "object": "chat.completion.chunk",
    "created": 1234,
    "model": "...",
    "provider": "...",
    "error": { "code": "server_error", "message": "Provider disconnected" },
    "choices": [
      {
        "index": 0,
        "delta": { "content": "" },
        "finish_reason": "error",
        "native_finish_reason": "..."
      }
    ]
  }
  ```

### 2.8 Error Format

```json
{
  "error": {
    "code": 429,
    "message": "Too many requests",
    "metadata": {
      "provider_name": "Anthropic",
      "raw": "upstream error text"
    }
  }
}
```

Error codes:

- `400` Bad Request (invalid params, CORS)
- `401` Unauthorized (invalid/expired API key)
- `402` Payment Required (insufficient credits)
- `403` Forbidden (moderation flag)
- `408` Request Timeout
- `429` Too Many Requests
- `502` Bad Gateway (model unavailable / invalid upstream response)
- `503` Service Unavailable (no provider meets routing requirements)

### 2.9 `/api/v1/responses` (Responses API Beta)

OpenRouter supports OpenAI's Responses API format at `/api/v1/responses` (beta as of 2026-02-20).

Key differences from the Codex-targeting responses format the proxy currently implements:

- **Endpoint**: `POST /api/v1/responses` (not `/v1/responses`)
- `input` accepts: plain string OR array of message objects with `type: "message"`
- `max_output_tokens` (not `max_tokens`) for output length control
- `instructions` field: system-level guidance (replaces system message)
- Streaming response object emits: `response.created`, `response.output_item.added`,
  `response.content_part.added`, `response.output_text.delta`, `response.output_text.done`,
  `response.content_part.done`, `response.output_item.done`, `response.completed`
- Non-streaming response: `{"id":..., "object":"response", "status":"completed",
"output":[...], "output_text":"...", "usage":{...}}`
- Supports `text.format` for structured output (instead of `response_format`)
- Supports `reasoning` object for thinking models
- Supports full `provider` routing object (same as chat completions)
- Supports `tools` and `tool_choice` for function calling
- Status: **Beta — may have breaking changes**

---

## 3. Gap Analysis Table

| Feature                                             | OpenRouter Spec                                                                                                                                                                                                                                                  | Current Proxy                                                                                                                                                                                                                                                                                                                                   | Gap / Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Authentication**                                  | `Authorization: Bearer <OPENROUTER_API_KEY>` injected at request time                                                                                                                                                                                            | Proxy passes through headers unchanged from client request. `cliproxy_manager.py` has `"openrouter"` provider entry but only injects keys into CLIProxy YAML config, not into outgoing HTTP headers when routing directly to OpenRouter.                                                                                                        | **GAP (P0):** No automatic Bearer token injection for OpenRouter backend. Clients must supply the key themselves, or a new middleware layer must inject `OPENROUTER_API_KEY` from environment.                                                                                                                                                                                                                                                                                                                                                               |
| **`HTTP-Referer` / `X-Title` headers**              | Optional; sent to OpenRouter for app ranking                                                                                                                                                                                                                     | Not added anywhere                                                                                                                                                                                                                                                                                                                              | **GAP (P2):** Nice-to-have for analytics. Low effort to add via a header injection middleware.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Base URL routing**                                | `https://openrouter.ai/api/v1`                                                                                                                                                                                                                                   | Backend URL is `http://127.0.0.1:8318/v1` (CLIProxyAPIPlus local). When `CLIPROXY_API` path is selected, routes to port 8317 (proxy itself). No path routes to `openrouter.ai`.                                                                                                                                                                 | **GAP (P0):** The proxy has no configuration or code path that routes requests to `https://openrouter.ai/api/v1`. OpenRouter must be added as a recognized backend target.                                                                                                                                                                                                                                                                                                                                                                                   |
| **Model ID format**                                 | `provider/model-name` (e.g. `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`)                                                                                                                                                                                      | `harness_model_mapping.py` only maps Codex/MiniMax/GLM/Kilo/Roo aliases. `model_metadata.py` has no `openai/gpt-4o` style OpenRouter IDs. The proxy passes model IDs through unchanged.                                                                                                                                                         | **GAP (P0):** No mapping from thegent-internal model IDs to OpenRouter `provider/model-name` format. Requests using thegent catalog names (`claude-sonnet-4.5`, `gemini-3-flash`) will fail at OpenRouter because those are not valid OpenRouter model IDs.                                                                                                                                                                                                                                                                                                  |
| **`/v1/chat/completions` proxying**                 | Full OpenAI-compatible + OpenRouter extensions                                                                                                                                                                                                                   | Proxy correctly forwards POST `/v1/chat/completions` to backend via `_proxy_request` / `_proxy_stream`. Streaming SSE is handled.                                                                                                                                                                                                               | **PARTIAL:** Core proxying works. Missing: does not inject OpenRouter-specific fields (`provider` routing object, `plugins`, `trace`, `session_id`), and does not forward `native_finish_reason` from OpenRouter responses back to clients.                                                                                                                                                                                                                                                                                                                  |
| **`/v1/models` response format**                    | `{"data": [...]}` with 14-field model objects per model                                                                                                                                                                                                          | Proxy returns Codex-format `{"models": [...], "fetched_at": "...", "client_version": "..."}` with Codex-specific enrichment (`slug`, `shell_type`, `supported_reasoning_levels`, etc.). This is incompatible with what OpenRouter clients expect.                                                                                               | **GAP (P0 when acting as OpenRouter):** If thegent proxy is supposed to look like OpenRouter to downstream clients (e.g. Claude Code configured to use OpenRouter), the `/v1/models` response format is entirely wrong — OpenRouter uses `"data"` key, OpenAI model fields, `pricing`, `architecture`, etc. The current enrichment is Codex-specific and would need a separate transform path for OpenRouter-compatible clients.                                                                                                                             |
| **OpenRouter model object fields**                  | `id`, `canonical_slug`, `name`, `created`, `description`, `context_length`, `architecture`, `pricing`, `top_provider`, `per_request_limits`, `supported_parameters`, `default_parameters`, `hugging_face_id`, `expiration_date`                                  | Current model enrichment adds Codex fields: `slug`, `display_name`, `shell_type`, `visibility`, `supported_in_api`, `supported_reasoning_levels`, `prefer_websockets`, `apply_patch_tool_type`, etc. None of the OpenRouter-specific fields (`pricing`, `architecture.input_modalities`, `top_provider`, `supported_parameters`) are populated. | **GAP (P1):** If proxying to OpenRouter as a backend and re-serving its model list, the proxy must either pass through OpenRouter's native model objects unchanged or translate them. Currently it overwrites them with Codex metadata.                                                                                                                                                                                                                                                                                                                      |
| **SSE streaming — `provider` field**                | Each chunk includes `"provider": "OpenAI"` (or whichever)                                                                                                                                                                                                        | `_proxy_stream` passes SSE chunks through verbatim (no transformation). If OpenRouter is the backend, `provider` field will be in the response. Proxy does not strip or forward this.                                                                                                                                                           | **OK (pass-through):** When proxying OpenRouter backend, the `provider` field will flow through unchanged. No action needed unless the proxy needs to filter it.                                                                                                                                                                                                                                                                                                                                                                                             |
| **SSE streaming — `native_finish_reason`**          | OpenRouter adds `native_finish_reason` alongside normalized `finish_reason`                                                                                                                                                                                      | Proxy passes SSE chunks through when not in `transform_responses` mode.                                                                                                                                                                                                                                                                         | **OK (pass-through):** Flows through unchanged.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **SSE comment lines (`: OPENROUTER PROCESSING`)**   | Keep-alive comments that SSE clients should ignore                                                                                                                                                                                                               | `_proxy_stream` iterates by `\n`, so it will emit these lines. The `_process_sse_line` function only acts on lines starting with `data:` and passes others through.                                                                                                                                                                             | **OK:** Comment lines are passed through correctly.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **OpenRouter-specific request fields**              | `provider`, `models` (array), `route`, `plugins`, `reasoning`, `trace`, `session_id`, `metadata`, `debug`, `structured_outputs`, `repetition_penalty`, `min_p`, `top_a`, `top_k`                                                                                 | Not forwarded, not parsed, not injected                                                                                                                                                                                                                                                                                                         | **GAP (P1):** The `provider` routing object is the most important missing feature. It enables per-request provider selection, fallback chains, data-collection policies, and cost controls. `plugins` (web search, response healing) are also not forwarded. These fields must be forwarded as-is to OpenRouter in the request body.                                                                                                                                                                                                                         |
| **`/v1/responses` endpoint**                        | OpenRouter supports `/api/v1/responses` (Responses API Beta) at its own domain                                                                                                                                                                                   | Proxy implements `/v1/responses` as a translation layer: it converts Responses API format to Chat Completions and back. It was built for Codex CLI compatibility (8-event sequence), not for acting as an OpenRouter-compatible Responses endpoint.                                                                                             | **PARTIAL:** The proxy's `/v1/responses` translation would allow harnesses using the Responses API format to reach OpenRouter via chat completions. However, the proxy does not route to `openrouter.ai/api/v1/responses` directly. If the goal is to expose an OpenRouter-compatible Responses API, the non-streaming response format is wrong (proxy returns `{"output":[...]}`, OpenRouter returns `{"id":...,"object":"response","status":"completed","output":[...],"output_text":"...","usage":{"input_tokens":...,"output_tokens":...,"cost":...}}`). |
| **`/v1/responses` streaming event sequence**        | OpenRouter Responses API Beta emits: `response.created`, `response.output_item.added`, `response.content_part.added`, `response.output_text.delta`, `response.output_text.done`, `response.content_part.done`, `response.output_item.done`, `response.completed` | `_ResponsesStreamState` in `cliproxy_adapter.py` already emits this exact 8-event sequence. The `litellm_responses_handler.py` emits a simplified 2-type sequence (`response.output_item.added` per chunk + `response.completed`).                                                                                                              | **PARTIAL:** The `cliproxy_adapter.py` path emits the correct 8-event sequence (compatible with Codex 0.104.0 and likely OpenRouter Responses API). The LiteLLM handler path (`litellm_responses_handler.py`) emits a non-conformant simplified sequence.                                                                                                                                                                                                                                                                                                    |
| **Tool call streaming**                             | OpenRouter emits `delta.tool_calls` chunks with `index`, `id`, `type`, `function.name`, `function.arguments` — identical to OpenAI                                                                                                                               | `_extract_delta_content` only extracts `delta.content`. Tool call deltas in `delta.tool_calls` are silently dropped when in `transform_responses` mode.                                                                                                                                                                                         | **GAP (P1):** Tool call streaming is broken in the responses-translation path. A client sending tool-using prompts through the proxy's `/v1/responses` endpoint will not receive tool call events. The pass-through path (non-transform mode) works fine.                                                                                                                                                                                                                                                                                                    |
| **Error format**                                    | `{"error": {"code": int, "message": str, "metadata": {...}}}`                                                                                                                                                                                                    | `cliproxy_adapter.py` emits `{"error": {"message": "..."}}` (no `code`, no `metadata`). `litellm_responses_handler.py` emits `{"error": {"message": "...", "type": "ExceptionClassName"}}` (no `code`, no `metadata`).                                                                                                                          | **GAP (P1):** The proxy error format does not include `code` (integer HTTP status) and `metadata` (provider details) that OpenRouter clients may parse.                                                                                                                                                                                                                                                                                                                                                                                                      |
| **402 Payment Required**                            | Returned when account has insufficient credits                                                                                                                                                                                                                   | Not handled or documented in proxy error mapping                                                                                                                                                                                                                                                                                                | **GAP (P2):** The LiteLLM router's `_ERROR_STATUS_MAP` does not include 402. If OpenRouter returns 402, it will be treated as a generic 500 by `litellm_responses_handler.py`.                                                                                                                                                                                                                                                                                                                                                                               |
| **503 Service Unavailable**                         | Returned when no provider meets routing requirements                                                                                                                                                                                                             | Not in proxy error mapping                                                                                                                                                                                                                                                                                                                      | **GAP (P2):** Same issue as 402.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **Rate limiting (429) / Retry-After**               | OpenRouter returns 429 with rate limit info. Free models: 20 req/min, 200 req/day.                                                                                                                                                                               | `litellm_responses_handler.py` maps 429-containing error messages to HTTP 429. Proxy does not read or forward `Retry-After` headers.                                                                                                                                                                                                            | **PARTIAL:** 429 detection works via substring match. `Retry-After` header not forwarded.                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **`/api/v1/generation?id=` stats endpoint**         | Returns token counts and cost after generation                                                                                                                                                                                                                   | Not implemented or proxied                                                                                                                                                                                                                                                                                                                      | **GAP (P2):** Not critical for basic operation but useful for auditing costs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **CORS handling**                                   | OpenRouter returns CORS headers                                                                                                                                                                                                                                  | Proxy routes pass through response headers except `transfer-encoding` and `connection`                                                                                                                                                                                                                                                          | **OK (pass-through):** CORS headers from OpenRouter will flow through.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Streaming error mid-stream**                      | OpenRouter sends error as SSE event with `finish_reason: "error"` in choices                                                                                                                                                                                     | `_proxy_stream` emits a raw `data: {"error":{"message":"Backend {status}"}}` line. This differs from the OpenRouter-spec mid-stream error format.                                                                                                                                                                                               | **GAP (P2):** Non-conformant mid-stream error format. The OpenRouter spec requires the error be at the top level of a full chunk object alongside `choices[0].finish_reason: "error"`.                                                                                                                                                                                                                                                                                                                                                                       |
| **OpenRouter model ID in `model_metadata.py`**      | Needs `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`, etc.                                                                                                                                                                                                       | `model_metadata.py` has no OpenRouter-format model IDs                                                                                                                                                                                                                                                                                          | **GAP (P0):** Without metadata for OpenRouter model IDs, the Codex enrichment path will always use `ctx=128000` default for any OpenRouter model.                                                                                                                                                                                                                                                                                                                                                                                                            |
| **`harness_model_mapping.py` — OpenRouter aliases** | OpenRouter model IDs are canonical; no alias needed for direct OpenRouter models                                                                                                                                                                                 | No OpenRouter entries                                                                                                                                                                                                                                                                                                                           | **GAP (P0 for reverse direction):** If thegent catalog names (e.g. `claude-sonnet-4.5`) must be mapped to OpenRouter IDs (e.g. `anthropic/claude-3.5-sonnet`), a new mapping section is required.                                                                                                                                                                                                                                                                                                                                                            |
| **`provider_types.py` — OpenRouter classification** | Should be `LITELLM_API` (API key provider)                                                                                                                                                                                                                       | `"openrouter"` is not in `API_KEY_PROVIDERS`, `LOGIN_AUTH_PROVIDERS`, or `NATIVE_CLI_PROVIDERS`. It falls through to `CLIPROXY_API`, which routes it to the local CLIProxy port — incorrect.                                                                                                                                                    | **GAP (P0):** `"openrouter"` must be added to `API_KEY_PROVIDERS` and `_get_api_key_env()` must return `"OPENROUTER_API_KEY"`.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **`litellm_router.py` — OpenRouter config**         | LiteLLM supports OpenRouter via `openrouter/<model>` provider string                                                                                                                                                                                             | No OpenRouter entry in `_get_api_key_env()`. No OpenRouter models in `build_litellm_model_list()`.                                                                                                                                                                                                                                              | **GAP (P0):** LiteLLM cannot route to OpenRouter without `api_key=OPENROUTER_API_KEY` and `api_base=https://openrouter.ai/api/v1`.                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **`/v1/models` — query parameters**                 | `?category=`, `?supported_parameters=` filtering                                                                                                                                                                                                                 | Not parsed or forwarded                                                                                                                                                                                                                                                                                                                         | **GAP (P2):** Minor. Query parameters are forwarded as-is to backend via `request.url.query` in `_proxy_request`, so if OpenRouter is the backend, they flow through naturally. No issue.                                                                                                                                                                                                                                                                                                                                                                    |
| **WebSocket `/v1/responses` — multi-turn**          | Not part of OpenRouter spec; OpenRouter Responses API is HTTP-only                                                                                                                                                                                               | Proxy implements persistent WebSocket bridge for Codex compatibility                                                                                                                                                                                                                                                                            | **OK:** WebSocket support is a thegent-specific feature for Codex clients. OpenRouter clients use HTTP. No conflict.                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **`x-models-etag` response header**                 | Not part of OpenRouter spec; this is a Codex-specific header                                                                                                                                                                                                     | Proxy adds `x-models-etag` when enriching model responses (SHA256 of model IDs)                                                                                                                                                                                                                                                                 | **OK:** This Codex-specific header does not conflict with OpenRouter usage.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **TLS / HTTPS**                                     | OpenRouter requires HTTPS (`https://openrouter.ai/api/v1`)                                                                                                                                                                                                       | `_proxy_request` uses `httpx.AsyncClient(verify=False)` for local backend. `_proxy_stream` uses default (verify=True).                                                                                                                                                                                                                          | **GAP (P1):** The `_proxy_request` function disables TLS verification (`verify=False`). This is acceptable for localhost CLIProxy but must NOT be used when the backend is OpenRouter. A new client configuration path is needed for remote HTTPS backends.                                                                                                                                                                                                                                                                                                  |

---

## 4. Findings Summary

### 4.1 What the Proxy Currently Handles Correctly for OpenRouter

1. **SSE streaming pass-through** — When the backend is OpenRouter and the proxy is in
   non-transform mode (direct `/v1/chat/completions` proxying), SSE chunks including
   `provider`, `native_finish_reason`, and comment lines all pass through correctly.

2. **Header pass-through** — All request headers from the client (including a pre-supplied
   `Authorization` header) are forwarded to the backend.

3. **CORS headers** — Response headers from OpenRouter flow back to the client.

4. **Query parameter forwarding** — URL query parameters (for model filtering) are forwarded.

5. **`_ResponsesStreamState` 8-event sequence** — The Codex-targeting
   `_ResponsesStreamState` in `cliproxy_adapter.py` emits the same event sequence that
   OpenRouter Responses API Beta also emits.

6. **Error substring detection** — `_ERROR_STATUS_MAP` correctly maps `rate_limit`,
   `authentication`, `invalid_model`, and `context_length_exceeded` to correct HTTP codes.

### 4.2 What the Proxy Is Missing That OpenRouter Requires

**P0 — Breaks basic OpenRouter compatibility:**

1. **No OpenRouter backend routing** — No code path routes to `https://openrouter.ai/api/v1`.
   OpenRouter must be added as a backend target with proper URL configuration.

2. **No automatic `Authorization` header injection** — If the client does not supply the key,
   requests to OpenRouter will be rejected with 401. The proxy must inject
   `OPENROUTER_API_KEY` from environment when OpenRouter is the selected backend.

3. **Model ID translation missing** — thegent catalog IDs (`claude-sonnet-4.5`,
   `gemini-3-flash`) are not valid OpenRouter model IDs (`anthropic/claude-3.5-sonnet`,
   `google/gemini-2.0-flash-001`). `harness_model_mapping.py` needs OpenRouter entries.

4. **`provider_types.py` miscategorization** — `"openrouter"` falls through to
   `CLIPROXY_API` path (local port 8317), not LiteLLM direct API path. Must be added to
   `API_KEY_PROVIDERS`.

5. **`litellm_router.py` missing OpenRouter config** — `_get_api_key_env()` has no
   `"openrouter"` entry; `build_litellm_model_list()` generates no OpenRouter routes.

6. **`model_metadata.py` missing OpenRouter model IDs** — Models in `openai/gpt-4o` format
   are not in the registry, so context window enrichment falls back to 128000 default.

**P1 — Functional gaps for production use:**

7. **OpenRouter-specific request fields not forwarded** — `provider` routing object, `plugins`,
   `models` array, `route`, `trace`, `session_id`, `metadata`, `reasoning` are not parsed or
   injected. Most pass through when the proxy forwards the raw body, but are lost in
   `transform_responses` mode where the body is reconstructed from a subset of fields.

8. **Tool call streaming broken in transform mode** — `_extract_delta_content` only reads
   `delta.content`; `delta.tool_calls` is silently dropped. This affects any prompt that
   invokes tools through the `/v1/responses` translation path.

9. **Non-conformant error format** — Missing `code` (integer) and `metadata` (provider info)
   fields that OpenRouter clients may expect in error bodies.

10. **TLS verification disabled for all backends** — `_proxy_request` uses `verify=False`,
    which must not be used when forwarding to HTTPS OpenRouter endpoint.

11. **`/v1/models` response format mismatch** — The current Codex-enriched format
    (`{"models": [...], "fetched_at": "...", "client_version": "..."}`) is incompatible with
    what OpenRouter clients (or OpenRouter-format-aware SDKs) expect
    (`{"data": [...]}` with pricing, architecture, supported_parameters).

**P2 — Nice-to-have / minor gaps:**

12. **Missing 402, 503 error code handling** — Payment required and no-provider-available
    errors not in `_ERROR_STATUS_MAP`.

13. **`HTTP-Referer` / `X-Title` headers** — Not injected. Minor analytics/ranking loss.

14. **`/api/v1/generation` stats endpoint** — Not proxied. Useful for cost auditing.

15. **`Retry-After` header not forwarded** — 429 responses should include retry delay.

16. **Mid-stream error format** — Does not match the OpenRouter SSE error spec
    (missing `choices[0].finish_reason: "error"` and chunk object wrapper).

### 4.3 OpenRouter `/v1/responses` — Does It Use the Responses API v2?

**Yes.** OpenRouter supports OpenAI's Responses API v2 format at `POST /api/v1/responses`
(currently in Beta). The endpoint:

- Accepts `input` (string or message array), `model`, `stream`, `tools`, `instructions`,
  `max_output_tokens`, `reasoning`, `text.format`, and the full `provider` routing object.
- Returns a `response` object with `id`, `object: "response"`, `status`, `output`, `output_text`,
  `usage.input_tokens`, `usage.output_tokens`, `usage.cost`.
- Streaming emits the same 8-event sequence that the proxy's `_ResponsesStreamState` already
  implements.

**The proxy does NOT currently forward to OpenRouter's Responses API endpoint.** It translates
Responses API input to chat completions internally and routes that to the local CLIProxy backend.
To route Responses API requests to OpenRouter natively, the proxy would need a new code path that
forwards the original Responses API body (not the translated chat completions body) to
`https://openrouter.ai/api/v1/responses`.

---

## 5. Recommended Fix Priority

### P0 — Required for basic OpenRouter compatibility

| Task                                                                                                      | File(s) to Modify                                         |
| --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Add `"openrouter"` to `API_KEY_PROVIDERS`                                                                 | `routing/provider_types.py`                               |
| Add `"openrouter": "OPENROUTER_API_KEY"` to `_get_api_key_env()`                                          | `routing/litellm_router.py`                               |
| Add OpenRouter model entries to `build_litellm_model_list()` with `api_base=https://openrouter.ai/api/v1` | `routing/litellm_router.py`                               |
| Add OpenRouter → thegent model ID mappings                                                                | `routing/harness_model_mapping.py`                        |
| Add representative OpenRouter model IDs to `model_metadata.py`                                            | `routing/model_metadata.py`                               |
| Add `Authorization: Bearer` injection when backend is OpenRouter                                          | `cliproxy_adapter.py` or new middleware                   |
| Fix TLS: use `verify=True` for HTTPS backends                                                             | `cliproxy_adapter.py` (`_proxy_request`, `_proxy_stream`) |

### P1 — Required for production-quality OpenRouter proxying

| Task                                                             | File(s) to Modify                                                               |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Forward OpenRouter-specific fields through transform path        | `cliproxy_adapter.py` `_responses_to_chat_completions`                          |
| Fix tool call delta extraction in streaming transform            | `cliproxy_adapter.py` `_extract_delta_content` → extract `delta.tool_calls` too |
| Add `code` and `metadata` to error responses                     | `litellm_responses_handler.py`, `cliproxy_adapter.py`                           |
| Add conditional `/v1/models` format (Codex vs OpenRouter client) | `cliproxy_adapter.py` `_transform_models_response`                              |
| Add OpenRouter-native model fields to enrichment                 | `cliproxy_adapter.py` `_transform_models_response`                              |

### P2 — Polish and completeness

| Task                                                           | File(s) to Modify                                 |
| -------------------------------------------------------------- | ------------------------------------------------- |
| Add 402, 503 to `_ERROR_STATUS_MAP`                            | `litellm_responses_handler.py`                    |
| Forward `Retry-After` header on 429                            | `cliproxy_adapter.py` `_proxy_request`            |
| Inject `HTTP-Referer` and `X-Title` when routing to OpenRouter | `cliproxy_adapter.py` or middleware               |
| Add `/api/v1/generation` proxy endpoint                        | `cliproxy_adapter.py` routing table               |
| Fix mid-stream error SSE format                                | `cliproxy_adapter.py` `_proxy_stream` error yield |

---

## 6. Open Questions

1. **Client mode vs. provider mode** — Is the goal to use OpenRouter as a _backend_ for the
   proxy (routing outgoing requests to OpenRouter), or to make the proxy _look like_ OpenRouter
   to downstream clients (expose the OpenRouter API surface)? These require different changes.
   The gap analysis above assumes **both**: OpenRouter as a backend (P0 fixes) and optional
   OpenRouter-compatible response format (P1 fixes).

2. **Model ID namespace collision** — `anthropic/claude-3.5-sonnet` (OpenRouter format) and
   `claude-sonnet-4.5` (thegent catalog format) refer to similar but not identical models.
   A mapping strategy is needed: should the proxy normalize all IDs to OpenRouter format before
   forwarding, or should it maintain a separate lookup for each backend type?

3. **Codex + OpenRouter simultaneously** — Codex CLI requires the Codex-format `/v1/models`
   response (`"models"` key, Codex metadata schema). If OpenRouter is used as the model
   backend while Codex is the harness client, the proxy must re-serialize OpenRouter's model
   objects into Codex format. This is currently done generically, but OpenRouter model IDs
   (`openai/gpt-4o`) will not match thegent's internal metadata unless explicitly mapped.

4. **Free vs. paid OpenRouter tier** — Free models (`:free` suffix, 20 req/min) vs paid
   models have different rate limits and behaviors. Should the proxy tier-manage these
   differently?

---

## Sources

- OpenRouter API Reference Overview: https://openrouter.ai/docs/api/reference/overview
- OpenRouter Chat Completions: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
- OpenRouter Models List: https://openrouter.ai/docs/api/api-reference/models/get-models
- OpenRouter Provider Routing: https://openrouter.ai/docs/guides/routing/provider-selection
- OpenRouter Responses API Beta: https://openrouter.ai/docs/api/reference/responses/overview
- OpenRouter Error Handling: https://openrouter.ai/docs/api/reference/errors-and-debugging
- OpenRouter Streaming: https://openrouter.ai/docs/api/reference/streaming
- OpenRouter Parameters: https://openrouter.ai/docs/api/reference/parameters
- OpenRouter Rate Limits: https://openrouter.ai/docs/api/reference/limits
