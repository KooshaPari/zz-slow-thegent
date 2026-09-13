# git_parallelism API Reference

> **Source**: `src/thegent/infra/git_parallelism.py`

High-performance parallel git operations via plumbing and per-agent index files.

---

## GitParallelismManager

Manages parallel git operations using per-agent index files and plumbing.

### Methods

#### GitParallelismManager.**init**

```python
__init__(self: Any, project_root: Path, agent_id: str)
```

---

#### GitParallelismManager.create_commit_from_index

```python
create_commit_from_index(self: Any, message: str, parent_ref: str)
```

Git plumbing commit pipeline: hash -> tree -> commit (TGNT-P6.2).

---

#### GitParallelismManager.ensure_index

```python
ensure_index(self: Any)
```

Create or refresh the per-agent index file (TGNT-P6.1).

---

#### GitParallelismManager.get_agent_status

```python
get_agent_status(self: Any)
```

Show per-agent staged changes (TGNT-P6.5).

---

#### GitParallelismManager.stage_files

```python
stage_files(self: Any, files: list[str])
```

Stage specific files using the agent's index (TGNT-P6.4).

---

#### GitParallelismManager.update_ref_cas

```python
update_ref_cas(self: Any, ref: str, new_hash: str, old_hash: str)
```

CAS (Compare-And-Swap) ref update with backoff + jitter (TGNT-P6.3).

---

---

## create_commit_from_index

```python
create_commit_from_index(self: Any, message: str, parent_ref: str)
```

Git plumbing commit pipeline: hash -> tree -> commit (TGNT-P6.2).

---

## ensure_index

```python
ensure_index(self: Any)
```

Create or refresh the per-agent index file (TGNT-P6.1).

---

## get_agent_status

```python
get_agent_status(self: Any)
```

Show per-agent staged changes (TGNT-P6.5).

---

## harness_git_status_view

```python
harness_git_status_view(agent_id: str)
```

Entry point for 'harness git status' (TGNT-P6.5).

---

## stage_files

```python
stage_files(self: Any, files: list[str])
```

Stage specific files using the agent's index (TGNT-P6.4).

---

## update_ref_cas

```python
update_ref_cas(self: Any, ref: str, new_hash: str, old_hash: str)
```

CAS (Compare-And-Swap) ref update with backoff + jitter (TGNT-P6.3).

---
