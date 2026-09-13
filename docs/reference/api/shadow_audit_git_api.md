# shadow_audit_git API Reference

> **Source**: `src/thegent/audit/shadow_audit_git.py`

Shadow audit Git log with secret scrubbing.

Tracks all git operations as immutable audit entries in SQLite, with
automatic secret scrubbing via the native secret scanner before storage.

WBS: wp-71002-shadow-git
FR Traceability: FR-VER-003 (shadow audit log with secret scrubbing)

---

## AuditEntry

An immutable audit log entry for a git commit.

**Inherits from**: `BaseModel`

### Methods

#### AuditEntry.to_dict

```python
to_dict(self: Any)
```

Serialize to a JSON-safe dict.

---

---

## ShadowAuditGit

Tracks git operations as immutable audit entries with secret scrubbing.

All commit messages and diffs are scrubbed for secrets before storage.
Uses the same SQLite database as ProjectRegistry (shared DB path).

### Methods

#### ShadowAuditGit.**init**

```python
__init__(self: Any, db_path: Any)
```

---

#### ShadowAuditGit.export_audit

```python
export_audit(self: Any, project_id: str, path: Any)
```

Export the audit log for a project to a JSON file.

---

#### ShadowAuditGit.get_audit_log

```python
get_audit_log(self: Any, project_id: str, limit: Any)
```

Return audit entries for a project, ordered by creation time.

**Parameters**:

- `project_id`: The project whose audit log to retrieve.
- `limit`: Maximum number of entries to return. None means all.

---

#### ShadowAuditGit.record_commit

```python
record_commit(self: Any, project_id: str, sha: str, message: str, diff: str)
```

Record a git commit as an immutable audit entry.

Both the message and diff are scrubbed for secrets before storage.

---

---

## export_audit

```python
export_audit(self: Any, project_id: str, path: Any)
```

Export the audit log for a project to a JSON file.

---

## get_audit_log

```python
get_audit_log(self: Any, project_id: str, limit: Any)
```

Return audit entries for a project, ordered by creation time.

**Parameters**:

- `project_id`: The project whose audit log to retrieve.
- `limit`: Maximum number of entries to return. None means all.

---

## record_commit

```python
record_commit(self: Any, project_id: str, sha: str, message: str, diff: str)
```

Record a git commit as an immutable audit entry.

Both the message and diff are scrubbed for secrets before storage.

---

## to_dict

```python
to_dict(self: Any)
```

Serialize to a JSON-safe dict.

---
