# Issue Wave CPB-0771..CPB-0780 Lane F Triage Report

- Lane: `F`
- Scope: `CPB-0771..CPB-0780`
- Mode: triage-only (no code edits)

## CPB Triage Entries

### CPB-0771

- Title focus: Claude thinking/tool-use compatibility via `anthropic-beta` header handling.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude/openai_claude_request.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/openai/apply.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude/openai_claude_request_test.go`
- Validation command: `rg -n "anthropic-beta|thinking|tool" cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/openai`

### CPB-0772

- Title focus: Antigravity model reliability hardening for OpenCode CLI flows.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/antigravity/apply.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/antigravity/apply_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/antigravity -run Test`

### CPB-0773

- Title focus: Antigravity native-Gemini ops coverage for model listing and search availability.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/sdk/api/handlers/gemini/gemini_handlers.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go`
- Validation command: `rg -n "antigravity|gemini-3-pro-preview|models" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/sdk/api/handlers/gemini/gemini_handlers.go`

### CPB-0774

- Title focus: System-instruction/cache-control block-limit handling generalized across translators.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/misc/claude_code_instructions.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude/openai_claude_request.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude/openai_claude_request_test.go`
- Validation command: `rg -n "checkSystemInstructions|cache_control|maximum of 4 blocks" cliproxyapi-plusplus/pkg/llmproxy/misc cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude`

### CPB-0775

- Title focus: Thinking budget normalization (`max_tokens` vs `thinking.budget_tokens`) for OpenAI/Gemini compatibility.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common/reasoning.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common/reasoning_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/thinking/validate.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common -run Test.*Reasoning`

### CPB-0776

- Title focus: Anthropic OAuth regression fallout triage plus quickstart/troubleshooting coverage.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/claude/oauth_server.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/claude/anthropic_auth.go`
  - `cliproxyapi-plusplus/docs/provider-quickstarts.md`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/auth/claude -run Test.*OAuth`

### CPB-0777

- Title focus: Droid-provider QA parity for stream and non-stream response surfaces.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/sdk/api/handlers/openai/openai_handlers_stream_chunk_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor_compact_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/sdk/api/handlers/openai -run "Test.*Stream|Test.*Responses"`

### CPB-0778

- Title focus: Structured-output/JSON-schema translation boundary cleanup.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/util/gemini_schema.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/util/gemini_schema_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor_schema_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/util -run Test.*Schema`

### CPB-0779

- Title focus: Thinking-path parity across OpenAI/Gemini/Claude with CLI command-surface implications.
- Likely impacted paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/thinking_providers.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
- Validation command: `rg -n "sonnet-4-5|thinking|provider" cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/thinking_providers.go cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`

### CPB-0780

- Title focus: Docker-deployed Gemini login metadata/naming consistency across docs and CLI UX.
- Likely impacted paths:
  - `cliproxyapi-plusplus/docker-compose.yml`
  - `cliproxyapi-plusplus/docs/docsets/user/quickstart.md`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go`
- Validation command: `rg -n "docker|gemini|login|auth" cliproxyapi-plusplus/docker-compose.yml cliproxyapi-plusplus/docs/docsets/user/quickstart.md cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go`

## Validation Block

```bash
rg -n "anthropic-beta|thinking|tool" cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/openai
go test ./cliproxyapi-plusplus/pkg/llmproxy/thinking/provider/antigravity -run Test
rg -n "antigravity|gemini-3-pro-preview|models" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/sdk/api/handlers/gemini/gemini_handlers.go
rg -n "checkSystemInstructions|cache_control|maximum of 4 blocks" cliproxyapi-plusplus/pkg/llmproxy/misc cliproxyapi-plusplus/pkg/llmproxy/translator/openai/claude
go test ./cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common -run Test.*Reasoning
go test ./cliproxyapi-plusplus/pkg/llmproxy/auth/claude -run Test.*OAuth
go test ./cliproxyapi-plusplus/sdk/api/handlers/openai -run "Test.*Stream|Test.*Responses"
go test ./cliproxyapi-plusplus/pkg/llmproxy/util -run Test.*Schema
rg -n "sonnet-4-5|thinking|provider" cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/thinking_providers.go cliproxyapi-plusplus/pkg/llmproxy/config/providers.json
rg -n "docker|gemini|login|auth" cliproxyapi-plusplus/docker-compose.yml cliproxyapi-plusplus/docs/docsets/user/quickstart.md cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go
```
