# Providers

`thegent` can route work across direct APIs and proxy-backed providers.

## Supported Provider Labels

| Provider                   | Typical default    | Notes                     |
| -------------------------- | ------------------ | ------------------------- |
| `free`                     | `gpt-5-mini`       | default convenience route |
| `claude`                   | `claude-haiku-4.5` | Anthropic API             |
| `codex`                    | `gpt-5.3-codex`    | OpenAI/Codex API          |
| `gemini`                   | `gemini-3-flash`   | Google API                |
| `cursor` / `kiro` / custom | varies             | proxy-dependent           |

## Credential Setup

```bash
thegent setup
```

For provider-specific credentials, use the provider login helper where available:

```bash
thegent cliproxy login claude
thegent cliproxy login codex
thegent cliproxy login gemini

# Or set environment credentials directly when using custom backends:
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
```

## Practical Routing Patterns

```bash
# Explicit provider
thegent run agent "generate migration checklist" --agent claude --provider claude

# Explicit model
thegent run agent "deep code audit" --model gpt-5.3-codex

# Cost-aware automatic routing
thegent run agent "summarize logs" --routing cheapest
```

## Proxy Provider Example

```bash
thegent config set providers.myproxy.url "http://localhost:8317"
thegent config set providers.myproxy.model "claude-sonnet-4-6"
thegent run agent "health check" --provider myproxy
```

## Failure Handling

- Re-run failing commands with `--debug`.
- Confirm credentials are loaded in the active shell.
- Use [Routing Reference](/reference/routing) for route decision behavior.
