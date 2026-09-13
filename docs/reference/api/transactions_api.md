# transactions API Reference

> **Source**: `src/thegent/orchestration/transactions.py`

WP-15003: Atomic Transactions and Commit-Log Orchestration (CLO).

MTSP-13/14: Ensure multi-step agent actions are atomic or revertible.

---

## TransactionManager

Manages atomic blocks of operations with rollback support.

### Methods

#### TransactionManager.**init**

```python
__init__(self: Any, run_id: str)
```

---

#### TransactionManager.add_op

```python
add_op(self: Any, description: str, do: Callable, undo: Callable)
```

Add an operation to the transaction.

---

---

## TransactionOperation

A single revertible operation within a transaction.

---

## add_op

```python
add_op(self: Any, description: str, do: Callable, undo: Callable)
```

Add an operation to the transaction.

---

## apply_multi_file_transaction

```python
apply_multi_file_transaction(changes: list[(tuple[(Path, str)], str)], cwd: Any, git_commit: bool, commit_message: str)
```

MTSP-13: Prepare multi-file changes and apply as a single atomic transaction.

Writes each file to a temp path, then renames all atomically. On failure, no files are modified.
If git_commit=True and cwd is a git repo, stages and commits as a single transaction.

**Returns**: (success, message)

---
