# Configuration Reference

This page documents common configuration patterns for `thegent`.

## Environment Variables

| Variable                 | Purpose                                     |
| ------------------------ | ------------------------------------------- |
| `ANTHROPIC_API_KEY`      | Claude provider authentication              |
| `OPENAI_API_KEY`         | OpenAI/Codex provider authentication        |
| `GOOGLE_API_KEY`         | Gemini provider authentication              |
| `THGENT_DEFAULT_ROUTING` | Default routing preference                  |
| `THGENT_DEBUG`           | Enable debug output for runtime diagnostics |

## Set Values with CLI

```bash
thegent config set providers.myproxy.url "http://localhost:8317"
thegent config set providers.myproxy.model "claude-sonnet-4-6"
```

## Recommended Defaults

- Keep credentials in environment or secure runtime config.
- Use explicit provider/model in CI for deterministic behavior.
- Set routing policy intentionally (`prefer_direct`, `prefer_proxy`, or explicit per command).

## Validation

After config changes:

```bash
thegent doctor
thegent run "configuration smoke test" --provider codex
```
