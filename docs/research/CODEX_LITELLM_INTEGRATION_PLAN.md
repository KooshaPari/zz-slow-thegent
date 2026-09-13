<DONE>
# Codex CLI + LiteLLM Integration Plan

**Date**: 2026-02-18
**Goal**: Fix codex CLI harnesses to work with LiteLLM as front matter over OAI+Anth compatible provider services, eliminating need for codex-proxy.

---

## Current Architecture

### Current Flow

```
Codex CLI → cliproxy_adapter.py → CLIProxyAPIPlus → Providers
```

### Issues

1. **Double Translation**: Adapter translates Responses API → Chat Completions, then CLIProxyAPIPlus may translate again
2. **Model Routing**: Model routing happens in CLIProxyAPIPlus, not leveraging LiteLLM Router's capabilities
3. **Unnecessary Complexity**: codex-proxy exists because Responses API isn't properly handled

---

## Target Architecture

### Target Flow

```
Codex CLI → LiteLLM Router (with Responses API adapter) → Individual Providers
```

### Benefits

1. **Single Translation Layer**: Responses API → Chat Completions happens once
2. **LiteLLM Routing**: Leverages LiteLLM's routing, fallback, caching, cost tracking
3. **Simpler Stack**: No need for codex-proxy if LiteLLM handles routing correctly

---

## Implementation Plan

### Option 1: LiteLLM Router with Responses API Adapter (Recommended)

**Approach**: Create a LiteLLM-compatible Responses API handler that:

1. Accepts Responses API format from Codex CLI
2. Translates to Chat Completions format
3. Routes through LiteLLM Router
4. Translates responses back to Responses API format

**Files to Modify**:

- `src/thegent/cliproxy_adapter.py` - Add LiteLLM Router backend option
- `src/thegent/routing/litellm_router.py` - Add Responses API handler
- `src/thegent/agents/codex_proxy.py` - Update to use LiteLLM Router when available

**Key Changes**:

```python
# In cliproxy_adapter.py
async def proxy_handler(request: Request) -> Response:
    backend = getattr(request.app.state, "backend_url", None)

    # Option: Use LiteLLM Router instead of CLIProxyAPIPlus
    use_litellm = os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1"

    if use_litellm and path == "/v1/responses":
        return await _handle_responses_via_litellm(request)

    # Fallback to CLIProxyAPIPlus
    ...
```

### Option 2: Enhance CLIProxyAPIPlus to Use LiteLLM Router

**Approach**: Configure CLIProxyAPIPlus to route through LiteLLM Router for certain providers

**Files to Modify**:

- `src/thegent/agents/cliproxy_manager.py` - Add LiteLLM Router configuration
- CLIProxyAPIPlus config generation - Add LiteLLM Router as backend

---

## Key Requirements

### 1. Responses API Format Support

Codex CLI sends:

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
  "stream": true
}
```

Must translate to Chat Completions:

```json
{
  "model": "gpt-5-mini",
  "messages": [{ "role": "user", "content": "Hello" }],
  "stream": true
}
```

### 2. Model Routing

LiteLLM Router should handle:

- Model name resolution (aliases → provider/model)
- Provider selection based on routing policy
- Fallback chains
- Cost optimization

### 3. Response Translation

LiteLLM Chat Completions response:

```json
{
  "choices": [
    {
      "delta": { "content": "Hello" }
    }
  ]
}
```

Must translate back to Responses API:

```json
{
  "type": "response.output_item.added",
  "item": {
    "type": "message",
    "role": "assistant",
    "content": [{ "type": "text", "text": "Hello" }]
  }
}
```

---

## Implementation Steps

### Phase 1: LiteLLM Router Responses API Handler

1. **Create `litellm_responses_handler.py`**:
   - Accept Responses API requests
   - Translate to Chat Completions
   - Call LiteLLM Router
   - Translate responses back to Responses API format

2. **Update `cliproxy_adapter.py`**:
   - Add option to use LiteLLM Router backend
   - Route `/v1/responses` to LiteLLM handler when enabled

### Phase 2: Model Configuration

1. **Ensure LiteLLM Router has all models configured**:
   - Check `build_litellm_model_list()` includes all codex CLI models
   - Verify model aliases are correct

2. **Update model routing**:
   - Ensure codex CLI model names map correctly to LiteLLM models
   - Test fallback chains work correctly

### Phase 3: Testing

1. **Test Responses API endpoint**:

   ```bash
   curl -X POST http://localhost:8765/v1/responses \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-dummy" \
     -d '{"model": "gpt-5-mini", "input": [{"type": "message", "role": "user", "content": [{"type": "text", "text": "Hello"}]}], "stream": true}'
   ```

2. **Test Codex CLI**:
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

## Migration Path

1. **Phase 1**: Implement LiteLLM Router handler (backward compatible)
2. **Phase 2**: Test with `THGENT_USE_LITELLM_ROUTER=1`
3. **Phase 3**: Make LiteLLM Router default, deprecate CLIProxyAPIPlus path
4. **Phase 4**: Remove CLIProxyAPIPlus dependency (optional)

---

## References

- [codex-proxy](https://github.com/cornellsh/codex-proxy) - Reference implementation
- [LiteLLM Router Docs](https://docs.litellm.ai/docs/routing)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)

---

**Status**: Planning phase
