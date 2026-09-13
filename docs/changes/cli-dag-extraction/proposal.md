---
title: CLI DAG Extraction — Proposal
date: 2026-02-21
status: implemented
owner: agent-f (B90-W2-F1)
tags: [wl-120, b90, monolith-split, cli]
---

# Proposal: Extract DAG Command Handlers from cli.py

## Problem Statement

`src/thegent/cli/commands/cli.py` had grown to 6,927 lines (pre-wave-2), far exceeding
the 500-line target for a single module. The DAG command group (`dag_validate_cmd`,
`dag_add_cmd`, `dag_update_cmd`, `dag_list_cmd`, `dag_run_cmd`, `dag_ready_cmd`,
`dag_sync_cmd`, `dag_recover_cmd`, and related helpers) represented a discrete,
testable responsibility that could be cleanly extracted without breaking the public
CLI surface.

## Why This Extraction

1. **Single-responsibility**: DAG lifecycle (add/validate/run/sync/recover) is a
   coherent domain unit. Combining it with session, model, plan, and infra commands
   in a single 6k-line file violates SRP and makes grep/navigation impractical.

2. **LOC reduction**: Extraction reduces the cli.py monolith by ~620 lines
   (the size of `cli_dag.py`), moving it from 6,927 to ~6,307 lines — a step
   toward the 500-line ceiling mandated by WL-120 / WL-124.

3. **Independent testability**: `cli_dag.py` can be unit-tested in isolation with
   stubbed helpers from `cli.py`, without importing the full 6k-line monolith.

4. **Parallel extraction enabled**: Once DAG handlers are isolated, other command
   groups (session, infra, plan, model, team, run) can be extracted in parallel by
   separate agents without merge conflicts.

## Decision

Extract DAG CLI command handlers to `src/thegent/cli/commands/cli_dag.py`.
Keep all helper functions and business logic in `cli.py` (or `impl.py`/`dag_impl.py`).
The new module imports the helpers it needs from `cli.py` and delegates to them.

`cli.py` does **not** re-export `cli_dag.py` — the DAG sub-app wires its own
commands by importing `cli_dag.py` directly. This is forward-compatible with
full monolith removal when all groups are extracted.

## Acceptance Criteria

- `cli_dag.py` exists and contains all `dag_*_cmd` handlers.
- `cli.py` still exports existing public symbols for backwards compatibility.
- `python -c "from thegent.cli.commands.cli_dag import dag_validate_cmd"` exits 0.
- Existing DAG-related tests pass without modification.
