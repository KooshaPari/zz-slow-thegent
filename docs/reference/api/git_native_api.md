# git_native API Reference

> **Source**: `src/thegent/native/git_native.py`

BKM-06: Thin Python wrapper for thegent-git native binary.

Provides HEAD, status, and diff-stat git metadata without spawning the git
CLI. Two execution strategies (tried in order):

1. `thegent-git` binary (Rust, gitoxide/git2 backend) — zero-process-spawn.
2. `git` subprocess fallback — always available on any developer machine.

The fallback is intentionally kept as a standalone, fully functional path so
the module works even when the Rust binary has not been compiled.

FR-GIT-001 @trace FR-GIT-001

---

## GitNative

Native git metadata provider.

Tries the `thegent-git` binary first; falls back to `git` subprocess.

### Methods

#### GitNative.**init**

```python
__init__(self: Any, repo_path: Any)
```

---

#### GitNative.diff_stat

```python
diff_stat(self: Any) -> ``{"files_changed"
```

Return diff stats comparing HEAD to current worktree + index.

**Returns** (```{"files_changed"`): N, "insertions": N, "deletions": N}``

---

#### GitNative.head

```python
head(self: Any) -> ``{"sha"
```

Return HEAD commit SHA and branch name.

**Returns** (```{"sha"`): "&lt;40-char-hex&gt;", "branch": "&lt;name&gt;"}``

---

#### GitNative.status

```python
status(self: Any) -> ``{"modified"
```

Return working-tree status.

**Returns** (```{"modified"`): [...], "untracked": [...], "staged": [...]}``

---

---

## diff_stat

```python
diff_stat(self: Any) -> ``{"files_changed"
```

Return diff stats comparing HEAD to current worktree + index.

**Returns** (```{"files_changed"`): N, "insertions": N, "deletions": N}``

---

## head

```python
head(self: Any) -> ``{"sha"
```

Return HEAD commit SHA and branch name.

**Returns** (```{"sha"`): "&lt;40-char-hex&gt;", "branch": "&lt;name&gt;"}``

---

## status

```python
status(self: Any) -> ``{"modified"
```

Return working-tree status.

**Returns** (```{"modified"`): [...], "untracked": [...], "staged": [...]}``

---
