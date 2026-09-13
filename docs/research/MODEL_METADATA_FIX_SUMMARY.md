<DONE>
# Model Metadata Fix Summary

## Issue
All models were showing warnings: "⚠ Model metadata for `{model}` not found. Defaulting to fallback metadata; this can degrade performance and cause issues."

## Root Cause
The warning originates from Codex CLI querying CLIProxyAPIPlus for model metadata. When metadata is missing, Codex CLI falls back to defaults, which can cause performance issues and incorrect cost estimation.

## Comprehensive Fix

### 1. Created Centralized Model Metadata Registry
**File**: `src/thegent/routing/model_metadata.py`

- Comprehensive registry with all models
- Includes: context window, cost per MTok, provider, backend
- Normalized lookup handles variations (e.g., `glm-5`, `GLM-5`, `z-ai/glm-5`)
- Helper functions: `get_model_metadata()`, `has_model_metadata()`, `get_all_models_with_metadata()`

### 2. Updated Context Window Dictionary
**File**: `src/thegent/routing/litellm_router.py`

Added entries for:
- `GLM-5`: 128000
- `z-ai/glm-5`: 128000
- `kilo-default`: 128000
- `roo-default`: 128000

### 3. Updated Cost Estimation
**Files**:
- `src/thegent/governance/cost.py` - Added to `_DEFAULT_PRICING_MTOK`
- `src/thegent/routing/litellm_router.py` - Added to `_estimate_cost()` cost_per_1k dict

Added pricing for:
- `GLM-5`: $0.40/MTok
- `z-ai/glm-5`: $0.40/MTok
- `kilo-default`: $0.50/MTok
- `roo-default`: $0.50/MTok

### 4. Enhanced CLIProxy Configuration
**File**: `src/thegent/agents/cliproxy_manager.py`

- Auto-configures model aliases for `glm`, `kilo`, `roo` providers
- Ensures all model variants are registered in `cliproxy-config.yaml`
- Handles provider-native names (e.g., `MiniMax-M2.5`, `GLM-5`)

### 5. Integrated Metadata Registry into Routing
**File**: `src/thegent/routing/litellm_router.py`

- `validate_context_window()` now checks metadata registry first
- `_estimate_cost()` now checks metadata registry first
- `_validate_model_metadata()` validates all router models on initialization
- Uses debug-level logging to avoid warning spam

## Models Covered

All models now have complete metadata:

### Anthropic Claude
- `claude-haiku-4.5`
- `claude-sonnet-4.5`
- `claude-sonnet-4.6`
- `claude-opus-4.6`
- `claude-opus-4.6-1m`

### Google Gemini
- `gemini-2.0-flash`
- `gemini-2.5-flash`
- `gemini-3-flash`
- `gemini-3-pro`

### OpenAI / Codex
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-5-mini`
- `gpt-5.3-codex-spark`
- `gpt-5.3-codex`
- `gpt-5.3-codex-high`
- `gpt-5.3-codex-max`

### Zhipu GLM
- `glm-5`
- `GLM-5`
- `z-ai/glm-5`

### MiniMax
- `minimax-m2.5`
- `MiniMax-M2.5`

### Other Providers
- `kilo-default` (Kilo)
- `roo-default` (Roo)
- `deepseek-v3.2` (DeepSeek)
- `kimi-k2.5` (Kimi)
- `qwen3-coder` (Qwen)
- `llama-nemotron-ultra` (Meta)
- `composer-1`, `composer-1.5` (Cursor)

## Verification Steps

1. **Check metadata registry**:

```python
from thegent.routing.model_metadata import has_model_metadata, get_model_metadata

assert has_model_metadata("glm-5")
assert get_model_metadata("glm-5")["context_window"] == 128000
```

2. **Verify CLIProxy config**:
   - Check `~/.config/cli-proxy-api/cliproxy-config.yaml`
   - Ensure all providers have `models` array with proper aliases

3. **Test routing**:
   - All models should route without warnings
   - Context window validation should work
   - Cost estimation should be accurate

## Next Steps

1. **Monitor**: Watch for any remaining warnings after restarting CLIProxyAPIPlus
2. **Test**: Verify all models work correctly with new metadata
3. **Update**: Add new models to `model_metadata.py` as they're added to the system

## Files Modified

1. `src/thegent/routing/model_metadata.py` (NEW)
2. `src/thegent/routing/litellm_router.py`
3. `src/thegent/governance/cost.py`
4. `src/thegent/agents/cliproxy_manager.py`

## Notes

- The warning originates from Codex CLI, not thegent code
- CLIProxyAPIPlus must be restarted to pick up new config
- Metadata registry is the single source of truth for model metadata
- All routing functions now check metadata registry first before falling back to static dictionaries
