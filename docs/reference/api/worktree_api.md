# worktree API Reference

> **Source**: `src/thegent/infra/worktree.py`

Phase 15: Worktree Support implementation.

Includes worktree creation, branch coordination, and cleanup.

---

## BranchCoordinator

Coordinates branch naming and collision avoidance.

### Methods

#### BranchCoordinator.get_safe_branch_name

```python
get_safe_branch_name(base: str)
```

---

---

## WorktreeManager

Manages git worktrees for isolated agent environments.

### Methods

#### WorktreeManager.**init**

```python
__init__(self: Any, project_root: Path, mesh_dir: Path)
```

---

#### WorktreeManager.cleanup_worktree

```python
cleanup_worktree(self: Any, agent_id: str)
```

Remove worktree and prune record.

---

#### WorktreeManager.create_worktree

```python
create_worktree(self: Any, agent_id: str, branch_name: Any)
```

Create a new worktree for an agent.

---

#### WorktreeManager.list_active_worktrees

```python
list_active_worktrees(self: Any)
```

List current git worktrees.

---

---

## cleanup_worktree

```python
cleanup_worktree(self: Any, agent_id: str)
```

Remove worktree and prune record.

---

## create_worktree

```python
create_worktree(self: Any, agent_id: str, branch_name: Any)
```

Create a new worktree for an agent.

---

## get_safe_branch_name

```python
get_safe_branch_name(base: str) -> str
```

---

## list_active_worktrees

```python
list_active_worktrees(self: Any)
```

List current git worktrees.

---
