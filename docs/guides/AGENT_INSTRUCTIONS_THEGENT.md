# Agent Instructions: thegent Deep-Dive

This guide provides architecture-level context for agents working on the thegent codebase. Read this before making non-trivial changes.

---

## Architecture Overview

thegent is an **MCP server + agent hook system** that governs AI agent lifecycle and quality. It has three primary subsystems:

```
MCP Server (transport)
  |
  +-- Agent Runner (persona execution)
  |     +-- agents/*.md (persona definitions)
  |     +-- AgentRunner strategy pattern
  |
  +-- Hook Dispatcher (lifecycle events)
  |     +-- hooks/hook-dispatcher/ (core dispatcher)
  |     +-- hooks/pretool-dispatcher.sh
  |     +-- hooks/posttool-dispatcher.sh
  |     +-- hooks/*.sh (individual hooks)
  |     +-- hooks/lib/ (shared utilities)
  |     +-- hooks/hook-config.yaml (registration)
  |
  +-- Governance Engine (policies + contracts)
        +-- contracts/*.json (policy definitions)
        +-- hooks/qa-*.sh (quality gates)
        +-- hooks/governance-gates.sh
```

---

## MCP Server Architecture

### Transport Layer

The MCP server handles JSON-RPC communication with connected clients (Claude Code, etc.). Domain logic MUST NOT depend on MCP transport details.

**Rule:** If you are adding business logic, it goes in `src/thegent/`, hooks, or commands -- never in the MCP server entry point.

### Tool Registration

MCP tools are registered via the FastMCP pattern. To add a new tool:

1. Define the tool function in the appropriate module under `src/thegent/`
2. Register it in the MCP server using FastMCP's `@mcp.tool()` decorator
3. Include type hints and docstrings (these become the tool's schema and description)

**Anti-pattern:** Do not register tools by manually constructing JSON-RPC schemas. Use FastMCP's decorator-based registration.

---

## Agent Persona System

### Discovery and Registration

Agent personas are markdown files in `agents/`. Each file defines:

- **Name and role** (heading)
- **Capabilities** (what the agent can do)
- **Constraints** (what the agent must not do)
- **Tools** (which MCP tools the agent uses)

### Adding a New Agent

1. Create `agents/<persona-name>.md`
2. Follow the template structure from existing agents (e.g., `agents/code-reviewer.md`)
3. The agent registry automatically discovers `.md` files in `agents/`

**Anti-pattern:** Do not create agent definitions outside `agents/`. Do not create programmatic agent classes when a markdown persona definition suffices.

### Agent Runner Strategy

The `AgentRunner` uses the strategy pattern: different execution strategies for different agent types. When adding a new execution mode:

- Implement a new strategy, not a new runner
- Register the strategy in the runner's strategy map
- Do not fork the runner class

---

## Hook Dispatch Lifecycle

### Event Flow

```
Session Start
  --> spec-preflight, qa-preflight

User Prompt Submit
  --> prompt-submit-guard

Pre Tool Use (Write/Edit)
  --> doc-location-guard
  --> pre-write-validator
  --> suppression-blocker

Post Tool Use (Write/Edit)
  --> change-doc-tracker
  --> post-edit-checker
  --> async-test-runner

Stop
  --> quality-gate
  --> stop-reconcile
  --> spec-verifier
  --> complexity-ratchet
  --> security-pipeline
  --> test-maturity

Session End
  --> session-cleanup
```

### Hook Naming Convention

| Prefix    | When it fires           | Examples                                             |
| --------- | ----------------------- | ---------------------------------------------------- |
| `pre-*`   | Before tool execution   | `pre-write-validator.sh`                             |
| `post-*`  | After tool execution    | `post-edit-checker.sh`                               |
| `qa-*`    | Quality assurance gates | `qa-policy-engine.sh`, `qa-artifact-quality-gate.sh` |
| `agent-*` | Agent-specific hooks    | `agent-antipattern-detector.sh`                      |

### Adding a New Hook

1. Create `hooks/<prefix>-<name>.sh`
2. Add the hook to `hooks/hook-config.yaml` under the appropriate event
3. Implement the hook as a thin script that calls library functions from `hooks/lib/`
4. Use the hook stderr convention: `HOOK_NAME FAIL: reason` on exit non-zero

**Anti-pattern:** Do not put shared logic directly in hook scripts. Extract to `hooks/lib/` and source it.

### Hook Libraries

Shared utilities live in `hooks/lib/`. These are sourced (not executed) by hook scripts:

```bash
#!/usr/bin/env bash
# In a hook script:
source "$(dirname "$0")/lib/common.sh"
source "$(dirname "$0")/lib/linting.sh"
```

---

## Governance and Contracts

### Contract Structure

Governance contracts in `contracts/` are JSON files that define:

- **Cost caps** (token budgets, API call limits)
- **Quality thresholds** (coverage minimums, complexity limits)
- **Security policies** (allowed dependencies, secret patterns)
- **SLOs** (response time, availability)

### Policy Engine

The `qa-policy-engine.sh` evaluates contracts against current project state. To add a new governance rule:

1. Define the policy in `contracts/<policy-name>.json`
2. Wire the evaluation logic into `qa-policy-engine.sh`
3. Reference the contract in relevant hooks

**Anti-pattern:** Do not hardcode thresholds in hook scripts. All thresholds belong in `contracts/` or `hooks/hook-config.yaml`.

---

## Commands

Commands in `commands/` provide CLI-accessible operations:

- DAG compilation
- Ledger initialization
- Spec hashing and verification

### Adding a New Command

1. Create `commands/<command-name>/` directory
2. Implement the command entry point
3. Register in the command dispatch system

---

## Key Architecture Decisions

### Boundary Enforcement

thegent uses `tach.toml` for import boundary enforcement:

- The MCP transport layer cannot import domain logic directly
- Hooks cannot import from the MCP server
- Domain logic in `src/thegent/` is the shared kernel

### Configuration Hierarchy

```
hooks/hook-config.yaml     (hook registration and event mapping)
contracts/*.json           (governance policies)
qa-config.json             (quality gate thresholds)
pyproject.toml             (Python tooling config)
tach.toml                  (architecture boundaries)
```

### When to Add What

| I need to...                            | Create a...      | Register in...                      |
| --------------------------------------- | ---------------- | ----------------------------------- |
| Govern agent behavior                   | Contract JSON    | `contracts/`, `qa-policy-engine.sh` |
| Check code quality at a lifecycle event | Hook script      | `hooks/hook-config.yaml`            |
| Expose functionality to MCP clients     | MCP tool         | FastMCP `@mcp.tool()`               |
| Add a new agent type                    | Persona markdown | `agents/<name>.md`                  |
| Add a CLI operation                     | Command module   | `commands/<name>/`                  |
| Share logic between hooks               | Library function | `hooks/lib/<name>.sh`               |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

## Error Handling and Actionability

thegent prioritizes actionable error messages. When reporting errors:

1. **Use `print_error`**: instead of direct `console.print(f"[red]...")`.
2. **Provide Hints**: Always include a `remediation_hint` if possible.
3. **Structured Errors**: Use classes from `thegent.errors` (e.g., `ConfigError`, `ProviderError`).

```python
from thegent.errors import print_error, get_install_hint

# Good
print_error("Tool 'process-compose' not found.", hint=get_install_hint("process-compose"))

# Also Good
raise ConfigError("Missing API key", remediation_hint="Run 'thegent cliproxy login'")
```

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
