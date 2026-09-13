# Code Ownership & Cross-Project Architecture

**Date:** February 23, 2026

---

## Current State

### thegent (this repo)

- **Focus:** Agent orchestration, CLI, agent runtime
- **LOC:** 426,991 total (258K Python, 168K Rust)
- **Strengths:** Agent system, CLI, hooks, integrations

### CLIProxyAPI (sibling project)

- **Focus:** LLM proxy, routing, provider management
- **Location:** `/Users/kooshapari/temp-PRODVERCEL/485/API/`

---

## Ownership Boundary Issues

### Code in thegent that belongs in CLIProxyAPI

| Module                            | LOC | Reason                                       |
| --------------------------------- | --- | -------------------------------------------- |
| Provider routing logic            | ~3K | Provider/Model selection is CLIProxy concern |
| API client wrappers               | ~2K | HTTP client code belongs with API layer      |
| Rate limiting (provider-specific) | ~1K | Provider policy is CLIProxy                  |

### Code in CLIProxyAPI that belongs in thegent

| Module         | Should Move | Reason                     |
| -------------- | ----------- | -------------------------- |
| Agent hooks    | → thegent   | Agent lifecycle is thegent |
| CLI for agents | → thegent   | CLI is thegent's domain    |

---

## Recommended Split

### thegent Responsibilities

- ✅ Agent lifecycle management
- ✅ CLI commands and UX
- ✅ Hook system
- ✅ Integration adapters
- ✅ Agent definitions and skills
- ✅ Session management

### CLIProxyAPI Responsibilities

- ✅ LLM proxy and routing
- ✅ Provider management
- ✅ Rate limiting policies
- ✅ Cost tracking per provider
- ✅ Model fallbacks

---

## Plugin Architecture Proposal

```
thegent/
├── core/           # Agent runtime, session, execution
├── cli/            # CLI commands
├── hooks/          # Hook system
├── integrations/   # Third-party integrations
└── agents/         # Agent definitions

plugins/            # Optional extensions
├── workstream/     # Workstream autosync
├── install/        # Install strategies
├── scaffold/       # Project scaffolding
└── [more...]

CLIProxyAPI/       # Separate repo
├── proxy/         # HTTP proxy logic
├── routing/       # Provider routing
├── providers/     # Provider clients
└── policies/      # Rate/cost policies
```

---

## Action Items

1. **Boundary clarity:** Document exact ownership between thegent and CLIProxy
2. **Move code:** Migrate provider-specific code to CLIProxy
3. **Extract plugins:** Make workstream/sync optional plugins
4. **Shared lib:** Create common lib for shared types
