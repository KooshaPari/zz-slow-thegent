# CPB-0701..0710 Lane E3 Notes

- Lane: `E3 (cliproxy)`
- Date: `2026-02-23`
- Scope: lane-local quickstart, troubleshooting, and verification guidance for the next 10 CPB issues.

## CPB-0701 - OpenAI alias used as model id

### Problem signal

- Requests using alias-only model identifiers fail or resolve unpredictably across OpenAI-compatible paths.

### Lane-safe guidance

1. Confirm alias entries exist in `config.example.yaml` and runtime config.
2. Validate resolved model id with `/v1/models` before sending generation traffic.
3. Reject ambiguous alias collisions during rollout and require unique alias names.

### Verification commands

```bash
rg -n "oauth-model|alias" config.example.yaml pkg/llmproxy/config
rg -n "models" pkg/llmproxy/api/handlers/openai sdk/api/handlers/openai
```

## CPB-0702 - Windows OAuth callback port conflict

### Problem signal

- Login flow fails when fixed callback port is unavailable.

### Lane-safe guidance

1. Confirm callback port can be configured, not hard-coded at runtime.
2. Document deterministic fallback process: reserve port, relaunch auth, verify callback listener.
3. Keep failure explicit with actionable remediation output.

### Verification commands

```bash
rg -n "51121|callback|oauth" pkg/llmproxy/auth sdk/auth
rg -n "port" docs/install.md docs/provider-quickstarts.md
```

## CPB-0703 - `tool_use_id` mismatch in `tool_result`

### Problem signal

- Tool-call flows fail when result blocks reference unexpected IDs.

### Lane-safe guidance

1. Validate request/result ID pairing in translator tests before runtime rollout.
2. Emit explicit mismatch diagnostics including expected and actual IDs.
3. Prefer deterministic rejection over silent mutation.

### Verification commands

```bash
rg -n "tool_use_id|tool_result" pkg/llmproxy/translator pkg/llmproxy/executor
rg -n "tool" pkg/llmproxy/translator/*/*/*_test.go
```

## CPB-0704 - Provider-agnostic `gpt5.2 cherry` error handling

### Problem signal

- Provider-specific response handling diverges for equivalent reasoning payloads.

### Lane-safe guidance

1. Normalize request/response shaping in shared translator utilities.
2. Keep provider adapters thin and fail loudly on unsupported fields.
3. Add parity checks for stream and non-stream paths.

### Verification commands

```bash
rg -n "reasoning|thinking|gpt-5" pkg/llmproxy/translator pkg/llmproxy/thinking
rg -n "stream|non-stream" pkg/llmproxy/translator/*/*/*_test.go
```

## CPB-0705 - Thinking mode unavailable through antigravity proxy

### Problem signal

- Thinking flags accepted at API boundary but dropped before provider execution.

### Lane-safe guidance

1. Trace thinking-related fields from HTTP handler to executor payload.
2. Verify executor path preserves reasoning metadata for Claude code flows.
3. Add explicit error when selected model/provider does not support thinking.

### Verification commands

```bash
rg -n "thinking|reasoning" pkg/llmproxy/api pkg/llmproxy/executor pkg/llmproxy/translator
rg -n "antigravity" pkg/llmproxy/executor pkg/llmproxy/thinking
```

## CPB-0706 - GPT-5.2 docs/examples expansion

### Problem signal

- Users can authenticate successfully but miss model-specific invocation rules.

### Lane-safe guidance

1. Add copy-paste examples for model selection and sanity-check calls.
2. Include troubleshooting for unsupported parameter errors.
3. Link model capability checks to `/v1/models` output.

### Verification commands

```bash
rg -n "gpt-5|models" docs README.md docs/provider-quickstarts.md
```

## CPB-0707 - OAI model failures parity tests

### Problem signal

- Stream and non-stream behavior diverges for identical model config.

### Lane-safe guidance

1. Add paired test cases for stream and non-stream requests.
2. Keep assertions on normalized payload parity and error contract parity.
3. Cover edge payloads (missing fields, mixed legacy/new params).

### Verification commands

```bash
rg -n "stream" pkg/llmproxy/translator pkg/llmproxy/api | head -n 50
rg -n "legacy|compat|normalize" pkg/llmproxy | head -n 50
```

## CPB-0708 - API behavior-change regression hardening

### Problem signal

- Behavioral drift perceived as "API changed" without explicit release note coverage.

### Lane-safe guidance

1. Capture request/response deltas in regression fixtures.
2. Add compatibility notes for intentional changes.
3. Require deterministic tests for previous accepted shapes.

### Verification commands

```bash
rg -n "compat|migration|deprecated" docs pkg/llmproxy
rg -n "fixture|golden" pkg/llmproxy test
```

## CPB-0709 - Missing automatic model discovery

### Problem signal

- New models exist upstream but do not appear in local registry/discovery output.

### Lane-safe guidance

1. Validate registry generation path and model metadata ingestion.
2. Add rollout checks for feature-flag and staged-default behavior.
3. Fail clearly when discovery cannot refresh.

### Verification commands

```bash
rg -n "registry|discover|models" pkg/llmproxy/registry pkg/llmproxy/api
rg -n "feature flag|feature-flag|staged" docs pkg/llmproxy
```

## CPB-0710 - Opus 4.5 thinking tool-calling naming parity

### Problem signal

- Tool-calling fails when naming/capability metadata drifts between translators/executors.

### Lane-safe guidance

1. Keep capability metadata canonical in one registry source.
2. Validate tool-calling field names across OpenAI-compatible and provider-native paths.
3. Record migration notes for renamed/deprecated fields.

### Verification commands

```bash
rg -n "opus|tool calling|tool_call|thinking" pkg/llmproxy docs
rg -n "capabilit|display_name|model" pkg/llmproxy/registry pkg/llmproxy/translator
```
