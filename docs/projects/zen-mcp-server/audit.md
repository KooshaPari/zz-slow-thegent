# CLIProxyAPIPlus Fork vs thegent: Zen / gemini-3-flash Audit

**Date:** 2026-02-18  
**Scope:** Verify fork supports openai-compatibility with model aliases; Zen block injection; gemini-3-flash routing.

---

## Executive Summary

**No fork changes are required.** The CLIProxyAPIPlus fork already supports openai-compatibility with model aliases. The thegent injects a Zen block when `THGENT_ZEN_API_KEY` (or `OPENCODE_API_KEY` / `ZEN_API_KEY`) is set. Config structure and routing logic align.

If you see `"unknown provider for model"` or 502, the cause is typically one of:

1. Zen API key not set (no Zen block in config)
2. Proxy not restarted after config change
3. Zen entry missing from `~/.config/thegent/cliproxy-config.yaml`

---

## 1. Config Format Comparison

### thegent Zen Injection (`cliproxy_manager.py`)

When `THGENT_ZEN_API_KEY` is set, `_inject_zen_into_cliproxy()` adds:

```yaml
openai-compatibility:
  - name: zen
    base-url: https://opencode.ai/zen/v1
    api-key-entries:
      - api-key: "<key>"
    models:
      - { name: glm-5, alias: glm-5 }
      - { name: glm-5, alias: z-ai/glm-5 }
      - { name: glm-5, alias: gpt-5-mini }
      - { name: glm-5, alias: gemini-3-flash }
      # ... plus extras from provider_definitions.json
```

`_ensure_config()` also ensures zen has `gemini-3-flash` and `gpt-5-mini` in models.

### Fork Expected Format (`internal/config/config.go`)

```go
type OpenAICompatibility struct {
    Name         string                         `yaml:"name"`
    BaseURL      string                         `yaml:"base-url"`
    APIKeyEntries []OpenAICompatibilityAPIKey   `yaml:"api-key-entries"`
    Models       []OpenAICompatibilityModel     `yaml:"models"`
}

type OpenAICompatibilityModel struct {
    Name  string `yaml:"name"`   // Actual provider model (e.g. glm-5)
    Alias string `yaml:"alias"` // Routing alias (e.g. gemini-3-flash)
}
```

**Verdict:** Config structure matches. Field names (`base-url`, `api-key-entries`, `api-key`, `name`, `alias`) are identical.

---

## 2. Routing Flow (Fork)

### "unknown provider for model" Source

- **File:** `sdk/api/handlers/handlers.go:652-653`
- **Condition:** `util.GetProviderName(baseModel)` returns empty
- **Meaning:** No provider has registered the requested model in the global registry

### Provider Resolution Chain

1. **`util.GetProviderName(modelName)`** → `registry.GetGlobalRegistry().GetModelProviders(modelName)`
2. **Registry** is populated by `registerModelsForAuth()` in `sdk/cliproxy/service.go`
3. **openai-compat models** are registered in the `default` branch (lines 939–1016):
   - Match `compat.Name` to `compatName` from Auth (e.g. `"zen"`)
   - For each `compat.Models`, use `modelID = m.Alias` (fallback: `m.Name`)
   - `GlobalModelRegistry().RegisterClient(a.ID, providerKey, models)` with `ModelInfo.ID = modelID`

So `gemini-3-flash` is registered when:

- Config has zen entry with `models[].alias == "gemini-3-flash"`
- Synthesizer creates Auth for zen
- `registerModelsForAuth` matches zen Auth to zen compat config

### Auth Synthesis (`internal/watcher/synthesizer/config.go`)

For each `openai-compatibility` entry with `APIKeyEntries`:

- `Provider` = `providerName` (e.g. `"zen"`)
- `Label` = `compat.Name` (`"zen"`)
- `Attributes["compat_name"]` = `compat.Name`
- `Attributes["provider_key"]` = `providerName`

`openAICompatInfoFromAuth()` returns `compatName` from `Attributes["compat_name"]`, so matching works.

### Sanitization

`SanitizeOpenAICompatibility()` drops entries without `base-url`. thegent always provides `base-url` for zen.

---

## 3. Verification Checklist

Before testing, ensure:

| Step | Action                                                                       |
| ---- | ---------------------------------------------------------------------------- |
| 1    | Set `THGENT_ZEN_API_KEY` (or `OPENCODE_API_KEY` / `ZEN_API_KEY`)             |
| 2    | Run `thegent cliproxy ensure-config` or `dex` (which triggers ensure-config) |
| 3    | Confirm zen block in `~/.config/thegent/cliproxy-config.yaml`                |
| 4    | Restart proxy: `thegent cliproxy restart` or `thegent cliproxy start`        |
| 5    | Test: `dex flash -p "hi"` (uses gemini-3-flash)                              |

### Config Check

```bash
grep -A 20 "name: zen" ~/.config/thegent/cliproxy-config.yaml
```

Expected: `name: zen`, `base-url`, `api-key-entries`, and `models` including `alias: gemini-3-flash`.

---

## 4. Troubleshooting

| Symptom                      | Likely Cause                                            | Fix                                                              |
| ---------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------- |
| "unknown provider for model" | Zen not in config or not registered                     | Set key, run ensure-config, restart proxy                        |
| 502 Bad Gateway              | Proxy not running or wrong config path                  | `thegent cliproxy start` with correct config                     |
| Zen missing from config      | Key not set or `_has_provider_credentials` already true | Set `THGENT_ZEN_API_KEY`; remove manual zen block if conflicting |

### Config Path

- thegent: `~/.config/thegent/cliproxy-config.yaml` (from `settings.cliproxy_config_path`)
- Proxy is started with `-config <path>` by thegent

---

## 5. Relevant Paths

| Purpose                     | Path                                                                       |
| --------------------------- | -------------------------------------------------------------------------- |
| Fork root                   | `CLIProxyAPIPlus-fork/`                                                    |
| "unknown provider" error    | `sdk/api/handlers/handlers.go:653`                                         |
| Provider resolution         | `internal/util/provider.go`                                                |
| Model registry              | `internal/registry/model_registry.go`                                      |
| openai-compat registration  | `sdk/cliproxy/service.go:977-1010`                                         |
| openAICompatInfoFromAuth    | `sdk/cliproxy/service.go:350-369`                                          |
| Config struct               | `internal/config/config.go`                                                |
| Synthesizer (openai-compat) | `internal/watcher/synthesizer/config.go:212-306`                           |
| Zen injection (thegent)     | `thegent/src/thegent/agents/cliproxy_manager.py:_inject_zen_into_cliproxy` |
| Provider definitions        | `thegent/src/thegent/agents/cliproxy_data/provider_definitions.json`       |
| Cliproxy config             | `~/.config/thegent/cliproxy-config.yaml`                                   |

---

## 6. Conclusion

- **Fork:** Supports openai-compatibility with model aliases; routes by `models[].alias`; no code changes needed.
- **thegent:** Injects Zen block with `gemini-3-flash` when the key is set; config format matches fork.
- **Action:** If issues persist, verify key, config contents, and proxy restart.
