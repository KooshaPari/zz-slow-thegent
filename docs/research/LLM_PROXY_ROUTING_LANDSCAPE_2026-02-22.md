<DONE>
# Open-Source LLM Proxy & Routing Landscape (2026)

**Date:** 2026-02-22
**Status:** Research Summary
**Context:** Competitive analysis for CLIProxyAPI-plusplus and thegent routing layer
**Research Period:** Feb 2026

---

## Executive Summary

The LLM proxy/routing market has exploded with specialized implementations. CLIProxyAPI-plusplus (Go-based, OpenAI-compatible, 30+ format translations) and thegent's routing layer (Pareto frontier algorithm, Python/Rust FFI) occupy a specific niche: **high-performance self-hosted proxy with intelligent routing**.

Key finding: **Performance and embedding feasibility are the primary differentiators.** Bifrost (Go, 11µs overhead) and LiteLLM (Python, widely embedded) dominate different niches. For CLIProxyAPI++, the key competitive advantages are:

1. CLI-tool-first design (Cursor, Kiro, Codex, Claude Code)
2. OAuth lifecycle management (15+ providers)
3. Multi-protocol translation (Responses API v2 ↔ Chat Completions ↔ WebSocket)
4. Embeddability as a library (thin wrapper over LiteLLM + custom routing)

---

## Competitive Matrix

| Project                      | Type        | Language          | Overlap % | Superior At                                               | Inferior At                                   | Embeddable?        | License                | Latest          |
| ---------------------------- | ----------- | ----------------- | --------- | --------------------------------------------------------- | --------------------------------------------- | ------------------ | ---------------------- | --------------- |
| **LiteLLM**                  | Proxy       | Python            | 85%       | 100+ providers, cost tracking, fallbacks, streaming       | Performance (>10ms latency), semantic caching | YES (library)      | MIT                    | Feb 2026        |
| **Bifrost**                  | Proxy       | Go                | 70%       | Performance (11µs), semantic caching, MCP, OTel           | Guardrails, prompt mgmt                       | PARTIAL (API only) | Proprietary            | 2026            |
| **Portkey**                  | Gateway     | Go (+ Python SDK) | 75%       | 60+ guardrails, semantic cache, virtual keys              | Performance, self-host simplicity             | YES (SDK)          | Proprietary (OSS core) | 2026            |
| **Kong AI Gateway**          | API Gateway | Go                | 60%       | Enterprise API mgmt, semantic routing, plugins            | CLI-specific features, cost focus             | PARTIAL (plugins)  | Proprietary            | 2026            |
| **Envoy AI Gateway**         | Proxy       | Go                | 55%       | MCP routing, K8s native, OTel-first, Gateway API          | Provider coverage, cost optimization          | NO (standalone)    | Apache 2.0             | v0.1 (Feb 2025) |
| **OpenRouter**               | SaaS Proxy  | Proprietary       | 65%       | 300+ models, community, pay-per-use                       | Self-hosted, cost transparency                | NO (SaaS only)     | Proprietary            | 2026            |
| **one-api**                  | Proxy       | Go                | 72%       | Simple, single binary, Chinese provider support           | English docs, routing sophistication          | PARTIAL (binary)   | MIT                    | 2025            |
| **RouteLLM**                 | Router Only | Python            | 40%       | ML-learned routing, cost-effective, open-source           | No gateway features, no OAuth                 | YES (library)      | MIT                    | 2024            |
| **Martian**                  | Router Only | Proprietary       | 35%       | ML mechanistic interpretability, compliance routing       | Closed source, SaaS-only, cost model unclear  | NO                 | Proprietary            | 2025            |
| **Not Diamond**              | Router Only | Proprietary       | 30%       | ML meta-model routing, prompt rewriting, agents           | Closed source, VPC only, expensive            | NO                 | Proprietary            | 2025            |
| **Unify**                    | Router Only | SaaS              | 25%       | Live benchmark routing (10-min refresh), provider routing | SaaS-only, no self-host                       | NO                 | Proprietary            | 2026            |
| **Apache APISIX AI Gateway** | Proxy       | Go                | 45%       | Token rate limiting, AI RAG plugins, content mod          | Provider coverage, semantic caching           | PARTIAL (plugins)  | Apache 2.0             | 2026            |
| **LM-Proxy**                 | Proxy       | Python (FastAPI)  | 70%       | Lightweight, async, extensible                            | Performance, provider count                   | YES (library)      | MIT                    | 2025            |
| **LLM-API-Key-Proxy**        | Proxy       | Python            | 68%       | Simple setup, token-level control                         | Performance, observability                    | PARTIAL (binary)   | MIT                    | 2025            |

---

## Detailed Analysis

### Tier 1: High-Performance Self-Hosted Proxies

#### **Bifrost** (Maxim AI)

- **What it does:** Go-based gateway with 11µs overhead @ 5k RPS; semantic caching (60-85% cost reduction); native MCP support; OTel observability; 12+ providers
- **Superior to CLIProxyAPI++:** Performance (Go native), semantic caching (embedding-based similarity), MCP-first, observability (OTel+Prometheus)
- **Inferior to CLIProxyAPI++:** Closed-source (no embedding as library), no OAuth flow management, limited to proprietary deployment, less granular provider translation
- **Embed?** API-only (no library). Can call HTTP endpoints but not use as a Rust/Go crate
- **License:** Proprietary (free tier available)
- **When to use instead:** If semantic caching cost reduction (60-85%) is a priority; if MCP agent tool routing is critical; if you need <1ms proxy overhead at scale

#### **LiteLLM**

- **What it does:** Python SDK + proxy server; 100+ providers; cost tracking; fallback routing; load balancing (least-busy, latency, usage-based); MIT open-source
- **Superior to CLIProxyAPI++:** Provider breadth (100+ vs thegent's 30+), cost tracking built-in, fallback routing native, large active community, caching (Redis/in-memory/S3)
- **Inferior to CLIProxyAPI++:** Performance (Python, 10-50ms latency vs 11µs), no OAuth lifecycle mgmt, no multi-protocol translation (Responses API v2, WebSocket), no semantic caching
- **Embed?** YES. Import as Python library; use `litellm.Router()` or `litellm.completion()` directly. Thin wrapper model
- **License:** MIT (fully open-source)
- **When to use instead:** If provider breadth is critical; if you're in Python already; if you need cost aggregation and fallback routing out-of-box; if community support matters

---

### Tier 2: Specialized Feature Leaders

#### **Portkey AI Gateway**

- **What it does:** Go-based gateway + Python SDK; 60+ guardrails (PII redaction, prompt injection, jailbreak); virtual keys with per-project budgets; semantic caching; 200+ LLM models
- **Superior to CLIProxyAPI++:** Guardrails (50+ edge cases covered), virtual key management (multi-tenant budgets), semantic caching, prompt versioning
- **Inferior to CLIProxyAPI++:** Requires Portkey managed service for full features (OSS core limited), no OAuth mgmt, no CLI-tool-specific protocols, closed guardrail logic
- **Embed?** PARTIAL. OSS core available, but guardrails & semantic cache are proprietary. Can use Portkey SDK but not as a full library
- **License:** Proprietary (free OSS core available)
- **When to use instead:** If guardrails (PII, injection detection) are table-stakes; if multi-tenant budget isolation is required; if you want prompt management built-in

#### **Kong AI Gateway**

- **What it does:** Extends Kong (traditional API gateway) with LLM plugins; semantic routing (similarity-based load balancing); token-based rate limiting; 60+ AI features
- **Superior to CLIProxyAPI++:** Enterprise API mgmt integration, semantic routing, token-level controls, existing Kong ecosystem
- **Inferior to CLIProxyAPI++:** Heavy (designed for enterprises with Kong), no OAuth mgmt, less CLI-focused, plugin-heavy (not library-first)
- **Embed?** PARTIAL. Designed as plugin ecosystem, not as a library. Can extend Kong but requires Kong infrastructure
- **License:** Proprietary + open-source components
- **When to use instead:** If you already use Kong for API management; if semantic load balancing across model families is needed; if enterprise plugin ecosystem matters

#### **Envoy AI Gateway**

- **What it does:** CNCF-backed, Kubernetes-native; MCP routing via MCPRoute CRD; Gateway API Inference Extension; OTel-native; streaming HTTP + JSON-RPC support
- **Superior to CLIProxyAPI++:** MCP-first (native tool routing), K8s-native, OTel observability, CNCF backing, Gateway API standard
- **Inferior to CLIProxyAPI++:** New (v0.1, Feb 2025), limited provider count, no semantic caching, no cost tracking, no OAuth, less mature
- **Embed?** NO. Standalone deployment model. No library version
- **License:** Apache 2.0 (fully open-source, CNCF)
- **When to use instead:** If MCP agent tool routing is primary use case; if Kubernetes-native is required; if OTel integration is critical; if standards-based (Gateway API) is priority

---

### Tier 3: Open-Source Lightweight Proxies

#### **one-api** (songquanpeng)

- **What it does:** Single Go binary; OpenAI-compatible; supports Chinese LLM providers (GLM, Qwen, Kimi, MiniMax); API key redistribution
- **Superior to CLIProxyAPI++:** Supports Chinese LLM ecosystem; simple single-binary deployment; straightforward key management
- **Inferior to CLIProxyAPI++:** Minimal routing logic, no semantic caching, no OAuth, limited English documentation, less sophisticated provider translation
- **Embed?** PARTIAL. Single binary, not designed as a library
- **License:** MIT
- **When to use instead:** If Chinese LLM providers (GLM, Qwen) are primary use case; if simplicity of deployment is priority; if single-binary distribution is preferred

#### **LM-Proxy** (Nayjest)

- **What it does:** Python/FastAPI lightweight proxy; OpenAI-compatible; supports Google, Anthropic, OpenAI, PyTorch; async-first; extensible
- **Superior to CLIProxyAPI++:** Lightweight, async, extensible architecture, good for custom extensions
- **Inferior to CLIProxyAPI++:** Limited provider count, minimal routing, no cost tracking, no OAuth, no semantic caching, small community
- **Embed?** YES. FastAPI-based, can be imported as library or run standalone
- **License:** MIT
- **When to use instead:** If you're extending a lightweight framework; if async-first is required; if you need a minimal base and will customize heavily

#### **LLM-API-Key-Proxy** (Mirrowel)

- **What it does:** Python proxy; OpenAI/Anthropic-compatible endpoints; multi-provider translation; intelligent load-balancing; token controls
- **Superior to CLIProxyAPI++:** Simple setup, token-level controls, straightforward multi-provider translation
- **Inferior to CLIProxyAPI++:** Performance (Python), no semantic caching, limited routing sophistication, no OAuth, small project
- **Embed?** PARTIAL. Designed as standalone binary
- **License:** MIT
- **When to use instead:** If you need a minimal Python proxy you can fork and customize; if token-level controls are important

---

### Tier 4: Routing Intelligence Only (No Gateway)

#### **RouteLLM** (LMSYS)

- **What it does:** ML-learned router; trained on preference data; selects model based on predicted quality; 40% cheaper than Martian/Unify
- **Superior to CLIProxyAPI++:** ML-based routing (no hand-crafted rules), academic rigor (LMSYS), open-source, cost-effective
- **Inferior to CLIProxyAPI++:** Router only (no gateway), no provider mgmt, no OAuth, no caching, no observability, no CLI tool support
- **Embed?** YES. Python library. Can integrate with any proxy (LiteLLM, Bifrost, etc.)
- **License:** MIT
- **When to use instead:** If you want to integrate intelligent routing into thegent's Pareto router; if academic validation matters; if cost is primary optimization target

#### **Martian** (with Accenture)

- **What it does:** Mechanistic interpretability-based router; model mapping (internal activation patterns); compliance-aware routing
- **Superior to CLIProxyAPI++:** Mechanistic interpretability (novel), compliance routing (unique)
- **Inferior to CLIProxyAPI++:** Closed-source, SaaS-only (VPC option), expensive, no self-hosted option, no gateway features
- **Embed?** NO. SaaS only
- **License:** Proprietary
- **When to use instead:** If mechanistic interpretability routing is differentiator (very niche); if compliance-based routing (HIPAA, SOC2) is required; if budget allows SaaS

#### **Not Diamond**

- **What it does:** ML meta-model routing; auto prompt rewriting per model family; agent workflow optimization
- **Superior to CLIProxyAPI++:** ML meta-model (proprietary), prompt rewriting (unique), agent-workflow aware (thegent opportunity)
- **Inferior to CLIProxyAPI++:** Closed-source, VPC/SaaS only, expensive, no self-hosted, no gateway features
- **Embed?** NO. SaaS only
- **License:** Proprietary
- **When to use instead:** If agent workflow optimization is priority; if prompt rewriting across model families is needed; if budget allows enterprise SaaS

#### **Unify**

- **What it does:** Provider-level routing (same model, cheapest host); live benchmark routing (10-min refresh); quality/cost/latency sliders
- **Superior to CLIProxyAPI++:** Live benchmarks (real-time), provider-level optimization (unique), quality vs cost tradeoffs exposed
- **Inferior to CLIProxyAPI++:** SaaS-only, no self-hosted, no gateway features, no OAuth
- **Embed?** NO. SaaS only
- **License:** Proprietary
- **When to use instead:** If provider-level shopping (same model across OpenAI/Azure/Bedrock) is key use case; if live benchmarks matter

---

## Feature Comparison Table (vs CLIProxyAPI++)

| Feature                               | CLIProxyAPI++           | LiteLLM            | Bifrost            | Portkey           | Kong              | Envoy      | one-api            | RouteLLM         |
| ------------------------------------- | ----------------------- | ------------------ | ------------------ | ----------------- | ----------------- | ---------- | ------------------ | ---------------- |
| **OpenAI-compatible API**             | Yes                     | Yes                | Yes                | Yes               | Yes               | Yes        | Yes                | No (router only) |
| **Multi-provider (30+)**              | Yes (15-30)             | Yes (100+)         | Yes (12+)          | Yes (200+)        | Yes (12+)         | Yes (10+)  | Yes (20+, Chinese) | N/A              |
| **OAuth flow management**             | Yes (15+ providers)     | No                 | No                 | No                | No                | No         | No                 | N/A              |
| **Responses API v2 translation**      | Yes (Codex/Claude Code) | No                 | No                 | No                | No                | No         | No                 | N/A              |
| **WebSocket streaming**               | Yes                     | Partial (HTTP SSE) | No                 | No                | No                | Yes        | No                 | N/A              |
| **Semantic caching**                  | No                      | No (Redis/in-mem)  | Yes                | Yes               | No (plugin)       | No         | No                 | N/A              |
| **Cost tracking**                     | Basic                   | Yes (per-request)  | Yes                | Yes               | Yes (token-based) | No         | No                 | N/A              |
| **Guardrails (PII, injection, etc.)** | No                      | Limited            | Limited            | Yes (60+)         | Partial (plugins) | Limited    | No                 | N/A              |
| **Load balancing strategies**         | Round-robin, fallback   | 4+ strategies      | Adaptive           | Multiple          | Semantic          | Weighted   | Basic              | N/A              |
| **Virtual keys / budgets**            | No                      | Yes (per-key)      | Yes (hierarchical) | Yes (per-project) | Partial           | No         | Yes                | N/A              |
| **Fallback routing**                  | Yes                     | Yes                | Yes                | Yes               | Partial           | Yes        | Yes                | N/A              |
| **Health checks / circuit breaker**   | Basic                   | Yes                | Yes                | Yes               | Yes               | Yes        | Basic              | N/A              |
| **Performance (latency)**             | <5ms (Go)               | 10-50ms (Python)   | 11µs (5k RPS)      | <50ms             | Varies            | Varies     | <10ms              | N/A (router)     |
| **Embeddable as library?**            | YES                     | YES                | API-only           | SDK               | Plugin            | NO         | NO                 | YES              |
| **Self-hostable?**                    | Yes                     | Yes                | Yes                | Partial           | Yes               | Yes        | Yes                | N/A              |
| **Open-source?**                      | TBD                     | MIT                | No                 | Partial           | Partial           | Apache 2.0 | MIT                | MIT              |

---

## Embedding Feasibility Analysis

### Candidates for Library Integration with CLIProxyAPI++ / thegent

**HIGH (Can be embedded as library):**

1. **LiteLLM** (Python)
   - Current thegent integration: Already used!
   - How: `from litellm import Router, completion()`
   - Lines of wrapper needed: <100 LOC for custom routing layer
   - Cost: Free (MIT)
   - Effort: Already integrated; minimal additional work

2. **RouteLLM** (Python)
   - How: `from routellm import Router; router.forward(input)`
   - Lines of wrapper needed: ~50 LOC to bridge with LiteLLM
   - Cost: Free (MIT)
   - Effort: Low (integrate as routing decision layer on top of LiteLLM)

3. **LM-Proxy** (Python/FastAPI)
   - How: `from lm_proxy import LLMProxy`
   - Lines of wrapper needed: ~100 LOC
   - Cost: Free (MIT)
   - Effort: Medium (requires adapting to thegent's FastAPI stack)

**MEDIUM (API-based embedding, not library):**

4. **Bifrost** (Go)
   - How: HTTP calls to `localhost:8317`
   - Integration cost: Process management (start/stop/health)
   - Cost: Free (tier), paid (enterprise)
   - Effort: Medium (manage as subprocess, handle startup/shutdown)

5. **Portkey** (Go + SDK)
   - How: Python SDK + API calls
   - Integration cost: SDK install + API key management
   - Cost: Proprietary (free tier limited)
   - Effort: Medium (SDK integration, but proprietary features behind paywall)

**LOW (Not embeddable):**

6. **Kong AI Gateway** — Requires Kong infrastructure
7. **Envoy AI Gateway** — Kubernetes-native, standalone deployment
8. **OpenRouter** — SaaS only
9. **Martian, Not Diamond, Unify** — SaaS/VPC only

---

## Strategic Recommendations for CLIProxyAPI++ / thegent

### Option A: "Library-First, Keep Thin Wrapper" (RECOMMENDED)

**Action:** Deepen LiteLLM integration; add RouteLLM as routing layer

- Keep LiteLLM as the provider translation backbone (100+ providers, proven, MIT)
- Add RouteLLM router on top for ML-learned routing (cost optimization)
- Enhance with custom OAuth flows (Cursor, Kiro, Claude Code, Gemini, Copilot)
- Add Responses API v2 ↔ Chat Completions translation
- Implement semantic caching layer (could use Bifrost's algorithm or custom)

**Pros:**

- Leverages battle-tested LiteLLM (widely used, MIT licensed)
- Cost-effective (free OSS stack)
- Full control over routing logic (thegent Pareto + RouteLLM ML)
- Maximally embeddable (pure Python/Rust via FFI)
- Smallest surface area for security/maintenance

**Cons:**

- Doesn't reach Bifrost's 11µs overhead (stuck at Python speed, 10-50ms)
- No built-in semantic caching (must implement custom)
- Limited guardrails (must add PII/injection detection separately)

**Implementation Estimate:** 2-3 sprints

---

### Option B: "Performance-First, Rust/Go Gateway"

**Action:** Build CLIProxyAPI-plusplus as pure Rust/Go gateway (library-first over LiteLLM)

- Use Bifrost's codebase as reference (11µs overhead, semantic cache)
- Implement in Rust or Go (match thegent's polyglot strategy)
- Embed LiteLLM SDK for provider support (via FFI if Rust)
- Own OAuth flows, Responses API v2, WebSocket translation
- Add Pareto routing + RouteLLM integration

**Pros:**

- Reaches Bifrost-level performance (11µs vs 10-50ms)
- Full control over semantic caching
- Can build custom guardrails
- Embeddable as a Rust crate or Go library

**Cons:**

- Significant engineering effort (build from scratch, not library-first)
- Duplicates LiteLLM's provider work (against library-first philosophy)
- Maintenance burden (now own 100+ provider integrations)

**Implementation Estimate:** 6-8 sprints

**Verdict:** Only pursue if performance is a hard requirement (e.g., <1ms proxy overhead) and current Python stack is a bottleneck.

---

### Option C: "Bifrost as External Service, Thin Wrapper"

**Action:** Deploy Bifrost as standalone service; integrate CLIProxyAPI++ as HTTP client wrapper

- Run Bifrost (free tier or BYOC) as localhost service
- Add OAuth, Responses API v2, WebSocket translation in CLIProxyAPI++ wrapper
- Use Bifrost for provider routing, semantic caching, MCP
- Keep thegent's Pareto router as decision layer

**Pros:**

- Bifrost handles performance (11µs) and semantic caching (60-85% cost reduction)
- No duplication of provider logic
- Bifrost's MCP support is table-stakes for agents (2026)
- Can move to Bifrost enterprise when cost allows

**Cons:**

- Bifrost is proprietary (no source, can't fix bugs)
- Creates external dependency (Bifrost must stay healthy)
- Harder to customize routing logic inside Bifrost
- Cost increases with usage (SaaS)

**Implementation Estimate:** 1-2 sprints (integration only)

**Verdict:** Viable if you can accept proprietary dependency and want fast time-to-market with best-in-class features.

---

## Market Position Summary

### Where CLIProxyAPI++ Currently Sits

| Dimension                  | Position                             | Strength                     |
| -------------------------- | ------------------------------------ | ---------------------------- |
| **Performance**            | Mid-tier (5-10ms, Python)            | Adequate for CLI tools       |
| **Provider breadth**       | Mid-tier (15-30)                     | Covers major cloud + custom  |
| **Routing sophistication** | High (Pareto + cost)                 | Above-average                |
| **OAuth/token lifecycle**  | Unique (15+ providers)               | Only product with this focus |
| **CLI-tool compatibility** | Unique (Responses API v2, WebSocket) | Only product with this       |
| **Embeddability**          | High (thin wrapper over LiteLLM)     | Library-first                |
| **Guardrails**             | Low (not a focus)                    | Needs investment             |
| **Semantic caching**       | None                                 | Opportunity                  |

### Competitive Gaps to Address (Priority Order)

1. **Semantic caching** (60-85% cost reduction) — Implement custom layer or integrate Bifrost
2. **Guardrails** (PII, injection, jailbreak) — Add 10-20 rules; reference Portkey (60+)
3. **MCP routing** (agent tools) — Critical for 2026; Envoy AI Gateway does this natively
4. **Multi-tenant budget isolation** — Add virtual key support (like Portkey/Bifrost)
5. **Prompt management** — Versioning + A/B testing (Portkey does this)

---

## License & Attribution Summary

| Project               | License                | Commercial Use | Modification | Redistribution  | Notes                |
| --------------------- | ---------------------- | -------------- | ------------ | --------------- | -------------------- |
| **LiteLLM**           | MIT                    | ✓              | ✓            | ✓               | Fully permissive     |
| **RouteLLM**          | MIT                    | ✓              | ✓            | ✓               | Fully permissive     |
| **one-api**           | MIT                    | ✓              | ✓            | ✓               | Fully permissive     |
| **LM-Proxy**          | MIT                    | ✓              | ✓            | ✓               | Fully permissive     |
| **LLM-API-Key-Proxy** | MIT                    | ✓              | ✓            | ✓               | Fully permissive     |
| **Envoy AI Gateway**  | Apache 2.0             | ✓              | ✓            | ✓ (with notice) | CNCF-backed          |
| **Apache APISIX AI**  | Apache 2.0             | ✓              | ✓            | ✓ (with notice) | CNCF-backed          |
| **Bifrost**           | Proprietary            | ✓ (free tier)  | ✗            | ✗               | Closed-source        |
| **Portkey**           | Proprietary (OSS core) | ✓ (core only)  | Limited      | Limited         | Proprietary features |
| **Kong AI Gateway**   | Proprietary            | ✓              | Limited      | Limited         | Plugin-based         |
| **OpenRouter**        | SaaS                   | ✓              | ✗            | ✗               | Cloud-only           |
| **Martian**           | Proprietary            | ✓ (SaaS)       | ✗            | ✗               | Closed, VPC/SaaS     |
| **Not Diamond**       | Proprietary            | ✓ (SaaS)       | ✗            | ✗               | Closed, VPC/SaaS     |
| **Unify**             | Proprietary            | ✓ (SaaS)       | ✗            | ✗               | Cloud-only           |

---

## Sources & References

- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [LiteLLM Docs - Router & Load Balancing](https://docs.litellm.ai/docs/routing)
- [Bifrost AI Gateway GitHub](https://github.com/maximhq/bifrost)
- [Bifrost Docs](https://docs.getbifrost.ai/)
- [Portkey AI Gateway GitHub](https://github.com/Portkey-AI/gateway)
- [Portkey Features](https://portkey.ai/features/ai-gateway)
- [Kong AI Gateway Docs](https://developer.konghq.com/ai-gateway/)
- [Envoy AI Gateway GitHub](https://github.com/envoyproxy/ai-gateway)
- [Envoy AI Gateway Docs](https://aigateway.envoyproxy.io/)
- [one-api GitHub](https://github.com/songquanpeng/one-api)
- [RouteLLM LMSYS Blog](https://lmsys.org/blog/2024-07-01-routellm/)
- [RouteLLM GitHub](https://github.com/lmsys/RouteLLM)
- [LM-Proxy GitHub](https://github.com/Nayjest/lm-proxy)
- [LLM-API-Key-Proxy GitHub](https://github.com/Mirrowel/LLM-API-Key-Proxy)
- [Apache APISIX AI Gateway](https://apisix.apache.org/ai-gateway/)
- [Martian - Model Routing](https://withmartian.com/)
- [Not Diamond - ML Model Routing](https://www.notdiamond.ai/)
- [Unify - Provider Routing](https://unify.ai/)
- [LiteLLM vs OpenRouter Comparison (TrueFoundry)](https://www.truefoundry.com/blog/litellm-vs-openrouter)
- [Top 5 AI Gateways 2026 (Maxim)](https://www.getmaxim.ai/articles/top-5-ai-gateways-for-optimizing-llm-cost-in-2026)
- [Go vs Python AI Infrastructure Benchmarks 2026](https://dasroot.net/posts/2026/02/go-vs-python-ai-infrastructure-throughput-benchmarks-2026/)
- [Envoy AI Gateway MCP Integration (Jan 2026)](https://joshuaberkowitz.us/blog/news-1/envoy-ai-gateway-ushers-in-a-new-era-with-mcp-integration-1367)

---

## Next Steps for thegent Team

1. **Immediate (Sprint 1):** Audit thegent's current LiteLLM integration depth; identify gaps vs feature matrix above
2. **Short-term (Sprint 2-3):** Add semantic caching prototype (reference Bifrost algorithm or integrate custom)
3. **Medium-term (Sprint 4-6):** Integrate RouteLLM for ML-learned routing; benchmark against current Pareto router
4. **Strategic (Quarterly):** Evaluate Bifrost integration vs building native Go/Rust gateway; assess MCP routing priority for 2026

---

**Document compiled:** 2026-02-22
**Research cutoff:** 2026-02-22 (latest info from web search + local docs/context)
**Next review date:** 2026-05-22 (quarterly)
