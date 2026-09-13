---
title: Two-Surface Architecture Proposal
date: 2026-02-21
status: accepted
owner: B90-W3-agent-a
tags: [wl-136, architecture, cli, decomposition]
---

# Two-Surface Architecture Proposal

## Summary

thegent's Python codebase is split into two distinct surfaces: **core** and **tooling**.
This separation was initiated in Wave-1 (WL-120) and formalized in Wave-2 (WL-136,
B90-W2-D2). The two-surface split enforces a strict import boundary and allows the
tooling surface to be omitted from production deployments.

## The Core Surface

The **core** surface contains the production runtime path of thegent:

- **Orchestration**: `src/thegent/agents/`, `src/thegent/orchestration/`
- **MCP server**: `src/thegent/mcp/`
- **Routing**: `src/thegent/routing/`
- **Governance runtime**: `src/thegent/governance/` (SLO emitters, policy engine)
- **Infrastructure**: `src/thegent/infra/`
- **Configuration**: `src/thegent/config.py`, `src/thegent/config/`
- **Session management**: `src/thegent/session/`
- **Core CLI dispatch**: `src/thegent/cli/commands/impl.py`, `src/thegent/cli/commands/run_cmds.py`

Core modules are performance-critical and must start quickly. They must not import
tooling modules. Core is the surface deployed to production and embedded in agent
runtimes.

## The Tooling Surface

The **tooling** surface contains development utilities, research helpers, benchmarks,
audit commands, and QA workflows:

- **DAG CLI commands**: `src/thegent/cli/commands/cli_dag.py` — dag\_\* orchestration
  commands for managing DAG sessions. These are developer and orchestration tooling.
- **Tooling CLI commands**: `src/thegent/cli/commands/cli_tooling.py` — audit_verify,
  benchmark, deep_research, drift_monitor, roadmap commands.
- **Execution boundary shim**: `src/thegent/cli/commands/impl_execution.py` — thin
  shim re-exporting core execution functions; lives in the CLI surface.
- **Benchmarking**: `benchmarks/`
- **Scripts**: `scripts/` — collection, analysis, rendering

Tooling modules may import core modules. Core modules MUST NOT import tooling modules.

## Motivation

1. **Startup performance**: Core CLI (`thegent run`, `thegent bg`) must start in under
   250ms. Importing heavy tooling at startup violates the CLI SLO.
2. **Deployment footprint**: Production containers do not need research/benchmarking
   code; the two-surface split enables slimmer images.
3. **Separation of responsibilities**: Tooling evolves at a different cadence than core.
   Decoupling prevents tooling churn from breaking core contracts.
4. **Test isolation**: Core unit tests run without tooling deps; tooling tests may
   require heavier fixtures.

## Decision

Split all CLI commands into core (production path) and tooling (developer/QA path),
with a machine-enforced import boundary. Violations are detected by
`scripts/check_thegent_core_boundary.py` and blocked in CI.

## Alternatives Considered

- **Single surface**: Rejected. Monolithic CLI.py (6,994 LOC) is unmaintainable and
  violates startup SLOs.
- **Plugin architecture**: Considered for Wave-5+. The current split is a prerequisite.
- **Separate packages**: Deferred. Two-surface within the same package is sufficient for
  now and avoids packaging complexity.
