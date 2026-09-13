<DONE>
# Codex CLI + LiteLLM Integration Fix Summary

**Date**: 2026-02-18
**Reference**: [codex-proxy](https://github.com/cornellsh/codex-proxy)
**Goal**: Fix codex CLI harnesses to work correctly with LiteLLM as front matter over OAI+Anth compatible provider services

---

## Key Insight

**You're correct**: If LiteLLM is correctly configured as front matter over individually wrapped OAI+Anth compatible provider services, codex-proxy shouldn't be necessary.

The issue is that the current adapter (`cliproxy_adapter.py`) routes Responses API requests to CLIProxyAPIPlus, which then routes to providers. Instead, it should route through LiteLLM Router when available.

---

## Current Architecture

```
Codex CLI → cliproxy_adapter.py → CLIProxyAPIPlus → Providers
```

**Problems**:

1. Double translation layer (adapter + CLIProxyAPIPlus)
2. Model routing happens in CLIProxyAPIPlus, not leveraging LiteLLM Router
3. Doesn't use LiteLLM's routing, caching, fallback capabilities

---

## Target Architecture

```
Codex CLI → cliproxy_adapter.py → LiteLLM Router → Providers
```

**Benefits**:

1. Single translation layer (Responses API → Chat Completions)
2. LiteLLM Router handles model routing, fallback, caching
3. Leverages LiteLLM's cost optimization and routing policies

---

## What codex-proxy Does (Reference)

From the codex-proxy repository:

1. **Responses API Handler**: Accepts `/v1/responses` endpoint
2. **Format Translation**: Converts Responses API → Provider API (Gemini/Z.AI)
3. **SSE Streaming**: Handles Server-Sent Events correctly
4. **Context Compaction**: Supports context compaction for long contexts
5. **Model Routing**: Routes models to correct providers

**Key Learning**: codex-proxy translates Responses API directly to provider APIs. But if LiteLLM Router is used, we translate Responses API → Chat Completions → LiteLLM Router → Providers.

---

## Fix Required

### 1. Update `cliproxy_adapter.py` to Support LiteLLM Router Backend

**Current**: Always proxies to CLIProxyAPIPlus
**Target**: Option to proxy to LiteLLM Router when available

**Implementation**:

```python
# In cliproxy_adapter.py
async def proxy_handler(request: Request) -> Response:
    backend = getattr(request.app.state, "backend_url", None)

    # Check if LiteLLM Router should be used
    use_litellm = os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1"

    if use_litellm and path == "/v1/responses":
        return await _handle_responses_via_litellm(request)

    # Fallback to CLIProxyAPIPlus
    ...
```

### 2. Create LiteLLM Router Responses Handler

**File**: `src/thegent/routing/litellm_responses_handler.py` (new)

**Functionality**:

- Accept Responses API format
- Translate to Chat Completions
- Call LiteLLM Router
- Translate responses back to Responses API format

### 3. Ensure Model Configuration

**Check**: `build_litellm_model_list()` includes all codex CLI models
**Verify**: Model aliases map correctly (e.g., `gpt-5-mini` → `openai/gpt-4o-mini`)

---

## Implementation Status

- ✅ **Plan Created**: `CODEX_LITELLM_INTEGRATION_PLAN.md`
- ⏳ **Implementation**: Pending
- ⏳ **Testing**: Pending

---

## Next Steps

1. **Implement LiteLLM Router Responses Handler**
   - Create `litellm_responses_handler.py`
   - Handle Responses API → Chat Completions translation
   - Route through LiteLLM Router
   - Translate responses back

2. **Update Adapter**
   - Add option to use LiteLLM Router backend
   - Maintain backward compatibility with CLIProxyAPIPlus

3. **Test Codex CLI**
   - Verify Responses API endpoint works
   - Test model routing
   - Verify streaming works correctly

---

## Configuration

**Environment Variable**:

```bash
export THGENT_USE_LITELLM_ROUTER=1  # Use LiteLLM Router instead of CLIProxyAPIPlus
```

**Codex CLI Setup**:

```bash
export OPENAI_BASE_URL=http://localhost:8765
export OPENAI_API_KEY=sk-dummy
codex exec - --model gpt-5-mini <<< "Hello"
```

---

## Benefits Over codex-proxy

1. **Unified Routing**: Single routing layer (LiteLLM) instead of multiple proxies
2. **Better Features**: Leverages LiteLLM's caching, fallback, cost tracking
3. **Simpler Stack**: One less service to maintain
4. **Provider Agnostic**: Works with any LiteLLM-compatible provider

---

**Status**: Planning complete, ready for implementation
