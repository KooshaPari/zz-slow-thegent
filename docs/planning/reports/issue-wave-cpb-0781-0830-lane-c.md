# Issue Wave CPB-0781..CPB-0830 Lane C Triage Report

- Lane: `C`
- Scope slice: `CPB-0797..CPB-0804`
- Mode: triage-only (report-only, no code edits)

## CPB Triage Entries

### CPB-0797

- Title focus: Add token-count QA coverage with stream/non-stream parity and edge-case payload handling.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/token_helpers.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/token_helpers_test.go`
  - `cliproxyapi-plusplus/sdk/translator/helpers.go`
- Validation command: `rg -n "count token|count_tokens|token counting|stream" cliproxyapi-plusplus/pkg/llmproxy/executor/token_helpers.go cliproxyapi-plusplus/pkg/llmproxy/executor/token_helpers_test.go cliproxyapi-plusplus/sdk/translator/helpers.go`

### CPB-0798

- Title focus: Promote "cursor with antigravity" flow into first-class Go CLI setup/login command paths.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/cursor_login.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/antigravity_login.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/setup.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/cmd -run "TestCursor|TestSetup"`

### CPB-0799

- Title focus: Refresh provider quickstart guidance for proxy-auth, model selection, and sanity-check flow.
- Likely impacted paths:
  - `cliproxyapi-plusplus/docs/provider-quickstarts.md`
  - `cliproxyapi-plusplus/docs/docsets/user/quickstart.md`
  - `cliproxyapi-plusplus/docs/troubleshooting.md`
- Validation command: `rg -n "proxy|auth|model|sanity|quickstart" cliproxyapi-plusplus/docs/provider-quickstarts.md cliproxyapi-plusplus/docs/docsets/user/quickstart.md cliproxyapi-plusplus/docs/troubleshooting.md`

### CPB-0800

- Title focus: Standardize OAuth metadata/naming around headless or remote `--manual-callback` usage.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/codex/oauth_server.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/oauth_callback.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/misc/oauth.go`
- Validation command: `rg -n "manual-callback|callback|headless|oauth" cliproxyapi-plusplus/pkg/llmproxy/auth/codex/oauth_server.go cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/oauth_callback.go cliproxyapi-plusplus/pkg/llmproxy/misc/oauth.go`

### CPB-0801

- Title focus: Close `gemini-3-pro-preview` regression risk by restoring robust 429 retry semantics.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor_retry_delay_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/executor -run "Test.*Retry.*|Test.*429.*"`

### CPB-0802

- Title focus: Harden AI Studio + Roo Code interoperability when Gemini 3 Pro returns no response.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/aistudio_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go`
  - `cliproxyapi-plusplus/docs/troubleshooting.md`
- Validation command: `rg -n "AI Studio|Roo Code|no response|gemini-3-pro" cliproxyapi-plusplus/pkg/llmproxy/executor/aistudio_executor.go cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go cliproxyapi-plusplus/docs/troubleshooting.md`

### CPB-0803

- Title focus: Operationalize HuggingFace-facing failures with clearer diagnostics and runbook alignment.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go`
  - `cliproxyapi-plusplus/docs/troubleshooting.md`
  - `cliproxyapi-plusplus/docs/provider-quickstarts.md`
- Validation command: `rg -n "huggingface|diagnostic|remediation|error" cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go cliproxyapi-plusplus/docs/troubleshooting.md cliproxyapi-plusplus/docs/provider-quickstarts.md`

### CPB-0804

- Title focus: Generalize Codex `/responses` Not Found handling into shared provider-agnostic translation patterns.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/codex_executor.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor.go`
  - `cliproxyapi-plusplus/sdk/translator/helpers.go`
- Validation command: `rg -n "backend-api/codex|/responses|Not Found|provider-agnostic" cliproxyapi-plusplus/pkg/llmproxy/executor/codex_executor.go cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor.go cliproxyapi-plusplus/sdk/translator/helpers.go`

## Read-Only Validation Block

```bash
rg -n "count token|count_tokens|token counting|stream" cliproxyapi-plusplus/pkg/llmproxy/executor/token_helpers.go cliproxyapi-plusplus/pkg/llmproxy/executor/token_helpers_test.go cliproxyapi-plusplus/sdk/translator/helpers.go
go test ./cliproxyapi-plusplus/pkg/llmproxy/cmd -run "TestCursor|TestSetup"
rg -n "proxy|auth|model|sanity|quickstart" cliproxyapi-plusplus/docs/provider-quickstarts.md cliproxyapi-plusplus/docs/docsets/user/quickstart.md cliproxyapi-plusplus/docs/troubleshooting.md
rg -n "manual-callback|callback|headless|oauth" cliproxyapi-plusplus/pkg/llmproxy/auth/codex/oauth_server.go cliproxyapi-plusplus/pkg/llmproxy/api/handlers/management/oauth_callback.go cliproxyapi-plusplus/pkg/llmproxy/misc/oauth.go
go test ./cliproxyapi-plusplus/pkg/llmproxy/executor -run "Test.*Retry.*|Test.*429.*"
rg -n "AI Studio|Roo Code|no response|gemini-3-pro" cliproxyapi-plusplus/pkg/llmproxy/executor/aistudio_executor.go cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_cli_executor.go cliproxyapi-plusplus/docs/troubleshooting.md
rg -n "huggingface|diagnostic|remediation|error" cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go cliproxyapi-plusplus/docs/troubleshooting.md cliproxyapi-plusplus/docs/provider-quickstarts.md
rg -n "backend-api/codex|/responses|Not Found|provider-agnostic" cliproxyapi-plusplus/pkg/llmproxy/executor/codex_executor.go cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor.go cliproxyapi-plusplus/sdk/translator/helpers.go
```
