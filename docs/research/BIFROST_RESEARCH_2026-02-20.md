<DONE>
# Bifrost AI Gateway — Exhaustive Research Report
**Date:** 2026-02-20
**Researcher:** Claude Sonnet 4.6 (via thegent agent)
**Scope:** Competitive/peer analysis for thegent CLIProxy feature parity

---

## 1. Product Identification

**Which Bifrost?**

There are several products named "Bifrost" in the software ecosystem (a network security product, a game engine bridge, etc.). The one relevant to AI/LLM is:

**Bifrost by Maxim AI (maximhq/bifrost)**

- GitHub: https://github.com/maximhq/bifrost
- Website: https://www.getmaxim.ai/bifrost/
- Docs: https://docs.getbifrost.ai
- NPM: `@maximhq/bifrost`
- Docker Hub: `maximhq/bifrost`
- License: Apache 2.0

This is the correct product. It is an open-source, high-performance LLM gateway written in Go,
built by the team behind Maxim AI (an AI observability platform). It was released in late 2024 and
has seen rapid adoption into 2025–2026. The name does not correspond to `bifrost.so` (that domain
does not host a competing AI product as of this research date).

---

## 2. What Is Bifrost?

Bifrost is a self-hosted, open-source AI gateway (also called an LLM proxy or LLM gateway) that
provides:

1. A single, unified OpenAI-compatible HTTP API that routes requests across 15–20+ LLM providers
2. Intelligent routing with fallback, load balancing, and governance controls
3. Semantic caching (vector-similarity based, not exact-match)
4. Observability via Prometheus, OpenTelemetry, and native Maxim AI integration
5. Enterprise governance: virtual keys, hierarchical budgets, rate limiting, SSO, audit logs
6. Native MCP (Model Context Protocol) gateway support
7. An optional Web UI for configuration and monitoring

Its primary positioning is: **"50x faster than LiteLLM with enterprise-grade governance and
near-zero overhead."**

The performance claim is backed by benchmarks on AWS t3.medium at 500 RPS:

- Bifrost: 100% success rate, P99 = 1.68s, throughput = 424 req/s, memory = 120MB
- LiteLLM: 88.78% success rate, P99 = 90.72s, throughput = 44.84 req/s, memory = 372MB

At 5,000 RPS on t3.xlarge:

- Gateway overhead: 11 µs (mean)
- Queue wait time: 1.67 µs
- Success rate: 100%

This performance comes from the Go implementation, connection pooling with zero runtime memory
allocation, and a lock-free weighted key selection mechanism (~10 ns latency).

---

## 3. Architecture

### 3.1 Module Layout

```
bifrost/
├── core/           # Provider implementations, unified schemas, account model
│   └── schemas/    # account.go (key config, provider config)
├── framework/      # Data persistence layer
│   ├── configstore/ # Config storage (SQLite or PostgreSQL)
│   ├── logstore/    # Request/response log storage
│   └── vectorstore/ # Embeddings for semantic cache (Weaviate, Qdrant, Redis)
├── transports/     # HTTP gateway (bifrost-http binary)
│   └── bifrost-http/ # Starlette-equivalent: HTTP server, Web UI, REST API
└── plugins/        # Extensible middleware
    ├── governance/  # Budget management, virtual keys, access control
    ├── cache/       # Semantic cache plugin
    ├── logging/     # Request/response logger
    ├── maxim/       # Maxim AI observability integration
    ├── telemetry/   # Prometheus + OpenTelemetry
    ├── mock/        # Mock responses for testing
    └── jsonparser/  # JSON normalization
```

### 3.2 Deployment Modes

Bifrost offers three integration patterns:

**Mode 1 — HTTP Gateway (most common)**

```bash
# NPX one-liner
npx -y @maximhq/bifrost

# Docker
docker run -p 8080:8080 maximhq/bifrost

# Docker with persistence
docker run -p 8080:8080 -v $(pwd)/data:/app/data maximhq/bifrost
```

Default port: 8080. Optional flags: `-port`, `APP_PORT`, host binding, log format.

**Mode 2 — Go SDK Embedded**

```go
import "github.com/maximhq/bifrost/core"
// Direct in-process integration; bypasses HTTP transport
```

**Mode 3 — Drop-in SDK Replacement**
Change the base URL in existing SDK calls:

- OpenAI SDK: `base_url = "http://localhost:8080/openai"`
- Anthropic SDK: `base_url = "http://localhost:8080/anthropic"`
- Google GenAI: `base_url = "http://localhost:8080/genai"`

---

## 4. Authentication

### 4.1 Client → Bifrost

Bifrost itself accepts a "dummy" API key from the calling application:

```python
api_key = "dummy"  # Bifrost handles actual provider credentials
```

The real provider API keys are managed by Bifrost via:

- **Web UI** at `http://localhost:8080`
- **REST API** POST `/api/providers`
- **File-based** `config.json` (disables Web UI; requires restart on changes)

When governance is enabled, clients authenticate using a **virtual key** (`x-bf-vk` header).

### 4.2 Provider Credentials

Keys support environment variable injection using `env.VAR_NAME` syntax:

```json
{
  "providers": {
    "openai": {
      "keys": [
        {
          "value": "env.OPENAI_API_KEY",
          "models": ["gpt-4o-mini", "gpt-4o"],
          "weight": 1.0
        }
      ]
    }
  }
}
```

For Kubernetes: secrets injected via environment variables; Vault, AWS Secrets Manager, and Azure
Key Vault are supported as external secret managers.

---

## 5. API Compatibility

### 5.1 Primary Endpoint

```
POST http://localhost:8080/v1/chat/completions
```

This is fully OpenAI-compatible. Model IDs use `provider/model` format:

```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [{ "role": "user", "content": "Hello" }]
}
```

### 5.2 SDK-Specific Endpoints

Bifrost exposes provider-namespaced endpoints so existing SDK code needs only a base URL change:

| Endpoint Prefix                             | SDK Compatibility            |
| ------------------------------------------- | ---------------------------- |
| `http://localhost:8080/openai`              | OpenAI SDK                   |
| `http://localhost:8080/anthropic`           | Anthropic SDK                |
| `http://localhost:8080/genai`               | Google GenAI SDK             |
| `http://localhost:8080/v1/chat/completions` | Any OpenAI-compatible client |

### 5.3 Additional Endpoints

| Endpoint               | Purpose                           |
| ---------------------- | --------------------------------- |
| `GET /metrics`         | Prometheus metrics scrape         |
| `POST /api/providers`  | Add/update provider configuration |
| `/v1/mcp/tool/execute` | Explicit MCP tool execution       |

---

## 6. Supported Providers

As of 2026-02-20 (15–20+ providers):

| Provider         | Notes                                                                      |
| ---------------- | -------------------------------------------------------------------------- |
| OpenAI           | Full support including Responses API                                       |
| Anthropic        | Claude 3.x, Claude 4.x families                                            |
| AWS Bedrock      | Requires `access_key`, `secret_key`, `region`, `arn`; model-to-ARN mapping |
| Google Vertex AI | Requires deployment config                                                 |
| Azure OpenAI     | Requires `deployments` mapping + `api_version`                             |
| Cerebras         | Fast inference                                                             |
| Cohere           | Command family                                                             |
| Mistral          | Mistral 7B, Mixtral, etc.                                                  |
| Ollama           | Local models                                                               |
| Groq             | Ultra-fast inference                                                       |
| Google GenAI     | Gemini family                                                              |
| Hugging Face     | Via inference API                                                          |
| Together AI      | (documented)                                                               |
| Perplexity       | (documented)                                                               |

AWS Bedrock and Azure OpenAI require special key schemas:

**Bedrock key schema:**

```json
{
  "access_key": "env.AWS_ACCESS_KEY_ID",
  "secret_key": "env.AWS_SECRET_ACCESS_KEY",
  "session_token": "env.AWS_SESSION_TOKEN",
  "region": "us-east-1",
  "arn": "arn:aws:bedrock:...",
  "deployments": {
    "claude-3-5-sonnet": "inference-profile-id"
  }
}
```

**Azure key schema:**

```json
{
  "value": "env.AZURE_API_KEY",
  "deployments": {
    "gpt-4o": "my-prod-gpt4o-deployment"
  },
  "api_version": "2024-10-21"
}
```

---

## 7. Routing Strategies

Bifrost implements a three-layer routing pipeline with explicit precedence:

```
Request → Routing Rules → Governance Routing → Adaptive Load Balancing
          (CEL-based)     (weighted random)     (performance scoring)
```

### 7.1 Routing Rules (Dynamic, CEL-based)

Evaluated first; override provider/model if matched. Uses Common Expression Language (CEL).

Available context variables:

```
model, provider                        // Request model/provider
headers["x-tier"]                      // Request headers
params["region"]                       // Request parameters
virtual_key_id, team_name, customer_id // Org context
budget_used, tokens_used               // Capacity metrics (0–100%)
request                                // Full request object
```

Example rules:

```cel
headers["x-tier"] == "premium"                              // Premium tier routing
budget_used > 85                                             // Failover at budget threshold
team_name == "ml-research"                                  // Team-based routing
headers["x-environment"] == "production" && tokens_used < 75 // Conditional routing
```

Scope hierarchy (first match wins): VirtualKey → Team → Customer → Global

If a rule matches: override provider/model, skip governance, proceed to key selection.

### 7.2 Governance Routing (Explicit, Weighted)

When no routing rule matches, governance runs. Uses virtual key `provider_configs`:

- Validates requested models against `allowed_models`
- Filters providers by budget limits and rate limits
- Applies weighted random selection among eligible providers
- Generates fallback chain from remaining providers sorted by weight (descending)

**Allowed models configuration:**

- Empty array: delegates to Model Catalog (all models the provider supports)
- Explicit list: restricts to those models only; supports `openai/gpt-4o` prefix format

### 7.3 Adaptive Load Balancing (Performance-Scored, Enterprise)

Always runs for key selection; optionally runs for provider selection.

**Level 1 — Provider selection** (skipped if provider already specified by routing rule or governance):

1. Lookup candidate providers from Model Catalog
2. Filter by allowed models and key availability
3. Score each provider: error rate (50% weight), latency via MV-TACOS (20%), utilization (5%)
4. Weighted random selection with jitter

**Level 2 — Key selection** (always runs, even when provider is pre-specified):

1. Fetch all keys for selected provider
2. Filter by key model restrictions
3. Score each key: error rate, latency, TPM hits, health state
4. Weighted random with 25% exploration factor
5. Skip circuit-broken keys (zero weight)

**Health state machine:** Healthy → Degraded → Failed → Recovering

- Fast recovery: 90% penalty reduction in 30 seconds
- Exploration probes allow potentially recovered routes to be retried

### 7.4 Model Catalog

Bifrost maintains an internal model catalog that:

- Downloads pricing data from `https://getbifrost.ai/datasheet` (synced at startup + every 24h)
- Calls each provider's `/v1/models` endpoint at startup and on provider add/update
- Provides `O(1)` lookup for model-to-provider mappings
- Powers routing decisions and UI dropdowns

Pricing lookup fallback chain: Gemini→Vertex, vertex format stripping, Bedrock prefix, Responses→Chat modes.

---

## 8. Fallbacks and Reliability

### 8.1 Automatic Fallbacks

When a request fails (provider error, rate limit, timeout):

- **Governance mode**: remaining providers sorted by weight (descending), tried in order
- **Load balancing mode**: remaining providers sorted by performance score (descending)
- **Routing rules**: explicitly defined fallback chains within rule conditions

### 8.2 Circuit Breaking

Bifrost's key health state machine acts as a circuit breaker per API key:

- Keys in `Failed` state are assigned zero weight (skipped)
- Keys in `Recovering` state are probed by the 25% exploration factor
- Error penalties applied immediately on failure

### 8.3 Retry Settings

Per-provider granular configuration includes retry counts, network proxy configuration, pool sizes, and timeouts. Specific retry knobs are available but not fully documented in public docs.

### 8.4 Claimed Reliability

"99.99% uptime for your applications" via automatic failover. At 5,000 RPS benchmark: 100% success rate (0 failed requests).

---

## 9. Semantic Caching

Bifrost's cache stores responses based on request _meaning_ (semantic similarity) rather than exact
string matching. This is the differentiating feature vs. most gateways that use exact-match caches.

### 9.1 Configuration Parameters

```json
{
  "cache": {
    "provider": "openai",
    "embedding_model": "text-embedding-3-small",
    "ttl": 3600,
    "threshold": 0.8,
    "conversation_history_threshold": 0.7,
    "cache_by_model": true,
    "cache_by_provider": false
  }
}
```

| Parameter                        | Description                                       |
| -------------------------------- | ------------------------------------------------- |
| `embedding_model`                | Model used to embed prompts for similarity search |
| `ttl`                            | Time-to-live in seconds                           |
| `threshold`                      | Cosine similarity cutoff (0.8 = 80% similar)      |
| `conversation_history_threshold` | Threshold for multi-turn caching                  |
| `cache_by_model`                 | Separate cache per model                          |
| `cache_by_provider`              | Separate cache per provider                       |

### 9.2 Vector Store Backends

| Backend  | Notes                            |
| -------- | -------------------------------- |
| Weaviate | 50Gi+ recommended for production |
| Qdrant   | External instance supported      |
| Redis    | Supported                        |

Vector store is optional; can be disabled if semantic caching is not needed.

### 9.3 Performance

- Cache hit latency: ~5ms end-to-end
- Cache miss with embedding + vector search: ~60ms
- Full LLM call: ~2,000ms
- Reported cost reduction: 10–25% from caching alone; 30–85% total with routing optimizations

### 9.4 Prometheus Cache Metrics

```
bifrost_cache_hits_total    // Count of cache hits
```

---

## 10. Observability and Logging

### 10.1 Prometheus Metrics

Native Prometheus at `/metrics` endpoint. Key metrics:

| Metric                            | Description                 |
| --------------------------------- | --------------------------- |
| `bifrost_upstream_requests_total` | Total requests to providers |
| `bifrost_cost_total`              | Real-time USD cost tracking |
| `bifrost_cache_hits_total`        | Cache hit count             |

**Custom labels via request headers:**
| Header | Purpose |
|--------|---------|
| `x-bf-prom-team` | Tag metrics by team |
| `x-bf-prom-environment` | Tag metrics by environment |

### 10.2 OpenTelemetry

Native OTLP (HTTP collector) support:

```json
{
  "telemetry": {
    "service_name": "bifrost-gateway",
    "collector_url": "http://otel-collector:4318",
    "trace_type": "genai_extension",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

Uses GenAI OpenTelemetry semantic conventions (`genai_extension` trace type).

### 10.3 Structured Logging

Request/response logging with two backends:

- **SQLite** (default, development): `logs.db`
- **PostgreSQL** (production): configurable via connection string

Logged fields: request/response content, token usage, costs, latency, error details.

### 10.4 Maxim AI Native Integration

Plugin-based integration with Maxim's observability platform:

- Automatic trace forwarding (all requests/responses)
- Session grouping via `session-id` tag
- Trace/generation ID propagation
- Repository-based routing for trace organization
- Threshold-based alerting for quality and latency
- A/B testing and simulation support

**Plugin config (Go SDK):**

```go
cfg := maxim.Config{
    ApiKey:    "MAXIM_API_KEY",
    LogRepoId: "repo-id",
}
```

### 10.5 Web UI Dashboard

Built-in real-time dashboard at `http://localhost:8080`:

- Request analytics (volume, latency, cost, errors)
- Provider health status
- Cache hit rate visualization
- Model catalog browser
- Virtual key management
- Budget utilization charts

The Web UI requires SQLite backend (`config.db`). File-only mode disables the UI.

---

## 11. Cost Tracking

### 11.1 Real-Time Cost Metrics

- `bifrost_cost_total` Prometheus metric tracks spend in real-time (USD)
- PostgreSQL log backend captures per-request cost with token counts
- Pricing data downloaded from Bifrost's datasheet endpoint (updated every 24h)

### 11.2 Budget Management

**Hierarchical budget structure:**

```
Customer → Team → Virtual Key → Provider Config
```

Each level supports:

```json
{
  "max_limit": 500.0,
  "duration": "1M",
  "rate_limits": {
    "max_tokens_per_hour": 1000000,
    "max_requests_per_hour": 10000
  }
}
```

When a budget is exhausted:

- Requests at that scope are blocked (hard limit, not silent degradation)
- Fallback logic can be configured to try alternative providers within budget
- Monthly auto-reset supported

---

## 12. Rate Limiting

Rate limiting operates at two levels:

**Virtual Key level:**

- `max_tokens_per_hour`: Token-based rate limiting
- `max_requests_per_hour`: Request count rate limiting

**Adaptive Load Balancing:**

- Keys at or near TPM (tokens per minute) limits are down-weighted
- Circuit breaker transitions to `Failed` state prevent key abuse
- 25% exploration keeps recovering keys in the rotation

Rate-limited providers are excluded from governance routing (`filter providers by rate limits` step).

---

## 13. Virtual Keys and Team/User Management

Virtual keys are Bifrost's primary governance abstraction. They sit between the calling application
and the provider credentials.

### 13.1 What a Virtual Key Provides

- **Access control**: which models and providers the key can use
- **Budget caps**: per-key or per-scope monthly spend limits
- **Rate limits**: token and request rate limits
- **Routing rules**: CEL expressions scoped to the key
- **Provider configs**: explicit provider allowlists with weights

### 13.2 Organizational Hierarchy

```
Customer (tenant)
└── Team
    └── User
        └── Virtual Key (API token issued to application)
```

Each level can have independent budget and rate limits. The system enforces the most restrictive
limit in the hierarchy.

### 13.3 Enterprise SSO

OpenID Connect (OIDC) integration:

- Supported IdPs: Okta, Microsoft Entra ID (Azure AD)
- SAML 2.0 support (Enterprise tier)
- Active Directory / LDAP sync
- Role mapping: Admin, Developer, Viewer (highest privilege wins on conflict)
- Automatic user provisioning on first SSO login
- Team membership synchronized from IdP groups

---

## 14. MCP Gateway

Bifrost is both an MCP client (connects to MCP servers to discover tools) and an MCP server
(exposes tools to calling models).

### 14.1 How It Works

1. **Discovery**: Bifrost connects to configured MCP servers and discovers available tools
2. **Schema injection**: Discovered tools are injected into the model's function-calling schema
3. **Suggestion**: Model's chat completion response includes `tool_calls` suggesting tool use
4. **Execution**: Application explicitly calls `/v1/mcp/tool/execute` to run the tool
5. **Policy enforcement**: Which tools a virtual key/team can execute is configurable

**Key design decision**: Bifrost never auto-executes tools. The application retains control and
must explicitly call the execute endpoint. This is a deliberate security boundary.

### 14.2 Supported MCP Tool Categories

- Filesystem access
- Database queries
- Web search
- External system integration

### 14.3 Agent Mode

Documented "autonomous agent mode" for orchestrating multi-step tool workflows, but the explicit
execute boundary is maintained throughout.

---

## 15. Enterprise and Compliance

### 15.1 Deployment Compliance

- Self-hosted: prompts/responses never leave controlled infrastructure
- Targeted at healthcare (HIPAA), finance, government

### 15.2 Compliance Frameworks

- SOC 2 Type II
- GDPR
- ISO 27001
- HIPAA

Automated compliance monitoring, policy enforcement, and audit trail generation.

### 15.3 Audit Logs

Four audit report types:

1. Access audits (authentication events)
2. Usage audits (API consumption)
3. Data audits (access/modification tracking)
4. Compliance reports

Real-time security event tracking via customizable notification channels.

### 15.4 Secrets Management

- Kubernetes secrets
- Environment variable injection (`env.VAR_NAME` syntax)
- HashiCorp Vault integration
- AWS Secrets Manager
- Azure Key Vault

---

## 16. Cluster Mode and Kubernetes

### 16.1 Kubernetes Deployment (Helm)

```bash
helm install bifrost maximhq/bifrost --set image.tag=latest
```

**Production HA configuration:**

- 3 replicas minimum; HPA scaling to 20 replicas
- CPU target: 70% utilization
- Memory target: 80% utilization
- Resource limits: 2–4 CPU, 2–8GB RAM per pod
- Pod anti-affinity across node topology
- PostgreSQL backend (50Gi+ PVC)
- NGINX ingress with TLS/cert-manager

**Storage backends:**

- Development: SQLite with 10Gi PVC
- Production: PostgreSQL (recommended)
- Vector store: Weaviate, Qdrant, or Redis

### 16.2 Private Container Registries

Supports Google Artifact Registry, AWS ECR, Azure ACR, or self-hosted registries.

---

## 17. Configuration Format

### 17.1 config.json Schema

```json
{
  "providers": {
    "openai": {
      "keys": [
        {
          "id": "key-1",
          "name": "primary",
          "value": "env.OPENAI_API_KEY",
          "models": ["gpt-4o-mini", "gpt-4o"],
          "weight": 1.0,
          "enabled": true,
          "use_for_batch_api": false
        }
      ]
    },
    "anthropic": {
      "keys": [
        {
          "value": "env.ANTHROPIC_API_KEY",
          "models": [],
          "weight": 0.5
        }
      ]
    },
    "bedrock": {
      "keys": [
        {
          "access_key": "env.AWS_ACCESS_KEY_ID",
          "secret_key": "env.AWS_SECRET_ACCESS_KEY",
          "region": "us-east-1",
          "arn": "arn:aws:bedrock:us-east-1::foundation-model/...",
          "deployments": {
            "claude-3-5-sonnet": "my-inference-profile"
          }
        }
      ]
    },
    "azure": {
      "keys": [
        {
          "value": "env.AZURE_OPENAI_API_KEY",
          "deployments": {
            "gpt-4o": "my-prod-deployment"
          },
          "api_version": "2024-10-21"
        }
      ]
    }
  },
  "cache": {
    "provider": "openai",
    "embedding_model": "text-embedding-3-small",
    "ttl": 3600,
    "threshold": 0.8
  },
  "telemetry": {
    "service_name": "bifrost-gateway",
    "collector_url": "http://otel-collector:4318",
    "trace_type": "genai_extension"
  }
}
```

### 17.2 Key Schema Fields

From `core/schemas/account.go`:

- `id`: Unique key identifier
- `name`: Human-readable name
- `value`: API key (or `env.VAR_NAME`)
- `models`: Model restriction list (empty = all)
- `weight`: Load balancing weight (float64)
- `enabled`: Active flag (default: true)
- `use_for_batch_api`: Batch API routing flag
- `config_hash`: Change detection hash

---

## 18. Unique Features vs. OpenRouter and LiteLLM

### 18.1 vs. OpenRouter

| Feature                 | Bifrost                       | OpenRouter                       |
| ----------------------- | ----------------------------- | -------------------------------- |
| Self-hosted             | Yes (core value prop)         | No (SaaS only)                   |
| Data sovereignty        | Full (never leaves infra)     | Data goes through OpenRouter     |
| Semantic caching        | Yes (vector similarity)       | No                               |
| Virtual keys / budgets  | Yes (hierarchical)            | Yes (credit system)              |
| CEL routing rules       | Yes                           | No (order/ignore arrays only)    |
| Adaptive load balancing | Yes (ML scoring)              | Yes (performance sort)           |
| MCP gateway             | Yes (built-in)                | No                               |
| Web UI                  | Yes                           | Yes (openrouter.ai)              |
| Pricing                 | Free + Enterprise tier        | Per-token markup                 |
| Compliance (HIPAA/SOC2) | Yes                           | Not documented                   |
| Go implementation       | Yes (ultra-low latency)       | Not open-source                  |
| Provider count          | 15–20+                        | 300+ models, 50+ providers       |
| Model catalog           | Self-maintained + pricing API | Extensive (community maintained) |

### 18.2 vs. LiteLLM

| Feature             | Bifrost               | LiteLLM                             |
| ------------------- | --------------------- | ----------------------------------- |
| Language            | Go                    | Python                              |
| Gateway overhead    | 11 µs                 | ~1,000+ µs                          |
| P99 at 500 RPS      | 1.68s                 | 90.72s                              |
| Memory (500 RPS)    | 120MB                 | 372MB                               |
| Semantic caching    | Yes (vector)          | Yes (exact match + semantic option) |
| Provider count      | 15–20                 | 100+                                |
| CEL routing rules   | Yes                   | No                                  |
| MCP gateway         | Yes                   | No                                  |
| Go SDK embed        | Yes                   | No (Python only)                    |
| Enterprise features | Yes (SSO, RBAC, SOC2) | Yes (proxy + enterprise tier)       |

### 18.3 vs. Portkey

| Feature             | Bifrost | Portkey            |
| ------------------- | ------- | ------------------ |
| Self-hosted         | Yes     | Yes (open source)  |
| Language            | Go      | TypeScript/Node    |
| Gateway binary size | Small   | 122KB              |
| Provider count      | 15–20+  | 1600+ models       |
| Semantic caching    | Yes     | Yes                |
| CEL routing rules   | Yes     | Config-based rules |
| Guardrails          | Yes     | Yes (50+)          |
| MCP gateway         | Yes     | Not documented     |

---

## 19. Notable API Extensions

Beyond standard OpenAI spec, Bifrost-specific behaviors:

| Extension                       | Description                                                  |
| ------------------------------- | ------------------------------------------------------------ |
| `x-bf-vk` header                | Virtual key authentication for governance                    |
| `x-bf-prom-team` header         | Tag Prometheus metrics by team                               |
| `x-bf-prom-environment` header  | Tag Prometheus metrics by environment                        |
| `provider/model` model format   | Provider prefix required for routing (e.g., `openai/gpt-4o`) |
| `env.VAR_NAME` in config        | Secure env var injection in config.json                      |
| `/v1/mcp/tool/execute` endpoint | Explicit MCP tool execution                                  |
| `/api/providers` POST           | REST API for dynamic provider configuration                  |
| `/metrics` GET                  | Prometheus metrics scrape endpoint                           |

---

## 20. Open Questions and Unknowns

1. **Bifrost Enterprise pricing**: The open-source tier is Apache 2.0. Enterprise features (SSO,
   SOC 2 compliance, advanced governance, adaptive load balancing) appear to require a commercial
   license. Pricing not publicly documented.

2. **gRPC support**: Documentation mentions gRPC as "planned" but not yet released.

3. **Guardrails specifics**: Content safety guardrails are referenced but detailed configuration
   schema not fully documented in public docs as of this research date.

4. **Redis-based caching**: Redis is listed as a vector store backend; it is unclear whether this
   supports semantic similarity search or only exact-match.

5. **Streaming error format**: Whether Bifrost's streaming error format conforms to OpenAI SSE
   error spec (mid-stream `finish_reason: "error"`) is not documented.

---

## 21. Brief Notes on Other AI Gateways

For completeness, other notable gateways in this space (in case "Bifrost" was ambiguous):

| Gateway                   | Language   | Self-hosted | Notable For                               |
| ------------------------- | ---------- | ----------- | ----------------------------------------- |
| **Portkey**               | TypeScript | Yes         | 1600+ models, 50+ guardrails, Configs API |
| **LiteLLM**               | Python     | Yes         | 100+ providers, established ecosystem     |
| **Helicone**              | TypeScript | Yes         | Developer-focused logging and replay      |
| **OpenRouter**            | N/A (SaaS) | No          | Largest model catalog, community          |
| **Martian**               | N/A (SaaS) | No          | Task-aware model routing                  |
| **Not Diamond**           | N/A (SaaS) | No          | ML-based model selection                  |
| **Unify**                 | N/A (SaaS) | No          | Benchmark-driven routing                  |
| **Cloudflare AI Gateway** | N/A (SaaS) | No          | Edge-native, Cloudflare ecosystem         |
| **Kong AI Gateway**       | Go/Nginx   | Yes         | Enterprise Kong plugin                    |
| **Envoy AI Gateway**      | Go         | Yes         | Envoy-based, Kubernetes native            |

---

## Sources

- GitHub repository: https://github.com/maximhq/bifrost
- Official website: https://www.getmaxim.ai/bifrost/
- Documentation root: https://docs.getbifrost.ai
- Provider routing docs: https://docs.getbifrost.ai/providers/provider-routing
- Setup guide: https://docs.getbifrost.ai/quickstart/gateway/setting-up
- Helm deployment: https://docs.getbifrost.ai/deployment-guides/helm
- Enterprise governance: https://docs.getbifrost.ai/enterprise/advanced-governance
- Observability (Maxim plugin): https://docs.getbifrost.ai/features/observability/maxim
- Performance blog: https://www.getmaxim.ai/blog/bifrost-a-drop-in-llm-proxy-40x-faster-than-litellm/
- Technical guide: https://www.getmaxim.ai/articles/building-better-ai-applications-with-bifrost-a-complete-technical-guide-for-ai-engineers/
- Go package docs: https://pkg.go.dev/github.com/maximhq/bifrost/core
- Docker Hub: https://hub.docker.com/r/maximhq/bifrost
- Benchmarking repo: https://github.com/maximhq/bifrost-benchmarking
- Medium setup guide: https://medium.com/@kuldeep.paul08/how-to-set-up-bifrost-your-llm-gateway-in-30-seconds-3b152fd9b7a3
