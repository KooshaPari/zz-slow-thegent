# Architecture

## Overview

- thegent is a Python dotfiles manager with a Typer CLI and Rich-rendered terminal UI.
- Stack: Python, Typer, Rich, with a BlackBoxProxy-style agent discovery layer.
- This document is a skeleton; expand with module-level ownership and boundaries as the system grows.

## Components

## src/thegent/

- Core Python package: CLI entrypoint, dotfile orchestration, agent discovery & registration.

## cli/commands/

- Typer subcommand implementations (governance, worktrees, hooks, etc.). Each module groups a command family.

## thegent/dotfiles/

- Managed dotfile content and the apply/rollback primitives that drive them.

## cli/commands/governance\*.py

- Governance contract commands: attestation, diff, report, sync. Backbone of the policy plane.

## tests/

- Unit tests (Ruff-enforced) plus governance and journey-traceability end-to-end suites.

## Data flow

```text
user (CLI / TUI) -> cli/commands/* -> src/thegent/ core -> dotfile apply / agent registry
                                                          -> external services (when configured)
```

## Key invariants

- Function length ≤ 40 lines; cognitive complexity ≤ 15 (see `AGENTS.md`).
- No placeholder TODOs in committed code; no stub implementations left behind.
- All new code MUST pass `ruff check .`, `ruff format .`, `pytest -q`.
- Governance contracts are first-class artifacts; never bypass the policy CLI in scripts.

## Cross-cutting concerns (config, telemetry, errors)

- Config: load via shared phenotype utilities (`phenotype-py-utils.load_config`).
- Telemetry: emit structured events through the post-agent-run hook (`tests/unit/governance/test_post_agent_run_hook.py`).
- Errors: surface as actionable CLI messages; do not swallow exceptions silently.

## Future considerations

- Replace the skeleton with module-level ADRs (mirroring `docs/governance/ARCHITECTURAL_GOVERNANCE.md`).
- Capture the journey-traceability contract between CLI runs and the audit ledger.
- Add sequence diagrams for `govern` and `vet` flows once the policy plane stabilizes.
