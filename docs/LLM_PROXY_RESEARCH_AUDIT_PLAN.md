# LLM Proxy: Research, Audit & Plan

**Date:** 2026-02-18  
**Scope:** Base provider primitive, Go lib extraction, codegen, delegation model. Heavy depth.  
**Status:** Extended and harmonized with prior plans.

---

## Prior Plans Alignment

This plan extends and harmonizes with:

| Plan                                      | Alignment                                                                                                                                                                               |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CATALOG_CLIPROXY_FORK_ALIGNMENT**       | Provider mapping (nim, zen, kilo), catalog vs fork, model-first routing. Zen via openai-compatibility; nim needs openai-compat entry.                                                   |
| **LITELLM_HARNESS_MASTER_PLAN**           | CLIProxyAPIPlus = core execution layer. LiteLLM Router = optional front door for Responses API, fallback chains, cost tracking. Not interchangeable—different auth (OAuth vs API key).  |
| **LITELLM_CLIPROXY_BIFROST_HARMONY**      | Option A: CLIProxyAPIPlus as single proxy (8317). Bifrost out (no Python SDK; agent-scale doesn't need 50x speed).                                                                      |
| **CLIPROXY_API_AND_THGENT_UNIFIED_PLAN**  | Equal parity for all providers (dedicated blocks, token-file, OAuth). Cursor, MiniMax, Roo, Kilo = same pattern as Kiro, Gemini, Claude, Codex.                                         |
| **OPENROUTER_STYLE_ROUTING_AND_CLIPROXY** | CLIProxy holds auth, routing, execution. Metrics endpoint (`GET /v1/metrics/providers`) for cost/latency/TPS. thegent uses metrics for routing policy when available. LiteLLM optional. |

**Unified principle:** CLIProxyAPIPlus is the core LLM layer. Routing, auth, credential resolution live in the proxy (or extracted Go lib). thegent orchestrates (config path, lifecycle, dex aliases); agents delegate.

---

## Table of Contents

1. [Prior Plans Alignment](#prior-plans-alignment)
2. [Part 1: Research](#part-1-research) — Go libs, LiteLLM, provider primitive, codegen, harness integration, metrics, Bifrost/Pareto
3. [Part 2: Audit](#part-2-audit) — Provider taxonomy, config/synthesizer duplication, executors, credential flow
4. [Part 3: Plan](#part-3-plan) — Goals, base primitive, codegen, lib extraction, delegation, zen injection, phases
5. [Appendices](#appendix-a-file-reference) — File reference, LiteLLM pattern, prior plans, timeline

---

## Part 1: Research

### 1.1 Go LLM Libraries

| Library                      | Stars | Purpose                | Multi-Provider    | Routing    | Auth            |
| ---------------------------- | ----- | ---------------------- | ----------------- | ---------- | --------------- |
| **go-openai** (sashabaranov) | 10.5k | OpenAI client for Go   | No (OpenAI/Azure) | No         | API key only    |
| **langchaingo**              | 8.7k  | LangChain for Go       | Yes (via llms/)   | Via chains | Per-provider    |
| **CLIProxyAPI** (current)    | —     | Proxy + routing + auth | Yes               | Yes        | OAuth + API key |

**Findings:**

- **go-openai**: Single-provider client. BaseURL + API key. No routing, no multi-provider. Good for raw HTTP calls to OpenAI-compatible endpoints.
- **langchaingo**: Agent/chains framework. Has `llms/openai`, `llms/ollama`, `llms/gemini`, etc. Each LLM impl is separate; no unified credential/routing layer. Agentic focus.
- **No Go lib** provides: multi-provider routing + credential resolution (OAuth + API key) + model registry + config synthesis. CLIProxyAPI is the closest.

**Conclusion:** Extract CLIProxyAPI core as the Go lib. No drop-in replacement exists for multi-provider routing + OAuth/API-key credential resolution.

---

### 1.2 Framework Options (Python)

| Framework   | Language | Role               | Multi-Provider | Proxy |
| ----------- | -------- | ------------------ | -------------- | ----- |
| **LiteLLM** | Python   | SDK + AI Gateway   | 100+           | Yes   |
| **Ollama**  | Go       | Local model runner | No (local)     | No    |

**LiteLLM Architecture (from ARCHITECTURE.md):**

- **SDK** (`litellm/`): `completion()`, `acompletion()` → `get_llm_provider()` → `BaseLLMHTTPHandler` → provider `transform_request`/`transform_response` → HTTP.
- **Proxy** (`proxy/`): Auth, rate limiting, budgets, routing on top of SDK.
- **Provider pattern**: Each provider has `Config` with `transform_request()` and `transform_response()`. Translation layer is per-provider.
- **Key insight**: LiteLLM separates (1) proxy/auth/routing from (2) SDK/translation. CLIProxyAPI combines both in one service.

**LiteLLM vs CLIProxyAPI:**

- LiteLLM: Python, 100+ providers, enterprise features (Postgres, Redis, spend tracking).
- CLIProxyAPI: Go, OAuth-first (Claude, Codex, Gemini CLI), file-based auth, embeddable SDK.
- **Not interchangeable**: Different auth model (OAuth token files vs API keys), different deployment target.

---

### 1.3 Provider Primitive Pattern (Industry)

**LiteLLM:** `ProviderConfig` with `transform_request` / `transform_response`. Credential comes from `litellm_params` (api_key, etc.). No unified credential primitive.

**CLIProxyAPI (current):** Two credential sources:

1. **OAuth** (FileSynthesizer): JSON files in auth-dir, `access_token` or `api_key` in JSON.
2. **API key** (ConfigSynthesizer): `api-key` in YAML config.

**Unified primitive:** Credential = `api_key` (from config) OR `token` (from file). Same resolution: `resolveAPIKeyFromEntry(tokenFile, apiKey)`. OAuth and API key are **drop-in replacements** for the same slot.

---

### 1.4 Codegen Patterns

- **LiteLLM**: Manual `llms/{provider}/chat/transformation.py` per provider. No codegen.
- **CLIProxyAPI**: Manual `synthesizeXxxKeys` per provider. 20+ nearly identical functions.
- **Codegen opportunity**: Provider spec (name, yaml_key, base_url_default, env_vars, models) → generate config struct, synthesizer, executor registration.

---

### 1.5 LiteLLM Harness Integration

**Source:** `LITELLM_HARNESS_MASTER_PLAN.md`, `COMPLETE_PLAN_AND_RESEARCH.md`

| Harness       | Flow                                                  | Translation              |
| ------------- | ----------------------------------------------------- | ------------------------ |
| Codex CLI     | Responses API → cliproxy_adapter → CLIProxyAPIPlus    | Double (adapter + proxy) |
| Claude Code   | Chat Completions → CodexProxyRunner → CLIProxyAPIPlus | Single                   |
| Factory Droid | Chat Completions → Factory API → Providers            | Separate stack           |

**LiteLLM Router option:** Unify harnesses via LiteLLM Router as front door. `litellm_responses_handler.py` translates Responses API → Chat Completions; Router handles routing, fallback chains, caching, cost tracking. CLIProxyAPIPlus can be backend for OAuth providers (antigravity, iflow, kiro) when LiteLLM routes `minimax/*` → `http://127.0.0.1:8317/v1`.

**Positioning:** CLIProxyAPIPlus remains core for OAuth + file-based auth. LiteLLM Router is optional enhancement (`THGENT_USE_LITELLM_ROUTER=1`) for direct-API providers; CLIProxy for OAuth-backed providers.

---

### 1.6 OpenRouter-Style Routing & Metrics

**Source:** `OPENROUTER_STYLE_ROUTING_AND_CLIPROXY.md`

**CLIProxy responsibilities:** Auth, execution, model→provider routing, per-request metrics (latency, tokens, success/failure).

**Metrics endpoint (implemented):** `GET /v1/metrics/providers` returns per-provider rolling stats:

- `latency_p50_ms`, `latency_p95_ms`, `tps_1m`, `cost_per_1k`, `success_rate`

**thegent routing policy:** `_fetch_provider_metrics()` calls proxy; policy `cheapest` uses measured cost when available; tie-break by `success_rate`.

**Provider hint (optional):** Header `X-Provider-Hint: nim` for thegent to prefer a provider when multiple serve the model.

---

### 1.7 Bifrost, Pareto Router, Semantic Router

| System                       | Role                                                                            | Fit for CLIProxy/thegent                               |
| ---------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **Bifrost** (Go)             | 50x faster than LiteLLM, 15+ providers                                          | Out: no Python SDK; agent-scale doesn't need 50x speed |
| **Pareto Router** (research) | Hard constraints → Pareto frontier → lexicographic selection; Offer abstraction | Conceptual alignment; implementation TBD               |
| **Semantic Router**          | Zero-cost intent routing (10ms, vector-based)                                   | Future: complexity-based routing, cascade              |

**Conclusion:** Focus on CLIProxyAPIPlus extraction and codegen. LiteLLM optional. Bifrost/Pareto/Semantic are research references, not immediate dependencies.

---

## Part 2: Audit

### 2.1 Provider Taxonomy

| Category               | Providers                                                                     | Config Block         | Auth Source                | Executor                            | Synthesizer                         |
| ---------------------- | ----------------------------------------------------------------------------- | -------------------- | -------------------------- | ----------------------------------- | ----------------------------------- |
| **OAuth (file)**       | Claude, Codex, Gemini, Qwen, iFlow, Kiro, GitHub Copilot                      | auth-dir JSON        | FileSynthesizer            | ClaudeExecutor, CodexExecutor, etc. | FileSynthesizer                     |
| **OAuth + API key**    | MiniMax, Roo, Kilo                                                            | minimax, roo, kilo   | Config + token-file        | OpenAICompatExecutor                | ConfigSynthesizer                   |
| **API key only**       | DeepSeek, Groq, Mistral, SiliconFlow, OpenRouter, Together, Fireworks, Novita | dedicated blocks     | Config                     | OpenAICompatExecutor                | ConfigSynthesizer                   |
| **API key (config)**   | Gemini, Claude, Codex                                                         | gemini-api-key, etc. | Config                     | GeminiExecutor, etc.                | ConfigSynthesizer                   |
| **Generic OAI-compat** | zen, glm, nim, custom                                                         | openai-compatibility | Config (or thegent inject) | OpenAICompatExecutor                | ConfigSynthesizer                   |
| **Special**            | Cursor, Kiro, AI Studio, Antigravity, Vertex                                  | cursor, kiro, etc.   | Mixed                      | Custom executors                    | ConfigSynthesizer / FileSynthesizer |

**Catalog alignment:** zen (gemini-3-flash via OpenCode), nim (glm-5, step-3.5-flash via NVIDIA NIM). See `CATALOG_CLIPROXY_FORK_ALIGNMENT.md`.

---

### 2.2 Config Struct Duplication

**Identical struct pattern** (10 providers):

```go
type XxxKey struct {
    TokenFile string `yaml:"token-file,omitempty"`
    APIKey    string `yaml:"api-key,omitempty"`
    BaseURL   string `yaml:"base-url,omitempty"`
    ProxyURL  string `yaml:"proxy-url,omitempty"`
}
```

Used by: MiniMaxKey, RooKey, KiloKey, DeepSeekKey, GroqKey, MistralKey, SiliconFlowKey, OpenRouterKey, TogetherKey, FireworksKey, NovitaKey.

**Variants:**

- **GeminiKey, ClaudeKey, CodexKey**: APIKey + BaseURL only (no TokenFile in config; OAuth is file-based).
- **OpenAICompatibility**: Name, BaseURL, APIKeyEntries, Models. No TokenFile (API key only).
- **VertexCompatKey**: APIKey + BaseURL.
- **CursorKey, KiroKey**: TokenFile-focused.

---

### 2.3 Synthesizer Duplication

**ConfigSynthesizer** has 20+ `synthesizeXxxKeys` functions. Pattern for OAI-compat providers (Roo, Kilo, DeepSeek, Groq, Mistral, SiliconFlow, OpenRouter, Together, Fireworks, Novita):

```go
func (s *ConfigSynthesizer) synthesizeXxxKeys(ctx *SynthesisContext) []*coreauth.Auth {
    cfg := ctx.Config
    for i := range cfg.XxxKey {
        entry := &cfg.XxxKey[i]
        apiKey := s.resolveAPIKeyFromEntry(entry.TokenFile, entry.APIKey, i, "xxx")
        if apiKey == "" { continue }
        baseURL := defaultOr(entry.BaseURL, "https://api.xxx.com/v1")
        // build Auth with Provider, Label, Attributes (base_url, api_key)
        out = append(out, a)
    }
    return out
}
```

**Only differences:** config slice name, provider string, default base URL. ~40 lines × 10 ≈ 400 lines of near-duplicate code; codegen eliminates this.

---

### 2.4 Executor Taxonomy

| Executor                  | Providers                                                                                                                        | Backend                              |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| **OpenAICompatExecutor**  | minimax, roo, kilo, deepseek, groq, mistral, siliconflow, openrouter, together, fireworks, novita, cursor, zen, glm, nim, custom | HTTP to base_url + /chat/completions |
| **GeminiExecutor**        | gemini                                                                                                                           | Generative Language API              |
| **ClaudeExecutor**        | claude                                                                                                                           | Anthropic API                        |
| **CodexExecutor**         | codex                                                                                                                            | OpenAI API                           |
| **GeminiVertexExecutor**  | vertex                                                                                                                           | Vertex AI                            |
| **GeminiCLIExecutor**     | gemini-cli                                                                                                                       | Gemini CLI                           |
| **AIStudioExecutor**      | aistudio                                                                                                                         | AI Studio                            |
| **AntigravityExecutor**   | antigravity                                                                                                                      | Antigravity                          |
| **IFlowExecutor**         | iflow                                                                                                                            | iFlow                                |
| **QwenExecutor**          | qwen                                                                                                                             | Qwen                                 |
| **KimiExecutor**          | kimi                                                                                                                             | Kimi                                 |
| **KiroExecutor**          | kiro                                                                                                                             | AWS CodeWhisperer                    |
| **GitHubCopilotExecutor** | github-copilot                                                                                                                   | GitHub Copilot                       |

**Key finding:** 12+ providers use **OpenAICompatExecutor** with different provider keys. Same executor, different config source. Dedicated executors exist only for non–OpenAI-compatible APIs (Gemini, Claude, Codex, Vertex, etc.).

---

### 2.5 Credential Flow

```
Config (YAML)                    Auth Dir (JSON)
     │                                    │
     ├── gemini-api-key                   ├── *.claude.json
     ├── claude-api-key                   ├── *.codex.json
     ├── minimax[] (TokenFile|APIKey)     └── *.gemini.json
     ├── openai-compatibility[]
     └── ...
              │
              ▼
     ConfigSynthesizer + FileSynthesizer
              │
              ▼
     Auth[] (Provider, Label, Attributes{api_key, base_url, ...})
              │
              ▼
     registerModelsForAuth() → Model Registry
     ensureExecutorsForAuth() → Executor registration
              │
              ▼
     Request → GetProviderName(model) → Registry → Executor → HTTP
```

**Zen injection (thegent):** Python writes zen block to config before proxy loads. Proxy does not read env for zen. Responsibility split: thegent = config synthesis, proxy = read config.

---

### 2.6 thegent Provider Definitions

`provider_definitions.json` defines: minimax, nim, openrouter, zen. Each has:

- `base_url`, `base_url_env`, `model`, `extra_aliases`, `login` (url, display_name, instructions).

**Gap:** thegent has provider metadata; proxy has no equivalent. Proxy config is structural (YAML blocks); thegent adds semantic layer (which providers exist, how to log in). **Alignment:** PremadeOAICompat registry (Phase 1) can be seeded from or synced with `provider_definitions.json` for zen, nim, glm.

---

## Part 3: Plan

### 3.1 Goals

1. **Base provider primitive**: One credential type (api_key | token_file), one config shape for OAI-compat providers.
2. **Codegen**: Provider spec → config struct, synthesizer, registration. Eliminate 20+ hand-written synthesizers.
3. **Go lib extraction**: Routing, auth, model registry, config loading as reusable library.
4. **Delegation**: Python (thegent), Rust, Go, Zig, Nim agents delegate to Go lib. No routing/auth logic in agents.
5. **Zen parity**: Move zen injection to proxy (env-based) OR keep in thegent but align with premade OAI-compat pattern.

---

### 3.2 Base Provider Primitive

**Unified OAI-compat provider config:**

```go
// OAICompatProviderConfig - single struct for all OpenAI-compatible providers
type OAICompatProviderConfig struct {
    Name      string   `yaml:"name"`       // provider key: minimax, zen, glm, etc.
    TokenFile string   `yaml:"token-file,omitempty"`
    APIKey    string   `yaml:"api-key,omitempty"`
    BaseURL   string   `yaml:"base-url"`
    ProxyURL  string   `yaml:"proxy-url,omitempty"`
    Models    []ModelAlias `yaml:"models,omitempty"`
    Priority  int      `yaml:"priority,omitempty"`
    Prefix    string   `yaml:"prefix,omitempty"`
}

type ModelAlias struct {
    Name  string `yaml:"name"`
    Alias string `yaml:"alias"`
}
```

**Provider registry (premade):**

```go
var PremadeOAICompat = map[string]PremadeSpec{
    "zen":  {BaseURL: "https://opencode.ai/zen/v1", EnvVars: []string{"ZEN_API_KEY", "OPENCODE_API_KEY"}, DefaultModels: [...]},
    "glm":  {BaseURL: "...", ...},
    "nim":  {BaseURL: "https://integrate.api.nvidia.com/v1", ...},
    // ...
}
```

At config load: for each premade, if env set and not in config, inject entry. Matches minimax/kilo pattern.

---

### 3.3 Codegen Strategy

**Provider spec (YAML or Go):**

```yaml
providers:
  - name: minimax
    yaml_key: minimax
    base_url: https://api.minimax.io/v1
    credential: [api_key, token_file]
  - name: zen
    yaml_key: openai-compatibility # or dedicated zen
    base_url: https://opencode.ai/zen/v1
    credential: [api_key]
    env_vars: [ZEN_API_KEY, OPENCODE_API_KEY]
```

**Codegen output:**

- Config struct field (if dedicated block)
- Synthesizer function (or generic loop)
- Executor registration (all use OpenAICompatExecutor)

**Tool:** `go generate` + custom generator, or `cue`/`protoc`-style codegen.

---

### 3.4 Go Lib Extraction

**Current:** `sdk/cliproxy` exposes `NewBuilder().WithConfig().Build()` for embedding. Config loading, watcher, executors are in `internal/`.

**Target layout:**

```
pkg/llmproxy/           # Public lib
├── config/             # Config loading, validation
├── auth/               # Auth synthesis, credential resolution
├── registry/           # Model registry
├── executor/           # Executor interface, OpenAICompat impl
├── router/             # Model → provider resolution
└── service/            # Service lifecycle (Run, shutdown)

internal/               # Proxy-specific (CLI binary)
├── api/                # HTTP handlers, middleware
├── watcher/            # File watching
└── ...
```

**Lib API:**

```go
// ResolveProvider returns provider(s) for model
func (r *Registry) ResolveProvider(model string) []string

// GetCredentials returns credential for provider+auth
func (a *AuthManager) GetCredentials(provider, authID string) (baseURL, apiKey string)

// Execute runs request through executor
func (e *Executor) Execute(ctx context.Context, auth *Auth, req Request) (Response, error)
```

**Consumers:** CLIProxyAPI binary, thegent (via subprocess or future FFI), other Go/Rust/Zig/Nim agents.

---

### 3.5 Delegation Model

| Layer                | Responsibility                                                                         | Implementation              |
| -------------------- | -------------------------------------------------------------------------------------- | --------------------------- |
| **Go lib**           | Config load, auth synthesis, model registry, routing, credential resolution, execution | `pkg/llmproxy`              |
| **Proxy service**    | HTTP server, middleware, management API                                                | `internal/api`, `cmd/`      |
| **thegent (Python)** | Config path, proxy lifecycle, dex model aliases (flash→gemini-3-flash), IDE/MCP        | Delegates to proxy via HTTP |
| **Other agents**     | Agent logic, tools, UI                                                                 | Delegate to proxy or lib    |

**Critical:** Routing (model→provider), credential resolution, config synthesis must live in Go lib. Python only orchestrates (start proxy, pass config path).

---

### 3.6 Zen Injection: Proxy vs thegent

**Option A (current):** thegent injects zen when `THGENT_ZEN_API_KEY` set. Proxy reads config.

**Option B:** Proxy injects zen at load when `ZEN_API_KEY` or `OPENCODE_API_KEY` set and no zen in config. Aligns with "proxy owns credential resolution."

**Recommendation:** Option B. Add to proxy's config load:

```go
func (cfg *Config) InjectPremadeFromEnv() {
    for name, spec := range PremadeOAICompat {
        if cfg.hasProvider(name) { continue }
        key := getEnv(spec.EnvVars...)
        if key == "" { continue }
        cfg.OpenAICompatibility = append(cfg.OpenAICompatibility, spec.ToEntry(key))
    }
}
```

thegent can still inject for other reasons (e.g. ensure-config before first run); proxy handles env fallback.

---

### 3.7 Phased Implementation

#### Phase 1: Consolidate OAI-compat (4–6 weeks)

- [ ] Introduce `OAICompatProviderConfig` (or unify under `openai-compatibility` with optional TokenFile).
- [ ] Add generic `synthesizeOAICompatFromDedicatedBlocks()` that iterates minimax, roo, kilo, etc. using a provider registry.
- [ ] Deprecate per-provider synthesizers one by one.
- [ ] Add premade env injection for zen (and optionally glm, nim).

#### Phase 2: Codegen (3–4 weeks)

- [ ] Define provider spec format (YAML or Go struct).
- [ ] Implement codegen to produce config structs and synthesizer registration.
- [ ] Migrate all OAI-compat providers to codegen.
- [ ] Document provider addition process.

#### Phase 3: Lib Extraction (4–6 weeks)

- [ ] Create `pkg/llmproxy` with config, auth, registry, executor, router.
- [ ] Refactor `internal/` to use `pkg/llmproxy`.
- [ ] Publish lib as separate module or submodule.
- [ ] Update SDK docs.

#### Phase 4: Delegation Hardening (2–3 weeks)

- [ ] Audit thegent for any routing/auth logic; move to proxy.
- [ ] Define clear API contract (HTTP or lib) for agents.
- [ ] Document delegation model for Rust/Go/Zig/Nim agents.

#### Phase 5: Metrics & Routing Policy (1–2 weeks, optional)

- [ ] Ensure `GET /v1/metrics/providers` is stable and documented.
- [ ] thegent routing policy uses metrics when `cheapest` or `fastest`; fallback to static costs.
- [ ] Optional: `X-Provider-Hint` header support in proxy for thegent-driven routing.

---

### 3.8 Risks & Mitigations

| Risk                   | Mitigation                                                                         |
| ---------------------- | ---------------------------------------------------------------------------------- |
| Breaking config format | Maintain backward compatibility; support both old and new blocks during transition |
| Lib API churn          | Version lib (v1, v2); proxy pins version                                           |
| Codegen complexity     | Start with small set of providers; expand incrementally                            |
| thegent coupling       | Keep thegent as thin orchestrator; all logic in proxy/lib                          |

---

### 3.9 Success Criteria

1. **Single credential primitive**: All OAI-compat providers use `resolveAPIKeyFromEntry` (or equivalent) with api_key | token_file.
2. **No duplicate synthesizers**: One generic path for OAI-compat; codegen for spec.
3. **Zen from env**: Proxy injects zen when env set; no thegent-specific injection required for basic use.
4. **Lib usable standalone**: New Go program can `import llmproxy` and resolve route + execute without HTTP server.
5. **thegent < 100 lines** of proxy-specific logic (config path, start/stop, health check).
6. **Metrics available**: `GET /v1/metrics/providers` returns latency, TPS, cost, success_rate for routing policy.

---

## Appendix A: File Reference

| Purpose                 | Path                                                                       |
| ----------------------- | -------------------------------------------------------------------------- |
| Config structs          | `CLIProxyAPIPlus-fork/internal/config/config.go`                           |
| Config synthesizer      | `CLIProxyAPIPlus-fork/internal/watcher/synthesizer/config.go`              |
| File synthesizer        | `CLIProxyAPIPlus-fork/internal/watcher/synthesizer/file.go`                |
| resolveAPIKeyFromEntry  | `config.go:860`                                                            |
| OpenAICompatExecutor    | `CLIProxyAPIPlus-fork/internal/runtime/executor/openai_compat_executor.go` |
| registerModelsForAuth   | `CLIProxyAPIPlus-fork/sdk/cliproxy/service.go:756`                         |
| ensureExecutorsForAuth  | `service.go:371`                                                           |
| Zen injection (thegent) | `thegent/src/thegent/agents/cliproxy_manager.py:_inject_zen_into_cliproxy` |
| Provider definitions    | `thegent/src/thegent/agents/cliproxy_data/provider_definitions.json`       |
| SDK usage               | `CLIProxyAPIPlus-fork/docs/sdk-usage.md`                                   |

---

## Appendix B: LiteLLM Provider Config Pattern

```python
class ProviderConfig(BaseConfig):
    def transform_request(self, model, messages, optional_params, litellm_params, headers):
        return {"messages": transformed_messages, ...}
    def transform_response(self, model, raw_response, model_response, logging_obj, ...):
        return ModelResponse(choices=[...], usage=Usage(...))
```

CLIProxyAPI equivalent: `Executor` interface with `Execute()`. Translation in `sdk/translator`. Different abstraction (executor vs transform) but same idea: provider-specific logic isolated.

---

## Appendix C: Prior Plans Reference

| Document                           | Path                                                          | Key Content                                               |
| ---------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| Catalog–Fork Alignment             | `thegent/docs/plans/CATALOG_CLIPROXY_FORK_ALIGNMENT.md`       | Provider mapping, nim/zen setup, model-first routing      |
| LiteLLM Harness Master Plan        | `thegent/docs/research/LITELLM_HARNESS_MASTER_PLAN.md`        | Unified harness via LiteLLM Router, Responses API handler |
| LiteLLM + CLIProxy Bifrost Harmony | `thegent/docs/plans/LITELLM_CLIPROXY_BIFROST_HARMONY.md`      | Option A (CLIProxy single), Bifrost out                   |
| CLIProxy + Thegent Unified Plan    | `thegent/docs/plans/CLIPROXY_API_AND_THGENT_UNIFIED_PLAN.md`  | Provider parity (Cursor, MiniMax, Roo, Kilo)              |
| OpenRouter-Style Routing           | `thegent/docs/plans/OPENROUTER_STYLE_ROUTING_AND_CLIPROXY.md` | Metrics endpoint, routing policy, LiteLLM optional        |
| Complete Plan and Research         | `thegent/docs/research/COMPLETE_PLAN_AND_RESEARCH.md`         | Research index, Pareto router, Ultra advanced             |

---

## Appendix D: Timeline Summary

| Phase                           | Duration  | Scope                                                           |
| ------------------------------- | --------- | --------------------------------------------------------------- |
| 1. Consolidate OAI-compat       | 4–6 weeks | OAICompatProviderConfig, generic synthesizer, zen env injection |
| 2. Codegen                      | 3–4 weeks | Provider spec → config, synthesizer, registration               |
| 3. Lib Extraction               | 4–6 weeks | `pkg/llmproxy`, refactor internal                               |
| 4. Delegation Hardening         | 2–3 weeks | thegent audit, API contract, docs                               |
| 5. Metrics & Routing (optional) | 1–2 weeks | Metrics stability, thegent policy                               |

**Total:** 14–21 weeks (core 14–19; Phase 5 optional).

---

## Quick Wins (Pre-Phase 1)

| Action                                           | Effort  | Impact                                     |
| ------------------------------------------------ | ------- | ------------------------------------------ |
| Document nim setup in CLAUDE.md                  | 1 hr    | Users can add openai-compatibility for NIM |
| Add zen to PremadeOAICompat (env injection)      | 2–4 hrs | Zen works without thegent injection        |
| Verify `GET /v1/metrics/providers` is documented | 1 hr    | thegent routing policy can use metrics     |
