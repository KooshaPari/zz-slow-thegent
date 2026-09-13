# ADR-003: Rule Engine Design

## Status

Proposed

## Context

TehGent needs a customizable rule system for code review criteria. Users want to:

- Enable/disable specific checks
- Set severity levels
- Define custom rules
- Share rule configurations

## Decision

We will implement a **Declarative Rule System**:

### 1. Rule Interface

```go
type Rule interface {
    Name() string
    Description() string
    Severity() Severity
    Evaluate(ctx context.Context, input *RuleInput) ([]Finding, error)
}
```

### 2. Rule Configuration

```yaml
rules:
  - id: security/hardcoded-secrets
    enabled: true
    severity: critical

  - id: performance/inefficient-loop
    enabled: true
    severity: warning

  - id: style/max-line-length
    enabled: false
```

### 3. Rule Categories

- Security
- Performance
- Style
- Best Practices
- Documentation

### 4. Custom Rules

- Lua/Starlark scripting for custom rules
- Simple YAML-based rules
- Go plugin system (future)

## Consequences

### Positive

- Highly configurable
- Easy to add built-in rules
- Custom rules possible
- Shareable configurations

### Negative

- Complexity in rule engine
- Performance overhead for many rules
- Need good documentation

## Related Issues

- #5 Rule System
- #28-31 Rule implementations
