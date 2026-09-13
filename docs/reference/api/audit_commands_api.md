# audit_commands API Reference

> **Source**: `src/thegent/commands/audit_commands.py`

CLI commands for the shadow audit log.

Provides `thegent audit log`, `thegent audit diff`, and `thegent audit list` subcommands
for inspecting the immutable audit trail of agent git operations.

WBS: wp-71004-audit-cli
FR Traceability: FR-VER-005 (audit log and diff CLI)

Commands:
thegent audit log [--project NAME] [--limit N]
thegent audit diff <sha1> <sha2> [--project NAME]
thegent audit list [--agent ID] [--session ID]

---

## audit_diff

```python
audit_diff(sha1: str, sha2: str, project: str)
```

Show diff between two audit entries.

---

## audit_log

```python
audit_log(project: str, limit: int | None = None)
```

Show audit log entries for a project.

---

## audit_list

```python
audit_list(agent: str | None = None, session: str | None = None)
```

List audit entries with optional filters.

---
