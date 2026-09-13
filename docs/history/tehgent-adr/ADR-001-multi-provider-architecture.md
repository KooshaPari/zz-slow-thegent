# ADR-001: Multi-Provider Architecture

## Status

Proposed

## Context

TehGent needs to support multiple AI providers (OpenAI, Claude, Gemini, etc.) for code review capabilities. Each provider has:

- Different API formats
- Different authentication methods
- Different rate limits
- Different pricing models

Users may want to:

- Use their preferred provider
- Switch providers based on cost
- Use different providers for different review types

## Decision

We will implement a **Provider Interface Pattern**:

### 1. Provider Interface

```go
type Provider interface {
    Name() string
    Review(ctx context.Context, req *ReviewRequest) (*ReviewResponse, error)
    IsAvailable() bool
    EstimateCost(req *ReviewRequest) (tokens int, err error)
}
```

### 2. Provider Registry

- Central registry for provider discovery
- Dynamic provider loading
- Configuration-based provider enablement

### 3. Request/Response Translation

- Unified internal types
- Per-provider translators
- Streaming support

## Consequences

### Positive

- Easy to add new providers
- Users can choose preferred provider
- Cost optimization possible
- Testable through mocks

### Negative

- Additional abstraction layer
- Provider-specific features may be harder to expose
- Maintenance of multiple integrations

## Related Issues

- #3 AI Provider Integration
- #20 Design Provider Interface
- #21-23 Provider implementations
