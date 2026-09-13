# Hexagonal Architecture Migration -- thegent

## Status: Brownfield -- Incremental Migration

thegent has substantial existing code in `src/thegent/`. This document proposes an incremental migration to hexagonal architecture that preserves backward compatibility and avoids a big-bang rewrite.

## What

Migrate thegent's existing flat module structure into hexagonal (ports-and-adapters) layers while keeping the codebase functional at every step.

## Why

- Current code mixes CLI concerns, MCP protocol handling, domain logic, and infrastructure in the same modules (e.g., `cli.py` at 174KB, `mcp_server.py` at 65KB)
- Business logic (agent governance, contracts, policies) is tightly coupled to transport (CLI, MCP)
- Testing requires mocking infrastructure that should be behind ports
- thegent already uses tach for boundary enforcement; this migration formalizes layers for import-linter

## Current Structure Analysis

```
src/thegent/
  agents/          # Agent runners, registry, state machine -- DOMAIN + ADAPTER mix
  contracts/       # Contract validation, conformance, policies -- mostly DOMAIN
  governance/      # Cost caps, input guardrails -- DOMAIN
  models/          # Data models, catalog -- DOMAIN
  planning/        # Simulation -- DOMAIN/APPLICATION
  cli.py           # CLI commands -- DRIVING ADAPTER (174KB, needs decomposition)
  cli_impl.py      # CLI implementation detail -- DRIVING ADAPTER (140KB)
  config.py        # Config/settings -- INFRASTRUCTURE
  execution.py     # Execution engine -- APPLICATION
  exit_codes.py    # Exit code constants -- DOMAIN
  install.py       # Installation logic -- INFRASTRUCTURE
  main.py          # Entry point -- DRIVING ADAPTER
  mcp_manage.py    # MCP management -- DRIVING ADAPTER
  mcp_server.py    # MCP server -- DRIVING ADAPTER
  operations.py    # Operations -- APPLICATION
  orchestration_modes.py # Mode definitions -- DOMAIN
  output_parser.py # Output parsing -- APPLICATION
```

## Target Structure

```
src/thegent/
  domain/                        # Pure business logic
    __init__.py
    agents/                      # Agent definitions, state machine, registry (pure logic)
    contracts/                   # Contract validation, conformance, policies
    governance/                  # Cost caps, guardrails (rules only, no I/O)
    models/                      # Domain entities, value objects
    planning/                    # Simulation logic
    exit_codes.py
    orchestration_modes.py
  application/                   # Use cases, orchestration
    __init__.py
    execution.py                 # Execution engine (orchestrates domain)
    operations.py                # Operation handlers
    output_parser.py             # Parse and transform output
  adapters/
    driving/                     # Input adapters
      __init__.py
      cli.py                     # Typer CLI commands
      cli_impl.py                # CLI implementation helpers
      main.py                    # Entry point
      mcp_server.py              # MCP server (FastMCP)
      mcp_manage.py              # MCP management commands
    driven/                      # Output adapters
      __init__.py
      # Future: file system, HTTP clients, etc.
  infrastructure/                # Cross-cutting concerns
    __init__.py
    config.py                    # Settings, env vars
    install.py                   # Installation and setup
```

## Migration Strategy: Strangler Fig

Phase 1 -- Establish layers (scaffold empty packages, add **init**.py):

- Create domain/, application/, adapters/driving/, adapters/driven/, infrastructure/
- Add import-linter config immediately (initially in audit mode)

Phase 2 -- Move pure domain code:

- Move contracts/, governance/, models/, planning/ into domain/
- Move exit_codes.py, orchestration_modes.py into domain/
- Extract pure logic from agents/ into domain/agents/

Phase 3 -- Move application layer:

- Move execution.py, operations.py, output_parser.py into application/
- Ensure they only import from domain/

Phase 4 -- Move adapters:

- Move cli.py, cli_impl.py, main.py into adapters/driving/
- Move mcp_server.py, mcp_manage.py into adapters/driving/

Phase 5 -- Move infrastructure:

- Move config.py, install.py into infrastructure/
- Wire dependency injection

Phase 6 -- Enforce:

- Switch import-linter from audit to enforcement mode
- Update pyproject.toml entry points
- Update test imports

## Risks and Mitigations

| Risk                                               | Mitigation                                                                       |
| -------------------------------------------------- | -------------------------------------------------------------------------------- |
| Large files (cli.py 174KB) hard to move atomically | Move entire file first, decompose later                                          |
| Test imports break                                 | Update test imports in same PR as source move                                    |
| Entry point changes                                | Update pyproject.toml `[project.scripts]` after moving main.py                   |
| tach.toml conflicts with import-linter             | Both tools can coexist; tach checks module deps, import-linter checks layer deps |

---

## See also

- [WORK_STREAM.md](../../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../../plans/00-MASTER-INDEX.md) — plan index
