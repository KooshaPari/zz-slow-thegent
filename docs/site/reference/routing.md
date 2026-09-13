# Routing Reference

Routing decides which provider/model executes a task.

## Routing Inputs

- Requested provider (for example `--provider codex`)
- Requested model (for example `-M gpt-5.3-codex`)
- Routing policy (`-R cheapest` or default behavior)
- Provider availability and credentials

## Common Routing Modes

| Mode              | Behavior                    | Best for                            |
| ----------------- | --------------------------- | ----------------------------------- |
| explicit provider | direct provider selection   | deterministic execution             |
| explicit model    | specific model override     | benchmark or quality-sensitive jobs |
| `-R cheapest`     | lowest-cost available route | bulk/background work                |

## Examples

```bash
# Explicit provider
thegent run "draft release notes" --provider claude

# Explicit model
thegent run "analyze perf regressions" -M gpt-5.3-codex

# Cost-aware route
thegent run "summarize logs" -R cheapest
```

## Troubleshooting Routing

- If routing picks an unexpected provider, specify `--provider` directly.
- If a model is unavailable, verify provider capability and credentials.
- Use `--debug` to inspect route decisions.
