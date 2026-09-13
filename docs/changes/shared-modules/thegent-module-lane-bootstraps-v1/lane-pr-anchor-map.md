# PR Anchor Map for Lane Split Bootstrap (P6.32)

## Purpose

Track the five PR anchors expected from dedicated lane worktrees before PR mechanics begin.

## Current state (2026-03-03)

- **thegent-app**: `lane/split-thegent-app-bootstrap` _(TBD: PR number)_
- **thegent-mcp**: `lane/split-thegent-mcp-bootstrap` _(TBD: PR number)_
- **thegent-control-plane**: `lane/split-thegent-control-plane-bootstrap` _(TBD: PR number)_
- **thegent-execution**: `lane/split-thegent-execution-bootstrap` _(TBD: PR number)_
- **thegent-governance**: `lane/split-thegent-governance-bootstrap` _(TBD: PR number)_

## Planned merge sequence

1. `thegent-app`
2. `thegent-mcp`
3. `thegent-control-plane`
4. `thegent-execution`
5. `thegent-governance`

## Verification owner

- Merge-order verifier: **thegent-platform**
- Lane owners: `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/handoff-report.md`

## Required evidence before opening each PR

- lane smoke command output for module
- `phench projects run` filtered smoke evidence from module branch
- scope-safeness pass from file ownership audit
