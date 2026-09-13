<DONE>
# Vercel AI Gateway — Deep Research Report

**Date:** 2026-02-20
**Source:** Vercel official documentation fetched 2026-02-20 from `vercel.com/docs/ai-gateway`
**Purpose:** Feature parity audit for thegent CLIProxy versus peer LLM gateway products.

---

## 1. What is Vercel AI Gateway?

Vercel AI Gateway is a cloud-hosted, SaaS-only LLM routing proxy that provides a unified API for accessing hundreds of AI models across many providers through a single endpoint. It was launched by Vercel as part of their AI platform alongside the Vercel AI SDK.

**Core value propositions:**

- One API key for hundreds of models from 30+ providers
- Fully OpenAI-compatible REST API (plus Anthropic-compatible endpoint)
- Zero markup on tokens — charges are at provider list price
- Automatic provider failover, load balancing, and fallbacks
- Spend monitoring, budget controls, and per-request cost metadata
- Native AI SDK v5/v6 integration (TypeScript/JavaScript first)
- Bring Your Own Key (BYOK) with no additional fee

**What it is NOT:**

- Not self-hostable — SaaS only, hosted at `ai-gateway.vercel.sh`
- Not a LiteLLM replacement in the self-hosted sense
- Not a model fine-tuning or training service
- No prompt transforms / context compression (unlike OpenRouter's `middle-out`)
- No moderation plugin layer (unlike OpenRouter)

---

## 2. Architecture

Vercel AI Gateway sits in front of all target AI providers as a hosted proxy. The architecture is:

```
Client
  |
  | Authorization: Bearer <AI_GATEWAY_API_KEY>
  v
https://ai-gateway.vercel.sh   (OpenAI-compat)
https://ai-gateway.vercel.sh   (Anthropic-compat, same host, different path prefix)
  |
  | Gateway routing engine:
  | - Selects provider by: explicit order, only/ignore filters,
  |   automatic uptime/latency scoring, BYOK credential injection
  |
  +---> Provider A (Anthropic, OpenAI, Google, xAI, etc.)
  +---> Provider B (fallback)
  +---> Provider C (fallback if B fails)
```

The gateway normalizes provider-specific request/response formats internally. Clients always speak a single unified format. The gateway handles:

- Credential injection to providers (system credentials or BYOK)
- Provider-specific request format translation
- Automatic prompt caching strategy per provider
- Reasoning token normalization across providers
- Cost deduction from AI Gateway Credits balance

---

## 3. Base URL and Authentication

### Base URLs

| API Surface | Base URL |
|-------------|----------|
| OpenAI-compatible API | `https://ai-gateway.vercel.sh/v1` |
| Anthropic-compatible API | `https://ai-gateway.vercel.sh` |

### Authentication Methods

**Method 1: API Key (recommended)**

```
Authorization: Bearer <AI_GATEWAY_API_KEY>
```

API keys are created in the Vercel Dashboard under the AI Gateway tab. The default
environment variable name is `AI_GATEWAY_API_KEY`.

**Method 2: OIDC Token (Vercel-native projects)**

```
Authorization: Bearer <VERCEL_OIDC_TOKEN>
```

Vercel automatically provisions OIDC tokens for projects linked to a Vercel team.
Tokens expire every 12 hours. Refresh with `vercel env pull`. The environment variable
name is `VERCEL_OIDC_TOKEN`.

**Precedence:** If both are set, API key takes precedence over OIDC token.

**Anthropic SDK header alternative:**

```
x-api-key: <AI_GATEWAY_API_KEY>
```

The Anthropic-compatible endpoint accepts both the `x-api-key` header (Anthropic SDK
native) and `Authorization: Bearer` (standard).

### Configuring Existing Clients

**OpenAI Python SDK:**

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("AI_GATEWAY_API_KEY"), base_url="https://ai-gateway.vercel.sh/v1")
```

**Anthropic Python SDK:**

```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("AI_GATEWAY_API_KEY"), base_url="https://ai-gateway.vercel.sh")
```

**Claude Code (the Anthropic CLI agent):**

```bash
ANTHROPIC_BASE_URL="https://ai-gateway.vercel.sh"
ANTHROPIC_AUTH_TOKEN="<AI_GATEWAY_API_KEY>"
ANTHROPIC_API_KEY=""    # Must be empty string — Claude Code checks this first
```

---

## 4. Supported Providers (as of 2026-02-20)

37 providers supported. Full slug table for use in `providerOptions.gateway.order/only`:

| Slug | Provider | Website |
|------|----------|---------|
| `alibaba` | Alibaba Cloud | alibabacloud.com |
| `anthropic` | Anthropic | anthropic.com |
| `arcee-ai` | Arcee AI | arcee.ai |
| `azure` | Azure AI | ai.azure.com |
| `baseten` | Baseten | baseten.co |
| `bedrock` | Amazon Bedrock | aws.amazon.com/bedrock |
| `bfl` | Black Forest Labs | bfl.ai |
| `bytedance` | ByteDance | byteplus.com |
| `cerebras` | Cerebras | cerebras.net |
| `cohere` | Cohere | cohere.com |
| `crusoe` | Crusoe | crusoe.ai |
| `deepinfra` | DeepInfra | deepinfra.com |
| `deepseek` | DeepSeek | deepseek.ai |
| `fireworks` | Fireworks | fireworks.ai |
| `google` | Google AI Studio | ai.google.dev |
| `groq` | Groq | groq.com |
| `inception` | Inception | inceptionlabs.ai |
| `klingai` | Kling AI | klingai.com |
| `meituan` | Meituan / LongCat | longcat.ai |
| `minimax` | MiniMax | minimax.io |
| `mistral` | Mistral | mistral.ai |
| `moonshotai` | Moonshot AI | moonshot.ai |
| `morph` | Morph | morphllm.com |
| `nebius` | Nebius | nebius.com |
| `novita` | Novita | novita.ai |
| `openai` | OpenAI | openai.com |
| `parasail` | Parasail | parasail.io |
| `perplexity` | Perplexity | perplexity.ai |
| `prodia` | Prodia | prodia.com |
| `recraft` | Recraft | recraft.ai |
| `sambanova` | SambaNova | sambanova.ai |
| `streamlake` | StreamLake | streamlake.ai |
| `togetherai` | Together AI | together.ai |
| `vercel` | Vercel (v0) | v0.app |
| `vertex` | Google Vertex AI | cloud.google.com/vertex-ai |
| `voyage` | Voyage AI | voyageai.com |
| `xai` | xAI | x.ai |
| `zai` | Z.ai | z.ai |

### Model ID Format

Models are specified as `{provider-slug}/{model-name}`:

```
openai/gpt-5.2
anthropic/claude-sonnet-4.5
google/gemini-3-flash
xai/grok-4
```

The `creator` in the model ID is the model creator (not necessarily the serving provider).
The same model (e.g., `anthropic/claude-sonnet-4.5`) may be served by multiple providers
(`anthropic`, `bedrock`, `vertex`). Provider selection is controlled by `providerOptions`.

### Dynamic Model Discovery

The models endpoint requires no authentication:

```
GET https://ai-gateway.vercel.sh/v1/models
```

Per-model provider endpoint data:

```
GET https://ai-gateway.vercel.sh/v1/models/{creator}/{model}/endpoints
```

---

## 5. Request Format — OpenAI Compatibility

The `/v1/chat/completions` endpoint implements the OpenAI Chat Completions API spec,
plus a set of gateway-specific extensions.

### Standard Parameters (OpenAI-compatible)

| Field | Type | Notes |
|-------|------|-------|
| `model` | string | Required. Format: `provider/model-name` |
| `messages` | array | Required. Standard OpenAI message objects |
| `stream` | boolean | Default false. Enables SSE streaming |
| `temperature` | number | Range 0-2 |
| `max_tokens` | integer | Max output tokens |
| `top_p` | number | Range 0-1 |
| `frequency_penalty` | number | Range -2 to 2 |
| `presence_penalty` | number | Range -2 to 2 |
| `stop` | string or array | Stop sequences |
| `tools` | array | Function calling tools (OpenAI-compatible shape) |
| `tool_choice` | string or object | `auto`, `none`, or named function |
| `response_format` | object | See structured outputs section |
| `user` | string | End-user identifier |

### Message Content Types

Standard text:
```json
{ "role": "user", "content": "Hello" }
```

Multimodal with image (base64):
```json
{
  "role": "user",
  "content": [
    { "type": "text", "text": "Describe this." },
    { "type": "image_url", "image_url": { "url": "data:image/png;base64,...", "detail": "auto" } }
  ]
}
```

File attachment (PDF):
```json
{
  "role": "user",
  "content": [
    { "type": "text", "text": "Summarize this PDF." },
    { "type": "file", "file": { "data": "<base64>", "media_type": "application/pdf", "filename": "doc.pdf" } }
  ]
}
```

Prompt caching (Anthropic-compatible `cache_control`):
```json
{
  "role": "user",
  "content": "Long document...",
  "cache_control": { "type": "ephemeral" }
}
```

### Gateway-Specific Request Extensions

These fields are NOT in the base OpenAI spec; they are Vercel AI Gateway additions:

**`providerOptions` (object)** — Routing and configuration:

```json
{
  "providerOptions": {
    "gateway": {
      "order": ["bedrock", "anthropic"],
      "only": ["anthropic", "vertex"],
      "caching": "auto",
      "models": ["anthropic/claude-sonnet-4.5", "google/gemini-3-flash"],
      "byok": {
        "anthropic": [{ "apiKey": "sk-ant-..." }]
      }
    },
    "anthropic": {
      "thinkingBudget": 0.001
    },
    "openai": {
      "reasoningEffort": "high",
      "reasoningSummary": "detailed"
    }
  }
}
```

**`models` (string[])** — Model fallback list (top-level alternative to `providerOptions.gateway.models`):

```json
{
  "model": "openai/gpt-5.2",
  "models": ["anthropic/claude-sonnet-4.5", "google/gemini-3-pro"]
}
```

**`reasoning` (object)** — Cross-provider reasoning control:

```json
{
  "reasoning": {
    "enabled": true,
    "max_tokens": 2000,
    "effort": "high",
    "exclude": false
  }
}
```

The `effort` levels: `none`, `minimal`, `low`, `medium`, `high`, `xhigh` (maps to ~10%, 20%, 50%, 80%, 95% of budget).
`max_tokens` and `effort` are mutually exclusive.

**Attribution headers** (optional, for app visibility on AI Gateway pages):

```
http-referer: https://myapp.vercel.app
x-title: MyApp
```

---

## 6. Response Format

### Non-Streaming Response

Standard OpenAI `chat.completion` object. No cost in the response body for non-streaming
(use the generation lookup endpoint or check `providerMetadata` on embeddings).

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "anthropic/claude-sonnet-4.5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris.",
        "reasoning": "Let me think about this...",
        "reasoning_details": [
          {
            "type": "reasoning.text",
            "text": "Let me think about this...",
            "signature": "anthropic-signature-xyz",
            "format": "anthropic-claude-v1",
            "index": 0
          }
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 28,
    "total_tokens": 43,
    "completion_tokens_details": {
      "reasoning_tokens": 50
    }
  }
}
```

**Gateway-specific response extensions:**

- `choices[].message.reasoning` — Normalized reasoning text (cross-provider, string)
- `choices[].message.reasoning_details` — Structured reasoning blocks with type, format, signature/data/summary, index
- `completion_tokens_details.reasoning_tokens` — Reasoning token count

The `model` field in the response reflects the ACTUAL model used, which may differ from the
requested model when fallbacks triggered.

### Provider Metadata (AI SDK responses)

When using the AI SDK, responses include a `providerMetadata` block:

```json
{
  "gateway": {
    "routing": {
      "originalModelId": "anthropic/claude-sonnet-4.5",
      "resolvedProvider": "anthropic",
      "resolvedProviderApiModelId": "claude-sonnet-4.5",
      "fallbacksAvailable": ["bedrock", "vertex"],
      "finalProvider": "anthropic",
      "attempts": [
        {
          "provider": "anthropic",
          "credentialType": "system",
          "success": true,
          "startTime": 458753.4,
          "endTime": 459891.7
        }
      ],
      "totalProviderAttemptCount": 1
    },
    "cost": "0.0045405",
    "marketCost": "0.0045405",
    "generationId": "gen_01K8KPJ0FZA7172X6CSGNZGDWY"
  }
}
```

**`gateway.cost`** — Amount debited from AI Gateway Credits (decimal string, USD).
**`gateway.marketCost`** — Provider market rate (may differ if BYOK with negotiated rates).
**`gateway.generationId`** — Unique ID usable with the generation lookup endpoint.

---

## 7. Streaming — SSE Format

Streaming follows the standard OpenAI SSE format:

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"anthropic/claude-sonnet-4.5","choices":[{"index":0,"delta":{"content":"Once"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"anthropic/claude-sonnet-4.5","choices":[{"index":0,"delta":{"content":" upon"},"finish_reason":null}]}

data: [DONE]
```

**Key characteristics:**
- Standard `data: {json}\n\n` SSE format
- No provider field in streaming chunks (unlike OpenRouter which adds `"provider": "OpenAI"`)
- No keep-alive comment lines (unlike OpenRouter's `": OPENROUTER PROCESSING"`)
- Ends with `data: [DONE]`

**Streaming with reasoning:**

```json
{
  "choices": [{
    "delta": {
      "reasoning": "Let me think...",
      "reasoning_details": [
        {
          "type": "reasoning.text",
          "text": "Let me think...",
          "format": "anthropic-claude-v1",
          "index": 0
        }
      ],
      "content": null
    }
  }]
}
```

Reasoning chunks arrive before content chunks. Reasoning details stream incrementally via
`delta.reasoning_details` alongside `delta.reasoning`.

---

## 8. Caching

Vercel AI Gateway does not implement a gateway-level semantic or exact response cache
(no "cache hits from previous identical requests" feature like some other proxies).

Instead, it orchestrates **provider-side prompt caching**:

### Implicit Caching (automatic at provider level)

Providers OpenAI, Google, and DeepSeek cache prompt tokens automatically. When routing to
these providers, no extra configuration is needed — the provider applies prompt caching and
the gateway passes through the cache discount.

### Explicit/Auto Caching for Anthropic

Anthropic requires explicit `cache_control` markers. The gateway provides two approaches:

**Approach 1: `caching: 'auto'`**

```json
{
  "providerOptions": {
    "gateway": {
      "caching": "auto"
    }
  }
}
```

When set, the gateway automatically adds a `cache_control` breakpoint at the end of static
content for Anthropic-hosted models. Works with Anthropic direct and Vertex AI. Bedrock
not yet supported.

**Approach 2: Manual `cache_control` markers**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Large document...",
      "cache_control": { "type": "ephemeral" }
    }
  ]
}
```

This is passed through to Anthropic exactly. Cache type `ephemeral` stores for the
session duration.

### Cache Pricing Metadata

The `/v1/models/{creator}/{model}/endpoints` endpoint returns cache pricing:

```json
{
  "pricing": {
    "input_cache_read": "0.0000002",
    "input_cache_write": "0.000002",
    "input_cache_read_tiers": [...],
    "input_cache_write_tiers": [...]
  }
}
```

The generation lookup endpoint returns `native_tokens_cached` for the request.

**Summary:** There is no Vercel-level semantic caching or exact-match response caching.
The feature is purely provider-side prompt token caching orchestrated via the gateway.

---

## 9. Rate Limiting

Vercel AI Gateway does not expose explicit rate limit headers or configurable rate limit
policies at the gateway level in the documented API. Rate limits are enforced by individual
providers and surfaced as standard 429 responses.

The API returns `429 Too Many Requests` when rate limits are exceeded. No `Retry-After`
header documentation was found in the gateway docs.

**Budget controls as an indirect rate limiting mechanism:**

- Teams can set credit balances; requests stop when balance is zero
- Auto top-up can be configured to prevent interruption

**No documented per-key or per-team rate limit configuration** was found. This contrasts
with OpenRouter, which has explicit free tier limits (60 req/min for `:free` models) and
documented `X-RateLimit-*` headers in error metadata.

---

## 10. Provider Routing and Fallbacks

This is one of the richest features of Vercel AI Gateway.

### Provider-Level Routing

Configure via `providerOptions.gateway` in the request:

```json
{
  "providerOptions": {
    "gateway": {
      "order": ["bedrock", "anthropic"],
      "only": ["anthropic", "vertex"],
      "caching": "auto"
    }
  }
}
```

**`order`** — Ordered list of provider slugs to attempt. The gateway tries providers in
this order, falling back to the next if a provider fails.

**`only`** — Allowlist of providers to consider. If none in the list serve the model,
the request fails. Intersects with `order` when both are specified: only providers in
both lists are tried, in `order` sequence.

**Default behavior (no config):** Vercel dynamically selects the optimal provider based
on a combination of recent uptime and latency metrics. No deterministic default provider
is specified; Vercel's scoring system selects it.

### Model-Level Fallbacks

Specify backup models tried in order if the primary model fails:

**Via `providerOptions.gateway.models`:**

```json
{
  "model": "openai/gpt-5.2",
  "providerOptions": {
    "gateway": {
      "models": ["anthropic/claude-sonnet-4.5", "google/gemini-3-flash"]
    }
  }
}
```

**Via top-level `models` field (simpler):**

```json
{
  "model": "openai/gpt-5.2",
  "models": ["anthropic/claude-sonnet-4.5", "google/gemini-3-flash"]
}
```

**Failover logic:**

1. Try primary model via configured providers (respecting `order`)
2. If all providers for primary model fail, try first fallback model
3. Repeat for each fallback model in sequence
4. Return from first successful model/provider combination

The `model` field in the response reflects which model actually served the request.

### Combining Provider and Model Fallbacks

```json
{
  "model": "openai/gpt-5.2",
  "providerOptions": {
    "gateway": {
      "models": ["openai/gpt-5-nano", "anthropic/claude-sonnet-4.5"],
      "order": ["azure", "openai"]
    }
  }
}
```

This tries:
1. `openai/gpt-5.2` via Azure, then OpenAI
2. `openai/gpt-5-nano` via Azure, then OpenAI
3. `anthropic/claude-sonnet-4.5` via available Anthropic providers

### BYOK Failback

When BYOK credentials are configured (dashboard or per-request), the gateway uses them
first. If BYOK credentials fail, the gateway retries with its system credentials. This
provides transparent failback from BYOK to system-provisioned provider access.

---

## 11. Load Balancing

Vercel AI Gateway does not expose explicit load-balancing configuration in the API (no
`sort: "price"` or `sort: "throughput"` knobs like OpenRouter). The default routing
algorithm is an automated scoring system using recent uptime and latency data.

**Implicit load balancing behaviors:**
- Provider auto-selection based on uptime + latency scoring (undocumented algorithm)
- Multi-provider retry sequence when primary fails

**No documented equivalent to OpenRouter's `provider.sort` options** (`price`, `throughput`,
`latency`, percentile-based thresholds). Vercel's gateway is opinionated about optimal
routing and does not expose the full routing policy surface that OpenRouter does.

---

## 12. Observability and Analytics

### Dashboard Metrics

Available in the AI Gateway tab of the Vercel dashboard:

- **Requests by Model**: Chart of request counts per model over time
- **Time to First Token (TTFT)**: P-latency chart for first token delivery
- **Input/Output Token Counts**: Token volume per request
- **Spend**: Total cost over time

Retention: Standard dashboard has limited retention. Extended retention requires
**Observability Plus** (paid add-on).

### Request Logs

Detailed request-level logs available in the dashboard:

- Per-request: model, provider, token counts (all types), cost
- Grouped by project or by API key
- Sortable and exportable

### Team vs. Project Scope

Metrics can be viewed at team level (all projects aggregated) or narrowed to a
single project by selecting from the top project dropdown.

### Programmatic Observability

**Credits endpoint:**
```
GET https://ai-gateway.vercel.sh/v1/credits
Authorization: Bearer <API_GATEWAY_API_KEY>
```
Response:
```json
{ "balance": "95.50", "total_used": "4.50" }
```

**Generation lookup endpoint:**
```
GET https://ai-gateway.vercel.sh/v1/generation?id=gen_01ARZ3NDEKTSV4RRFFQ69G5FAV
Authorization: Bearer <API_GATEWAY_API_KEY>
```
Response fields:
```json
{
  "data": {
    "id": "gen_01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "total_cost": 0.00123,
    "created_at": "2024-01-01T00:00:00.000Z",
    "model": "gpt-4",
    "is_byok": false,
    "provider_name": "openai",
    "streamed": true,
    "latency": 200,
    "generation_time": 1500,
    "tokens_prompt": 100,
    "tokens_completion": 50,
    "native_tokens_prompt": 100,
    "native_tokens_completion": 50,
    "native_tokens_reasoning": 0,
    "native_tokens_cached": 0
  }
}
```

**Billing charges endpoint** (FOCUS v1.3 open-standard format, returns JSONL):
```
GET /billing/charges
```
Returns cost data with 1-day granularity. Mentioned in changelog as a new feature (2026).

---

## 13. Cost Tracking

**Zero markup policy:** AI Gateway charges provider list price. When using BYOK, there is
no additional fee. Credits are consumed at market rate.

**In-response cost data:**

Cost is NOT in the standard chat completion response body. It IS available:

1. Via `providerMetadata.gateway.cost` (AI SDK responses only) — decimal string in USD
2. Via `GET /v1/generation?id={id}` — `total_cost` and `usage` fields in USD
3. Via `/v1/models/{creator}/{model}/endpoints` — pricing metadata per model per provider
4. Via `GET /v1/models` — pricing metadata in the model list

**Cache pricing** is tracked separately: `native_tokens_cached` in generation data,
`input_cache_read` / `input_cache_write` pricing in model metadata.

**In-request cost tracking (embeddings):**

For embeddings, the response body includes `providerMetadata.gateway.cost` directly:
```json
{
  "providerMetadata": {
    "gateway": {
      "cost": "0.00000012"
    }
  }
}
```

---

## 14. Model Routing per Request

**Explicit provider routing** is the primary mechanism:

```json
{
  "model": "anthropic/claude-sonnet-4.5",
  "providerOptions": {
    "gateway": {
      "order": ["vertex", "anthropic"]
    }
  }
}
```

**Per-request BYOK** allows routing through your own provider credentials:

```json
{
  "providerOptions": {
    "gateway": {
      "byok": {
        "anthropic": [{ "apiKey": "sk-ant-..." }],
        "vertex": [
          { "project": "proj-1", "location": "us-east5", "googleCredentials": {...} },
          { "project": "proj-2", "location": "us-east5", "googleCredentials": {...} }
        ]
      }
    }
  }
}
```

Multiple credentials per provider are tried in order. Multiple providers can be specified.

**Provider slug query** (for dynamic routing configuration):

```
GET https://ai-gateway.vercel.sh/v1/models/anthropic/claude-sonnet-4.5/endpoints
```

Returns all providers that host the model with pricing, context lengths, supported parameters,
uptime, and `supports_implicit_caching` flag.

---

## 15. Unique Features vs. OpenRouter

### 1. Dual Native API Compatibility (OpenAI + Anthropic)

Vercel AI Gateway exposes both OpenAI-compatible and Anthropic-compatible endpoint surfaces:

- `POST /v1/chat/completions` — OpenAI format
- `POST /v1/messages` — Anthropic Messages API format

OpenRouter provides only an OpenAI-compatible surface (no native Anthropic endpoint).
This means tools like Claude Code can connect to Vercel AI Gateway using their native
Anthropic SDK without any translation layer.

### 2. Cross-Provider Reasoning Normalization

The `reasoning` parameter in Vercel AI Gateway is a first-class, deeply normalized
construct. It supports:

- `reasoning.enabled`, `reasoning.max_tokens`, `reasoning.effort`, `reasoning.exclude`
- Normalized `choices[].message.reasoning` (string) across all providers
- Structured `choices[].message.reasoning_details` array with type variants:
  - `reasoning.text` — plain reasoning (Anthropic)
  - `reasoning.encrypted` — encrypted/redacted reasoning (OpenAI)
  - `reasoning.summary` — condensed summary (OpenAI)
- Includes cryptographic `signature` fields from Anthropic for reasoning verification
- Provider mapping handled internally: effort → Anthropic thinking budget, OpenAI reasoningEffort, Google thinkingConfig, etc.
- Automatic extraction of reasoning from `<think>` tags for providers that use that format

OpenRouter has `reasoning.effort` and `reasoning.summary` but the normalization is less
documented and does not expose `reasoning_details` with structured type variants.

### 3. First-Class AI SDK Integration

The `@ai-sdk/gateway` package provides:

- `gateway()` function for direct use in AI SDK calls with plain strings
- `gateway.getAvailableModels()` for programmatic model discovery
- `gateway.textEmbeddingModel()` for embedding models
- `gateway.tools.perplexitySearch()` and `gateway.tools.parallelSearch()` built-in tools
- Provider metadata via `result.providerMetadata` including routing details, cost, generationId

### 4. Provider Routing Transparency (via providerMetadata)

The AI SDK response exposes the full routing decision including:
- `resolvedProvider`, `resolvedProviderApiModelId`
- `fallbacksAvailable` list
- `internalReasoning` and `planningReasoning` (text explanations)
- `attempts` array with per-attempt timing and credential type used

### 5. Per-Request Multi-Credential BYOK

The `byok` option in `providerOptions.gateway` allows passing multiple credential objects
per provider, tried in order, within a single request. This is more granular than
OpenRouter's account-level BYOK configuration.

### 6. Web Search Tools (Provider + Universal)

Two flavors:
- **Provider-native search:** Anthropic web search, OpenAI web search, Google Search grounding
- **Universal search:** `perplexitySearch` and `parallelSearch` tools work with ANY model

OpenRouter has web search via the `:online` model suffix and `plugins: [{id: "web"}]`, but
does not have the universal provider-agnostic search tools via the gateway SDK.

### 7. Video and Image Generation

Vercel AI Gateway explicitly supports image and video generation models:
- Image: Flux 2 Flex, Recraft V3, Imagen, DALL-E (via provider-specific endpoints)
- Video: Veo 3.1, KlingAI, Wan (Alibaba), Grok Imagine Video
- Model type classification in `/v1/models`: `language`, `embedding`, `image`, `video`

OpenRouter is primarily focused on language models.

### 8. Embeddings Endpoint

`POST /v1/embeddings` with automatic provider routing and `dimensions` parameter normalization
across providers (the gateway maps the root-level `dimensions` field to each provider's
expected parameter name automatically).

---

## 16. Pricing Model

**Gateway fee: zero markup**

- Free tier: Monthly free credits included when you first use AI Gateway
- Paid tier: Purchase AI Gateway Credits at any amount; no subscription required; no markup
- BYOK: Zero additional fee from Vercel when using your own provider credentials
- Provider list price is what you pay
- Payment processing fees may apply

**Credit system:**
- Balance visible in dashboard
- Auto top-up configurable with threshold + amount
- Balance viewable programmatically via `GET /v1/credits`

**Billing API:**
- `GET /billing/charges` — Returns FOCUS v1.3 format JSONL with 1-day granularity

---

## 17. Deployment Model

**SaaS only.** The Vercel AI Gateway is a fully managed, hosted service at
`https://ai-gateway.vercel.sh`. There is no self-hosted deployment option documented.

This is the fundamental architectural difference from LiteLLM (which is self-hostable)
and OpenRouter (which is also SaaS-only but positions differently).

**Infrastructure considerations:**
- No docker image / helm chart / terraform module for self-hosting
- All data flows through Vercel's infrastructure
- Observability is Vercel-dashboard-native; no OTEL export documented
- No on-premise or VPC deployment option

---

## 18. Supported API Endpoints (Complete List)

### OpenAI-Compatible (`/v1` base path)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/models` | List all available models (no auth required) |
| GET | `/v1/models/{model}` | Retrieve specific model |
| GET | `/v1/models/{creator}/{model}/endpoints` | Model provider endpoints + pricing |
| POST | `/v1/chat/completions` | Chat completions (streaming + non-streaming) |
| POST | `/v1/embeddings` | Generate vector embeddings |
| GET | `/v1/credits` | Credit balance |
| GET | `/v1/generation` | Generation lookup by ID |

### Anthropic-Compatible (root base path)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/messages` | Anthropic Messages API (streaming + non-streaming) |

### Notable Missing Endpoints (vs OpenRouter)

- No `/v1/responses` (OpenAI Responses API beta) — not documented
- No `/v1/key` (auth key introspection / credit status beyond `/v1/credits`)
- No `/v1/keys` management API
- No `/billing/charges` in the OpenAI-compat path (separate Vercel billing API)

---

## 19. Framework Integrations

The following frameworks have documented integrations with Vercel AI Gateway:

- **Vercel AI SDK** (first-class, native `@ai-sdk/gateway` package)
- **LangChain** (via OpenAI-compat endpoint)
- **LangFuse** (observability integration)
- **LiteLLM** (can route through Vercel AI Gateway)
- **LlamaIndex** (via OpenAI-compat endpoint)
- **Mastra** (AI agent framework)
- **Pydantic AI** (Python AI SDK)
- **OpenAI SDK** (TypeScript + Python, full compatibility)
- **Anthropic SDK** (TypeScript + Python, via Anthropic-compat endpoint)

---

## 20. Recent Changes (2025-2026, from Changelog)

- **Video generation models added**: Grok Imagine Video, Wan (Alibaba), Kling 3.0, Veo 3.x
- **Gemini 3.1 Pro**: Added with `medium` thinking level
- **Billing API (`/billing/charges`)**: New programmatic cost endpoint (FOCUS v1.3 format, JSONL)
- **Private Blob Storage**: Adjacent feature; not AI Gateway direct
- **App Attribution**: `http-referer` + `x-title` headers for app visibility on AI Gateway pages

---

## 21. Gap Analysis: Vercel AI Gateway vs. thegent CLIProxy

### Context

thegent's CLIProxy (`cliproxy_adapter.py`) is a Starlette ASGI app that:
- Listens on port 8317, proxies to CLIProxyAPIPlus on port 8318
- Translates OpenAI Responses API (`/v1/responses`) to Chat Completions
- Enriches `/v1/models` with Codex-specific metadata
- Bridges WebSocket `/v1/responses` for Codex CLI
- Has no direct knowledge of Vercel AI Gateway as a backend or surface

### Gap Table

| Feature | Vercel AI Gateway | thegent CLIProxy | Gap / Status |
|---------|-------------------|------------------|--------------|
| **Base URL** | `https://ai-gateway.vercel.sh/v1` | `http://127.0.0.1:8317/v1` | **GAP (P0):** No routing path to Vercel AI Gateway. Must add as backend target. |
| **Auth method** | `Authorization: Bearer <AI_GATEWAY_API_KEY>` | Passes headers through unchanged | **GAP (P0):** No `AI_GATEWAY_API_KEY` injection. Client must supply key or middleware must inject from env. |
| **Anthropic-compat endpoint** | `POST /v1/messages` at `ai-gateway.vercel.sh` | Not exposed | **GAP (P1):** Proxy does not expose an Anthropic-format endpoint. Tools like Claude Code using native Anthropic SDK cannot benefit from proxy routing without this. |
| **Model ID format** | `provider/model-name` (e.g. `anthropic/claude-sonnet-4.5`) | thegent catalog IDs (e.g. `claude-sonnet-4.5`) passed through, some mapping in `harness_model_mapping.py` | **GAP (P0):** No mapping from thegent catalog IDs to Vercel AI Gateway format. Requests with bare model names will fail. |
| **Provider routing (`providerOptions.gateway.order`)** | Per-request provider ordering | Not implemented | **GAP (P1):** No pass-through or injection of `providerOptions.gateway` routing fields. In body-reconstruction mode (transform path) these are silently dropped. |
| **Model fallbacks (`models` array)** | Top-level `models` field and `providerOptions.gateway.models` | Not implemented | **GAP (P1):** No pass-through or injection of model fallback arrays. |
| **Reasoning (`reasoning` object)** | Normalized cross-provider `reasoning` parameter | Not implemented | **GAP (P1):** The `reasoning` request field is not forwarded in the transform path. |
| **BYOK per-request (`providerOptions.gateway.byok`)** | Pass per-request credentials for any provider | Not implemented | **GAP (P1):** No BYOK credential injection mechanism. |
| **Caching (`providerOptions.gateway.caching: 'auto'`)** | Auto cache_control insertion for Anthropic | Not implemented | **GAP (P2):** No auto caching orchestration. Manual `cache_control` markers flow through if body not reconstructed. |
| **Reasoning response fields** | `choices[].message.reasoning`, `choices[].message.reasoning_details` | Not forwarded | **GAP (P1):** Proxy's `_extract_delta_content` only reads `delta.content`; `delta.reasoning` and `delta.reasoning_details` are dropped in transform mode. |
| **Cost in response** | `providerMetadata.gateway.cost` (AI SDK), `GET /v1/generation` | Not tracked | **GAP (P1):** No cost data returned. Would need generation lookup forwarding and/or cost metadata injection. |
| **Generation lookup endpoint** | `GET /v1/generation?id={id}` | Not proxied | **GAP (P2):** Users cannot look up per-request cost data. |
| **Credits endpoint** | `GET /v1/credits` | Not proxied | **GAP (P2):** No balance introspection forwarding. |
| **Embeddings endpoint** | `POST /v1/embeddings` | Not explicitly handled (passes through to backend) | **PARTIAL:** Passes through but no Vercel AI Gateway routing awareness or cost tracking. |
| **Models endpoint format** | OpenAI format `{"object":"list","data":[...]}` with pricing, type, tags | Codex format `{"models":[...], "fetched_at":..., "client_version":...}` | **GAP (P0 when acting as Vercel):** Format incompatible. If clients expect Vercel AI Gateway model format (with pricing, type, tags), the current Codex enrichment format is wrong. |
| **Model metadata in /v1/models** | `type`, `tags`, `context_window`, `max_tokens`, `pricing` per model | Codex-specific fields (`slug`, `shell_type`, `supported_reasoning_levels`, etc.) | **GAP (P1):** No pricing, type, or tags in model objects. |
| **`/v1/models/{creator}/{model}/endpoints`** | Per-model provider list with pricing and metrics | Not implemented | **GAP (P2):** Endpoint not proxied. |
| **Anthropic `POST /v1/messages`** | Full Anthropic Messages API | Not exposed | **GAP (P1):** Proxy does not expose `/v1/messages` at all. Claude Code connecting via native Anthropic SDK cannot use the proxy. |
| **Streaming — no provider field in chunks** | Vercel does NOT add `provider` field to SSE chunks | Proxy passes chunks through (no `provider` added either) | **OK (compatible):** Both omit `provider` from chunks. Distinct from OpenRouter which adds it. |
| **Streaming — no SSE comments** | No keep-alive comment lines | Proxy emits no comment lines | **OK (compatible)** |
| **SSE `data: [DONE]`** | Standard `data: [DONE]` terminator | Proxy passes through or emits | **OK** |
| **Tool call streaming** | Standard `delta.tool_calls` | Dropped in transform mode | **GAP (P1):** Same issue as documented in OpenRouter gap analysis — applies equally here. |
| **Error format** | Standard OpenAI format `{"error":{"message":"...","type":"...","param":"...","code":"..."}}` | Proxy emits `{"error":{"message":"..."}}` (no type/param/code) | **GAP (P1):** Missing `type`, `param`, `code` fields in error objects. |
| **TLS verification** | HTTPS to `ai-gateway.vercel.sh` required | `_proxy_request` uses `verify=False` | **GAP (P0):** TLS verification disabled; must use `verify=True` for Vercel AI Gateway backend. |
| **Attribution headers** | `http-referer` + `x-title` optional | Not injected | **GAP (P2):** No thegent identity headers sent. Low priority. |
| **OIDC token authentication** | `Authorization: Bearer <VERCEL_OIDC_TOKEN>` | No OIDC awareness | **GAP (P2):** For Vercel-native deployments, OIDC is more convenient than API key. Not critical for standalone thegent use. |
| **Automatic provider selection** | Dynamic uptime/latency scoring | No comparable mechanism | **GAP (P2):** thegent has static model routing; no dynamic provider health scoring. |
| **Web search tools** | `perplexitySearch`, `parallelSearch`, provider-native search | Not implemented | **GAP (P2):** These are AI SDK features; not relevant to the proxy layer directly. |
| **Image/Video generation** | Full `language`, `embedding`, `image`, `video` model types | Not typed; any model request proxied uniformly | **GAP (P2):** No model type awareness for routing image/video generation requests differently. |
| **Self-hosting** | SaaS only | thegent is self-hosted | **N/A:** Different deployment model. thegent proxy is self-hosted, which is actually a competitive advantage for organizations that cannot use external SaaS. |

### Priority Summary

**P0 — Required for basic Vercel AI Gateway compatibility:**

1. Add Vercel AI Gateway backend target URL (`https://ai-gateway.vercel.sh/v1`)
2. Add `AI_GATEWAY_API_KEY` injection when Vercel AI Gateway is the backend
3. Add `"vercel-gateway"` provider type to `API_KEY_PROVIDERS` (analogous to `openrouter`)
4. Fix TLS verification (`verify=True` for HTTPS backends)
5. Add thegent-to-Vercel model ID mapping (`claude-sonnet-4.5` → `anthropic/claude-sonnet-4.5`)

**P1 — Required for production-quality Vercel AI Gateway proxying:**

6. Pass through `providerOptions.gateway` fields (routing order, only, models, caching) without dropping them in transform mode
7. Pass through `reasoning` request field without dropping in transform mode
8. Extract and forward `delta.reasoning` and `delta.reasoning_details` in streaming
9. Add `choices[].message.reasoning` and `reasoning_details` to non-streaming response
10. Expose `POST /v1/messages` (Anthropic-compat) endpoint to allow Anthropic SDK clients
11. Add `type`, `tags`, `pricing` fields to model objects in `/v1/models` response
12. Fix error format: add `type`, `param`, `code` fields

**P2 — Polish and completeness:**

13. Proxy `GET /v1/generation?id=` for post-request cost lookup
14. Proxy `GET /v1/credits` for balance introspection
15. Add `http-referer` + `x-title` injection for app attribution
16. Add OIDC token authentication option
17. Add `GET /v1/models/{creator}/{model}/endpoints` proxy

### Features Where thegent Has Advantage Over Vercel AI Gateway

1. **Self-hostable:** thegent runs in the user's own infrastructure. Vercel AI Gateway is SaaS-only. This is critical for enterprises with data residency or compliance requirements.
2. **Codex CLI compatibility:** thegent has native Codex `/v1/responses` support (including WebSocket bridge). Vercel AI Gateway has no `/v1/responses` endpoint documented.
3. **Context window enrichment:** thegent enriches model metadata with Codex-specific fields that Codex CLI requires.
4. **Existing OpenRouter support path:** thegent's gap analysis for OpenRouter is already documented; Vercel AI Gateway can reuse much of the same infrastructure once added.

---

## Sources

- Vercel AI Gateway main docs: https://vercel.com/docs/ai-gateway
- Getting started: https://vercel.com/docs/ai-gateway/getting-started
- Models & Providers: https://vercel.com/docs/ai-gateway/models-and-providers
- Provider Options: https://vercel.com/docs/ai-gateway/models-and-providers/provider-options
- Model Fallbacks: https://vercel.com/docs/ai-gateway/models-and-providers/model-fallbacks
- OpenAI Compatibility: https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-compat
- OpenAI Chat Completions: https://vercel.com/docs/ai-gateway/openai-compat/chat-completions
- OpenAI Advanced: https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-compat/advanced
- Anthropic Compatibility: https://vercel.com/docs/ai-gateway/sdks-and-apis/anthropic-compat
- Anthropic Advanced: https://vercel.com/docs/ai-gateway/sdks-and-apis/anthropic-compat/advanced
- Authentication: https://vercel.com/docs/ai-gateway/authentication-and-byok/authentication
- BYOK: https://vercel.com/docs/ai-gateway/authentication-and-byok/byok
- Observability: https://vercel.com/docs/ai-gateway/capabilities/observability
- Usage & Billing: https://vercel.com/docs/ai-gateway/capabilities/usage
- Web Search: https://vercel.com/docs/ai-gateway/capabilities/web-search
- Pricing: https://vercel.com/docs/ai-gateway/pricing
- App Attribution: https://vercel.com/docs/ai-gateway/ecosystem/app-attribution
- Framework Integrations: https://vercel.com/docs/ai-gateway/ecosystem/framework-integrations
- Vercel Changelog: https://vercel.com/changelog
