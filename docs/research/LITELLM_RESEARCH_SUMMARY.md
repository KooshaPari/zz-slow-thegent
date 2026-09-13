<DONE>
# LiteLLM Router Research Summary

**Date**: 2026-02-18
**Purpose**: Research findings for LiteLLM Router integration

---

## LiteLLM Router Overview

**Source**: [LiteLLM Router Documentation](https://docs.litellm.ai/docs/routing), [LiteLLM GitHub](https://github.com/BerriAI/litellm)

### What is LiteLLM Router?

LiteLLM Router is a Python library that provides:

- **Unified interface** to 100+ LLM providers
- **Load balancing** across multiple deployments
- **Automatic fallback** and retry logic
- **Caching** (in-memory or Redis)
- **Cost tracking** and budget management
- **Routing strategies** (cost-based, latency-based, etc.)

### Key Statistics

- **36,226 stars** on GitHub
- **100+ providers** supported
- **8ms P95 latency** at 1k RPS (production-tested)
- **Used by Netflix** at scale

---

## Routing Strategies

### 1. simple-shuffle (Default, Recommended)

**How it works**:

- Weighted random selection based on RPM/TPM limits
- If RPM/TPM not provided, randomly picks deployment
- Can set `weight` param for preference

**Performance**: Best performance with minimal latency overhead

**Use Case**: Production (recommended)

**Example**:

```python
router = Router(model_list=model_list, routing_strategy="simple-shuffle")
```

### 2. cost-based-routing

**How it works**:

- Routes to cheapest available model
- Considers pricing from `model_prices_and_context_window.json`
- Falls back if cheapest unavailable

**Use Case**: Budget-conscious deployments

### 3. latency-based-routing

**How it works**:

- Routes based on latency metrics
- Tracks deployment latency over time
- Selects fastest deployment

**Use Case**: Performance-critical applications

### 4. least-busy

**How it works**:

- Selects least loaded deployment
- Tracks concurrent requests per deployment
- Distributes load evenly

**Use Case**: High traffic scenarios

### 5. usage-based-routing / usage-based-routing-v2

**How it works**:

- Routes based on RPM/TPM limits
- Prevents hitting rate limits
- ASYNC version (v2) for better performance

**Use Case**: Rate limit management

---

## Reliability Features

### Retries

**Configuration**:

```python
router = Router(
    num_retries=3,
    retry_after=5,  # Wait 5s before retrying
)
```

**Behavior**:

- Exponential backoff for `RateLimitError`
- Immediate retry for generic errors
- Custom retry policies per error type

**Custom Retry Policy**:

```python
retry_policy = RetryPolicy(
    ContentPolicyViolationErrorRetries=3, AuthenticationErrorRetries=0, RateLimitErrorRetries=3, TimeoutErrorRetries=2
)
```

### Cooldowns

**How it works**:

- Tracks failures per deployment
- Cooldowns deployment if failures > threshold
- Cooldown duration configurable
- Per-deployment tracking (not model group)

**Configuration**:

```python
router = Router(
    allowed_fails=1,  # Cooldown if > 1 failure/minute
    cooldown_time=100,  # Cooldown for 100 seconds
)
```

**Cooldown Triggers**:

- Rate Limiting (429): Immediate 5s cooldown
- High Failure Rate (>50% failures): 5s cooldown
- Non-Retryable Errors (401, 404, 408): 5s cooldown

### Fallback Chains

**Configuration**:

```python
fallbacks = [{"gpt-4": ["gpt-3.5-turbo", "deepseek-v3.2"]}, {"claude-opus-4.6": ["claude-sonnet-4.5", "glm-5"]}]

router = Router(
    model_list=model_list,
    fallbacks=fallbacks,
    max_fallbacks=5,  # Max fallbacks to try
)
```

**Types**:

- **Generic Fallbacks**: Model → Alternative models
- **Context Window Fallbacks**: For prompts too large
- **Content Policy Fallbacks**: For content violations

---

## Caching

### In-Memory Cache

**Configuration**:

```python
router = Router(
    cache_responses=True  # Uses in-memory cache
)
```

**Use Case**: Local development, single instance

### Redis Cache

**Configuration**:

```python
router = Router(cache_responses=True, redis_url="redis://localhost:6379")
```

**Use Case**: Production, multiple instances

### Cache Groups

**Configuration**:

```python
router = Router(cache_responses=True, caching_groups=[("openai-gpt-3.5-turbo", "azure-gpt-3.5-turbo")])
```

**Use Case**: Cache across model groups (e.g., Azure + OpenAI)

---

## Cost Tracking

### Per-Deployment Cost Tracking

**How it works**:

- Tracks cost per deployment automatically
- Uses pricing from `model_prices_and_context_window.json`
- Can set custom pricing via `model_info["base_model"]`

**Access**:

```python
# In custom callback
def log_success_event(self, kwargs, response_obj, start_time, end_time):
    response_cost = kwargs.get("response_cost")
    print(f"Cost: ${response_cost}")
```

### Budget Limits

**Configuration**:

```python
provider_budget_config = {
    "openai": {"budget": 100.0, "budget_duration": "1d"},
    "anthropic": {"budget": 50.0, "budget_duration": "1d"},
}

router = Router(model_list=model_list, provider_budget_config=provider_budget_config)
```

**Behavior**:

- Tracks spending per provider
- Blocks requests when budget exceeded
- Resets based on `budget_duration`

---

## Pre-Call Checks

### Context Window Validation

**Configuration**:

```python
router = Router(
    enable_pre_call_checks=True,
    model_list=[
        {
            "model_name": "gpt-3.5-turbo",
            "litellm_params": {
                "model": "azure/chatgpt-v-2",
                "base_model": "azure/gpt-35-turbo",  # For context window check
            },
        }
    ],
)
```

**Behavior**:

- Filters out deployments with context window < prompt size
- Leaves 25% buffer for response
- Falls back to larger context window models

### EU Region Filtering

**Configuration**:

```python
model_list = [
    {
        "model_name": "gpt-3.5-turbo",
        "litellm_params": {
            "model": "azure/chatgpt-v-2",
            "region_name": "eu",  # Filter for EU region
        },
    }
]
```

**Behavior**:

- Filters deployments outside EU region
- Automatic inference for Vertex AI, Bedrock, IBM WatsonxAI
- Manual setting for Azure

---

## Observability

### Custom Callbacks

**Usage**:

```python
from litellm.integrations.custom_logger import CustomLogger


class MyCustomHandler(CustomLogger):
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        api_key = kwargs.get("litellm_params", {}).get("api_key")
        api_base = kwargs.get("litellm_params", {}).get("api_base")
        model = kwargs.get("model")
        cost = kwargs.get("response_cost")
        print(f"Model: {model}, Cost: ${cost}, Base: {api_base}")


customHandler = MyCustomHandler()
litellm.callbacks = [customHandler]
```

### Alerting

**Configuration**:

```python
from litellm.router import AlertingConfig

router = Router(
    model_list=model_list,
    alerting_config=AlertingConfig(
        alerting_threshold=10,  # Alert after 10 errors
        webhook_url="https://hooks.slack.com/...",
    ),
)
```

**Alerts On**:

- Slow LLM responses (> threshold)
- LLM API exceptions
- Budget exceeded

---

## Model Configuration

### Model List Structure

```python
model_list = [
    {
        "model_name": "gpt-3.5-turbo",  # Alias (used in requests)
        "litellm_params": {
            "model": "azure/chatgpt-v-2",  # Actual model
            "api_key": os.getenv("AZURE_API_KEY"),
            "api_base": os.getenv("AZURE_API_BASE"),
            "api_version": os.getenv("AZURE_API_VERSION"),
            "rpm": 900,  # Requests per minute
            "tpm": 100000,  # Tokens per minute
            "max_parallel_requests": 10,
        },
        "model_info": {
            "base_model": "azure/gpt-35-turbo",  # For cost tracking
            "context_window": 16384,  # Optional override
        },
    }
]
```

### Deployment Ordering (Priority)

```python
model_list = [
    {
        "model_name": "gpt-4",
        "litellm_params": {
            "model": "azure/gpt-4-primary",
            "order": 1,  # Highest priority
        },
    },
    {
        "model_name": "gpt-4",
        "litellm_params": {
            "model": "azure/gpt-4-fallback",
            "order": 2,  # Used when order=1 unavailable
        },
    },
]

router = Router(
    model_list=model_list,
    enable_pre_call_checks=True,  # Required for 'order' to work
)
```

### Weighted Deployments

```python
model_list = [
    {"model_name": "o1", "litellm_params": {"model": "o1-preview", "weight": 1}},
    {
        "model_name": "o1",
        "litellm_params": {
            "model": "o1-preview",
            "weight": 2,  # Picked 2x more often
        },
    },
]
```

---

## Responses API Support

### Current Status

**LiteLLM Router does NOT natively support Responses API format**

**Why**: LiteLLM Router uses Chat Completions format internally

### Solution

**Adapter Layer Approach**:

1. Accept Responses API requests
2. Translate to Chat Completions format
3. Route through LiteLLM Router
4. Translate responses back to Responses API format

**Reference**: codex-proxy does similar translation for Gemini/Z.AI

---

## Performance Characteristics

### Benchmarks

- **8ms P95 latency** at 1k RPS
- **Proven at Netflix scale**
- **Minimal overhead** with `simple-shuffle` strategy

### Optimization Tips

1. **Use Redis cache** for production (shared across instances)
2. **Enable pre-call checks** to avoid failed requests
3. **Set RPM/TPM limits** to prevent rate limiting
4. **Use fallback chains** for reliability
5. **Monitor deployment health** via callbacks

---

## Comparison with CLIProxyAPIPlus

| Feature            | LiteLLM Router       | CLIProxyAPIPlus |
| ------------------ | -------------------- | --------------- |
| Routing Strategies | 6 strategies         | Basic routing   |
| Load Balancing     | ✅ Advanced          | ✅ Basic        |
| Caching            | ✅ Redis + In-Memory | ❌ No           |
| Cost Tracking      | ✅ Built-in          | ❌ No           |
| Fallback Chains    | ✅ Automatic         | ⚠️ Manual       |
| Provider Support   | 100+ providers       | Limited         |
| Responses API      | ❌ Via adapter       | ✅ Native       |
| WebSocket          | ❌ Via adapter       | ✅ Native       |
| Performance        | 8ms P95 @ 1k RPS     | Unknown         |

**Verdict**: LiteLLM Router is superior for routing, but needs adapter for Responses API support.

---

## Integration Approach

### Option 1: LiteLLM Router with Adapter (Recommended)

**Architecture**:

```
Codex CLI → Adapter (Responses API) → LiteLLM Router → Providers
```

**Pros**:

- Leverages LiteLLM Router features
- Single routing layer
- Better performance and reliability

**Cons**:

- Requires adapter layer
- Additional translation step

### Option 2: Enhance CLIProxyAPIPlus

**Architecture**:

```
Codex CLI → CLIProxyAPIPlus → LiteLLM Router → Providers
```

**Pros**:

- Native Responses API support
- No translation needed

**Cons**:

- Double routing layer
- CLIProxyAPIPlus becomes unnecessary wrapper

**Verdict**: Option 1 is better - adapter is simpler than maintaining CLIProxyAPIPlus wrapper.

---

## Key Takeaways

1. **LiteLLM Router is production-ready** (Netflix-scale proven)
2. **Responses API support requires adapter** (translation layer)
3. **Router provides advanced features** (caching, fallback, cost tracking)
4. **Simple-shuffle is recommended** for best performance
5. **Adapter approach is cleaner** than enhancing CLIProxyAPIPlus

---

## References

- [LiteLLM Router Documentation](https://docs.litellm.ai/docs/routing)
- [LiteLLM GitHub Repository](https://github.com/BerriAI/litellm)
- [codex-proxy Reference](https://github.com/cornellsh/codex-proxy)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
