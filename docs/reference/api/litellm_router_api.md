# litellm_router API Reference

> **Source**: `src/thegent/routing/litellm_router.py`

LiteLLM Router wrapper with full feature support.

Provides comprehensive LiteLLM integration including:

- Multi-provider routing (cheapest, fastest, latency-based, round_robin)
- Response caching (in-memory or Redis)
- Fallback chains with cooldown times
- Context window validation
- Cost tracking and budget alerts
- Webhook alerting for latency/errors/budget
- Streaming support
- Donut Architecture integration

---

## EnhancedRouter

Enhanced router with full feature support.

Wraps LiteLLM Router with:

- Cost tracking integration
- Alert management
- Donut Architecture integration
- Context window validation
- Streaming support

### Methods

#### EnhancedRouter.**init**

```python
__init__(self: Any, policy: Any)
```

Initialize enhanced router.

**Parameters**:

- `policy`: Optional routing policy override

---

#### EnhancedRouter.alert_manager

```python
alert_manager(self: Any)
```

Get alert manager (lazy initialization).

---

#### EnhancedRouter.cost_tracker

```python
cost_tracker(self: Any)
```

Get cost tracker (lazy initialization).

---

#### EnhancedRouter.donut_adapter

```python
donut_adapter(self: Any)
```

Get Donut adapter (lazy initialization).

---

#### EnhancedRouter.route

```python
route(self: Any, prompt: str, model: Any, stream: bool)
```

Route a request through LiteLLM.

**Parameters**:

- `prompt`: The prompt to send
- `model`: Optional model override (otherwise router selects)
- `stream`: Whether to stream the response
- `**kwargs`: Additional LiteLLM parameters

**Returns**: RoutingResult with response and metadata

---

#### EnhancedRouter.route_stream

```python
route_stream(self: Any, prompt: str, model: Any)
```

Route with streaming response.

**Parameters**:

- `prompt`: The prompt to send
- `model`: Optional model override
- `**kwargs`: Additional LiteLLM parameters

**Returns**: Stream chunks from the model

---

---

## RouterConfig

Configuration for LiteLLM Router.

---

## RoutingResult

Result from a routing operation.

---

## alert_manager

```python
alert_manager(self: Any)
```

Get alert manager (lazy initialization).

---

## build_fallback_chains

Build fallback chains for models.

**Returns**: Dict mapping primary model to list of fallback models

---

## build_litellm_model_list

Build LiteLLM model_list from catalog routes.

Excludes NATIVE_CLI_PROVIDERS (codex, claude).
Routes API_KEY_PROVIDERS directly.
Routes LOGIN_AUTH_PROVIDERS via CLIProxyAPIPlus.

**Returns**: List of LiteLLM model_list entries

---

## cost_tracker

```python
cost_tracker(self: Any)
```

Get cost tracker (lazy initialization).

---

## donut_adapter

```python
donut_adapter(self: Any)
```

Get Donut adapter (lazy initialization).

---

## get_all_models_with_metadata

---

## get_context_window

```python
get_context_window(model: str)
```

Get context window size for a model.

**Parameters**:

- `model`: Model name (may be alias)

**Returns**: Context window in tokens

---

## get_enhanced_router

```python
get_enhanced_router(policy: Any)
```

Get global enhanced router instance.

**Parameters**:

- `policy`: Optional routing policy override

**Returns**: EnhancedRouter instance

---

## get_litellm_router

```python
get_litellm_router(policy: str)
```

Get configured LiteLLM Router instance.

**Parameters**:

- `policy`: Routing policy (cost-based-routing, fastest, round_robin, latency-based-routing)

**Returns**: Configured LiteLLM Router

---

## get_model_metadata

```python
get_model_metadata(model_id: str) -> Any
```

---

## get_pareto_preferred_model

```python
get_pareto_preferred_model(complexity_tier: str)
```

Pre-select model via Pareto for LiteLLM when policy=pareto. Returns provider/model or None.

---

## get_router_config

Get router configuration from settings.

**Returns**: RouterConfig with values from ThegentSettings

---

## has_model_metadata

```python
has_model_metadata(model_id: str) -> bool
```

---

## reset_enhanced_router

Reset the global enhanced router (useful for testing).

---

## route

```python
route(self: Any, prompt: str, model: Any, stream: bool)
```

Route a request through LiteLLM.

**Parameters**:

- `prompt`: The prompt to send
- `model`: Optional model override (otherwise router selects)
- `stream`: Whether to stream the response
- `**kwargs`: Additional LiteLLM parameters

**Returns**: RoutingResult with response and metadata

---

## route_stream

```python
route_stream(self: Any, prompt: str, model: Any)
```

Route with streaming response.

**Parameters**:

- `prompt`: The prompt to send
- `model`: Optional model override
- `**kwargs`: Additional LiteLLM parameters

**Returns**: Stream chunks from the model

---

## validate_context_window

```python
validate_context_window(model: str, prompt_tokens: int)
```

Validate that prompt fits within model's context window.

**Parameters**:

- `model`: Model name
- `prompt_tokens`: Estimated prompt token count

**Returns**: True if prompt fits, False otherwise

---
