# 05_KNOWN_ISSUES

- The local forest is fragmented into many legacy roots; canonicalization is incomplete across several families.
- `cliproxy-wtress` is a typo-level duplicate of `cliproxy-wtrees` and should be treated as a separate cleanup risk.
- `portage` contains prunable worktrees whose gitdir paths are already broken.
- `trace-wtrees` has a locked initializing lane.
- `trash-cli` has a detached lane under `PROJECT-wtrees`.
- `thegent` still has a detached dirty legacy lane in `.worktrees` history, even though the specific merge conflict was resolved.
