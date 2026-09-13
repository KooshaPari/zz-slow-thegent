<DONE>
# Kong AI Gateway: Exhaustive Research (2026-02-20)

## Table of Contents

1. [What Is Kong AI Gateway?](#1-what-is-kong-ai-gateway)
2. [Deployment Models](#2-deployment-models)
3. [Plugin-Based Architecture](#3-plugin-based-architecture)
4. [Full AI Plugin Catalog](#4-full-ai-plugin-catalog)
5. [ai-proxy Plugin](#5-ai-proxy-plugin)
6. [ai-proxy-advanced Plugin](#6-ai-proxy-advanced-plugin)
7. [Load Balancing Algorithms](#7-load-balancing-algorithms)
8. [Semantic Caching](#8-semantic-caching)
9. [AI Rate Limiting](#9-ai-rate-limiting)
10. [Guardrails: Prompt Guard](#10-guardrails-prompt-guard)
11. [Guardrails: Semantic Prompt Guard](#11-guardrails-semantic-prompt-guard)
12. [Request and Response Transformation](#12-request-and-response-transformation)
13. [Prompt Decoration and Templating](#13-prompt-decoration-and-templating)
14. [Observability](#14-observability)
15. [Cost Tracking](#15-cost-tracking)
16. [MCP Gateway (Agentic Infrastructure)](#16-mcp-gateway-agentic-infrastructure)
17. [Enterprise-Only Plugins](#17-enterprise-only-plugins)
18. [Declarative Configuration](#18-declarative-configuration)
19. [Benchmarks vs Alternatives](#19-benchmarks-vs-alternatives)
20. [Comparison: Kong vs OpenRouter vs LiteLLM vs Portkey](#20-comparison-kong-vs-openrouter-vs-litellm-vs-portkey)
21. [Gap Analysis for thegent](#21-gap-analysis-for-thegent)

---

## 1. What Is Kong AI Gateway?

Kong AI Gateway is a **connectivity and governance layer for AI-native applications** built on top of Kong Gateway (the battle-tested API gateway). It extends Kong's established Nginx/Lua-based runtime with a suite of AI-specific plugins that manage, secure, transform, and observe LLM traffic.

Key design principles:

- **Plugin-based composition**: No new runtime. AI capabilities are Kong plugins layered on top of standard Kong Gateway. You compose capabilities by stacking plugins on services/routes.
- **Provider-agnostic universal API**: Accepts OpenAI-format requests and translates them to any provider format. Clients never need to know which provider is behind a route.
- **Infrastructure governance parity**: LLM traffic gets the same controls (auth, rate limiting, WAF, RBAC, logging, circuit breakers) as traditional API traffic — because it literally runs on the same gateway.
- **No-code AI integration**: Platform teams can inject AI capabilities (RAG, PII sanitization, prompt decoration) at the gateway layer without touching application code.

### Supported LLM Providers (as of 3.13, early 2026)

OpenAI, Azure OpenAI, Anthropic, AWS Bedrock, Google Vertex AI, Google Gemini, Cohere, Mistral, Hugging Face, Llama (self-hosted), and additional custom endpoints.

### Modality Support (added 3.11, July 2025)

- Text (chat completions, completions, embeddings)
- Audio (speech-to-text transcription, text-to-speech synthesis)
- Image generation
- Stateful assistants (OpenAI Assistants API)
- Function calling

---

## 2. Deployment Models

Kong supports all topologies:

| Mode                              | Description                                                                                                                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Kong OSS**                      | Open source, self-hosted. No GUI (Kong Manager). Basic AI plugins (ai-proxy, ai-prompt-guard, ai-prompt-decorator, ai-prompt-template, ai-request-transformer, ai-response-transformer) are free. |
| **Kong Gateway Enterprise**       | Self-hosted with enterprise license. Full plugin catalog, Kong Manager GUI, RBAC, advanced analytics, SSO/OIDC.                                                                                   |
| **Kong Konnect (SaaS)**           | Cloud-managed control plane, self-hosted or cloud data planes. Konnect Advanced Analytics for pre-built dashboards. Free tier available for AI Gateway.                                           |
| **Hybrid**                        | Control plane in Konnect/Enterprise, data planes self-hosted or cloud.                                                                                                                            |
| **DB-less**                       | No PostgreSQL required. Declarative YAML config only. Ideal for Kubernetes / KIC.                                                                                                                 |
| **Kong Ingress Controller (KIC)** | Kubernetes-native. CRDs map to Kong entities.                                                                                                                                                     |

### Pricing (2026 estimates)

- **Konnect SaaS**: ~$105/month per Gateway Service + ~$34.25 per 1M API requests + ~$720/month base infrastructure. Not well-suited for agentic workloads with high internal API call counts.
- **Enterprise self-hosted**: Exceeds $50,000/year for mid-sized deployments. AI Rate Limiting Advanced and other enterprise AI plugins require add-on licenses.
- **OSS**: Free. Missing enterprise plugins and GUI.

### Key Limitation (Customization)

Kong customization is done in **Lua** (LuaJIT). This is a significant friction point for AI teams used to Python. No native Python plugin runtime — AI teams must either learn Lua or write plugins in Go using the PDK.

---

## 3. Plugin-Based Architecture

Kong AI Gateway has no standalone binary. It is composed by layering plugins on Kong Gateway routes and services:

```
Client Request
    │
    ▼
Kong Route
    │
    ├── ai-prompt-guard        (pre-flight: reject banned content)
    ├── ai-prompt-decorator    (inject system prompts)
    ├── ai-prompt-template     (enforce template usage)
    ├── ai-rate-limiting-advanced  (token quota enforcement)
    ├── ai-request-transformer (LLM-based request rewrite)
    │
    ├── ai-proxy / ai-proxy-advanced  (core: translate + route to LLM)
    │
    ├── ai-semantic-cache      (cache hit check, short-circuit)
    ├── ai-response-transformer (LLM-based response rewrite)
    ├── ai-semantic-prompt-guard (post-routing content check)
    └── observability / logging plugins
```

Plugins execute in a defined phase order (access, header_filter, body_filter, log). The `ai-request-transformer` runs before `ai-proxy`; `ai-response-transformer` runs after. Plugin ordering within phases is deterministic.

---

## 4. Full AI Plugin Catalog

As of February 2026, Kong has **21 AI plugins**:

### Free / OSS Plugins

| Plugin                    | Function                                                     |
| ------------------------- | ------------------------------------------------------------ |
| `ai-proxy`                | Core routing to single LLM provider                          |
| `ai-prompt-decorator`     | Prepend/append system messages to chat history               |
| `ai-prompt-guard`         | Regex-based allow/deny list for prompts                      |
| `ai-prompt-template`      | Fill-in-the-blank prompt templates with injection prevention |
| `ai-request-transformer`  | LLM rewrites upstream request bodies                         |
| `ai-response-transformer` | LLM rewrites upstream response bodies                        |

### Enterprise / AI License Required

| Plugin                       | Function                                                          |
| ---------------------------- | ----------------------------------------------------------------- |
| `ai-proxy-advanced`          | Multi-provider load balancing with 7 algorithms                   |
| `ai-rate-limiting-advanced`  | Token- and cost-based rate limiting                               |
| `ai-semantic-cache`          | Vector similarity response caching (Redis/pgvector)               |
| `ai-semantic-prompt-guard`   | Embedding-based semantic allow/deny (multilingual)                |
| `ai-semantic-response-guard` | Semantic filtering of LLM responses                               |
| `ai-rag-injector`            | Automated RAG context injection at gateway layer                  |
| `ai-pii-sanitizer`           | PII detection/redaction in prompts (20+ categories, 12 languages) |
| `ai-prompt-compressor`       | Reduce token count via LLM compression (up to 5x savings)         |
| `ai-llm-as-judge`            | Use an LLM to evaluate/compare other LLM responses                |
| `ai-mcp-proxy`               | MCP protocol gateway (passthrough, conversion, aggregation)       |
| `ai-mcp-oauth2`              | OAuth2 for MCP endpoints                                          |
| `ai-aws-guardrails`          | AWS Bedrock Guardrails integration                                |
| `ai-azure-content-safety`    | Azure Content Safety integration                                  |
| `ai-gcp-model-armor`         | Google Cloud Model Armor integration                              |
| `ai-lakera-guard`            | Lakera Guard prompt injection detection                           |

---

## 5. ai-proxy Plugin

### What It Does

The core AI plugin. Takes an OpenAI-format request, translates it to the target provider's format, routes it, and translates the response back.

### Configuration

```yaml
plugins:
  - name: ai-proxy
    config:
      route_type: llm/v1/chat # llm/v1/chat | llm/v1/completions | llm/v1/embeddings
      auth:
        header_name: Authorization
        header_value: "Bearer ${OPENAI_API_KEY}"
      model:
        provider: openai # openai | anthropic | azure | bedrock | gemini | cohere | mistral | etc.
        name: gpt-4o
        options:
          max_tokens: 1024
          temperature: 0.7
```

### Route Types

- `llm/v1/chat` — OpenAI Chat Completions format
- `llm/v1/completions` — legacy text completions
- `llm/v1/embeddings` — embedding vectors
- `llm/v1/audio/transcriptions` — audio transcription (3.11+)
- `llm/v1/audio/speech` — text-to-speech (3.11+)
- `llm/v1/images/generations` — image generation (3.11+)

### Streaming Support

Full SSE (Server-Sent Events) streaming passthrough. Kong parses the streamed token chunks to extract token counts for observability.

### Auth Methods

- Header-based (Bearer token, API key header)
- AWS SigV4 (for Bedrock)
- Google OAuth2 (for Vertex/Gemini)
- Azure Entra ID / Managed Identity

### What ai-proxy Does NOT Do

- Multi-provider routing (one upstream only)
- Load balancing
- Failover

---

## 6. ai-proxy-advanced Plugin

### What It Does

Enterprise-tier replacement for ai-proxy that supports **multiple targets** with sophisticated load balancing, failover, and cost-aware routing.

### Core Differences from ai-proxy

| Feature           | ai-proxy | ai-proxy-advanced             |
| ----------------- | -------- | ----------------------------- |
| Targets           | 1        | Unlimited                     |
| Load balancing    | None     | 7 algorithms                  |
| Failover          | No       | Yes (configurable criteria)   |
| Circuit breakers  | No       | Yes (v3.13+)                  |
| Cost routing      | No       | Yes (lowest-usage by cost)    |
| Semantic routing  | No       | Yes (vector similarity)       |
| Health checks     | No       | Yes (v3.13+)                  |
| Native LLM format | No       | Yes (skip OpenAI translation) |

### Configuration Example

```yaml
plugins:
  - name: ai-proxy-advanced
    config:
      balancer:
        algorithm: lowest-latency # algorithm selection
        retries: 3
        failover_criteria:
          - http_429
          - http_502
      targets:
        - route_type: llm/v1/chat
          auth:
            header_name: Authorization
            header_value: "Bearer ${OPENAI_API_KEY}"
          model:
            provider: openai
            name: gpt-4o
          weight: 80
        - route_type: llm/v1/chat
          auth:
            header_name: x-api-key
            header_value: "${ANTHROPIC_API_KEY}"
          model:
            provider: anthropic
            name: claude-3-5-sonnet-20241022
          weight: 20
```

### Circuit Breaker (v3.13+)

When a target's failure count exceeds `max_fails`, it is marked unhealthy and removed from the load balancer pool. After `fail_timeout` elapses, the target is re-tested. Success restores health immediately. Failure counters are cumulative (not consecutive).

---

## 7. Load Balancing Algorithms

Kong AI Gateway implements 7 algorithms via `ai-proxy-advanced`:

### 1. Round-Robin (Weighted)

Distributes traffic proportionally by weight. No dynamic adjustment. Default for multi-provider with fixed cost splits.

### 2. Consistent-Hashing

Sticky sessions based on a header value (default: `X-Kong-LLM-Request-ID`). Routes identical header values to the same model — useful for conversation context within a session.

### 3. Least-Connections (v3.13+)

Tracks in-flight requests per backend. Routes new requests to the target with highest spare capacity. Dynamically adapts to response time variance.

### 4. Lowest-Latency

Uses **Peak EWMA** (Exponentially Weighted Moving Average) to track response times. Routes to the fastest model. Metric: time-per-output-token (default) or end-to-end latency. EWMA decays over time, allowing recovery after slow spikes.

### 5. Lowest-Usage

Routes based on resource consumption:

- `prompt_tokens` — minimize input token usage
- `completion_tokens` — minimize output token usage
- `cost` (v3.10+) — minimize financial cost (pricing per million tokens configured per target)

### 6. Semantic

The most sophisticated algorithm. Uses vector embeddings to route each prompt to the model whose **description** is most semantically similar to the prompt content.

**How it works:**

1. Each target has a `description` string (e.g., "Expert in Python programming")
2. On each request, Kong embeds the user prompt using a configured embedding model (e.g., OpenAI `text-embedding-3-small`)
3. Cosine similarity is computed in Redis VSS against stored description embeddings
4. Request is routed to the target exceeding the similarity threshold
5. Ties or no-match above threshold → round-robin among matched targets or fallback to CATCHALL

```yaml
config:
  balancer:
    algorithm: semantic
  embeddings:
    provider: openai
    model_name: text-embedding-3-small
  vectordb:
    strategy: redis
    redis:
      host: redis.example.com
      port: 6379
    dimensions: 1536
    distance_metric: cosine
    threshold: 0.75
  targets:
    - model: { provider: openai, name: gpt-4o }
      description: "Expert in Python programming and software architecture"
    - model: { provider: anthropic, name: claude-3-5-haiku }
      description: "Creative writing, storytelling, and ideation"
    - model: { provider: openai, name: gpt-4o-mini }
      description: "CATCHALL"
```

### 7. Priority

Tiered failover groups. Traffic goes entirely to the highest-priority group until that group fails, then cascades to lower-priority groups. Useful for primary/fallback provider patterns:

- Priority 1: GPT-4o (primary)
- Priority 2: Claude 3.5 Sonnet (secondary)
- Priority 3: Mistral (emergency fallback)

---

## 8. Semantic Caching

### How It Works

The `ai-semantic-cache` plugin intercepts LLM requests and checks a vector database for semantically similar prior queries:

1. **Access phase**: Embed incoming prompt → query Redis VSS for similar cached responses
2. **Cache hit**: Return cached response immediately (no LLM call). Adds `X-Cache-Status: Hit`.
3. **Cache miss**: Forward to LLM. After response, embed and store in Redis with TTL. Adds `X-Cache-Status: Miss`.

### Storage Backends

| Backend                  | Notes                              |
| ------------------------ | ---------------------------------- |
| Redis (with VSS)         | Primary option since 3.8           |
| AWS MemoryDB for Redis   | Managed Redis with VSS, added 3.12 |
| PostgreSQL + pgvector    | Added 3.10                         |
| AWS ElastiCache          | IAM-based credential rotation      |
| Azure Managed Redis      | IAM-based                          |
| Google Cloud Memorystore | IAM-based                          |

### Configuration

```yaml
plugins:
  - name: ai-semantic-cache
    config:
      embeddings:
        provider: openai
        model_name: text-embedding-3-small
        auth:
          header_name: Authorization
          header_value: "Bearer ${OPENAI_API_KEY}"
      vectordb:
        strategy: redis
        redis:
          host: redis.example.com
          port: 6379
        dimensions: 1536
        distance_metric: cosine
        threshold: 0.85 # Similarity cutoff (higher = stricter)
      cache_ttl: 300 # Default 300s
```

### Cache Headers

| Header           | Meaning                  |
| ---------------- | ------------------------ |
| `X-Cache-Status` | `Hit` / `Miss`           |
| `X-Cache-Key`    | Hash of the cached entry |
| `Age`            | Seconds since caching    |
| `X-Cache-Ttl`    | Remaining TTL            |

### Cache Control Respect

Respects standard HTTP cache directives: `no-store`, `no-cache`, `private`, `max-age`, `s-maxage`.

### Exact vs Semantic Caching

Both modes run simultaneously:

- **Exact cache**: Hash-match on identical prompts (faster lookup, zero embedding cost)
- **Semantic cache**: VSS search for near-matches

### Cost Reduction

Kong claims up to **5x cost reduction** using semantic caching + prompt compression together.

---

## 9. AI Rate Limiting

### Plugin: `ai-rate-limiting-advanced` (Enterprise)

Extends the standard Rate Limiting Advanced plugin with LLM token awareness.

### Token Count Strategies

| Strategy            | What Is Counted                                         |
| ------------------- | ------------------------------------------------------- |
| `total_tokens`      | Prompt + completion tokens combined                     |
| `prompt_tokens`     | Input tokens only                                       |
| `completion_tokens` | Output tokens only                                      |
| `cost`              | Financial cost (USD) based on per-million-token pricing |

### Window Strategies

| Strategy  | How Counters Are Stored                                 |
| --------- | ------------------------------------------------------- |
| `local`   | Per-node in-memory (fast, less accurate across cluster) |
| `cluster` | Shared via data store (accurate, higher latency)        |
| `redis`   | Redis-backed (accurate, moderate latency)               |

### Rate Limit Response Headers

```
X-AI-RateLimit-Limit-minute-openai: 100000
X-AI-RateLimit-Remaining-minute-openai: 87432
X-AI-RateLimit-Retry-After: 23
```

Limit exceeded: HTTP 429 with `"API rate limit exceeded for provider [openai]"`

### Important Behavior

Token costs are calculated from the **previous response** (LLM returns token counts in its response body). This means rate limit enforcement for the current request uses the cost calculated from the prior response. There is a one-request lag in enforcement.

### Provider-Specific Limiting

You can define separate rate limits per provider, per window (second, minute, hour, day, month, year), per Consumer or Consumer Group.

---

## 10. Guardrails: Prompt Guard

### Plugin: `ai-prompt-guard` (OSS/Free)

Pattern-based (regex) content filtering for incoming prompts.

**How it works:**

1. Intercepts the request in the access phase (before LLM routing)
2. Evaluates all message content against configured regex patterns
3. Allow-list logic: if allow patterns configured, request must match at least one
4. Deny-list logic: if request matches any deny pattern, returns HTTP 400
5. Deny takes precedence over allow

### Use Cases

- Block known jailbreak phrases
- Restrict to topic-relevant queries (e.g., only allow questions containing "support" or "help")
- Reject requests containing competitor names
- PII pattern blocking (basic regex-based)

### Limitation

Regex patterns are circumventable by paraphrasing. Does not understand semantic intent — only literal string matching.

---

## 11. Guardrails: Semantic Prompt Guard

### Plugin: `ai-semantic-prompt-guard` (Enterprise)

Semantic-intent-based content filtering using vector embeddings. Overcomes regex circumvention.

**How it works:**

1. Converts incoming prompt to a vector embedding
2. Computes cosine similarity against stored reference prompts in Redis/pgvector
3. Deny list: if similarity to any deny-list prompt exceeds threshold → HTTP 400
4. Allow list: if configured, prompt must be similar to at least one allow-list entry
5. Multilingual: supports prompts and reference entries in different languages (embedding models handle semantic cross-language comparison)

### Supported Embedding Providers

Azure, AWS Bedrock, Google Gemini, Hugging Face, Mistral, OpenAI.

### Storage Backends

Redis VSS, AWS MemoryDB, PostgreSQL pgvector.

### Also: `ai-semantic-response-guard` (Enterprise)

Same mechanism applied to **LLM response content** — blocks responses that are semantically similar to banned topics before they reach the client.

---

## 12. Request and Response Transformation

### Plugin: `ai-request-transformer` (OSS/Free)

Uses an LLM to **rewrite the upstream request body** before routing.

**Pipeline position**: Runs before `ai-proxy`.

**How it works:**

1. Admin configures a transformation prompt (system message) describing the desired transformation
2. For each incoming request, Kong sends the entire request body as the user message to the configured LLM
3. The LLM returns a transformed version of the request
4. That transformed version becomes the new upstream request body

**Use cases:**

- Normalize inconsistent client request formats
- Inject metadata or context into prompts automatically
- Translate requests from one format/schema to another

**Configuration:**

```yaml
plugins:
  - name: ai-request-transformer
    config:
      prompt: "Transform the following API request into a structured JSON format suitable for our internal service..."
      llm:
        provider: openai
        name: gpt-4o-mini
        auth:
          header_name: Authorization
          header_value: "Bearer ${OPENAI_API_KEY}"
```

### Plugin: `ai-response-transformer` (OSS/Free)

Uses an LLM to **rewrite the upstream response body** before returning to the client.

**Pipeline position**: Runs after `ai-proxy` (in the response phase).

**How it works:**

1. Admin configures a transformation prompt
2. After LLM response is received, Kong sends the response body as the user message to the transformer LLM
3. Transformer LLM returns a modified response
4. That modified response is sent to the client

**Special feature**: If `parse_llm_response_json_instructions: true`, Kong parses JSON instructions in the LLM response to set response headers, status codes, and replacement bodies.

**Use cases:**

- Format LLM responses to match client expectations
- Redact or summarize responses
- Add metadata to responses
- Translate responses

---

## 13. Prompt Decoration and Templating

### Plugin: `ai-prompt-decorator` (OSS/Free)

Injects predefined messages into the user's chat history, either prepended (before) or appended (after) the user's messages.

**Use cases:**

- Inject system prompts invisible to the end user
- Add context, persona, or constraint messages
- Inject guardrail instructions
- Add conversation history boilerplate

**Configuration:**

```yaml
plugins:
  - name: ai-prompt-decorator
    config:
      prepend:
        - role: system
          content: "You are a helpful customer support agent for Acme Corp. Only answer questions about our products."
      append:
        - role: system
          content: "Always respond in formal English. Never disclose internal pricing."
```

The user never sees these injected messages.

### Plugin: `ai-prompt-template` (OSS/Free)

Admins define structured prompt templates with `{{variable}}` placeholders. Users fill in variables rather than crafting free-form prompts.

**Template definition** (admin-configured):

```json
{
  "name": "summarize-document",
  "messages": [
    {
      "role": "user",
      "content": "Summarize the following document in {{language}}: {{document_text}}"
    }
  ]
}
```

**Client request:**

```json
{
  "messages": "{template://summarize-document}",
  "properties": {
    "language": "English",
    "document_text": "..."
  }
}
```

**Security**: Input values are JSON-escaped to prevent prompt injection. Setting `allow_untemplated_requests: false` forces all clients to use templates (HTTP 400 otherwise).

---

## 14. Observability

### Metrics Exposed

Kong AI Gateway exposes LLM-specific metrics through multiple channels:

**Prometheus (standard Kong metrics + AI extensions):**

- Token counts (prompt, completion, total) per provider/model/consumer
- Request latency (TTFT — time to first token, end-to-end)
- Error rates by provider
- Cache hit/miss ratios
- Cost per request

**OpenTelemetry (Span Attributes per GenAI spec):**

- `gen_ai.system` (provider name)
- `gen_ai.request.model`
- `gen_ai.usage.input_tokens`
- `gen_ai.usage.output_tokens`
- `gen_ai.response.finish_reason`
- Custom Kong attributes for cost, routing decisions

**Audit Logging:**
Full request/response bodies can be logged (with redaction options) for compliance. Log format: structured JSON.

### Integrations

| Platform                   | Method                                                       |
| -------------------------- | ------------------------------------------------------------ |
| Grafana                    | Grafana Dashboard 24057 (official Kong AI Gateway dashboard) |
| Prometheus                 | Native scrape endpoint                                       |
| Datadog                    | Crest Data Systems Kong AI Gateway integration               |
| Dynatrace                  | Native Kong AI observability integration                     |
| Langfuse                   | Kong AI plugin integration for LLM tracing                   |
| AWS CloudWatch             | OpenTelemetry export                                         |
| Konnect Advanced Analytics | Pre-built dashboards (Konnect/Enterprise only)               |

### Konnect Advanced Analytics (Enterprise/Konnect)

- Pre-built dashboards showing token usage, cost trends, provider breakdown
- Per-consumer, per-route, per-service drilling
- Anomaly detection on token/cost spikes

---

## 15. Cost Tracking

Multiple layers of cost visibility:

1. **`ai-rate-limiting-advanced`**: Enforces cost budgets (token or USD per window)
2. **Metrics**: Per-provider cost counters in Prometheus/OTel
3. **Audit logs**: Per-request cost in structured log output
4. **Konnect Analytics**: Aggregated cost dashboards
5. **`ai-proxy-advanced` with lowest-usage/cost**: Actively routes to cheapest provider

### Cost Configuration (per target in ai-proxy-advanced)

```yaml
targets:
  - model:
      provider: openai
      name: gpt-4o
    pricing:
      input_tokens_per_million: 2.50
      output_tokens_per_million: 10.00
  - model:
      provider: openai
      name: gpt-4o-mini
    pricing:
      input_tokens_per_million: 0.15
      output_tokens_per_million: 0.60
```

The `lowest-usage` balancer with `cost` strategy uses these prices to compute per-request cost and routes to the cheaper provider.

---

## 16. MCP Gateway (Agentic Infrastructure)

### Plugin: `ai-mcp-proxy` (Enterprise)

The most agentic-focused new capability. Kong acts as an MCP (Model Context Protocol) gateway, bridging MCP clients with both MCP servers and existing REST APIs.

### Four Operating Modes

| Mode                   | Description                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| `passthrough-listener` | Routes MCP requests to an upstream MCP server. Kong adds auth, rate limiting, observability.                  |
| `conversion-listener`  | Converts REST API endpoints into MCP tools AND accepts incoming MCP requests on the same path.                |
| `conversion-only`      | Converts REST APIs to MCP tools but does not accept MCP requests directly. Aggregated by a `listener` plugin. |
| `listener`             | Aggregates tools from multiple `conversion-only` plugins via tag matching. Creates a unified MCP endpoint.    |

### Protocol Translation

```
MCP Client
    │  (MCP request: tool call)
    ▼
Kong Gateway (ai-mcp-proxy)
    │  (parse tool invocation → map to OpenAPI operation → HTTP request)
    ▼
Upstream REST API or MCP Server
    │  (HTTP response or MCP response)
    ▼
Kong Gateway
    │  (wrap in MCP response format)
    ▼
MCP Client
```

### Access Control

- **Default ACLs**: Baseline rules applying to all tools
- **Per-tool ACLs**: Fine-grained exceptions per tool
- Identifier types: usernames, Consumer IDs, custom IDs, Consumer Group names
- `ai-mcp-oauth2` plugin: OAuth2 flows for MCP client authentication (added for cookie-based auth in v3.13)

### Why This Matters

MCP is becoming the protocol standard for AI agent tool use. Kong's MCP proxy means:

1. Any existing REST API becomes an MCP tool without code changes
2. Third-party MCP servers get enterprise governance (auth, rate limiting, audit logging) transparently
3. Multiple MCP tool sources aggregated into a single MCP endpoint for agents

### MCP Tool-Level ACLs (v3.13, January 2026)

Fine-grained authorization: specific authenticated consumers can only call specific MCP tools. Prevents privilege escalation in agentic workflows where agents have broad MCP server access.

---

## 17. Enterprise-Only Plugins

### `ai-rag-injector`

Automates the retrieval phase of RAG at the gateway layer.

- Platform teams configure a vector DB and retrieval parameters
- On each request, Kong automatically retrieves relevant context documents
- Injects them into the prompt before forwarding to the LLM
- No application code changes needed
- Reduces hallucinations by ensuring LLMs have factual context
- Added in Kong AI Gateway 3.10 (April 2025)

### `ai-pii-sanitizer`

- Detects and redacts 20+ PII categories (names, emails, SSNs, phone numbers, financial data, etc.)
- Supports 12 languages
- **Re-insertion**: Can re-inject original PII values back into the response before returning to client (PII-safe round-trip)
- Added in Kong AI Gateway 3.10

### `ai-prompt-compressor`

- Uses an LLM to compress prompts before sending to the target LLM
- Reduces token count while preserving semantic meaning
- Claimed: up to 5x cost reduction, 80% semantic retention
- Added in Kong AI Gateway 3.11

### `ai-llm-as-judge`

- Uses a configured LLM to evaluate/score responses from other LLMs
- Enables quality control and A/B testing across models
- Can compare accuracy across different model configurations

### `ai-aws-guardrails`, `ai-azure-content-safety`, `ai-gcp-model-armor`, `ai-lakera-guard`

External content safety service integrations. Kong proxies content through these services for toxicity scoring, PII detection, prompt injection detection, and policy enforcement before/after LLM calls.

---

## 18. Declarative Configuration

Kong supports fully declarative, Git-friendly configuration via **decK** (declarative Kong):

### Example: kong.yaml AI Gateway Configuration

```yaml
_format_version: "3.0"
_transform: true

services:
  - name: openai-chat
    url: https://api.openai.com
    routes:
      - name: chat-route
        paths:
          - /v1/chat/completions
        methods:
          - POST
    plugins:
      - name: ai-proxy
        config:
          route_type: llm/v1/chat
          auth:
            header_name: Authorization
            header_value: "Bearer ${OPENAI_API_KEY}"
          model:
            provider: openai
            name: gpt-4o
      - name: ai-prompt-decorator
        config:
          prepend:
            - role: system
              content: "You are a helpful assistant."
      - name: ai-prompt-guard
        config:
          deny:
            - ".*jailbreak.*"
            - ".*ignore previous instructions.*"
      - name: ai-rate-limiting-advanced
        config:
          limit:
            - 100000
          window_size:
            - 3600
          identifier: consumer
          strategy: redis
          token_count_strategy: total_tokens
```

### decK CLI

```bash
# Push config to Kong
deck gateway sync kong.yaml

# Pull running config
deck gateway dump > kong-current.yaml

# Diff
deck gateway diff kong.yaml
```

### DB-less Mode

```bash
# Start Kong with declarative config (no PostgreSQL required)
KONG_DATABASE=off \
KONG_DECLARATIVE_CONFIG=/path/to/kong.yaml \
kong start
```

This enables Git-as-source-of-truth for Kong configuration, including all AI plugin settings.

---

## 19. Benchmarks vs Alternatives

### Kong's Own Benchmark (2024, published on konghq.com)

Testing basic proxy performance under identical hardware (12 CPUs):

| Product        | Relative Throughput | P95 Latency vs Kong |
| -------------- | ------------------- | ------------------- |
| Kong Konnect   | Baseline (highest)  | Baseline            |
| Portkey        | ~200% slower        | ~65% higher latency |
| LiteLLM        | ~800% slower        | ~86% higher latency |
| WireMock (raw) | Closest to Kong     | Near baseline       |

**Caveat**: Kong ran this benchmark internally and published it. The test measured basic proxy performance without AI-specific plugins active. Real-world performance with semantic caching, rate limiting, and PII sanitization active would differ.

### Why Kong Is Fast

- Nginx/LuaJIT runtime — same engine used for some of the highest-traffic APIs on the internet
- Battle-tested production infrastructure vs purpose-built AI gateway startups
- No Python interpreter overhead in the critical path
- C-level Nginx processing for request routing

---

## 20. Comparison: Kong vs OpenRouter vs LiteLLM vs Portkey

| Dimension              | Kong AI Gateway                                                | OpenRouter              | LiteLLM                             | Portkey                               |
| ---------------------- | -------------------------------------------------------------- | ----------------------- | ----------------------------------- | ------------------------------------- |
| **Architecture**       | Plugin on API gateway                                          | Cloud-native AI router  | Python proxy + SDK                  | Cloud + self-hosted                   |
| **Self-hostable**      | Yes (OSS + Enterprise)                                         | No (cloud-only)         | Yes (OSS)                           | Yes (Enterprise)                      |
| **Provider count**     | 12+ (curated, full integration)                                | 500+ (breadth-first)    | 100+                                | 200+                                  |
| **Load balancing**     | 7 algorithms incl. semantic                                    | Basic (fallback)        | Fallback/round-robin                | Round-robin + fallback                |
| **Semantic routing**   | Yes (vector-based, native)                                     | No                      | No                                  | No                                    |
| **Semantic caching**   | Yes (Redis/pgvector)                                           | No                      | No                                  | Yes                                   |
| **Rate limiting**      | Token + cost + request                                         | None                    | Basic                               | Yes                                   |
| **Prompt guards**      | Regex + semantic (vector)                                      | None                    | Basic                               | Yes                                   |
| **PII sanitization**   | Yes (20+ categories, 12 langs)                                 | No                      | No                                  | Partial                               |
| **RAG injection**      | Yes (gateway-level)                                            | No                      | No                                  | No                                    |
| **MCP gateway**        | Yes (4 modes, ACLs)                                            | No                      | Yes (MCP server)                    | No                                    |
| **Observability**      | Deep (OTel, Prometheus, Grafana, Datadog, Dynatrace, Langfuse) | Basic                   | Basic + Langfuse                    | Yes (Langfuse)                        |
| **Declarative config** | Yes (decK YAML)                                                | No                      | Partial (YAML proxy config)         | No                                    |
| **RBAC / Workspaces**  | Yes (Enterprise)                                               | No                      | No                                  | Yes                                   |
| **Governance**         | Enterprise-grade (audit logs, SSO, RBAC, Dev Portal)           | None                    | None                                | Partial                               |
| **Customization**      | Lua plugins (niche)                                            | None                    | Python                              | JavaScript                            |
| **Performance**        | Highest (Nginx/LuaJIT)                                         | High (cloud)            | Lowest                              | Medium                                |
| **Cost**               | High ($50k+/year Enterprise)                                   | Free tier + per-call    | Free (OSS)                          | Free + Enterprise                     |
| **Best fit**           | Enterprise, existing Kong users, compliance-heavy              | Developers, prototyping | Platform teams, OSS, multi-provider | Teams wanting observability + caching |

### Kong's Unique Strengths

1. **Unified governance**: LLM traffic managed under the same policy engine as REST/gRPC APIs — no separate governance silo
2. **Plugin composability**: Stack 10+ plugins declaratively on any route without code changes
3. **MCP gateway**: Only gateway with production-grade MCP protocol support including ACLs and OAuth2
4. **Semantic routing**: Vector-similarity-based intelligent model selection (not just fallback chains)
5. **RAG at gateway layer**: Eliminates per-application RAG plumbing
6. **Enterprise compliance**: RBAC, SSO/OIDC, audit logs, developer portals, workspace isolation
7. **Performance**: Nginx-based runtime significantly outperforms Python-based alternatives

### Kong's Weaknesses

1. **Customization in Lua**: Python AI teams face steep learning curve or must use Go
2. **Cost**: Enterprise pricing is enterprise-level expensive
3. **Per-HTTP-request billing**: Agentic workloads with 20+ internal calls per user turn are penalized vs per-token billing
4. **Complexity**: Requires understanding Kong's routing model (Services, Routes, Upstreams, Consumers, Plugins) before adding AI features
5. **Provider breadth**: 12 providers vs 100+ in LiteLLM / 500+ in OpenRouter
6. **Not AI-native from ground up**: AI capabilities layered on API gateway — occasional friction at conceptual seams

---

## 21. Gap Analysis for thegent

### What thegent Has

- CLIProxy with LiteLLM routing backend
- Multi-provider support via LiteLLM (100+ providers)
- Cost tracking (per-session, per-run)
- Basic rate limiting
- Plugin/hook system (different paradigm — lifecycle hooks, not request-path plugins)
- MCP server integration (as MCP server, not MCP proxy gateway)

### What Kong Has That thegent Lacks (or Could Steal)

| Kong Feature                       | Relevance to thegent                                               | Priority |
| ---------------------------------- | ------------------------------------------------------------------ | -------- |
| **Semantic load balancing**        | Route agent tasks to specialist models by content similarity       | HIGH     |
| **Priority-based failover**        | Tiered fallback: GPT-4o → Claude → Mistral                         | HIGH     |
| **Lowest-latency EWMA routing**    | Route to fastest model for latency-sensitive agent steps           | HIGH     |
| **Semantic caching**               | Cache identical/similar agent queries (huge cost savings in loops) | HIGH     |
| **Token-based rate limiting**      | Budget enforcement per agent, per team, per project                | HIGH     |
| **PII sanitization**               | Strip PII before sending agent context to LLMs                     | MEDIUM   |
| **Prompt decoration (middleware)** | Inject system prompts at routing layer, not agent layer            | MEDIUM   |
| **Prompt guard (semantic)**        | Block jailbreaks/misuse in multi-tenant agent deployments          | MEDIUM   |
| **RAG injection at router layer**  | Standardize RAG context injection across all agents                | MEDIUM   |
| **MCP proxy with ACLs**            | Fine-grained tool access control per agent identity                | HIGH     |
| **Declarative config**             | Git-traceable routing config for reproducible deployments          | MEDIUM   |
| **LLM-as-judge**                   | Automated quality evaluation across model variants                 | LOW      |
| **Prompt compression**             | Reduce token cost for verbose agent contexts                       | LOW      |
| **Cost-based routing**             | Route to cheapest adequate model for each task type                | HIGH     |
| **Circuit breakers**               | Stop routing to degraded providers automatically                   | HIGH     |
| **Consistent-hashing**             | Sticky session routing for multi-turn agent conversations          | MEDIUM   |

### thegent's Advantages Over Kong

1. **Python-native**: AI teams can extend thegent without learning Lua
2. **Agent-native**: Designed for agent lifecycle (plan/execute/observe loops), not just request routing
3. **Agentic primitives**: Work streams, session continuity, agent memory, parallel subagents — Kong has none of this
4. **Cost model**: Not charged per-HTTP-request (agentic workloads often have 20+ internal calls per user turn)
5. **Hook system**: Pre/post lifecycle hooks vs Kong's per-request plugin pipeline
6. **100+ providers via LiteLLM**: More breadth out of the box

### What thegent Should Build Next (Informed by Kong)

Based on Kong's mature feature set, the highest-ROI additions to thegent's CLIProxy layer:

1. **Semantic routing for model selection**: Use embedding similarity to route tasks to specialist models (Kong calls this "semantic load balancing")
2. **Token budget enforcement per agent/session**: Kong's token rate limiting concept applied to agent sessions
3. **Priority failover chains**: Declarative primary/secondary/emergency model sequences
4. **Semantic response caching**: Cache agent query results by semantic similarity (not just exact match)
5. **MCP tool ACLs**: Per-agent, per-tool access control for MCP server tools
6. **Circuit breaker per provider**: Automatic removal of degraded providers from routing pool
7. **Cost-aware model routing**: `lowest-cost` routing strategy for non-latency-sensitive tasks

---

## Sources

- [Kong AI Gateway Overview](https://developer.konghq.com/ai-gateway/)
- [Kong Plugin Hub - AI Category](https://developer.konghq.com/plugins/?category=AI)
- [AI Proxy Advanced Plugin](https://developer.konghq.com/plugins/ai-proxy-advanced/)
- [Kong AI Gateway Load Balancing](https://developer.konghq.com/ai-gateway/load-balancing/)
- [Semantic Load Balancing How-To](https://developer.konghq.com/how-to/use-semantic-load-balancing/)
- [AI Semantic Cache Plugin](https://developer.konghq.com/plugins/ai-semantic-cache/)
- [AI Semantic Prompt Guard Plugin](https://developer.konghq.com/plugins/ai-semantic-prompt-guard/)
- [AI MCP Proxy Plugin](https://developer.konghq.com/plugins/ai-mcp-proxy/)
- [AI Prompt Decorator Plugin](https://developer.konghq.com/plugins/ai-prompt-decorator/)
- [AI Prompt Template Plugin](https://developer.konghq.com/plugins/ai-prompt-template/)
- [AI Rate Limiting Advanced Plugin](https://developer.konghq.com/plugins/ai-rate-limiting-advanced/)
- [Kong AI Gateway Benchmark vs Portkey vs LiteLLM](https://konghq.com/blog/engineering/ai-gateway-benchmark-kong-ai-gateway-portkey-litellm)
- [Kong AI Gateway 3.10 - RAG and PII](https://konghq.com/blog/product-releases/ai-gateway-3-10)
- [Kong AI Gateway 3.11 - Multimodal](https://konghq.com/blog/product-releases/ai-gateway-3-11)
- [Kong AI Gateway 3.13 - Agentic/MCP](https://konghq.com/blog/product-releases/ai-gateway-3-13)
- [Kong AI Gateway and Redis Integration](https://redis.io/blog/kong-ai-gateway-and-redis/)
- [Kong AI Gateway Dashboard on Grafana](https://grafana.com/grafana/dashboards/24057-kong-ai-gateway-dashboard/)
- [Kong API Gateway Langfuse Integration](https://langfuse.com/integrations/gateways/kong-ai-plugin)
- [Dynatrace Kong AI Integration](https://docs.dynatrace.com/docs/observe/dynatrace-for-ai-observability/ai-traffic-management-and-security/kong)
- [Datadog Kong AI Integration](https://docs.datadoghq.com/integrations/crest-data-systems-kong-ai-gateway/)
- [TrueFoundry Kong Pricing 2026 Analysis](https://www.truefoundry.com/blog/kong-gateway-pricing-architecture-an-analysis-for-ai-teams-2026-edition)
- [Top 5 LLM Gateways 2026 - Maxim](https://www.getmaxim.ai/articles/top-5-llm-gateways-for-2026-a-comprehensive-comparison/)
