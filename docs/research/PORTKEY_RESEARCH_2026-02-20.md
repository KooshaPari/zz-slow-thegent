<DONE>
# Portkey AI Gateway — Exhaustive Research

**Date:** 2026-02-20
**Purpose:** Provider audit for thegent CLIProxy feature-parity analysis
**Sources:** portkey.ai/docs, GitHub Portkey-AI/gateway, helicone.ai comparison, truefoundry.com comparison, getmaxim.ai

---

## 1. What is Portkey

Portkey is a production-grade AI Gateway and LLMOps control plane built for GenAI workloads at enterprise scale. It sits between your application and LLM providers, adding routing, reliability, security, observability, and governance as a transparent middleware layer.

Key identity markers:

- "Control Panel for Production AI" (their tagline)
- **Managed SaaS** (default) + **Open-source self-hosted gateway** (separate tier)
- 250+ models, 45+ providers, 1,600+ total model variants
- OpenAI SDK drop-in compatible (change `base_url`, add headers)
- Battle-tested: 300B+ tokens, 25M+ daily requests, 99.99% uptime
- ~45KB installed footprint, 9.9x faster than naive implementations
- ~10,000+ GitHub stars on open-source gateway
- Recognized as Gartner Cool Vendor in LLM Observability (2025)
- **Series A: $15M raised February 19, 2026**

---

## 2. Architecture and Deployment Options

### 2.1 Open-Source Gateway (OSS)

GitHub: `Portkey-AI/gateway`

The OSS gateway is a Node.js/TypeScript edge-compatible proxy. It handles routing, fallbacks, load balancing, caching, and basic guardrails — but **without** observability persistence, prompt management, virtual keys, RBAC, or the control-plane SaaS features.

Install methods:

```bash
# Docker
docker pull portkeyai/gateway
docker run -p 8787:8787 portkeyai/gateway

# Node.js
npx @portkey-ai/gateway

# Deploy to: Cloudflare Workers, Replit, Koyeb, Railway, Render, etc.
```

Gateway console at: `http://localhost:8787/public/`

OSS gateway is latest version 1.8.2 as of research date.

### 2.2 Portkey-Managed SaaS

- Fully managed on Portkey's infrastructure
- Isolated cluster per enterprise org
- All observability, prompt management, virtual keys, RBAC available
- Data plane hosted by Portkey

Base URL for managed: `https://api.portkey.ai/v1`

### 2.3 Hybrid Deployment (Enterprise)

- AI Gateway + data plane run in **customer's VPC**
- Control plane managed by Portkey
- Sensitive LLM data (prompts, responses) never leaves customer's network
- Gateway still benefits from Portkey's routing logic and config updates

### 2.4 Fully Airgapped Deployment (Enterprise)

- All components (data plane, control plane, AI Gateway) inside customer infrastructure
- Zero data leaves customer's network
- Supports: AWS, GCP, Azure private VPC
- VPC peering and private network connectivity available

---

## 3. Authentication

### 3.1 Portkey API Key

Primary authentication credential. Used to identify your Portkey account.

Header: `x-portkey-api-key: <YOUR_PORTKEY_API_KEY>`

### 3.2 Provider Authentication

Two methods:

**Direct provider key** (simpler, less secure):

```
x-portkey-provider: openai
x-portkey-api-key: <PORTKEY_KEY>
Authorization: Bearer <OPENAI_API_KEY>
```

**Virtual Key / AI Provider slug** (recommended):

```
x-portkey-virtual-key: my-openai-prod-vk
```

or with model catalog:

```
model: "@openai-prod/gpt-4o"
```

### 3.3 Full x-portkey-\* Header Inventory

| Header                          | Type        | Purpose                                            |
| ------------------------------- | ----------- | -------------------------------------------------- |
| `x-portkey-api-key`             | string      | Portkey account authentication                     |
| `x-portkey-provider`            | string      | Direct provider name (e.g., "openai", "anthropic") |
| `x-portkey-virtual-key`         | string      | Virtual key slug (legacy)                          |
| `x-portkey-config`              | string/json | Config ID or inline JSON config object             |
| `x-portkey-trace-id`            | string      | Custom trace ID for observability                  |
| `x-portkey-span-id`             | string      | Span ID for distributed tracing                    |
| `x-portkey-parent-span-id`      | string      | Parent span for nested traces                      |
| `x-portkey-span-name`           | string      | Human-readable span label                          |
| `x-portkey-metadata`            | json object | Custom key-value pairs attached to logs            |
| `x-portkey-cache-namespace`     | string      | Custom cache partition key (e.g., user ID)         |
| `x-portkey-cache-force-refresh` | boolean     | Bypass cache and re-fetch                          |
| `x-portkey-debug`               | boolean     | Enable debug mode (must be true for caching)       |
| `x-portkey-forward-headers`     | array       | List of headers to forward to provider             |
| `x-portkey-input-guardrails`    | string      | Guardrail ID for input checking                    |
| `x-portkey-output-guardrails`   | string      | Guardrail ID for output checking                   |

W3C standard `traceparent` and `baggage` headers are also supported for OTel compatibility; Portkey-specific headers take precedence if both present.

---

## 4. OpenAI SDK Compatibility

Portkey is a drop-in replacement. Change `base_url` and add headers:

### Python (OpenAI SDK)

```python
from openai import OpenAI
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders

client = OpenAI(
    api_key="OPENAI_API_KEY",  # or can be anything if using virtual keys
    base_url=PORTKEY_GATEWAY_URL,  # https://api.portkey.ai/v1
    default_headers=createHeaders(api_key="PORTKEY_API_KEY", provider="openai"),
)

response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Hello"}])
```

### Python (Portkey native SDK)

```python
from portkey_ai import Portkey

portkey = Portkey(api_key="PORTKEY_API_KEY", virtual_key="my-openai-vk")

response = portkey.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Hello"}])
```

### JavaScript/TypeScript (OpenAI SDK)

```typescript
import OpenAI from "openai";
import { PORTKEY_GATEWAY_URL, createHeaders } from "portkey-ai";

const client = new OpenAI({
  apiKey: "OPENAI_API_KEY",
  baseURL: PORTKEY_GATEWAY_URL,
  defaultHeaders: createHeaders({
    apiKey: "PORTKEY_API_KEY",
    provider: "openai",
  }),
});
```

### Vercel AI SDK

```typescript
import { createPortkey } from "@portkey-ai/vercel-provider";
import { streamText } from "ai";

const portkey = createPortkey({
  apiKey: "PORTKEY_API_KEY",
  provider: "openai",
  overrideParams: { model: "gpt-4o" },
});

const result = await streamText({
  model: portkey.chatModel("gpt-4o"),
  prompt: "Hello",
});
```

### cURL

```bash
curl https://api.portkey.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-portkey-api-key: PORTKEY_API_KEY" \
  -H "x-portkey-provider: openai" \
  -H "Authorization: Bearer OPENAI_API_KEY" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## 5. Config Object — The Core Abstraction

The Config Object is Portkey's primary routing/reliability/caching/guardrail configuration artifact. It is JSON and can be:

1. Created in the Portkey UI and referenced by ID (`x-portkey-config: config_id`)
2. Passed inline as JSON in the `x-portkey-config` header
3. Applied as a default to a Virtual Key or AI Provider

### 5.1 Config Schema (simplified)

```json
{
  "strategy": {
    "mode": "single" | "fallback" | "loadbalance" | "conditional",
    "on_status_codes": [429, 500, 503],
    "conditions": [...],
    "default": "target_name"
  },
  "targets": [
    {
      "name": "target_name",
      "provider": "@provider-slug",
      "virtual_key": "vk-slug",
      "api_key": "sk-...",
      "custom_host": "http://localhost:11434",
      "weight": 0.7,
      "override_params": {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 2000
      },
      "forward_headers": ["x-custom-header"],
      "cache": { "mode": "semantic", "max_age": 3600 },
      "retry": { "attempts": 3, "on_status_codes": [429] },
      "request_timeout": 30000,
      "input_guardrails": ["guardrail_id_1"],
      "output_guardrails": ["guardrail_id_2"]
    }
  ],
  "cache": { "mode": "simple", "max_age": 604800 },
  "retry": { "attempts": 3, "use_retry_after_headers": true },
  "request_timeout": 60000,
  "cb_config": {
    "failure_threshold": 5,
    "cooldown_interval": 60000,
    "failure_status_codes": [500, 503]
  }
}
```

Key rules:

- `targets` is recursive — each target can itself be a full config (enabling nested strategies)
- Target-level settings override top-level settings
- `strategy.mode` defaults to `single` if omitted and one target is present

---

## 6. Routing Strategies

### 6.1 Single Provider (Default)

Direct routing to one provider/model:

```json
{
  "provider": "@openai-prod",
  "override_params": { "model": "gpt-4o" }
}
```

### 6.2 Fallback Routing

Sequential: try each target in order; trigger on configured HTTP status codes.

```json
{
  "strategy": {
    "mode": "fallback",
    "on_status_codes": [429, 500, 503]
  },
  "targets": [
    { "provider": "@openai-primary" },
    {
      "provider": "@anthropic-backup",
      "override_params": { "model": "claude-3-5-sonnet" }
    },
    { "provider": "@azure-openai-tertiary" }
  ]
}
```

### 6.3 Load Balancing

Weighted distribution across targets:

```json
{
  "strategy": { "mode": "loadbalance" },
  "targets": [
    { "provider": "@openai-prod", "weight": 0.7 },
    { "provider": "@openai-backup", "weight": 0.2 },
    { "provider": "@azure-openai", "weight": 0.1 }
  ]
}
```

Weights represent relative traffic share (not required to sum to 1.0 — they are ratios).

### 6.4 Conditional Routing

Route based on metadata values or request parameters:

```json
{
  "strategy": {
    "mode": "conditional",
    "conditions": [
      {
        "query": { "metadata.user_plan": { "$eq": "enterprise" } },
        "then": "premium-target"
      },
      {
        "query": {
          "$and": [
            { "metadata.user_type": { "$eq": "pro" } },
            { "params.temperature": { "$gte": 0.7 } }
          ]
        },
        "then": "creative-target"
      }
    ],
    "default": "standard-target"
  },
  "targets": [
    {
      "name": "premium-target",
      "provider": "@anthropic",
      "override_params": { "model": "claude-3-5-opus" }
    },
    {
      "name": "creative-target",
      "provider": "@openai",
      "override_params": { "model": "gpt-4o" }
    },
    {
      "name": "standard-target",
      "provider": "@openai",
      "override_params": { "model": "gpt-4o-mini" }
    }
  ]
}
```

**Supported condition operators:**

| Operator | Meaning                           |
| -------- | --------------------------------- |
| `$eq`    | Equals                            |
| `$ne`    | Not equals                        |
| `$in`    | In array                          |
| `$nin`   | Not in array                      |
| `$regex` | JavaScript regex (case-sensitive) |
| `$gt`    | Greater than                      |
| `$gte`   | Greater than or equal             |
| `$lt`    | Less than                         |
| `$lte`   | Less than or equal                |
| `$and`   | All subconditions true            |
| `$or`    | Any subcondition true             |

**Condition query paths:**

- `metadata.<key>` — custom metadata attached to the request
- `params.<key>` — request body parameters (model, temperature, max_tokens, etc.)
- `url.pathname` — full request URL path matching

**Limitations:**

- Only two-segment keys: `metadata.user_plan` works; `metadata.features.new_model` does not
- Only primitive types (string, number, boolean) in conditions
- Conditions evaluated sequentially; first match wins

### 6.5 Nested Strategies (Combined)

Targets can contain full sub-configs, enabling load balance with nested fallback:

```json
{
  "strategy": { "mode": "loadbalance" },
  "targets": [
    {
      "provider": "@anthropic",
      "override_params": { "model": "claude-3-5-sonnet" },
      "weight": 0.5
    },
    {
      "strategy": { "mode": "fallback" },
      "targets": [
        { "provider": "@openai", "override_params": { "model": "gpt-4o" } },
        {
          "provider": "@azure-openai",
          "override_params": { "model": "gpt-4o" }
        }
      ],
      "weight": 0.5
    }
  ]
}
```

### 6.6 Custom Host Routing (Local/Private Models)

```json
{
  "provider": "openai",
  "custom_host": "http://localhost:11434/v1",
  "api_key": "ollama"
}
```

---

## 7. Retry and Timeout Configuration

### 7.1 Retry

```json
{
  "retry": {
    "attempts": 5,
    "on_status_codes": [429, 500, 502, 503, 504],
    "use_retry_after_headers": true
  }
}
```

- Max 5 attempts
- Exponential backoff applied automatically
- `use_retry_after_headers`: honors provider's `Retry-After` header

### 7.2 Request Timeout

```json
{ "request_timeout": 30000 }
```

Value in milliseconds. Applied per-request. Triggers fallback if configured.

### 7.3 Circuit Breaker (`cb_config`)

```json
{
  "cb_config": {
    "failure_threshold": 5,
    "cooldown_interval": 60000,
    "failure_status_codes": [500, 502, 503],
    "minimum_requests": 10,
    "failure_threshold_percentage": 50
  }
}
```

- `failure_threshold`: absolute failure count before circuit opens
- `failure_threshold_percentage`: % failure rate before circuit opens
- `cooldown_interval`: min 30000ms (30 seconds); time before circuit closes
- `minimum_requests`: requests before failure rate is evaluated
- Default failure codes: all >500 (if `failure_status_codes` omitted)
- When open: all requests to that target are blocked until cooldown passes
- Child strategies inherit `cb_config` from parent if not set

---

## 8. Caching

### 8.1 Simple Cache

Exact match on request content (prompt + model + params).

```json
{ "cache": { "mode": "simple" } }
```

- Available on all plans (including free with 1-day TTL)
- Works with all models including image generation
- Stores exact prompt/response pairs

### 8.2 Semantic Cache

Fuzzy match using cosine similarity on prompt embeddings. Catches semantically equivalent queries.

```json
{ "cache": { "mode": "semantic", "max_age": 7200 } }
```

- Requires Pro or Enterprise plan
- Uses a vector database internally
- "Semantic cache is a superset — it handles simple cache hits too"
- Constraint: requests must have ≤ 8,191 tokens and ≤ 4 messages
- System message is ignored during similarity matching (can change system prompt without busting cache)

### 8.3 TTL Configuration

```json
{ "cache": { "mode": "simple", "max_age": 3600 } }
```

| Bound         | Value                                                            |
| ------------- | ---------------------------------------------------------------- |
| Minimum       | 60 seconds                                                       |
| Maximum       | 90 days (7,776,000 seconds)                                      |
| Default       | 7 days (604,800 seconds)                                         |
| Free plan cap | 1 day (86,400 seconds)                                           |
| Org-max TTL   | 25,923,000 seconds (settable in Admin → Organization Properties) |

TTL precedence: request `max_age` honored unless it exceeds org-level cap (org cap wins).

### 8.4 Cache Namespace (Per-User Caching)

Override default cache partitioning (which uses all headers) with a custom string key:

```python
portkey.chat.completions.create(..., cache_namespace="user-123")
```

```bash
curl ... -H "x-portkey-cache-namespace: user-123"
```

Cache is partitioned solely by this namespace string — all other headers ignored. Useful for per-user caches or to boost hit rates by ignoring unimportant headers.

### 8.5 Force Refresh

Bypass cache for a specific request:

```python
portkey.chat.completions.create(..., cache_force_refresh=True)
```

```bash
curl ... -H "x-portkey-cache-force-refresh: true"
```

Note: cache config must be active; semantic force-refreshes affect all matching entries.

### 8.6 Cache Analytics

Dashboard shows: Cache Hit, Cache Semantic Hit, Cache Miss, Cache Refreshed, Cache Disabled per request.

---

## 9. Guardrails

### 9.1 Overview

Guardrails run before (input hook) and/or after (output hook) each LLM call. They can:

- Block the request (return error to caller)
- Log violations but allow through
- Transform/redact the request or response
- Trigger fallback to alternate target

### 9.2 Native Guardrails (Deterministic — All Plans)

| Check               | Parameters                                      | Hook         |
| ------------------- | ----------------------------------------------- | ------------ |
| Regex Match         | `rule: string`                                  | input/output |
| Sentence Count      | `minSentences, maxSentences: number`            | input/output |
| Word Count          | `minWords, maxWords: number`                    | input/output |
| Character Count     | `minCharacters, maxCharacters: number`          | input/output |
| JSON Schema         | `schema: json`                                  | output only  |
| JSON Keys           | `keys: array; operator: string`                 | output only  |
| Contains            | `words: array; operator: string`                | output only  |
| Valid URLs          | `onlyDNS: boolean`                              | output only  |
| Contains Code       | `format: string` (SQL, Python, etc.)            | output only  |
| Lowercase Detection | `format: string`                                | input/output |
| Ends With           | `Suffix: string`                                | input/output |
| Webhook (BYOG)      | `webhookURL: string; headers: json`             | input/output |
| JWT Token Validator | JWKS signature, introspection, claim validation | input only   |
| Model Whitelist     | `Models: array; Inverse: boolean`               | input only   |

### 9.3 LLM-Based Guardrails (Pro/Enterprise Plans)

| Check            | Parameters          | Hook         |
| ---------------- | ------------------- | ------------ |
| Moderate Content | `categories: array` | input only   |
| Check Language   | `language: string`  | input only   |
| Detect PII       | `categories: array` | input/output |
| Detect Gibberish | `boolean`           | input/output |

### 9.4 Partner Guardrail Integrations (13 Partners)

| Partner                    | Key Capabilities                                                        |
| -------------------------- | ----------------------------------------------------------------------- |
| **Acuvity**                | PII detection, toxicity, prompt injection                               |
| **Aporia**                 | Custom policy validation via Aporia project ID                          |
| **AWS Bedrock Guardrails** | PII redaction, content safety, jailbreak detection, copyright detection |
| **Azure Content Safety**   | PII redaction, jailbreak/injection detection, Protected Material        |
| **Javelin**                | GenAI/Agent/MCP security, visibility, emerging threats                  |
| **Lasso Security**         | Security risk analysis, jailbreak detection, custom policies            |
| **Mistral Moderation**     | Harmful content filtering, multi-dimensional safety                     |
| **Pangea Text Guard**      | Input/output protection, malicious content, model manipulation          |
| **Palo Alto Prisma AIRS**  | Real-time threat detection across OSI layers 1-7, DoS blocking          |
| **Patronus AI**            | Hallucination detection, factual error, bias, quality evaluation        |
| **Pillar**                 | Comprehensive scanning, PII/toxicity/injection, enterprise security     |
| **Prompt Security**        | Vulnerability scanning, policy violations, advanced threats             |
| **Qualifire**              | Agent/RAG/chatbot evaluation, hallucination, grounding                  |

### 9.5 Bring Your Own Guardrails (Webhook)

Custom webhook integration:

```json
{
  "type": "webhook",
  "webhookURL": "https://your-guardrail-service.com/check",
  "headers": { "Authorization": "Bearer token" }
}
```

Portkey POSTs request/response data to your URL. Expected response:

```json
{
  "verdict": true,
  "data": {
    "transformedData": "...modified content..."
  }
}
```

- `verdict: true` = PASS, `false` = FAIL
- Webhook timeout: hardcoded 3 seconds; timeout = PASS (to avoid blocking)
- Enterprise: can configure webhooks within private VPC networks

### 9.6 Guardrail Actions

When a guardrail fires:

- **Block**: Return error to caller (configurable error message)
- **Log**: Record violation, allow request to proceed
- **Override**: Substitute transformed content
- **Fallback**: Route to alternate target

### 9.7 Guardrail in Config

```json
{
  "targets": [
    {
      "provider": "@openai-prod",
      "input_guardrails": ["pg-pii-detector-abc123"],
      "output_guardrails": ["pg-fact-checker-xyz789"]
    }
  ]
}
```

---

## 10. Observability

### 10.1 Logs

Every request produces a structured log containing:

- Timestamp, user, application identifier
- Full prompt and response content
- Provider, model, and routing decisions
- Latency (time-to-first-token + total)
- Cost (calculated from provider pricing)
- Token counts (input, output, total)
- Custom metadata and tags
- Cache hit/miss status
- Guardrail violations or errors
- Retry attempts and fallback activations

Log retention: 3 days (Dev), 30 days (Pro), custom (Enterprise).

### 10.2 Traces

Hierarchical view of multi-step execution (especially for agents):

- Sequence of LLM calls, tool invocations, state transitions
- Each span: inputs, outputs, model, temperature, token usage, latency, status
- Spans linked by trace ID and parent span ID
- Custom span names and metadata attachable

### 10.3 OpenTelemetry (OTel) Integration

Portkey exposes an OTLP HTTP endpoint:

```
https://api.portkey.ai/v1/otel
```

- Send existing OTel instrumentation directly to Portkey
- W3C `traceparent` and `baggage` headers accepted
- OTel trace/span IDs automatically extracted and correlated with LLM logs
- Enables "single connected stream" of infrastructure + LLM observability
- Agent frameworks can send traces; Portkey enriches with LLM call details

### 10.4 Metrics (40+ tracked)

Key metrics monitored:

- Request count, error rate, latency (p50, p95, p99)
- Cost per request, cost per token, total spend
- Cache hit rate, cache savings
- Guardrail violation rates
- Fallback activation rates
- Token usage by model/provider/workspace

### 10.5 Cost Analytics

- Automatic cost attribution using built-in pricing database (2,000+ models tracked)
- Cost breakdown by workspace, team, user, model, provider
- FinOps dashboards available in Enterprise
- `$93M+ in LLM spends tracked` (per Portkey's 2026 blog post)

### 10.6 Feedback API

Collect human evaluation signals linked to logs:

```python
portkey.feedback.create(
    trace_id="trace_id_from_response",
    value=1,  # 1 = thumbs up, -1 = thumbs down
    weight=1,
)
```

Feedback is visible in the logs UI with count and value:weight pairs per trace.

### 10.7 Custom Metadata

Attach arbitrary key-value pairs to any request for filtering/segmentation:

```python
portkey.chat.completions.create(..., metadata={"user_id": "user_123", "environment": "production", "feature": "search"})
```

---

## 11. Virtual Keys and Model Catalog

### 11.1 Virtual Keys (Legacy → Now "AI Providers")

Virtual Keys store encrypted provider credentials in Portkey's vault (AES-256), so actual API keys are never exposed in code. As of late 2025, Virtual Keys have been migrated to the **Model Catalog** system and renamed to "AI Providers" — but all existing slugs and code remain backward compatible.

Slug format: `@my-openai-prod` — used in configs and the `@provider/model` syntax.

### 11.2 Model Catalog (Current System)

Replaces Virtual Keys with a richer governance layer:

- **Org-level provider integrations**: Create credentials once, provision to multiple workspaces
- **`@provider_slug/model_name` syntax**: e.g., `@openai-prod/gpt-4o`, `@anthropic/claude-3-5-sonnet`
- **Model allowlists**: Define which models each workspace/team can access
- **Budget limits**: Per-integration spend caps (USD) — auto-expires key when limit reached
- **Rate limits**: Per-integration request rate caps
- **Custom models**: Fine-tuned models, self-hosted models, private models — all get same governance
- **Auto-enable new models**: Optionally surface new provider releases automatically

### 11.3 Budget and Rate Limits

- Budget limits in USD: key auto-expires at limit (currently Enterprise only for API-enforced budgets)
- Rate limits: requests per minute/hour/day per key
- Granular budgets per team/workspace/department
- Usage tracking and spend visibility

### 11.4 Access Control

- RBAC: Owner, Admin, Member, Viewer roles
- Workspace-level isolation
- Key scoping: organization API keys with specific permission scopes

---

## 12. Prompt Management (Prompt Engineering Studio)

### 12.1 Capabilities

- Centralized prompt storage (up to 3 in Dev, unlimited in Pro/Enterprise)
- Version control: every edit creates a new version
- Publish/unpromote: publishing makes a version "production"
- Labels: custom labels like `platform-team`, `staging`, `production` attachable to any version
- A/B testing: label-based traffic control between versions
- Template variables: dynamic `{{variable_name}}` placeholders in prompts
- Prompt partials: reusable prompt fragments (snippets)
- Comparison view: side-by-side version comparison

### 12.2 Prompt API

Call prompts by ID with variable substitution:

```python
portkey.prompts.completions.create(
    prompt_id="pp-my-prompt-abc", variables={"user_name": "Alice", "topic": "machine learning"}
)
```

### 12.3 Environment Promotion

Prompts can be promoted through dev → staging → production using label-based routing. Different config versions or API callers can target specific labeled versions.

### 12.4 Playground

- Multimodal playground (text, vision, audio)
- Side-by-side model comparison
- User access controls per prompt

---

## 13. Multimodal Capabilities

All available through the unified API:

| Modality                  | Supported                                                  |
| ------------------------- | ---------------------------------------------------------- |
| Chat completions          | Yes — all text providers                                   |
| Text completions (legacy) | Yes                                                        |
| Embeddings                | Yes — all embedding providers                              |
| Vision (image input)      | Yes — OpenAI GPT-4V, Anthropic Claude, Google Gemini, etc. |
| Image generation          | Yes — DALL-E, Stable Diffusion, etc.                       |
| Text-to-speech            | Yes — OpenAI TTS, ElevenLabs, etc.                         |
| Speech-to-text            | Yes — OpenAI Whisper, etc.                                 |
| Realtime API (WebSockets) | Yes — OpenAI Realtime API through integrated WS server     |

All modalities benefit from routing, fallbacks, load balancing, guardrails, and observability.

---

## 14. MCP Gateway

A new capability (announced 2025-2026):

- Portkey acts as an **MCP client** connecting to MCP servers
- Provides unified authentication layer for all MCP tool calls
- Access control: which teams/users can access which MCP servers/tools
- Instant revocation of MCP server access
- Every tool call logged with full context (who, what, parameters, response, latency)
- Header forwarding for distributed tracing and tenant context
- Integrates with agent frameworks: LangChain, LlamaIndex, CrewAI, AutoGen, etc.

---

## 15. Agent Framework Integrations

Native SDKs/integrations for:

- LangChain (Python + JS)
- LlamaIndex
- CrewAI
- AutoGen (Microsoft)
- Vercel AI SDK
- LangGraph
- Semantic Kernel
- Haystack
- Portkey own SDK (Python + TypeScript)

---

## 16. Enterprise Features

### 16.1 Security and Compliance

| Certification | Status                 |
| ------------- | ---------------------- |
| SOC 2 Type 2  | Certified              |
| ISO 27001     | Certified              |
| GDPR          | Compliant              |
| HIPAA         | Certified (Enterprise) |
| CCPA          | Compliant              |
| Custom BAAs   | Available (Enterprise) |

### 16.2 Access Management

- SSO integration: Okta, Azure AD (SAML)
- SCIM provisioning: Automatic user/group sync
- RBAC: Granular roles per workspace and org
- JWT authentication: Custom auth flows
- Audit logs: Full request and admin action history
- Admin APIs: Programmatic workspace and user management
- Encryption key management: Bring your own encryption keys (Enterprise)

### 16.3 Data Governance

- PII anonymization in logs
- Custom data retention policies
- Regional data planes: Keep data in specified jurisdictions
- Data export to data lakes (Enterprise)
- Data isolation guarantees

---

## 17. Pricing (as of 2026-02-20)

| Plan        | Price     | Requests   | Log Retention | Key Features                                                     |
| ----------- | --------- | ---------- | ------------- | ---------------------------------------------------------------- |
| Dev (Free)  | $0        | 10K/month  | 3 days        | Basic observability, simple caching (1d TTL), 3 prompt templates |
| Pro         | $49/month | 100K/month | 30 days       | Semantic caching, unlimited prompts, RBAC, alerts                |
| Pro Overage | $9/100K   | up to 3M   | —             | Overage billing                                                  |
| Enterprise  | Custom    | Custom     | Custom        | SSO, SCIM, VPC, HIPAA, airgapped, FinOps dashboards              |

Enterprise typically: $2,000–$10,000+/month depending on volume, deployment, retention, support.

The OSS gateway core is available free (no managed observability/prompt management).

**Note:** Portkey announced February 19, 2026 that their **core enterprise gateway is now free** following their $15M Series A raise.

---

## 18. API Endpoints

All OpenAI-compatible:

| Endpoint                       | Method    | Purpose                       |
| ------------------------------ | --------- | ----------------------------- |
| `/v1/chat/completions`         | POST      | Chat completions              |
| `/v1/completions`              | POST      | Text completions (legacy)     |
| `/v1/embeddings`               | POST      | Text embeddings               |
| `/v1/images/generations`       | POST      | Image generation              |
| `/v1/audio/speech`             | POST      | Text-to-speech                |
| `/v1/audio/transcriptions`     | POST      | Speech-to-text                |
| `/v1/realtime`                 | WebSocket | OpenAI Realtime API           |
| `/v1/feedback`                 | POST      | Submit feedback               |
| `/v1/prompts/{id}/completions` | POST      | Prompt template execution     |
| `/v1/otel`                     | OTLP      | OpenTelemetry ingestion       |
| Admin APIs                     | Various   | User/workspace/key management |

---

## 19. Comparison with OpenRouter and LiteLLM

| Feature                 | Portkey                              | LiteLLM                      | OpenRouter                   |
| ----------------------- | ------------------------------------ | ---------------------------- | ---------------------------- |
| **Type**                | Managed SaaS + OSS gateway           | Open-source proxy            | Managed SaaS only            |
| **Model coverage**      | 1,600+                               | 100+                         | 400+                         |
| **Routing strategies**  | fallback, LB, conditional, nested    | fallback, LB, cost-optimized | auto-routing, model fallback |
| **Caching**             | Simple + Semantic                    | Simple only                  | Simple only                  |
| **Guardrails**          | 20+ native + 13 partner integrations | Basic (via extensions)       | None                         |
| **Observability**       | Full (40+ metrics, traces, OTel)     | Basic (external callbacks)   | Minimal                      |
| **Prompt management**   | Full versioning, A/B, API            | None                         | None                         |
| **Virtual keys**        | Yes (Model Catalog)                  | Yes (via config)             | No (direct API keys)         |
| **Budget limits**       | Yes (per key, per workspace)         | Limited                      | No                           |
| **RBAC**                | Yes (roles, workspaces)              | No native                    | No                           |
| **SSO/SCIM**            | Yes (Enterprise)                     | No                           | No                           |
| **Audit logs**          | Yes                                  | No                           | No                           |
| **Self-hosted**         | Yes (OSS gateway)                    | Yes (full)                   | No                           |
| **Airgapped**           | Yes (Enterprise)                     | Yes                          | No                           |
| **MCP Gateway**         | Yes                                  | No                           | No                           |
| **Agent integrations**  | 8+ frameworks                        | Multiple                     | Limited                      |
| **Pricing model**       | $0/49/custom                         | Free (OSS)                   | 5% markup on spend           |
| **SOC2/HIPAA**          | Yes (Enterprise)                     | Self-certified               | No                           |
| **Circuit breaker**     | Yes (cb_config)                      | Limited                      | No                           |
| **Conditional routing** | Yes (metadata/params/URL)            | Limited                      | No                           |
| **Feedback API**        | Yes                                  | No                           | No                           |
| **OTel support**        | Yes (OTLP endpoint)                  | Via callbacks                | No                           |

**Portkey unique advantages over OpenRouter:**

1. Self-hostable / airgapped — data never leaves your network
2. Guardrails (50+) — OpenRouter has none
3. Semantic caching — OpenRouter has none
4. Prompt management — OpenRouter has none
5. RBAC + SSO + audit logs — OpenRouter has none
6. No percentage markup on spend (flat monthly fee)
7. Conditional routing based on metadata
8. MCP Gateway support

**Portkey unique advantages over LiteLLM:**

1. Managed SaaS (no infra to operate)
2. Full observability dashboard out of box (LiteLLM needs external tools)
3. Semantic caching (LiteLLM simple only)
4. Prompt versioning and management
5. 13 partner guardrail integrations (LiteLLM has fewer)
6. SSO/SCIM/audit logs in managed tier
7. Feedback API
8. MCP Gateway

**LiteLLM advantages over Portkey:**

1. Fully open-source (MIT) — no SaaS dependency
2. Richer Python SDK for library-mode (not just proxy)
3. More deployment flexibility for custom builds
4. Free for any volume (self-hosted)

---

## 20. Gap Analysis for thegent CLIProxy

### 20.1 Features thegent Should Adopt from Portkey

**HIGH PRIORITY — Core routing capability:**

| Portkey Feature                              | thegent Status           | Gap                                             |
| -------------------------------------------- | ------------------------ | ----------------------------------------------- |
| Config Object with `strategy`/`targets` JSON | Partial (ad-hoc routing) | Formalize a declarative routing config format   |
| Nested strategies (LB inside fallback, etc.) | Not present              | Implement recursive config evaluation           |
| Conditional routing by metadata/params       | Not present              | Add metadata-keyed routing rules                |
| Circuit breaker (`cb_config`)                | Not present              | Implement failure_threshold + cooldown_interval |
| Per-target `override_params`                 | Partial                  | Allow per-target model/param override in config |
| `x-portkey-config` inline JSON               | Not present              | Allow inline config JSON in headers             |

**HIGH PRIORITY — Reliability:**

| Portkey Feature              | thegent Status | Gap                                      |
| ---------------------------- | -------------- | ---------------------------------------- |
| `use_retry_after_headers`    | Not present    | Honor provider Retry-After headers       |
| Per-target retry configs     | Not present    | Allow retry settings per routing target  |
| Request timeout (per-target) | Partial        | Per-target timeout with fallback trigger |

**MEDIUM PRIORITY — Observability:**

| Portkey Feature                         | thegent Status | Gap                                             |
| --------------------------------------- | -------------- | ----------------------------------------------- |
| `x-portkey-trace-id` / span propagation | Not present    | Structured trace/span headers on all requests   |
| `x-portkey-metadata` custom tagging     | Partial        | Formalize metadata header + attach to logs      |
| OTel OTLP endpoint                      | Not present    | Expose `/v1/otel` for external trace ingestion  |
| Feedback API                            | Not present    | POST endpoint to attach user feedback to traces |
| Cache hit/miss logging                  | Not present    | Log cache outcomes with each request            |

**MEDIUM PRIORITY — Caching:**

| Portkey Feature                               | thegent Status | Gap                                    |
| --------------------------------------------- | -------------- | -------------------------------------- |
| Cache namespace (`x-portkey-cache-namespace`) | Not present    | Per-user/per-session cache namespacing |
| Cache TTL via config                          | Not present    | `max_age` in cache config object       |
| Semantic caching                              | Not present    | Vector-based fuzzy cache (longer-term) |
| Cache force refresh                           | Not present    | Per-request cache bypass header        |

**MEDIUM PRIORITY — Guardrails:**

| Portkey Feature                 | thegent Status | Gap                                                         |
| ------------------------------- | -------------- | ----------------------------------------------------------- |
| Webhook-based custom guardrails | Not present    | Implement BYOG webhook with verdict/transform               |
| Input guardrail IDs in config   | Not present    | `input_guardrails` and `output_guardrails` in target config |
| JWT validator guardrail         | Partial        | JWT claim validation at gateway level                       |
| Model whitelist guardrail       | Not present    | Block requests to non-approved models                       |

**LOWER PRIORITY — Enterprise:**

| Portkey Feature               | thegent Status | Gap                                    |
| ----------------------------- | -------------- | -------------------------------------- |
| Budget limits per virtual key | Not present    | USD spend cap + auto-expiry on keys    |
| SCIM provisioning             | Not present    | Automated user sync from IdP           |
| FinOps dashboards             | Not present    | Cost breakdown by team/workspace/model |
| Prompt versioning API         | Partial        | Formalize prompt template versioning   |

### 20.2 Portkey Features NOT Worth Copying

- **Portkey Prompt Studio UI**: thegent is CLI-first; a full GUI prompt editor is out of scope
- **13 partner guardrail integrations**: Implement the webhook interface and let partners plug in — don't hardcode each
- **Model Catalog GUI**: CLI-based config files are sufficient for thegent's use case
- **SCIM**: Valid for enterprise build-out but not immediate priority

### 20.3 Architecture Recommendation for thegent

Portkey's Config Object model is the right mental model to steal:

1. **Define a `RouteConfig` JSON schema** similar to Portkey's (strategy + targets + cache + retry + guardrails)
2. **Support inline config via header** (`x-thegent-config`) or by config ID reference
3. **Make targets recursive** so nested strategies work out of the box
4. **Add circuit breaker state** at the router level using the `cb_config` pattern
5. **Add `cache_namespace`** to existing cache layer for per-user partitioning
6. **Expose an OTLP endpoint** for receiving external OTel spans to correlate with LLM logs
7. **Implement webhook guardrails** with the 3-second timeout and verdict/transform pattern

---

## Sources

- [GitHub - Portkey-AI/gateway](https://github.com/Portkey-AI/gateway)
- [Portkey AI Gateway Features](https://portkey.ai/features/ai-gateway)
- [Portkey Guardrails](https://portkey.ai/features/guardrails)
- [Top 5 LLM Gateways 2025 - Helicone](https://www.helicone.ai/blog/top-llm-gateways-comparison-2025)
- [Best LLM Gateways 2025 - TrueFoundry](https://www.truefoundry.com/blog/best-llm-gateways)
- [Portkey Pricing 2026 - TrueFoundry](https://www.truefoundry.com/blog/portkey-pricing-guide)
- [OpenRouter Alternatives - Portkey](https://portkey.ai/alternatives/openrouter-alternatives)
- [LiteLLM Alternatives - Portkey](https://portkey.ai/alternatives/litellm-alternatives)
- [Portkey Raises $15M Series A](https://finance.yahoo.com/news/portkey-raises-15m-series-scale-170000953.html)
- [Portkey Config Object Docs](https://portkey.ai/docs/api-reference/config-object)
- [Portkey Conditional Routing](https://portkey.ai/docs/product/ai-gateway/conditional-routing)
- [Portkey Virtual Keys](https://portkey.ai/docs/product/ai-gateway/virtual-keys)
- [Portkey Model Catalog](https://portkey.ai/docs/product/model-catalog)
- [Portkey OTel Integration](https://portkey.ai/docs/product/observability/opentelemetry)
- [Portkey MCP Gateway](https://portkey.ai/features/mcp)
- [Portkey Guardrail Checks](https://docs1.portkey.ai/docs/product/guardrails/list-of-guardrail-checks)
- [Portkey Vercel Provider](https://github.com/Portkey-AI/vercel-provider)
- [Portkey Prompt Versioning](https://portkey.ai/docs/product/prompt-engineering-studio/prompt-versioning)
