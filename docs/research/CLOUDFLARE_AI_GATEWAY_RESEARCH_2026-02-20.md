<DONE>
# Cloudflare AI Gateway: Exhaustive Research (2026-02-20)

## Executive Summary

Cloudflare AI Gateway is an edge-hosted, CDN-native AI control plane that sits between applications and AI providers. It provides caching, rate limiting, observability, guardrails, dynamic routing, and unified billing in a single managed proxy. As of early 2026, it supports 24 providers (including Workers AI), has rolled out dynamic routing with visual flow configuration, DLP in its firewall, Unified Billing across 5 providers, and OpenTelemetry tracing. It is available on all Cloudflare plans with a generous free tier, and is positioned as the best choice for teams already on Cloudflare's stack.

---

## 1. Architecture

### CDN-Edge Hosted

Cloudflare AI Gateway runs on Cloudflare's global network (300+ PoPs). All AI requests are proxied through Cloudflare's edge before reaching providers. This means:

- Requests are routed to the nearest Cloudflare edge node first
- Caching happens at the edge (sub-millisecond for cache hits)
- The gateway itself adds minimal overhead; Cloudflare claims latency overhead is negligible
- No user-operated infrastructure — fully managed SaaS

### Account-Based Gateway Model

Each Cloudflare account can have up to 10 gateways (free tier) or 20 gateways (paid tier). A gateway is a named routing endpoint scoped to an account. All configuration (caching, rate limiting, guardrails, routing) is per-gateway.

### Request Flow

```
Client → Cloudflare Edge (AI Gateway) → Provider API → Response
                      ↑
               Cache / Rate Limit / Guardrails / Logging / DLP checks happen here
```

---

## 2. URL Format and Endpoint Structure

### Provider-Specific Endpoints

```
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/{provider}
```

Example for OpenAI:

```
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/openai
```

### OpenAI-Compatible Unified Endpoint (`/compat`)

Introduced 2025-05-28. Allows any OpenAI SDK client to point at Cloudflare AI Gateway without provider-specific URL changes:

```
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/compat
```

This is the recommended approach for multi-provider setups. The gateway translates to the appropriate provider format.

### Universal Endpoint (for fallback chains)

The Universal endpoint accepts a JSON array of provider configs and attempts them in order:

```
POST https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}
```

Request body is an array of provider objects, each specifying the provider, endpoint, headers, and query params.

### Dynamic Routing Endpoint

Named routes under the gateway:

```
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/dynamic/{route_name}
```

### Models Endpoint

Lists available models with cost metadata (added 2025-09-19):

```
GET https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/compat/v1/models
```

### Custom Provider Endpoint

For self-hosted or non-native providers:

```
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/custom-{slug}/{provider-path}
```

---

## 3. Authentication

### Provider Key Passthrough (Default)

Pass your provider API key in the Authorization header as you normally would. The gateway forwards it to the provider. No additional Cloudflare auth needed for unauthenticated gateways.

```
Authorization: Bearer {provider_api_key}
```

### Authenticated Gateway Mode

Enable "Authenticated Gateway" in settings to require a Cloudflare API token on every request via:

```
cf-aig-authorization: Bearer {cloudflare_api_token}
```

Both the gateway auth header AND the provider key must be present simultaneously for authenticated gateways.

### BYOK (Bring Your Own Keys)

Introduced 2025-08-21. Store provider API keys in Cloudflare's encrypted Secret Store. At request time, specify which stored key to use:

```
cf-aig-byok-alias: {key_alias}
```

Keys are encrypted at rest (AES) and in transit. Supports 20+ providers. Secrets are scoped to AI Gateway only — they cannot be used elsewhere on Cloudflare's infrastructure. Supports WebSocket transport (added 2025-09-19).

### Unified Billing (Auth via Cloudflare Credits)

For Unified Billing providers, no provider API key is needed. Use only your Cloudflare API token; Cloudflare's own credentials are used with the provider, and credits are deducted from your account balance.

Supported providers for Unified Billing:

- OpenAI
- Anthropic
- Google AI Studio
- xAI
- Groq

---

## 4. Supported Providers (24 as of early 2026)

| #   | Provider         | Notes                                         |
| --- | ---------------- | --------------------------------------------- |
| 1   | Workers AI       | Native; no extra token needed post-2025-11-14 |
| 2   | OpenAI           | Full support incl. Responses API, WebSocket   |
| 3   | Anthropic        | Unified Billing supported                     |
| 4   | Google AI Studio | Unified Billing supported                     |
| 5   | Google Vertex AI | Unified API support added 2025-09-19          |
| 6   | Azure OpenAI     | Supported                                     |
| 7   | Amazon Bedrock   | Supported                                     |
| 8   | Mistral AI       | Supported                                     |
| 9   | Cohere           | Supported                                     |
| 10  | Groq             | GA 2025-06-18; Unified Billing                |
| 11  | xAI (Grok)       | Unified Billing supported                     |
| 12  | DeepSeek         | GA 2025-06-18; added 2025-01-02               |
| 13  | Replicate        | Supported                                     |
| 14  | HuggingFace      | Supported                                     |
| 15  | Perplexity       | Supported                                     |
| 16  | OpenRouter       | GA 2025-06-18                                 |
| 17  | ElevenLabs       | GA 2025-06-18; voice cost tracking            |
| 18  | Cartesia         | GA 2025-06-18; voice                          |
| 19  | Cerebras         | GA 2025-06-18                                 |
| 20  | Fal AI           | Added 2025-09-21                              |
| 21  | Baseten          | Added 2025-11-03                              |
| 22  | Ideogram         | Added 2025-11-03                              |
| 23  | Deepgram         | Added 2025-11-03; WebSocket + Workers AI      |
| 24  | Parallel         | Added 2025-10-07                              |

Plus: **Custom Providers** via OpenAI-compatible API (added 2025-11-14). This means any OpenAI-compatible endpoint can be plugged in.

---

## 5. Caching

### Exact Match Only (as of early 2026)

Cache is keyed on the full request body. Only byte-for-byte identical requests hit the cache. Semantic/vector caching is listed as planned but not yet released.

### Cache Headers

| Header                | Direction | Purpose                                                                              |
| --------------------- | --------- | ------------------------------------------------------------------------------------ |
| `cf-aig-cache-ttl`    | Request   | Set TTL in seconds (min 60s, max ~1 month)                                           |
| `cf-aig-skip-cache`   | Request   | Bypass cache; fetch from provider                                                    |
| `cf-aig-cache-key`    | Request   | Override the default cache key (allows per-user caching by including user ID in key) |
| `cf-aig-cache-status` | Response  | `HIT` or `MISS`                                                                      |

### Cache Behavior Details

- Cache TTL is set globally at the gateway level or overridden per-request via `cf-aig-cache-ttl`
- Cache supports text and image responses (not audio/video)
- Volatile cache: simultaneous identical requests may not share a cache entry (race condition at cache population)
- Cache hits always show $0 cost in analytics
- Cache key was updated 2025-04-02, causing a transition period of increased misses
- Cache hit rates are tracked in the analytics dashboard and reported as a percentage

### Per-User Caching

No native per-user caching concept, BUT you can implement it by setting `cf-aig-cache-key` to include a user identifier, which namespaces the cache. This is a manual approach.

### Claimed Benefit

Up to 90% latency reduction for cached responses served from Cloudflare's edge network.

---

## 6. Rate Limiting

### Configuration

Rate limiting is configured at the gateway level via the dashboard or API. Three parameters:

| Parameter                 | Description                            |
| ------------------------- | -------------------------------------- |
| `rate_limiting_interval`  | Time window in seconds (e.g., 60)      |
| `rate_limiting_limit`     | Max requests in the window (e.g., 100) |
| `rate_limiting_technique` | `fixed` or `sliding`                   |

### Techniques

- **Fixed Window**: Time buckets (e.g., 12:00–12:01). All requests in that bucket count toward the limit.
- **Sliding Window**: Continuously calculates requests in the last N seconds, preventing burst clustering at window boundaries.

### Response on Limit Exceeded

HTTP 429 Too Many Requests.

### Scope

Rate limiting applies uniformly to all requests for a gateway. As of early 2026:

- No per-user rate limiting at the gateway level natively
- Dynamic Routing's Rate Limit nodes enable per-key quota enforcement (the more granular approach)
- No per-IP rate limiting is documented

### Dynamic Routing Rate Limits

Via Dynamic Routing, you can configure **Rate Limit nodes** that enforce cost quotas per key per period and switch to a fallback model when exceeded. This is the recommended path for per-user/per-key rate limiting.

---

## 7. Observability

### Analytics Dashboard

Available at AI > AI Gateway in the Cloudflare dashboard. Tracks:

1. **Requests** — Total count over time
2. **Token Usage** — Input/output token breakdown
3. **Costs** — Provider cost breakdown; cache hits show $0
4. **Errors** — Error counts and types
5. **Cached Responses** — Cache hit rate percentage

Time range filtering available. GraphQL API access for external querying.

### Logging

**What is logged per request:**

- User prompt
- Model response
- Provider
- Timestamp
- Request status
- Token usage (input + output)
- Cost estimate
- Duration
- Cache status
- Custom metadata

**Storage Limits:**
| Plan | Log Limit |
|------|-----------|
| Free | 100,000 logs per account (across all gateways) |
| Paid | 10,000,000 logs per gateway |

**Rate limit:** 500 logs/second per gateway; 10 MB max per log (larger logs not stored).

**Log Filtering (dashboard):**
Status, cache status, provider, model, cost threshold, request type (Universal/Workers AI/WebSocket), token count, duration, feedback (thumbs up/down), custom metadata key-value, log ID/event ID.

**Storage Behavior Options:**

- Auto-delete oldest logs when limit reached
- Stop storing new logs when limit reached
- Manual deletion via dashboard or API

**Logpush:** Export logs to external storage (S3, R2, Splunk, etc.). Requires Workers Paid plan. 4 jobs max per account; 1 MB max per log for Logpush. 10M requests/month included; $0.05/M overage.

### Custom Metadata

Attach up to 5 custom key-value pairs per request via `cf-aig-metadata` header (JSON-encoded). Accepted types: string, number, boolean. Objects are not supported. Appears in logs and enables filtering.

```
cf-aig-metadata: {"user_id": "u_123", "team": "eng", "env": "prod"}
```

### OpenTelemetry (OTEL)

Added 2025-09-24. Export traces from AI Gateway to any OTEL-compatible backend (Jaeger, Zipkin, Grafana, Datadog, etc.). Enables distributed tracing across the full request lifecycle.

### Response Tracking Headers

| Header                | Description                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------------ |
| `cf-aig-event-id`     | Unique event identifier (returned on all requests including failures, added 2025-10-24)          |
| `cf-aig-log-id`       | Log entry identifier; used for feedback submission                                               |
| `cf-aig-step`         | Which provider in the fallback chain handled the request (0 = primary, 1 = first fallback, etc.) |
| `cf-aig-cache-status` | `HIT` or `MISS`                                                                                  |

### Cost Tracking

Per-request cost estimates based on token usage × model pricing. Custom pricing overrides supported via `cf-aig-custom-cost` header (for negotiated rates):

```
cf-aig-custom-cost: {"per_token_in": 0.000001, "per_token_out": 0.000002}
```

Voice model cost/usage tracking added 2025-11-14. Async video generation (OpenAI Sora 2, Google Veo 3) cost tracking added 2025-10-24.

---

## 8. Guardrails

Added 2025-02-26.

### What It Does

Real-time content moderation applied to both incoming user prompts AND outgoing model responses. Acts as a proxy-level filter across all providers uniformly.

### How It Works

1. Request intercepted at edge
2. Prompt scanned against configured content categories
3. If flagged: either block (return error) or flag (log and pass through)
4. Response intercepted
5. Response scanned against configured content categories
6. Same block/flag action applied

### Content Categories

Examples from documentation: violence, hate, sexual content. The full category list is configurable via the dashboard. Categories can be independently configured for prompts vs. responses.

### Actions

- **Block**: Return error response to client; provider is never called
- **Flag**: Pass through but mark in logs for compliance/audit trails

### Audit Trails

All guardrail decisions are logged with details for compliance and regulatory tracking (GDPR, HIPAA, etc.).

---

## 9. Data Loss Prevention (DLP)

Added 2025-08-28. Part of the AI Gateway Firewall.

### What It Detects

Pre-built profiles include:

- Financial data (credit card numbers, bank accounts)
- Social Security / Tax Identifiers
- PII (personally identifiable information)
- Healthcare data (HIPAA-relevant)
- Custom patterns (user-defined)

Compliance frameworks supported: GDPR, HIPAA, PCI DSS.

### How It Works

DLP profiles are selected in the Firewall settings. The gateway scans:

- Incoming prompts (before reaching the model)
- Outgoing AI responses (before reaching the client)

For each request, the log shows which DLP profiles matched and what action was taken.

### Actions

- **Block**: Reject the request/response
- **Alert/Flag**: Allow but log the match with details

### Configuration

Select pre-built or custom DLP profiles in the AI Gateway Firewall dashboard settings. No per-request configuration needed — it's a gateway-level policy.

---

## 10. Evaluations

### What It Is

A built-in evaluation system for assessing AI application performance against logs. Helps answer: Is my model accurate? Fast enough? Cost-effective?

### How It Works

1. **Create a Dataset**: Apply filters in the Logs tab to select a set of logs for analysis
2. **Select Evaluators**: Choose which metrics to measure
3. **Run Evaluation**: Get results across the dataset

### Available Evaluators

- **Human Feedback** (currently in open beta): Measures % of positive (thumbs up) ratings on logged requests. Requires feedback submission via API using `cf-aig-log-id` response header.
- Additional evaluators are planned but not yet released.

### Metrics Tracked

- Cost (per request, per dataset)
- Latency (duration)
- Accuracy (via human feedback %)

### Limits

- 10 datasets per gateway

### Model Playground

Added 2025-10-14. A dashboard UI to send test requests and compare model behavior across supported models without writing code. Useful for model selection and debugging.

---

## 11. Fallback Behavior

### Universal Endpoint Fallbacks

The Universal endpoint accepts a JSON array of provider objects. The gateway tries them in order:

```json
[
  {
    "provider": "openai",
    "endpoint": "chat/completions",
    "headers": { "Authorization": "Bearer sk-..." },
    "query": {}
  },
  {
    "provider": "workers-ai",
    "endpoint": "@cf/meta/llama-3.1-8b-instruct",
    "headers": { "Authorization": "Bearer cf-..." },
    "query": {}
  }
]
```

Fallback triggers:

- Request errors (any error response from provider)
- Request timeouts (configurable via `requestTimeout` in ms)

### Response Tracking

`cf-aig-step` header in the response indicates which provider succeeded:

- `0` = primary provider
- `1` = first fallback
- `N` = Nth fallback

### Retry Behavior

Separate from fallbacks. Per-request retry configuration:

| Header                   | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `cf-aig-max-attempts`    | Max retry attempts (up to 5)                     |
| `cf-aig-retry-delay`     | Delay between retries (ms, max 5000)             |
| `cf-aig-backoff`         | Strategy: `constant`, `linear`, or `exponential` |
| `cf-aig-request-timeout` | Timeout to trigger fallback/retry (ms)           |

**Note:** Dynamic Routing is now the preferred approach for advanced fallback/routing logic.

---

## 12. Dynamic Routing

Added 2025-08-25. This is the flagship feature of the August 2025 refresh.

### What It Does

Define routing flows visually (drag-and-drop UI) or via JSON without modifying application code. Flows are versioned and instantly rollback-able.

### Node Types

| Node             | Description                                                                            |
| ---------------- | -------------------------------------------------------------------------------------- |
| **Conditional**  | Branch on request body, headers, or metadata expressions (e.g., `user_plan == 'paid'`) |
| **Percentage**   | Probabilistic traffic split — e.g., 80% to GPT-4o, 20% to Claude (A/B testing)         |
| **Rate Limit**   | Enforce per-key cost/request quotas per period; switch to fallback when exceeded       |
| **Budget Limit** | Cap spending per key per period                                                        |
| **Provider**     | Route to a specific provider/model                                                     |
| **Fallback**     | Define what happens when a provider fails                                              |

### Use Cases

- **A/B Testing**: Split traffic 80/20 between two models
- **User Segmentation**: Paid users → GPT-4o, free users → GPT-4o-mini
- **Per-User Quotas**: Rate limit free tier users, fallback to cheaper model when quota exceeded
- **Model Chaining**: Send prompt through a custom guardrails model before the main model
- **Gradual Rollouts**: Slowly increase traffic to a new model

### Configuration

Visual interface in the AI Gateway dashboard. Each change creates a draft version. Deploy to make live. Instant rollback available.

JSON-based configuration also supported for programmatic management.

### Access

Routes are accessed via:

```
https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/dynamic/{route_name}
```

---

## 13. Load Balancing

Cloudflare AI Gateway does not have a native "load balancing" feature in the traditional sense (round-robin, weighted). However:

- **Dynamic Routing Percentage nodes** enable traffic splitting (e.g., 50/50 between providers) — effectively weighted load balancing
- **Dynamic Routing Conditional nodes** enable rule-based routing (geography, user type)
- **Fallbacks** in the Universal endpoint provide failure-based routing

No active health checking or automatic least-connections balancing is documented.

---

## 14. Streaming Support

### SSE (Server-Sent Events) Streaming

Standard streaming (text tokens via SSE) is supported through all provider-specific endpoints and the `/compat` endpoint. The gateway passes the stream through.

### WebSocket API

Added 2025-03-18. Persistent WebSocket connections for lower-latency AI interactions:

- Endpoint: `wss://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/websockets-api/realtime-api/`
- Supports OpenAI Realtime API (including voice)
- BYOK support for WebSocket transport (added 2025-09-19)
- Deepgram via WebSocket on Workers AI (added 2025-10-07)
- Pipecat model support on Workers AI (added 2025-10-29)

### Async Video Generation

Cost tracking and observability for async video generation added 2025-10-24, covering:

- OpenAI Sora 2
- Google AI Studio Veo 3

---

## 15. Workers AI Integration

Workers AI is Cloudflare's own model inference service running on their edge. It is deeply integrated with AI Gateway:

- Access via `env.AI.run()` in Workers scripts — no additional API token needed after 2025-11-14
- Available as a provider in the Universal endpoint and Dynamic Routing flows
- Supports Deepgram models via WebSocket
- Supports Pipecat models (voice/audio pipelines)
- No extra authentication configuration needed (native binding within Cloudflare account)

Workers AI models are served from Cloudflare's GPU infrastructure globally. Combined with AI Gateway, this gives Cloudflare a fully integrated edge inference + observability stack.

---

## 16. Request Extensions (cf-aig- Headers)

Complete glossary of all `cf-aig-` prefixed headers:

| Header                   | Direction | Description                                             |
| ------------------------ | --------- | ------------------------------------------------------- |
| `cf-aig-authorization`   | Request   | Cloudflare API token for authenticated gateway mode     |
| `cf-aig-cache-ttl`       | Request   | Cache TTL in seconds (60 to ~2.6M)                      |
| `cf-aig-skip-cache`      | Request   | Set to `true` to bypass cache                           |
| `cf-aig-cache-key`       | Request   | Override default cache key                              |
| `cf-aig-cache-status`    | Response  | `HIT` or `MISS`                                         |
| `cf-aig-collect-log`     | Request   | Override gateway log collection setting                 |
| `cf-aig-custom-cost`     | Request   | JSON: `{"per_token_in": float, "per_token_out": float}` |
| `cf-aig-metadata`        | Request   | JSON: up to 5 key-value pairs (string/number/boolean)   |
| `cf-aig-request-timeout` | Request   | Timeout in ms before triggering fallback/retry          |
| `cf-aig-max-attempts`    | Request   | Retry count (max 5)                                     |
| `cf-aig-retry-delay`     | Request   | Delay between retries in ms (max 5000)                  |
| `cf-aig-backoff`         | Request   | `constant`, `linear`, or `exponential`                  |
| `cf-aig-byok-alias`      | Request   | Which stored key alias to use                           |
| `cf-aig-zdr`             | Request   | Enable Zero Data Retention for this request             |
| `cf-aig-step`            | Response  | Which fallback step handled the request (0=primary)     |
| `cf-aig-event-id`        | Response  | Unique event ID (all requests, including failures)      |
| `cf-aig-log-id`          | Response  | Log entry ID for feedback submission                    |

### Configuration Hierarchy

1. Provider-level request headers (highest priority)
2. Request-level headers
3. Gateway-level settings (dashboard defaults)

---

## 17. Pricing Model

### Free Tier (All Plans)

Cloudflare AI Gateway is available on all Cloudflare plans with no plan gating for core features. Core features available free:

- Caching
- Rate limiting
- Analytics dashboard
- Basic guardrails

### Log Storage

| Plan         | Included Logs                          |
| ------------ | -------------------------------------- |
| Workers Free | 100,000 logs total across all gateways |
| Workers Paid | 1,000,000 logs total; 10M per gateway  |

Additional log storage: tiered pricing based on monthly volume (exact rates not published).

### Logpush (Paid Only)

- Workers Paid plan required
- 10M requests/month included
- $0.05 per million additional requests
- Max 4 Logpush jobs per account

### Unified Billing

Credits loaded into Cloudflare account. Provider requests billed at list price + Cloudflare convenience/transaction fee (exact fee not publicly disclosed). Auto-replenishment available. Daily/weekly/monthly spend limits.

### Gateway Limits

| Plan | Max Gateways   |
| ---- | -------------- |
| Free | 10 per account |
| Paid | 20 per account |

### No Per-Request or Per-Token Fees

There is no Cloudflare-imposed fee per AI request or per token (beyond Unified Billing transaction fees). The gateway itself is free to use; you pay the provider.

---

## 18. Unique Features vs. OpenRouter / LiteLLM / Portkey

### What Cloudflare Has That Others Don't

| Feature                       | Cloudflare          | OpenRouter        | LiteLLM         | Portkey      |
| ----------------------------- | ------------------- | ----------------- | --------------- | ------------ |
| **Edge-native caching**       | Yes (CDN edge)      | No                | No              | No           |
| **Workers AI native binding** | Yes                 | No                | No              | No           |
| **DLP in Firewall**           | Yes (with profiles) | No                | No              | Limited      |
| **Dynamic Routing (visual)**  | Yes (visual + JSON) | No                | No              | Limited      |
| **WebSocket/Realtime**        | Yes                 | No                | Partial         | No           |
| **Zero Data Retention**       | Yes (per-provider)  | No                | No              | Partial      |
| **Unified Billing**           | Yes (5 providers)   | No (you pay each) | No              | No           |
| **BYOK Secret Store**         | Yes (encrypted)     | No                | No              | Virtual keys |
| **OTEL Export**               | Yes                 | No                | Yes             | Yes          |
| **Model Playground**          | Yes                 | No                | No              | No           |
| **Custom Cost Override**      | Yes (per request)   | No                | Yes             | Yes          |
| **Async Video Tracking**      | Yes (Sora/Veo)      | No                | No              | No           |
| **Global Edge PoPs**          | 300+                | No (SaaS)         | Self-hosted     | SaaS         |
| **Logpush to S3/R2**          | Yes                 | No                | No              | No           |
| **Custom Providers**          | Yes (OAI-compat)    | No                | Yes             | No           |
| **Evaluation System**         | Yes (beta)          | No                | No              | Yes          |
| **Semantic Caching**          | Planned             | No                | Yes             | Yes          |
| **Deployment Model**          | SaaS/Managed        | SaaS              | OSS/Self-hosted | SaaS         |
| **Free Tier**                 | Generous            | Usage markup      | Free OSS        | $49/mo       |

### Where Cloudflare Falls Short

- **Semantic caching**: Not yet released. LiteLLM and Portkey have it.
- **Per-user rate limiting**: Only through Dynamic Routing, not native header-based.
- **Evaluation depth**: Only human feedback currently (in beta). Portkey has more evaluation types.
- **Model coverage in Unified Billing**: Only 5 providers. LiteLLM supports 100+ providers.
- **Self-hosted option**: SaaS only. No on-premise deployment. LiteLLM is OSS.
- **Vendor lock-in**: Best value when on Cloudflare stack. Workers AI, Logpush to R2 create lock-in.
- **Performance overhead**: Bifrost claims 11µs overhead; Cloudflare's overhead is unquantified.

---

## 19. Edge-Specific Advantages

1. **Global Cache Proximity**: Cached responses served from the nearest of 300+ PoPs, not a centralized region. Sub-millisecond latency for cache hits.

2. **CDN-Grade Infrastructure**: Leverages the same network used for Cloudflare's CDN — proven at massive scale (millions of requests/second globally).

3. **Integrated DDoS Protection**: Cloudflare's DDoS mitigation applies to AI Gateway traffic automatically. Rate limiting + DDoS = double protection.

4. **Workers AI Colocation**: When using Workers AI, model inference and the gateway are on the same edge node, eliminating network hops entirely.

5. **Edge Routing Decisions**: Dynamic Routing evaluates routing rules at the edge, not in a centralized server. Decision latency is minimal.

6. **Cloudflare Ecosystem Integration**: Seamless integration with R2 (log storage), Workers (custom logic), Secret Store (BYOK), Zero Trust, DLP, and the broader Cloudflare platform.

7. **TLS Termination at Edge**: All connections terminate at the nearest Cloudflare PoP; backend connections to providers are from Cloudflare's infrastructure with optimized routing (Argo Smart Routing can apply).

---

## 20. Webhooks / Integrations

No native webhook system documented. Integration is via:

- **Logpush**: Push logs to external destinations (S3, R2, Splunk, Sumo Logic, New Relic, etc.)
- **GraphQL Analytics API**: Query metrics programmatically
- **OpenTelemetry**: Trace export to any OTEL backend
- **Workers**: Custom Workers scripts can intercept, transform, or react to AI Gateway requests (since Workers run on the same edge)
- **Cloudflare Notifications**: Cloudflare's general alerting system may cover gateway events

---

## 21. Changelog Summary (2025 to 2026-02-20)

| Date       | Feature                                                                     |
| ---------- | --------------------------------------------------------------------------- |
| 2025-01-02 | DeepSeek added                                                              |
| 2025-02-05 | ElevenLabs, Cartesia, Cerebras added                                        |
| 2025-02-06 | Request handling options (retries, timeouts)                                |
| 2025-02-19 | Customizable log storage settings                                           |
| 2025-02-26 | **Guardrails** (content moderation for prompts + responses)                 |
| 2025-03-18 | **WebSockets API** (persistent connections)                                 |
| 2025-04-02 | Cache key calculation updated                                               |
| 2025-04-22 | Max gateways increased to 20; timeout limit extended                        |
| 2025-05-28 | **OpenAI-compatible `/compat` endpoint**                                    |
| 2025-06-18 | 5 providers graduated from beta to GA                                       |
| 2025-08-21 | **BYOK** via Cloudflare Secret Store                                        |
| 2025-08-25 | **Dynamic Routing** (visual flow + A/B + quotas)                            |
| 2025-08-28 | **Data Loss Prevention (DLP)** in Firewall                                  |
| 2025-09-19 | `/compat/v1/models` endpoint; Vertex AI Unified API; BYOK for WebSocket     |
| 2025-09-21 | Fal AI added; Custom Stripe usage reporting                                 |
| 2025-09-24 | **OpenTelemetry (OTEL) tracing export**                                     |
| 2025-10-07 | Deepgram WebSocket on Workers AI; Parallel provider added                   |
| 2025-10-14 | **Model playground** in dashboard                                           |
| 2025-10-24 | Async video cost tracking (Sora 2, Veo 3); `cf-aig-eventId` on all requests |
| 2025-10-29 | Pipecat on Workers AI; OpenAI Realtime WebSocket auth fix                   |
| 2025-11-03 | Baseten, Ideogram, Deepgram added                                           |
| 2025-11-06 | **Unified Billing** open beta                                               |
| 2025-11-14 | Custom Provider support; voice model costs; Workers AI no-token-needed      |
| 2025-11-21 | **Zero Data Retention** opt-in for Unified Billing providers                |

---

## 22. Sources

- [Cloudflare AI Gateway Overview](https://developers.cloudflare.com/ai-gateway/)
- [Getting Started](https://developers.cloudflare.com/ai-gateway/get-started/)
- [Providers List](https://developers.cloudflare.com/ai-gateway/providers/)
- [Changelog](https://developers.cloudflare.com/ai-gateway/changelog/)
- [Logging](https://developers.cloudflare.com/ai-gateway/observability/logging/)
- [Analytics](https://developers.cloudflare.com/ai-gateway/observability/analytics/)
- [Custom Metadata](https://developers.cloudflare.com/ai-gateway/observability/custom-metadata/)
- [Caching](https://developers.cloudflare.com/ai-gateway/configuration/caching/)
- [Rate Limiting](https://developers.cloudflare.com/ai-gateway/configuration/rate-limiting/)
- [Request Handling (Retries/Timeouts)](https://developers.cloudflare.com/ai-gateway/configuration/request-handling/)
- [Fallbacks](https://developers.cloudflare.com/ai-gateway/configuration/fallbacks/)
- [Guardrails](https://developers.cloudflare.com/ai-gateway/guardrails/)
- [Evaluations](https://developers.cloudflare.com/ai-gateway/evaluations/)
- [Features Index](https://developers.cloudflare.com/ai-gateway/features/)
- [Dynamic Routing](https://developers.cloudflare.com/ai-gateway/features/dynamic-routing/)
- [Unified Billing](https://developers.cloudflare.com/ai-gateway/features/unified-billing/)
- [Limits Reference](https://developers.cloudflare.com/ai-gateway/reference/limits/)
- [Pricing Reference](https://developers.cloudflare.com/ai-gateway/reference/pricing/)
- [OpenAI Provider](https://developers.cloudflare.com/ai-gateway/providers/openai/)
- [AI Gateway llms-full.txt](https://developers.cloudflare.com/ai-gateway/llms-full.txt)
- [August 2025 Refresh Blog Post](https://blog.cloudflare.com/ai-gateway-aug-2025-refresh/)
- [Best AI Gateways 2026 Comparison](https://www.getmaxim.ai/articles/5-best-ai-gateways-in-2026/)
