# ADR-004: Output Format Strategy

## Status

Proposed

## Context

TehGent needs to output review results in multiple formats for different use cases:

- Human-readable terminal output
- JSON for programmatic consumption
- SARIF for security tools
- Markdown for PR comments
- GitHub Actions annotations

## Decision

We will implement **Multiple Output Formatters**:

### 1. Output Interface

```go
type Formatter interface {
    Format(review *Review) ([]byte, error)
    Extension() string
}
```

### 2. Supported Formats

| Format   | Use Case        | Priority |
| -------- | --------------- | -------- |
| text     | Terminal        | High     |
| json     | API/integration | High     |
| markdown | PR comments     | High     |
| sarif    | Security tools  | Medium   |
| github   | GitHub Actions  | High     |

### 3. Output Selection

```bash
tehgent review --format json
tehgent review --format markdown --output review.md
tehgent review --format sarif > results.sarif
```

## Consequences

### Positive

- Flexible output options
- Easy integration with tools
- Standard formats supported

### Negative

- Maintenance of multiple formatters
- Format-specific features may vary

## Related Issues

- #27 Output Formatters
