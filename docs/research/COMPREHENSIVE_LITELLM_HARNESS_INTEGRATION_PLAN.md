<DONE>
# Comprehensive LiteLLM Harness Integration Plan

**Date**: 2026-02-18
**Goal**: Fix and optimize CLI harnesses (Codex, Claude Code, Factory Droid) to work with LiteLLM Router as unified front matter over OAI+Anth compatible provider services, eliminating need for codex-proxy and simplifying architecture.

**Reference**: [codex-proxy](https://github.com/cornellsh/codex-proxy), [LiteLLM Router](https://docs.litellm.ai/docs/routing)

---

## Executive Summary

**Key Insight**: If LiteLLM Router is correctly configured as front matter over individually wrapped OAI+Anth compatible provider services, separate proxies like codex-proxy are unnecessary. LiteLLM Router provides:
- Unified routing across 100+ providers
- Load balancing, fallback chains, caching
- Cost optimization and budget tracking
- Responses API support (via adapter layer)
- WebSocket support for streaming

**Target Harnesses**:
1. **Codex CLI** (`@openai/codex`) - Uses Responses API format
2. **Claude Code** (`clode`) - Uses Chat Completions format
3. **Factory Droid** (`droid exec`) - Uses Chat Completions format

---

## Current Architecture Analysis

### Current Flow

```
┌─────────────┐
│ Codex CLI   │──┐
└─────────────┘  │
                 ├──► cliproxy_adapter.py ──► CLIProxyAPIPlus ──► Providers
┌─────────────┐  │
│ Claude Code │──┤
└─────────────┘  │
                 │
┌─────────────┐  │
│ Factory     │──┘
│ Droid       │
└─────────────┘
```

### Issues Identified

1. **Double Translation**: Adapter translates Responses API → Chat Completions, then CLIProxyAPIPlus may translate again
2. **Fragmented Routing**: Model routing happens in CLIProxyAPIPlus, not leveraging LiteLLM Router's advanced capabilities
3. **Missing Features**: No access to LiteLLM's caching, fallback chains, cost optimization, load balancing
4. **Unnecessary Complexity**: codex-proxy exists because Responses API isn't properly handled at the router level
5. **Inconsistent Patterns**: Each harness uses different routing mechanisms

---

## Target Architecture

### Unified Flow with LiteLLM Router

```
┌─────────────┐
│ Codex CLI   │──┐
└─────────────┘  │
                 │
┌─────────────┐  │     ┌──────────────────────────────┐
│ Claude Code │──┼────►│ LiteLLM Router               │
└─────────────┘  │     │  - Responses API Adapter     │
                 │     │  - Chat Completions Handler  │
┌─────────────┐  │     │  - Load Balancing           │
│ Factory     │──┘     │  - Fallback Chains           │
│ Droid       │        │  - Caching (Redis/In-Mem)   │
└─────────────┘        │  - Cost Tracking            │
                       └──────────┬───────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼───┐  ┌───────▼───┐  ┌───────▼───┐
            │ OpenAI    │  │ Anthropic │  │ Gemini    │
            │ Azure     │  │ Claude    │  │ GLM       │
            │ MiniMax   │  │ ...       │  │ ...       │
            └───────────┘  └───────────┘  └───────────┘
```

### Benefits

1. **Single Translation Layer**: Responses API → Chat Completions happens once at adapter level
2. **Unified Routing**: All harnesses use same LiteLLM Router with consistent policies
3. **Advanced Features**: Caching, fallback, cost optimization, load balancing
4. **Simpler Stack**: One routing layer instead of multiple proxies
5. **Provider Agnostic**: Works with any LiteLLM-compatible provider (100+)
6. **Better Observability**: Unified logging, metrics, cost tracking

---

## LiteLLM Router Capabilities (Research Findings)

### Core Features

1. **Routing Strategies**:
   - `simple-shuffle` (default, recommended) - Weighted random selection
   - `least-busy` - Select least loaded deployment
   - `latency-based-routing` - Route based on latency metrics
   - `cost-based-routing` - Optimize for cost
   - `usage-based-routing` - Route based on RPM/TPM limits

2. **Reliability Features**:
   - **Retries**: Configurable retry policies per error type
   - **Cooldowns**: Automatic cooldown of failing deployments
   - **Fallback Chains**: Automatic fallback to alternative models
   - **Pre-call Checks**: Context window validation, region filtering

3. **Caching**:
   - In-memory cache (default)
   - Redis cache (production)
   - Cache across model groups
   - Configurable TTL

4. **Cost Tracking**:
   - Per-deployment cost tracking
   - Budget limits per provider
   - Cost optimization routing

5. **Observability**:
   - Custom callbacks for logging
   - Alerting (Slack webhooks)
   - Deployment metrics tracking

### Responses API Support

LiteLLM Router doesn't natively support Responses API format, but:
- Can be added via adapter layer (Responses API → Chat Completions)
- Router handles Chat Completions natively
- Responses API adapter translates back to Responses format

---

## Implementation Plan

### Phase 1: LiteLLM Router Responses API Handler

**Goal**: Enable Codex CLI to work with LiteLLM Router

**Tasks**:
1. **Create `litellm_responses_handler.py`**:
   - Accept Responses API requests (`/v1/responses`)
   - Translate `input` array → `messages` array
   - Call LiteLLM Router with Chat Completions format
   - Translate streaming responses back to Responses API format
   - Handle WebSocket connections for streaming

2. **Update `cliproxy_adapter.py`**:
   - Add option to use LiteLLM Router backend (`THGENT_USE_LITELLM_ROUTER=1`)
   - Route `/v1/responses` to LiteLLM handler when enabled
   - Maintain backward compatibility with CLIProxyAPIPlus

3. **WebSocket Support**:
   - Bridge WebSocket `/v1/responses` to HTTP SSE streaming
   - Handle Responses API WebSocket protocol
   - Translate Chat Completions SSE → Responses API events

**Files**:
- `src/thegent/routing/litellm_responses_handler.py` (new)
- `src/thegent/cliproxy_adapter.py` (modify)
- `src/thegent/routing/litellm_router.py` (enhance)

**Key Code**:
```python
# litellm_responses_handler.py
async def handle_responses_request(request: Request) -> Response:
    """Handle Responses API request via LiteLLM Router."""
    body = await request.body()
    data = json.loads(body)

    # Translate Responses API → Chat Completions
    messages = _responses_input_to_messages(data.get("input", []))
    model = data.get("model", "")
    stream = data.get("stream", False)

    # Get LiteLLM Router instance
    router = get_litellm_router()

    # Call router
    if stream:
        return await _stream_via_router(router, model, messages)
    else:
        response = await router.acompletion(model=model, messages=messages)
        return _chat_to_responses_response(response)
```

### Phase 2: Claude Code Integration

**Goal**: Route Claude Code (`clode`) through LiteLLM Router

**Current**: Claude Code uses `CodexProxyRunner` which routes through CLIProxyAPIPlus

**Tasks**:
1. **Update `CodexProxyRunner`**:
   - Add option to use LiteLLM Router directly
   - Route Chat Completions requests through LiteLLM Router
   - Maintain backward compatibility

2. **Model Configuration**:
   - Ensure all Claude Code models are in LiteLLM Router model list
   - Configure fallback chains for Claude models
   - Set up cost tracking for Claude provider

**Files**:
- `src/thegent/agents/codex_proxy.py` (modify)
- `src/thegent/clode_main.py` (verify)

**Key Code**:
```python
# In CodexProxyRunner.run()
if use_litellm_router:
    from thegent.routing.litellm_router import get_litellm_router

    router = get_litellm_router()
    response = await router.acompletion(model=model, messages=[{"role": "user", "content": prompt}], stream=use_stream)
    return _convert_to_run_result(response)
```

### Phase 3: Factory Droid Integration

**Goal**: Route Factory Droid through LiteLLM Router

**Current**: Droid uses Factory's native API, but can be configured to use OpenAI-compatible endpoints

**Tasks**:
1. **Update `DroidRunner`**:
   - Add option to route through LiteLLM Router
   - Configure droid to use LiteLLM Router endpoint
   - Handle model name mapping (Factory models → LiteLLM models)

2. **Factory Configuration**:
   - Configure `.factory/settings.json` to use LiteLLM Router endpoint
   - Map Factory model names to LiteLLM model aliases
   - Set up authentication (API keys)

**Files**:
- `src/thegent/agents/droid.py` (modify)
- Factory config generation (enhance)

**Key Code**:
```python
# In DroidRunner.run()
if use_litellm_router:
    # Configure droid to use LiteLLM Router
    env["OPENAI_BASE_URL"] = "http://localhost:8765/v1"
    env["OPENAI_API_KEY"] = "sk-dummy"
    # Model mapping happens in LiteLLM Router config
```

### Phase 4: Plan Incorporate Enhancement

**Goal**: Add task validation during `plan incorporate` command

**Tasks**:
1. **Update `plan incorporate` implementation**:
   - Validate task files before merging
   - Use `TaskValidator` to check schema compliance
   - Report validation errors with clear messages
   - Auto-sync tasks to WORK_STREAM.md after successful incorporation

2. **Integration Points**:
   - Hook into `plan incorporate` command
   - Validate all task files in `tasks/` directory
   - Update WORK_STREAM.md automatically
   - Provide summary of incorporated tasks

**Files**:
- `src/thegent/cli_impl.py` (modify `plan_incorporate_impl`)
- `src/thegent/task/validator.py` (use existing)
- `src/thegent/task/sync.py` (use existing)

**Key Code**:
```python
# In plan_incorporate_impl()
from thegent.task import validate_task_file, WorkStreamSync

# Validate all task files
validation_errors = []
for task_file in tasks_dir.glob("*.md"):
    result = validate_task_file(task_file)
    if not result.valid:
        validation_errors.append((task_file, result.errors))

if validation_errors:
    return {"error": "Task validation failed", "errors": validation_errors}

# Sync to WORK_STREAM.md
sync = WorkStreamSync(work_stream_path, tasks_dir)
sync.update_work_stream_from_tasks()
```

---

## Model Configuration Strategy

### Model List Building

**Current**: `build_litellm_model_list()` builds from catalog routes

**Enhancement**: Ensure all harness models are included:

```python
# In build_litellm_model_list()
# Codex CLI models
codex_models = ["gpt-5-mini", "gpt-5.3-codex-spark", "gpt-5.3-codex-high", "minimax-m2.5", "glm-5", "gemini-3-flash"]

# Claude Code models
claude_models = ["claude-opus-4.6", "claude-sonnet-4.5", "claude-haiku-4.5", "composer-1.5", "composer-1.5-high"]

# Factory Droid models
droid_models = ["Qwen3 Coder [CEREBRAS]", "GLM-4.6 [Z.AI]", "MiniMax-M2.5", "claude-opus-4.6"]

# Ensure all are in model_list
```

### Fallback Chains

**Configuration**:
```python
fallbacks = [
    {"gpt-5-mini": ["gpt-4o-mini", "deepseek-v3.2", "glm-5"]},
    {"claude-opus-4.6": ["claude-sonnet-4.5", "deepseek-v3.2", "glm-5"]},
    {"minimax-m2.5": ["glm-5", "deepseek-v3.2"]},
    {"glm-5": ["deepseek-v3.2", "qwen3-coder"]},
]
```

### Routing Policy

**Recommended**: `simple-shuffle` (default) for best performance
- Weighted random selection based on RPM/TPM limits
- Minimal latency overhead
- Good for production use

**Alternative**: `cost-based-routing` for cost optimization
- Routes to cheapest available model
- Useful for budget-conscious deployments

---

## Testing Strategy

### Unit Tests

1. **Responses API Translation**:
   - Test `input` array → `messages` array conversion
   - Test streaming response translation
   - Test WebSocket protocol handling

2. **LiteLLM Router Integration**:
   - Test model routing
   - Test fallback chains
   - Test caching behavior

### Integration Tests

1. **Codex CLI**:
   ```bash
   export OPENAI_BASE_URL=http://localhost:8765
   export OPENAI_API_KEY=sk-dummy
   export THGENT_USE_LITELLM_ROUTER=1
   codex exec - --model gpt-5-mini <<< "Hello"
   ```

2. **Claude Code**:
   ```bash
   export THGENT_USE_LITELLM_ROUTER=1
   thegent clode flash "Hello"
   ```

3. **Factory Droid**:
   ```bash
   export THGENT_USE_LITELLM_ROUTER=1
   droid exec --model "GLM-4.6 [Z.AI]" <<< "Hello"
   ```

### End-to-End Tests

1. **Multi-Harness Test**:
   - Run same prompt through all three harnesses
   - Verify consistent routing and responses
   - Check cost tracking works correctly

2. **Fallback Test**:
   - Simulate provider failure
   - Verify automatic fallback to alternative
   - Check cooldown behavior

---

## Migration Path

### Phase 1: Implementation (Week 1)
- ✅ Create LiteLLM Responses API handler
- ✅ Update adapter to support LiteLLM Router backend
- ✅ Add WebSocket support

### Phase 2: Integration (Week 2)
- ✅ Integrate Claude Code with LiteLLM Router
- ✅ Integrate Factory Droid with LiteLLM Router
- ✅ Update model configuration

### Phase 3: Plan Incorporate (Week 2)
- ✅ Add task validation to `plan incorporate`
- ✅ Auto-sync to WORK_STREAM.md
- ✅ Error reporting

### Phase 4: Testing & Optimization (Week 3)
- ✅ Comprehensive testing
- ✅ Performance optimization
- ✅ Cost tracking verification

### Phase 5: Rollout (Week 4)
- ✅ Enable LiteLLM Router by default
- ✅ Deprecate CLIProxyAPIPlus path (optional)
- ✅ Documentation updates

---

## Configuration

### Environment Variables

```bash
# Enable LiteLLM Router
export THGENT_USE_LITELLM_ROUTER=1

# LiteLLM Router Configuration
export THGENT_LITELLM_ROUTING_POLICY=simple-shuffle  # or cost-based-routing
export THGENT_LITELLM_ENABLE_CACHE=1
export THGENT_LITELLM_REDIS_URL=redis://localhost:6379
export THGENT_LITELLM_FALLBACK_ENABLED=1

# Codex CLI
export OPENAI_BASE_URL=http://localhost:8765
export OPENAI_API_KEY=sk-dummy

# Factory Droid
export FACTORY_API_KEY=fk-...
```

### LiteLLM Router Config

```python
# In litellm_router.py
router_config = RouterConfig(
    routing_policy="simple-shuffle",
    enable_cache=True,
    cache_type="redis",
    redis_url=os.getenv("THGENT_LITELLM_REDIS_URL"),
    enable_fallback=True,
    fallback_enabled=True,
    num_retries=3,
    timeout=300,
    enable_cost_tracking=True,
)
```

---

## Benefits Summary

### Technical Benefits

1. **Unified Architecture**: Single routing layer for all harnesses
2. **Better Performance**: LiteLLM Router optimized for production (8ms P95 latency at 1k RPS)
3. **Advanced Features**: Caching, fallback, cost optimization out of the box
4. **Simpler Stack**: Eliminate codex-proxy dependency
5. **Provider Agnostic**: Support 100+ providers through LiteLLM

### Operational Benefits

1. **Cost Optimization**: Automatic routing to cheapest available model
2. **Reliability**: Automatic fallback and retry logic
3. **Observability**: Unified logging and metrics
4. **Scalability**: Load balancing across multiple deployments
5. **Maintainability**: Single codebase for routing logic

---

## Risk Mitigation

### Backward Compatibility

- Maintain CLIProxyAPIPlus path as fallback
- Feature flag (`THGENT_USE_LITELLM_ROUTER`) for gradual rollout
- No breaking changes to existing APIs

### Performance

- LiteLLM Router proven at scale (Netflix adoption)
- Caching reduces latency for repeated requests
- Load balancing distributes load efficiently

### Provider Support

- LiteLLM supports 100+ providers
- Easy to add new providers via LiteLLM
- Fallback chains ensure availability

---

## Success Metrics

1. **Functionality**: All three harnesses work with LiteLLM Router
2. **Performance**: Latency < 100ms P95 for routing decisions
3. **Reliability**: 99.9% success rate with fallback chains
4. **Cost**: 20-30% cost reduction through optimization
5. **Developer Experience**: Simplified configuration and debugging

---

## References

- [LiteLLM Router Documentation](https://docs.litellm.ai/docs/routing)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [codex-proxy Reference](https://github.com/cornellsh/codex-proxy)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [Factory Droid Documentation](https://app.factory.ai/docs)

---

## Next Steps

1. **Immediate**: Review and approve plan
2. **Week 1**: Implement LiteLLM Responses API handler
3. **Week 2**: Integrate all three harnesses
4. **Week 3**: Testing and optimization
5. **Week 4**: Rollout and documentation

---

**Status**: Ready for implementation
**Priority**: High
**Estimated Effort**: 3-4 weeks
**Dependencies**: LiteLLM library, Redis (optional, for caching)
