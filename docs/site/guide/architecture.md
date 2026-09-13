# Architecture

`thegent` is an orchestration runtime with three primary layers: execution, governance, and interface.

## Layer Overview

| Layer      | Responsibility                             | Typical artifacts                        |
| ---------- | ------------------------------------------ | ---------------------------------------- |
| Execution  | Run agent personas and workflows           | `thegent run`, loop commands             |
| Governance | Apply policy, quality, and budget controls | contracts, QA hooks, policy engine       |
| Interface  | Expose CLI + MCP tools                     | CLI commands, MCP server resources/tools |

## Runtime Flow

1. A command starts an agent session.
2. Hook dispatchers run pre/post checks.
3. Policy checks enforce constraints (cost, quality, safety).
4. Outputs and status are persisted for later continuation.

## Practical Design Patterns

- Keep hooks thin; move shared logic into reusable libraries.
- Keep policies data-driven in contracts, not hardcoded in command handlers.
- Prefer explicit failures over hidden fallback behavior.

## Where To Extend

- Add new persona: `agents/<name>.md`
- Add new hook: `hooks/<event>-<name>.sh`
- Add new governance policy: `contracts/<policy>.json`
- Add new CLI command: `commands/<command>/`

Use [Reference Configuration](/reference/configuration) before changing environment defaults.
