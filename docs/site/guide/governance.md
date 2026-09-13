# Governance

`thegent` includes built-in controls so autonomous runs remain auditable and bounded.

## Governance Surfaces

- Cost controls: provider/model routing and spend-sensitive policies.
- Quality gates: lint, tests, and policy checks on lifecycle events.
- Security checks: secret scanning and static analysis in validation pipelines.
- Operational safety: explicit session lifecycle and auditable history.

## Baseline Policy Workflow

```bash
# 1) Verify runtime health
thegent doctor

# 2) Execute work
thegent run agent "implement feature and tests" --agent codex

# 3) Validate and review state
thegent ps
thegent plan next
```

## Recommended Team Defaults

| Area       | Recommendation                                       |
| ---------- | ---------------------------------------------------- |
| Routing    | Use explicit provider/model for critical jobs        |
| Budgets    | Enforce environment-level spend caps                 |
| Validation | Run quality checks on each merge candidate           |
| Recovery   | Prefer continuation/takeover over restarting context |

## Common Pitfalls

- Running long loops without policy or budget constraints.
- Mixing unrelated workstreams in a single session.
- Bypassing hook-based validation.

See [Operations Runbooks](/operations/runbooks) for remediation steps.
