# Issue Wave CPB-0813..CPB-0820 Lane E Triage Report

- Lane: `E`
- Scope: `CPB-0813..CPB-0820`
- Mode: triage-only (no code edits)

## CPB Triage Entries

### CPB-0813

- Title focus: Operationalize VPS account-ban risk with observability, alert thresholds, and runbook guidance.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/middleware/logger.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/server/http_server.go`
  - `cliproxyapi-plusplus/docs/docsets/user/troubleshooting.md`
- Validation command: `rg -n "ban|blocked|rate limit|observability|runbook" cliproxyapi-plusplus/pkg/llmproxy cliproxyapi-plusplus/docs`

### CPB-0814

- Title focus: Correct `auth-dir` default behavior and enforce provider-agnostic auth-path resolution.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/config/config.example.yaml`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/config.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/common/path_resolver.go`
- Validation command: `rg -n "auth-dir|auth_dir|auth directory|default" cliproxyapi-plusplus/config cliproxyapi-plusplus/pkg/llmproxy/config cliproxyapi-plusplus/pkg/llmproxy/auth`

### CPB-0815

- Title focus: Harden auth directory permissions (`0700`) and improve DX feedback around insecure modes.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/common/fs.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/auth/common/fs_test.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/auth/common -run "Test.*Perm|Test.*Auth.*Dir"`

### CPB-0816

- Title focus: Refresh Gemini OAuth quickstart for Claude Code workflows with explicit sanity-check steps.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/docs/provider-quickstarts.md`
  - `cliproxyapi-plusplus/docs/docsets/user/quickstart.md`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go`
- Validation command: `rg -n "Gemini|OAuth|Claude Code|quickstart|sanity" cliproxyapi-plusplus/docs/provider-quickstarts.md cliproxyapi-plusplus/docs/docsets/user/quickstart.md`

### CPB-0817

- Title focus: Promote failing Gemini CLI flow into first-class Go CLI command path with interactive setup.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/root.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/login.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/cmd/models.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/cmd -run "Test.*Gemini|Test.*Login|Test.*Models"`

### CPB-0818

- Title focus: Update model-ID transformation boundaries to track fast-moving GPT minor versions.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common/model_aliases.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common/model_aliases_test.go`
- Validation command: `rg -n "gpt-5|5\.1|model alias|model_id|model-id" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common`

### CPB-0819

- Title focus: Stabilize `/compress` session-compaction behavior for Gemini 2.5 with guarded rollout controls.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor_compact.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/runtime/executor/codex_executor_compact_test.go`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/gemini_executor.go`
- Validation command: `go test ./cliproxyapi-plusplus/pkg/llmproxy/runtime/executor -run "Test.*Compact|Test.*Compress"`

### CPB-0820

- Title focus: Standardize registry metadata/naming for `gpt-5-pro` across config and provider surfaces.
- Likely impacted file paths:
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/config/providers.schema.json`
  - `cliproxyapi-plusplus/pkg/llmproxy/executor/openai_compat_executor.go`
- Validation command: `rg -n "gpt-5-pro|metadata|alias|display_name|model_name" cliproxyapi-plusplus/pkg/llmproxy/config cliproxyapi-plusplus/pkg/llmproxy/executor`

## Read-Only Validation Block

```bash
rg -n "ban|blocked|rate limit|observability|runbook" cliproxyapi-plusplus/pkg/llmproxy cliproxyapi-plusplus/docs
rg -n "auth-dir|auth_dir|auth directory|default" cliproxyapi-plusplus/config cliproxyapi-plusplus/pkg/llmproxy/config cliproxyapi-plusplus/pkg/llmproxy/auth
go test ./cliproxyapi-plusplus/pkg/llmproxy/auth/common -run "Test.*Perm|Test.*Auth.*Dir"
rg -n "Gemini|OAuth|Claude Code|quickstart|sanity" cliproxyapi-plusplus/docs/provider-quickstarts.md cliproxyapi-plusplus/docs/docsets/user/quickstart.md
go test ./cliproxyapi-plusplus/pkg/llmproxy/cmd -run "Test.*Gemini|Test.*Login|Test.*Models"
rg -n "gpt-5|5\.1|model alias|model_id|model-id" cliproxyapi-plusplus/pkg/llmproxy/config/providers.json cliproxyapi-plusplus/pkg/llmproxy/translator/openai/common
go test ./cliproxyapi-plusplus/pkg/llmproxy/runtime/executor -run "Test.*Compact|Test.*Compress"
rg -n "gpt-5-pro|metadata|alias|display_name|model_name" cliproxyapi-plusplus/pkg/llmproxy/config cliproxyapi-plusplus/pkg/llmproxy/executor
```
