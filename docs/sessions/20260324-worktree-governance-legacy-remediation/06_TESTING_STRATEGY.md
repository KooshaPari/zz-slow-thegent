# 06_TESTING_STRATEGY

## Focused coverage

- CLI forwarding tests for worktree governance commands
- Script behavior tests for migration and inventory
- MCP tooling smoke tests for `thegent_worktree` actions

## Validation commands

- `python -m pytest -p no:tach tests/commands/test_worktree_governance_script.py -q`
- `python -m pytest -p no:tach tests/commands/test_cli_git_worktree_governance.py -q`
- `python -m pytest -p no:tach tests/mcp/test_worktree_governance_tool.py -q`
