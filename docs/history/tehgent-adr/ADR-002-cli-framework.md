# ADR-002: CLI Framework Selection

## Status

Proposed

## Context

TehGent needs a CLI framework that supports:

- Multiple subcommands (review, config, version)
- Flag parsing (global and command-specific)
- Configuration file integration
- Shell completion
- Help generation

Popular Go CLI frameworks:

- Cobra (most popular)
- urfave/cli
- Kong

## Decision

We will use **Cobra** for the CLI framework.

### Rationale

1. Most widely used in Go ecosystem
2. Excellent documentation
3. Built-in shell completion
4. Integrated with Viper for config
5. Large community support

### Structure

```
cmd/
  tehgent/
    main.go
    root.go
    review.go
    config.go
    version.go
```

## Consequences

### Positive

- Familiar to Go developers
- Good documentation
- Shell completion for bash/zsh/fish
- Easy to add commands

### Negative

- Verbose command definitions
- Large dependency tree

## Related Issues

- #2 Core CLI & Commands
- #16 Implement CLI Framework with Cobra
