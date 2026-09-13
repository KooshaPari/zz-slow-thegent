# audit_log API Reference

> **Source**: `src/thegent/orchestration/state/audit_log.py`

ShadowAuditGit: git-backed audit log for agent episodes (wp-71002).

Maintains a separate git repository at `~/.thegent/audit/` that records
file snapshots (with secrets scrubbed) for every episode transaction.

# @trace FR-VCS-001

---

## ShadowAuditGit

Git-backed shadow audit repository.

### Methods

#### ShadowAuditGit.**init**

```python
__init__(self: Any, audit_path: Path)
```

---

#### ShadowAuditGit.commit_transaction

```python
commit_transaction(self: Any, episode_id: str, changed_files: list[Path], message: str)
```

Stage file snapshots (scrubbed) and commit to the audit repo.

**Parameters**:

- `episode_id`: Episode identifier to include in commit message.
- `changed_files`: List of file paths to snapshot into the audit repo.
- `message`: Commit message (episode_id will be prepended).

---

#### ShadowAuditGit.get_diff

```python
get_diff(self: Any, commit_hash: str)
```

Return the diff for a specific commit.

**Parameters**:

- `commit_hash`: The git commit hash to diff.

**Returns**: The diff output as a string.

---

#### ShadowAuditGit.get_log

```python
get_log(self: Any, limit: int, episode_id: Any)
```

Query the audit git log.

**Parameters**:

- `limit`: Maximum number of entries to return.
- `episode_id`: If provided, filter to commits containing this ID.

**Returns**: List of dicts with keys: hash, message, date.

---

#### ShadowAuditGit.init_shadow_repo

```python
init_shadow_repo(self: Any)
```

Initialize the shadow audit git repository.

Idempotent: if the repo already exists, this is a no-op.

---

#### ShadowAuditGit.path

```python
path(self: Any)
```

---

---

## commit_transaction

```python
commit_transaction(self: Any, episode_id: str, changed_files: list[Path], message: str)
```

Stage file snapshots (scrubbed) and commit to the audit repo.

**Parameters**:

- `episode_id`: Episode identifier to include in commit message.
- `changed_files`: List of file paths to snapshot into the audit repo.
- `message`: Commit message (episode_id will be prepended).

**Raises**:

- `FileNotFoundError`: If any file in changed_files does not exist.

---

## get_diff

```python
get_diff(self: Any, commit_hash: str)
```

Return the diff for a specific commit.

**Parameters**:

- `commit_hash`: The git commit hash to diff.

**Returns**: The diff output as a string.

---

## get_log

```python
get_log(self: Any, limit: int, episode_id: Any)
```

Query the audit git log.

**Parameters**:

- `limit`: Maximum number of entries to return.
- `episode_id`: If provided, filter to commits containing this ID.

**Returns**: List of dicts with keys: hash, message, date.

---

## init_shadow_repo

```python
init_shadow_repo(self: Any)
```

Initialize the shadow audit git repository.

Idempotent: if the repo already exists, this is a no-op.

---

## path

```python
path(self: Any) -> Path
```

---
