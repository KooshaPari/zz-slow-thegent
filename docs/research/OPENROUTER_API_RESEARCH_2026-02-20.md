<DONE>
# OpenRouter API Exhaustive Research

**Date:** 2026-02-20
**Researcher:** Claude Code (claude-sonnet-4-6)
**Sources:** openrouter.ai/docs, live API endpoints, web research

---

## Table of Contents

1. [Overview and Base URL](#1-overview-and-base-url)
2. [Authentication](#2-authentication)
3. [Model IDs and Variants](#3-model-ids-and-variants)
4. [Endpoints Reference](#4-endpoints-reference)
5. [Chat Completions - Full Request Schema](#5-chat-completions---full-request-schema)
6. [Chat Completions - Full Response Schema](#6-chat-completions---full-response-schema)
7. [Streaming (SSE)](#7-streaming-sse)
8. [Provider Routing](#8-provider-routing)
9. [Tool and Function Calling](#9-tool-and-function-calling)
10. [Structured Outputs](#10-structured-outputs)
11. [Prompt Caching](#11-prompt-caching)
12. [Plugins](#12-plugins)
13. [Reasoning / Extended Thinking](#13-reasoning--extended-thinking)
14. [Multimodal Inputs](#14-multimodal-inputs)
15. [Image Generation](#15-image-generation)
16. [Embeddings](#16-embeddings)
17. [Responses API (Beta)](#17-responses-api-beta)
18. [Key Management APIs](#18-key-management-apis)
19. [OAuth PKCE Flow](#19-oauth-pkce-flow)
20. [Credits and Billing APIs](#20-credits-and-billing-apis)
21. [Analytics and Activity Tracking](#21-analytics-and-activity-tracking)
22. [Generation Stats Endpoint](#22-generation-stats-endpoint)
23. [Rate Limits](#23-rate-limits)
24. [Error Codes and Error Response Format](#24-error-codes-and-error-response-format)
25. [Response Headers](#25-response-headers)
26. [Message Transforms](#26-message-transforms)
27. [Presets](#27-presets)
28. [Guardrails and Governance](#28-guardrails-and-governance)
29. [Observability and Broadcast](#29-observability-and-broadcast)
30. [Differences from OpenAI API](#30-differences-from-openai-api)
31. [OpenAPI Specification](#31-openapi-specification)
32. [BYOK (Bring Your Own Key)](#32-byok-bring-your-own-key)

---

## 1. Overview and Base URL

OpenRouter is a unified API gateway providing access to 400+ language models from 60+ providers through a single endpoint. It is designed to be an OpenAI-compatible drop-in replacement, with extensions for provider routing, fallbacks, and multi-model orchestration.

**Base URL:** `https://openrouter.ai/api/v1`

**OpenAI compatibility:** Full compatibility for `/chat/completions` and `/completions`. To use with OpenAI SDK, set:

- `base_url` / `baseURL` to `https://openrouter.ai/api/v1`
- `api_key` / `apiKey` to your OpenRouter API key

**Overhead:** ~25-40ms additional latency over direct provider calls.

**OpenAPI Specifications:**

- YAML: `https://openrouter.ai/openapi.yaml`
- JSON: `https://openrouter.ai/openapi.json`

---

## 2. Authentication

### 2.1 Standard Bearer Token Authentication

All API requests require a Bearer token in the `Authorization` header:

```
Authorization: Bearer sk-or-v1-<your-key-here>
```

**API key format:** Keys begin with `sk-or-v1-`.

### 2.2 Optional Attribution Headers

These headers are optional but allow your app to appear in OpenRouter leaderboards and rankings:

```
HTTP-Referer: https://your-site.com
X-Title: Your App Name
```

### 2.3 Required Headers

```
Content-Type: application/json
Authorization: Bearer <OPENROUTER_API_KEY>
```

### 2.4 Key Types

There are three distinct key types with different permissions:

| Key Type                    | Purpose                                                               | Create Via                     |
| --------------------------- | --------------------------------------------------------------------- | ------------------------------ |
| Regular API Key             | Making completion/inference API calls                                 | openrouter.ai/keys             |
| Management/Provisioning Key | Managing other API keys programmatically; cannot make inference calls | Settings > Management API Keys |
| OAuth-derived Key           | User-authorized key from PKCE flow                                    | OAuth PKCE exchange            |

### 2.5 Security

- OpenRouter is a **GitHub secret scanning partner** — exposed keys are automatically detected
- Compromised keys trigger email notification; rotate immediately via openrouter.ai/keys
- Keys are scoped with credit limits, rate resets, and expiration timestamps

### 2.6 Anthropic Beta Headers

For accessing experimental Anthropic features, pass the `x-anthropic-beta` header with comma-separated feature flags:

```
x-anthropic-beta: fine-grained-tool-streaming-2025-05-14,interleaved-thinking-2025-05-14
x-anthropic-beta: structured-outputs-2025-11-13
```

Note: `structured-outputs-2025-11-13` is required for strict tool use (`strict: true` on tools). Without it, OpenRouter strips the `strict` field and routes normally.

---

## 3. Model IDs and Variants

### 3.1 Model ID Format

OpenRouter model IDs follow the format:

```
{provider}/{model-slug}
```

Examples:

- `openai/gpt-4o`
- `anthropic/claude-3.5-sonnet`
- `google/gemini-2.5-pro`
- `meta-llama/llama-3.3-70b-instruct`
- `deepseek/deepseek-r1`
- `mistralai/mistral-7b-instruct`

This differs from OpenAI model IDs which have no provider prefix (e.g., `gpt-4o` vs `openai/gpt-4o`).

### 3.2 Model Variants (Suffixes)

Append suffixes to any model ID to change routing behavior:

**Static Variants** (select a specific model version):

| Suffix      | Behavior                                         |
| ----------- | ------------------------------------------------ |
| `:free`     | Use the free-tier version; low rate limits       |
| `:extended` | Extended context window / output length          |
| `:thinking` | Reasoning-enabled variant (for supported models) |
| `:exacto`   | OpenRouter-curated high-quality endpoints only   |

**Dynamic Variants** (change routing behavior for any model):

| Suffix    | Behavior                                                    |
| --------- | ----------------------------------------------------------- |
| `:nitro`  | Route to highest-throughput provider (`sort: "throughput"`) |
| `:floor`  | Route to lowest-cost provider (`sort: "price"`)             |
| `:online` | Inject live web search results into the prompt              |

Example: `anthropic/claude-3.5-sonnet:nitro` routes to the fastest available provider for Claude 3.5 Sonnet.

### 3.3 Special Model IDs

| Model ID                 | Behavior                                                     |
| ------------------------ | ------------------------------------------------------------ |
| `openrouter/auto`        | Auto Router (NotDiamond-powered intelligent model selection) |
| `openrouter/free`        | Free Models Router (selects from free models)                |
| `openrouter/bodybuilder` | Body Builder (generates API requests from natural language)  |

### 3.4 Model Permaslugs

Each model version has a `model_permaslug` — a timestamped, immutable identifier for a specific model version. Use this in the `model_permaslug` field of activity responses to identify exactly which model version served a request.

---

## 4. Endpoints Reference

### 4.1 Complete Endpoint List

| Method | Path                                       | Purpose                             | Auth Required  |
| ------ | ------------------------------------------ | ----------------------------------- | -------------- |
| POST   | `/api/v1/chat/completions`                 | Chat completions (primary)          | API key        |
| POST   | `/api/v1/completions`                      | Legacy text completions             | API key        |
| GET    | `/api/v1/models`                           | List all models                     | API key        |
| GET    | `/api/v1/models/{author}/{slug}/endpoints` | List provider endpoints for a model | API key        |
| GET    | `/api/v1/generation`                       | Get generation stats by ID          | API key        |
| GET    | `/api/v1/activity`                         | User activity analytics (30 days)   | Management key |
| GET    | `/api/v1/key`                              | Get current API key details         | API key        |
| GET    | `/api/v1/credits`                          | Get account credit balance          | Management key |
| POST   | `/api/v1/keys`                             | Create new API key                  | Management key |
| GET    | `/api/v1/keys`                             | List all API keys                   | Management key |
| GET    | `/api/v1/keys/{hash}`                      | Get a single API key                | Management key |
| DELETE | `/api/v1/keys/{hash}`                      | Delete an API key                   | Management key |
| GET    | `/auth`                                    | OAuth PKCE authorization redirect   | None           |
| POST   | `/api/v1/auth/keys`                        | Exchange OAuth code for API key     | None           |
| POST   | `/api/v1/embeddings`                       | Text embeddings                     | API key        |
| POST   | `/api/v1/responses`                        | Responses API (Beta)                | API key        |

---

## 5. Chat Completions - Full Request Schema

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`

### 5.1 Core Fields

```json
{
  "model": "openai/gpt-4o",
  "messages": [...],
  "stream": false
}
```

### 5.2 Message Types

All message types follow this structure, with role-specific variations:

**SystemMessage:**

```json
{
  "role": "system",
  "content": "string | ContentArray",
  "name": "optional string"
}
```

**UserMessage:**

```json
{
  "role": "user",
  "content": "string | ContentArray",
  "name": "optional string"
}
```

**DeveloperMessage:**

```json
{
  "role": "developer",
  "content": "string | ContentArray",
  "name": "optional string"
}
```

**AssistantMessage:**

```json
{
  "role": "assistant",
  "content": "string | ContentArray | null",
  "name": "optional string",
  "tool_calls": [...],
  "refusal": "string",
  "reasoning": "string",
  "reasoning_details": [...],
  "images": [...]
}
```

**ToolResponseMessage:**

```json
{
  "role": "tool",
  "content": "string | ContentArray",
  "tool_call_id": "required string"
}
```

### 5.3 Content Item Types

**Text:**

```json
{
  "type": "text",
  "text": "string",
  "cache_control": { "type": "ephemeral", "ttl": "1h" }
}
```

**Image:**

```json
{
  "type": "image_url",
  "image_url": {
    "url": "https://... or data:image/...",
    "detail": "auto|low|high"
  }
}
```

**Audio:**

```json
{
  "type": "input_audio",
  "input_audio": { "data": "base64string", "format": "wav|mp3|..." }
}
```

**Video:**

```json
{"type": "input_video", "video_url": {"url": "https://..."}}
{"type": "video_url", "video_url": {"url": "https://..."}}
```

### 5.4 Generation Parameters

| Parameter               | Type            | Range               | Default | Description                                                 |
| ----------------------- | --------------- | ------------------- | ------- | ----------------------------------------------------------- |
| `temperature`           | float           | 0.0–2.0             | 1.0     | Randomness/creativity                                       |
| `top_p`                 | float           | 0.0–1.0             | 1.0     | Nucleus sampling threshold                                  |
| `top_k`                 | integer         | 0+                  | 0       | Top-K sampling (0 = disabled)                               |
| `frequency_penalty`     | float           | -2.0–2.0            | 0.0     | Penalize repeated tokens by frequency                       |
| `presence_penalty`      | float           | -2.0–2.0            | 0.0     | Penalize any repeated tokens                                |
| `repetition_penalty`    | float           | 0.0–2.0             | 1.0     | Reduce repetition (alternative to above)                    |
| `min_p`                 | float           | 0.0–1.0             | 0.0     | Minimum token probability relative to top token             |
| `top_a`                 | float           | 0.0–1.0             | 0.0     | Dynamic top-P; tokens must exceed `top_a * p_max^2`         |
| `seed`                  | integer         | any                 | none    | Deterministic sampling seed                                 |
| `max_tokens`            | integer         | 1+                  | none    | Maximum response tokens                                     |
| `max_completion_tokens` | integer         | 1+                  | none    | Alias for max_tokens (OpenAI compat)                        |
| `stop`                  | string/string[] |                     | none    | Stop sequences                                              |
| `logit_bias`            | map             | -100 to 100         | none    | Token ID → bias value                                       |
| `logprobs`              | boolean         |                     | false   | Return log probabilities                                    |
| `top_logprobs`          | integer         | 0–20                | none    | Top N log probability tokens                                |
| `verbosity`             | enum            | low/medium/high/max | medium  | Response verbosity (maps to Anthropic output_config.effort) |

### 5.5 Response Format

```json
{
  "response_format": {"type": "text"},
  "response_format": {"type": "json_object"},
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "schema_name",
      "description": "optional",
      "schema": {...},
      "strict": true
    }
  },
  "response_format": {"type": "grammar", "grammar": "EBNF grammar string"},
  "response_format": {"type": "python"}
}
```

`structured_outputs` (boolean) enables structured outputs where supported.

### 5.6 Streaming Options

```json
{
  "stream": true,
  "stream_options": { "include_usage": true }
}
```

### 5.7 Tools and Function Calling

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": { "type": "string" }
          },
          "required": ["location"]
        },
        "strict": false
      }
    }
  ],
  "tool_choice": "auto",
  "parallel_tool_calls": true
}
```

`tool_choice` options: `"none"` | `"auto"` | `"required"` | `{"type": "function", "function": {"name": "tool_name"}}`

### 5.8 Reasoning / Extended Thinking

```json
{
  "reasoning": {
    "effort": "high",
    "max_tokens": 2000,
    "exclude": false,
    "enabled": true
  }
}
```

Effort levels: `"xhigh"` | `"high"` | `"medium"` | `"low"` | `"minimal"` | `"none"`

Effort ratios applied to `max_tokens`: xhigh=0.95, high=0.80, medium=0.50, low=0.20, minimal=0.10

### 5.9 Provider Routing (full schema)

```json
{
  "provider": {
    "order": ["Anthropic", "Amazon Bedrock"],
    "allow_fallbacks": true,
    "require_parameters": false,
    "data_collection": "allow",
    "zdr": false,
    "enforce_distillable_text": false,
    "only": ["Anthropic"],
    "ignore": ["Together"],
    "quantizations": ["fp8", "fp16"],
    "sort": "price",
    "max_price": {
      "prompt": 1.0,
      "completion": 2.0,
      "request": 0.01,
      "image": 0.05
    },
    "preferred_min_throughput": {
      "p50": 100,
      "p90": 50
    },
    "preferred_max_latency": {
      "p50": 1,
      "p90": 3,
      "p99": 5
    }
  }
}
```

### 5.10 Model Fallbacks

```json
{
  "model": "anthropic/claude-3.5-sonnet",
  "models": [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "google/gemini-2.0-flash"
  ],
  "route": "fallback"
}
```

When using OpenAI SDK, wrap non-standard fields in `extra_body`:

```python
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[...],
    extra_body={"models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o"], "route": "fallback"},
)
```

### 5.11 Plugins

```json
{
  "plugins": [
    {
      "id": "auto-router",
      "enabled": true,
      "allowed_models": ["anthropic/*", "openai/gpt-5*"]
    },
    { "id": "moderation" },
    {
      "id": "web",
      "enabled": true,
      "max_results": 5,
      "search_prompt": "Custom search instructions",
      "engine": "native"
    },
    {
      "id": "file-parser",
      "enabled": true,
      "pdf": { "engine": "mistral-ocr" }
    },
    { "id": "response-healing", "enabled": true }
  ]
}
```

Plugin IDs: `"auto-router"` | `"moderation"` | `"web"` | `"file-parser"` | `"response-healing"`

Web search engine options: `"native"` | `"exa"` | omit for auto (native if available, else exa)

File-parser PDF engine options: `"mistral-ocr"` | `"pdf-text"` | `"native"`

`web_search_options` field (for native web search context sizing):

```json
{
  "web_search_options": { "search_context_size": "low|medium|high" }
}
```

### 5.12 Observability and Tracing

```json
{
  "user": "user_id_or_hash",
  "session_id": "session-abc123",
  "trace": {
    "trace_id": "custom-trace-id",
    "trace_name": "my-trace",
    "span_name": "completion-span",
    "generation_name": "chat-generation",
    "parent_span_id": "parent-span",
    "custom_key": "custom_value"
  },
  "metadata": {
    "environment": "production",
    "version": "1.2.3"
  }
}
```

`session_id`: max 128 characters. `metadata`: max 16 key-value pairs; keys max 64 chars, values max 512 chars.

### 5.13 OpenRouter-Specific Fields

| Field          | Type     | Description                                                                 |
| -------------- | -------- | --------------------------------------------------------------------------- |
| `transforms`   | string[] | Message transformation strategies. `["middle-out"]` or `[]` to disable      |
| `models`       | string[] | Fallback model list in priority order                                       |
| `route`        | string   | `"fallback"` or `"sort"`                                                    |
| `provider`     | object   | Provider routing preferences (see above)                                    |
| `user`         | string   | Stable user identifier for caching and analytics                            |
| `session_id`   | string   | Session identifier for observability                                        |
| `trace`        | object   | Tracing metadata for broadcast destinations                                 |
| `metadata`     | object   | Custom key-value pairs                                                      |
| `prediction`   | object   | `{"type": "content", "content": "predicted text"}` for speculative decoding |
| `debug`        | object   | `{"echo_upstream_body": true}` to debug transformed requests                |
| `reasoning`    | object   | Extended thinking configuration                                             |
| `plugins`      | array    | Plugin configurations                                                       |
| `modalities`   | string[] | Output modalities: `["text"]`, `["image"]`, `["text", "image"]`             |
| `image_config` | object   | Image generation configuration                                              |
| `preset`       | string   | Preset slug to apply saved configuration                                    |

### 5.14 Presets

Three ways to reference a preset:

```json
{"model": "@preset/email-copywriter", "messages": [...]}
{"model": "openai/gpt-4o", "preset": "email-copywriter", "messages": [...]}
{"model": "openai/gpt-4o@preset/email-copywriter", "messages": [...]}
```

### 5.15 Assistant Prefill

Append an incomplete assistant message to steer model completion:

```json
{
  "messages": [
    { "role": "user", "content": "Who are you?" },
    { "role": "assistant", "content": "I am" }
  ]
}
```

### 5.16 Prediction (Speculative Decoding)

```json
{
  "prediction": {
    "type": "content",
    "content": "The expected output text to speed up generation"
  }
}
```

---

## 6. Chat Completions - Full Response Schema

### 6.1 Non-Streaming Response

```json
{
  "id": "gen-abc123def456",
  "object": "chat.completion",
  "created": 1708474800,
  "model": "anthropic/claude-3.5-sonnet",
  "system_fingerprint": "optional-string-or-null",
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "native_finish_reason": "end_turn",
      "message": {
        "role": "assistant",
        "content": "Response text",
        "tool_calls": null,
        "refusal": null,
        "reasoning": "Internal reasoning text",
        "reasoning_details": [...],
        "images": [...],
        "annotations": [...]
      },
      "logprobs": null,
      "error": null
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150,
    "prompt_tokens_details": {
      "cached_tokens": 80,
      "cache_write_tokens": 100,
      "audio_tokens": 0,
      "video_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 20,
      "audio_tokens": 0,
      "accepted_prediction_tokens": 10,
      "rejected_prediction_tokens": 5
    },
    "cost": 0.000150,
    "is_byok": false,
    "cost_details": {
      "upstream_inference_cost": 0.000145,
      "upstream_inference_prompt_cost": 0.000050,
      "upstream_inference_completions_cost": 0.000095
    },
    "server_tool_use": {
      "web_search_requests": 1
    }
  }
}
```

### 6.2 Finish Reasons (Normalized)

OpenRouter normalizes finish reasons to these standard values:

| Finish Reason    | Meaning                             |
| ---------------- | ----------------------------------- |
| `stop`           | Normal completion                   |
| `length`         | Hit max_tokens limit                |
| `tool_calls`     | Model requested tool call           |
| `content_filter` | Content moderation stopped response |
| `error`          | Error during generation             |

The raw provider finish reason is always available in `native_finish_reason`.

### 6.3 Response Model Field

The `model` field in the response reflects the **actual model that handled the request**, which may differ from the requested model when:

- Fallback models were used
- Auto Router selected a different model
- A model variant resolved to a specific endpoint

### 6.4 Tool Call Response

```json
{
  "finish_reason": "tool_calls",
  "message": {
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"San Francisco\"}"
        }
      }
    ]
  }
}
```

### 6.5 Web Search Annotations

When web search plugin is active, `annotations` array is added to the message:

```json
{
  "annotations": [
    {
      "type": "url_citation",
      "url_citation": {
        "url": "https://example.com/article",
        "title": "Article Title",
        "content": "Excerpt from the source",
        "start_index": 100,
        "end_index": 200
      }
    }
  ]
}
```

### 6.6 Reasoning Details Structure

```json
{
  "reasoning_details": [
    {
      "type": "reasoning.text",
      "text": "Raw reasoning text",
      "signature": "optional"
    },
    { "type": "reasoning.summary", "text": "High-level summary" },
    { "type": "reasoning.encrypted", "data": "encrypted_content" }
  ]
}
```

### 6.7 Cache Discount Field

The response may include a `cache_discount` field at the response level indicating cost savings from cache hits. Some providers have negative discounts on cache writes but positive discounts on cache reads.

---

## 7. Streaming (SSE)

### 7.1 Enabling Streaming

Set `"stream": true` in the request body.

### 7.2 SSE Format

Each event is a line prefixed with `data: ` followed by JSON, separated by blank lines:

```
data: {"id":"gen-abc123","object":"chat.completion.chunk","created":1708474800,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}]}

data: {"id":"gen-abc123","object":"chat.completion.chunk","created":1708474800,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}

data: {"id":"gen-abc123","object":"chat.completion.chunk","created":1708474800,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{...}}

data: [DONE]
```

### 7.3 OpenRouter-Specific SSE Comment Payloads

OpenRouter sends SSE comments to prevent connection timeouts. Per the SSE spec, comments start with `:` and must be ignored:

```
: OPENROUTER PROCESSING
```

**Important:** Some SSE client implementations that do not follow the SSE spec may throw errors on comment payloads when attempting `JSON.parse()`. Use compliant SSE clients.

### 7.4 Streaming Chunk Schema

```json
{
  "id": "gen-abc123",
  "object": "chat.completion.chunk",
  "created": 1708474800,
  "model": "openai/gpt-4o",
  "choices": [
    {
      "index": 0,
      "delta": {
        "role": "assistant",
        "content": "text chunk",
        "tool_calls": [...],
        "reasoning": "reasoning chunk"
      },
      "finish_reason": null,
      "native_finish_reason": null,
      "error": null
    }
  ],
  "usage": null
}
```

Usage is included in the final chunk (before `[DONE]`).

### 7.5 Mid-Stream Errors

If an error occurs after tokens have already been streamed, the HTTP status code remains `200 OK`. The error is delivered as an SSE event:

```json
{
  "choices": [
    {
      "finish_reason": "error",
      "error": {
        "code": 502,
        "message": "Provider error occurred",
        "metadata": { "provider_name": "Anthropic" }
      }
    }
  ]
}
```

### 7.6 Debug Chunk

When `debug.echo_upstream_body: true` is set, the first streaming chunk contains the transformed request body sent upstream:

```json
{
  "choices": [],
  "debug": {
    "upstream_body": {...}
  }
}
```

For requests with provider fallbacks, a debug chunk is sent for each provider attempt.

### 7.7 Stream Cancellation

Supported providers: OpenAI, Azure, Anthropic, Fireworks, and 25+ others. Aborting the HTTP connection immediately stops model processing and billing for supported providers. For non-streaming requests or unsupported providers, the model continues processing and you are billed for the complete response.

### 7.8 Legacy Text Completions Streaming

For `/api/v1/completions` (non-chat), streaming choices use `text` instead of `delta`:

```json
{
  "choices": [{ "text": "chunk", "finish_reason": null }]
}
```

---

## 8. Provider Routing

### 8.1 Default Load Balancing

OpenRouter's default three-tier strategy:

1. **Uptime filtering:** Exclude providers with significant outages in the last 30 seconds
2. **Cost weighting:** From remaining providers, select weighted by inverse square of the price (i.e., a $1/M provider gets 9x more traffic than a $3/M provider)
3. **Fallbacks:** Remaining providers serve as backups

### 8.2 Provider Object Fields

```json
{
  "provider": {
    "order": ["Anthropic", "Amazon Bedrock", "Google Vertex"],
    "allow_fallbacks": true,
    "require_parameters": false,
    "data_collection": "allow",
    "zdr": false,
    "enforce_distillable_text": false,
    "only": ["Anthropic"],
    "ignore": ["Together"],
    "quantizations": [
      "int4",
      "int8",
      "fp4",
      "fp6",
      "fp8",
      "fp16",
      "bf16",
      "fp32",
      "unknown"
    ],
    "sort": "price",
    "max_price": {
      "prompt": 1.0,
      "completion": 2.0,
      "image": 0.05,
      "audio": 0.01,
      "request": 0.005
    },
    "preferred_min_throughput": 100,
    "preferred_max_latency": 2.0
  }
}
```

All `max_price` values are in USD per million tokens (or per unit for images/requests).

### 8.3 Sort Options

Simple sort (string):

```json
{"provider": {"sort": "price"}}
{"provider": {"sort": "throughput"}}
{"provider": {"sort": "latency"}}
```

Advanced sort (object):

```json
{
  "provider": {
    "sort": {
      "by": "throughput",
      "partition": "model"
    }
  }
}
```

`partition` values: `"model"` (default, groups endpoints by model before sorting) | `"none"` (sorts globally across all models)

### 8.4 Percentile-Based Routing

```json
{
  "provider": {
    "preferred_min_throughput": {
      "p50": 100,
      "p75": 80,
      "p90": 50,
      "p99": 25
    },
    "preferred_max_latency": {
      "p50": 1,
      "p90": 3,
      "p99": 5
    }
  }
}
```

Percentile thresholds **deprioritize** rather than exclude. Requests still execute if all providers fail thresholds. `max_price` by contrast **blocks** requests if no provider meets the price constraint.

### 8.5 Data Collection

```json
{ "provider": { "data_collection": "deny" } }
```

`"deny"` excludes providers that may store data non-transiently.

### 8.6 Zero Data Retention (ZDR)

```json
{ "provider": { "zdr": true } }
```

Restricts routing to ZDR-compliant endpoints. Note: OpenRouter considers ephemeral KV caching (e.g., implicit caching on Gemini) as ZDR-compliant since it doesn't constitute persistent data retention.

### 8.7 Require Parameters

```json
{ "provider": { "require_parameters": true } }
```

Only routes to providers that support all parameters in the request (e.g., `tools`, `max_tokens`, specific `response_format` types). When `tools` or `tool_choice` are in the request, OpenRouter automatically routes only to tool-supporting providers (same effect without needing this field).

### 8.8 Model Variant Shortcuts

- Model ID suffix `:nitro` is equivalent to `"sort": "throughput"`
- Model ID suffix `:floor` is equivalent to `"sort": "price"`

### 8.9 Fallback Models

```json
{
  "model": "anthropic/claude-3.5-sonnet",
  "models": [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "google/gemini-2.0-flash"
  ],
  "route": "fallback"
}
```

Triggers on: context length errors, moderation flags, rate limiting, provider downtime. If a fallback also fails, OpenRouter returns that error. The `model` field in the response identifies which model actually responded. Billing is based on the model that handled the request.

### 8.10 EU In-Region Routing

Enterprise customers can enable EU-only routing via account settings. When enabled, all prompts and completions are processed entirely within the EU.

---

## 9. Tool and Function Calling

### 9.1 Request Structure (Three-Turn Pattern)

**Turn 1 - Initial request with tools:**

```json
{
  "model": "openai/gpt-4o",
  "messages": [{ "role": "user", "content": "What's the weather in SF?" }],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": { "type": "string", "description": "City name" }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

**Turn 1 - Response with tool call:**

```json
{
  "choices": [
    {
      "finish_reason": "tool_calls",
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\":\"San Francisco\"}"
            }
          }
        ]
      }
    }
  ]
}
```

**Turn 2 - Follow-up with tool results (tools array must be included again):**

```json
{
  "model": "openai/gpt-4o",
  "messages": [
    {"role": "user", "content": "What's the weather in SF?"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_abc123", "type": "function", "function": {"name": "get_weather", "arguments": "{\"location\":\"San Francisco\"}"}}]},
    {"role": "tool", "tool_call_id": "call_abc123", "content": "72°F, sunny"}
  ],
  "tools": [...]
}
```

**Critical:** The `tools` parameter must be included in every request (all turns), not just the first one.

### 9.2 Parallel Tool Calls

```json
{ "parallel_tool_calls": true }
```

Default is `true`. When `false`, model requests one tool at a time sequentially.

### 9.3 Streaming with Tool Calls

Monitor `delta.tool_calls` in streaming chunks for tool call data building up incrementally. Check `finish_reason` to detect when tool calls complete.

### 9.4 OpenRouter Normalization

OpenRouter transforms tool calls to match each provider's native format. From the developer's perspective, the OpenAI function calling format works universally.

---

## 10. Structured Outputs

### 10.1 JSON Object Mode

```json
{
  "response_format": { "type": "json_object" },
  "messages": [
    { "role": "system", "content": "Always respond with valid JSON." },
    { "role": "user", "content": "Give me user data" }
  ]
}
```

When using JSON mode, also instruct the model to produce JSON via system/user message.

### 10.2 JSON Schema Mode

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "user_data",
      "description": "User information schema",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "age": { "type": "integer" },
          "email": { "type": "string", "format": "email" }
        },
        "required": ["name", "age"],
        "additionalProperties": false
      }
    }
  }
}
```

Internally, OpenRouter converts JSON Schema to a context-free grammar (CFG) for constrained generation.

### 10.3 Grammar Mode

```json
{
  "response_format": {
    "type": "grammar",
    "grammar": "EBNF grammar string here"
  }
}
```

### 10.4 Strict Tool Use

For strict schema enforcement on tool calls, pass the Anthropic beta header:

```
x-anthropic-beta: structured-outputs-2025-11-13
```

Without this header, `strict: true` on tools is stripped.

### 10.5 Response Healing Plugin Integration

Pair with `response-healing` plugin to auto-repair malformed JSON before it reaches your application:

```json
{
  "plugins": [{"id": "response-healing"}],
  "response_format": {"type": "json_schema", "json_schema": {...}}
}
```

Response healing only works for non-streaming requests.

---

## 11. Prompt Caching

### 11.1 How It Works

Most providers automatically enable prompt caching. For providers that support explicit caching (Anthropic, Google), add `cache_control` breakpoints in message content.

When caching is used, OpenRouter makes a best effort to continue routing to the same provider to hit the warm cache.

### 11.2 Cache Control Syntax

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "Large context to cache...",
      "cache_control": {
        "type": "ephemeral",
        "ttl": "1h"
      }
    },
    {
      "type": "text",
      "text": "Dynamic user query"
    }
  ]
}
```

`ttl` values: `"5m"` (default, 1.25x write cost) | `"1h"` (2x write cost, available on Claude 4.5 models)

### 11.3 Provider-Specific Cache Behavior

| Provider                    | Cache Type           | Setup Required        | Breakpoints               |
| --------------------------- | -------------------- | --------------------- | ------------------------- |
| OpenAI                      | Automatic            | None                  | N/A                       |
| Anthropic                   | Explicit             | Yes (`cache_control`) | Max 4 per request         |
| Google Gemini 2.5 Pro/Flash | Implicit (automatic) | None                  | N/A                       |
| Google Gemini (others)      | Explicit             | Yes (`cache_control`) | Only last breakpoint used |
| DeepSeek                    | Automatic            | None                  | N/A                       |
| Grok                        | Automatic            | None                  | N/A                       |
| Moonshot                    | Automatic            | None                  | N/A                       |
| Groq                        | Automatic            | None                  | N/A                       |

**Anthropic minimum tokens:** 4,096 for Opus 4.5/Haiku 4.5, 1,024 for Opus 4.1/4/Sonnet 4.5/4

**OpenAI minimum tokens:** 1,024

**Google Gemini minimum tokens:** 4,096

### 11.4 Cache Hit Indicators in Response

```json
{
  "usage": {
    "prompt_tokens_details": {
      "cached_tokens": 1000,
      "cache_write_tokens": 1000
    }
  },
  "cache_discount": 0.15
}
```

`cached_tokens` = tokens read from cache (positive = cache hit)
`cache_write_tokens` = tokens written to cache (establishing new cache entry)
`cache_discount` = cost savings percentage for this generation

### 11.5 Best Practices

- Place static content (system prompts, RAG context) at the top; dynamic content at bottom
- Use consistent user identifiers (`user` field) to improve cache "stickiness" routing
- Large content (CSV files, character cards, RAG data) benefits most

---

## 12. Plugins

### 12.1 Web Search Plugin

**Enable via model suffix:**

```json
{ "model": "openai/gpt-4o:online" }
```

**Enable via plugins array:**

```json
{
  "plugins": [
    {
      "id": "web",
      "enabled": true,
      "max_results": 5,
      "search_prompt": "Custom citation instructions",
      "engine": "native"
    }
  ]
}
```

Engine options:

- `"native"`: Provider's built-in search (OpenAI, Anthropic, Perplexity, xAI). Forces native even if model doesn't support it (may error).
- `"exa"`: Exa.ai keyword + embeddings search
- Omit: Auto-select native if available, else Exa

**Pricing:** Exa search costs $4 per 1,000 results (~$0.02/request at 5 results). Native search pricing passes through from provider.

**Response format:** Citations appear in `message.annotations` array following OpenAI annotation schema (see section 6.5).

### 12.2 File Parser Plugin (PDF Processing)

```json
{
  "plugins": [
    {
      "id": "file-parser",
      "pdf": { "engine": "mistral-ocr" }
    }
  ]
}
```

PDF engine options: `"mistral-ocr"` | `"pdf-text"` | `"native"`

Default: OpenRouter uses native file processing if available, else `mistral-ocr`.

**Sending a PDF:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        { "type": "file", "file": { "url": "https://example.com/doc.pdf" } },
        { "type": "text", "text": "Summarize this document" }
      ]
    }
  ]
}
```

PDFs can be URLs or base64-encoded data URLs.

**File annotations:** The response may include `file_annotations` in the assistant message that can be sent back in subsequent requests to avoid re-parsing the same PDF.

Works with any model on OpenRouter, regardless of native PDF support.

### 12.3 Response Healing Plugin

```json
{
  "plugins": [{"id": "response-healing"}],
  "response_format": {"type": "json_schema", "json_schema": {...}}
}
```

Activates automatically for non-streaming requests with `json_schema` or `json_object` response format.

Fixes:

- Missing brackets/commas/quotes
- Markdown wrapping around JSON (extracts JSON from code blocks)
- Trailing commas
- Unquoted keys (`{name: "x"}` → `{"name": "x"}`)
- Mixed content (isolates JSON from surrounding text)

**Limitations:**

- Non-streaming only
- Cannot fix truncated responses (hit by `max_tokens`)
- Some severely malformed JSON remains unrepairable

**Performance:** Reduces JSON defects by 80-99%+ depending on model.

### 12.4 Auto Router Plugin

```json
{
  "model": "openrouter/auto",
  "plugins": [
    {
      "id": "auto-router",
      "allowed_models": ["anthropic/*", "openai/gpt-5*", "google/*"]
    }
  ]
}
```

Uses NotDiamond's routing to select the optimal model based on prompt analysis. Wildcard patterns supported in `allowed_models`.

---

## 13. Reasoning / Extended Thinking

### 13.1 Request Format

```json
{
  "reasoning": {
    "effort": "high",
    "max_tokens": 8000,
    "exclude": false,
    "enabled": true,
    "summary": "auto"
  }
}
```

`summary` values: `"auto"` | `"concise"` | `"detailed"` (nullable)

### 13.2 Effort-to-Token Mapping

If using `effort` with a `max_tokens` of 10,000:

| Effort  | Ratio | Budget Tokens |
| ------- | ----- | ------------- |
| xhigh   | 0.95  | 9,500         |
| high    | 0.80  | 8,000         |
| medium  | 0.50  | 5,000         |
| low     | 0.20  | 2,000         |
| minimal | 0.10  | 1,000         |

Capped at 128,000 maximum; minimum 1,024 tokens.

`max_tokens` must be strictly greater than the reasoning budget to ensure space for the final response.

### 13.3 Model Support Matrix

| Parameter                        | Supported Models                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------- |
| `reasoning.effort`               | OpenAI (o1/o3/GPT-5), Grok models                                                     |
| `reasoning.max_tokens`           | Gemini thinking, Anthropic, Alibaba Qwen                                              |
| Preserved reasoning across turns | OpenAI, Anthropic, Gemini, xAI, MiniMax, Kimi, INTELLECT-3, Nemotron 3, MiMo-V2, Z.ai |

Note: The `:thinking` model variant is no longer supported for Anthropic models — use the `reasoning` parameter directly.

### 13.4 Excluding Reasoning from Response

```json
{ "reasoning": { "exclude": true } }
```

Model still uses reasoning internally; reasoning tokens are not returned in the response but are still billed as output tokens.

### 13.5 Preserving Reasoning Context Across Turns

Include the previous `reasoning_details` when sending follow-up messages:

```json
{
  "messages": [
    {"role": "assistant", "content": "Previous response", "reasoning": "plaintext reasoning", "reasoning_details": [...]}
  ]
}
```

---

## 14. Multimodal Inputs

### 14.1 Image Inputs

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "https://example.com/image.jpg",
            "detail": "auto"
          }
        },
        { "type": "text", "text": "What's in this image?" }
      ]
    }
  ]
}
```

`detail` options: `"auto"` | `"low"` | `"high"`

Images can be URLs or base64-encoded data URLs: `"data:image/png;base64,<base64_data>"`

Multiple images can be sent in separate content array entries.

### 14.2 Video Inputs

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "video_url",
          "video_url": { "url": "https://youtube.com/watch?v=..." }
        },
        { "type": "text", "text": "Summarize this video" }
      ]
    }
  ]
}
```

Only models with video processing capabilities handle video inputs. OpenRouter only sends video URLs to providers that explicitly support them. Google AI Studio only supports YouTube links for video (not Vertex AI). Video uploads not available in OpenRouter chatroom.

### 14.3 Audio Inputs

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_audio",
          "input_audio": { "data": "base64audiodata", "format": "wav" }
        },
        { "type": "text", "text": "Transcribe this audio" }
      ]
    }
  ]
}
```

---

## 15. Image Generation

### 15.1 Endpoint and Setup

Uses the same `/api/v1/chat/completions` endpoint with the `modalities` field:

```json
{
  "model": "openai/gpt-5-image",
  "messages": [
    { "role": "user", "content": "Generate a sunset over mountains" }
  ],
  "modalities": ["image"],
  "stream": false
}
```

For models producing both text and images (e.g., Gemini):

```json
{ "modalities": ["text", "image"] }
```

### 15.2 Image Configuration

```json
{
  "image_config": {
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "font_inputs": [{ "font_url": "https://...", "text": "Sample text" }],
    "super_resolution_references": ["https://reference-image-url.jpg"]
  }
}
```

Aspect ratio options: `"1:1"` (1024×1024), `"16:9"` (1344×768), `"9:16"` (768×1344)

Resolution options: `"1K"`, `"2K"`, `"4K"`

Font inputs: max 2, cost $0.03 per font (Sourceful only)

Super resolution references: max 4, cost $0.20 each, image-to-image requests only (Sourceful only)

### 15.3 Image Generation Response

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "images": [
          {
            "type": "image_url",
            "image_url": { "url": "data:image/png;base64,..." }
          }
        ]
      }
    }
  ]
}
```

Images return as base64-encoded PNG data URLs.

---

## 16. Embeddings

### 16.1 Endpoint

**POST** `https://openrouter.ai/api/v1/embeddings`

### 16.2 Request

```json
{
  "model": "openai/text-embedding-3-small",
  "input": "Text to embed",
  "encoding_format": "float",
  "dimensions": 1536,
  "user": "user_id",
  "input_type": "optional string",
  "provider": {...}
}
```

`input` accepts: single string | array of strings | array of floats (vector) | array of float arrays | array of content objects with text/image combinations

`encoding_format`: `"float"` | `"base64"`

`dimensions`: Integer output dimensionality.

Provider routing object same as chat completions.

### 16.3 Response

```json
{
  "id": "emb-abc123",
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023064255, -0.009327292, ...],
      "index": 0
    }
  ],
  "model": "openai/text-embedding-3-small",
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5,
    "cost": 0.000001
  }
}
```

### 16.4 Key Characteristics

- No streaming support (deterministic output)
- Same text always produces identical embeddings
- Models have maximum input lengths; exceeding may cause truncation or error
- Added to OpenRouter in November 2025
- Browse available embedding models: `https://openrouter.ai/models?fmt=cards&output_modalities=embeddings`

---

## 17. Responses API (Beta)

### 17.1 Overview

**Endpoint:** `POST https://openrouter.ai/api/v1/responses`

OpenAI-compatible Responses API. Stateless — each request is independent, no conversation state is persisted server-side. Full conversation history must be included with every request.

**Warning:** Beta status, may introduce breaking changes.

### 17.2 Request Fields

```json
{
  "model": "openai/o4-mini",
  "input": "User prompt or message content"
}
```

### 17.3 Capabilities

- **Reasoning:** Configurable effort levels, encrypted reasoning chains
- **Tool Calling:** Function invocation with parallel execution
- **Web Search:** Real-time information retrieval with citation annotations

### 17.4 Responses API Tool Calling

Documented separately at: `https://openrouter.ai/docs/api/reference/responses/tool-calling`

---

## 18. Key Management APIs

All key management requires a Management/Provisioning key (cannot be a regular API key).

### 18.1 Create API Key

**POST** `https://openrouter.ai/api/v1/keys`

```json
{
  "name": "my-app-key",
  "limit": 10.0,
  "limit_reset": "monthly",
  "include_byok_in_limit": false,
  "expires_at": "2027-01-01T00:00:00Z"
}
```

`limit_reset` values: `"daily"` | `"weekly"` | `"monthly"` | `null` (no reset). Resets at midnight UTC; weeks are Monday–Sunday.

**Response (201):**

```json
{
  "key": "sk-or-v1-<actual-key-string-only-shown-once>",
  "data": {
    "hash": "key-hash-id",
    "name": "my-app-key",
    "label": "display label",
    "disabled": false,
    "limit": 10.0,
    "limit_remaining": 10.0,
    "limit_reset": "monthly",
    "include_byok_in_limit": false,
    "usage": 0,
    "usage_daily": 0,
    "usage_weekly": 0,
    "usage_monthly": 0,
    "byok_usage": 0,
    "byok_usage_daily": 0,
    "byok_usage_weekly": 0,
    "byok_usage_monthly": 0,
    "created_at": "2026-02-20T00:00:00Z",
    "updated_at": null,
    "expires_at": "2027-01-01T00:00:00Z"
  }
}
```

The `key` field is only shown once at creation. Store it securely.

### 18.2 List API Keys

**GET** `https://openrouter.ai/api/v1/keys`

Query params: `include_disabled` (string) | `offset` (string, for pagination)

Response contains `data` array of key objects (same schema as create response `data` field).

### 18.3 Get Single API Key

**GET** `https://openrouter.ai/api/v1/keys/{hash}`

Path param: `hash` — the key's hash identifier.

Returns the key metadata object (not the key string itself).

### 18.4 Delete API Key

**DELETE** `https://openrouter.ai/api/v1/keys/{hash}`

```json
{ "deleted": true }
```

### 18.5 Get Current Key Info (any key type)

**GET** `https://openrouter.ai/api/v1/key`

Returns 18-field object about the key used to authenticate:

```json
{
  "label": "my-key",
  "limit": 100.0,
  "limit_remaining": 85.5,
  "limit_reset": "monthly",
  "include_byok_in_limit": false,
  "usage": 14.5,
  "usage_daily": 2.1,
  "usage_weekly": 8.3,
  "usage_monthly": 14.5,
  "byok_usage": 0,
  "byok_usage_daily": 0,
  "byok_usage_weekly": 0,
  "byok_usage_monthly": 0,
  "is_free_tier": false,
  "is_management_key": false,
  "is_provisioning_key": false,
  "expires_at": null,
  "rate_limit": {
    "requests": 1000,
    "interval": "minute",
    "note": "legacy field"
  }
}
```

---

## 19. OAuth PKCE Flow

Allows users to authorize your application with one click, providing you their OpenRouter API key.

### 19.1 Step 1 — Redirect User

```
GET https://openrouter.ai/auth?callback_url=https://yourapp.com/callback&code_challenge=<base64_sha256_of_verifier>&code_challenge_method=S256
```

Parameters:

- `callback_url` (required): Your application's return URL
- `code_challenge` (optional, recommended): Base64-encoded SHA-256 hash of `code_verifier`
- `code_challenge_method` (optional): `"S256"` or `"plain"`

### 19.2 Step 2 — Receive Authorization Code

After user authorizes, they are redirected to:

```
https://yourapp.com/callback?code=<authorization_code>
```

### 19.3 Step 3 — Exchange Code for Key

**POST** `https://openrouter.ai/api/v1/auth/keys`

```json
{
  "code": "<authorization_code>",
  "code_verifier": "<original_verifier_string>",
  "code_challenge_method": "S256"
}
```

**Response:**

```json
{ "key": "sk-or-v1-<user-api-key>" }
```

### 19.4 Error Codes

| Code | Meaning                                                                      |
| ---- | ---------------------------------------------------------------------------- |
| 400  | Invalid `code_challenge_method` (mismatched with Step 1)                     |
| 403  | Invalid code or `code_verifier` (user not logged in, or verification failed) |
| 405  | Method Not Allowed (must use POST over HTTPS)                                |

---

## 20. Credits and Billing APIs

### 20.1 Get Credit Balance

**GET** `https://openrouter.ai/api/v1/credits`

Requires management key.

```json
{
  "data": {
    "total_credits": 100.0,
    "total_usage": 14.5
  }
}
```

Remaining balance = `total_credits - total_usage`

### 20.2 Pricing Structure

- **No markup** on inference pricing — developer pays provider rates
- **5.5% fee ($0.80 minimum)** when purchasing credits via Stripe
- **Higher fee** for USDC cryptocurrency payments via Coinbase
- **BYOK:** First monthly threshold of requests free; subsequent requests incur a percentage fee deducted from OpenRouter credits
- **Free models:** No cost; low rate limits

### 20.3 HTTP 402 Triggers

Account receives `402 Payment Required` when:

- Account has negative credit balance
- API key has exceeded its credit limit
- Even free model access requires non-negative balance

---

## 21. Analytics and Activity Tracking

### 21.1 User Activity Endpoint

**GET** `https://openrouter.ai/api/v1/activity`

Requires management key. Provides last 30 completed UTC days of data.

Query params: `date` (optional, YYYY-MM-DD format, limited to last 30 days)

**Response:**

```json
{
  "data": [
    {
      "date": "2026-02-20",
      "model": "openai/gpt-4o",
      "model_permaslug": "openai/gpt-4o-2025-01-15",
      "endpoint_id": "endpoint-uuid",
      "provider_name": "OpenAI",
      "usage": 1.25,
      "byok_usage_inference": 0,
      "requests": 100,
      "prompt_tokens": 50000,
      "completion_tokens": 10000,
      "reasoning_tokens": 0
    }
  ]
}
```

Data grouped by endpoint per day.

---

## 22. Generation Stats Endpoint

### 22.1 Retrieve Generation Stats

**GET** `https://openrouter.ai/api/v1/generation?id={generation_id}`

The `generation_id` is returned in the `id` field of every chat completion response. Use this to asynchronously retrieve detailed stats after a request completes.

Query params: `id` (required, string, min 1 char)

**Response:** Returns a `data` object with 34 properties including token counts, costs, latency, model used, and provider information.

**Use cases:**

- Post-hoc cost auditing
- Asynchronous usage retrieval
- Historical request analysis

**Status codes:** 401 | 402 | 404 | 429 | 500 | 502

---

## 23. Rate Limits

### 23.1 Free Model Rate Limits

Models with `:free` suffix:

- **20 requests per minute**
- **200 requests per day** (if account has < 10 credits purchased)
- **1,000 requests per day** (if account has ≥ 10 credits purchased)

Failed attempts still count toward daily quota.

### 23.2 Paid Model Rate Limits

No hard rate limits imposed by OpenRouter. Rate limits are determined by the underlying provider's capacity. BYOK: rate limits match your provider account directly.

### 23.3 DDoS Protection

Cloudflare's DDoS protection blocks requests that dramatically exceed reasonable usage patterns.

### 23.4 Global Rate Limit Scope

Rate limits apply globally across all API keys for a user (not per-key).

### 23.5 Rate Limit Headers in Error Body

When rate limited (429), the error body's `metadata.headers` contains:

```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded: limit_rpd/...",
    "metadata": {
      "headers": {
        "X-RateLimit-Limit": "80",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1741305600000"
      }
    }
  }
}
```

`X-RateLimit-Reset` is a Unix timestamp in milliseconds.

---

## 24. Error Codes and Error Response Format

### 24.1 Standard Error Response Structure

```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "metadata": {
      "headers": {...},
      "reasons": ["..."],
      "flagged_input": "truncated input text...",
      "provider_name": "Anthropic",
      "model_slug": "anthropic/claude-3.5-sonnet",
      "raw": {...}
    }
  }
}
```

The HTTP status code matches `error.code` when the original request is invalid or the account lacks credits. Otherwise, responses return `200 OK` with the error in the body.

### 24.2 HTTP Status Codes

| Code | Meaning               | Notes                                                                          |
| ---- | --------------------- | ------------------------------------------------------------------------------ |
| 200  | Success               | Also used for mid-stream errors after tokens have been sent                    |
| 201  | Created               | Used for key creation                                                          |
| 400  | Bad Request           | Invalid/missing params, CORS issues                                            |
| 401  | Unauthorized          | Invalid credentials, expired OAuth session, disabled/invalid API key           |
| 402  | Payment Required      | Insufficient credits or credit limit exceeded                                  |
| 403  | Forbidden             | Input flagged by moderation; non-management key accessing management endpoints |
| 404  | Not Found             | Resource not found                                                             |
| 405  | Method Not Allowed    | Wrong HTTP method                                                              |
| 408  | Request Timeout       | Request exceeded time limit                                                    |
| 429  | Too Many Requests     | Rate limit exceeded                                                            |
| 500  | Internal Server Error | Server error                                                                   |
| 502  | Bad Gateway           | Model down or invalid upstream response                                        |
| 503  | Service Unavailable   | No provider meets routing requirements                                         |

### 24.3 Moderation Error Metadata

When input is flagged (403):

```json
{
  "metadata": {
    "reasons": ["Contains harmful content"],
    "flagged_input": "first 100 chars of flagged text...",
    "provider_name": "Anthropic",
    "model_slug": "anthropic/claude-3.5-sonnet"
  }
}
```

### 24.4 Provider Error Metadata

When a provider fails:

```json
{
  "metadata": {
    "provider_name": "OpenAI",
    "raw": { "original": "provider error body" }
  }
}
```

### 24.5 503 Service Unavailable

Returned when no available provider meets your routing requirements, e.g.:

- `provider.only` specifies unavailable providers
- All providers in `provider.order` are down
- `max_price` constraints eliminate all providers
- `zdr: true` with no ZDR providers available for the model

---

## 25. Response Headers

OpenRouter does not extensively document response headers, but based on observed behavior:

**Standard Headers:**

- `Content-Type: application/json` or `text/event-stream` (streaming)
- `Transfer-Encoding: chunked` (streaming)

**Rate limit information** is embedded in the error response body (`metadata.headers`) rather than as standard HTTP response headers.

**Note:** OpenRouter does NOT return `openai-organization` or `x-ratelimit-*` as standalone response headers the way OpenAI does. Rate limit data is only surfaced in the error body on 429 responses.

---

## 26. Message Transforms

### 26.1 Middle-Out Compression

Default behavior for models with ≤8k context:

```json
{ "transforms": ["middle-out"] }
```

Middle-out removes content from the middle of the conversation when it exceeds the model's context limit, because LLMs pay less attention to middle content. Preserves:

- First half of messages (for context)
- Last half of messages (for recency)

For models: first targets models with context ≥50% of required tokens; falls back to highest-context available.

### 26.2 Disabling Transforms

```json
{ "transforms": [] }
```

### 26.3 Compatibility

Works with any model on OpenRouter.

---

## 27. Presets

Named configurations encapsulating provider routing, model selection, system prompts, and generation parameters.

### 27.1 Usage

```json
{"model": "@preset/email-copywriter", "messages": [...]}
{"model": "openai/gpt-4o", "preset": "email-copywriter", "messages": [...]}
{"model": "openai/gpt-4o@preset/email-copywriter", "messages": [...]}
```

### 27.2 Behavior

- Latest preset version always used
- Request parameters are shallow-merged with preset settings
- Organization accounts share presets across team members
- Version history preserved for rollback

### 27.3 Configurable via Presets

- Provider routing preferences
- Model selection and fallbacks
- System prompts
- Temperature, top_p, and other generation parameters
- Provider inclusion/exclusion rules

---

## 28. Guardrails and Governance

### 28.1 Guardrail Types

| Type                | Description                                                                       |
| ------------------- | --------------------------------------------------------------------------------- |
| Budget limit        | Spending cap in USD; resets daily/weekly/monthly; requests rejected when exceeded |
| Model allowlist     | Restrict to specific models (empty = allow all)                                   |
| Provider allowlist  | Restrict to specific providers (empty = allow all)                                |
| Zero Data Retention | Require ZDR-compatible providers for all requests                                 |

### 28.2 Enforcement Logic

When multiple guardrails apply:

- **Allowlists:** Intersection (only options allowed by ALL guardrails)
- **ZDR:** OR logic (enforced if ANY guardrail requires it)
- **Budget limits:** Checked independently per user and per key

### 28.3 Assignment Levels

- **Member-level:** Baseline for all of a member's API keys and chatroom usage
- **API key-level:** Granular control layered on top of member settings

Only one guardrail can be directly assigned to a user or key.

### 28.4 Organization Features

- Shared credit pool billed to organization
- Admins control credit purchases and billing access
- Members can create and manage their own API keys
- API keys created by any member are usable by all members
- SSO (SAML) available on Enterprise plans

### 28.5 Zero Data Retention (ZDR) Per-Request

```json
{ "provider": { "zdr": true } }
```

Ephemeral KV caching (Gemini implicit caching) is considered ZDR-compatible by OpenRouter's policy.

---

## 29. Observability and Broadcast

### 29.1 Supported Observability Platforms

OpenRouter Broadcast automatically sends traces to 13+ platforms without code changes:

- Comet Opik
- Grafana Cloud
- New Relic
- Sentry
- OpenTelemetry Collector (OTLP)
- LangSmith
- Langfuse
- Datadog
- Braintrust
- Helicone

### 29.2 Trace Fields

```json
{
  "trace": {
    "trace_id": "custom-trace-id",
    "trace_name": "my-trace",
    "span_name": "completion-span",
    "generation_name": "chat-generation",
    "parent_span_id": "parent-span-id",
    "environment": "production",
    "custom_key": "custom_value"
  }
}
```

Special keys (trace_id, trace_name, span_name, generation_name, parent_span_id) have special handling per destination. Additional keys are custom metadata passed through to destinations.

When using OpenTelemetry, custom metadata keys appear under `trace.metadata.*` namespace in OTLP span attributes.

### 29.3 Privacy Mode

Each broadcast destination can enable Privacy Mode to exclude prompt/completion content from traces (token counts, costs, timing, model info still sent).

### 29.4 Per-Destination API Key Filtering

Configure which API keys send traces to which destinations for granular routing of observability data.

### 29.5 User Tracking

The `user` field in requests improves caching (sticky routing to same provider for warm cache) and enables per-user analytics in the Activity dashboard.

---

## 30. Differences from OpenAI API

### 30.1 Request Differences

| Feature              | OpenAI                              | OpenRouter                                              |
| -------------------- | ----------------------------------- | ------------------------------------------------------- |
| Model field          | `"gpt-4o"`                          | `"openai/gpt-4o"` (provider prefix required)            |
| `models` array       | Not supported                       | Supported for fallbacks                                 |
| `route` field        | Not supported                       | Supported: `"fallback"`, `"sort"`                       |
| `provider` object    | Not supported                       | Full provider routing config                            |
| `transforms` field   | Not supported                       | `["middle-out"]` or `[]`                                |
| `plugins` array      | Not supported (has different tools) | `web`, `file-parser`, `response-healing`, `auto-router` |
| `reasoning.effort`   | Supported (specific models)         | Unified across all reasoning models                     |
| `session_id`         | Not supported                       | Supported for observability                             |
| `trace`              | Not supported                       | Full tracing metadata                                   |
| `metadata`           | Not supported                       | Key-value observability metadata                        |
| `preset`             | Not supported                       | Named configuration preset                              |
| `prediction`         | `prediction` field                  | Same field, same format                                 |
| `top_k`              | Not supported                       | Supported (forwarded to compatible providers)           |
| `min_p`              | Not supported                       | Supported                                               |
| `top_a`              | Not supported                       | Supported                                               |
| `repetition_penalty` | Not supported                       | Supported                                               |
| `verbosity`          | Not supported                       | Maps to Anthropic output_config.effort                  |

### 30.2 Response Differences

| Feature                | OpenAI                       | OpenRouter                                                              |
| ---------------------- | ---------------------------- | ----------------------------------------------------------------------- |
| `model` field          | Reflects requested model     | Reflects **actual model used** (may differ with fallbacks/auto-routing) |
| `native_finish_reason` | Not present                  | Always present; raw provider finish reason                              |
| `finish_reason` values | Provider-specific            | Normalized: `stop`, `length`, `tool_calls`, `content_filter`, `error`   |
| `usage.cost`           | Not present                  | Present: total cost in USD                                              |
| `usage.cost_details`   | Not present                  | Present: upstream cost breakdown                                        |
| `usage.is_byok`        | Not present                  | Present: whether BYOK key was used                                      |
| `cache_discount`       | Not present                  | Present: cost savings from caching                                      |
| `server_tool_use`      | Not present                  | Present: e.g., `{"web_search_requests": 1}`                             |
| `annotations`          | Present (GPT-4o with search) | Present (standardized for all models)                                   |

### 30.3 Streaming Differences

| Feature           | OpenAI                      | OpenRouter                                                           |
| ----------------- | --------------------------- | -------------------------------------------------------------------- |
| SSE comments      | Not sent                    | Sends `: OPENROUTER PROCESSING` comments                             |
| Mid-stream errors | HTTP 200 with error in body | Same, plus `finish_reason: "error"`                                  |
| Debug chunk       | Not present                 | First chunk with `debug` field when `debug.echo_upstream_body: true` |

### 30.4 Authentication Differences

| Feature             | OpenAI                      | OpenRouter                                        |
| ------------------- | --------------------------- | ------------------------------------------------- |
| API key prefix      | `sk-...`                    | `sk-or-v1-...`                                    |
| Attribution headers | Not supported               | `HTTP-Referer` and `X-Title` optional             |
| Management keys     | Not separate                | Distinct management key type for key provisioning |
| OAuth PKCE          | Via organization management | Native first-class support                        |

### 30.5 Endpoint Differences

| Endpoint         | OpenAI      | OpenRouter                          |
| ---------------- | ----------- | ----------------------------------- |
| `/v1/generation` | Not present | Present (post-request stats lookup) |
| `/v1/activity`   | Not present | Present (30-day analytics)          |
| `/v1/credits`    | Not present | Present (credit balance)            |
| `/v1/key`        | Not present | Present (key metadata)              |
| `/v1/keys`       | Not present | Present (key management CRUD)       |
| `/auth`          | Not present | Present (OAuth PKCE initiation)     |
| `/v1/auth/keys`  | Not present | Present (OAuth code exchange)       |

### 30.6 Behavioral Differences

| Behavior               | OpenAI                | OpenRouter                                                |
| ---------------------- | --------------------- | --------------------------------------------------------- |
| Unsupported parameters | May error             | Silently ignored and forwarded where possible             |
| Provider routing       | N/A (single provider) | Multi-provider with weighted load balancing               |
| Automatic fallback     | N/A                   | Automatic on 5xx or rate limit                            |
| Default model          | Must specify          | Optional; uses user's default if omitted                  |
| Latency overhead       | None                  | ~25-40ms                                                  |
| `transforms` default   | N/A                   | `middle-out` applied to models ≤8k context                |
| Cancellation billing   | Continues billing     | Stops billing for supported providers when stream aborted |

---

## 31. OpenAPI Specification

Machine-readable specification available in two formats:

- **YAML:** `https://openrouter.ai/openapi.yaml`
- **JSON:** `https://openrouter.ai/openapi.json`

These can be imported into Postman, Swagger UI, Insomnia, or used with OpenAPI code generators to produce client libraries.

The Postman collection is available at: `https://www.postman.com/ai-engineer/generative-ai-apis/documentation/ef6c9qg/openrouter-api`

---

## 32. BYOK (Bring Your Own Key)

### 32.1 Supported Providers

- Amazon Bedrock (API keys or AWS credentials)
- Google Vertex AI (service account JSON)
- Anthropic (direct API key)
- Azure AI Services (API key + endpoint URL)

### 32.2 Routing Behavior

BYOK keys receive priority in routing. If a BYOK key encounters rate limiting or failure, OpenRouter falls back to shared OpenRouter credits (unless "Always use this key" is configured).

### 32.3 Pricing

BYOK is free for the first monthly threshold of requests. Subsequent usage incurs a percentage fee deducted from OpenRouter credits. The `is_byok` field in `usage` indicates when a response was served via BYOK.

### 32.4 AWS Bedrock Configuration

```json
{
  "accessKeyId": "AKIA...",
  "secretAccessKey": "...",
  "region": "us-east-1"
}
```

Requires IAM permissions: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`.

### 32.5 Azure AI Services Configuration

```json
{
  "model_slug": "openai/gpt-4o",
  "endpoint_url": "https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions",
  "api_key": "...",
  "model_id": "gpt-4o"
}
```

### 32.6 Google Vertex AI Configuration

Service account JSON with optional region:

```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "region": "us-central1"
}
```

Requires IAM permissions: `aiplatform.endpoints.predict` and `aiplatform.endpoints.streamingPredict`.

---

## Summary: Key OpenRouter-Specific Request Fields Reference

| Field                               | Type          | Purpose                                         |
| ----------------------------------- | ------------- | ----------------------------------------------- |
| `models`                            | string[]      | Fallback model list in priority order           |
| `route`                             | string        | `"fallback"` or `"sort"`                        |
| `provider.order`                    | string[]      | Ordered provider preference list                |
| `provider.allow_fallbacks`          | boolean       | Allow backup providers                          |
| `provider.require_parameters`       | boolean       | Filter to param-supporting providers only       |
| `provider.data_collection`          | string        | `"allow"` or `"deny"`                           |
| `provider.zdr`                      | boolean       | Require Zero Data Retention providers           |
| `provider.only`                     | string[]      | Provider whitelist                              |
| `provider.ignore`                   | string[]      | Provider blacklist                              |
| `provider.quantizations`            | string[]      | Required quantization levels                    |
| `provider.sort`                     | string/object | Sort providers by price/throughput/latency      |
| `provider.max_price`                | object        | Max price per million tokens                    |
| `provider.preferred_min_throughput` | number/object | Throughput threshold (simple or percentile)     |
| `provider.preferred_max_latency`    | number/object | Latency threshold (simple or percentile)        |
| `transforms`                        | string[]      | `["middle-out"]` or `[]`                        |
| `plugins`                           | array         | web, file-parser, response-healing, auto-router |
| `reasoning`                         | object        | Extended thinking config                        |
| `prediction`                        | object        | Speculative decoding hint                       |
| `debug`                             | object        | `echo_upstream_body` for request inspection     |
| `user`                              | string        | Stable user ID for analytics/caching            |
| `session_id`                        | string        | Session ID for observability                    |
| `trace`                             | object        | Tracing metadata for broadcast                  |
| `metadata`                          | object        | Custom key-value observability data             |
| `preset`                            | string        | Named configuration preset                      |
| `modalities`                        | string[]      | Output modalities for image generation          |
| `image_config`                      | object        | Image generation parameters                     |
| `web_search_options`                | object        | Native web search context size                  |

---

## Notes on Undocumented / Community-Observed Behaviors

1. **Silent parameter dropping:** Unsupported parameters for a given model/provider are silently ignored rather than causing errors. This can mask misconfigurations.

2. **Provider-specific passthrough:** Some provider-specific parameters like `safe_prompt` (Mistral) or `raw_mode` (Hyperbolic) are forwarded directly to the provider without normalization.

3. **503 on impossible routing:** Specifying contradictory routing constraints (e.g., `only` providers that don't support the requested model) returns 503, not 400. The error message indicates no available provider meets requirements.

4. **Rate limit headers in error body, not HTTP headers:** Unlike OpenAI which uses `x-ratelimit-*` HTTP response headers, OpenRouter embeds rate limit info in the error JSON body under `metadata.headers`.

5. **`model` field in response always reflects actual model used:** When using fallbacks, auto-router, or model variants, the `model` in the response body always shows what actually ran, not what was requested.

6. **Free tier negative credit balance:** Negative credit balance blocks even free model access. Users must top up to restore access to `:free` models.

7. **`tool_calls` array required on all turns:** The `tools` parameter must be re-included in every multi-turn tool calling request, not just the first turn, so OpenRouter can validate the schema.

8. **Implicit caching = ZDR compliant:** OpenRouter's policy explicitly classifies ephemeral KV cache (as used in Gemini implicit caching) as Zero Data Retention compliant, which may differ from some users' expectations.

---

_Sources consulted:_

- https://openrouter.ai/docs/api/reference/overview
- https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
- https://openrouter.ai/docs/guides/routing/provider-selection
- https://openrouter.ai/docs/guides/routing/model-fallbacks
- https://openrouter.ai/docs/guides/features/tool-calling
- https://openrouter.ai/docs/guides/best-practices/prompt-caching
- https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
- https://openrouter.ai/docs/guides/features/plugins/web-search
- https://openrouter.ai/docs/guides/features/plugins/response-healing
- https://openrouter.ai/docs/guides/features/message-transforms
- https://openrouter.ai/docs/api/reference/streaming
- https://openrouter.ai/docs/api/reference/errors-and-debugging
- https://openrouter.ai/docs/api/reference/limits
- https://openrouter.ai/docs/guides/overview/auth/oauth
- https://openrouter.ai/docs/guides/overview/auth/byok
- https://openrouter.ai/docs/guides/features/guardrails
- https://openrouter.ai/docs/guides/guides/usage-accounting
- https://openrouter.ai/docs/faq
- https://openrouter.ai/api/v1/models (live endpoint)
- https://openrouter.ai/openapi.yaml
