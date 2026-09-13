# Issue Wave CPB-0805..CPB-0812 Lane D Triage Report

- Lane: `D`
- Scope: `CPB-0805..CPB-0812`
- Mode: triage-only (no code edits)

## CPB Triage Entries

### CPB-0805

- Title focus: Define non-subprocess integration path for Gemini 3 image support (Go bindings + HTTP fallback + capability/version negotiation).
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/integration/capabilities.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/integration/http_fallback.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go`
- Validation command: `rg -n "image|capabilit|fallback|negotiat|gemini-3" cliproxyapi-plusplus/pkg/llmproxy/runtime/integration cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go`

### CPB-0806

- Title focus: Expand docs/examples for Gemini 3 thinking-budget normalization in CLI translation flows.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common/reasoning.go`
  - `cliproxyapi-plusplus/docs/provider-quickstarts.md`
  - `cliproxyapi-plusplus/docs/troubleshooting.md`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common -run "Test.*Reasoning|Test.*Budget"`

### CPB-0807

- Title focus: Add QA scenarios for Gemini 3 Pro Preview with stream/non-stream and edge-case payload parity.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go`
  - `cliproxyapi-plusplus/sdk/api/handlers/openai/openai_handlers_stream_chunk_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_executor_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/sdk/api/handlers/openai -run "Test.*Stream|Test.*Responses|Test.*Gemini"`

### CPB-0808

- Title focus: Refactor prompt-caching path to avoid all-request round-robin and isolate cache transformation boundaries.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/cache/prompt_cache.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor_compact.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cache/prompt_cache_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/cache -run "Test.*Prompt|Test.*Cache"`

### CPB-0809

- Title focus: Rollout safety for Google Antigravity provider via staged defaults, flags, and migration notes.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/feature_flags.go`
  - `cliproxyapi-plusplus/docs/migration-guide.md`
- Validation command: `rg -n "antigravity|feature flag|staged|migration|default" cliproxyapi-plusplus/pkg/llmproxy/config cliproxyapi-plusplus/docs`

### CPB-0810

- Title focus: Standardize metadata/naming for copilot CLI proxy surfaces across config, translator, and UX docs.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go`
  - `cliproxyapi-plusplus/docs/docsets/user/quickstart.md`
- Validation command: `rg -n "copilot|metadata|display_name|model_name|alias" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go cliproxyapi-plusplus/docs/docsets/user/quickstart.md`

### CPB-0811

- Title focus: Close compatibility gaps behind missing `gemini-3-pro-preview` and prevent neighboring-provider regressions.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/thinking_providers.go`
- Validation command: `rg -n "gemini-3-pro-preview|model not found|compat|provider" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/thinking_providers.go`

### CPB-0812

- Title focus: Add deterministic process-compose/HMR refresh flow for gemini-3-pro-preview doc/config/runtime updates.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/process-compose.yaml`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/reload.go`
  - `cliproxyapi-plusplus/docs/docsets/user/quickstart.md`
- Validation command: `rg -n "process-compose|HMR|refresh|reload|gemini-3-pro-preview" cliproxyapi-plusplus/process-compose.yaml cliproxyapi-plusplus/pkg/llmproxy/cmd/reload.go cliproxyapi-plusplus/docs/docsets/user/quickstart.md`

## Read-Only Validation Block

```bash
# rg suggestions
rg -n "image|capabilit|fallback|negotiat|gemini-3" cliproxyapi-plusplus/pkg/llmproxy/runtime/integration cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go
rg -n "antigravity|feature flag|staged|migration|default" cliproxyapi-plusplus/pkg/llmproxy/config cliproxyapi-plusplus/docs
rg -n "copilot|metadata|display_name|model_name|alias" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go cliproxyapi-plusplus/docs/docsets/user/quickstart.md
rg -n "gemini-3-pro-preview|model not found|compat|provider" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/thinking_providers.go
rg -n "process-compose|HMR|refresh|reload|gemini-3-pro-preview" cliproxyapi-plusplus/process-compose.yaml cliproxyapi-plusplus/pkg/llmproxy/cmd/reload.go cliproxyapi-plusplus/docs/docsets/user/quickstart.md

# go test suggestions
go test ./cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common -run "Test.*Reasoning|Test.*Budget"
go test ./cliproxyapi-plusplus/sdk/api/handlers/openai -run "Test.*Stream|Test.*Responses|Test.*Gemini"
go test ./cliproxyapi-plusplus/pkg/llmproxy/cache -run "Test.*Prompt|Test.*Cache"
```
