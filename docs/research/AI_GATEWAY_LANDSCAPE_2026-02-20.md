<DONE>
# AI Gateway / LLM Proxy Landscape — Research (2026-02-20)

## Overview

The AI gateway market has matured significantly by 2026. Products have moved well beyond simple proxy/fan-out and now compete across six dimensions: **routing intelligence**, **observability depth**, **security/guardrails**, **cost governance**, **agent/MCP support**, and **deployment flexibility**. The market splits into three broad archetypes:

1. **Infrastructure-first gateways** — Focus on routing, performance, reliability, and multi-provider unification (Bifrost, LiteLLM, Portkey, Helicone, Cloudflare, Kong, Vercel, Envoy AI Gateway).
2. **Routing-intelligence-first products** — ML-based model selection, not just proxy fan-out (Not Diamond, Martian, Unify, Requesty).
3. **Observability/eval-first platforms** — Tracing and evaluation integrated with a proxy (Helicone, Langfuse, Braintrust).

Emerging in 2026: **MCP-native gateways** that sit between AI agents and tools rather than between agents and LLMs (AgentGateway, Operant AI, TrueFoundry MCP Gateway, Azure APIM + MCP). This is a distinct and rapidly growing sub-category.

---

## Competitive Profiles

### Tier 1 — Deep Research

#### 1. Helicone (helicone.ai)

**What it is:** Open-source LLM observability platform that also functions as a high-performance AI gateway. Processed 2 billion+ LLM interactions. YC W23.

**Deployment model:** SaaS (managed cloud via Cloudflare Workers + ClickHouse + Kafka) AND self-hosted (Docker/Helm). True dual-mode.

**OpenAI-compatible API:** Yes — drop-in proxy. Also async SDK integration mode (no proxy required).

**Key differentiating features:**

- Observability-first architecture — every request gets trace/session/segment tracking automatically.
- Sub-1ms computational overhead (Rust + Cloudflare Workers edge deployment).
- Prompt management with version tracking and production-data feedback loop.
- Playground with production data playback.
- Session tracing for multi-step agent flows.

**Unique features:**

- **Async integration mode** — can ingest observability data without being in the hot path at all. No other major gateway offers this as a first-class option.
- **SOC 2 Type II + HIPAA** compliance with full self-hosted option.
- **Proxy vs Async** dual integration — teams can choose whether to route through Helicone or just push logs to it.
- Cache is at the edge (Cloudflare), not just centralized Redis.

**Pricing:** Free (10k req/month), paid from $20/seat/month.

---

#### 2. Not Diamond (notdiamond.ai)

**What it is:** ML-based model router that automatically selects the best LLM for each query. IBM-backed. Notable customers: IBM, Dropbox, Notion, Snowflake, OpenRouter.

**Deployment model:** SaaS API + VPC/on-premise enterprise option. SOC-2 and ISO 27001 certified.

**OpenAI-compatible API:** Yes — acts as a drop-in router.

**Key differentiating features:**

- **ML meta-model routing** — combines multiple LLMs into a meta-model that learns when to invoke each. Not rule-based, not benchmark-lookup: actual learned routing.
- **Prompt adaptation** — automatically rewrites prompts for different model families, improving accuracy up to 60%.
- **Agent optimization** — self-improving algorithms for multi-step agentic workflows (not just single-turn routing).
- Three optimization axes: Quality, Cost, Latency — user-configurable per application.

**Unique features:**

- **Automatic prompt rewriting per model** — no other router does this as a first-class feature. Converts hours of manual prompt engineering to minutes.
- **Agent workflow optimization** — beyond single-call routing, optimizes multi-step agent plans.
- Their routing is ML-trained, not just benchmark lookup or rule matching.

**Pricing:** Contact sales; enterprise contracts.

---

#### 3. Martian (withmartian.com)

**What it is:** LLM router built on "Model Mapping" — a mechanistic interpretability technique that converts models from black boxes into interpretable representations to enable accurate per-query routing. $9M raised (Accenture invested).

**Deployment model:** SaaS API; enterprise VPC options.

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- **Model Mapping** — the first commercial application of mechanistic interpretability for routing. Converts LLM weights into interpretable representations to predict which model will handle each specific query best.
- **Automatic new model indexing** — as new models release, Martian indexes them and makes them available for routing with zero manual configuration.
- **Compliance routing** — routes based on model compliance properties (e.g., only GDPR-compliant endpoints).
- Uses model compression, quantization, distillation to make routing predictions without running full models.

**Unique features:**

- **Mechanistic interpretability as routing signal** — only Martian does this. Competitors use benchmarks or embeddings; Martian uses model internals.
- **Zero-friction new model adoption** — automatic model discovery and indexing is unique.
- Performance claim: outperforms GPT-4 alone by using dynamic routing across models.

**Pricing:** Contact sales; enterprise.

---

#### 4. Unify (unify.ai)

**What it is:** LLM routing and benchmarking platform that dynamically routes prompts to the best model/provider combination based on real-time performance data. Benchmarks updated every 10 minutes.

**Deployment model:** SaaS (cloud-hosted). OpenAI-compatible single endpoint.

**OpenAI-compatible API:** Yes — single endpoint accessing all providers.

**Key differentiating features:**

- **Live benchmark leaderboard** — continuous real-world benchmarking updated every 10 minutes across providers. Not static evals.
- **Three-slider UX** — quality / cost / latency sliders let you tune routing without writing code.
- **Task-specific routing** — benchmark your actual prompts against candidate models, then steer traffic to best performers.
- Routes across providers (not just models) — can route the same model across different hosting providers based on real-time latency and price.

**Unique features:**

- **Provider-level routing** — can route between e.g. Llama-3.1-405B on Fireworks vs Together vs Groq based on real-time pricing and latency. No other gateway competes at the provider-instance level this way.
- **Continuous live benchmarking as routing signal** — updates every 10 minutes.

**Pricing:** Pay-per-use; see unify.ai.

---

#### 5. Requesty (requesty.ai)

**What it is:** Production-grade unified LLM gateway routing 500+ models with enterprise governance, observability, and a Rust core for 8ms P50 overhead. Positioned as OpenRouter alternative for enterprises.

**Deployment model:** SaaS (managed). OpenAI-compatible API.

**OpenAI-compatible API:** Yes — drop-in OpenAI SDK replacement.

**Key differentiating features:**

- 500+ models across all major providers.
- **Latency-based routing** — continuously measures response times and routes to fastest model in real time.
- **40+ tracked metrics** with multi-dimensional grouping (user, model, metadata, custom dimensions).
- **Conversation coherence with load balancing** — trace ID consistency preserves multi-turn conversation state across backends.
- **Rust core** delivering 8ms P50 overhead and horizontal scale.

**Unique features:**

- **5% flat markup pricing model** — transparent, predictable. $5/1M tokens becomes $5.25/1M through Requesty including all features.
- **Multi-dimensional observability** — 40+ metrics with custom dimension grouping is unusually deep for a managed SaaS.
- **Content-aware PII + prompt injection detection** built in at the gateway layer.

**Pricing:** 5% markup on model costs. All features included.

---

### Tier 2 — Overview Level

#### 6. Braintrust (braintrustdata.com)

**What it is:** AI observability and evaluation platform with a free OpenAI-compatible proxy. Eval-first: the proxy exists to capture data for evaluation, not as the primary product.

**Deployment model:** SaaS + open-source proxy (self-hostable on Cloudflare Workers). Free proxy even without Braintrust account.

**OpenAI-compatible API:** Yes — fully compatible, 100+ models including GPT-5, Claude 4, Gemini 2.5.

**Key differentiating features:**

- **Online evaluation** — automatically scores production traffic as logs arrive, asynchronously (zero added latency).
- **Unified reasoning parameters** — normalizes `reasoning_effort`, `reasoning_enabled`, `reasoning_budget` across OpenAI/Anthropic/Google.
- Automatic caching (under 100ms for cache hits).
- Eval-native: every logged trace can become an eval dataset entry.

**Unique features:**

- **Asynchronous online eval** — scores production traffic in background, zero latency impact. Connects eval directly to production gateway.
- **Unified reasoning abstraction** across providers (normalize o1/Claude-extended-thinking/Gemini thinking into one API).

**Pricing:** Free proxy (even without account); paid tiers for eval platform.

---

#### 7. Langfuse (langfuse.com)

**What it is:** Open-source LLM engineering platform — observability, prompt management, evals, datasets. Gateway is not the primary product; Langfuse integrates as an observability backend for LiteLLM and other gateways.

**Deployment model:** SaaS + open-source self-hosted (Docker). YC W23.

**OpenAI-compatible API:** Via LiteLLM integration, not native.

**Key differentiating features:**

- OpenTelemetry-native — thin layer on top of official OTel client with LLM-specific helpers (token usage, cost tracking, prompt linking, scoring).
- 50+ library/framework integrations (LangChain, LlamaIndex, etc.).
- Full LLM Playground for prompt iteration.
- Dataset management for eval.
- Prompt management with versioning.

**Unique features:**

- **OpenTelemetry-first** — only major platform built natively on OTel rather than a custom telemetry format. Best for organizations already using OTel infrastructure.
- **Score/feedback loop** — human and automated feedback can be attached to any trace.

**Pricing:** Free self-hosted; cloud tiers from ~$49/month.

---

#### 8. Azure API Management AI Gateway (Microsoft)

**What it is:** Azure APIM extended with LLM-specific policies (GA 2025). Enterprise integration of traditional API management with AI gateway capabilities.

**Deployment model:** Azure cloud managed service; hybrid on-premises via Azure Arc. Enterprise-only.

**OpenAI-compatible API:** Yes — imports OpenAI/Azure OpenAI backends as standard APIM APIs.

**Key differentiating features:**

- **Token-level rate limiting** — set TPM (tokens per minute) limits per consumer.
- **Semantic caching** — vector-proximity cache using embeddings to recognize semantically equivalent prompts.
- **Managed identity auth** — no API keys for Azure AI services; uses Azure Managed Identity.
- Load balancing with circuit breakers across multiple Azure OpenAI deployments.
- WebSocket Realtime API support (GPT-4o Realtime) with token tracking.
- MCP server management via APIM policies.
- Integration with Azure AI Content Safety for prompt moderation.
- Azure Monitor / Application Insights for token consumption dashboards.

**Unique features:**

- **Native Azure ecosystem integration** — Managed Identity, Content Safety, Monitor, VNET, Entra ID — all first-class. No other gateway matches this for Azure-native organizations.
- **WebSocket Realtime API with token tracking** — one of few gateways with built-in streaming/realtime token metering.

**Pricing:** Azure APIM pricing + consumption-based.

---

#### 9. AWS Bedrock (as a gateway)

**What it is:** AWS's managed AI platform that also provides an OpenAI-compatible gateway (Bedrock Access Gateway, open-source sample) and multi-provider routing guidance.

**Deployment model:** AWS managed (SaaS on AWS), plus open-source Bedrock Access Gateway deployable on Lambda/Fargate.

**OpenAI-compatible API:** Yes — Bedrock Access Gateway provides OpenAI-compatible REST on top of Bedrock.

**Key differentiating features:**

- Access to all Bedrock-hosted models (Anthropic, Meta, Mistral, Amazon Nova, Stability, AI21, Cohere) through one endpoint.
- **Prompt Caching** for Claude and Nova: up to 90% cost reduction, 85% latency reduction for repeated prompts.
- AWS IAM auth (no API keys needed when running in AWS).
- Intelligent retry and fallback across regions/models.
- VPC-native deployment — fully within customer's AWS account.

**Unique features:**

- **No-egress routing** — runs entirely within AWS VPC; data never leaves customer's cloud account.
- **AgentCore Gateway** (2025/2026): transforms enterprise APIs and data sources into MCP-compatible tools for agents — one of the first hyperscaler MCP gateways.

**Pricing:** Bedrock model pricing; no additional gateway fee for Bedrock Access Gateway.

---

#### 10. Google Vertex AI (as a gateway)

**What it is:** Google's AI platform with unified model serving, also used as a gateway for accessing Gemini and third-party models.

**Deployment model:** Google Cloud managed.

**OpenAI-compatible API:** Yes — Vertex AI provides OpenAI-compatible endpoints for Gemini models.

**Key differentiating features:**

- Access to all Gemini models + third-party models (Llama, Mistral, Claude via Model Garden).
- TPU/GPU-accelerated serving.
- Grounding with Google Search (real-time web retrieval baked in).
- Built-in safety filters (Vertex AI Safety).
- Vertex AI Pipelines for orchestration.

**Unique features:**

- **Grounding with Google Search** — native, real-time web search integrated into completions. No other gateway has direct search grounding as a first-class feature.

**Pricing:** Vertex AI pricing (per token).

---

#### 11. Fireworks AI

**What it is:** Fast inference platform specializing in open-source model serving (Llama, DeepSeek, Mistral, etc.). OpenAI-compatible API. 140B+ tokens/day.

**Deployment model:** SaaS (serverless per-token) + Dedicated GPU clusters + BYOC (Bring-Your-Own-Cloud, runs inference engine inside customer VPC).

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- Optimized inference engine: DeepSeek V3/R1 at 250+ tokens/second.
- 99.99% uptime SLA.
- Fine-tuned model hosting (PEFT, LoRA).
- **BYOC** — inference engine runs inside customer's VPC on their GPU hardware.

**Unique features:**

- **BYOC inference** — unique for fast-inference providers. Customer gets Fireworks speed inside their own cloud account.
- **Fine-tuning + serving combined** — same platform for training and serving custom models.

**Pricing:** Serverless per-token; dedicated per-GPU-second; BYOC custom.

---

#### 12. ZenMux (zenmux.ai)

**What it is:** Enterprise AI API aggregation platform with a unique "LLM Insurance" model — automatic compensation for hallucinations, latency breaches, and throughput drops.

**Deployment model:** SaaS. One API key for 200+ LLMs.

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- **LLM Insurance** — automatic credits for hallucinations detected, latency exceeding thresholds, or throughput degradation. No other gateway has this.
- Global Edge Acceleration via Cloudflare.
- Multi-provider failover.
- Regular Human Last Exam (HLE) quality tests — community-auditable real-time benchmarks.
- Task classification for automatic model selection.

**Unique features:**

- **LLM Insurance as a product** — automatic compensation with no claims process. Entirely novel in the market.
- **HLE quality benchmarks** — community-auditable quality monitoring published in real time.

**Pricing:** Per-use.

---

#### 13. Envoy AI Gateway (envoyproxy.io/ai-gateway)

**What it is:** Open-source project extending Envoy Gateway (CNCF) for LLM traffic management. Infrastructure-native, Kubernetes-first.

**Deployment model:** Self-hosted on Kubernetes (open-source, Apache 2.0).

**OpenAI-compatible API:** Yes — single OpenAI-compatible endpoint routing to any provider.

**Key differentiating features:**

- Built on Envoy (battle-tested, CNCF), not a new proxy.
- Token-based rate limiting (not just request-count).
- MCP protocol support (one of few gateways with MCP as first-class).
- **Gateway API Inference Extension v1.0** — intelligent endpoint selection with spec-stable API.
- OpenTelemetry tracing with OpenInference conventions.
- Cached token statistics from cloud providers (Anthropic, Bedrock) — accurate cost attribution for prompt caching.
- Header mutation for advanced routing.

**Unique features:**

- **Built on Envoy + Kubernetes Gateway API** — for organizations running Envoy-based service meshes (Istio, etc.), this is the natural choice; no other AI gateway integrates natively.
- **xDS dynamic config** — runtime updates without restarts, inherited from Envoy.

**Pricing:** Free, open-source.

---

#### 14. TrueFoundry (truefoundry.com)

**What it is:** Full-stack, Kubernetes-native LLMOps platform with a dedicated AI Gateway + MCP Gateway. Named in Gartner 2025 Market Guide for AI Gateways.

**Deployment model:** SaaS + self-hosted (Kubernetes).

**OpenAI-compatible API:** Yes — 1000+ LLMs via unified interface.

**Key differentiating features:**

- **MCP Gateway** — dedicated gateway for agent-tool communication using MCP protocol, not just LLM routing. Claims sub-3ms added latency for MCP routing.
- **99% token savings** with N×M integration control for MCP (one gateway replaces N-agents × M-tools direct integrations).
- OAuth 2.0 security for MCP traffic.
- Fine-grained access control and permissions per user/model/application.
- Full MLOps integration: model serving, autoscaling, fine-tuning, CI/CD.

**Unique features:**

- **Unified LLM + MCP gateway** — both LLM routing and agent-tool routing in one control plane. Only platform doing both as first-class.
- **MLOps-native** — gateway is part of a full model lifecycle platform including fine-tuning and deployment.

**Pricing:** Contact sales; enterprise.

---

#### 15. AgentGateway (agentgateway.dev)

**What it is:** Open-source, Rust-based agentic proxy for agent-to-agent (A2A) and agent-to-tool (MCP) communication. Solo.io-backed. Next-generation gateway for agentic AI.

**Deployment model:** Self-hosted (open-source, Rust binary or Docker). Kubernetes-native via kgateway.

**OpenAI-compatible API:** Not primarily — focuses on MCP and A2A protocols.

**Key differentiating features:**

- **A2A protocol support** — one of few gateways implementing Google's Agent-to-Agent protocol natively.
- **Federated MCP endpoint** — single endpoint for all MCP tools with centralized registry and self-service discovery.
- **REST-to-MCP conversion** — automatically exposes existing REST APIs as MCP-native tools.
- RBAC for agent/tool access.
- Multi-tenancy with resource isolation.
- OTel + Prometheus + Grafana + Jaeger out of box.
- **xDS dynamic config** — runtime updates without downtime.
- **Developer portal** — self-service UI for agent and tool developers.

**Unique features:**

- **A2A + MCP dual protocol** — only open-source gateway implementing both agent communication protocols.
- **REST-to-MCP bridge** — automatic conversion of existing REST APIs into MCP tools without code changes.
- **Federated tool registry** — centralized, self-service.

**Pricing:** Free, open-source (Apache 2.0).

---

#### 16. Operant AI (operant.ai)

**What it is:** AI security platform with MCP Gateway focus. "AI Gatekeeper" product. Featured in Gartner MCP cybersecurity guide 2026.

**Deployment model:** SaaS + enterprise.

**OpenAI-compatible API:** Focused on MCP, not LLM routing.

**Key differentiating features:**

- **3D Runtime Defense** — live traffic graphs showing active access patterns between AI agents and MCP servers.
- Detection of: prompt injection, jailbreaks, tool poisoning, rogue agents, zero-click attacks ("Shadow Escape"), zero-day vulnerabilities.
- **Inline auto-redaction** of sensitive data in MCP traffic.
- "Private mode" operation.
- Comprehensive audit logs for agent-tool interactions.

**Unique features:**

- **Shadow Escape attack detection** — zero-click AI exploits specific to MCP protocol. Unique security research and detection.
- **Agent Protector** (Feb 2026) — real-time security for entire agentic ecosystem.
- Security-research-backed: publishes original research on AI attack vectors.

**Pricing:** Enterprise.

---

#### 17. IBM API Connect AI Gateway

**What it is:** IBM's enterprise API management platform with AI gateway capabilities integrated into API Connect.

**Deployment model:** Multi-deployment: cloud, on-premises, hybrid.

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- Request rate limiting and response caching.
- Enterprise analytics and audit trails.
- Built-in compliance support with data masking.
- Integration with IBM Watson services.

**Unique features:**

- **IBM enterprise ecosystem integration** — Watson, OpenShift, IBM Cloud IAM. Relevant only for IBM-native organizations.

---

#### 18. GitLab AI Gateway

**What it is:** GitLab's internal AI gateway powering GitLab Duo (AI coding assistant) features, unified across GitLab.com, self-managed, and dedicated instances.

**Deployment model:** SaaS (bundled with GitLab).

**OpenAI-compatible API:** Internal.

**Key differentiating features:**

- Centralized AI integration across all GitLab deployment modes.
- Policy enforcement and data encryption.
- Unified access for all GitLab Duo AI features.

**Unique features:**

- **Bundled with GitLab** — not a standalone product. Relevant for GitLab shops adopting Duo.

---

#### 19. Tyk AI Gateway

**What it is:** Open-source API gateway (Tyk) extended with AI-assisted API design and LLM routing features.

**Deployment model:** Open-source (self-hosted) + commercial cloud.

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- AI-powered API design and automated generation.
- LLM routing integrated into traditional API management.
- Extensive plugin ecosystem.

**Unique features:**

- **AI-assisted API development** — uses LLMs to help design APIs, not just route to them.

**Pricing:** Open-source free; commercial from $450/month.

---

#### 20. Gloo Gateway (Solo.io)

**What it is:** Kubernetes-native API gateway (Envoy-based) with AI extension for LLM traffic. Enterprise product from Solo.io, same team as AgentGateway.

**Deployment model:** Self-hosted (Kubernetes, open-source + enterprise).

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- Function-level routing.
- Kubernetes-native with hybrid app support.
- Enterprise support with SLAs.
- Integration with Istio service mesh.

---

#### 21. Portkey (portkey.ai)

**What it is:** Enterprise AI gateway with integrated guardrails. 1,600+ LLMs supported. Open-source gateway core + managed SaaS.

**Deployment model:** Open-source self-hosted + managed SaaS (freemium). Free tier: 10k logs/month.

**OpenAI-compatible API:** Yes.

**Key differentiating features:**

- **60+ built-in guardrails** — PII redaction, prompt injection detection, jailbreak detection, JSON validation, RegEx patterns, content filters.
- **Virtual keys** — generate virtual keys per team/project with spend limits and access control.
- **Configs** — declarative routing rules: fallbacks, canary deployments, circuit breakers, cost/latency routing.
- Semantic caching (both exact and similarity-based).
- Prompt management with versioning and templates.
- 1,600+ LLMs.

**Unique features:**

- **60+ guardrails open-sourced on the gateway framework** — broadest guardrail coverage in open-source.
- **Virtual key system** — hierarchical key management with per-key budgets is more sophisticated than most competitors.
- **Config-driven routing** — declarative YAML/JSON configs for routing logic without code changes.

**Pricing:** Free (10k logs/month); paid tiers.

---

## Feature Comparison Matrix

| Product          | OpenAI Compat | Deployment         | Multi-Provider     | Semantic Cache  | Guardrails     | ML Routing            | Prompt Mgmt     | MCP/A2A           | Observability       | Budget Mgmt      | Self-Host |
| ---------------- | ------------- | ------------------ | ------------------ | --------------- | -------------- | --------------------- | --------------- | ----------------- | ------------------- | ---------------- | --------- |
| **Bifrost**      | Yes           | Cloud/Edge/On-prem | 1000+ models       | Yes (embedding) | Yes            | No                    | No              | MCP tools         | OTel+Prometheus     | Hierarchical     | Yes       |
| **LiteLLM**      | Yes           | Self-hosted        | 100+ providers     | No              | Basic          | No                    | No              | No                | Multi-platform      | Per-key/team     | Yes       |
| **Portkey**      | Yes           | Both               | 1600+ LLMs         | Yes (semantic)  | 60+            | No                    | Yes             | No                | Yes                 | Virtual keys     | Yes (OSS) |
| **Helicone**     | Yes           | Both               | Major              | Edge cache      | Basic          | No                    | Yes (versioned) | No                | Deep traces         | No               | Yes       |
| **Cloudflare**   | Yes           | SaaS only          | 350+ / 6 providers | Yes             | Basic          | No                    | No              | No                | Real-time analytics | Rate limiting    | No        |
| **Kong**         | Yes           | Both               | Multi-provider     | Semantic        | Plugin-based   | No                    | Plugin          | MCP (via plugin)  | Extensive           | Plugin           | Yes       |
| **Vercel**       | Yes           | SaaS only          | Hundreds           | Yes             | Basic          | No                    | No              | No                | Per-model analytics | No               | No        |
| **OpenRouter**   | Yes           | SaaS only          | 300+ models        | No              | No             | Basic                 | No              | No                | Basic               | No               | No        |
| **Not Diamond**  | Yes           | Both               | Any                | No              | No             | Yes (ML meta-model)   | Auto-rewrite    | No                | No                  | No               | VPC only  |
| **Martian**      | Yes           | SaaS+VPC           | Configurable       | No              | Compliance     | Yes (model mapping)   | No              | No                | No                  | No               | VPC only  |
| **Unify**        | Yes           | SaaS only          | Provider-level     | No              | No             | Yes (live benchmarks) | No              | No                | No                  | No               | No        |
| **Requesty**     | Yes           | SaaS only          | 500+ models        | Yes             | PII+injection  | Latency-based         | No              | No                | 40+ metrics         | Budget caps      | No        |
| **Braintrust**   | Yes           | Both (OSS)         | 100+ models        | Yes             | No             | No                    | No              | No                | Eval-native         | No               | Yes       |
| **Langfuse**     | Via LiteLLM   | Both               | Via LiteLLM        | No              | No             | No                    | Yes (versioned) | No                | OTel-native         | No               | Yes       |
| **Azure APIM**   | Yes           | Azure cloud        | Azure AI + more    | Semantic        | Content Safety | No                    | No              | MCP servers       | Azure Monitor       | TPM limits       | Hybrid    |
| **AWS Bedrock**  | Yes           | AWS cloud          | AWS models         | Prompt cache    | Basic          | No                    | No              | AgentCore MCP     | CloudWatch          | IAM-based        | VPC       |
| **Vertex AI**    | Yes           | GCP cloud          | Google models      | No              | Safety filters | No                    | No              | No                | Cloud Monitoring    | Quotas           | No        |
| **Fireworks**    | Yes           | SaaS+BYOC          | Fireworks models   | No              | No             | No                    | No              | No                | Basic               | No               | BYOC      |
| **Envoy AI GW**  | Yes           | K8s self-hosted    | Any provider       | No              | No             | No                    | No              | MCP (first-class) | OTel+OI             | Token rate limit | Yes       |
| **TrueFoundry**  | Yes           | Both               | 1000+ LLMs         | No              | Yes            | No                    | No              | MCP Gateway       | Yes                 | Budget           | Yes       |
| **AgentGateway** | No (MCP/A2A)  | Self-hosted        | N/A                | No              | No             | No                    | No              | MCP+A2A           | OTel                | No               | Yes       |
| **Operant AI**   | No (MCP)      | SaaS               | N/A                | No              | Security-focus | No                    | No              | MCP security      | Traffic graphs      | No               | No        |
| **ZenMux**       | Yes           | SaaS               | 200+ LLMs          | No              | No             | Task classify         | No              | No                | HLE benchmarks      | No               | No        |

---

## Table Stakes (Everyone Has These)

These features appear in 3+ products and are now minimum requirements for any competitive AI gateway:

1. **OpenAI-compatible API** — drop-in replacement for the OpenAI SDK. Non-negotiable.
2. **Multi-provider routing** — support for at least OpenAI, Anthropic, Google, AWS.
3. **Automatic failover** — when a provider fails, route to backup automatically.
4. **Request/response logging** — capture all traffic for debugging and audit.
5. **Cost tracking** — per-request token cost attribution.
6. **Rate limiting** — by API key, user, or team.
7. **Load balancing** — distribute across multiple provider endpoints.
8. **Basic caching** — exact-match caching to reduce redundant calls.
9. **SSL/TLS termination** and basic auth.
10. **Health checks** — detect and remove unhealthy backends.

---

## Differentiating Features (1-2 Products)

Features that only 1-2 products have, representing competitive advantages:

| Feature                                                 | Who Has It                | Description                                                                      |
| ------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------- |
| **ML meta-model routing**                               | Not Diamond, Martian      | Learned routing (not rules/benchmarks). Routes per-query based on trained model. |
| **Automatic prompt rewriting per model**                | Not Diamond               | Auto-adapts prompts for different model families.                                |
| **Mechanistic interpretability routing**                | Martian                   | Uses model internals (not just outputs) to predict quality.                      |
| **Provider-level routing (same model, different host)** | Unify                     | Routes Llama 3.1 to cheapest/fastest provider in real-time.                      |
| **Live 10-min benchmark updates as routing signal**     | Unify                     | Continuous benchmark refresh vs static leaderboards.                             |
| **LLM Insurance / automatic compensation**              | ZenMux                    | Credits for hallucinations, latency breaches, quality drops.                     |
| **Async observability (no hot path)**                   | Helicone                  | Ingest traces without being in the proxy path at all.                            |
| **Unified reasoning API abstraction**                   | Braintrust                | Normalizes o1/Claude-thinking/Gemini-thinking into one API.                      |
| **Eval-integrated gateway**                             | Braintrust                | Asynchronous online eval of production traffic, zero latency.                    |
| **OTel-native (not OTel adapter)**                      | Langfuse                  | Built on OTel client, not a wrapper.                                             |
| **A2A + MCP dual protocol**                             | AgentGateway              | Both Google A2A and Anthropic MCP protocols.                                     |
| **REST-to-MCP bridge**                                  | AgentGateway              | Auto-converts REST APIs to MCP tools.                                            |
| **Federated MCP tool registry**                         | AgentGateway, TrueFoundry | Centralized tool discovery for agents.                                           |
| **MCP security (Shadow Escape detection)**              | Operant AI                | Zero-click exploit detection for MCP traffic.                                    |
| **Grounding with live search**                          | Vertex AI                 | Native Google Search integration into completions.                               |
| **BYOC inference (customer's GPUs)**                    | Fireworks AI              | Inference engine runs on customer's VPC hardware.                                |
| **Agent workflow optimization**                         | Not Diamond               | Optimizes multi-step agent plans, not just single calls.                         |
| **Kubernetes Gateway API Inference Extension**          | Envoy AI Gateway          | Spec-stable intelligent endpoint selection for K8s.                              |
| **WebSocket Realtime API with token tracking**          | Azure APIM                | Streaming/realtime token metering for GPT-4o Realtime.                           |
| **Native Managed Identity auth**                        | Azure APIM                | No API keys; Azure MSI for auth.                                                 |
| **Prompt compliance routing**                           | Martian                   | Routes based on regulatory/compliance model properties.                          |
| **HLE community benchmarks**                            | ZenMux                    | Human Last Exam tests, community-auditable.                                      |
| **Unified LLM + MCP gateway**                           | TrueFoundry               | Both LLM and agent-tool routing in one control plane.                            |
| **Model fine-tuning + gateway**                         | TrueFoundry, Fireworks    | Train and serve custom models through the same platform.                         |

---

## Patterns by Category

### Multi-provider unification

All gateways solve this. Table stakes. Differentiation is now at: (a) how many providers, (b) provider-instance routing (Unify), (c) routing intelligence (Not Diamond, Martian).

### Caching

Exact-match caching: table stakes. Semantic caching (embedding-based): Bifrost, Portkey, Azure APIM, Cloudflare. Prompt caching (provider-level): AWS Bedrock (Claude/Nova). Edge caching: Helicone (Cloudflare Workers), Cloudflare AI Gateway. Eval-cached results: Braintrust.

### Guardrails / Security

PII redaction: Portkey, Requesty, Helicone (basic), Azure APIM (Content Safety). Prompt injection detection: Portkey, Requesty, Operant AI (MCP-specific), Azure APIM. Jailbreak detection: Portkey, Operant AI. Output validation: Portkey (JSON, RegEx). MCP-specific security: Operant AI (market leader), AgentGateway (RBAC).

### Observability

Basic metrics: all products. Deep traces/sessions: Helicone, Langfuse, Braintrust. OTel-native: Langfuse, Envoy, AgentGateway. Eval integration: Braintrust (market leader). Real-time analytics dashboards: Requesty, Cloudflare, Azure APIM.

### Cost governance

Per-key budgets: LiteLLM, Portkey (virtual keys), Bifrost, Requesty. Team/project budgets: LiteLLM, TrueFoundry, Azure APIM (TPM quotas). Cost routing: Requesty, Portkey, Bifrost. Tag-based attribution: LiteLLM. Chargeback: TrueFoundry, Azure APIM.

### Agent / MCP support (2026 hot topic)

LLM-to-MCP routing: Bifrost (MCP tool filtering), Kong (via plugin), Envoy AI Gateway (first-class), TrueFoundry (MCP Gateway). Agent-to-tool gateway: AgentGateway, Operant AI, AWS AgentCore, Azure APIM, TrueFoundry. A2A protocol: AgentGateway (only open-source).

---

## Emerging Trends in 2026

### 1. MCP as the dominant agent protocol

The Model Context Protocol is winning the agent-to-tool connectivity race. By early 2026, nearly every gateway has MCP support or is adding it. The Linux Foundation has accepted MCP under open governance. Gateway vendors are racing to add MCP routing, security, and management.

### 2. A2A (Agent-to-Agent) protocol

Google's Agent-to-Agent protocol is emerging alongside MCP for agent orchestration. AgentGateway is the first open-source implementation. Expect more gateways to add A2A in 2026.

### 3. Agentic routing (multi-step, not single-call)

Routing is moving from single-call optimization to multi-step agent workflow optimization. Not Diamond's "agent optimization" feature and TrueFoundry's MCP Gateway both address this. The challenge: optimizing routing across an entire agent session, not just a single LLM call.

### 4. ML-based routing outperforms rule-based

Not Diamond and Martian both claim to outperform fixed-model usage via ML routing. Industry consensus is forming: ML routing trained on production data outperforms static benchmark-based routing for most enterprise tasks.

### 5. Multimodal gateway support

Vision/image/audio inputs are becoming table stakes. Gateways need to handle routing across text-only and multimodal models transparently.

### 6. Security specialization

Dedicated AI security gateways (Operant AI, Sentinel) are emerging alongside general-purpose gateways. Attack vectors specific to AI (prompt injection, tool poisoning, Shadow Escape) require dedicated detection that general gateways haven't prioritized.

### 7. Hyperscaler gateway offerings

AWS (AgentCore), Azure (APIM AI), and Google (Vertex) all have strong native gateway stories. For enterprise customers already on one cloud, the hyperscaler gateway is increasingly compelling because it eliminates egress, uses native auth (IAM/MSI), and integrates with existing monitoring. This is table stakes pressure on independent gateways.

### 8. Performance arms race

Rust and Go implementations (Bifrost ~11µs, Requesty ~8ms P50, Helicone <1ms compute overhead) are pushing Python-based gateways (LiteLLM) out of high-performance scenarios. Performance is increasingly measured in microseconds, not milliseconds.

### 9. Gateway-as-eval-platform

The line between gateway and eval platform is blurring. Braintrust scores production traffic through the gateway asynchronously. Bifrost integrates with Maxim's eval/simulation platform. Expect eval-native routing (routing based on online eval scores) to emerge as a capability.

### 10. Unified LLM + tool gateway

The next frontier: one gateway for both LLM routing (model traffic) and tool routing (agent-to-tool MCP traffic). TrueFoundry is first. AWS AgentCore + Bedrock Gateway is second. This will likely be standard by late 2026.

---

## Features thegent Should Prioritize

### Must-have (table stakes — without these, thegent is not competitive):

1. OpenAI-compatible API (drop-in replacement)
2. Multi-provider support (OpenAI, Anthropic, Google, AWS Bedrock, Azure, Groq, Mistral minimum)
3. Automatic failover with configurable fallback chains
4. Request/response logging with cost and latency tracking
5. Rate limiting (per API key, per user, per team)
6. Exact-match caching
7. Load balancing across provider endpoints
8. Health check and circuit breaker for provider backends
9. Per-key budget enforcement

### High-value differentiators to implement:

1. **Semantic caching** — embedding-based; reduces costs up to 95% for similar queries.
2. **ML routing intelligence** — either integrate Not Diamond/Martian as a routing backend, or build lightweight task-classification-based routing.
3. **MCP gateway** — agent-to-tool routing is the growth direction for 2026. First-class MCP support (not just LLM routing).
4. **Guardrails: PII redaction + prompt injection detection** — Portkey has 60+; even basic coverage is a significant differentiator vs no guardrails.
5. **Virtual keys / hierarchical key management** — per-project, per-team virtual keys with spend limits. Portkey's model is the benchmark.
6. **Prompt management** — versioned prompt templates with variable substitution and A/B testing. Prevents prompt drift.
7. **Deep observability** — session/trace tracking for multi-step agent flows (not just per-request metrics).
8. **Online eval integration** — asynchronous scoring of production traffic (Braintrust model).
9. **Provider-level routing** — route the same model to cheapest/fastest provider in real time (Unify model).
10. **Budget management with chargebacks** — tag-based cost attribution by team/project/user for internal billing.

### Moonshot/long-term:

1. **A2A + MCP dual protocol gateway** — position thegent as the unified agentic gateway.
2. **LLM Insurance model** — novel, defensible moat if thegent has quality monitoring.
3. **Live benchmark routing signal** — continuous benchmark updates driving routing decisions.
4. **Unified reasoning API** — normalize reasoning parameters across providers (Braintrust model).

---

## Sources Consulted

- [Top 5 LLM Gateways for 2026 — Maxim AI](https://www.getmaxim.ai/articles/top-5-llm-gateways-for-2026-a-comprehensive-comparison/)
- [Top 5 AI Gateways for 2026 — Maxim AI](https://www.getmaxim.ai/articles/top-5-ai-gateways-for-2026/)
- [Top 5 AI Gateways for Cost Optimization 2026 — Maxim AI](https://www.getmaxim.ai/articles/top-5-ai-gateways-for-optimizing-llm-cost-in-2026/)
- [Helicone Homepage](https://www.helicone.ai/)
- [Helicone GitHub](https://github.com/Helicone/helicone)
- [Not Diamond Homepage](https://www.notdiamond.ai/)
- [Not Diamond Docs — What is Model Routing](https://docs.notdiamond.ai/docs/what-is-model-routing)
- [Martian — VentureBeat](https://venturebeat.com/ai/why-accenture-and-martian-see-model-routing-as-key-to-enterprise-ai-success/)
- [Martian $9M Raise](https://www.hpcwire.com/bigdatawire/this-just-in/martian-raises-9m-for-advanced-model-mapping-to-enhance-llm-performance-and-accuracy/)
- [Unify AI](https://xnavi.ai/tools/unify)
- [Requesty — DataCamp Tutorial](https://www.datacamp.com/tutorial/requesty-tutorial)
- [Requesty Homepage](https://www.requesty.ai/)
- [Braintrust AI Proxy](https://www.braintrust.dev/blog/ai-proxy)
- [Langfuse](https://langfuse.com/)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [Azure APIM AI Gateway](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)
- [Azure APIM AI Gateway Enhancements](https://techcommunity.microsoft.com/blog/integrationsonazureblog/ai-gateway-enhancements-llm-policies-real-time-api-support-content-safety-and-mo/4409828)
- [AWS Bedrock Access Gateway](https://github.com/aws-samples/bedrock-access-gateway)
- [AWS AgentCore Gateway](https://aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-gateway-transforming-enterprise-ai-agent-tool-development/)
- [Fireworks AI](https://docs.fireworks.ai/getting-started/introduction)
- [ZenMux](https://www.nxcode.io/resources/news/zenmux-complete-guide-ai-api-gateway-2026)
- [Envoy AI Gateway](https://aigateway.envoyproxy.io/)
- [Envoy AI Gateway GitHub](https://github.com/envoyproxy/ai-gateway)
- [TrueFoundry AI Gateway](https://www.truefoundry.com/ai-gateway)
- [TrueFoundry MCP Gateway Blog](https://www.truefoundry.com/blog/truefoundry-mcp-gateway-critical-infrastructure-for-productive-and-secure-enterprise-ai-in-2026)
- [AgentGateway](https://agentgateway.dev/)
- [AgentGateway GitHub](https://github.com/agentgateway/agentgateway)
- [Operant AI MCP Gateway](https://www.operant.ai/solutions/mcp-gateway)
- [Portkey AI Gateway GitHub](https://github.com/Portkey-AI/gateway)
- [Portkey Features](https://portkey.ai/features/ai-gateway)
- [Portkey Guardrails](https://portkey.ai/features/guardrails)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Bifrost — Maxim AI](https://www.getmaxim.ai/blog/bifrost-a-drop-in-llm-proxy-40x-faster-than-litellm/)
- [Kong AI Gateway 3.8](https://konghq.com/blog/product-releases/ai-gateway-3-8)
- [13 LLM Gateways List — DrDroid](https://drdroid.io/engineering-tools/list-of-top-13-llm-gateways)
- [MCP Gateways 2026 Guide — Integrate.io](https://www.integrate.io/blog/best-mcp-gateways-and-ai-agent-security-tools/)
- [5 Key Agentic Trends 2026 — The New Stack](https://thenewstack.io/5-key-trends-shaping-agentic-development-in-2026/)
- [IBM + Not Diamond](https://www.ibm.com/think/insights/why-ibm-ventures-invested-in-not-diamond)
- [Agentic AI Trends 2026](https://machinelearningmastery.com/7-agentic-ai-trends-to-watch-in-2026/)
