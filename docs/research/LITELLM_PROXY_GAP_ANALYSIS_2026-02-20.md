<DONE>
# LiteLLM Proxy Gap Analysis — 2026-02-20

**Scope:** Features LiteLLM Proxy provides that thegent's CLIProxy stack does NOT currently
implement, with focus on features that would make thegent better as a provider aggregate.
**Related:** `docs/research/OPENROUTER_GAP_ANALYSIS_2026-02-20.md` (already documents OpenRouter gaps).
**LiteLLM source:** `docs/research/LITELLM_PROXY_RESEARCH_2026-02-20.md`

This document covers **LiteLLM-exclusive gaps** — features LiteLLM has that OpenRouter does not,
meaning features not already catalogued in the OpenRouter gap analysis.

---

## 1. Context: What thegent's CLIProxy Currently Is

The CLIProxy stack consists of:

| Component                      | File                                | What it does                                                                                   |
| ------------------------------ | ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| `cliproxy_adapter.py`          | Starlette ASGI proxy                | Listens on port 8317; forwards `/v1/*` to CLIProxyAPIPlus on 8318; Responses API translation   |
| `litellm_router.py`            | LiteLLM Router wrapper              | Wraps LiteLLM's Python SDK `Router` for multi-provider routing; cost tracking; fallback chains |
| `cost_tracker.py`              | CostTracker                         | In-memory JSONL cost log; daily/session budget; no multi-tenant scope                          |
| `cost_aware_router.py`         | BudgetAwareRouter + CostAwareRouter | Project-scoped budget enforcement; Pareto candidate filtering                                  |
| `pareto_router.py`             | ParetoRouter                        | Pareto-front model selection by cost/quality/speed                                             |
| `alerting.py`                  | AlertManager                        | Webhook alerting for latency/errors/budget                                                     |
| `scoring.py`, `auto_router.py` | Routing heuristics                  | Model scoring, task-type routing                                                               |

**What the stack currently does NOT have** (relevant to this analysis):

- No virtual key system (no per-key budgets, rate limits, model restrictions)
- No multi-tenant hierarchy (no teams, orgs, or user-scoped budgets; only project_id in
  `cost_aware_router.py`)
- No per-deployment cooldown / circuit breaker (retries exist, no deployment exclusion)
- No deployment pool concept (all routes are one-to-one provider/model, no load-balanced pools)
- No tag-based routing (no ability to route requests with `tags=["free"]` to different pools)
- No provider-level spend caps (can limit total daily spend, not per-provider)
- No semantic caching (LiteLLM Router has `cache_responses=True` but no semantic cache)
- No guardrails (no PII masking, no prompt injection detection, no content filtering)
- No Prometheus metrics endpoint (no `/metrics` exposed; no deployment health metrics)
- No admin UI (no built-in dashboard for spend/keys/model health)
- No wildcard routing (every model must be explicitly listed in `model_metadata.py` and
  `harness_model_mapping.py`)
- No traffic mirroring / shadow deployments
- No dynamic model management API (models defined at startup via catalog, no add/remove at runtime)
- No MCP gateway access control (no per-key MCP tool permissions)

---

## 2. Gap Matrix: LiteLLM vs. thegent CLIProxy

Legend: **P0** = critical for feature parity / competitive positioning, **P1** = significant,
**P2** = valuable enhancement

### 2.1 Cost Tracking and Budget Enforcement

| Feature                                | LiteLLM                                                                                                    | thegent Current                                                                                          | Gap                                                                                                            | Priority |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------- |
| **Per-provider spend cap**             | `provider_budget_config` per provider; auto-skip when exceeded; `/provider/budgets` API; Prometheus metric | None. `cost_tracker.py` has per-model breakdown but no provider-level hard cap that affects routing      | thegent has no mechanism to say "stop routing to OpenAI when we've spent $100 on it today, shift to Anthropic" | **P0**   |
| **Multi-level budget hierarchy**       | 8 levels: key → user → team → org → model → global → provider → tag                                        | 2 levels: session + daily (`SimpleCostTracker`); project-scoped (`BudgetManager`) with no sub-scopes     | No team/user scoping means all agents running under the same project_id share one budget without isolation     | **P0**   |
| **Tag-based cost tracking + budgets**  | Requests tagged with metadata; spend aggregated per tag; configurable tag budget caps (Enterprise)         | Tags not tracked in cost log; no tag-level aggregation                                                   | Cannot slice cost by project phase, experiment name, agent role, or cost center                                | **P1**   |
| **Flexible budget reset periods**      | `Xs`, `Xm`, `Xh`, `Xd`, `Xmo`                                                                              | Daily only (no automatic reset at all — `daily_spend` is never reset without explicit `reset_session()`) | Rolling budget windows (e.g., "$500/week" or "$2000/month") not possible                                       | **P1**   |
| **Soft-budget alerts with thresholds** | `alerting_threshold: 0.8` sends alert at 80% spend before hard block                                       | `alert_budget_exceeded` fires only after exceeding (`is_over_budget()`)                                  | No advance warning before hitting the wall; agents get surprise hard stops                                     | **P1**   |
| **Per-model spend limits**             | `model_max_budget` on a virtual key (Enterprise)                                                           | Approximate cost estimation per model in `_estimate_cost()`; no enforcement                              | Cannot say "this key can spend at most $50 on GPT-4o specifically"                                             | **P2**   |
| **End-user (customer) spend tracking** | `user` field in request body; `max_end_user_budget` global default                                         | No end-user attribution in cost tracking                                                                 | Cannot attribute costs to individual Claude Code users or external customers                                   | **P2**   |
| **Spend query API**                    | REST API: filter by key, team, model, date, tag                                                            | JSONL file only; no API                                                                                  | No programmatic spend queries; post-hoc analysis requires parsing JSONL files                                  | **P2**   |

### 2.2 Load Balancing and Deployment Pools

| Feature                                    | LiteLLM                                                                                        | thegent Current                                                                                                                | Gap                                                                                           | Priority |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | -------- |
| **Deployment pool concept**                | Multiple entries with same `model_name` form a load-balanced pool                              | One route per `provider/model` key in catalog                                                                                  | Cannot have two different Azure GPT-4o endpoints in a balanced pool; each is a distinct route | **P0**   |
| **Tag-based routing to deployment pools**  | Assign `tags` to deployments; route requests by `x-litellm-tags` header or `"tags"` in body    | No tag routing                                                                                                                 | Cannot send "free tier" requests to cheaper deployment and "paid tier" requests to premium    | **P0**   |
| **Wildcard provider routing**              | `model_name: openai/*` — any model from a provider routes without listing it                   | Every model must be in `model_metadata.py` + `harness_model_mapping.py`                                                        | New model releases require code changes to `model_metadata.py` before they can be used        | **P0**   |
| **RPM/TPM limits per deployment**          | `rpm: 500`, `tpm: 100000` in `litellm_params` directly                                         | No per-route rate limit enforcement in routing layer                                                                           | When a provider returns 429, thegent retries rather than switching deployment                 | **P1**   |
| **Per-deployment max parallel requests**   | `max_parallel_requests` per deployment                                                         | No concurrency limit per provider route                                                                                        | A single slow provider can absorb all capacity                                                | **P1**   |
| **Traffic mirroring (shadow deployments)** | Silent copy of production traffic to secondary model                                           | Not implemented                                                                                                                | Cannot benchmark new models against production traffic without impacting users                | **P1**   |
| **Pre-call context window check**          | `enable_pre_call_checks: true` — validates before calling; triggers `context_window_fallbacks` | `validate_context_window()` logs a warning but does not prevent the call or trigger fallback                                   | Requests that overflow context window are sent to the provider and fail with provider error   | **P1**   |
| **Weight-based traffic splitting**         | `weight: 9` vs `weight: 1` per deployment for proportional distribution                        | Not available; `simple-shuffle` or `latency-based-routing` in LiteLLM Router, but no explicit weight config surface in thegent | Cannot do 90%/10% traffic experiments                                                         | **P2**   |
| **Dynamic model management API**           | `POST /model/new` — add deployments at runtime; `STORE_MODEL_IN_DB=True` for persistence       | Models defined at startup from catalog only                                                                                    | Cannot add a new model deployment without a restart                                           | **P2**   |

### 2.3 Reliability

| Feature                                       | LiteLLM                                                                                                | thegent Current                                                                             | Gap                                                                                                                | Priority |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------- |
| **Per-deployment cooldown / circuit breaker** | `allowed_fails: N` + `cooldown_time: N` — deployment excluded from pool for N seconds after N failures | No deployment-level exclusion; `EnhancedRouter.route()` retries all fallbacks on each error | Failing deployments continue receiving traffic; no automatic exclusion; client re-tries all candidates in sequence | **P0**   |
| **Content policy fallbacks**                  | Separate `content_policy_fallbacks` triggered on moderation rejections                                 | Regular fallback chain only; content policy errors treated as generic errors                | When GPT-4o rejects content, the fallback may also reject it; Claude might accept it — no separate path            | **P1**   |
| **Fallback to specific deployment UUID**      | Fallback can target `model_info.id` for specific deployment, not just model group                      | Fallbacks are model-group names only                                                        | Cannot pin "if gpt-4o-us fails, use gpt-4o-eu specifically"                                                        | **P1**   |
| **Per-request fallback disable**              | `"disable_fallbacks": true` in request body                                                            | No per-request fallback control                                                             | Cannot tell the router "do not fallback on this request; fail fast if primary fails"                               | **P2**   |

### 2.4 Caching

| Feature                               | LiteLLM                                                                                | thegent Current                                                                 | Gap                                                                                                                                | Priority |
| ------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------- |
| **Semantic caching**                  | Redis-semantic (RediSearch) and Qdrant-semantic with configurable similarity threshold | Not implemented; LiteLLM Router has `cache_responses=True` for exact-match only | Similar prompts get no cache benefit; "what is the capital of France?" vs "what's the capital of france?" are treated as different | **P1**   |
| **Multi-backend cache (7 types)**     | local, disk, redis, redis-semantic, qdrant-semantic, s3, gcs                           | In-memory only via `cache_responses=True` in Router                             | No persistent, distributed, or semantic caching                                                                                    | **P1**   |
| **DualCache L1+L2**                   | Automatic two-tier: in-memory L1 for speed, Redis L2 for distribution                  | Single-tier in-memory                                                           | Multi-instance proxy deployments cannot share cache state                                                                          | **P1**   |
| **Cache-hit response headers**        | `x-litellm-cache-key`, `x-litellm-semantic-similarity`                                 | No cache-hit headers                                                            | Clients cannot detect cache hits; no cache observability                                                                           | **P2**   |
| **Per-request cache control**         | `{"cache": {"use-cache": true/false}}` in request body                                 | No per-request cache control                                                    | All requests always use (or don't use) the global cache setting                                                                    | **P2**   |
| **Opt-in cache mode (`default_off`)** | `mode: default_off` — caching disabled unless client opts in per request               | Not available                                                                   | Cannot deploy semantic caching selectively; must be all-on or all-off                                                              | **P2**   |
| **Cache namespace isolation**         | `namespace: "litellm.prod"` key prefix                                                 | No namespacing                                                                  | Cannot isolate cache between production and staging environments                                                                   | **P2**   |

### 2.5 Guardrails

| Feature                                       | LiteLLM                                                                         | thegent Current | Gap                                                                                       | Priority |
| --------------------------------------------- | ------------------------------------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------- | -------- |
| **PII/PHI masking (Presidio)**                | Pre-call PII detection; MASK or BLOCK per entity type; GDPR-eligible deployment | Not implemented | Cannot safely route user-supplied content through cloud LLMs without PII exposure         | **P1**   |
| **Prompt injection detection**                | In-memory detection + Pillar/Lasso integrations as pre-call hooks               | Not implemented | No protection against prompt injection in agent workloads processing untrusted user input | **P1**   |
| **Content policy filtering**                  | LiteLLM Content Filter (regex/keywords, no external deps)                       | Not implemented | No pre-call content validation; relies entirely on provider-side moderation               | **P1**   |
| **Secret detection/redaction**                | Enterprise: masks API keys in request/response logs                             | Not implemented | API keys that appear in agent prompts/responses are logged in plaintext                   | **P2**   |
| **Blocked user lists**                        | Enterprise: opt-out capability for specific user IDs                            | Not implemented | Cannot prevent specific users from accessing the proxy                                    | **P2**   |
| **Guardrail hooks (pre/post/during/logging)** | Configurable hook points with named guardrails                                  | Not implemented | No lifecycle hook framework for request validation                                        | **P2**   |

### 2.6 Multi-Tenant Architecture (Teams / Orgs / Virtual Keys)

| Feature                        | LiteLLM                                                                            | thegent Current                                                                                                      | Gap                                                                                 | Priority |
| ------------------------------ | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------- |
| **Virtual key lifecycle**      | Full key management: create, rotate, block, expire, set budgets/models/rate-limits | No virtual key system; single shared API key per provider                                                            | No per-consumer key isolation; all consumers share the provider API keys            | **P0**   |
| **Per-key model restrictions** | `models: ["gpt-4o", "claude-sonnet"]` — key can only access listed models          | Not implemented                                                                                                      | Cannot prevent a key from accessing expensive models                                | **P0**   |
| **Team budget scoping**        | Team has its own budget; all keys belonging to the team share that budget          | `BudgetManager` has `project_id`-scoped budgets (closer to a team), but no key-to-project association in proxy layer | Agent teams (coder, reviewer, planner) cannot have isolated spend caps in the proxy | **P1**   |
| **Per-key rate limiting**      | `tpm_limit`, `rpm_limit`, `max_parallel_requests` enforced per virtual key         | No per-key rate limiting                                                                                             | Cannot throttle a specific key from consuming all capacity                          | **P1**   |
| **Per-key model aliases**      | Virtual keys carry their own alias table (`gpt-4` → `gpt-4o-mini` for budget keys) | Not implemented                                                                                                      | Cannot give different agents different model name → actual model mappings           | **P1**   |
| **Key rotation**               | `auto_rotate`, `rotation_interval`, `POST /key/regenerate`                         | Not implemented                                                                                                      | No credential rotation for compliance                                               | **P2**   |
| **Service account keys**       | Machine-to-machine keys that survive employee turnover                             | Not implemented                                                                                                      | No distinction between user and service keys                                        | **P2**   |
| **Org-level isolation**        | Organizations create complete tenant boundaries (Enterprise)                       | Not implemented                                                                                                      | No multi-organization support                                                       | **P2**   |

### 2.7 Observability

| Feature                                 | LiteLLM                                                                                                     | thegent Current                                                              | Gap                                                                                         | Priority |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------- |
| **Prometheus `/metrics` endpoint**      | 25+ metric families with per-deployment, per-key, per-team labels                                           | No Prometheus metrics endpoint; cost tracking is JSONL file + in-memory only | Cannot integrate with Grafana, Prometheus Alertmanager, or any standard observability stack | **P0**   |
| **Deployment health metrics**           | `litellm_deployment_state` (0/1/2), `litellm_deployment_cooled_down`, success/failure counts per deployment | No deployment-level health tracking                                          | Cannot see which specific provider deployments are healthy vs. degraded                     | **P1**   |
| **TTFT (time-to-first-token) metrics**  | `litellm_llm_api_time_to_first_token_metric` Prometheus histogram                                           | Not tracked                                                                  | Streaming latency quality is invisible                                                      | **P1**   |
| **LiteLLM overhead latency metric**     | `litellm_overhead_latency_metric` separates proxy processing time from LLM API time                         | Not tracked                                                                  | Cannot distinguish slow LLM from slow proxy code                                            | **P1**   |
| **Per-provider fallback count metrics** | `litellm_deployment_successful_fallbacks`, `litellm_deployment_failed_fallbacks`                            | `_fallbacks: int` counter in `RoutingStats`, not per-deployment              | Cannot tell which model/provider is causing fallbacks                                       | **P1**   |
| **Redis latency metrics**               | `litellm_redis_latency` histogram                                                                           | No Redis metrics                                                             | Infrastructure monitoring gap when Redis is used                                            | **P2**   |
| **Region outage alerting**              | Alerts when ≥5 requests to a provider region fail in 1 minute (Enterprise)                                  | `alerting.py` has `alert_provider_error()` but no region-level aggregation   | Cannot detect region-level outages; treats each failure independently                       | **P2**   |
| **Budget remaining metrics**            | `litellm_remaining_team_budget_metric`, `litellm_remaining_api_key_budget_metric` in Prometheus             | Budget remaining available in API but not Prometheus                         | No automated alerts on budget consumption via existing monitoring stack                     | **P2**   |

### 2.8 MCP Gateway

| Feature                             | LiteLLM                                                                                | thegent Current                                                                   | Gap                                                                       | Priority |
| ----------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------- |
| **Centralized MCP server registry** | Register multiple MCP servers via config or UI; namespaced tool names                  | thegent has MCP management (`thegent mcp prune`) but no centralized proxy gateway | Each agent session negotiates its own MCP connections; no shared registry | **P1**   |
| **Per-key MCP tool permissions**    | Restrict which MCP servers/tools a virtual key can access                              | Not implemented                                                                   | Any key can use any registered MCP tool; no isolation between agent roles | **P1**   |
| **Per-team MCP budgets**            | Track and cap spend on MCP tool usage per team                                         | Not implemented                                                                   | MCP tool costs not attributed to teams/keys                               | **P2**   |
| **MCP OAuth gateway**               | Handles OAuth discovery, PKCE, token exchange transparently for registered MCP servers | thegent agents handle OAuth themselves per session                                | No centralized credential management for MCP OAuth flows                  | **P2**   |
| **OpenAPI → MCP auto-conversion**   | REST APIs with OpenAPI specs automatically become MCP tools                            | Not implemented                                                                   | Adding a new tool requires manual MCP server implementation               | **P2**   |

### 2.9 Request/Response API Extensions

| Feature                                              | LiteLLM                                                      | thegent Current                                                         | Gap                                                                                               | Priority |
| ---------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------- |
| **`x-litellm-model-id` response header**             | Stable deployment UUID of the model that handled the request | `model_used` in `RoutingResult` but not exposed as HTTP response header | Clients cannot tell which specific deployment (of potentially several with same name) served them | **P1**   |
| **`x-litellm-response-cost` response header**        | USD cost of the response, per response                       | Not exposed in proxy response                                           | Clients cannot see per-request cost without querying the cost log                                 | **P1**   |
| **`x-litellm-key-remaining-budget` response header** | Remaining budget for the key, per response                   | Not exposed                                                             | Clients cannot self-monitor their budget consumption                                              | **P2**   |
| **`Litellm-metadata` request header**                | Attach arbitrary metadata to spend logs and callbacks        | `metadata` body field in some contexts but no header variant            | No header-based metadata injection for contexts where body modification is inconvenient           | **P2**   |
| **Per-request `ttl` field**                          | `{"ttl": 120}` in request body overrides cache TTL           | Not available                                                           | Cannot vary cache duration per request type (e.g., longer TTL for stable reference queries)       | **P2**   |

---

## 3. Features in OpenRouter Gap Analysis That Overlap With LiteLLM Gaps

The following gaps were already identified in the OpenRouter gap analysis and also apply to LiteLLM
parity (not duplicated above, just cross-referenced):

| From OpenRouter Gap Analysis                       | LiteLLM Equivalent                                 |
| -------------------------------------------------- | -------------------------------------------------- |
| No model ID normalization (P0)                     | LiteLLM: `model_group_alias` in router_settings    |
| Tool call streaming broken in transform mode (P1)  | LiteLLM handles tool call streaming natively       |
| TLS verification disabled for remote backends (P1) | LiteLLM uses proper TLS for provider calls         |
| 402/503 error codes not handled (P2)               | LiteLLM maps provider errors to correct HTTP codes |

---

## 4. LiteLLM-Exclusive Features Beyond What OpenRouter Has

These are features LiteLLM has that OpenRouter **does not** have, meaning they are not in the
OpenRouter gap analysis at all:

### 4.1 Provider Budget Routing (P0)

**LiteLLM:** `provider_budget_config` — hard USD cap per provider per time period. When provider
budget is exhausted, routing automatically skips that provider. Prometheus metric tracks remaining
budget per provider.

**OpenRouter:** No provider-level budget routing. OpenRouter itself is the provider.

**thegent impact:** This is the most operationally critical missing feature for a multi-provider
proxy. Without per-provider caps, a single API key misconfiguration or rogue agent session can
exhaust OpenAI budget while Anthropic and Gemini have capacity.

**Implementation path:** Add `provider_budget_config` dict to `RouterConfig`; track spend per
provider in `CostTracker` (add `by_provider_today` dict); check in `build_litellm_model_list()` at
route selection time; exclude providers above cap from `model_list`.

### 4.2 Deployment Pool Load Balancing (P0)

**LiteLLM:** Multiple `model_list` entries with the same `model_name` form a pool. A single
`model_name: gpt-4o` can have 5 Azure deployments, 2 direct OpenAI deployments, and a backup
Bedrock deployment — all load-balanced.

**OpenRouter:** Not applicable; OpenRouter is the single endpoint.

**thegent impact:** thegent currently treats each `provider/model` as a distinct route. There is
no concept of "two different Azure GPT-4o endpoints backing the same logical model". Adding pool
support enables horizontal scaling of a single model across multiple API keys, regions, or
sub-accounts.

**Implementation path:** Extend `build_litellm_model_list()` to generate multiple entries with the
same `model_name` for models with multiple configured backends; allow catalog `Route` objects to
carry `backends: list[Backend]`.

### 4.3 Virtual Key System (P0 for multi-tenant use)

**LiteLLM:** Full CRUD virtual key API; each key carries budget, rate limits, model restrictions,
aliases, tags, expiry; keys are scoped to teams; rotation and blocking supported.

**OpenRouter:** Simple API keys with no sub-key system.

**thegent impact:** thegent is building teammate runners and agent session isolation. Without a
virtual key layer, all agent sessions share the same API credentials and budget. The teammate
isolation model (`isolation/uid_pool.py`, `isolation/sub_user_provider.py`) could leverage a
virtual key system to give each agent session an isolated budget and model access profile.

**Implementation path:** Short-term: add a `VirtualKeyRegistry` (in-memory or SQLite) that maps
`sk-<random>` tokens to `{budget_limit, rpm_limit, allowed_models, project_id, tags}` and enforce
in the CLIProxy request path before forwarding to the backend.

### 4.4 Circuit Breaker / Deployment Cooldown (P0)

**LiteLLM:** `allowed_fails` + `cooldown_time` per deployment. A deployment that fails N times is
removed from the routing pool for N seconds, then re-admitted.

**OpenRouter:** Implicit — OpenRouter handles provider health internally.

**thegent impact:** thegent's `EnhancedRouter.route()` iterates fallback chains on error. If a
provider is having a transient outage, every request tries the failing provider, gets an error,
then falls back — even requests from N seconds later that would still hit the same failing provider.
A cooldown removes the provider from consideration for the duration of the outage.

**Implementation path:** Add a `DeploymentHealthRegistry` (dict: `{provider: excluded_until}`)
updated by the error handler in `EnhancedRouter.route()`; check before building the candidate list.

### 4.5 Semantic Caching (P1)

**LiteLLM:** Redis-semantic (RediSearch) and Qdrant-semantic with configurable similarity
threshold. Similar prompts hit the cache at configurable cosine-similarity thresholds.

**OpenRouter:** No semantic caching.

**thegent impact:** Agent workloads often repeat semantically similar prompts (e.g., "summarize
this code" on slightly different code chunks). Exact-match caching saves little; semantic caching
could achieve 20-40% cache hit rates on typical agentic workflows, reducing both latency and cost.

**Implementation path:** Add `redis-semantic` backend support to LiteLLM Router configuration;
expose `cache_params.type` and `similarity_threshold` in `RouterConfig`.

### 4.6 Tag-Based Routing to Deployment Pools (P0)

**LiteLLM:** Deployments carry `tags`; requests carry `tags` (header or body); router matches
them. `default` tag catches untagged requests.

**OpenRouter:** No tag routing; OpenRouter routes by `provider` object in request body.

**thegent impact:** This is the primary mechanism for multi-tier routing in LiteLLM. It enables:

- Free vs. paid user tiers (different model deployments, same model name)
- Agent role tiers (coder agents get GPT-4o; reviewer agents get cheaper Claude Haiku)
- Region compliance (EU agents tagged `eu` route to EU-only deployments)

**Implementation path:** Add `tags` field to `model_info` in catalog `Route` objects; add tag
matching logic in `_proxy_request` or `build_litellm_model_list()` that filters the LiteLLM
model_list by matching tags from the incoming request's `x-litellm-tags` header.

### 4.7 Prometheus Metrics Endpoint (P0)

**LiteLLM:** Native `/metrics` endpoint with 25+ metric families including per-deployment health,
fallback counts, TTFT histograms, budget remaining, and Redis latency.

**OpenRouter:** No Prometheus; not self-hosted.

**thegent impact:** thegent has no way to feed routing health into any monitoring stack. All
operational insight comes from parsing JSONL cost logs. A Prometheus endpoint would enable
Grafana dashboards, PagerDuty alerting on deployment failures, and budget burn-rate tracking.

**Implementation path:** Add a Prometheus endpoint to `cliproxy_adapter.py` using the
`prometheus_client` library; expose:

1. `thegent_routing_requests_total` (labels: provider, model, status)
2. `thegent_routing_latency_seconds` (histogram; labels: provider, model)
3. `thegent_cost_usd_total` (labels: provider, model)
4. `thegent_budget_remaining_usd` (labels: project_id)
5. `thegent_deployment_cooldown_total` (labels: provider)

### 4.8 Config-as-Code for Model Deployments (P1)

**LiteLLM:** `config.yaml` fully defines the proxy; version-control friendly; can be loaded from
S3/GCS; changes picked up on restart or hot-reload.

**OpenRouter:** Web UI/API configuration; no GitOps.

**thegent impact:** thegent uses Python catalog files (`model_metadata.py`,
`harness_model_mapping.py`, `provider_types.py`). Adding a new provider requires code changes +
deployment. A config.yaml-style external configuration would allow operators to add providers
without code changes.

**Implementation path:** Already partially addressed by LiteLLM's own Router (which accepts a
`model_list`). Exposing a `proxy_config.yaml` that maps to `build_litellm_model_list()` would
be the first step.

---

## 5. Summary: Prioritized Implementation Roadmap

### P0 — Core Infrastructure Gaps (implement before claiming provider parity)

| Gap                                       | Files to Touch                                                   | Effort        |
| ----------------------------------------- | ---------------------------------------------------------------- | ------------- |
| Provider budget routing                   | `routing/cost_tracker.py`, `routing/litellm_router.py`           | S (1-2 days)  |
| Deployment pool concept                   | `routing/litellm_router.py`, `models/catalog.py`                 | M (3-5 days)  |
| Per-deployment cooldown (circuit breaker) | `routing/litellm_router.py` new `DeploymentHealthRegistry`       | S (1-2 days)  |
| Virtual key system (minimal)              | New `routing/virtual_keys.py` + `cliproxy_adapter.py` middleware | L (1-2 weeks) |
| Tag-based routing to pools                | `routing/litellm_router.py`, `cliproxy_adapter.py`               | M (2-3 days)  |
| Prometheus `/metrics` endpoint            | `cliproxy_adapter.py` new route + `prometheus_client`            | M (2-3 days)  |
| Wildcard provider routing                 | `routing/litellm_router.py` `build_litellm_model_list()`         | S (1 day)     |

### P1 — Significant Value (implement in next sprint)

| Gap                                      | Files to Touch                                            | Effort                         |
| ---------------------------------------- | --------------------------------------------------------- | ------------------------------ |
| Pre-call context window check + fallback | `routing/litellm_router.py`, `cliproxy_adapter.py`        | S (1 day)                      |
| Semantic caching (Redis-semantic)        | `routing/litellm_router.py` `get_litellm_router()`        | S (1 day, uses LiteLLM native) |
| Budget reset periods (flexible)          | `routing/cost_tracker.py`, `routing/cost_aware_router.py` | S (1 day)                      |
| Soft-budget alert thresholds             | `routing/alerting.py` + `routing/cost_tracker.py`         | XS (0.5 day)                   |
| x-litellm-model-id response header       | `cliproxy_adapter.py` `_proxy_request`                    | XS (0.5 day)                   |
| x-litellm-response-cost response header  | `cliproxy_adapter.py` + `routing/litellm_router.py`       | XS (0.5 day)                   |
| Per-team budget scoping                  | `routing/cost_aware_router.py`, `routing/virtual_keys.py` | M (2-3 days)                   |
| Traffic mirroring / shadow deployments   | `routing/litellm_router.py`                               | M (2-3 days)                   |
| PII masking (Presidio)                   | New `guardrails/presidio.py` + `cliproxy_adapter.py` hook | M (3-5 days)                   |

### P2 — Polish and Compliance (implement in future sprints)

| Gap                           | Notes                                                 |
| ----------------------------- | ----------------------------------------------------- |
| Content policy fallbacks      | Separate fallback chain from generic errors           |
| Semantic caching with Qdrant  | Higher-performance semantic cache for heavy workloads |
| Per-request cache control     | `cache.use-cache`, `ttl` in request body              |
| Audit logs                    | Full action log for enterprise deployments            |
| Key rotation                  | Automated credential rotation                         |
| Region-aware routing          | Pre-call region compliance check                      |
| MCP gateway access control    | Per-key MCP server/tool permissions                   |
| OpenAPI → MCP auto-conversion | REST APIs become MCP tools automatically              |

---

## 6. Features thegent Has That LiteLLM Does NOT

These are thegent competitive advantages not present in LiteLLM Proxy:

| Feature                             | Where                                                                      |
| ----------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Harness-native routing**          | Routes to Codex CLI, Claude Code, Gemini CLI as native processes, not HTTP | `routing/provider_types.py` NATIVE_CLI_PROVIDERS          |
| **Codex Responses API translation** | Full 8-event SSE sequence translation; WebSocket bridge                    | `cliproxy_adapter.py` `_ResponsesStreamState`             |
| **Pareto-front model selection**    | Multi-objective optimization (cost × quality × speed)                      | `routing/pareto_router.py`                                |
| **Donut Architecture integration**  | Cross-session usage harvesting for routing decisions                       | `routing/donut_adapter.py`                                |
| **Agent task-type routing**         | Routes by task type (code, analysis, conversation)                         | `routing/task_router.py`, `routing/auto_router.py`        |
| **Session/agent isolation**         | Linux UID pool for process isolation per agent                             | `isolation/uid_pool.py`, `isolation/sub_user_provider.py` |
| **MCP server management**           | `thegent mcp prune`, session-level MCP lifecycle                           | `mcp/borrowed_tools.py`                                   |
| **Teammate runner model**           | Named agent roles with persistent sessions                                 | `agents/teammate_runner.py`                               |

---

## Sources

- `docs/research/LITELLM_PROXY_RESEARCH_2026-02-20.md` (primary source)
- `docs/research/OPENROUTER_GAP_ANALYSIS_2026-02-20.md` (cross-reference)
- `src/thegent/routing/litellm_router.py` (current thegent LiteLLM integration)
- `src/thegent/routing/cost_tracker.py` (current cost tracking)
- `src/thegent/routing/cost_aware_router.py` (current budget-aware routing)
- `src/thegent/cliproxy_adapter.py` (current CLIProxy ASGI app)
