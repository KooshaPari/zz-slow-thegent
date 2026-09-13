<DONE>
# CLIProxy++ Standalone Product Design

**Date:** 2026-02-20
**Status:** Architecture Proposal
**Author:** Claude Code (design session)

---

## 1. Context and Motivation

`CLIProxyAPIPlus++` (cliproxy++) is currently embedded inside thegent as a binary process manager (`cliproxy_manager.py`) paired with an adapter layer (`cliproxy_adapter.py`). It solves a real, widely-felt problem: any CLI agent tool (Codex CLI, Claude Code CLI, Gemini CLI, Cursor, Kiro, Copilot, etc.) is hardwired to one set of providers. Developers who want to route those tools through a different provider, or through a self-hosted or cheaper LLM, have no clean first-party option.

cliproxy++ intercepts the tool's HTTP calls and routes them through a unified OpenAI-compatible proxy backed by LiteLLM. It handles the translation between the Responses API v2 (what Codex uses), Chat Completions (what most providers expose), and WebSocket streaming. It also manages OAuth and API-key credential flows for ~15 providers.

The goal of this document is to define the clean boundary between:

- **cliproxy++ standalone** — the publicly-marketable product
- **thegent's additions** — agent orchestration hooks that consume cliproxy++ as infrastructure

---

## 2. What Belongs in the Standalone Product

### 2.1 Core Feature Set (In Scope)

**Protocol Translation Layer**

- OpenAI-compatible HTTP server (listens on configurable port, default `8317`)
- `POST /v1/chat/completions` — standard Chat Completions passthrough with provider routing
- `POST /v1/responses` — Responses API v2 (used by Codex CLI and Claude Code CLI) translated to Chat Completions at the provider side
- `GET /v1/models` — unified model list from all configured providers; response normalized to `{"models": [...]}` (Codex format, not `{"data": [...]}` OpenAI format)
- WebSocket `ws://host/v1/responses` — Codex CLI WebSocket mode, bridging WS to HTTP streaming SSE
- `GET /v1/metrics/providers` — per-provider metrics (latency, error rate, cost)

**Model Aliasing**

- Call any model by any name: `claude-sonnet-4.5`, `sonnet`, `haiku`, `gpt-4o` all resolve to whatever underlying model you configure
- Alias table driven by a config file (YAML or JSON); no code changes needed to add aliases
- Provider-native names always work alongside alias names (e.g., `MiniMax-M2.5` and `minimax-m2.5` both work)

**Provider Routing**

- LiteLLM Router as the routing core (library-first; thin wrapper only)
- Routing strategies: `cheapest` (cost-based), `fastest` (latency-based), `round_robin`, `latency-based`
- Configurable fallback chains: if primary model fails, automatically try next model in chain
- Cooldown tracking: failed providers back off automatically

**Provider Authentication**

- OAuth flow for providers that require it: Claude Code (`-claude-login`), Codex (`-codex-login`), Gemini (`-login`), Copilot (`-github-copilot-login`), Kiro, Kimi, GLM/iFlow, Qwen, Roo, Kilo, Antigravity
- API-key flow for API-key providers: MiniMax, NVIDIA NIM, OpenRouter, OpenCode Zen, Qwen, Roo
- Credential storage in auth directory (`~/.cli-proxy-api/`)
- `cliproxy login <provider>` CLI command for interactive setup
- `cliproxy login --all` for batch setup

**Configuration**

- Single YAML config file at `~/.cliproxy/config.yaml` (override via `CLIPROXY_CONFIG`)
- Provider definitions in a bundled JSON (equivalent of the current `provider_definitions.json`)
- Model alias definitions in a bundled JSON (equivalent of `model_definitions.json`)
- Zero-config default: works with a minimal config; add providers incrementally
- Port configurable via `CLIPROXY_PORT` or config file

**Cost Tracking**

- Per-request cost estimation using LiteLLM's built-in cost tracking
- Per-provider spend aggregated and exposed at `GET /v1/metrics/providers`
- Optional daily budget cap with hard stop when exceeded
- Webhook alerting when budget threshold is crossed

**Lifecycle Management**

- Foreground mode: `cliproxy start`
- Background mode: `cliproxy start --daemon`
- macOS LaunchAgent service: `cliproxy service install` / `cliproxy service start`
- Linux systemd unit file generation: `cliproxy service install --systemd`
- Readiness check: proxy polls `GET /v1/models` internally before declaring ready
- Clean shutdown via `cliproxy stop`
- `cliproxy status` — is it running, what port, which providers are active

**Cursor and Kiro Injection**

- Cursor token-file flow (`sk-...` from `/build-key`) and auth-token flow (zero-action)
- Kiro token import from `~/.kiro/kiro-auth-token.json`
- Both injected into proxy config automatically when credentials exist

### 2.2 Explicitly Excluded from Standalone Product

The following capabilities exist in thegent today but are thegent-specific agent orchestration concerns. They must not be part of the public cliproxy++ product:

| Feature                                                       | Why it stays in thegent                           |
| ------------------------------------------------------------- | ------------------------------------------------- |
| Agent lifecycle management (start/stop agent sessions)        | cliproxy++ is infrastructure, not an orchestrator |
| Work stream integration (`thegent plan`, `thegent free`)      | Domain-specific to thegent's task queue           |
| Team/swarm coordination hooks                                 | Agent-to-agent routing logic                      |
| Memory systems (`thegent_memory_add`, session scraping)       | Agent state management                            |
| Governance hooks (kill switch, audit trails, OPA integration) | Enterprise policy layer above the proxy           |
| Pareto routing (multi-objective model selection)              | thegent's specialized routing algorithm           |
| Model metadata registry (`model_metadata.py`)                 | Shared infra but thegent-specific consumers       |
| Donut Architecture adapter (`donut_adapter.py`)               | thegent internal observability pattern            |
| Shared MCP server manager                                     | thegent process orchestration                     |
| `ThegentSettings` — the settings class itself                 | Replace with a self-contained `ClipproxySettings` |
| Factory config lookup (`~/.factory/config.json`)              | Factory-platform-specific integration             |

---

## 3. Recommended Architecture

### 3.1 Repository Structure

```
cliproxy/                          # repo root (suggested name: cliproxy)
  src/cliproxy/
    __init__.py
    config.py                      # ClipproxySettings (pydantic-settings, no ThegentSettings dep)
    server.py                      # Starlette app factory
    router.py                      # LiteLLM Router wrapper (thin, <100 LOC)
    responses_handler.py           # Responses API v2 <-> Chat Completions translation
    websocket_handler.py           # WebSocket /v1/responses bridge
    models_handler.py              # /v1/models normalization
    metrics_handler.py             # /v1/metrics/providers
    auth/
      manager.py                   # Credential storage and lookup
      oauth.py                     # OAuth flow delegator (calls binary's -login flags)
      api_key.py                   # API-key flow (browser + prompt)
    providers/
      definitions.json             # Provider base URLs, models, login URLs (portable JSON)
      model_definitions.json       # Common model aliases
      loader.py                    # Load and validate definitions JSON
    lifecycle/
      daemon.py                    # Start/stop background process
      service.py                   # LaunchAgent (macOS) + systemd (Linux) generators
      health.py                    # Readiness polling
    cli/
      main.py                      # `cliproxy` entry point (typer)
      login.py                     # `cliproxy login <provider>`
      start.py                     # `cliproxy start [--daemon]`
      stop.py                      # `cliproxy stop`
      status.py                    # `cliproxy status`
      service.py                   # `cliproxy service install|start|stop|uninstall`
  tests/
  pyproject.toml
  README.md
  CHANGELOG.md
```

### 3.2 Core Dependencies

| Need             | Library               | Notes                                        |
| ---------------- | --------------------- | -------------------------------------------- |
| HTTP server      | starlette + uvicorn   | Minimal ASGI; no FastAPI overhead            |
| Provider routing | litellm (Router)      | Do not reimplement; thin config wrapper only |
| HTTP client      | httpx                 | Async, used for proxy passthrough            |
| CLI              | typer                 | Consistent with thegent conventions          |
| Config           | pydantic-settings     | Env var + YAML config merging                |
| YAML             | ruamel.yaml or PyYAML | Config read/write                            |
| Logging          | structlog             | Structured JSON for aggregation              |

Do NOT add: custom retry loops (use LiteLLM's built-in `num_retries`), custom cache logic (use LiteLLM's `cache_responses`), custom circuit breaker (LiteLLM handles cooldowns).

### 3.3 Config File Format

```yaml
# ~/.cliproxy/config.yaml
port: 8317
auth-dir: ~/.cliproxy/auth

# Routing policy: cheapest | fastest | round_robin | latency-based
routing: cheapest

# Cost budget (USD/day). Requests blocked when exceeded.
# cost-budget: 5.00

# Fallback chains (primary -> fallbacks)
fallbacks:
  claude-sonnet-4.5: [deepseek-v3.2, glm-5]
  gpt-4o: [gpt-4o-mini, glm-5]

# OpenAI-compatible providers (API-key auth)
openai-compatibility:
  - name: minimax
    base-url: https://api.minimax.io/v1
    api-key-entries:
      - api-key: sk-...
    models:
      - name: MiniMax-M2.5
        alias: MiniMax-M2.5
      - name: MiniMax-M2.5
        alias: minimax-m2.5
      # Alias any Claude name to MiniMax for transparent substitution:
      - name: MiniMax-M2.5
        alias: claude-sonnet-4.5

# Cursor (token-file or auth-token)
cursor:
  - cursor-api-url: http://127.0.0.1:3000
    auth-token: <your-cursor-auth-token>

# Kiro (token-file from ~/.kiro/kiro-auth-token.json)
kiro:
  - token-file: ~/.kiro/kiro-auth-token.json
```

The config format is intentionally compatible with the existing cliproxy++ binary's config schema so migration from the current embedded version is zero-effort.

### 3.4 Dependency Boundaries

```
cliproxy++ (public product)
    |
    +-- starlette (HTTP server)
    +-- litellm (routing, cost tracking, caching)
    +-- httpx (proxy passthrough)
    +-- typer (CLI)
    +-- pydantic-settings (config)
    +-- structlog (logging)

thegent (private, consumes cliproxy++)
    |
    +-- cliproxy++ (via pip install or internal package)
    +-- cliproxy.ClipproxySettings extended by ThegentSettings
    +-- cliproxy.lifecycle.start_managed() called by thegent process manager
    +-- cliproxy.router extended with ParetoRouter strategy
    +-- cliproxy.metrics consumed by thegent observability layer
```

---

## 4. thegent Extension Pattern

thegent should consume cliproxy++ as a library and extend it through three clean seams.

### 4.1 Settings Extension

```python
# thegent/config.py
from cliproxy.config import ClipproxySettings


class ThegentSettings(ClipproxySettings):
    # thegent-specific overrides and additions
    cliproxy_binary: str = "cli-proxy-api-plus"
    use_litellm_router: bool = True
    pareto_routing_enabled: bool = False
    # ... thegent-specific fields
```

### 4.2 Router Extension (Strategy Pattern)

cliproxy++ exposes a `RouterStrategy` protocol:

```python
# cliproxy/router.py
from typing import Protocol


class RouterStrategy(Protocol):
    async def select_model(self, request: dict) -> str:
        """Return model identifier to route to."""
        ...
```

thegent registers its Pareto router:

```python
# thegent/routing/pareto_router_strategy.py
from cliproxy.router import RouterStrategy


class ParetoRouterStrategy:
    async def select_model(self, request: dict) -> str:
        from thegent.routing.pareto_router import select_offer

        route = select_offer(complexity_tier=request.get("complexity", "moderate"))
        if route:
            return f"{route[0]}/{route[1]}"
        return request.get("model", "")
```

Registered at startup:

```python
from cliproxy.server import ClipproxyServer
from thegent.routing.pareto_router_strategy import ParetoRouterStrategy

server = ClipproxyServer(settings=thegent_settings)
server.set_router_strategy(ParetoRouterStrategy())
```

### 4.3 Metrics Hook

cliproxy++ emits structured metrics events. thegent subscribes:

```python
# cliproxy/metrics.py
class MetricsEvent:
    model: str
    provider: str
    tokens: int
    cost_usd: float
    latency_ms: float
    is_fallback: bool


# thegent registers a callback:
from cliproxy.metrics import subscribe_metrics

subscribe_metrics(thegent_observability_collector.record)
```

This keeps all agent-specific observability in thegent while cliproxy++ remains transport-only.

### 4.4 Lifecycle Management (Current Pattern, Preserved)

thegent calls the managed start function. cliproxy++ exposes:

```python
# cliproxy/lifecycle/daemon.py
def start_managed(settings: ClipproxySettings) -> tuple[Process | None, str]:
    """Start proxy and return (proc, base_url). None if already running."""
    ...
```

thegent's current `ensure_proxy_running()` and `start_proxy_managed()` map directly to this. The rename to `start_managed()` is the only change.

---

## 5. Public API Surface

### 5.1 HTTP Endpoints

| Method | Path                    | Description                                                        |
| ------ | ----------------------- | ------------------------------------------------------------------ |
| `GET`  | `/v1/models`            | Unified model list; response in Codex format (`{"models": [...]}`) |
| `POST` | `/v1/chat/completions`  | Standard Chat Completions; routes to configured provider           |
| `POST` | `/v1/responses`         | Responses API v2; translated to Chat Completions internally        |
| `WS`   | `/v1/responses`         | WebSocket Responses API v2; streaming mode for Codex               |
| `GET`  | `/v1/metrics/providers` | Per-provider cost, latency, error rate                             |
| `GET`  | `/health`               | Returns `{"status": "ok"}` when proxy is ready                     |

### 5.2 Python API (for programmatic consumers)

```python
from cliproxy import ClipproxyServer, ClipproxySettings

settings = ClipproxySettings(port=8317)
server = ClipproxyServer(settings)

# Start in background (returns base_url)
base_url = server.start()

# Start in foreground (blocks)
server.run()

# Check if running
server.is_ready()  # -> bool

# Stop
server.stop()
```

### 5.3 CLI Commands

```bash
# Auth setup
cliproxy login claude          # OAuth flow
cliproxy login minimax         # API-key flow (opens browser, prompts for key)
cliproxy login --all           # Setup all configured providers
cliproxy login gemini --force  # Re-authenticate even if already configured

# Proxy lifecycle
cliproxy start                 # Foreground (Ctrl-C to stop)
cliproxy start --daemon        # Background (writes PID file)
cliproxy stop                  # Stop background instance
cliproxy status                # Is it running? Port? Active providers?
cliproxy restart               # Stop + start

# System service
cliproxy service install       # macOS LaunchAgent or Linux systemd
cliproxy service start
cliproxy service stop
cliproxy service uninstall

# Config and diagnostics
cliproxy config show           # Print resolved config
cliproxy config init           # Create starter config at ~/.cliproxy/config.yaml
cliproxy providers list        # List known providers and auth status
cliproxy metrics               # Print current per-provider metrics
```

### 5.4 Environment Variables

| Variable               | Default                   | Description                      |
| ---------------------- | ------------------------- | -------------------------------- |
| `CLIPROXY_PORT`        | `8317`                    | Proxy listen port                |
| `CLIPROXY_CONFIG`      | `~/.cliproxy/config.yaml` | Config file path                 |
| `CLIPROXY_AUTH_DIR`    | `~/.cliproxy/auth`        | OAuth credential storage         |
| `CLIPROXY_ROUTING`     | `cheapest`                | Routing strategy                 |
| `CLIPROXY_DEBUG`       | `0`                       | Enable debug logging             |
| `CLIPROXY_COST_BUDGET` | unset                     | Daily cost budget in USD         |
| `CLIPROXY_BINARY`      | `cli-proxy-api-plus`      | Path to the underlying Go binary |

---

## 6. Competitive Positioning

### 6.1 Market Landscape

| Tool                  | Strength                       | Weakness vs cliproxy++                                                                                                 |
| --------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **LiteLLM Proxy**     | Broad provider support, mature | Does not speak Responses API v2; no CLI-tool-native OAuth flows; requires API keys only; no WebSocket Responses bridge |
| **OpenRouter**        | Easy signup, many models       | Cloud service (data leaves machine); no self-hosted option; no Codex/Claude Code native support                        |
| **Ollama**            | Great for local models         | Local-only; no routing to cloud providers; no OAuth flows                                                              |
| **Portkey**           | Observability focus, cloud     | SaaS; no OAuth for CLI tools; no Responses API v2                                                                      |
| **litellm (library)** | Very flexible                  | Requires custom server code; developer-facing, not end-user-facing                                                     |

### 6.2 cliproxy++ Differentiators

1. **Responses API v2 native support.** LiteLLM Proxy does not implement `/v1/responses`. cliproxy++ does, including WebSocket mode. This is the only tool that makes Codex CLI and Claude Code CLI work with arbitrary backends without patching the tools.

2. **OAuth-native CLI tool authentication.** No other proxy handles the OAuth flows that Codex, Claude Code, Gemini, Copilot, and Kiro use. cliproxy++ manages these credential files so the developer just runs `cliproxy login claude`.

3. **Zero-code model aliasing.** Call `claude-sonnet-4.5` and have it routed to MiniMax, GLM-5, or any other provider transparently. The CLI tool sees the model it expects; cliproxy++ handles the substitution.

4. **Local-first, zero-data-sharing.** All traffic stays on localhost by default. No cloud dependency. Works air-gapped when using local providers.

5. **Single binary + Python package.** The Go binary handles OAuth sessions; the Python package handles routing, cost tracking, and serving. Simple installation.

---

## 7. Marketing Pitch

> **cliproxy++** is an OpenAI-compatible local proxy that lets you point any AI CLI tool — Codex CLI, Claude Code, Gemini CLI, Cursor, GitHub Copilot — at any LLM provider you choose. Set up once, use everywhere: model aliasing means your tools keep calling `claude-sonnet-4.5` while cliproxy++ quietly routes to MiniMax, GLM-5, OpenRouter, or your own LiteLLM deployment. Full Responses API v2 support (the protocol Codex uses over WebSocket) means zero compatibility hacks. Native OAuth flows for 15+ providers mean zero API-key gymnastics. Track spend per provider, set daily budgets, and configure automatic fallbacks — all from a single YAML file.

---

## 8. Suggested Repo Name and README Structure

**Repo name:** `cliproxy` (short, memorable, unambiguous)
**Binary name:** `cliproxy`
**PyPI package:** `cliproxy`
**npm shim (optional):** `@cliproxy/cli`

### README Structure

```
# cliproxy

One proxy. Every AI tool. Any LLM.

## Quick Start
## Installation
## Supported CLI Tools (Codex, Claude Code, Gemini, Cursor, Copilot, Kiro)
## Supported Providers (15+ listed with auth type)
## Configuration
  - Provider setup
  - Model aliasing
  - Fallback chains
  - Cost budgets
## CLI Reference
## API Reference
  - /v1/chat/completions
  - /v1/responses (Responses API v2)
  - WebSocket /v1/responses
  - /v1/models
  - /v1/metrics/providers
## Routing Strategies
## Running as a System Service
## Extending cliproxy (strategy hooks for custom routers)
## Architecture
## Contributing
## License (MIT or Apache-2.0)
```

---

## 9. Extraction Checklist (Current thegent -> Standalone)

### Files to extract and clean:

| Current thegent path                                         | Target cliproxy path                                                | Changes needed                                                                                                                                                                                                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/thegent/agents/cliproxy_manager.py`                     | `src/cliproxy/lifecycle/daemon.py` + `src/cliproxy/auth/manager.py` | Remove `ThegentSettings` imports; replace with `ClipproxySettings`; remove factory config lookup (`_get_factory_api_key`) — that's Factory-platform-specific                                                                                        |
| `src/thegent/cliproxy_adapter.py`                            | `src/cliproxy/server.py` + `src/cliproxy/responses_handler.py`      | Remove `use_litellm_router` flag (always use LiteLLM); remove thegent settings import; remove `resolve_model_for_backend` (harness model mapping is thegent-specific)                                                                               |
| `src/thegent/routing/litellm_responses_handler.py`           | `src/cliproxy/responses_handler.py`                                 | Remove `get_litellm_router()` from thegent; replace with cliproxy's own router init                                                                                                                                                                 |
| `src/thegent/routing/litellm_router.py`                      | `src/cliproxy/router.py` (subset only)                              | Extract: `build_litellm_model_list`, `build_fallback_chains`, `get_litellm_router`. Remove: `EnhancedRouter` (thegent's wrapper with cost_tracker, alert_manager, donut_adapter), Pareto integration, model metadata validation specific to thegent |
| `src/thegent/agents/cliproxy_data/provider_definitions.json` | `src/cliproxy/providers/definitions.json`                           | Portable as-is; remove `base_url_env` entries that reference `THGENT_*` env vars (replace with `CLIPROXY_*`)                                                                                                                                        |
| `src/thegent/agents/cliproxy_data/model_definitions.json`    | `src/cliproxy/providers/model_definitions.json`                     | Portable as-is                                                                                                                                                                                                                                      |

### What thegent retains after extraction:

```python
# thegent keeps thin wrappers that delegate to cliproxy:
from cliproxy.lifecycle import start_managed, stop_proxy, is_ready
from cliproxy.config import ClipproxySettings


class ThegentSettings(ClipproxySettings):
    # thegent-specific fields only
    ...


# thegent's cliproxy_manager.py becomes:
def ensure_proxy_running(settings: ThegentSettings) -> str:
    from cliproxy.lifecycle import start_managed

    _, base_url = start_managed(settings)
    return base_url
```

---

## 10. Open Questions

1. **Binary distribution model.** The Go binary (`cli-proxy-api-plus`) handles OAuth credential management. Options: (a) keep it as a required external download with clear install instructions, (b) vendor it inside the Python package wheel as a platform-specific artifact, (c) rewrite OAuth flows in Python long-term to remove the Go dependency. Recommendation: (a) for v1 with install script, (b) for v2 using `shiv` or package_data.

2. **Versioning policy.** The config file format must remain stable across versions since users hand-edit it. A formal schema version field in the YAML is recommended from day one.

3. **The `cli-proxy-api-plus` binary name.** If cliproxy++ becomes the public product name, the binary name `cli-proxy-api-plus` is an artifact of the original naming. For public release, aligning on `cliproxy` as both the Python package and the binary name reduces confusion.

4. **Plugin/hook API surface.** The `RouterStrategy` protocol and `subscribe_metrics()` hook described above are the minimal extension points thegent needs. Before publishing these as stable public API, decide if third-party consumers (not just thegent) are a target for v1.

5. **Factory config lookup removal.** The current code reads `~/.factory/config.json` and `~/.factory/settings.json` to find API keys from the Factory platform. This is 100% Factory-platform-specific and must be removed from the standalone product. The `_get_factory_api_key` function and `_FACTORY_PROVIDER_PATTERNS` dict go away entirely in cliproxy++ standalone.
