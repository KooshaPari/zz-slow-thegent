<DONE>
# LiteLLM Harness Integration - Master Plan & Research

**Date**: 2026-02-18
**Status**: Planning Complete - Ready for Implementation
**Goal**: Unify Codex CLI, Claude Code, and Factory Droid harnesses through LiteLLM Router

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Research Findings](#research-findings)
3. [Architecture Design](#architecture-design)
4. [Implementation Plan](#implementation-plan)
5. [Technical Specifications](#technical-specifications)
6. [Testing Strategy](#testing-strategy)
7. [Migration Path](#migration-path)
8. [Risk Assessment](#risk-assessment)

---

## Executive Summary

### Problem Statement

Currently, three different CLI harnesses (Codex CLI, Claude Code, Factory Droid) use fragmented routing mechanisms:

- Codex CLI → `cliproxy_adapter.py` → CLIProxyAPIPlus → Providers
- Claude Code → `CodexProxyRunner` → CLIProxyAPIPlus → Providers
- Factory Droid → Factory API → Providers

**Issues**:

- Double translation layers
- No unified routing, caching, or cost optimization
- codex-proxy exists as workaround for Responses API handling
- Inconsistent patterns across harnesses

### Solution

Unify all harnesses through **LiteLLM Router** as single front matter:

- Single translation layer (Responses API → Chat Completions)
- Unified routing with advanced features (load balancing, fallback, caching)
- Cost optimization and budget tracking
- Provider agnostic (100+ providers supported)

### Key Insight

**If LiteLLM Router is correctly configured as front matter over individually wrapped OAI+Anth compatible provider services, separate proxies like codex-proxy are unnecessary.**

### Research Foundation

This plan is based on comprehensive research of:

- **OpenRouter** (commercial, industry-leading) - 300+ models, smart routing, guardrails, broadcast
- **LiteLLM Router** (OSS, Netflix-proven) - 100+ providers, load balancing, caching
- **Advanced routing strategies** - Intent-based, complexity-based, cascade routing
- **Enterprise features** - Guardrails, observability, cost optimization

See `ADVANCED_ROUTER_RESEARCH.md` for complete analysis.

---

## Research Findings

### LiteLLM Router Capabilities

#### 1. Routing Strategies

**Source**: [LiteLLM Router Documentation](https://docs.litellm.ai/docs/routing)

| Strategy                | Description                                | Use Case                     | Performance                       |
| ----------------------- | ------------------------------------------ | ---------------------------- | --------------------------------- |
| `simple-shuffle`        | Weighted random selection based on RPM/TPM | **Production (Recommended)** | Best performance, minimal latency |
| `least-busy`            | Select least loaded deployment             | High traffic scenarios       | Good for load distribution        |
| `latency-based-routing` | Route based on latency metrics             | Performance critical         | Requires metrics collection       |
| `cost-based-routing`    | Optimize for cost                          | Budget conscious             | Routes to cheapest model          |
| `usage-based-routing`   | Route based on RPM/TPM limits              | Rate limit management        | Prevents hitting limits           |

**Recommendation**: Use `simple-shuffle` as default (proven at Netflix scale, 8ms P95 latency at 1k RPS)

#### 2. Reliability Features

**Retries**:

- Configurable retry policies per error type
- Exponential backoff for rate limits
- Immediate retry for generic errors
- Custom retry policies via `RetryPolicy` class

**Cooldowns**:

- Automatic cooldown of failing deployments
- Configurable `allowed_fails` per minute
- Cooldown duration configurable
- Per-deployment tracking (not model group)

**Fallback Chains**:

- Automatic fallback to alternative models
- Context window fallbacks
- Content policy fallbacks
- Configurable max fallbacks (default: 5)

**Pre-Call Checks**:

- Context window validation
- EU region filtering
- Rate limit checking
- Budget limit checking

#### 3. Caching

**Types**:

- **In-Memory Cache**: Default, fast, local to process
- **Redis Cache**: Production-ready, shared across instances
- **Cache Groups**: Cache across model groups (e.g., Azure + OpenAI)

**Configuration**:

```python
router = Router(
    cache_responses=True,
    redis_url="redis://localhost:6379",  # Optional
    caching_groups=[("openai-gpt-3.5-turbo", "azure-gpt-3.5-turbo")],
)
```

#### 4. Cost Tracking

**Features**:

- Per-deployment cost tracking
- Budget limits per provider
- Cost optimization routing
- Custom pricing support

**Usage**:

```python
router = Router(
    provider_budget_config={
        "openai": {"budget": 100.0, "budget_duration": "1d"},
        "anthropic": {"budget": 50.0, "budget_duration": "1d"},
    }
)
```

#### 5. Observability

**Custom Callbacks**:

- Track API key, endpoint, model used
- Log success/failure events
- Custom logging integrations

**Alerting**:

- Slack webhook support
- Alert on slow responses
- Alert on API exceptions
- Configurable thresholds

### codex-proxy Reference Implementation

**Source**: [codex-proxy GitHub](https://github.com/cornellsh/codex-proxy)

**What it does**:

1. Accepts Responses API format (`/v1/responses`)
2. Translates to Gemini/Z.AI APIs
3. Handles SSE streaming
4. Supports context compaction
5. Model routing

**Key Learning**: codex-proxy translates Responses API directly to provider APIs. Our approach: Translate Responses API → Chat Completions → LiteLLM Router → Providers.

**Why we don't need it**: LiteLLM Router handles routing, and our adapter handles Responses API translation.

### Current Architecture Analysis

#### Codex CLI Flow

```
Codex CLI
  ↓ (Responses API format)
cliproxy_adapter.py
  ↓ (Translates to Chat Completions)
CLIProxyAPIPlus (port 8317)
  ↓ (Routes to provider)
Provider (OpenAI, Anthropic, etc.)
```

**Issues**:

- Double translation (adapter + CLIProxyAPIPlus)
- No caching
- No cost optimization
- No unified fallback chains

#### Claude Code Flow

```
Claude Code (clode)
  ↓ (Chat Completions format)
CodexProxyRunner
  ↓ (Sets OPENAI_BASE_URL to proxy)
CLIProxyAPIPlus
  ↓ (Routes to provider)
Provider
```

**Issues**:

- Uses Codex proxy even though it's Claude Code
- No direct LiteLLM Router integration
- Same limitations as Codex CLI

#### Factory Droid Flow

```
Factory Droid (droid exec)
  ↓ (Chat Completions format)
Factory API
  ↓ (Routes to provider)
Provider
```

**Issues**:

- Separate routing mechanism
- No integration with thegent routing
- Can't leverage LiteLLM Router features

---

## Architecture Design

### Target Unified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Harnesses                             │
├──────────────┬──────────────┬───────────────────────────────┤
│ Codex CLI    │ Claude Code  │ Factory Droid                 │
│ (Responses)  │ (Chat)       │ (Chat)                        │
└──────┬───────┴──────┬───────┴───────────────┬───────────────┘
       │              │                       │
       │              │                       │
       ▼              ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Translation Layer                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ litellm_responses_handler.py                        │   │
│  │ - Responses API → Chat Completions                  │   │
│  │ - Chat Completions → Responses API                  │   │
│  │ - WebSocket support                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LiteLLM Router                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ - Routing Strategy (simple-shuffle)                  │   │
│  │ - Load Balancing                                     │   │
│  │ - Fallback Chains                                    │   │
│  │ - Caching (Redis/In-Memory)                          │   │
│  │ - Cost Tracking                                      │   │
│  │ - Retry Logic                                        │   │
│  │ - Cooldown Management                                │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Providers (100+ via LiteLLM)                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ OpenAI   │ Anthropic│ Gemini   │ GLM      │ MiniMax  │  │
│  │ Azure    │ Claude   │ Vertex   │ Z.AI     │ ...      │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Design

#### 1. LiteLLM Responses API Handler

**File**: `src/thegent/routing/litellm_responses_handler.py` (new)

**Responsibilities**:

- Accept Responses API requests (`/v1/responses`)
- Translate `input` array → `messages` array
- Call LiteLLM Router
- Translate streaming responses back to Responses API format
- Handle WebSocket connections

**Key Functions**:

```python
async def handle_responses_request(request: Request) -> Response
async def handle_responses_stream(request: Request) -> StreamingResponse
async def handle_responses_websocket(websocket: WebSocket) -> None
def _responses_to_chat_completions(data: dict) -> dict
def _chat_completions_to_responses(chunk: dict) -> dict | None
```

#### 2. Adapter Enhancement

**File**: `src/thegent/cliproxy_adapter.py` (modify)

**Changes**:

- Add `THGENT_USE_LITELLM_ROUTER` environment variable check
- Route `/v1/responses` to LiteLLM handler when enabled
- Maintain backward compatibility with CLIProxyAPIPlus

**Key Changes**:

```python
async def proxy_handler(request: Request) -> Response:
    use_litellm = os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1"

    if use_litellm and path == "/v1/responses":
        from thegent.routing.litellm_responses_handler import handle_responses_request

        return await handle_responses_request(request)

    # Fallback to CLIProxyAPIPlus
    ...
```

#### 3. CodexProxyRunner Enhancement

**File**: `src/thegent/agents/codex_proxy.py` (modify)

**Changes**:

- Add option to use LiteLLM Router directly
- Route Chat Completions requests through LiteLLM Router
- Maintain backward compatibility

#### 4. DroidRunner Enhancement

**File**: `src/thegent/agents/droid.py` (modify)

**Changes**:

- Add option to route through LiteLLM Router
- Configure droid to use LiteLLM Router endpoint
- Handle model name mapping

#### 5. Plan Incorporate Enhancement

**File**: `src/thegent/cli_impl.py` (modify)

**Changes**:

- Add task validation during incorporation
- Use `TaskValidator` to check schema compliance
- Auto-sync to WORK_STREAM.md after successful incorporation
- Report validation errors clearly

---

## Implementation Plan

### Phase 1: LiteLLM Router Responses API Handler

**Goal**: Enable Codex CLI to work with LiteLLM Router

**Tasks**:

1. **Create `litellm_responses_handler.py`**
   - [ ] Implement `handle_responses_request()` for HTTP POST
   - [ ] Implement `handle_responses_stream()` for SSE streaming
   - [ ] Implement `handle_responses_websocket()` for WebSocket
   - [ ] Add translation functions (`_responses_to_chat_completions`, `_chat_completions_to_responses`)
   - [ ] Integrate with LiteLLM Router
   - [ ] Handle error cases and edge cases

2. **Update `cliproxy_adapter.py`**
   - [ ] Add `THGENT_USE_LITELLM_ROUTER` environment variable check
   - [ ] Route `/v1/responses` to LiteLLM handler when enabled
   - [ ] Maintain backward compatibility
   - [ ] Update WebSocket handler

3. **Update `litellm_router.py`**
   - [ ] Ensure router can be accessed from handler
   - [ ] Add helper function to get router instance
   - [ ] Verify model list includes Codex CLI models

**Files to Create**:

- `src/thegent/routing/litellm_responses_handler.py`

**Files to Modify**:

- `src/thegent/cliproxy_adapter.py`
- `src/thegent/routing/litellm_router.py`

**Testing**:

- [ ] Test HTTP POST `/v1/responses` endpoint
- [ ] Test SSE streaming
- [ ] Test WebSocket connections
- [ ] Test model routing
- [ ] Test error handling

### Phase 2: Claude Code Integration

**Goal**: Route Claude Code (`clode`) through LiteLLM Router

**Tasks**:

1. **Update `CodexProxyRunner`**
   - [ ] Add `use_litellm_router` parameter
   - [ ] Implement direct LiteLLM Router integration
   - [ ] Handle Chat Completions format (no translation needed)
   - [ ] Maintain backward compatibility

2. **Update `clode_main.py`**
   - [ ] Add option to use LiteLLM Router
   - [ ] Update model configuration
   - [ ] Verify routing works correctly

3. **Model Configuration**
   - [ ] Ensure all Claude Code models in LiteLLM Router model list
   - [ ] Configure fallback chains for Claude models
   - [ ] Set up cost tracking

**Files to Modify**:

- `src/thegent/agents/codex_proxy.py`
- `src/thegent/clode_main.py`
- `src/thegent/routing/litellm_router.py`

**Testing**:

- [ ] Test `thegent clode flash "Hello"`
- [ ] Test model routing
- [ ] Test fallback chains
- [ ] Test cost tracking

### Phase 3: Factory Droid Integration

**Goal**: Route Factory Droid through LiteLLM Router

**Tasks**:

1. **Update `DroidRunner`**
   - [ ] Add option to route through LiteLLM Router
   - [ ] Configure droid to use LiteLLM Router endpoint
   - [ ] Handle model name mapping

2. **Factory Configuration**
   - [ ] Update Factory config generation
   - [ ] Map Factory model names to LiteLLM model aliases
   - [ ] Set up authentication

**Files to Modify**:

- `src/thegent/agents/droid.py`
- Factory config generation code

**Testing**:

- [ ] Test `droid exec --model "GLM-4.6 [Z.AI]"`
- [ ] Test model routing
- [ ] Test authentication

### Phase 4: Plan Incorporate Enhancement

**Goal**: Add task validation during `plan incorporate` command

**Tasks**:

1. **Find `plan incorporate` implementation**
   - [ ] Locate `plan_incorporate_impl()` function
   - [ ] Understand current flow
   - [ ] Identify integration points

2. **Add validation**
   - [ ] Import `TaskValidator`
   - [ ] Validate all task files before merging
   - [ ] Collect validation errors
   - [ ] Report errors clearly

3. **Add auto-sync**
   - [ ] Import `WorkStreamSync`
   - [ ] Sync tasks to WORK_STREAM.md after successful incorporation
   - [ ] Provide summary of incorporated tasks

**Files to Modify**:

- `src/thegent/cli_impl.py` (find and modify `plan_incorporate_impl`)

**Testing**:

- [ ] Test with valid task files
- [ ] Test with invalid task files
- [ ] Test auto-sync to WORK_STREAM.md
- [ ] Test error reporting

### Phase 5: Testing & Optimization

**Goal**: Comprehensive testing and performance optimization

**Tasks**:

1. **Unit Tests**
   - [ ] Test Responses API translation
   - [ ] Test LiteLLM Router integration
   - [ ] Test error handling

2. **Integration Tests**
   - [ ] Test Codex CLI end-to-end
   - [ ] Test Claude Code end-to-end
   - [ ] Test Factory Droid end-to-end
   - [ ] Test plan incorporate

3. **Performance Tests**
   - [ ] Measure routing latency
   - [ ] Test caching effectiveness
   - [ ] Test load balancing

4. **Documentation**
   - [ ] Update user documentation
   - [ ] Create migration guide
   - [ ] Document configuration options

---

## Technical Specifications

### Responses API Format

#### Request Format

```json
{
  "model": "gpt-5-mini",
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": [{ "type": "text", "text": "Hello" }]
    }
  ],
  "stream": true,
  "temperature": 0.7,
  "max_output_tokens": 1000
}
```

#### Response Format (Streaming)

```json
{"type": "response.output_item.added", "item": {"type": "message", "role": "assistant", "content": [{"type": "text", "text": "Hello"}]}}
{"type": "response.output_item.added", "item": {"type": "message", "role": "assistant", "content": [{"type": "text", "text": " there"}]}}
{"type": "response.completed"}
```

### Chat Completions Format

#### Request Format

```json
{
  "model": "gpt-5-mini",
  "messages": [{ "role": "user", "content": "Hello" }],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

#### Response Format (Streaming)

```
data: {"choices": [{"delta": {"content": "Hello"}}]}

data: {"choices": [{"delta": {"content": " there"}}]}

data: [DONE]
```

### Translation Logic

#### Responses → Chat Completions

```python
def _responses_to_chat_completions(body: dict[str, Any]) -> dict[str, Any]:
    input_items = body.get("input", [])
    messages = []
    for item in input_items:
        if item.get("type") == "message":
            role = item.get("role", "user")
            content = item.get("content")
            if isinstance(content, list):
                # Extract text from content array
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                content = "".join(text_parts)
            messages.append({"role": role, "content": content})

    return {
        "model": body.get("model", ""),
        "messages": messages,
        "stream": body.get("stream", False),
        "temperature": body.get("temperature"),
        "max_tokens": body.get("max_output_tokens") or body.get("max_tokens"),
    }
```

#### Chat Completions → Responses

```python
def _chat_completions_to_responses(chunk: dict[str, Any]) -> dict[str, Any] | None:
    choices = chunk.get("choices", [])
    if not choices:
        return None
    delta = choices[0].get("delta", {})
    content = delta.get("content", "")
    if not content:
        return None  # Skip empty chunks

    return {
        "type": "response.output_item.added",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
        },
    }
```

### Model Configuration

#### Model List Structure

```python
model_list = [
    {
        "model_name": "gpt-5-mini",  # Alias used by Codex CLI
        "litellm_params": {
            "model": "openai/gpt-4o-mini",  # Actual LiteLLM model
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        "model_info": {
            "base_model": "gpt-4o-mini",  # For cost tracking
        },
    },
    {
        "model_name": "claude-opus-4.6",
        "litellm_params": {
            "model": "anthropic/claude-opus-4-20240229",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
    },
    # ... more models
]
```

#### Fallback Chains

```python
fallbacks = [
    {"gpt-5-mini": ["gpt-4o-mini", "deepseek-v3.2", "glm-5"]},
    {"claude-opus-4.6": ["claude-sonnet-4.5", "deepseek-v3.2", "glm-5"]},
    {"minimax-m2.5": ["glm-5", "deepseek-v3.2"]},
    {"glm-5": ["deepseek-v3.2", "qwen3-coder"]},
]
```

### Router Configuration

```python
router = Router(
    model_list=model_list,
    routing_strategy="simple-shuffle",  # Recommended
    cache_responses=True,
    redis_url=os.getenv("THGENT_LITELLM_REDIS_URL"),  # Optional
    fallbacks=fallbacks,
    num_retries=3,
    timeout=300,
    enable_pre_call_checks=True,
    enable_cost_tracking=True,
    provider_budget_config={
        "openai": {"budget": 100.0, "budget_duration": "1d"},
        "anthropic": {"budget": 50.0, "budget_duration": "1d"},
    },
)
```

---

## Testing Strategy

### Unit Tests

#### Responses API Translation

```python
def test_responses_to_chat_completions():
    """Test Responses API → Chat Completions translation."""
    responses_body = {
        "model": "gpt-5-mini",
        "input": [{"type": "message", "role": "user", "content": [{"type": "text", "text": "Hello"}]}],
        "stream": True,
    }

    chat_body = _responses_to_chat_completions(responses_body)

    assert chat_body["model"] == "gpt-5-mini"
    assert chat_body["messages"] == [{"role": "user", "content": "Hello"}]
    assert chat_body["stream"] is True


def test_chat_completions_to_responses():
    """Test Chat Completions → Responses API translation."""
    chat_chunk = {"choices": [{"delta": {"content": "Hello"}}]}

    responses_event = _chat_completions_to_responses(chat_chunk)

    assert responses_event["type"] == "response.output_item.added"
    assert responses_event["item"]["content"][0]["text"] == "Hello"
```

#### LiteLLM Router Integration

```python
async def test_litellm_router_integration():
    """Test LiteLLM Router integration."""
    router = get_litellm_router()

    response = await router.acompletion(model="gpt-5-mini", messages=[{"role": "user", "content": "Hello"}])

    assert response.choices[0].message.content is not None
```

### Integration Tests

#### Codex CLI

```bash
# Test HTTP POST
curl -X POST http://localhost:8765/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-dummy" \
  -d '{
    "model": "gpt-5-mini",
    "input": [{"type": "message", "role": "user", "content": [{"type": "text", "text": "Hello"}]}],
    "stream": false
  }'

# Test Codex CLI
export OPENAI_BASE_URL=http://localhost:8765
export OPENAI_API_KEY=sk-dummy
export THGENT_USE_LITELLM_ROUTER=1
codex exec - --model gpt-5-mini <<< "Hello"
```

#### Claude Code

```bash
export THGENT_USE_LITELLM_ROUTER=1
thegent clode flash "Hello"
```

#### Factory Droid

```bash
export THGENT_USE_LITELLM_ROUTER=1
droid exec --model "GLM-4.6 [Z.AI]" <<< "Hello"
```

### End-to-End Tests

```python
async def test_multi_harness_routing():
    """Test routing consistency across all harnesses."""
    # Same prompt through all three harnesses
    prompt = "Hello, world!"

    # Codex CLI
    codex_result = await codex_cli_execute(prompt, model="gpt-5-mini")

    # Claude Code
    claude_result = await claude_code_execute(prompt, model="flash")

    # Factory Droid
    droid_result = await droid_execute(prompt, model="GLM-4.6 [Z.AI]")

    # All should route through LiteLLM Router
    assert all_used_litellm_router(codex_result, claude_result, droid_result)
```

---

## Migration Path

### Phase 1: Implementation (Week 1)

- ✅ Create LiteLLM Responses API handler
- ✅ Update adapter to support LiteLLM Router backend
- ✅ Add WebSocket support
- ✅ Unit tests

### Phase 2: Integration (Week 2)

- ✅ Integrate Claude Code with LiteLLM Router
- ✅ Integrate Factory Droid with LiteLLM Router
- ✅ Update model configuration
- ✅ Integration tests

### Phase 3: Plan Incorporate (Week 2)

- ✅ Add task validation to `plan incorporate`
- ✅ Auto-sync to WORK_STREAM.md
- ✅ Error reporting
- ✅ Tests

### Phase 4: Testing & Optimization (Week 3)

- ✅ Comprehensive testing
- ✅ Performance optimization
- ✅ Cost tracking verification
- ✅ Documentation

### Phase 5: Rollout (Week 4)

- ✅ Enable LiteLLM Router by default (feature flag)
- ✅ Monitor performance and errors
- ✅ Gather feedback
- ✅ Deprecate CLIProxyAPIPlus path (optional)

### Rollback Plan

- Feature flag `THGENT_USE_LITELLM_ROUTER=0` disables LiteLLM Router
- Falls back to CLIProxyAPIPlus automatically
- No breaking changes to existing APIs

---

## Risk Assessment

### Technical Risks

| Risk                              | Impact | Probability | Mitigation                                |
| --------------------------------- | ------ | ----------- | ----------------------------------------- |
| LiteLLM Router performance issues | High   | Low         | Feature flag, fallback to CLIProxyAPIPlus |
| Responses API translation bugs    | Medium | Medium      | Comprehensive testing, code review        |
| Model routing errors              | Medium | Low         | Pre-call checks, fallback chains          |
| WebSocket handling issues         | Low    | Medium      | Test WebSocket connections thoroughly     |

### Operational Risks

| Risk                 | Impact | Probability | Mitigation                           |
| -------------------- | ------ | ----------- | ------------------------------------ |
| Configuration errors | Medium | Medium      | Validation, clear error messages     |
| Provider API changes | Low    | Low         | LiteLLM handles provider abstraction |
| Cost overruns        | Medium | Low         | Budget limits, cost tracking         |

### Migration Risks

| Risk                        | Impact | Probability | Mitigation                           |
| --------------------------- | ------ | ----------- | ------------------------------------ |
| Breaking existing workflows | High   | Low         | Backward compatibility, feature flag |
| User confusion              | Medium | Medium      | Clear documentation, migration guide |
| Performance degradation     | Medium | Low         | Performance testing, monitoring      |

---

## Success Metrics

### Functionality

- ✅ All three harnesses work with LiteLLM Router
- ✅ Responses API translation works correctly
- ✅ WebSocket streaming works
- ✅ Plan incorporate validation works

### Performance

- ✅ Routing latency < 100ms P95
- ✅ Cache hit rate > 50% (with Redis)
- ✅ Fallback success rate > 99%

### Cost

- ✅ 20-30% cost reduction through optimization
- ✅ Budget limits enforced correctly
- ✅ Cost tracking accurate

### Developer Experience

- ✅ Simplified configuration
- ✅ Clear error messages
- ✅ Good documentation

---

## Configuration Reference

### Environment Variables

```bash
# Enable LiteLLM Router
export THGENT_USE_LITELLM_ROUTER=1

# LiteLLM Router Configuration
export THGENT_LITELLM_ROUTING_POLICY=simple-shuffle
export THGENT_LITELLM_ENABLE_CACHE=1
export THGENT_LITELLM_REDIS_URL=redis://localhost:6379
export THGENT_LITELLM_FALLBACK_ENABLED=1
export THGENT_LITELLM_NUM_RETRIES=3
export THGENT_LITELLM_TIMEOUT=300

# Codex CLI
export OPENAI_BASE_URL=http://localhost:8765
export OPENAI_API_KEY=sk-dummy

# Factory Droid
export FACTORY_API_KEY=fk-...
```

### Code Configuration

```python
# In ThegentSettings (config.py)
litellm_routing_policy: str = "simple-shuffle"
litellm_enable_cache: bool = True
litellm_redis_url: str | None = None
litellm_fallback_enabled: bool = True
litellm_num_retries: int = 3
litellm_timeout: int = 300
use_litellm_router: bool = False  # Feature flag
```

---

## References

### Documentation

- [LiteLLM Router Docs](https://docs.litellm.ai/docs/routing)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [codex-proxy Reference](https://github.com/cornellsh/codex-proxy)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [OpenRouter Docs](https://openrouter.ai/docs) - Commercial router inspiration
- [OpenRouter Provider Routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [OpenRouter Guardrails](https://openrouter.ai/docs/guides/features/guardrails)
- [OpenRouter Broadcast](https://openrouter.ai/docs/guides/features/broadcast/overview)
- [OpenRouter Plugins](https://openrouter.ai/docs/guides/features/plugins/overview)
- [OpenRouter Message Transforms](https://openrouter.ai/docs/guides/features/message-transforms)
- [OpenRouter Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter Prompt Caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching)
- [OpenRouter Latency Optimization](https://openrouter.ai/docs/guides/best-practices/latency-and-performance)
- [OpenRouter Zero Completion Insurance](https://openrouter.ai/docs/guides/features/zero-completion-insurance)
- [OpenRouter ZDR](https://openrouter.ai/docs/guides/features/zdr)
- [Portkey Gateway](https://github.com/Portkey-AI/gateway) - OSS gateway with guardrails
- [Helicone](https://github.com/Helicone/helicone) - OSS observability + gateway
- [Semantic Router](https://github.com/aurelio-labs/semantic-router) - Zero-cost intent routing

### Internal Documentation

- `ULTRA_ADVANCED_ROUTER_RESEARCH.md` - **⭐⭐ Maximum depth research with production-ready code, complete feature analysis**
- `CHATGPT_PARETO_DEEP_INDEX.md` - **⭐⭐⭐ 7-part deep research from chatgpt3/4 (Foundations, Indices, API, Catalog, Speed Stack, Helios Spec, SOTA)**
- `CHATGPT_PARETO_ROUTER_EXTENSION.md` - **⭐⭐ Pareto router synthesis: Offer abstraction, shadow pricing, project catalog**
- `ADVANCED_ROUTER_RESEARCH.md` - **⭐ Comprehensive router research (OpenRouter, LiteLLM, advanced strategies)**
- `COMPREHENSIVE_LITELLM_HARNESS_INTEGRATION_PLAN.md`
- `CODEX_LITELLM_INTEGRATION_PLAN.md`
- `CODEX_CLI_LITELLM_FIX_SUMMARY.md`
- `TASK_IO_PHASE2_PROGRESS.md`
- `LITELLM_RESEARCH_SUMMARY.md`
- `IMPLEMENTATION_ROADMAP.md`

---

## Next Steps

1. **Review Plan**: Review this master plan and approve
2. **Start Implementation**: Begin with Phase 1 (LiteLLM Responses API Handler)
3. **Iterate**: Implement, test, iterate through each phase
4. **Document**: Update documentation as we go
5. **Rollout**: Gradual rollout with feature flags

---

**Status**: Planning Complete
**Ready for**: Implementation
**Estimated Effort**: 3-4 weeks
**Priority**: High
