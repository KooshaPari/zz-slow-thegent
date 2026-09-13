# Provider Setup Guide

Per-provider OAuth, token-file, and refresh instructions for thegent + CLIProxyAPIPlus.

---

## Primary cliproxy/provider docs

- This guide: `docs/guides/PROVIDER_SETUP_GUIDE.md` (operational setup, login, routing, troubleshooting)
- Public docsite provider quickstart: `docs/site/guide/providers.md`
- Provider model catalog: `docs/reference/PROVIDER_MODEL_REFERENCE.md`
- Adapter behavior: `docs/contracts/PROVIDER_ADAPTER_CONTRACTS.md` and `docs/contracts/FALLBACK_POLICY.md`

## Quick start: get proxy agents passing

All providers use CLIProxyAPIPlus native config. Provider/model definitions are internal (no external config dependency):

1. **Start proxy:** `thegent mcp up` (or `thegent cliproxy start` for proxy only)
2. **OAuth login (preferred):** `thegent cliproxy login <provider>` — for claude, codex, gemini, qwen, glm, roo, kilo, kimi, copilot, antigravity, iflow, kiro. Opens browser, completes OAuth, stores tokens.
3. **API-key login (minimax, nim only):** `thegent cliproxy login minimax` or `thegent cliproxy login nim` — opens URL, prompts for API key, writes to config. Use `--force` to re-enter.
4. **Verify:** `thegent run "Output only 1" minimax` (or glm, antigravity, cliproxy)

**Proxy management:** `thegent cliproxy start` | `thegent cliproxy stop` | `thegent cliproxy restart`. After config changes, run `thegent cliproxy restart`.

**MCP + browser tools (single config):** `thegent mcp up` bundles Playwright, Serena, and Octocode. Use `thegent mcp install cursor` (or `all`) to add thegent and remove manual playwright from Cursor/Claude Code/Codex. One MCP entry = thegent + browser + LSP + code search. All mounts required by default.

**macOS LaunchAgent (runs at login):** `thegent cliproxy service install` then `thegent cliproxy service start`.

**Debug mode (model/provider/latency tags):** `thegent run --debug "task" minimax` or `thegent bg --debug "task" glm`. Sets `THGENT_DEBUG=1`; proxy started with `-debug` when env is set. See [DEBUG_TAGS_AND_METRICS.md](../plans/DEBUG_TAGS_AND_METRICS.md).

---

## Login (thegent cliproxy login)

All providers use `thegent cliproxy login <provider>`. **OAuth (preferred):** browser opens → log in → tokens stored. **API-key (minimax, nim only):** open URL → prompt for key → save to config. Use `--force` to re-enter.

| Provider    | Command                                              | Notes                                  |
| ----------- | ---------------------------------------------------- | -------------------------------------- |
| Claude      | `thegent cliproxy login claude`                      | Anthropic OAuth                        |
| Codex       | `thegent cliproxy login codex`                       | OpenAI OAuth                           |
| Gemini      | `thegent cliproxy login gemini`                      | Google OAuth                           |
| Copilot     | `thegent cliproxy login copilot`                     | GitHub Copilot OAuth                   |
| Antigravity | `thegent cliproxy login antigravity`                 | Antigravity OAuth                      |
| Qwen        | `thegent cliproxy login qwen`                        | Alibaba Qwen OAuth                     |
| iFlow       | `thegent cliproxy login iflow`                       | iFlow OAuth (GLM)                      |
| Kimi        | `thegent cliproxy login kimi`                        | Moonshot Kimi OAuth                    |
| Kiro        | `thegent cliproxy login kiro`                        | AWS CodeWhisperer (Google OAuth)       |
| Kiro AWS    | `thegent cliproxy login kiro-aws`                    | Kiro via AWS Builder ID                |
| Kiro import | `thegent cliproxy login kiro-import`                 | Import from Kiro IDE                   |
| Roo         | `thegent cliproxy login roo` / `thegent login roo`   | Roo Code Cloud (runs `roo auth login`) |
| Kilo        | `thegent cliproxy login kilo` / `thegent login kilo` | Kilo auth wizard (runs `kilo auth`)    |
| MiniMax     | `thegent cliproxy login minimax`                     | API-key only (no OAuth)                |
| NIM         | `thegent cliproxy login nim`                         | NVIDIA NIM API-key only (no OAuth)     |

**Flow (CLIProxy providers):** Run the command → browser opens → log in → tokens stored in `~/.cli-proxy-api`. CLIProxyAPIPlus merges them into config on first proxy start.

**Flow (roo, kilo):** `thegent login roo` / `thegent login kilo` (or `thegent cliproxy login roo/kilo`) invokes `roo auth login` or `kilo auth` directly. Tokens stored in provider-specific paths. Ensure CLIProxy config has the roo/kilo block (see below).

---

## Provider model mapping (practical)

Use this table when choosing harness commands (`clode`, `dex`, `roid`) and cliproxy login targets.

| Alias                           | Typical model ID                             | Primary provider route(s)                             | Login command                                                  |
| ------------------------------- | -------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------- |
| `clode` (default, no model arg) | `gemini-3-flash`                             | `gemini` flash path                                   | `thegent cliproxy login gemini`                                |
| `dex` (default, no model arg)   | `gemini-3-flash`                             | `gemini` flash path                                   | `thegent cliproxy login gemini`                                |
| `dex` (explicit model alias)    | `gpt-5.3-codex`                              | `codex` (non-spark)                                   | `thegent cliproxy login codex`                                 |
| `high` / `xhigh`                | `gpt-5.3-codex-high` / `gpt-5.3-codex-xhigh` | `codex` (available on `clode` + `dex`)                | `thegent cliproxy login codex`                                 |
| `haiku`                         | `claude-haiku-4.5`                           | `claude`, `antigravity`, `codex`, `kiro`              | `thegent cliproxy login claude`                                |
| `opus`                          | `claude-opus-4.6`                            | `claude`, `antigravity`, `kiro`                       | `thegent cliproxy login claude`                                |
| `sonnet`                        | `anthropic/claude-sonnet-4-20250514`         | `openrouter`                                          | `thegent cliproxy login claude` (or `openrouter` route config) |
| `flash`                         | `gemini-3-flash`                             | `gemini` (or proxy-mapped alternatives)               | `thegent cliproxy login gemini`                                |
| `mini`                          | `gpt-5-mini`                                 | `codex`/OpenAI-compatible routes                      | `thegent cliproxy login codex`                                 |
| `glm`                           | `glm-5`                                      | `iflow`, `kilo`, `nim`, `minimax` (catalog dependent) | `thegent cliproxy login iflow` / `nim` / `minimax`             |
| `max`                           | `minimax-m2.5`                               | `minimax`                                             | `thegent cliproxy login minimax`                               |
| `composer`                      | Cursor/OpenAI-compatible model alias         | `cursor` + configured backend route                   | `thegent cliproxy login cursor`                                |

Check current resolved routing before long runs:

```bash
thegent resolve-model-route -M claude-haiku-4.5
thegent resolve-model-route -M gemini-3-flash
thegent list-models --provider minimax
```

## WL-118: Ollama alias normalization map

For local Ollama routing, thegent normalizes these provider aliases to canonical `ollama` before route/model resolution:

| Input alias        | Canonical provider |
| ------------------ | ------------------ |
| `ollama-local`     | `ollama`           |
| `local-ollama`     | `ollama`           |
| `ollama-localhost` | `ollama`           |
| `ollama@localhost` | `ollama`           |

Normalization is case-insensitive and trims surrounding whitespace, so values like `OLLAMA-LOCAL` and `local-ollama` resolve identically.

## WL-118: `thegent doctor` Ollama remediation playbook

Use `thegent doctor` to validate local Ollama routing prerequisites before running `--provider ollama`.

| Doctor output signal                              | Meaning                              | Actionable remediation                                                               |
| ------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------ |
| `Ollama CLI not found in PATH`                    | `ollama` binary is missing           | Install from `https://ollama.com/download`, then reopen shell and run `which ollama` |
| `daemon is not reachable on 127.0.0.1:11434`      | daemon not running/listening         | Start daemon: `ollama serve`, then re-run `thegent doctor`                           |
| `daemon probe timed out on 127.0.0.1:11434`       | daemon hung or overloaded            | Restart daemon and verify endpoint: `curl http://127.0.0.1:11434/api/tags`           |
| `reachable ... but no local models are installed` | daemon is up but model catalog empty | Pull at least one model, for example: `ollama pull llama3.3`                         |
| `endpoint returned HTTP <code>`                   | daemon returned an API error         | Check `ollama serve` logs, confirm `/api/tags` returns HTTP 200, then retry          |

Quick remediation loop:

```bash
thegent doctor
ollama serve
ollama pull llama3.3
curl http://127.0.0.1:11434/api/tags
thegent doctor
```

## API key env vars and auth mode

| Env var              | Used by                          | Typical mode                                                                 |
| -------------------- | -------------------------------- | ---------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`  | Claude/Anthropic-compatible path | OAuth-derived token or direct key                                            |
| `OPENAI_API_KEY`     | OpenAI/Codex-compatible path     | OAuth-derived token, direct key, or `sk-dummy` for local proxy adapter flows |
| `GOOGLE_API_KEY`     | Gemini direct path               | Direct API key                                                               |
| `THGENT_ZEN_API_KEY` | Zen provider path                | Direct API key                                                               |

Notes:

- For most cliproxy providers, preferred auth is `thegent cliproxy login <provider>` (OAuth/token-file).
- API-key-only providers in this guide: `minimax`, `nim`.
- For Codex CLI against local cliproxy, `OPENAI_BASE_URL=http://127.0.0.1:8317/v1` with a proxy-accepted key (`sk-dummy` in local adapter examples) is expected.

## Adapter vs native behavior

Use adapter mode when you want one endpoint and provider failover. Use native mode when you must bypass thegent/cliproxy routing.

| Mode                             | What happens                                                     | Command pattern                                       |
| -------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| Adapter (default)                | Harness routes through thegent + cliproxy provider model mapping | `clode haiku ...`, `dex flash ...`, `thegent run ...` |
| Native bypass (`clode`)          | Calls native Claude CLI directly                                 | `clode --native`                                      |
| Native bypass (`dex`)            | Calls native Codex CLI directly                                  | `dex --native`                                        |
| Droid alias passthrough (`roid`) | Rewrites alias to droid model flag and forwards args             | `roid flash ...` / `roid flash exec ...`              |

## Failover expectations

- Routing policy is controlled by `THGENT_DEFAULT_ROUTING` and per-command `-R/--routing`.
- `prefer_direct`: try direct/provider-native routes first.
- `prefer_proxy`: bias proxy routes.
- `failover`: attempt alternate provider routes for the same model family when primary route fails.
- Adapter normalization fallback policy is controlled separately (`docs/contracts/FALLBACK_POLICY.md`), including strict providers and confidence thresholds.
- Verify route behavior quickly with:

```bash
thegent run "Output only 1" -M gemini-3-flash -R failover
thegent run "Output only 1" -M claude-haiku-4.5 -R prefer_direct
```

## clode / dex / roid practical examples

### Interactive

```bash
# clode default (no alias) => flash path
clode

# dex default (no alias) => flash path
dex

# Claude harness (model alias)
clode haiku

# Codex harness (model alias)
dex flash

# clode run dex => codex non-spark (gpt-5.3-codex)
clode run dex "ship it"

# codex tier aliases available on both clode and dex
clode high
dex xhigh

# Droid harness via alias
roid flash
```

### Headless exec / CI-style

```bash
# clode headless print (validated by doctor check path)
clode haiku --print "Respond with exactly: pong"

# dex headless print (validated by doctor check path)
dex flash --print "Respond with exactly: pong"

# roid exec passthrough preflight (headless command path)
roid flash exec --help
```

### Provider-specific routing checks before execution

```bash
thegent cliproxy login claude
thegent cliproxy login codex
thegent cliproxy login gemini
thegent doctor
```

---

## Cursor (cursor-api + zero-action) — Phase 2

> G-CP-01 / G-CP-02 / G-CP-03 — implements the full Cursor dedicated block with
> token-file provider, automatic refresh, and rebindExecutors (WL-018).

### CLIProxy cursor: schema

CLIProxyAPIPlus accepts a `cursor:` top-level key. Two auth variants:

| Variant      | When to use                         | Config key                               |
| ------------ | ----------------------------------- | ---------------------------------------- |
| `token-file` | sk-... from cursor-api `/build-key` | `token-file: "<path>"`                   |
| `auth-token` | zero-action (IDE auto-injects)      | `auth-token: "${CURSOR_API_AUTH_TOKEN}"` |

### Option A — Zero-action (recommended)

Log in to Cursor IDE only. Set `THGENT_CURSOR_API_TOKEN` to cursor-api `AUTH_TOKEN`:

```yaml
# ~/.config/thegent/cliproxy-config.yaml
cursor:
  - cursor-api-url: "http://127.0.0.1:3000"
    auth-token: "${CURSOR_API_AUTH_TOKEN}" # Must match cursor-api AUTH_TOKEN env
```

Token is auto-read from Cursor IDE storage (`state.vscdb`). No manual copy required.

### Option B — token-file (Phase 2)

Run cursor-api `/build-key`, write the `sk-...` token to a file:

```bash
# Step 1: start cursor-api (wisdgod)
cursor-api --port 3000

# Step 2: build a session key
TOKEN=$(curl -s http://127.0.0.1:3000/build-key | jq -r .key)
echo "$TOKEN" > ~/.cursor/session-token.txt
chmod 600 ~/.cursor/session-token.txt

# Step 3: set env vars (or add to ~/.config/thegent/cliproxy-config.yaml)
export THGENT_CURSOR_API_URL=http://127.0.0.1:3000
export THGENT_CURSOR_TOKEN_FILE=~/.cursor/session-token.txt
```

CLIProxy config (written automatically by `thegent cliproxy ensure-config`):

```yaml
cursor:
  - token-file: "~/.cursor/session-token.txt"
    cursor-api-url: "http://127.0.0.1:3000"
```

### Token refresh (automatic)

`CursorTokenProvider` re-reads the token file every `THGENT_CURSOR_TOKEN_REFRESH_INTERVAL`
seconds (default 300). On mtime change the token is considered rotated.

When the token rotates, `CursorExecutorManager.rebind_executors()` closes all active
httpx sessions so the next request uses the new bearer token. No manual restart needed.

```bash
# Override refresh interval (e.g. 60 s for short-lived tokens)
export THGENT_CURSOR_TOKEN_REFRESH_INTERVAL=60
```

### Verifying the connection

```bash
thegent run "Output only the number 1" cursor
# Expected: exit 0, stdout contains "1"

# Or via proxy health check
curl -s http://127.0.0.1:8317/v1/models | jq '.models[] | select(.id | startswith("cursor"))'
```

### Auto-discovery

When `THGENT_CURSOR_TOKEN_FILE` is not set, thegent probes these paths in order:

1. `~/.cursor-server/session-token.txt`
2. `~/.cursor/session-token.txt`
3. `~/.config/cursor/session-token.txt`

The first readable file wins.

### Environment variables

| Variable                               | Default                 | Purpose                                                  |
| -------------------------------------- | ----------------------- | -------------------------------------------------------- |
| `THGENT_CURSOR_API_URL`                | `http://127.0.0.1:3000` | cursor-api base URL                                      |
| `THGENT_CURSOR_API_TOKEN`              | ``                      | sk-... or AUTH_TOKEN (written to token file when sk-...) |
| `THGENT_CURSOR_TOKEN_FILE`             | auto                    | Override token-file path                                 |
| `THGENT_CURSOR_TOKEN_REFRESH_INTERVAL` | 300                     | Seconds between token re-reads                           |

---

## MiniMax (api-key; no OAuth)

**Automated:** `thegent cliproxy login minimax` prompts for your API key and writes it to config. Get key from [platform.minimax.io](https://platform.minimax.io). Restart proxy after login.

**Manual:** Add to `~/.config/thegent/cliproxy-config.yaml`:

```yaml
minimax:
  - api-key: "sk-..."
    base-url: "https://api.minimax.io/v1"
```

**Base URL:** `https://api.minimax.io/v1`

---

## GLM (via iFlow)

**OAuth:** `thegent cliproxy login iflow` (or `thegent cliproxy login glm`). GLM models (glm-5, glm-4.7) are served via the iFlow channel.

---

## Roo Code (token-file or API key)

**OAuth:** Run `thegent cliproxy login roo` (invokes `roo auth login`). Token stored in `~/.config/roo/credentials.json`.

**Token-file (OAuth/Cloud):**

```yaml
roo:
  - token-file: "~/.config/roo/credentials.json"
    base-url: "https://api.roocode.com/v1"
```

Or legacy path:

```yaml
roo:
  - token-file: "~/.roo/oauth-token.json"
    base-url: "https://api.roocode.com/v1"
```

**API key:**

```yaml
roo:
  - api-key: "sk-..."
    base-url: "https://api.roocode.com/v1"
```

**Refresh:** Update token-file when token expires.

---

## Kilo (token-file or API key)

**OAuth:** Run `thegent cliproxy login kilo` (invokes `kilo auth`). Interactive wizard configures provider; credentials stored in `~/.kilocode/cli/`.

**Free credits:** Sign up at kilo.ai; optional API key.

**Token-file:**

```yaml
kilo:
  - token-file: "~/.kilo/token.json"
    base-url: "https://api.kilo.ai/v1"
```

**API key:**

```yaml
kilo:
  - api-key: "sk-..."
    base-url: "https://api.kilo.ai/v1"
```

**Refresh:** Update token-file when token expires.

---

## Kiro (AWS CodeWhisperer)

**Token-file (SSO cache):**

```yaml
kiro:
  - token-file: "~/.aws/sso/cache/kiro-auth-token.json"
```

**Refresh:** CLIProxyAPIPlus background refresh; Kiro tokens auto-renew.

---

## thegent run commands

| Agent      | Command                        | Default model        |
| ---------- | ------------------------------ | -------------------- |
| cliproxy   | `thegent run cliproxy "..."`   | gemini-3-flash       |
| minimax    | `thegent run minimax "..."`    | minimax-m2.5         |
| glm        | `thegent run glm "..."`        | glm-5                |
| roo        | `thegent run roo "..."`        | roo-default          |
| kilo       | `thegent run kilo "..."`       | kilo-default         |
| cursor-api | `thegent run cursor-api "..."` | claude-4.5-opus-high |

---

## Codex CLI with CLIProxy (all providers)

Codex uses the Responses API; CLIProxyAPIPlus only exposes Chat Completions. **Enable the adapter** so Codex works with any CLIProxy provider (minimax, glm, antigravity, kilo, etc.):

1. **Start proxy with adapter:** `THGENT_CLIPROXY_ADAPTER=1 thegent mcp up`
2. **Login:** `thegent cliproxy login <provider>` (minimax, glm, antigravity, etc.)
3. **Run Codex:** `OPENAI_BASE_URL=http://127.0.0.1:8317/v1 OPENAI_API_KEY=sk-dummy codex exec - "task" --model <model>`

Use catalog model IDs (e.g. `minimax-m2.5`, `glm-5`, `gemini-3-flash`). For custom provider config patterns, see [MiniMax Codex CLI guide](https://platform.minimax.io/docs/coding-plan/codex-cli).

**Agent self-service (no user intervention):**

- `thegent mgmt ensure-proxy` — Ensure MCP+proxy running (starts via process-compose if needed)
- `thegent mgmt verify-codex-cliproxy` — Full verification: ensure proxy, run `codex exec`, report pass/fail
- `task mgmt:verify-codex-cliproxy` — Same via Taskfile

**Reference:** [CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md](../research/CODEX_MINIMAX_CLIPROXY_RESEARCH_AND_PLAN.md)

---

## OpenCode Zen with CLIProxyAPIPlus

**OpenCode** (opencode.ai) is an OSS AI coding agent. **Zen** is its curated model layer. You can use **CLIProxyAPIPlus** as OpenCode's backend instead of or alongside Zen.

1. **Start proxy:** `thegent cliproxy start` (or `THGENT_CLIPROXY_ADAPTER=1 thegent mcp up` if using Codex)
2. **Login:** `thegent cliproxy login <provider>` (minimax, glm, kilo, roo, etc.)
3. **Run OpenCode with CLIProxy:**
   ```bash
   export OPENAI_BASE_URL=http://127.0.0.1:8317/v1
   export OPENAI_API_KEY=sk-dummy
   opencode
   ```

OpenCode will route requests through CLIProxy to your configured providers (minimax, glm, kilo, roo, antigravity, etc.). Use catalog model IDs (e.g. `minimax-m2.5`, `glm-5`).

**GoZen** (dopejs/GoZen): Multi-CLI switcher for Claude Code, Codex, OpenCode. Add a provider with `base_url: http://127.0.0.1:8317/v1` to use CLIProxy with `zen --cli opencode`.

**Reference:** [AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md](../research/AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md)

## OpenCode + Zen Native in thegent

You can now use OpenCode and Zen directly from thegent:

1. `thegent run opencode "summarize this repo"`
   Uses the `opencode` CLI (`opencode run ...`) as a direct harness.
2. `thegent run zen "implement X"`
   Uses Zen OpenAI-compatible API via Codex client path.

Zen env vars:

```bash
export THGENT_ZEN_API_KEY="<your-zen-key>"
export THGENT_ZEN_BASE_URL="https://api.opencode.ai"   # optional override
```

Optional aliases:

```bash
export OPENCODE_API_KEY="<your-zen-key>"   # recognized as fallback
export ZEN_API_KEY="<your-zen-key>"        # recognized as fallback
```

---

## References

- [AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md](../research/AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md)
- [CLIPROXY_API_AND_THGENT_UNIFIED_PLAN.md](../plans/CLIPROXY_API_AND_THGENT_UNIFIED_PLAN.md)
- Cursor zero-action spec: `docs/guides/CURSOR_ZERO_ACTION_FLOW_SPEC.md` (in heliosShield)

---

## Troubleshooting by symptom

### Symptom: `OAuth credentials not found` / login prompts repeat

```bash
thegent cliproxy login claude --force
thegent cliproxy login codex --force
thegent cliproxy login gemini --force
thegent doctor
```

Check token/config presence:

```bash
ls -la ~/.cli-proxy-api
thegent cliproxy ensure-config
thegent cliproxy restart
```

### Symptom: `Invalid API key` (MiniMax/NIM)

```bash
thegent cliproxy login minimax --force
thegent cliproxy login nim --force
thegent cliproxy restart
thegent list-models --provider minimax
```

### Symptom: model not found / wrong model-route provider

```bash
thegent resolve-model-route -M glm-5
thegent list-models --provider iflow
thegent list-models --provider nim
```

If route is wrong for your intent, explicitly pin provider/model in command options.

### Symptom: headless harness run times out

```bash
clode haiku --print "respond with pong"
dex flash --print "respond with pong"
roid flash exec --help
```

If still failing, check for active conflicting sessions and rerun:

```bash
thegent ps
thegent doctor
```

### Symptom: Codex cannot talk to cliproxy

```bash
THGENT_CLIPROXY_ADAPTER=1 thegent mcp up
thegent mgmt verify-codex-cliproxy
```

Manual sanity:

```bash
OPENAI_BASE_URL=http://127.0.0.1:8317/v1 OPENAI_API_KEY=sk-dummy codex exec - "Output only 1" --model gemini-3-flash
```

## Operational env vars

| Variable                               | Purpose                                                    | Default         |
| -------------------------------------- | ---------------------------------------------------------- | --------------- |
| `THGENT_DEFAULT_ROUTING`               | Route policy (`prefer_direct`, `prefer_proxy`, `failover`) | `prefer_direct` |
| `THGENT_DEBUG`                         | Enable debug tags and verbose diagnostics                  | `0`             |
| `THGENT_CLIPROXY_ADAPTER`              | Enable Responses->Chat adapter for Codex via cliproxy      | `0`             |
| `THGENT_CURSOR_TOKEN_REFRESH_INTERVAL` | Cursor token-file refresh cadence (seconds)                | `300`           |
