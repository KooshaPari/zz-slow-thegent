<DONE>
# LiteLLM Proxy (AI Gateway) — Exhaustive Research

**Date:** 2026-02-20
**Scope:** LiteLLM's proxy/gateway product ("LiteLLM Proxy" or "LiteLLM AI Gateway"), not the Python SDK.
**Context:** Competitor/inspiration analysis for thegent CLIProxy parity planning.

---

## 1. What Is It

LiteLLM Proxy is a standalone HTTP server (AI Gateway) that exposes a unified OpenAI-compatible API
surface over 100+ LLM providers. It is the server mode of the LiteLLM project
(`pip install litellm[proxy]`), started with `litellm --config config.yaml`. The proxy runs on port
4000 by default and implements `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`,
`/v1/models`, and many management endpoints.

Key GitHub stats (as of Feb 2026): >470,000 downloads, MIT-licensed open-source core with a paid
Enterprise tier.

Benchmarked at **1,500+ req/sec**, **8ms P95 latency at 1k RPS** in their own load tests.

---

## 2. Deployment Model

### 2.1 Self-Hosted Docker

The primary deployment path. A docker-compose file is provided via:

```bash
curl -O https://raw.githubusercontent.com/BerriAI/litellm/main/docker-compose.yml
docker compose up
```

The compose stack includes:

- `litellm` container (the proxy itself)
- `postgres` container (required for virtual keys, spend tracking, audit logs)
- Optional `redis` container (required for distributed load balancing, rate-limit counters, caching)

Stable Docker images are tagged `-stable` and have been load-tested for 12 hours before publishing.

### 2.2 Kubernetes

No managed K8s operator is documented, but the Docker image runs in any K8s cluster. For
multi-worker setups, `PROMETHEUS_MULTIPROC_DIR` must be set for aggregated metrics.

### 2.3 Cloud Managed

LiteLLM offers a demo "LiteLLM Cloud" instance, but the primary model is self-hosted. Enterprise
customers can purchase via AWS Marketplace (~$30,000/year for enterprise license with SLAs, SSO,
dedicated support).

### 2.4 Infrastructure Dependencies

| Dependency | Required for                                                            |
| ---------- | ----------------------------------------------------------------------- |
| PostgreSQL | Virtual key management, spend logs, audit logs, user/team/org tables    |
| Redis      | Distributed rate-limiting, cross-instance load-balancing state, caching |
| Prometheus | `/metrics` endpoint scraping                                            |

Redis and PostgreSQL are optional for single-instance testing but required for production.

---

## 3. Configuration Format

The primary configuration is a YAML file passed with `--config config.yaml`:

```yaml
model_list:
  - model_name: gpt-4o # User-facing name
    litellm_params:
      model: azure/gpt-4o # Provider/model-id
      api_base: https://endpoint.openai.azure.com/
      api_key: os.environ/AZURE_API_KEY # Env var reference
      rpm: 100 # Rate limit: req/min
      tpm: 100000 # Rate limit: tokens/min
      temperature: 0.9
      max_tokens: 4000
      organization: my-org
      extra_headers: { "X-Custom": "value" }
      aws_region_name: us-east-1 # Bedrock only
      api_version: 2024-02-15-preview # Azure only
    model_info:
      mode: chat
      access_groups: ["team-a", "team-b"]
      id: "gpt4o-primary-deployment" # Stable ID for fallback references

router_settings:
  routing_strategy: "usage-based-routing-v2" # see §5
  model_group_alias:
    gpt-4: gpt-4o # Maps incoming "gpt-4" to group "gpt-4o"
  num_retries: 3
  timeout: 30
  redis_host: redis
  redis_port: 6379
  redis_password: os.environ/REDIS_PASSWORD
  redis_ssl: true
  enable_pre_call_checks: true # Context window + region checks before calling
  enable_tag_filtering: true

litellm_settings:
  drop_params: true # Drop unsupported params per provider
  set_verbose: false
  cache: true
  cache_params:
    type: redis-semantic
    ttl: 600
    default_in_memory_ttl: 60
    namespace: "litellm.prod"
    similarity_threshold: 0.85
    embedding_model: "text-embedding-3-small"
  success_callback: ["langfuse", "prometheus"]
  failure_callback: ["slack"]
  num_retries: 2
  request_timeout: 30
  fallbacks:
    - { "gpt-4o": ["claude-sonnet", "gemini-pro"] }
  context_window_fallbacks:
    - { "gpt-4o": ["gpt-4o-128k"] }
  allowed_fails: 3 # Failures before cooldown
  cooldown_time: 60 # Cooldown seconds

general_settings:
  master_key: sk-my-admin-key # Proxy admin key (must start with sk-)
  database_url: postgresql://user:pass@postgres/litellm
  database_connection_pool_limit: 10
  database_connection_timeout: 30
  alerting: ["slack"]
  alerting_threshold: 0.8 # Alert at 80% budget usage
  litellm_key_header_name: "X-My-Key" # Custom key header name

environment_variables:
  REDIS_HOST: redis
  REDIS_PORT: "6379"
  LANGFUSE_PUBLIC_KEY: os.environ/LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY: os.environ/LANGFUSE_SECRET_KEY
  SLACK_WEBHOOK_URL: os.environ/SLACK_WEBHOOK_URL
  LITELLM_ENVIRONMENT: production

credential_list:
  - credential_name: my-azure-creds
    credential_values:
      AZURE_API_KEY: os.environ/AZURE_API_KEY
      AZURE_API_BASE: https://endpoint.openai.azure.com/
    credential_info:
      description: "Azure EU deployment"
```

Config can also be stored in S3/GCS and loaded via environment variables
(`LITELLM_CONFIG_BUCKET_TYPE`, `LITELLM_CONFIG_BUCKET_NAME`, `LITELLM_CONFIG_BUCKET_OBJECT_KEY`).

Dynamic model management is possible via `STORE_MODEL_IN_DB=True` — models added via API persist
across restarts.

---

## 4. Authentication: Virtual Keys, Master Key, Team Keys

### 4.1 Master Key

Set in `general_settings.master_key`. This is the "proxy admin" key — it can call any endpoint
including management endpoints (`/key/generate`, `/team/new`, etc.). Must start with `sk-`.

Alternatively set via `LITELLM_PROXY_MASTER_KEY` environment variable.

### 4.2 Virtual Keys (Verification Tokens)

The primary auth mechanism for external callers. Format: `sk-{random_url_safe_16_bytes}`.

Generated via:

```bash
POST /key/generate
Authorization: Bearer sk-master-key
{
  "budget_limit": 100.0,          # USD maximum spend
  "budget_duration": "30d",       # Reset period
  "max_parallel_requests": 10,
  "tpm_limit": 50000,
  "rpm_limit": 100,
  "models": ["gpt-4o", "claude-sonnet"],  # Restrict to these models
  "metadata": {"user": "alice@corp.com"},
  "aliases": {"gpt-4": "gpt-4o"},         # Per-key model aliases
  "team_id": "team-engineering",
  "expires": "2026-03-01",
  "soft_budget_cooldown": 5.0,    # Alert threshold (%) before hard block
  "allowed_routes": ["llm_api_routes"],   # Restrict to LLM routes only
  "tags": ["cost-center-eng"],
  "auto_rotate": true,
  "rotation_interval": "30d"
}
```

Only the hashed key is stored in PostgreSQL. Plaintext is returned once at creation time.

Key management endpoints:

- `POST /key/generate` — create
- `POST /key/update` — modify limits/metadata
- `POST /key/delete` — soft-delete
- `POST /key/regenerate` — rotate (new token, same settings)
- `POST /key/block` — disable without deletion
- `GET /key/info` — retrieve metadata
- `GET /key/list` — paginated listing
- `POST /key/service-account/generate` — machine-to-machine keys

### 4.3 Key Rotation

Enabled by setting `LITELLM_KEY_ROTATION_ENABLED=true` and a rotation interval. Keys auto-rotate on
schedule; `auto_rotate` and `rotation_interval` fields on the key control per-key cadence.

### 4.4 Custom Key Header

By default, the proxy reads the key from `Authorization: Bearer`. This can be changed:

```yaml
general_settings:
  litellm_key_header_name: "X-My-Org-Key"
```

### 4.5 Budget Hierarchy

LiteLLM enforces budgets at 8 levels (checked in this order, blocking at first exhaustion):

1. Key-level soft budget (alert threshold)
2. Key-level hard budget
3. User budget
4. Team budget
5. Organization budget
6. Model-specific spend limit (Enterprise)
7. Global proxy budget
8. Provider-specific budget (via `provider_budget_config`)

```yaml
general_settings:
  max_budget: 10000 # Global proxy cap (USD)
  max_internal_user_budget: 50 # Default per internal user
  max_end_user_budget: 5 # Default per end-user (via `user` param)
```

Budget reset periods: seconds (`Xs`), minutes (`Xm`), hours (`Xh`), days (`Xd`), months (`Xmo`).
Budget reset checker runs every 10 minutes by default.

Rate limit types configurable as `input`, `output`, or `total` (default: `total`) tokens.

---

## 5. Load Balancing Strategies

LiteLLM groups deployments by `model_name`. Multiple entries with the same `model_name` form a pool
that the router load-balances across.

### 5.1 Available Strategies

| Strategy                 | Description                                                                      | Recommended for                       |
| ------------------------ | -------------------------------------------------------------------------------- | ------------------------------------- |
| `simple-shuffle`         | Weighted random selection (default)                                              | General use; lowest overhead          |
| `usage-based-routing-v2` | Routes to deployment with lowest TPM usage for the current minute (Redis-backed) | High-throughput, rate-limit avoidance |
| `latency-based-routing`  | Selects deployment with lowest recent TTFT/latency; configurable TTL window      | Latency-sensitive workloads           |
| `least-busy`             | Fewest in-flight concurrent requests                                             | Parallel-heavy workloads              |
| `cost-based-routing`     | Selects cheapest deployment via LiteLLM cost map                                 | Budget optimization                   |
| Custom                   | Implement `CustomRoutingStrategyBase`                                            | Application-specific logic            |

### 5.2 Weight-Based Distribution

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_KEY
    weight: 9 # 90% of traffic

  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_base: https://endpoint.openai.azure.com/
      api_key: os.environ/AZURE_KEY
    weight: 1 # 10% of traffic
```

### 5.3 RPM/TPM-Based Filtering

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_KEY
      rpm: 500
      tpm: 100000
```

`usage-based-routing-v2` respects these limits and filters out deployments that have hit their quota.

### 5.4 Priority/Order-Based Fallback

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
    model_info:
      order: 1 # Primary (lower = higher priority)

  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o
    model_info:
      order: 2 # Secondary fallback
```

### 5.5 Max Parallel Requests Per Deployment

Set `max_parallel_requests` in `litellm_params` to cap concurrent in-flight requests to a single
deployment.

### 5.6 Traffic Mirroring (A/B Testing)

LiteLLM supports silent "shadow" deployments: production traffic is mirrored to a secondary model
for evaluation without affecting production responses.

### 5.7 Pre-Call Checks

With `enable_pre_call_checks: true` in `router_settings`:

- **Context window check**: Request is rejected before sending if it would exceed the model's
  context window, routing to `context_window_fallbacks` instead.
- **Regional compliance check**: Routes only to deployments matching the request's region
  constraints (e.g., EU-only data residency).

---

## 6. Reliability: Fallbacks, Retries, Circuit Breakers

### 6.1 Fallback Types

**Regular fallbacks** — triggered on any error (rate limit, timeout, model error):

```yaml
litellm_settings:
  fallbacks:
    - { "gpt-4o": ["claude-sonnet", "gemini-pro"] }
    - { "claude-sonnet": ["gpt-4o-mini"] }
```

**Context window fallbacks** — triggered when the prompt exceeds the model's context limit:

```yaml
litellm_settings:
  context_window_fallbacks:
    - { "gpt-4o": ["gpt-4o-128k"] }
```

**Content policy fallbacks** — triggered on content policy violation errors:

```yaml
litellm_settings:
  content_policy_fallbacks:
    - { "gpt-4o": ["claude-sonnet"] }
```

**Default fallbacks** — catch-all if no specific fallback is configured:

```yaml
litellm_settings:
  default_fallbacks: ["gpt-4o-mini"]
```

Per-request fallback disable: set `disable_fallbacks: true` in request body or key metadata.

Fallbacks can reference specific deployment IDs (`model_info.id`) for precise routing, not just
model group names.

### 6.2 Retries

```yaml
litellm_settings:
  num_retries: 3 # Retry each model before fallback
  retry_after: 5 # Delay between retries (seconds)
  request_timeout: 30 # Timeout per request
```

`RateLimitError` retries use exponential backoff. Generic errors retry immediately.
If all retries on the primary model fail, fallback is attempted.

### 6.3 Cooldown (Circuit Breaker Pattern)

```yaml
litellm_settings:
  allowed_fails: 3 # Failures allowed in cooldown_time window
  cooldown_time: 60 # Seconds to exclude deployment after threshold exceeded
```

When a deployment exceeds `allowed_fails`, it is removed from the routing pool for
`cooldown_time` seconds, then automatically re-admitted. This is LiteLLM's circuit breaker
implementation. Prometheus metric `litellm_deployment_cooled_down` tracks cooled-down deployments.

---

## 7. Caching

### 7.1 Supported Cache Backends (7 types)

| Backend             | Notes                                                                         |
| ------------------- | ----------------------------------------------------------------------------- |
| `local` (in-memory) | In-process Python dict; single-instance only                                  |
| `disk`              | File-based; no external dep; persistence without Redis                        |
| `redis`             | Distributed; required for multi-instance shared state                         |
| `redis-semantic`    | Redis + vector search (RediSearch module); requires Redis >= 4.2 + RediSearch |
| `qdrant-semantic`   | Qdrant vector DB; for semantic similarity caching                             |
| `s3`                | AWS S3; long-term archival with lifecycle policies                            |
| `gcs`               | Google Cloud Storage                                                          |

### 7.2 DualCache Architecture

LiteLLM uses a two-tier DualCache internally:

- **L1 (in-memory)**: Sub-millisecond local lookups
- **L2 (Redis)**: Shared state across all proxy instances

L1 is always checked first; only on miss does the proxy check L2. Router health tracking, virtual
key metadata, rate-limit counters, and model pricing all leverage this DualCache.

### 7.3 Configuration

```yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis-semantic
    ttl: 600 # Default TTL (seconds)
    default_in_memory_ttl: 60 # L1 (in-memory) TTL
    default_in_redis_ttl: 3600 # L2 (Redis) TTL
    namespace: "litellm.prod" # Key prefix for isolation
    supported_call_types: # Restrict to specific API types
      - completion
      - acompletion
      - embedding
    mode: default_off # Opt-in mode: clients must pass cache.use-cache=true
    similarity_threshold: 0.85 # Semantic cache threshold (0-1)
    embedding_model: "text-embedding-3-small"
```

### 7.4 Cache Key Generation

Cache keys are hashed from request parameters. Provider-specific parameters (e.g., Vertex AI
`thinking`) can be included via optional configuration. Namespace creates key prefix
`litellm.caching.production:<hash>`.

### 7.5 Response Headers

Cache-hit detection via response headers:

- `x-litellm-cache-key`: The matched cache hash
- `x-litellm-semantic-similarity`: Similarity score (0-1) for semantic matches

### 7.6 Per-Request Cache Control

Client can explicitly force caching:

```json
{ "cache": { "use-cache": true } }
```

Or opt out when `mode: default_off` is set. Setting `supported_call_types: []` disables response
caching while keeping Redis active for rate-limit counters.

### 7.7 Redis Connection Options

Supports standard Redis, Redis Cluster, and Redis Sentinel. GCP Memorystore IAM authentication is
supported via `create_gcp_iam_redis_connect_func()`. Connection pool timeout configured via
`REDIS_CONNECTION_POOL_TIMEOUT`.

---

## 8. Cost Tracking

### 8.1 Automatic Cost Calculation

LiteLLM maintains a built-in cost map for 100+ models. For every request, it automatically
calculates cost from token counts × price per token and stores in `LiteLLM_SpendLogs` PostgreSQL
table:

Fields stored per request: `api_key`, `user`, `team_id`, `model`, `model_group`, `prompt_tokens`,
`completion_tokens`, `total_cost`, `request_tags`, `end_user`, `start_time`, `end_time`.

### 8.2 Custom Pricing

```yaml
model_list:
  - model_name: my-custom-model
    litellm_params:
      model: openai/custom
      input_cost_per_token: 0.000002
      output_cost_per_token: 0.000006
```

Provider **margins** (markup) and **discounts** are also configurable.

### 8.3 Tag-Based Cost Tracking

Attach tags at multiple levels:

- **Request-level**: `"metadata": {"tags": ["cost-center-eng", "project-alpha"]}`
- **Key-level**: Stored in key metadata, applied to all requests from that key
- **Team-level**: Auto-applied to all team members' requests

Tag budgets (Enterprise):

```yaml
litellm_settings:
  tag_budgets:
    - tag: "cost-center-eng"
      max_budget: 500.0
      budget_duration: "30d"
```

### 8.4 Provider-Level Budgets

```yaml
router_settings:
  provider_budget_config:
    openai:
      budget_limit: 100
      time_period: 1d
    azure:
      budget_limit: 500
      time_period: 1d
    anthropic:
      budget_limit: 200
      time_period: 7d
```

When a provider exceeds its budget, that provider is skipped and requests route to other
configured providers. Exhausted state returns 429 with message indicating budget exceeded.
Monitored via Prometheus metric `litellm_provider_remaining_budget_metric`. The `/provider/budgets`
endpoint shows remaining budget per provider.

### 8.5 Spend Queries

Spend queries filtered by key, team, model, date range, or tag via management API endpoints. The
`/spend/report` endpoint (Enterprise) provides detailed analytics. Daily reports can be sent to
Slack/Discord.

### 8.6 End-User (Customer) Tracking

The `user` field in chat completion requests is tracked as `end_user`. Budget limits can be applied
per end-user via `max_end_user_budget` without creating explicit keys:

```yaml
general_settings:
  max_end_user_budget: 5.0 # USD per end-user per budget_duration
```

---

## 9. Guardrails

Guardrails run at configurable lifecycle hooks: `pre_call`, `post_call`, `during_call`, or
`logging_only`.

### 9.1 Built-in: LiteLLM Content Filter

No external dependencies. Uses regex patterns and keyword matching to block or flag requests
containing matched content. Supports banned keyword lists.

### 9.2 PII/PHI Masking — Microsoft Presidio

Integration with deployed Presidio Analyzer + Anonymizer containers:

```yaml
litellm_settings:
  guardrails:
    - guardrail_name: presidio-pii-guard
      litellm_params:
        guardrail: presidio
        mode: pre_call
        presidio_analyzer_api_base: http://presidio-analyzer:3000
        presidio_anonymizer_api_base: http://presidio-anonymizer:3001
        presidio_filter_scope: both # "input", "output", or "both"
        output_parse_pii: true
        pii_entities_config:
          PHONE_NUMBER: MASK
          EMAIL_ADDRESS: MASK
          SSN: BLOCK # Block request if SSN detected
          CREDIT_CARD: BLOCK
```

Supports all Presidio entity types. GDPR use case: mask PII before sending to any LLM provider,
making Claude/Gemini/etc. GDPR-eligible.

### 9.3 Prompt Injection Detection

LiteLLM has in-memory prompt injection detection running pre-call. Multiple detection methods are
supported. Third-party integrations (Pillar Security, Lasso Security) provide additional
jailbreak detection, PII+PCI detection, and secret detection via LiteLLM's Generic Guardrail API.

### 9.4 OpenAI Moderation

```yaml
guardrails:
  - guardrail_name: openai-moderation
    litellm_params:
      guardrail: openai-moderation
      mode: pre_call
```

Uses OpenAI's moderation API to filter inputs.

### 9.5 LlamaGuard / LLM Guard / Google Text Moderation

Enterprise integrations that use an LLM as the safety classifier for input/output.

### 9.6 Rate Limiting (per-key, per-team, per-user)

Rate limiting is not a guardrail plugin but enforced at the proxy layer. See §4.5 (budget
hierarchy). Rate limits apply to all non-admin keys. Admin keys (`proxy_admin` role) bypass rate
limits.

### 9.7 Secret Detection / Redaction (Enterprise)

Automatically masks API keys and secrets in request/response logs. Prevents credential leakage
in observability pipelines.

---

## 10. Tag-Based Routing

Tag routing assigns requests to specific deployment pools based on tags. It replaced the deprecated
team-based routing.

### 10.1 Configuration

```yaml
router_settings:
  enable_tag_filtering: true
  tag_filtering_match_any: true # Match if request has ANY configured tag

model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_KEY
    model_info:
      tags: ["free"]

  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o-premium
      api_base: https://eu-endpoint.openai.azure.com/
      api_key: os.environ/AZURE_KEY
    model_info:
      tags: ["paid", "eu"]

  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_KEY_DEFAULT
    model_info:
      tags: ["default"] # Fallback for untagged requests
```

### 10.2 Request Tagging

Two methods to tag a request:

**JSON body:**

```json
{"model": "gpt-4o", "messages": [...], "tags": ["paid"]}
```

**Request header:**

```
x-litellm-tags: paid,eu
```

### 10.3 Team-to-Tag Routing (Enterprise)

Teams created via `/team/new` can be assigned tags. All requests from team members automatically
receive the team's tags, enabling per-team deployment pool isolation without per-request tag
injection by the client.

### 10.4 Use Cases

- Free vs. paid tier: `tags: ["free"]` → cheaper deployments; `tags: ["paid"]` → premium
- Region compliance: `tags: ["eu"]` → EU-only deployments for GDPR
- Team isolation: Team A's pool, Team B's pool, using the same model name

---

## 11. Team / User / Org Routing and Budget Enforcement

### 11.1 Four-Level Hierarchy

```
Organization (Enterprise)
  └── Team
        └── User / Internal User
              └── Virtual Key
```

Budget constraint: team budget cannot exceed org budget; user budget cannot exceed team budget.

### 11.2 Team Creation

```bash
POST /team/new
Authorization: Bearer sk-master-key
{
  "team_alias": "engineering",
  "max_budget": 500.0,
  "budget_duration": "30d",
  "tpm_limit": 200000,
  "rpm_limit": 1000,
  "models": ["gpt-4o", "claude-sonnet"],
  "metadata": {"department": "Engineering"}
}
```

### 11.3 Role-Based Access Control

Platform-wide roles:

- `proxy_admin` — full access, bypasses rate limits
- `proxy_admin_viewer` — read-only
- `internal_user` — default user role

Scoped roles (Enterprise):

- `org_admin` — manages their organization's teams
- `team_admin` — manages their team only

### 11.4 Self-Serve (Enterprise)

Internal users can create their own API keys within their team's budget. `proxy_admin` can
configure whether self-serve key generation is allowed, and which fields users can set.

### 11.5 Team-Level Logging Isolation (Enterprise)

Each team can route their Langfuse logs to a dedicated Langfuse project. GDPR-compliant teams can
disable logging entirely.

---

## 12. Pass-Through Headers and Request Modifications

### 12.1 Header Forwarding

By default, client headers are NOT forwarded to LLM provider APIs. Selective forwarding is
enabled per model group:

```yaml
general_settings:
  forward_client_headers_to_llm_api: true # Global (risky)
  # Or per model group:
model_group_settings:
  - model_name: gpt-4o
    forward_client_headers_to_llm_api: true
```

Wildcard patterns like `openai/*` and `anthropic/*` are supported in model group settings.

### 12.2 Extra Headers Per Model

```yaml
litellm_params:
  extra_headers:
    X-Custom-Header: "value"
    X-Trace-Id: "os.environ/TRACE_ID"
```

### 12.3 Pass-Through Endpoints

Route arbitrary requests through LiteLLM to any external API:

```yaml
litellm_settings:
  pass_through_endpoints:
    - path: /custom-api
      target: https://api.example.com/v1/endpoint
      headers:
        Authorization: "Bearer os.environ/CUSTOM_KEY"
      include_subpath: true # Forward /custom-api/* not just /custom-api
      auth_type: api_key
```

Provider-specific pass-through is built-in for Vertex AI SDK compatibility, Azure Cognitive
Services, etc.

### 12.4 Request Metadata

Clients can attach metadata to requests:

```json
{ "metadata": { "generation_name": "my-task", "user_id": "alice" } }
```

This metadata flows into spend logs and observability callbacks.

---

## 13. Streaming Behavior

### 13.1 SSE (Server-Sent Events)

LiteLLM proxy passes streaming chunks through largely unchanged. For providers that don't natively
support streaming, LiteLLM handles the buffering and SSE formatting.

The proxy exposes `POST /v1/chat/completions` with `stream: true`. Chunks are in OpenAI SSE format:

```
data: {"id":"...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{"content":"..."},"finish_reason":null}]}
```

### 13.2 Streaming + Caching

LiteLLM supports caching responses for streaming calls. The cache stores the complete response;
on cache hit, it replays the chunks from the cache.

### 13.3 TTFT Metrics

`litellm_llm_api_time_to_first_token_metric` is a Prometheus histogram tracking time-to-first-token
per deployment, used by `latency-based-routing` as a signal.

### 13.4 Repeated Chunk Limit

`REPEATED_STREAMING_CHUNK_LIMIT` can be set to cap how many identical consecutive chunks are
allowed before the stream is forcibly terminated (guards against runaway infinite loops in some
provider implementations).

### 13.5 MCP over SSE

The MCP gateway (§18) supports SSE-based MCP transports in addition to Streamable HTTP and stdio.

---

## 14. Model Aliases and Model Mapping

### 14.1 Model Group Aliases (Router-Level)

Maps incoming model names to deployment pools:

```yaml
router_settings:
  model_group_alias:
    gpt-4: gpt-4o # Requests for "gpt-4" go to the "gpt-4o" group
    claude: claude-sonnet
```

### 14.2 Per-Key Aliases

Virtual keys can carry their own model alias table, stored in key metadata:

```json
{ "aliases": { "gpt-4": "gpt-4o-mini" } }
```

A key holder who requests `gpt-4` is silently served `gpt-4o-mini`, allowing cost control without
changing client code.

### 14.3 User-Facing vs. Provider Model Names

`model_name` in config is the user-facing name; `litellm_params.model` is the actual provider
model string. This decoupling allows arbitrary rename at the API surface.

### 14.4 Model ID Referencing

Each deployment can have a stable `model_info.id` UUID. Fallback chains can reference specific
deployment IDs rather than model group names, enabling precise failover control.

---

## 15. Wildcard Routing

Route all models from a provider without listing each individually:

```yaml
model_list:
  - model_name: openai/*
    litellm_params:
      model: openai/* # Wildcard: any model name under openai/
      api_key: os.environ/OPENAI_API_KEY

  - model_name: xai/*
    litellm_params:
      model: xai/*
      api_key: os.environ/XAI_API_KEY

litellm_settings:
  check_provider_endpoint: true # Validate model exists at provider before forwarding
```

With wildcard routing, a client requesting any `openai/gpt-5-whatever` will be proxied to
OpenAI without the model being explicitly listed. The `check_provider_endpoint: true` setting
makes the `/v1/models` endpoint dynamically query the provider to return accurate model lists.

---

## 16. Webhook/Callback Integrations

### 16.1 Callback Architecture

LiteLLM supports callbacks at the SDK level (`success_callback`, `failure_callback`) and proxy
level (config `success_callback`, `failure_callback`). Callbacks receive full request/response
metadata.

### 16.2 Observability Platforms (Pre-Built Callbacks)

| Platform                | Config                                               |
| ----------------------- | ---------------------------------------------------- |
| Langfuse                | `success_callback: ["langfuse"]`                     |
| MLflow                  | `success_callback: ["mlflow"]`                       |
| Helicone                | `success_callback: ["helicone"]`                     |
| Lunary                  | `success_callback: ["lunary"]`                       |
| Promptlayer             | `success_callback: ["promptlayer"]`                  |
| Traceloop/OpenTelemetry | `success_callback: ["traceloop"]`                    |
| Datadog                 | Via Prometheus + Datadog Agent (`/metrics` endpoint) |

### 16.3 Alerting Webhooks

```yaml
general_settings:
  alerting: ["slack"]
  alerting_threshold: 0.8

environment_variables:
  SLACK_WEBHOOK_URL: https://hooks.slack.com/services/...
```

Supports 24+ alert types, including:

- `llm_exceptions`, `llm_too_slow`, `llm_requests_hanging` (on by default)
- `budget_alerts`, `spend_reports`, `daily_reports`
- `region_outage_alerts` (Enterprise — triggers when ≥5 requests to a region fail in 1 minute)
- Key/team/user management events (off by default, opt-in)

Alert routing: specific alert types can be sent to dedicated Slack channels. Discord (`/slack`
appended to webhook URL) and Microsoft Teams are also supported.

Budget alert webhook payload (beta):

```json
{
  "spend": 95.0,
  "max_budget": 100.0,
  "token": "hashed_key_value",
  "team_id": "team-engineering",
  "projected_exceeded_date": "2026-02-25"
}
```

### 16.4 Custom Callbacks

Implement the `CustomLogger` interface to build custom sinks (database, internal monitoring, etc.)
and register with `litellm.callbacks = [MyCustomLogger()]`.

---

## 17. Observability: Prometheus/Datadog/Langfuse

### 17.1 Prometheus

Enable via:

```yaml
litellm_settings:
  callbacks: ["prometheus"]
```

Metrics endpoint: `GET /metrics` (unauthenticated by default; opt-in auth via
`require_auth_for_metrics_endpoint: true`).

Key metric families:

**Spend & Budget:**

- `litellm_spend_metric` — total spend, labeled by `end_user`, `hashed_api_key`, `api_key_alias`, `model`, `team`
- `litellm_total_tokens_metric`, `litellm_input_tokens_metric`, `litellm_output_tokens_metric`
- `litellm_team_max_budget_metric`, `litellm_remaining_team_budget_metric`, `litellm_team_budget_remaining_hours_metric`
- `litellm_api_key_max_budget_metric`, `litellm_remaining_api_key_budget_metric`
- `litellm_remaining_api_key_requests_for_model`, `litellm_remaining_api_key_tokens_for_model`
- `litellm_provider_remaining_budget_metric`

**Request Tracking:**

- `litellm_proxy_total_requests_metric` — all client requests
- `litellm_proxy_failed_requests_metric` — failed responses with exception details
- `litellm_callback_logging_failures_metric` — downstream callback failures

**Deployment Health:**

- `litellm_deployment_success_responses`, `litellm_deployment_failure_responses`
- `litellm_remaining_requests_metric`, `litellm_remaining_tokens_metric`
- `litellm_deployment_state` — 0=healthy, 1=partial, 2=outage
- `litellm_deployment_cooled_down` — deployments currently in circuit-breaker cooldown
- `litellm_deployment_successful_fallbacks`, `litellm_deployment_failed_fallbacks`

**Latency:**

- `litellm_request_total_latency_metric` — end-to-end (histogram)
- `litellm_overhead_latency_metric` — LiteLLM processing overhead
- `litellm_llm_api_latency_metric` — upstream API response time
- `litellm_llm_api_time_to_first_token_metric` — TTFT for streaming

**Infrastructure:**

- `litellm_redis_latency` — Redis call latency histogram
- `litellm_in_memory_daily_spend_update_queue_size`
- `litellm_pod_lock_manager_size`

Standard labels on most metrics: `hashed_api_key`, `api_key_alias`, `model`, `requested_model`,
`team`, `team_alias`, `end_user`, `status_code`, `exception_status`, `exception_class`,
`api_provider`, `model_id`.

**Advanced options:**

- `prometheus_initialize_budget_metrics: true` — emit metrics for inactive keys/teams every 5 min
- `enable_end_user_cost_tracking_prometheus_only: true` — track per end-user cost in Prometheus
- `custom_prometheus_metadata_labels` — custom label dimensions
- `custom_prometheus_tags` — boolean labels
- `prometheus_metrics_config` — selective metric/label filtering by group

### 17.2 Datadog

No native Datadog integration; Datadog Agent uses the OpenMetrics check to scrape `/metrics`:

```yaml
init_config: {}
instances:
  - prometheus_url: http://litellm:4000/metrics
    namespace: litellm
    metrics: ["litellm_*"]
```

### 17.3 Langfuse

Full LLM tracing (prompt, response, latency, cost, model, user) sent to Langfuse on each
completion. Supports per-team Langfuse project routing (Enterprise).

---

## 18. Admin UI Features

### 18.1 Core (Open Source)

The proxy ships with a built-in web UI at `http://localhost:4000/ui`:

- Dashboard: usage, token burn, latency over time
- Key management: create, view, revoke virtual keys
- Spend tracking: view spend per key/model/team
- Model management: add/remove models
- MCP server management

### 18.2 Enterprise Admin UI

- SSO (SAML, OIDC) for the admin UI — free for up to 5 users since v1.76.0, Enterprise for >5
- RBAC: org_admin and team_admin roles visible in UI
- Audit logs: who created/deleted/modified keys, teams, models; with configurable retention
- Custom branding / company logo on Swagger UI
- Team management with self-serve access for internal users
- Data export to GCS Bucket / Azure Blob Storage

---

## 19. Unique Features vs. OpenRouter

| Feature                        | LiteLLM Proxy                                                | OpenRouter                         |
| ------------------------------ | ------------------------------------------------------------ | ---------------------------------- |
| **Deployment model**           | Self-hosted, full infra control                              | SaaS, no infrastructure            |
| **Data residency**             | All data stays on-prem                                       | Data passes through OpenRouter     |
| **Config-as-code**             | YAML `config.yaml`, GitOps-friendly                          | Web UI / API only                  |
| **Virtual key system**         | Full key lifecycle (create, rotate, block, budget)           | Single-tier API keys               |
| **Budget hierarchy**           | 8 levels: key, user, team, org, model, global, provider, tag | Per-key credits only               |
| **Tag-based routing**          | Route by request/key/team tags to deployment pools           | Not supported                      |
| **Provider budget routing**    | Cap spend per provider, auto-skip when exhausted             | Not supported                      |
| **Semantic caching**           | Redis-semantic, Qdrant-semantic with threshold config        | Prompt caching (exact match)       |
| **PII/PHI masking**            | Presidio integration (pre-call scrubbing)                    | Not supported                      |
| **Prompt injection detection** | In-memory detection + Pillar/Lasso integrations              | Not supported                      |
| **MCP Gateway**                | Full MCP server registry, OAuth, per-key permissions         | Not supported                      |
| **Prometheus metrics**         | ~25 metric families with full label dimensions               | Not supported                      |
| **Circuit breaker**            | `allowed_fails` + `cooldown_time` per deployment             | Implicit (via routing)             |
| **Traffic mirroring**          | Shadow deployments for A/B testing                           | Not supported                      |
| **Wildcard routing**           | `provider/*` — route any model without listing it            | Not applicable (all models listed) |
| **Pre-call validation**        | Context window check, region check before API call           | Implicit                           |
| **Custom routing strategy**    | `CustomRoutingStrategyBase` — implement any logic            | Not supported                      |
| **Audit logs**                 | Enterprise: who did what, when                               | Not supported                      |
| **SSO for admin UI**           | Enterprise SAML/OIDC                                         | Not supported                      |
| **Per-team Langfuse projects** | Each team's traces go to their own project                   | Not supported                      |
| **Model discovery endpoint**   | `/v1/models` queries provider for wildcard models            | `/api/v1/models` static list       |
| **GDPR-compliant logging**     | Per-team logging opt-out                                     | Not supported                      |

---

## 20. LiteLLM Proxy API Extensions

### 20.1 Custom Request Headers

Headers the proxy reads from client requests:

- `Authorization: Bearer <virtual-key>` — standard auth (or custom header per config)
- `x-litellm-tags: tag1,tag2` — route request to tagged deployments
- `x-litellm-end-user-id: user123` — attribute cost to end-user
- `Litellm-metadata: {"key": "value"}` — arbitrary metadata attached to spend logs

### 20.2 Custom Response Headers

Headers the proxy adds to responses:

- `x-litellm-model-id` — stable deployment UUID of the model that handled the request
- `x-litellm-cache-key` — cache hash (on cache hit)
- `x-litellm-semantic-similarity` — similarity score for semantic cache hits
- `x-litellm-response-cost` — computed USD cost of the response
- `x-litellm-key-remaining-budget` — remaining budget for the key
- `x-litellm-deployment-cooled-down-exception` — details if a deployment was cooled down

### 20.3 Request Body Extensions

Non-standard fields accepted by LiteLLM proxy in the request body:

- `metadata` — arbitrary key-value pairs forwarded to callbacks and spend logs
- `cache` — `{"use-cache": true/false}` to control per-request caching
- `ttl` — custom cache TTL for this request
- `tags` — routing tags array

### 20.4 Management API

The proxy exposes extensive management endpoints beyond the OpenAI-compatible ones:

- `/key/*` — key CRUD, rotation, blocking
- `/team/*` — team CRUD, budget management
- `/user/*` — user management
- `/org/*` — organization management (Enterprise)
- `/model/*` — dynamic model add/remove
- `/spend/*` — spend queries, reports
- `/provider/budgets` — provider budget status
- `/health` — deployment health check
- `/metrics` — Prometheus metrics
- `/mcp/*` — MCP server management
- `/guardrails/*` — guardrail management

---

## Sources

- [LiteLLM AI Gateway Overview](https://docs.litellm.ai/docs/simple_proxy)
- [LiteLLM Proxy Quick Start](https://docs.litellm.ai/docs/proxy/quick_start)
- [LiteLLM Config Settings](https://docs.litellm.ai/docs/proxy/configs)
- [LiteLLM Router - Load Balancing](https://docs.litellm.ai/docs/routing)
- [LiteLLM Proxy - Load Balancing](https://docs.litellm.ai/docs/proxy/load_balancing)
- [LiteLLM Virtual Keys](https://docs.litellm.ai/docs/proxy/virtual_keys)
- [LiteLLM Budgets & Rate Limits](https://docs.litellm.ai/docs/proxy/users)
- [LiteLLM Spend Tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)
- [LiteLLM Tag Budgets](https://docs.litellm.ai/docs/proxy/tag_budgets)
- [LiteLLM Provider Budget Routing](https://docs.litellm.ai/docs/proxy/provider_budget_routing)
- [LiteLLM Caching All Backends](https://docs.litellm.ai/docs/caching/all_caches)
- [LiteLLM Proxy Caching](https://docs.litellm.ai/docs/proxy/caching)
- [LiteLLM Caching System Architecture (DeepWiki)](https://deepwiki.com/BerriAI/litellm/5.1-caching-system-architecture)
- [LiteLLM API Key Management (DeepWiki)](https://deepwiki.com/BerriAI/litellm/3.5.1-api-key-management)
- [LiteLLM Multi-Tenant Architecture](https://docs.litellm.ai/docs/proxy/multi_tenant_architecture)
- [LiteLLM Tag Based Routing](https://docs.litellm.ai/docs/proxy/tag_routing)
- [LiteLLM Reliability / Fallbacks](https://docs.litellm.ai/docs/proxy/reliability)
- [LiteLLM Guardrails Quick Start](https://docs.litellm.ai/docs/proxy/guardrails/quick_start)
- [LiteLLM PII Masking via Presidio](https://docs.litellm.ai/docs/proxy/guardrails/pii_masking_v2)
- [LiteLLM Prometheus Metrics](https://docs.litellm.ai/docs/proxy/prometheus)
- [LiteLLM Alerting/Webhooks](https://docs.litellm.ai/docs/proxy/alerting)
- [LiteLLM Enterprise Features](https://docs.litellm.ai/docs/proxy/enterprise)
- [LiteLLM MCP Overview](https://docs.litellm.ai/docs/mcp)
- [LiteLLM Wildcard Routing](https://docs.litellm.ai/docs/wildcard_routing)
- [LiteLLM Model Discovery](https://docs.litellm.ai/docs/proxy/model_discovery)
- [LiteLLM Pass Through Endpoints](https://docs.litellm.ai/docs/proxy/pass_through)
- [LiteLLM Request Headers](https://docs.litellm.ai/docs/proxy/request_headers)
- [LiteLLM Response Headers](https://docs.litellm.ai/docs/proxy/response_headers)
- [LiteLLM Docker Quick Start](https://docs.litellm.ai/docs/proxy/docker_quick_start)
- [LiteLLM vs OpenRouter - TruFoundry](https://www.truefoundry.com/blog/litellm-vs-openrouter)
- [LiteLLM vs OpenRouter - Xenoss](https://xenoss.io/blog/openrouter-vs-litellm)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [LiteLLM Elest.io Feature Overview](https://blog.elest.io/litellm-stop-burning-money-on-llm-apis-virtual-keys-cost-tracking-and-guardrails/)
