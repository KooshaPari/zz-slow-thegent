<DONE>
# OpenRouter Advanced Features Research

**Date**: 2026-02-20
**Scope**: OpenRouter features that go beyond the standard OpenAI API

---

## Table of Contents

1. [Provider Routing (`provider` field)](#1-provider-routing)
2. [Model Routing & Fallbacks (`models` array, `route`)](#2-model-routing--fallbacks)
3. [Reasoning / Extended Thinking (`reasoning` field)](#3-reasoning--extended-thinking)
4. [Web Search Plugin (`plugins: [{id: "web"}]`)](#4-web-search-plugin)
5. [Message Transforms (`transforms` field)](#5-message-transforms)
6. [Context Length Handling](#6-context-length-handling)
7. [Structured Outputs (`response_format`)](#7-structured-outputs)
8. [Tool Calling Differences](#8-tool-calling-differences)
9. [Prompt Caching (`cache_control`)](#9-prompt-caching)
10. [Multimodal: Images, PDFs, Audio](#10-multimodal-images-pdfs-audio)
11. [Streaming (SSE)](#11-streaming-sse)
12. [Error Handling & Debugging](#12-error-handling--debugging)
13. [Response Fields Beyond OpenAI](#13-response-fields-beyond-openai)
14. [Request Headers](#14-request-headers)
15. [Cost Tracking & Usage Accounting](#15-cost-tracking--usage-accounting)
16. [Zero Data Retention (ZDR)](#16-zero-data-retention-zdr)
17. [Response Healing Plugin](#17-response-healing-plugin)
18. [Responses API Beta](#18-responses-api-beta)
19. [Dynamic Model Variants (Suffixes)](#19-dynamic-model-variants-suffixes)
20. [Auto Router](#20-auto-router)
21. [Proxy Implications Summary](#21-proxy-implications-summary)

---

## 1. Provider Routing

**URL**: https://openrouter.ai/docs/guides/routing/provider-selection

### What It Does

Allows fine-grained control over which AI providers handle a request. Without explicit routing preferences, OpenRouter uses intelligent load balancing with inverse-square price weighting (e.g., Provider A at $1/M tokens gets 9x more traffic than Provider C at $3/M tokens).

### Request Field: `provider` Object

Added to the request body alongside `model` and `messages`. All fields are optional.

```json
{
  "model": "meta-llama/llama-3.3-70b-instruct",
  "messages": [{ "role": "user", "content": "Hello" }],
  "provider": {
    "order": ["anthropic", "openai"],
    "allow_fallbacks": true,
    "require_parameters": false,
    "only": ["anthropic", "together"],
    "ignore": ["deepinfra"],
    "data_collection": "deny",
    "zdr": true,
    "quantizations": ["fp8"],
    "sort": {
      "by": "price",
      "partition": "model"
    },
    "preferred_min_throughput": { "p90": 50 },
    "preferred_max_latency": { "p90": 3 },
    "max_price": { "prompt": 2, "completion": 5 }
  }
}
```

### Full `provider` Object Schema

| Field                      | Type                | Default   | Description                                                                                    |
| -------------------------- | ------------------- | --------- | ---------------------------------------------------------------------------------------------- |
| `order`                    | `string[]`          | -         | Provider slugs to try in priority order                                                        |
| `allow_fallbacks`          | `boolean`           | `true`    | Enable backup providers when primary is unavailable                                            |
| `require_parameters`       | `boolean`           | `false`   | Only route to providers supporting ALL request parameters                                      |
| `data_collection`          | `"allow" \| "deny"` | `"allow"` | Filter by data storage policy                                                                  |
| `zdr`                      | `boolean`           | -         | Restrict to Zero Data Retention endpoints only                                                 |
| `enforce_distillable_text` | `boolean`           | -         | Route only to models permitting text distillation                                              |
| `only`                     | `string[]`          | -         | Allowlist: only these providers                                                                |
| `ignore`                   | `string[]`          | -         | Blocklist: never use these providers                                                           |
| `quantizations`            | `string[]`          | -         | Filter by quantization: `int4`, `int8`, `fp4`, `fp6`, `fp8`, `fp16`, `bf16`, `fp32`, `unknown` |
| `sort`                     | `string \| object`  | -         | Sort strategy (see below)                                                                      |
| `preferred_min_throughput` | `number \| object`  | -         | Min tokens/sec threshold (soft preference)                                                     |
| `preferred_max_latency`    | `number \| object`  | -         | Max latency threshold (soft preference)                                                        |
| `max_price`                | `object`            | -         | Hard price ceiling (blocks requests exceeding it)                                              |

### Sorting Options

**Simple string values** (disables load balancing, tries providers sequentially):

- `"price"` — sort cheapest first
- `"throughput"` — sort fastest first
- `"latency"` — sort lowest latency first

**Object-based sorting** (enables cross-model optimization):

```json
{
  "sort": {
    "by": "throughput",
    "partition": "none"
  }
}
```

Setting `"partition": "none"` removes model-level grouping, allowing global endpoint ranking across all fallback models.

### Performance Thresholds with Percentiles

Percentiles track rolling 5-minute metrics. Unmet thresholds deprioritize (not exclude) endpoints:

```json
{
  "preferred_min_throughput": { "p50": 100, "p90": 50 },
  "preferred_max_latency": { "p50": 1, "p90": 3 }
}
```

### Price Hard Ceiling

Unlike performance preferences, `max_price` hard-blocks requests:

```json
{
  "max_price": {
    "prompt": 1,
    "completion": 2,
    "request": 0.05,
    "image": 0.01
  }
}
```

Units are USD per million tokens (or per request/image where applicable).

### What Changes in Response

No structural changes to the response format. The `model` field in the response shows which provider/model ultimately handled the request.

### Proxy Implications

The `provider` object passes through transparently to OpenRouter. A proxy does NOT need to transform this field — OpenRouter interprets it. However, the proxy should be aware that:

- `require_parameters: true` may cause 503 errors if the proxy adds parameters the chosen provider does not support
- `max_price` may cause 503 if all providers exceed the ceiling

---

## 2. Model Routing & Fallbacks

**URL**: https://openrouter.ai/docs/guides/routing/model-fallbacks

### What It Does

Enables automatic failover to backup models if the primary model fails (due to rate limits, downtime, moderation flags, or context length errors).

### The `models` Array Field

Instead of a single `model` string, provide a `models` array listing models in priority order:

```json
{
  "models": [
    "anthropic/claude-sonnet-4-5",
    "openai/gpt-4o",
    "gryphe/mythomax-l2-13b"
  ],
  "messages": [{ "role": "user", "content": "What is the meaning of life?" }]
}
```

If the first model fails, OpenRouter tries the next in sequence. Requests are priced using whichever model ultimately responds.

### Fallback Triggers

Any of these cause automatic fallback to the next model:

- Context length validation errors
- Moderation flags (model filtered the input)
- Rate limiting
- Provider downtime (5xx responses)

### What's Reported in the Response

The `model` field in the response body contains the model that actually processed the request — not necessarily the first in the `models` array:

```json
{
  "id": "gen-abc123",
  "model": "openai/gpt-4o",
  "choices": [...],
  "usage": {...}
}
```

### Using with OpenAI SDK

When using the OpenAI SDK, pass `models` in the `extra_body` parameter:

```python
client.chat.completions.create(
    model="anthropic/claude-sonnet-4-5",
    messages=[...],
    extra_body={"models": ["anthropic/claude-sonnet-4-5", "openai/gpt-4o"]},
)
```

### Cross-Model Sorting with Fallbacks

When using fallbacks, the `provider.sort` object can control cross-model ranking:

```json
{
  "models": ["model-a", "model-b"],
  "provider": {
    "sort": {
      "by": "price",
      "partition": "none"
    }
  }
}
```

`"partition": "none"` allows global ranking across all fallback models instead of grouping by model first.

### Proxy Implications

The proxy must forward the `models` array as-is. If the proxy only handles `model` (singular), it must be extended to also pass `models`. The response `model` field will differ from the requested primary model if fallback occurred.

---

## 3. Reasoning / Extended Thinking

**URL**: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens

### What It Does

Enables reasoning tokens (thinking tokens) for models that support them. OpenRouter normalizes the interface across providers (OpenAI, Anthropic, Gemini, etc.) into a unified `reasoning` parameter.

### Request Field: `reasoning` Object

```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "messages": [{ "role": "user", "content": "Solve this step by step..." }],
  "reasoning": {
    "effort": "high",
    "max_tokens": 8000,
    "exclude": false,
    "enabled": true
  }
}
```

**Important**: Use `effort` OR `max_tokens`, not both.

### Full `reasoning` Object Schema

| Field        | Type      | Default  | Description                                                       |
| ------------ | --------- | -------- | ----------------------------------------------------------------- |
| `effort`     | `string`  | -        | `"xhigh"`, `"high"`, `"medium"`, `"low"`, `"minimal"`, `"none"`   |
| `max_tokens` | `number`  | -        | Direct token budget for reasoning                                 |
| `exclude`    | `boolean` | `false`  | If `true`, model still reasons but output is hidden from response |
| `enabled`    | `boolean` | inferred | Activate reasoning with medium effort defaults                    |

### Effort Level to Token Ratio

| Effort Level | Approximate Token % of `max_tokens` |
| ------------ | ----------------------------------- |
| `xhigh`      | ~95%                                |
| `high`       | ~80%                                |
| `medium`     | ~50%                                |
| `low`        | ~20%                                |
| `minimal`    | ~10%                                |
| `none`       | Disabled                            |

### Provider-Specific Mappings

- **OpenAI** (o1/o3/GPT-5): Use `effort` field. Maps to OpenAI's `reasoning.effort`.
- **Anthropic** (Claude 3.7+): Use `max_tokens`. Minimum 1024, maximum 128,000. Formula: `budget = max(min(max_tokens × ratio, 128000), 1024)`. If you pass `effort`, OpenRouter converts it to `max_tokens`.
- **Gemini**: Maps `effort` directly to `thinkingLevel`; actual tokens determined by Google internally.
- **xAI Grok**: Supports `effort` field.
- **Alibaba Qwen**: Use `max_tokens` via `thinking_budget`. Check individual model descriptions.

### Response Format

Reasoning appears in two places in the response:

**Non-streaming:**

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The answer is 42.",
        "reasoning": "Let me think through this...",
        "reasoning_details": [
          {
            "type": "reasoning.text",
            "id": "rs_abc123",
            "format": "anthropic-claude-v1",
            "index": 0,
            "text": "First, I'll consider...",
            "signature": "ErUkwi..."
          }
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "completion_tokens": 50,
    "completion_tokens_details": {
      "reasoning_tokens": 2000
    }
  }
}
```

**Streaming:** Reasoning arrives in `choices[].delta.reasoning_details` chunks.

### `reasoning_details` Object Types

| `type`                | Description                                                               |
| --------------------- | ------------------------------------------------------------------------- |
| `reasoning.text`      | Plaintext reasoning, optionally with `signature` for verification         |
| `reasoning.summary`   | Summarized reasoning (provider may summarize long chains)                 |
| `reasoning.encrypted` | Encrypted reasoning (required for multi-turn continuation with Anthropic) |

`format` values: `"anthropic-claude-v1"`, `"openai-responses-v1"`, `"google-gemini-v1"`, and others.

### Multi-Turn Reasoning Continuation

To preserve reasoning across conversation turns, pass the full `reasoning_details` array back in subsequent requests:

```json
{
  "messages": [
    {"role": "user", "content": "Original question"},
    {
      "role": "assistant",
      "content": "My answer",
      "reasoning": "My thinking...",
      "reasoning_details": [...]
    },
    {"role": "user", "content": "Follow-up question"}
  ],
  "reasoning": {"effort": "high"}
}
```

The entire sequence of consecutive reasoning blocks MUST match the model's original output exactly.

### Legacy Parameter

`include_reasoning: true/false` is still supported but superseded by the unified `reasoning` parameter.

### Proxy Implications

The proxy needs to:

1. Pass `reasoning` object through to OpenRouter transparently
2. Forward `reasoning_details` in responses to the client
3. Support clients passing `reasoning_details` back in message history
4. Reasoning tokens count as output tokens and are billed accordingly
5. The `reasoning` field in `message` (plaintext string) is a simpler alternative to `reasoning_details` for clients that don't need structured access

---

## 4. Web Search Plugin

**URL**: https://openrouter.ai/docs/guides/features/plugins/overview

### What It Does

Augments any model's response with real-time web search results before generating the answer. Powered by Exa (an AI-focused search engine). Works with any model on OpenRouter.

### How to Enable

**Method 1: `plugins` array** (explicit, configurable):

```json
{
  "model": "openai/gpt-4o",
  "messages": [{ "role": "user", "content": "What happened today in tech?" }],
  "plugins": [
    {
      "id": "web",
      "max_results": 3,
      "search_prompt": "Consider these web results when forming your response:"
    }
  ]
}
```

**Method 2: `:online` model suffix** (shorthand, uses defaults):

```json
{
  "model": "openai/gpt-4o:online",
  "messages": [{ "role": "user", "content": "What happened today in tech?" }]
}
```

### Plugin Configuration Options

| Field           | Type      | Default  | Description                                                         |
| --------------- | --------- | -------- | ------------------------------------------------------------------- |
| `id`            | `"web"`   | required | Plugin identifier                                                   |
| `max_results`   | `number`  | 5        | Number of search results to fetch                                   |
| `search_prompt` | `string`  | -        | Custom text prepended to search results in the prompt               |
| `enabled`       | `boolean` | `true`   | Set `false` to disable a default-configured plugin for this request |

### Pricing

$4 per 1,000 results. With the default of 5 results per prompt, this is approximately $0.02 per search-augmented request.

### Disabling a Default Plugin

If web search is configured as a default at the account level:

```json
{
  "plugins": [{ "id": "web", "enabled": false }]
}
```

### What Changes in Response

The response is structurally identical to standard chat completions. The search results are injected into the prompt context before generation — they are not returned as separate fields. The model's answer incorporates the search results.

### Combining Multiple Plugins

```json
{
  "plugins": [{ "id": "web", "max_results": 3 }, { "id": "response-healing" }]
}
```

### Proxy Implications

The proxy must forward the `plugins` array as-is. No response transformation is needed. If the proxy strips unknown fields from request bodies, `plugins` must be whitelisted. The `:online` suffix can be used as an alternative that doesn't require `plugins` support.

---

## 5. Message Transforms

**URL**: https://openrouter.ai/docs/guides/features/message-transforms

### What It Does

Pre-processes the message array before sending to the model. Currently only one transform is available: `middle-out`, which compresses long conversations to fit within a model's context window.

### Request Field: `transforms` Array

```json
{
  "model": "openai/gpt-4o",
  "messages": [...],
  "transforms": ["middle-out"]
}
```

To disable transforms explicitly:

```json
{
  "transforms": [],
  "messages": [...]
}
```

### Available Transform Values

| Value          | Description                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------- |
| `"middle-out"` | Removes/truncates messages from the middle of the conversation to fit within context window |

Only `"middle-out"` is currently supported. More transforms are planned.

### How `middle-out` Works

Two compression mechanisms:

1. **Token-based compression**: Removes or truncates messages from the middle of the prompt until the content fits within the model's context window. Applied when the prompt exceeds the context limit.

2. **Message-count compression**: When models enforce a maximum message count (e.g., Anthropic Claude: max 1,000 messages), keeps the first half and last half of the conversation.

**Rationale**: LLMs pay significantly less attention to content in the middle of long sequences, making middle messages the safest to compress.

**Limit**: Only applied to prompts up to **twice** the model's context size. If the prompt exceeds 2x context, the request fails rather than compressing.

### Default Behavior

Models with **8,192 tokens or fewer** context length have `middle-out` applied by default. To disable this automatic behavior for short-context models:

```json
{
  "transforms": []
}
```

### Model Selection with `middle-out`

When `middle-out` is enabled, OpenRouter prioritizes models whose context length is at least half of your total token requirement. For example, if a prompt requires 10,000 tokens total, models with at least 5,000 context length are considered first.

### Proxy Implications

The proxy must forward the `transforms` array as-is. If the proxy does not pass `transforms: []`, short-context models will have `middle-out` applied by default — which may be undesirable if the client expects their full message history to be sent. This is a significant proxy consideration: the proxy should either:

- Always forward `transforms` from the client request
- Add `transforms: []` if context compression is not desired for the proxy use case

---

## 6. Context Length Handling

### OpenRouter's Automatic Behavior

When a request's token count approaches or exceeds a model's context limit, OpenRouter:

1. Applies `middle-out` transform (if enabled — see above)
2. Routes to alternative providers with larger context windows
3. Returns a 503 error if no provider can handle the request

### `require_parameters: true` Interaction

Setting `provider.require_parameters: true` ensures OpenRouter only routes to providers that support all parameters in the request — including the `max_tokens` value:

```json
{
  "model": "openai/gpt-4o",
  "max_tokens": 100000,
  "provider": {
    "require_parameters": true
  }
}
```

Without this, OpenRouter may route to a provider with insufficient context or `max_tokens` support, then fall back.

### Context Length in Model Metadata

The `/api/v1/models` endpoint returns `context_length` for each model, enabling clients to check limits before sending:

```json
{
  "id": "openai/gpt-4o",
  "context_length": 128000,
  "per_request_limits": {
    "prompt_tokens": "...optional..."
  }
}
```

### Proxy Implications

No request/response transformation needed specifically for context length. The proxy should surface 503 errors from OpenRouter cleanly. If the proxy implements context-length checking, it should use the `/api/v1/models` metadata.

---

## 7. Structured Outputs

**URL**: https://openrouter.ai/docs/guides/features/structured-outputs

### What It Does

Ensures model responses conform to a specific JSON schema. OpenRouter normalizes the `response_format` parameter across providers.

### How to Enable

Set `response_format` in the request body:

**JSON object mode** (valid JSON, no specific schema):

```json
{
  "response_format": { "type": "json_object" }
}
```

**JSON schema mode** (strict schema conformance):

```json
{
  "model": "openai/gpt-4o",
  "messages": [{ "role": "user", "content": "Extract user info" }],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "user_info",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "age": { "type": "integer" },
          "email": { "type": "string", "format": "email" }
        },
        "required": ["name", "age", "email"],
        "additionalProperties": false
      }
    }
  }
}
```

### `strict` Field

Always set `strict: true` within `json_schema` to ensure exact schema conformance. Without it, the model uses best-effort schema matching.

### Special Header for Strict Tool Use

For strict tool use (`strict: true` on tools), you must explicitly pass the `structured-outputs-2025-11-13` header:

```
structured-outputs-2025-11-13: true
```

Without this header, OpenRouter strips the `strict` field from tool definitions and routes normally (without strict conformance).

### Supported Providers

- OpenAI (GPT-4o and later)
- Google Gemini
- Anthropic (Claude Sonnet 4.5+ and Opus 4.1+)
- Most open-source models
- Fireworks-provided models

Use `provider.require_parameters: true` to ensure routing only to supporting providers.

### Streaming with Structured Outputs

Structured outputs work with streaming. The model streams valid partial JSON that, when complete, forms a valid response matching the schema.

### Response Healing Integration

Combine with the `response-healing` plugin for automatic repair of malformed JSON (non-streaming only):

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {...}
  },
  "plugins": [{"id": "response-healing"}]
}
```

### What Changes in Response

The response structure is unchanged. The `content` field of the assistant message contains the JSON string conforming to your schema.

### Proxy Implications

The proxy must:

1. Forward `response_format` as-is
2. Forward the `structured-outputs-2025-11-13` header if the client sends it (for strict tool use)
3. Not strip unknown fields from `response_format.json_schema`

---

## 8. Tool Calling Differences

**URL**: https://openrouter.ai/docs/guides/features/tool-calling

### What It Does

OpenRouter normalizes tool/function calling across all providers. For non-OpenAI providers (Anthropic, Gemini, etc.), OpenRouter automatically transforms the request schema to the provider's native format.

### How It Works (Same as OpenAI)

Standard OpenAI tool calling format works unchanged:

```json
{
  "model": "google/gemini-3-flash-preview",
  "messages": [
    { "role": "user", "content": "What are some James Joyce books?" }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_gutenberg_books",
        "description": "Search Project Gutenberg for books",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string", "description": "Search query" }
          },
          "required": ["query"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### `tool_choice` Values

| Value                                                   | Description                         |
| ------------------------------------------------------- | ----------------------------------- |
| `"none"`                                                | Model will not call any tool        |
| `"auto"`                                                | Model decides whether to call tools |
| `"required"`                                            | Model must call one or more tools   |
| `{"type": "function", "function": {"name": "my_func"}}` | Force a specific tool               |

### `parallel_tool_calls`

Controls whether the model can call multiple tools simultaneously:

```json
{
  "parallel_tool_calls": false
}
```

Default: `true` for most models. Set `false` for sequential tool execution.

### What Changes in Response

When a tool is called, the response includes:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "search_gutenberg_books",
              "arguments": "{\"query\": \"James Joyce\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### Follow-up with Tool Result

```json
{
  "messages": [
    {"role": "user", "content": "What are some James Joyce books?"},
    {
      "role": "assistant",
      "tool_calls": [{"id": "call_abc123", "type": "function", "function": {...}}]
    },
    {
      "role": "tool",
      "tool_call_id": "call_abc123",
      "content": "[{\"title\": \"Ulysses\"}, {\"title\": \"Dubliners\"}]"
    }
  ],
  "tools": [...]
}
```

Note: The `tools` parameter must be included again in the follow-up request.

### Key Difference from Native OpenAI

OpenRouter's provider transformation layer is entirely unique. When routing to Anthropic Claude, Gemini, or other non-OpenAI providers, OpenRouter converts the OpenAI tool schema to the provider's native format. This abstraction means:

- The same request JSON works with any provider
- Provider-specific quirks are handled by OpenRouter
- `finish_reason: "tool_calls"` is normalized across all providers

### Proxy Implications

Tool calling passes through transparently. The proxy does not need to transform tool definitions or responses. The one exception is the `structured-outputs-2025-11-13` header for strict tool mode (see Section 7).

---

## 9. Prompt Caching

**URL**: https://openrouter.ai/docs/guides/best-practices/prompt-caching

### What It Does

Reduces latency and cost by caching portions of the prompt that remain constant across requests. OpenRouter attempts to route cached requests to the same provider to maximize cache hits.

### Two Modes of Caching

**Implicit caching** (Google Gemini 2.5 Pro/Flash, some others):

- Fully automatic, no configuration required
- OpenRouter handles routing to the same provider transparently
- No `cache_control` markers needed

**Explicit caching** (Anthropic Claude, some Gemini models):

- Requires `cache_control` breakpoints in message content
- Must use multipart content format (not plain text strings)

### Anthropic Explicit Caching

Up to 4 `cache_control` breakpoints per request. Cache breakpoints can only be inserted into the `text` part of a multipart message:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "You are analyzing this large document:"
        },
        {
          "type": "text",
          "text": "<LARGE DOCUMENT CONTENT HERE - 10,000+ tokens>",
          "cache_control": { "type": "ephemeral" }
        },
        {
          "type": "text",
          "text": "What are the key themes?"
        }
      ]
    }
  ]
}
```

### Cache TTL Options (Anthropic)

| `cache_control`                      | TTL       | Write Cost             | Use Case       |
| ------------------------------------ | --------- | ---------------------- | -------------- |
| `{"type": "ephemeral"}`              | 5 minutes | 1.25x base input price | Short sessions |
| `{"type": "ephemeral", "ttl": "1h"}` | 1 hour    | 2x base input price    | Long sessions  |

### Gemini-Specific Caching

- Uses the same `cache_control` syntax as Anthropic
- Only the **last** `cache_control` breakpoint applies (multiple breakpoints are ignored except the final one)
- OpenRouter abstracts cache management — no need to manually create/update/delete caches
- Cached tokens cost 0.25x the original input token cost
- TTL varies (average 3-5 minutes)

### Minimum Token Requirements (Anthropic)

| Model               | Minimum tokens for cache write |
| ------------------- | ------------------------------ |
| Claude Opus 4.5     | 4,096 tokens                   |
| Claude Haiku 4.5    | 4,096 tokens                   |
| Other Claude models | 1,024 tokens                   |

### Response Usage Fields for Caching

```json
{
  "usage": {
    "prompt_tokens": 10500,
    "prompt_tokens_details": {
      "cached_tokens": 10000,
      "cache_write_tokens": 100
    },
    "completion_tokens": 200,
    "total_tokens": 10700,
    "cost": 0.012,
    "cache_discount": 0.088
  }
}
```

| Field                | Description                                 |
| -------------------- | ------------------------------------------- |
| `cached_tokens`      | Tokens read from cache (cheaper)            |
| `cache_write_tokens` | Tokens written to cache (incurs write cost) |
| `cache_discount`     | Total savings from caching operations       |

### Maximizing Cache Hits

Keep the initial portion of your message arrays consistent between requests. Push variations (user questions, dynamic context) toward the **end** of the prompt/messages array.

### Proxy Implications

The proxy must:

1. Forward `cache_control` inside multipart content arrays without stripping it
2. Recognize that content must be in multipart format (array of objects), not plain strings, for `cache_control` to work
3. Forward `prompt_tokens_details` and `cache_discount` in the response to the client
4. Not strip `cache_write_tokens` from usage reporting

---

## 10. Multimodal: Images, PDFs, Audio

**URL**: https://openrouter.ai/docs/guides/overview/multimodal/overview

All multimodal inputs use the standard `/api/v1/chat/completions` endpoint.

### Image Inputs

**URL format** (recommended for publicly accessible images):

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image? (text prompt first)"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://example.com/image.jpg"
          }
        }
      ]
    }
  ]
}
```

**Base64 format** (for local/private images):

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgAB..."
  }
}
```

Supported types: `image/png`, `image/jpeg`, `image/webp`, `image/gif`

Best practice: Send the text prompt first, then images. If images must come first, put them in the system prompt.

### Image Generation (Output)

For models that generate images (check `output_modalities: ["image"]`):

```json
{
  "model": "openai/dall-e-3",
  "messages": [...],
  "modalities": ["image", "text"]
}
```

Response structure for generated images:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Here is the image:",
        "images": [
          {
            "image_url": {
              "url": "data:image/png;base64,iVBORw0KGgo..."
            }
          }
        ]
      }
    }
  ]
}
```

Note: `message.images` is an OpenRouter-specific response field not present in the standard OpenAI API.

### PDF Inputs

PDFs use the `file` content type:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "file",
          "file": {
            "url": "https://example.com/document.pdf",
            "filename": "document.pdf"
          }
        },
        {
          "type": "text",
          "text": "Summarize this document."
        }
      ]
    }
  ],
  "plugins": [{ "id": "file-parser" }]
}
```

**Base64 PDF:**

```json
{
  "type": "file",
  "file": {
    "url": "data:application/pdf;base64,JVBERi0xLjQ...",
    "filename": "document.pdf"
  }
}
```

**PDF Processing Engines** (configure via `plugins`):

```json
{
  "plugins": [{ "id": "file-parser", "engine": "mistral-ocr" }]
}
```

`"mistral-ocr"` is the recommended engine for scanned documents.

**Re-using parsed PDFs** (file annotations):
After an initial PDF request, the response may include `file_annotations` in the message. Pass these back in subsequent requests to avoid re-parsing:

```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "Here is the summary...",
      "file_annotations": [...]
    },
    {"role": "user", "content": "Tell me more about chapter 3"}
  ]
}
```

### Audio Inputs

Audio MUST be base64-encoded (direct URLs are not supported):

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_audio",
          "input_audio": {
            "data": "base64encodedaudiodata...",
            "format": "wav"
          }
        },
        {
          "type": "text",
          "text": "Transcribe this audio."
        }
      ]
    }
  ]
}
```

### Proxy Implications

The proxy must:

1. Forward multipart `content` arrays without collapsing them to plain strings
2. Handle `file` content type (not standard OpenAI)
3. Forward the `message.images` field from responses (not standard OpenAI)
4. Forward `file_annotations` in both directions for PDF caching
5. Audio requires base64 encoding before sending

---

## 11. Streaming (SSE)

**URL**: https://openrouter.ai/docs/api/reference/streaming

### How to Enable

```json
{
  "stream": true,
  "model": "openai/gpt-4o",
  "messages": [...]
}
```

### SSE Format

Standard OpenAI SSE format: `data: {json}\n\n`, terminated by `data: [DONE]\n\n`.

**OpenRouter-specific keep-alive comment** (sent periodically to prevent timeouts):

```
: OPENROUTER PROCESSING
```

This is an SSE comment (starts with `:`). Per SSE spec, comments must be ignored by clients. Some SSE client libraries may not handle non-JSON payloads correctly — use eventsource-parser, OpenAI SDK, or Vercel AI SDK.

### Streaming Response Delta Format

```json
{
  "id": "gen-abc123",
  "object": "chat.completion.chunk",
  "created": 1708444800,
  "model": "openai/gpt-4o",
  "provider": "OpenAI",
  "choices": [
    {
      "index": 0,
      "delta": {
        "role": "assistant",
        "content": "Hello"
      },
      "finish_reason": null
    }
  ]
}
```

Final chunk includes `usage` statistics.

### Streaming with Reasoning

Reasoning details arrive as separate delta chunks in `choices[].delta.reasoning_details`.

### Stream Cancellation

Cancellation (aborting the connection) is supported by major providers. For supported providers, this immediately stops model processing and billing:

- Supported: OpenAI, Anthropic, Fireworks
- Not supported: AWS Bedrock, Groq, Google, Mistral

For unsupported providers, the model continues processing and you are billed for the complete response even if you abort.

### Mid-Stream Errors (HTTP 200 with error in body)

If an error occurs after streaming has started, the HTTP status code remains 200. The error arrives as an SSE event:

```json
{
  "id": "gen-abc123",
  "object": "chat.completion.chunk",
  "created": 1708444800,
  "model": "openai/gpt-4o",
  "provider": "OpenAI",
  "error": {
    "code": "server_error",
    "message": "Provider returned an error"
  },
  "choices": [
    {
      "index": 0,
      "delta": { "content": "" },
      "finish_reason": "error"
    }
  ]
}
```

### Proxy Implications

The proxy must:

1. Forward SSE keep-alive comments (`: OPENROUTER PROCESSING`) or strip them — but NOT attempt to parse them as JSON
2. Handle mid-stream errors gracefully (HTTP 200 but error in body)
3. Forward the final usage chunk
4. Support cancellation/abort forwarding if desired
5. Handle reasoning delta chunks in the stream

---

## 12. Error Handling & Debugging

**URL**: https://openrouter.ai/docs/api/reference/errors-and-debugging

### Error Response Format

```json
{
  "error": {
    "code": 503,
    "message": "No available model provider that meets your routing requirements.",
    "metadata": {
      "provider_name": "anthropic",
      "raw": "Provider-specific error message"
    }
  }
}
```

HTTP status code matches `error.code`.

### Error Codes

| HTTP Code | Meaning                                                      |
| --------- | ------------------------------------------------------------ |
| 400       | Bad request: invalid/missing params, CORS                    |
| 401       | Invalid credentials: OAuth expired, disabled/invalid API key |
| 402       | Insufficient credits                                         |
| 403       | Input flagged by moderation                                  |
| 408       | Request timeout                                              |
| 429       | Rate limited                                                 |
| 502       | Model provider unavailable or returned invalid response      |
| 503       | No available provider matching routing requirements          |

### Error Metadata

**Moderation error (403)**:

```json
{
  "error": {
    "code": 403,
    "message": "Your input was flagged",
    "metadata": {
      "reasons": ["sexual content", "violence"],
      "flagged_input": "First 100 chars of flagged text...",
      "provider_name": "openai",
      "model_slug": "openai/gpt-4o"
    }
  }
}
```

**Provider error (502)**:

```json
{
  "error": {
    "code": 502,
    "message": "Provider returned an error",
    "metadata": {
      "provider_name": "anthropic",
      "raw": "{\"error\": {\"type\": \"overloaded_error\"}}"
    }
  }
}
```

### Rate Limit Headers (429 Responses)

When rate limited, the error response metadata includes:

- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Unix millisecond timestamp when limit resets

**Free model rate limits**: 20 requests/minute and 200 requests/day for models with `:free` suffix.

### Debugging: `debug.echo_upstream_body`

Inspect the transformed request that OpenRouter sends to the upstream provider. **Only works with streaming enabled**:

```json
{
  "model": "openai/gpt-4o",
  "messages": [...],
  "stream": true,
  "debug": {
    "echo_upstream_body": true
  }
}
```

Debug chunks arrive first in the stream with empty `choices` arrays. They contain the `debug.echo_upstream_body` object showing:

- Parameter transformations applied
- Message formatting changes
- Applied defaults
- Provider fallback behavior

### Proxy Implications

The proxy must:

1. Forward error metadata to clients (especially `provider_name` and `raw` for debugging)
2. Parse rate limit headers from error responses and surface them
3. Handle the `debug.echo_upstream_body` field if proxy clients use it (requires streaming)
4. Distinguish between pre-stream errors (proper HTTP error codes) and mid-stream errors (HTTP 200, error in SSE body)

---

## 13. Response Fields Beyond OpenAI

### OpenRouter-Specific Response Fields

Every response includes these non-standard fields:

```json
{
  "id": "gen-abc123",
  "object": "chat.completion",
  "created": 1708444800,
  "model": "openai/gpt-4o",
  "provider": "OpenAI",
  "system_fingerprint": "fp_abc",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello!",
        "reasoning": "Let me think...",
        "reasoning_details": [...],
        "images": [...],
        "file_annotations": [...]
      },
      "finish_reason": "stop",
      "native_finish_reason": "end_turn",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15,
    "completion_tokens_details": {
      "reasoning_tokens": 0
    },
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "cache_write_tokens": 0,
      "audio_tokens": 0
    },
    "cost": 0.00015,
    "cost_details": {
      "upstream_inference_cost": 0.00014
    },
    "cache_discount": 0
  }
}
```

### Field-by-Field Description

| Field                                  | Location                           | Description                                                              |
| -------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------ |
| `provider`                             | root                               | Which provider handled the request (e.g., `"OpenAI"`, `"Anthropic"`)     |
| `native_finish_reason`                 | `choices[].`                       | Provider's raw finish reason before normalization                        |
| `finish_reason`                        | `choices[].`                       | Normalized to: `tool_calls`, `stop`, `length`, `content_filter`, `error` |
| `reasoning`                            | `choices[].message.`               | Plaintext reasoning (when reasoning is enabled)                          |
| `reasoning_details`                    | `choices[].message.`               | Structured reasoning with type/format/id                                 |
| `images`                               | `choices[].message.`               | Array of generated images (image generation models)                      |
| `file_annotations`                     | `choices[].message.`               | Parsed PDF metadata for re-use                                           |
| `cost`                                 | `usage.`                           | Total credits charged (USD)                                              |
| `cost_details.upstream_inference_cost` | `usage.`                           | Actual upstream provider cost (BYOK only)                                |
| `cached_tokens`                        | `usage.prompt_tokens_details.`     | Tokens read from provider cache                                          |
| `cache_write_tokens`                   | `usage.prompt_tokens_details.`     | Tokens written to provider cache                                         |
| `cache_discount`                       | `usage.`                           | Total savings from caching                                               |
| `reasoning_tokens`                     | `usage.completion_tokens_details.` | Tokens used for reasoning                                                |
| `audio_tokens`                         | `usage.prompt_tokens_details.`     | Audio input tokens                                                       |
| `is_byok`                              | `usage.` (optional)                | Boolean: Bring Your Own Key request                                      |

### The `id` Field and `/api/v1/generation` Endpoint

The response `id` (e.g., `"gen-abc123"`) can be used to fetch detailed generation stats asynchronously:

```
GET https://openrouter.ai/api/v1/generation?id=gen-abc123
Authorization: Bearer YOUR_API_KEY
```

This returns full token counts, cost, and timing data — useful for async auditing.

---

## 14. Request Headers

### Standard OpenRouter Headers

| Header                            | Required | Description                                               |
| --------------------------------- | -------- | --------------------------------------------------------- |
| `Authorization: Bearer KEY`       | Yes      | API key authentication                                    |
| `Content-Type: application/json`  | Yes      | Request body format                                       |
| `HTTP-Referer: https://myapp.com` | No       | App URL for rankings/analytics                            |
| `X-Title: My App Name`            | No       | App display name for rankings                             |
| `x-session-id: SESSION_ID`        | No       | Groups related requests for observability (max 128 chars) |

### `HTTP-Referer` and `X-Title`

Both are optional but enabling both unlocks attribution features:

- Public app rankings on openrouter.ai
- Appearance on model pages showing which apps use which models
- Detailed analytics access
- Professional visibility in the OpenRouter community

**Localhost exception**: Apps using `localhost` URLs MUST include `X-Title` to be tracked.

Neither header affects rate limits. They do not expose sensitive request information.

### `x-session-id`

Groups related requests (e.g., a single conversation or agent workflow) for observability. If provided in both the request body and the `x-session-id` header, the body value takes precedence.

### Provider-Pass-Through Headers

OpenRouter forwards certain vendor-specific headers to providers:

- `x-anthropic-beta`: Passes Anthropic beta feature flags directly (e.g., `interleaved-thinking-2025-05-14`)
- Other vendor params like `safe_prompt` (Mistral), `raw_mode` (Hyperbolic) can be included in the request body and OpenRouter forwards them

### Proxy Implications

The proxy should:

1. Forward `HTTP-Referer` and `X-Title` from client requests (or set its own for the proxy app)
2. Forward `x-session-id` if provided by clients
3. Forward `x-anthropic-beta` and other vendor-specific headers/params
4. Not strip the `Authorization` header (or substitute its own)

---

## 15. Cost Tracking & Usage Accounting

**URL**: https://openrouter.ai/docs/guides/guides/usage-accounting

### Usage Always Included

Usage data is automatically included in every response. The deprecated `usage: { include: true }` and `stream_options: { include_usage: true }` parameters are no longer needed and have no effect.

### Full Usage Object Schema

```json
{
  "usage": {
    "prompt_tokens": 194,
    "completion_tokens": 56,
    "total_tokens": 250,
    "completion_tokens_details": {
      "reasoning_tokens": 32
    },
    "prompt_tokens_details": {
      "cached_tokens": 150,
      "cache_write_tokens": 44,
      "audio_tokens": 0
    },
    "cost": 0.00095,
    "cost_details": {
      "upstream_inference_cost": 0.00088
    },
    "cache_discount": 0.00012,
    "is_byok": false
  }
}
```

### Currency

All costs are in **USD**, deducted from your OpenRouter credits balance. OpenRouter adds no markup on inference pricing but charges a **5.5% fee ($0.80 minimum)** when purchasing credits. Prices exclude applicable taxes.

### Async Cost Lookup

Use the generation `id` from any response to fetch detailed stats:

```
GET https://openrouter.ai/api/v1/generation?id=gen-abc123
Authorization: Bearer YOUR_API_KEY
```

### Streaming Usage

For streaming responses, usage statistics appear in the **last SSE message** before `[DONE]`.

### Activity Export

The `/api/v1/activity` endpoint returns daily usage grouped by model for the last 30 days — useful for BI system integration.

---

## 16. Zero Data Retention (ZDR)

**URL**: https://openrouter.ai/docs/guides/features/zdr

### What It Does

Restricts routing to providers that guarantee no data retention (and by extension, no training on your data).

### Per-Request Enforcement

```json
{
  "model": "openai/gpt-4o",
  "messages": [...],
  "provider": {
    "zdr": true
  }
}
```

### Behavior

- OR logic: if either account setting or request parameter enables ZDR, it takes effect
- Per-request `zdr: true` cannot override account-wide ZDR enforcement (but account-wide does not block per-request `zdr: true`)
- In-memory prompt caching is NOT considered "retaining" data — ZDR-compliant endpoints may still cache in memory

### ZDR-Compliant Endpoints List

```
GET https://openrouter.ai/api/v1/endpoints/zdr
```

### Proxy Implications

Forward `provider.zdr` as-is. If your proxy use case requires data privacy guarantees, set `zdr: true` at the proxy level for all requests.

---

## 17. Response Healing Plugin

**URL**: https://openrouter.ai/docs/guides/features/plugins/response-healing

### What It Does

Automatically validates and repairs malformed JSON from AI models.

### Issues It Fixes

- Missing closing brackets/braces
- Markdown code block wrappers (e.g., ` ```json ... ``` `)
- Text preceding JSON output
- Trailing commas in objects
- Unquoted object keys (JavaScript-style syntax)

### How to Enable

```json
{
  "model": "openai/gpt-4o",
  "messages": [...],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "my_schema",
      "strict": true,
      "schema": {...}
    }
  },
  "plugins": [{"id": "response-healing"}]
}
```

### Activation Requirements

All three conditions must be met:

1. Non-streaming request (does not work with `stream: true`)
2. `response_format` set to `json_schema` or `json_object`
3. `response-healing` plugin included in `plugins` array

### Limitations

- Cannot repair responses truncated by `max_tokens`
- Some severely malformed responses may still be unrepairable
- Only works with non-streaming

---

## 18. Responses API Beta

**URL**: https://openrouter.ai/docs/api/reference/responses/overview

### What It Is

A separate stateless API endpoint that mirrors OpenAI's Responses API format. Beta status — may have breaking changes.

**Endpoint**: `https://openrouter.ai/api/v1/responses`
**Method**: POST

### How It Differs from Chat Completions

| Aspect       | Chat Completions                  | Responses API                    |
| ------------ | --------------------------------- | -------------------------------- |
| State        | Stateless                         | Stateless (no server-side state) |
| Input field  | `messages` array                  | `input` string                   |
| Architecture | Conversation management by client | Same                             |
| Reasoning    | `reasoning` parameter             | Integrated                       |
| Tool calling | `tools` + `tool_choice`           | Integrated                       |
| Web search   | `plugins: [{id: "web"}]`          | Integrated                       |

### Basic Request

```json
{
  "model": "openai/o4-mini",
  "input": "Hello, world!"
}
```

### Streaming Error Events (Responses API)

The Responses API uses typed events for errors:

- `response.failed`
- `response.error`
- `error`

### Proxy Implications

The Responses API is at a different path (`/api/v1/responses` vs `/api/v1/chat/completions`) and uses different input schema. Proxies targeting only chat completions may need separate handling for this endpoint.

---

## 19. Dynamic Model Variants (Suffixes)

These suffixes modify routing behavior without changing the `provider` object:

| Suffix      | Effect                                   | Equivalent                    |
| ----------- | ---------------------------------------- | ----------------------------- |
| `:nitro`    | Sort providers by throughput             | `provider.sort: "throughput"` |
| `:floor`    | Sort providers by price                  | `provider.sort: "price"`      |
| `:online`   | Enable web search                        | `plugins: [{id: "web"}]`      |
| `:thinking` | Enable reasoning (model must support it) | `reasoning: {enabled: true}`  |
| `:free`     | Use free tier variant                    | Model-specific free access    |
| `:extended` | Use extended context variant             | Model-specific long context   |

### Examples

```json
{"model": "openai/gpt-4o:nitro"}       // Throughput-optimized
{"model": "openai/gpt-4o:floor"}       // Cheapest provider
{"model": "openai/gpt-4o:online"}      // Web search enabled
{"model": "meta-llama/llama-3.3-70b-instruct:free"}  // Free tier
```

### Proxy Implications

Model suffixes are passed through in the `model` field. If the proxy rewrites or validates model names, it must not strip suffixes. The response `model` field will contain the resolved model (suffix removed or normalized).

---

## 20. Auto Router

**URL**: https://openrouter.ai/docs/guides/routing/routers/auto-router

### What It Does

Powered by NotDiamond. Analyzes the prompt and automatically selects the optimal model from a curated pool. No extra fee — charged at the standard rate of whichever model is selected.

### How to Use

```json
{
  "model": "openrouter/auto",
  "messages": [{ "role": "user", "content": "Your prompt here" }]
}
```

### Restricting the Model Pool

Use the `plugins` parameter with `allowed_models` patterns:

```json
{
  "model": "openrouter/auto",
  "messages": [...],
  "plugins": [
    {
      "id": "auto-router",
      "allowed_models": [
        "anthropic/*",
        "openai/gpt-5.1",
        "google/gemini-3*"
      ]
    }
  ]
}
```

Patterns: exact model IDs, wildcard `provider/*`, or glob patterns like `gpt-5*`.

### What's in the Response

The `model` field in the response reveals which model was actually selected:

```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "choices": [...],
  "usage": {...}
}
```

### Requires `messages` Format

The auto router requires the `messages` array format. The `prompt` string format is not supported.

---

## 21. Proxy Implications Summary

### Fields That Pass Through Transparently (No Transformation Needed)

These OpenRouter-specific request fields can be forwarded as-is without any proxy-side transformation:

| Field                                         | Proxy Action                              |
| --------------------------------------------- | ----------------------------------------- |
| `provider`                                    | Forward as-is                             |
| `models` (array)                              | Forward as-is                             |
| `reasoning`                                   | Forward as-is                             |
| `plugins`                                     | Forward as-is                             |
| `transforms`                                  | Forward as-is (or inject `[]` to disable) |
| `response_format`                             | Forward as-is                             |
| `tools`, `tool_choice`, `parallel_tool_calls` | Forward as-is                             |
| `debug`                                       | Forward as-is                             |
| `modalities`                                  | Forward as-is                             |

### Response Fields the Proxy Must NOT Strip

| Field                                              | Reason                             |
| -------------------------------------------------- | ---------------------------------- |
| `provider` (root)                                  | Which provider handled the request |
| `native_finish_reason`                             | Provider's raw finish reason       |
| `choices[].message.reasoning`                      | Reasoning text                     |
| `choices[].message.reasoning_details`              | Structured reasoning               |
| `choices[].message.images`                         | Generated images                   |
| `choices[].message.file_annotations`               | PDF parse cache                    |
| `usage.cost`                                       | Cost tracking                      |
| `usage.cost_details`                               | BYOK cost breakdown                |
| `usage.cache_discount`                             | Caching savings                    |
| `usage.prompt_tokens_details`                      | Cache hit/write counts             |
| `usage.completion_tokens_details.reasoning_tokens` | Reasoning token count              |
| `usage.is_byok`                                    | BYOK flag                          |

### Behaviors That Require Active Proxy Handling

1. **SSE keep-alives**: `": OPENROUTER PROCESSING"` comments must not be parsed as JSON. Either forward or strip.

2. **Mid-stream errors**: HTTP 200 with `error` field in SSE body — the proxy must propagate these to clients.

3. **`transforms: []`**: If the proxy targets models with ≤8,192 token context, `middle-out` is applied by default. The proxy should inject `"transforms": []` if this behavior is undesired.

4. **Multipart content**: `cache_control`, `file`, and `input_audio` content types require multipart format — the proxy must not collapse `content` arrays to plain strings.

5. **`structured-outputs-2025-11-13` header**: Required for strict tool use. The proxy must forward this header if clients send it.

6. **Rate limit headers in 429 errors**: Extract from error metadata and expose to clients.

7. **`models` array in fallbacks**: If the proxy only reads `model` (singular), it must also read `models` (array) and forward it.

8. **`x-session-id` header**: Forward for observability grouping.

9. **`HTTP-Referer` and `X-Title` headers**: Forward or set proxy-level values for attribution.

---

## Sources

- [Provider Routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Model Fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks)
- [Auto Router](https://openrouter.ai/docs/guides/routing/routers/auto-router)
- [Reasoning Tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
- [Plugins Overview](https://openrouter.ai/docs/guides/features/plugins/overview)
- [Response Healing](https://openrouter.ai/docs/guides/features/plugins/response-healing)
- [Message Transforms](https://openrouter.ai/docs/guides/features/message-transforms)
- [Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [Tool Calling](https://openrouter.ai/docs/guides/features/tool-calling)
- [Prompt Caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching)
- [Multimodal Overview](https://openrouter.ai/docs/guides/overview/multimodal/overview)
- [Image Inputs](https://openrouter.ai/docs/guides/overview/multimodal/images)
- [PDF Inputs](https://openrouter.ai/docs/guides/overview/multimodal/pdfs)
- [Audio Inputs](https://openrouter.ai/docs/guides/overview/multimodal/audio)
- [Image Generation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [Streaming](https://openrouter.ai/docs/api/reference/streaming)
- [Errors and Debugging](https://openrouter.ai/docs/api/reference/errors-and-debugging)
- [API Reference Overview](https://openrouter.ai/docs/api/reference/overview)
- [API Parameters](https://openrouter.ai/docs/api/reference/parameters)
- [Responses API Beta](https://openrouter.ai/docs/api/reference/responses/overview)
- [Usage Accounting](https://openrouter.ai/docs/guides/guides/usage-accounting)
- [Zero Data Retention](https://openrouter.ai/docs/guides/features/zdr)
- [App Attribution](https://openrouter.ai/docs/app-attribution)
