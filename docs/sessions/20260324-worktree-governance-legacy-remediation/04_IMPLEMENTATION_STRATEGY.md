# 04_IMPLEMENTATION_STRATEGY

## Strategy

- Keep governance commands centralized in `scripts/worktree_governance.sh` with CLI/MCP forwarding.
- Require remediation report before migration to keep decisions explicit and auditable.
- Block migrations on dirty or detached worktrees to avoid implicit state loss.

## Interfaces

- Script: `worktree_governance.sh migrate-legacy ...`
- CLI: `thegent worktree migrate-legacy ...`
- MCP: `thegent_worktree` tool with `action="migrate-legacy"`
