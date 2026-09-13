# Issue Wave CPB-0821..CPB-0830 Lane F Triage Report

- Lane: `F`
- Scope: `CPB-0821..CPB-0830`
- Mode: triage-only (no code edits)

## CPB Triage Entries

### CPB-0821

- Title focus: Gemini OAuth unknown-provider compatibility gaps in Droid CLI/provider registry mapping.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/gemini/gemini_auth.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/sdk/api/handlers/gemini/gemini-cli_handlers.go`
- Validation command: `rg -n "unknown provider|gemini|oauth|droid" cliproxyapi-plusplus/pkg/llmproxy/auth/gemini cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/sdk/api/handlers/gemini`

### CPB-0822

- Title focus: Auth-file management主动同步 hardening with safer validation/fallback behavior.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/auth_files.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/synthesizer/file.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/auth_files_callback_forwarder_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management -run Test.*AuthFiles`

### CPB-0823

- Title focus: Kimi K2 Thinking operational readiness (observability, thresholds, runbook alignment).
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/kimi_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/gemini/apply.go`
  - `cliproxyapi-plusplus/docs/operations/release-governance.md`
- Validation command: `rg -n "kimi|thinking|reasoning|threshold|log" cliproxyapi-plusplus/pkg/llmproxy/executor/kimi_executor.go cliproxyapi-plusplus/pkg/llmproxy/thinking cliproxyapi-plusplus/docs/operations/release-governance.md`

### CPB-0824

- Title focus: “nano banana 水印” generalized into provider-agnostic translation utilities.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/util/translator.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/util/translator_test.go`
  - `cliproxyapi-plusplus/docs/provider-quickstarts.md`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/util -run Test.*Translator`

### CPB-0825

- Title focus: AI Studio unusable DX/ops polish via clearer CLI ergonomics and handler boundaries.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/gemini_cli_executor.go`
  - `cliproxyapi-plusplus/docs/docsets/user/quickstart.md`
- Validation command: `rg -n "ai studio|gemini cli|auth|init|login" cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/gemini_cli_executor.go cliproxyapi-plusplus/docs/docsets/user/quickstart.md`

### CPB-0826

- Title focus: Scoped `auto` model docs/compat expansion with explicit logging and troubleshooting.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_compat_executor.go`
  - `cliproxyapi-plusplus/docs/docsets/developer/external/integration-quickstart.md`
- Validation command: `rg -n "scoped|auto|provider\s*\+\s*pattern|normalized config" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_compat_executor.go cliproxyapi-plusplus/docs/docsets/developer/external/integration-quickstart.md`

### CPB-0827

- Title focus: WSS链接失败 QA matrix for stream/non-stream parity and rollout toggles.
- Likely impacted paths:
  - `cliproxyapi-plusplus/sdk/api/handlers/openai/openai_responses_websocket.go`
  - `cliproxyapi-plusplus/sdk/api/handlers/openai/openai_responses_websocket_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/api/responses_websocket_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/sdk/api/handlers/openai -run Test.*Websocket`

### CPB-0828

- Title focus: GPT-5.1 `-none` suffix integration path for Go bindings + HTTP fallback negotiation.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/thinking/suffix.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/interfaces/client_models.go`
  - `cliproxyapi-plusplus/docs/docsets/developer/external/integration-quickstart.md`
- Validation command: `rg -n "gpt-5\.1|-none|capability|fallback|version" cliproxyapi-plusplus/pkg/llmproxy/thinking/suffix.go cliproxyapi-plusplus/pkg/llmproxy/interfaces/client_models.go cliproxyapi-plusplus/docs/docsets/developer/external/integration-quickstart.md`

### CPB-0829

- Title focus: Candidate-count multi-response rollout safety with feature flags and contract tests.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_compat_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/model_definitions.go`
  - `cliproxyapi-plusplus/sdk/api/handlers/openai/endpoint_compat_test.go`
- Validation command: `rg -n "candidate_count|multiple|responses|feature flag" cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_compat_executor.go cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/model_definitions.go cliproxyapi-plusplus/sdk/api/handlers/openai/endpoint_compat_test.go`

### CPB-0830

- Title focus: GPT-5.1 model-add naming/metadata standardization plus migration-note hygiene.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/registry/model_definitions.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/docs/guides/release-batching.md`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/registry -run Test.*ModelDefinitions`

## Read-Only Validation Block (suggestions: `rg` / `go test` only)

```bash
rg -n "unknown provider|gemini|oauth|droid" cliproxyapi-plusplus/pkg/llmproxy/auth/gemini cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/sdk/api/handlers/gemini
go test ./cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management -run Test.*AuthFiles
rg -n "kimi|thinking|reasoning|threshold|log" cliproxyapi-plusplus/pkg/llmproxy/executor/kimi_executor.go cliproxyapi-plusplus/pkg/llmproxy/thinking cliproxyapi-plusplus/docs/operations/release-governance.md
go test ./cliproxyapi-plusplus/pkg/llmproxy/util -run Test.*Translator
rg -n "ai studio|gemini cli|auth|init|login" cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/gemini_cli_executor.go cliproxyapi-plusplus/docs/docsets/user/quickstart.md
rg -n "scoped|auto|provider\s*\+\s*pattern|normalized config" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_compat_executor.go cliproxyapi-plusplus/docs/docsets/developer/external/integration-quickstart.md
go test ./cliproxyapi-plusplus/sdk/api/handlers/openai -run Test.*Websocket
rg -n "gpt-5\.1|-none|capability|fallback|version" cliproxyapi-plusplus/pkg/llmproxy/thinking/suffix.go cliproxyapi-plusplus/pkg/llmproxy/interfaces/client_models.go cliproxyapi-plusplus/docs/docsets/developer/external/integration-quickstart.md
rg -n "candidate_count|multiple|responses|feature flag" cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/openai_compat_executor.go cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/model_definitions.go cliproxyapi-plusplus/sdk/api/handlers/openai/endpoint_compat_test.go
go test ./cliproxyapi-plusplus/pkg/llmproxy/registry -run Test.*ModelDefinitions
```
