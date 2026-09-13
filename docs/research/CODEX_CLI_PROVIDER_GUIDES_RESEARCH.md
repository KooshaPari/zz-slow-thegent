<DONE>
# Codex CLI Provider Guides Research

**Date**: 2026-02-18
**Scope**: MiniMax and GLM Codex CLI integration guides

---

## MiniMax Codex CLI Guide

**Source**: [platform.minimax.io/docs/coding-plan/codex-cli](https://platform.minimax.io/docs/coding-plan/codex-cli)

### Key Points

1. **Recommended model**: `codex-MiniMax-M2.5` (provider-specific naming with `codex-` prefix)
2. **Codex version**: Use `@openai/codex@0.57.0` — newer versions have compatibility issues
3. **Wire API**: `wire_api = "chat"` — uses Chat Completions, not Responses API
4. **Auth**: `requires_openai_auth = false` — uses provider API key, not OpenAI auth

### Configuration Pattern

```toml
[model_providers.minimax]
name = "MiniMax Chat Completions API"
base_url = "https://api.minimax.io/v1"
env_key = "MINIMAX_API_KEY"
wire_api = "chat"
requires_openai_auth = false
request_max_retries = 4
stream_max_retries = 10
stream_idle_timeout_ms = 300000

[profiles.m21]
model = "codex-MiniMax-M2.5"
model_provider = "minimax"
```

### For thegent Proxy

When using CLIProxy (thegent) instead of direct MiniMax API:

- `base_url` → `http://127.0.0.1:8317/v1`
- `env_key` → typically `OPENAI_API_KEY` or provider-specific (CLIProxy handles routing)
- Model `codex-MiniMax-M2.5` maps to backend `minimax-m2.5` via adapter

### Model Metadata Warning

The warning _"Model metadata for `minimax-m2.5` not found"_ originates from **Codex CLI** when it queries the backend's `/v1/models` endpoint. Codex expects model objects to include metadata (e.g. `context_window`, `max_tokens`) for cost estimation and performance. If the backend returns models without this metadata, Codex falls back to defaults and warns.

**Fix**: The cliproxy adapter's `_transform_models_response` should enrich each model object with metadata from `model_metadata.py` before returning to Codex.

---

## GLM Codex CLI Guide

**Source**: Attempted URLs (all timed out or 404):

- `https://open.bigmodel.cn/dev/doc/codex-cli`
- `https://open.bigmodel.cn/docs/codex-cli`
- `https://zhipuai.cn/doc/codex-cli`
- `https://open.bigmodel.cn/dev/doc/guide/codex-cli`

**Status**: Could not fetch. GLM (Zhipu/BigModel) likely has a similar guide; common patterns from other providers suggest:

- Model name: `codex-GLM-5` or `glm-5`
- `wire_api = "chat"`
- `base_url` for China: `https://open.bigmodel.cn/api/paas/v4` or similar
- Config structure mirrors MiniMax's `[model_providers.<name>]` pattern

**Manual check**: Visit [open.bigmodel.cn](https://open.bigmodel.cn) dev docs and search for "Codex CLI" or "codex-cli".

---

## Provider Guide Comparison

| Item                 | MiniMax                     | GLM (expected)                 |
| -------------------- | --------------------------- | ------------------------------ |
| Model prefix         | `codex-MiniMax-M2.5`        | `codex-GLM-5` or `glm-5`       |
| wire_api             | `chat`                      | `chat`                         |
| base_url (direct)    | `https://api.minimax.io/v1` | `https://open.bigmodel.cn/...` |
| base_url (proxy)     | `http://127.0.0.1:8317/v1`  | `http://127.0.0.1:8317/v1`     |
| env_key              | `MINIMAX_API_KEY`           | `ZHIPU_API_KEY` or similar     |
| requires_openai_auth | false                       | false                          |

---

## Implications for thegent

1. **Adapter model mapping**: `_MODEL_ALIAS_MAP` in `cliproxy_adapter.py` already maps `codex-MiniMax-M2.5` → `minimax-m2.5`. Add `codex-GLM-5` → `glm-5` if using GLM.
2. **Model metadata**: Enrich `/v1/models` response in adapter with `context_window`, `max_tokens` from `model_metadata.py` to fix Codex warning.
3. **Docs**: Reference MiniMax guide in provider setup; add GLM guide link when available.

---

## References

- [MiniMax Codex CLI](https://platform.minimax.io/docs/coding-plan/codex-cli)
- [MiniMax Docs Index](https://platform.minimax.io/docs/llms.txt)
- [CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md](./CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md)
- [MINIMAX_CODEX_CLI_CONFIG_AUDIT_PLAN.md](./MINIMAX_CODEX_CLI_CONFIG_AUDIT_PLAN.md)
