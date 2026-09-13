<DONE>
# OpenRouter Models Endpoint Research & Codex Warning Fix

**Date:** 2026-02-20
**Author:** Research agent
**Scope:** Fix "Model metadata not found" warning in Codex CLI proxy; document OpenRouter vs OpenAI model schemas; design transformation function.

---

## 1. Issue Summary

When Codex CLI connects through the thegent proxy at port 8317, it shows:

```
Model metadata not found for gemini-3-flash (or glm-5), using fallback metadata
```

**Root cause:** Codex 0.104.0 fetches its model catalog from its configured `OPENAI_BASE_URL/v1/models` (which is our proxy). Our proxy's `/v1/models` response must return the full Codex metadata schema or Codex falls back to hardcoded defaults and logs the warning. The proxy's `_transform_models_response` in `src/thegent/cliproxy_adapter.py` already implements this enrichment, but it is only invoked when the backend returns models in a parseable list. If the backend returns no models for `gemini-3-flash` or `glm-5` (because they may not be in CLIProxyAPIPlus's own model list), those models never appear in the enriched response.

**Status:** NON-BLOCKING. Codex uses fallback metadata and works fine. The fix eliminates the warning.

---

## 2. OpenAI `/v1/models` Response Schema

OpenAI returns a simple, minimal schema. Each model object has exactly four fields:

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1715367049,
      "owned_by": "openai"
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Canonical model identifier |
| `object` | string | Always `"model"` |
| `created` | integer | Unix timestamp |
| `owned_by` | string | Provider/org name |

This minimal schema is what Codex would encounter if it called `api.openai.com` directly. Codex does NOT use this endpoint for its model catalog; instead it uses the Codex-specific `/v1/models` endpoint (which returns the richer schema below).

---

## 3. Codex `/v1/models` Model Cache Schema (Real Format)

The actual Codex model cache is stored at `~/.codex/models_cache.json`. This was verified against Codex 0.104.0's live cache.

**Top-level cache structure:**

```json
{
  "fetched_at": "2026-02-20T12:49:14.483154Z",
  "etag": "W/\"a152b492560d015c07cc5a6ed1b8b4ca\"",
  "client_version": "0.104.0",
  "models": [ ... ]
}
```

**Per-model object — complete field list** (22 fields, all required to avoid the warning):

```json
{
  "slug": "gpt-5.3-codex",
  "display_name": "gpt-5.3-codex",
  "description": "Latest frontier agentic coding model.",
  "default_reasoning_level": "medium",
  "supported_reasoning_levels": [
    {"effort": "low",    "description": "Fast responses with lighter reasoning"},
    {"effort": "medium", "description": "Balances speed and reasoning depth for everyday tasks"},
    {"effort": "high",   "description": "Greater reasoning depth for complex problems"},
    {"effort": "xhigh",  "description": "Extra high reasoning depth for complex problems"}
  ],
  "shell_type": "shell_command",
  "visibility": "list",
  "supported_in_api": true,
  "priority": 0,
  "upgrade": null,
  "base_instructions": "You are Codex...",
  "model_messages": {
    "instructions_template": "...",
    "instructions_variables": { ... }
  },
  "supports_reasoning_summaries": true,
  "support_verbosity": true,
  "default_verbosity": "low",
  "apply_patch_tool_type": "freeform",
  "truncation_policy": {"mode": "tokens", "limit": 10000},
  "supports_parallel_tool_calls": true,
  "context_window": 272000,
  "effective_context_window_percent": 95,
  "experimental_supported_tools": [],
  "input_modalities": ["text", "image"],
  "prefer_websockets": false
}
```

**Key observations:**

- The primary key is `slug` (not `id`). Codex looks up models by `slug`.
- There is NO `max_completion_tokens` field in the real cache. The proxy's `_transform_models_response` sets it via `setdefault` but Codex does not use it for the warning check.
- There is NO `context_length` field; only `context_window`.
- `model_messages` can be an empty string `"[]"` or a full structured dict — both are valid.
- `base_instructions` can be an empty string for non-Codex-native models.
- The top-level key is `"models"` (not OpenAI's `"data"`), and the outer envelope includes `fetched_at`, `etag`, `client_version`.
- The `x-models-etag` response header must match the `etag` value for Codex to cache the response.

---

## 4. OpenRouter `/api/v1/models` Response Schema

OpenRouter returns a significantly richer schema per model. Verified by live fetch of `https://openrouter.ai/api/v1/models` (337 models as of 2026-02-20).

**Top-level response:**

```json
{
  "data": [ ... ]
}
```

**Per-model object — complete field list:**

```json
{
  "id": "google/gemini-3.1-pro-preview",
  "canonical_slug": "google/gemini-3.1-pro-preview-20260219",
  "hugging_face_id": "",
  "name": "Google: Gemini 3.1 Pro Preview",
  "created": 1771509627,
  "description": "Gemini 3.1 Pro Preview is Google's frontier reasoning model...",
  "context_length": 1048576,
  "architecture": {
    "modality": "text+image+file+audio+video->text",
    "input_modalities": ["audio", "file", "image", "text", "video"],
    "output_modalities": ["text"],
    "tokenizer": "Gemini",
    "instruct_type": null
  },
  "pricing": {
    "prompt": "0.000002",
    "completion": "0.000012",
    "image": "0.000002",
    "audio": "0.000002",
    "internal_reasoning": "0.000012",
    "input_cache_read": "0.0000002",
    "input_cache_write": "0.000000375"
  },
  "top_provider": {
    "context_length": 1048576,
    "max_completion_tokens": 65536,
    "is_moderated": false
  },
  "per_request_limits": null,
  "supported_parameters": [
    "include_reasoning", "max_tokens", "reasoning",
    "response_format", "seed", "stop", "structured_outputs",
    "temperature", "tool_choice", "tools", "top_p"
  ],
  "default_parameters": {
    "temperature": null,
    "top_p": null,
    "frequency_penalty": null
  },
  "expiration_date": null
}
```

**Second example — Anthropic Claude Sonnet 4.6:**

```json
{
  "id": "anthropic/claude-sonnet-4.6",
  "canonical_slug": "anthropic/claude-4.6-sonnet-20260217",
  "hugging_face_id": "",
  "name": "Anthropic: Claude Sonnet 4.6",
  "created": 1771342990,
  "description": "Sonnet 4.6 is Anthropic's most capable Sonnet-class model...",
  "context_length": 1000000,
  "architecture": {
    "modality": "text+image->text",
    "input_modalities": ["text", "image"],
    "output_modalities": ["text"],
    "tokenizer": "Claude",
    "instruct_type": null
  },
  "pricing": {
    "prompt": "0.000003",
    "completion": "0.000015",
    "web_search": "0.01",
    "input_cache_read": "0.0000003",
    "input_cache_write": "0.00000375"
  },
  "top_provider": {
    "context_length": 1000000,
    "max_completion_tokens": 128000,
    "is_moderated": true
  },
  "per_request_limits": null,
  "supported_parameters": [
    "include_reasoning", "max_tokens", "reasoning",
    "response_format", "stop", "structured_outputs",
    "temperature", "tool_choice", "tools", "top_k", "top_p", "verbosity"
  ],
  "default_parameters": {
    "temperature": null,
    "top_p": null,
    "frequency_penalty": null
  },
  "expiration_date": null
}
```

**OpenRouter field inventory:**

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Namespaced: `"provider/model-name"` |
| `canonical_slug` | string | Versioned slug with date suffix |
| `hugging_face_id` | string | HuggingFace model ID or `""` |
| `name` | string | Human-readable display name |
| `created` | integer | Unix timestamp |
| `description` | string | Long-form markdown description |
| `context_length` | integer or null | Input context window in tokens |
| `architecture.modality` | string | e.g. `"text+image->text"` |
| `architecture.input_modalities` | string[] | `["text", "image", "audio", "file", "video"]` subset |
| `architecture.output_modalities` | string[] | `["text", "image", "embeddings", "audio"]` subset |
| `architecture.tokenizer` | string | e.g. `"Gemini"`, `"Claude"`, `"GPT"` |
| `architecture.instruct_type` | string or null | Fine-tune instruction format |
| `pricing.prompt` | string (decimal) | Cost per token (input) as string |
| `pricing.completion` | string (decimal) | Cost per token (output) as string |
| `pricing.image` | string or absent | Cost per image token |
| `pricing.audio` | string or absent | Cost per audio token |
| `pricing.internal_reasoning` | string or absent | Cost for reasoning tokens |
| `pricing.input_cache_read` | string or absent | Cache read cost |
| `pricing.input_cache_write` | string or absent | Cache write cost |
| `pricing.web_search` | string or absent | Web search cost per call |
| `pricing.discount` | number or absent | Discount multiplier |
| `top_provider.context_length` | integer or null | Provider's actual context limit |
| `top_provider.max_completion_tokens` | integer or null | Max output tokens |
| `top_provider.is_moderated` | boolean | Whether content is moderated |
| `per_request_limits` | object or null | Token limits per request |
| `supported_parameters` | string[] | LLM parameter names supported |
| `default_parameters` | object | Default param values (often null) |
| `expiration_date` | string (ISO 8601) or null | Model deprecation date |

**How OpenRouter differs from OpenAI:**
- OpenAI: 4 fields (`id`, `object`, `created`, `owned_by`) — minimal.
- OpenRouter: 13+ top-level fields plus nested objects — provider metadata, pricing, architecture, capability matrix.
- OpenRouter uses `"data"` as the list key (same as OpenAI).
- OpenRouter model IDs are namespaced: `"google/gemini-3.1-pro-preview"` vs OpenAI's flat `"gpt-4o"`.

**How OpenRouter differs from Codex:**
- Codex uses `"models"` as the list key; OpenRouter uses `"data"`.
- Codex uses `slug` as the primary key; OpenRouter uses `id`.
- Codex has agent/shell-specific fields (`shell_type`, `apply_patch_tool_type`, `base_instructions`, `model_messages`, `supported_reasoning_levels`, etc.) that OpenRouter does not have.
- OpenRouter has pricing, architecture tokenizer, and per-request limit fields that Codex does not use.
- Context window: OpenRouter calls it `context_length`; Codex calls it `context_window`.

---

## 5. Where the Warning Originates

The warning `"Model metadata not found for gemini-3-flash, using fallback metadata"` is emitted by Codex when it looks up a model slug in its local cache (`~/.codex/models_cache.json`) and does not find a matching entry.

**Codex model lookup flow:**

1. On startup, Codex calls `GET /v1/models` against `OPENAI_BASE_URL` (our proxy at port 8317).
2. Our proxy's `_transform_models_response` (lines 447-532 of `cliproxy_adapter.py`) transforms the response into Codex format with all required fields, outputting `{"fetched_at": ..., "client_version": "proxy", "models": [...]}`.
3. Codex writes this to `~/.codex/models_cache.json`.
4. When a request uses model `"gemini-3-flash"`, Codex searches `models_cache.json` for `slug == "gemini-3-flash"`.
5. If not found (because the backend didn't list it), Codex logs the warning and uses hardcoded fallback metadata.

**The real problem:** The backend (CLIProxyAPIPlus) may not return `gemini-3-flash` or `glm-5` in its `/v1/models` list. Our `_transform_models_response` enriches whatever models are returned, but cannot create models that the backend didn't list.

---

## 6. Current State of the Proxy's Transform

`src/thegent/cliproxy_adapter.py` lines 447-532 already implement `_transform_models_response`. It:

1. Parses the backend's `/v1/models` response (`"data"` or `"models"` key).
2. For each model, looks up thegent's `MODEL_METADATA` registry via `get_model_metadata(mid)` for context window.
3. Sets all 22+ Codex fields via `setdefault` so existing fields are not overwritten.
4. Emits the result as `{"fetched_at": ..., "client_version": "proxy", "models": [...]}`.
5. Computes and returns an `x-models-etag` SHA256 header.

**What the adapter correctly sets** (matching real Codex cache):
- `slug`, `display_name`, `description`, `shell_type`, `visibility`, `supported_in_api`
- `priority`, `upgrade`, `base_instructions`, `model_messages`
- `supports_reasoning_summaries`, `support_verbosity`, `default_verbosity`
- `apply_patch_tool_type`, `truncation_policy`, `supports_parallel_tool_calls`
- `context_window`, `effective_context_window_percent`
- `experimental_supported_tools`, `input_modalities`, `prefer_websockets`
- `default_reasoning_level`, `supported_reasoning_levels`

**What the adapter sets that the real cache does NOT have** (harmless extras):
- `context_length` — real cache uses `context_window`; Codex ignores `context_length`
- `max_completion_tokens` — not present in real cache models; Codex ignores it at the model level

These extra fields are harmless; Codex ignores unknown fields.

**The gap:** If `gemini-3-flash` or `glm-5` are not returned by the backend's `/v1/models`, the transform never runs for them.

---

## 7. Transformation Function: OpenRouter -> Codex Format

When the proxy backend is OpenRouter (or when we want to inject models proactively), the following function converts an OpenRouter model object into the Codex cache format:

```python
"""Transform OpenRouter /api/v1/models entries into Codex /v1/models format.

OpenRouter field -> Codex field mapping:
  id             -> slug (strip provider prefix if desired, or keep namespaced)
  name           -> display_name
  description    -> description
  context_length -> context_window
  architecture.input_modalities -> input_modalities (with "file"/"audio"/"video" stripped to "text"/"image")
  top_provider.max_completion_tokens -> used for truncation_policy.limit heuristic
"""

from __future__ import annotations

import time
from typing import Any


# Codex only accepts these input modalities
_CODEX_INPUT_MODALITIES = {"text", "image"}


def _openrouter_slug(model_id: str) -> str:
    """Convert OpenRouter namespaced id to a Codex slug.

    OpenRouter uses 'provider/model-name'; Codex expects a flat slug.
    We strip the provider prefix so 'google/gemini-3.1-pro-preview' -> 'gemini-3.1-pro-preview'.
    For models already without a prefix (e.g. 'gemini-3-flash'), return as-is.
    """
    return model_id.split("/", 1)[1] if "/" in model_id else model_id


def _codex_input_modalities(openrouter_input_modalities: list[str] | None) -> list[str]:
    """Map OpenRouter input_modalities to the subset Codex understands."""
    if not openrouter_input_modalities:
        return ["text"]
    return [m for m in openrouter_input_modalities if m in _CODEX_INPUT_MODALITIES] or ["text"]


def _truncation_limit(context_window: int, max_completion_tokens: int | None) -> int:
    """Derive a sensible truncation_policy limit.

    Codex uses this to trim context before sending to the model.
    A reasonable default is 10000 (Codex's own default), but we scale
    it to 10% of the context window for very large models, capped at 50000.
    """
    if max_completion_tokens:
        return min(max_completion_tokens, 50000)
    return min(max(10000, context_window // 20), 50000)


def openrouter_model_to_codex(
    or_model: dict[str, Any],
    *,
    base_instructions: str = "",
    model_messages: str = "[]",
    shell_type: str = "shell_command",
    default_reasoning_level: str = "medium",
) -> dict[str, Any]:
    """Convert a single OpenRouter model object to Codex /v1/models format.

    Args:
        or_model: One entry from OpenRouter's GET /api/v1/models response data list.
        base_instructions: Optional agent instructions. Empty string is valid.
        model_messages: Optional model_messages JSON string. "[]" is valid.
        shell_type: Codex shell type. "shell_command" is the standard value.
        default_reasoning_level: One of "low", "medium", "high".

    Returns:
        A dict with all 22 required Codex model cache fields set.
    """
    model_id: str = or_model.get("id", "")
    slug = _openrouter_slug(model_id)
    name: str = or_model.get("name", slug)
    description: str = or_model.get("description", "")
    context_length: int = or_model.get("context_length") or 128000

    arch: dict[str, Any] = or_model.get("architecture") or {}
    or_input_modalities: list[str] = arch.get("input_modalities") or ["text"]
    codex_modalities = _codex_input_modalities(or_input_modalities)

    top_provider: dict[str, Any] = or_model.get("top_provider") or {}
    max_completion_tokens: int | None = top_provider.get("max_completion_tokens")
    trunc_limit = _truncation_limit(context_length, max_completion_tokens)

    return {
        # --- Identity ---
        "slug": slug,
        "display_name": name,
        "description": description,
        # --- Reasoning ---
        "default_reasoning_level": default_reasoning_level,
        "supported_reasoning_levels": [
            {"effort": "low", "description": "Fast responses with lighter reasoning"},
            {"effort": "medium", "description": "Balances speed and reasoning depth for everyday tasks"},
            {"effort": "high", "description": "Greater reasoning depth for complex problems"},
        ],
        # --- Shell / API ---
        "shell_type": shell_type,
        "visibility": "list",
        "supported_in_api": True,
        "priority": 0,
        "upgrade": None,
        # --- Instructions ---
        "base_instructions": base_instructions,
        "model_messages": model_messages,
        # --- Capabilities ---
        "supports_reasoning_summaries": False,
        "support_verbosity": False,
        "default_verbosity": "low",
        "apply_patch_tool_type": "freeform",
        "truncation_policy": {"mode": "tokens", "limit": trunc_limit},
        "supports_parallel_tool_calls": True,
        # --- Context ---
        "context_window": context_length,
        "effective_context_window_percent": 95,
        # --- Modalities ---
        "experimental_supported_tools": [],
        "input_modalities": codex_modalities,
        "prefer_websockets": False,
    }


def openrouter_response_to_codex(
    openrouter_response: dict[str, Any],
) -> dict[str, Any]:
    """Convert a full OpenRouter GET /api/v1/models response to Codex cache format.

    Args:
        openrouter_response: The JSON response body from GET https://openrouter.ai/api/v1/models

    Returns:
        A dict matching Codex's models_cache.json format:
        {"fetched_at": ..., "client_version": "proxy", "models": [...]}
    """
    or_models: list[dict[str, Any]] = openrouter_response.get("data") or []
    codex_models = [openrouter_model_to_codex(m) for m in or_models if isinstance(m, dict)]
    return {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "client_version": "proxy",
        "models": codex_models,
    }
```

---

## 8. Transformation for OpenRouter Backend in the Proxy

When the proxy's backend is an OpenRouter-compatible endpoint (rather than CLIProxyAPIPlus), the existing `_transform_models_response` in `cliproxy_adapter.py` handles OpenAI-format `"data"` lists. It already:

1. Reads `payload.get("data") or payload.get("models")` — covers both OpenAI and Codex formats.
2. Calls `get_model_metadata(mid)` from `thegent.routing.model_metadata` for context window.
3. Enriches with all required Codex fields.

For OpenRouter backends, the additional fields available (`context_length`, `architecture.input_modalities`, `top_provider.max_completion_tokens`) can be leveraged by updating `_transform_models_response` to also read:

```python
# Inside the per-model loop in _transform_models_response:
arch = m.get("architecture") or {}
or_input_modalities = arch.get("input_modalities") or ["text"]
codex_modalities = [mod for mod in or_input_modalities if mod in ("text", "image")] or ["text"]

top_provider = m.get("top_provider") or {}
max_output = top_provider.get("max_completion_tokens")

# Override context from OpenRouter if not in our registry
if not meta:
    ctx = m.get("context_length") or 128000

m.setdefault("input_modalities", codex_modalities)
```

---

## 9. Fix: Proactive Model Injection for `gemini-3-flash` and `glm-5`

The root cause of the warning is that these models are not in the backend's model list. The fix is to inject them into the `/v1/models` response even if the backend does not return them.

**Strategy:** In `_transform_models_response`, after enriching the backend's model list, append any models from thegent's `MODEL_METADATA` registry that are not already present in the enriched list.

```python
# After enriching models from backend response, inject missing known models:
existing_slugs = {m.get("slug", m.get("id", "")) for m in models}

from thegent.routing.model_metadata import MODEL_METADATA
import time as _time

for known_id, known_meta in MODEL_METADATA.items():
    # Skip aliases (uppercase variants, path variants already covered)
    if known_id in existing_slugs:
        continue
    # Skip if a case-insensitive match already exists
    known_lower = known_id.lower()
    if any(s.lower() == known_lower for s in existing_slugs):
        continue
    ctx = known_meta.get("context_window", 128000)
    injected = {
        "slug": known_id,
        "display_name": known_id,
        "description": f"{known_meta.get('provider', 'unknown')} model",
        "default_reasoning_level": "medium",
        "supported_reasoning_levels": [
            {"effort": "low", "description": "Fast responses with lighter reasoning"},
            {"effort": "medium", "description": "Balanced"},
            {"effort": "high", "description": "Thorough, higher quality"},
        ],
        "shell_type": "shell_command",
        "visibility": "list",
        "supported_in_api": True,
        "priority": 0,
        "upgrade": None,
        "base_instructions": "",
        "model_messages": "[]",
        "supports_reasoning_summaries": False,
        "support_verbosity": False,
        "default_verbosity": "low",
        "apply_patch_tool_type": "freeform",
        "truncation_policy": {"mode": "tokens", "limit": 10000},
        "supports_parallel_tool_calls": True,
        "context_window": ctx,
        "effective_context_window_percent": 95,
        "experimental_supported_tools": [],
        "input_modalities": ["text"],
        "prefer_websockets": False,
    }
    models.append(injected)
    existing_slugs.add(known_id)
```

This ensures that `gemini-3-flash`, `glm-5`, `minimax-m2.5`, and all other models in `MODEL_METADATA` are always present in the Codex models response, eliminating the warning regardless of what the backend returns.

---

## 10. Schema Comparison Table

| Field | OpenAI | OpenRouter | Codex Cache | Proxy _transform |
|-------|--------|-----------|-------------|-----------------|
| `id` / `slug` | `id` | `id` (namespaced) | `slug` | sets `slug` from `id` |
| `object` | `"model"` | absent | absent | not set |
| `created` | integer | integer | absent | not set |
| `owned_by` | string | absent | absent | not set |
| `name` / `display_name` | absent | `name` | `display_name` | sets `display_name` |
| `description` | absent | `description` (long) | `description` | sets `description=""` |
| `context_length` / `context_window` | absent | `context_length` | `context_window` | sets both |
| `architecture` | absent | nested object | absent | reads `input_modalities` |
| `pricing` | absent | nested object | absent | not used |
| `top_provider` | absent | nested object | absent | not used |
| `per_request_limits` | absent | object or null | absent | not used |
| `supported_parameters` | absent | string[] | absent | not used |
| `shell_type` | absent | absent | `shell_type` | sets `"shell_command"` |
| `visibility` | absent | absent | `visibility` | sets `"list"` |
| `supported_in_api` | absent | absent | `supported_in_api` | sets `true` |
| `supported_reasoning_levels` | absent | absent | present | sets default 3-level list |
| `base_instructions` | absent | absent | present (long) | sets `""` |
| `model_messages` | absent | absent | present (structured) | sets `"[]"` |
| `truncation_policy` | absent | absent | present | sets `{"mode":"tokens","limit":10000}` |
| `input_modalities` | absent | via `architecture` | present | sets `["text"]` |
| `prefer_websockets` | absent | absent | present | sets `false` |
| `apply_patch_tool_type` | absent | absent | present | sets `"freeform"` |

---

## 11. Files Involved

- **`src/thegent/cliproxy_adapter.py`** — Contains `_transform_models_response` (lines 447-532) and `proxy_handler` (lines 543-610). The models endpoint transform lives here.
- **`src/thegent/routing/model_metadata.py`** — `MODEL_METADATA` registry and `get_model_metadata()`. Source of truth for context windows and provider info for all known models (including `gemini-3-flash`, `glm-5`, etc.).
- **`src/thegent/routing/harness_model_mapping.py`** — `CODEX_TO_BACKEND_MODEL` map for request-time model ID translation (Codex alias -> backend model ID).
- **`~/.codex/models_cache.json`** — Codex's local model cache. Populated from the proxy's `/v1/models` response. The schema here is the ground truth for what Codex requires.

---

## 12. Open Questions

1. **Does CLIProxyAPIPlus list `gemini-3-flash` in its `/v1/models`?** If not, the proactive injection strategy (Section 9) is needed. If yes, the existing transform already handles it — the warning may be a transient or version-specific issue.

2. **Should the proxy fetch from OpenRouter directly?** If the proxy is configured with an OpenRouter backend, it can proxy `/v1/models` to OpenRouter and use `openrouter_response_to_codex()` (Section 7) to transform the full 337-model list into Codex format. This gives Codex a complete, accurate model catalog from OpenRouter.

3. **`x-models-etag` vs `etag`:** Codex's real cache includes an `etag` field from the response header (`W/"a152..."` format from OpenRouter). Our proxy returns `x-models-etag` as an SHA256 hex string. Verify that Codex honors `x-models-etag` and does not also expect the outer `etag` field in the JSON body.

4. **`model_messages` format:** The real cache has `model_messages` as a full nested dict with `instructions_template` and `instructions_variables`. Our proxy sets `"[]"` (a JSON string). This may cause Codex to show fallback behavior for extended model context. For non-Codex-native models, `"[]"` is acceptable.
