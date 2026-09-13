# Agent-D Batch Status

## WL-122

- status: in-progress
- done: wired canonical max-lines gate through task defaults, pre-commit, and CI quality lane env
- files changed:
  - `Taskfile.yml`
  - `.pre-commit-config.yaml`
  - `.github/workflows/ci.yml`
- validation commands run:
  - `task -n quality:max-lines` (pass)
  - `uv run pre-commit validate-config` (pass)
  - `MAX_LINES_SCOPE=changed sh scripts/max-lines-gate.sh` (blocked: cargo could not reach `index.crates.io`)
  - `THEGENT_MAX_LINES_IMPL=zig MAX_LINES_SCOPE=changed sh scripts/max-lines-gate.sh` (pass; `checked=3 warn=0 fail=0`)

## WL-104

- status: blocked
- done: authored implementation-ready plan artifact for JSON-RPC stdio daemon mode
- files changed:
  - `docs/plans/WL-104-EMBEDDING-PROTOCOL-IMPLEMENTATION-PLAN.md`
- validation commands run:
  - `python scripts/agent_helpers.py next --limit 30` (result: `[]`)
  - `thegent plan next --format json` (timed out in this sandbox while fetching remote model cost map)

## WL-106

- status: blocked
- done: authored implementation-ready plan artifact for fork/rollback semantics and CLI surface
- files changed:
  - `docs/plans/WL-106-SESSION-FORK-ROLLBACK-IMPLEMENTATION-PLAN.md`
- validation commands run:
  - `python scripts/agent_helpers.py next --limit 30` (result: `[]`)
  - `thegent plan next --format json` (timed out in this sandbox while fetching remote model cost map)

## WL-111

- status: blocked
- done: authored implementation-ready plan artifact for MCP skill list/activate tools
- files changed:
  - `docs/plans/WL-111-MCP-SKILL-TOOLS-IMPLEMENTATION-PLAN.md`
- validation commands run:
  - `python scripts/agent_helpers.py next --limit 30` (result: `[]`)
  - `thegent plan next --format json` (timed out in this sandbox while fetching remote model cost map)

## WL-117

- status: blocked
- done: authored implementation-ready plan artifact for VS Code extension execution phases
- files changed:
  - `docs/plans/WL-117-VSCODE-EXTENSION-IMPLEMENTATION-PLAN.md`
- validation commands run:
  - `python scripts/agent_helpers.py next --limit 30` (result: `[]`)
  - `thegent plan next --format json` (timed out in this sandbox while fetching remote model cost map)
