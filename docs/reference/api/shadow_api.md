# shadow API Reference

> **Source**: `src/thegent/orchestration/shadow.py`

## ShadowWorkspace

MTSP-12: Shadow Workspace for isolated planning and testing.

Uses git worktree for a true isolated branch/workspace, or symlink-shadow as fallback.

### Methods

#### ShadowWorkspace.**init**

```python
__init__(self: Any, project_root: Path, shadow_id: str)
```

---

#### ShadowWorkspace.create

```python
create(self: Any, branch: Any)
```

Create a shadow workspace using git worktree.

---

#### ShadowWorkspace.destroy

```python
destroy(self: Any)
```

Destroy the shadow workspace and clean up git references.

---

#### ShadowWorkspace.get_env

```python
get_env(self: Any)
```

Return environment variables for isolating tools within the shadow workspace.

---

#### ShadowWorkspace.merge_back

```python
merge_back(self: Any)
```

Merge changes from the shadow workspace back to the main project.

---

#### ShadowWorkspace.run

```python
run(self: Any, cmd: list[str])
```

Run a command within the shadow workspace.

---

---

## create

```python
create(self: Any, branch: Any)
```

Create a shadow workspace using git worktree.

---

## destroy

```python
destroy(self: Any)
```

Destroy the shadow workspace and clean up git references.

---

## get_env

```python
get_env(self: Any)
```

Return environment variables for isolating tools within the shadow workspace.

---

## merge_back

```python
merge_back(self: Any)
```

Merge changes from the shadow workspace back to the main project.

---

## run

```python
run(self: Any, cmd: list[str])
```

Run a command within the shadow workspace.

---
