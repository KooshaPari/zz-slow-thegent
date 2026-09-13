<DONE>
# Codex CLI + CLIProxy Configuration Audit and Plan

**Date**: 2026-02-18
**Scope**: Fix Codex CLI 404 on `/v1/responses`, model metadata warning, and correct cliproxy API handling
**Context**: User running OpenAI Codex v0.103.0 with `gemini-3-flash medium`, baseUrl `http://localhost:8317`

---

## 1. Audit Findings

### 1.1 404 on `ws://127.0.0.1:8317/v1/responses`

**Symptom**: `Unexpected status 404 Not Found: 404 page not found, url: ws://127.0.0.1:8317/v1/responses`

**Root cause**: The server on port 8317 is **raw CLIProxyAPIPlus** (Go binary), which only exposes Chat Completions (`/v1/chat/completions`). Codex CLI uses the **Responses API** (HTTP POST + WebSocket `/v1/responses`). Raw CLIProxy does not implement `/v1/responses`.

**Fix**: Run the **adapter** instead of raw proxy. The adapter (`cliproxy_adapter.py`) bridges Responses API ↔ Chat Completions and exposes `/v1/responses` (HTTP + WebSocket).

| What runs on 8317                     | Exposes /v1/responses? |
| ------------------------------------- | ---------------------- |
| Raw CLIProxyAPIPlus (direct binary)   | No → 404               |
| Adapter (start_proxy_with_adapter.py) | Yes ✓                  |

### 1.2 Model Metadata Warning

**Symptom**: `Model metadata for gemini-3-flash not found. Defaulting to fallback metadata; this can degrade performance and cause issues.`

**Root cause**: Codex queries `GET /v1/models` and expects each model object to include `context_window`, `max_completion_tokens`, etc. The adapter's `_transform_models_response` enriches models from `model_metadata.py`, but:

- Enrichment only runs when the **adapter** is serving (not raw proxy)
- Model ID matching may fail if CLIProxy returns different IDs (e.g. `google/gemini-3-flash` vs `gemini-3-flash`)

**Fix**: Ensure adapter is running (fixes 1.1). If warning persists, add `gemini-3-flash` and aliases to `model_metadata.py` and improve ID normalization in `_transform_models_response`.

### 1.3 baseUrl Configuration

**Observed**: `.factory/settings.json` uses `baseUrl: "http://localhost:8317"` (no `/v1` suffix).

**Codex expectation**: `OPENAI_BASE_URL` should be `http://127.0.0.1:8317/v1` for Chat/Responses API. Some clients append `/v1` automatically; others do not. If Codex uses `http://localhost:8317` without `/v1`, requests may hit `http://localhost:8317/v1/responses` (path added by client) or `http://localhost:8317/responses` (wrong).

**Fix**: Use `baseUrl: "http://127.0.0.1:8317/v1"` explicitly.

### 1.4 Codex Version

**Observed**: Codex v0.103.0
**MiniMax reference**: Recommends `@openai/codex@0.57.0` due to compatibility issues with newer versions.

**Implication**: Codex 0.103+ may use Responses API by default; 0.57.0 can use `wire_api = "chat"` (Chat Completions). If 0.103+ always uses Responses API, the adapter is required.

---

## 2. Correct Configuration (Local)

### 2.1 Start Proxy with Adapter

```bash
# Option A: process-compose (MCP + proxy with adapter)
cd thegent
THGENT_CLIPROXY_ADAPTER=1 thegent mcp up

# Option B: Direct adapter script (proxy only)
cd thegent
uv run python scripts/start_proxy_with_adapter.py
```

**Verify adapter is running**:

```bash
curl -s http://127.0.0.1:8317/v1/models | jq 'keys'
# Adapter returns {"models": [...]}; raw proxy returns {"data": [...]}
```

### 2.2 Codex Configuration

**Environment** (for `codex` CLI):

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8317/v1
export OPENAI_API_KEY=sk-dummy
```

**Or `.codex/config.toml`** (if using Codex config):

```toml
[model_providers.cliproxy]
name = "CLIProxy (thegent)"
base_url = "http://127.0.0.1:8317/v1"
env_key = "OPENAI_API_KEY"
wire_api = "responses"   # or "chat" if Codex supports it; "responses" if using adapter
requires_openai_auth = false
```

### 2.3 Factory / Cursor Settings

If using `.factory/settings.json` or similar for Codex:

- `baseUrl`: `http://127.0.0.1:8317/v1` (include `/v1`)
- `apiKey`: `sk-dummy` or any dummy (CLIProxy routes by provider config)

---

## 3. Correct Configuration (Web)

**Web docs**:

- [PROVIDER_SETUP_GUIDE.md](../guides/PROVIDER_SETUP_GUIDE.md) — Codex CLI with CLIProxy
- [CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md](./CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md) — Adapter architecture
- [CODEX_CLI_PROVIDER_GUIDES_RESEARCH.md](./CODEX_CLI_PROVIDER_GUIDES_RESEARCH.md) — MiniMax/GLM patterns

**MiniMax Codex CLI** (reference pattern): https://platform.minimax.io/docs/coding-plan/codex-cli

---

## 4. Remediation Plan

| #   | Task                                                                                | Priority | Owner |
| --- | ----------------------------------------------------------------------------------- | -------- | ----- |
| 1   | Kill any process on 8317; start adapter: `THGENT_CLIPROXY_ADAPTER=1 thegent mcp up` | P0       | User  |
| 2   | Set `OPENAI_BASE_URL=http://127.0.0.1:8317/v1` (include `/v1`)                      | P0       | User  |
| 3   | Update `.factory/settings.json` baseUrl to `http://127.0.0.1:8317/v1`               | P1       | User  |
| 4   | Run `thegent mgmt verify-codex-cliproxy` to confirm end-to-end                      | P1       | User  |
| 5   | If model metadata warning persists: add gemini-3-flash aliases to model_metadata.py | P2       | Dev   |
| 6   | Consider pinning Codex to 0.57.0 if 0.103+ continues to have issues                 | P3       | User  |

---

## 5. Quick Fix Commands

```bash
# 1. Ensure adapter is running
cd thegent
lsof -ti :8317 | xargs kill -9 2>/dev/null || true
THGENT_CLIPROXY_ADAPTER=1 thegent mcp up

# 2. Verify (after ~10s)
curl -s http://127.0.0.1:8317/v1/models | head -c 200
# Should output JSON with "models" key

# 3. Run Codex
OPENAI_BASE_URL=http://127.0.0.1:8317/v1 OPENAI_API_KEY=sk-dummy codex exec - "echo hi" --model gemini-3-flash
```

---

## 6. References

- [CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md](./CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md)
- [CODEX_CLI_PROVIDER_GUIDES_RESEARCH.md](./CODEX_CLI_PROVIDER_GUIDES_RESEARCH.md)
- [PROVIDER_SETUP_GUIDE.md](../guides/PROVIDER_SETUP_GUIDE.md)
- [MiniMax Codex CLI](https://platform.minimax.io/docs/coding-plan/codex-cli)
