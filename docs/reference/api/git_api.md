# git API Reference

> **Source**: `src/thegent/mesh/git.py`

High-performance parallel git operations for the agent mesh.

---

## GitParallelismManager

Manages parallel git operations using per-agent index files and plumbing (SCLI-P4.1–P4.2).

### Methods

#### GitParallelismManager.**init**

```python
__init__(self: Any, project_root: Path, agent_id: str, mesh_root: Path)
```

---

#### GitParallelismManager.create_commit_from_index

```python
create_commit_from_index(self: Any, message: str, parent_ref: str)
```

Git plumbing commit pipeline: hash -&gt; tree -&gt; commit (SCLI-P4.2).

---

#### GitParallelismManager.ensure_index

```python
ensure_index(self: Any)
```

Create or refresh the per-agent index file (SCLI-P4.1).

---

#### GitParallelismManager.get_agent_status

```python
get_agent_status(self: Any)
```

Show per-agent staged changes (SCLI-P4.5).

---

#### GitParallelismManager.stage_files

```python
stage_files(self: Any, files: list[str])
```

Stage specific files using the agent's index (SCLI-P4.4).

---

#### GitParallelismManager.update_ref_cas

```python
update_ref_cas(self: Any, ref: str, new_hash: str, old_hash: str)
```

CAS (Compare-And-Swap) ref update with backoff + jitter (SCLI-P4.3).

---

---

## create_commit_from_index

```python
create_commit_from_index(self: Any, message: str, parent_ref: str)
```

Git plumbing commit pipeline: hash -&gt; tree -&gt; commit (SCLI-P4.2).

---

## ensure_index

```python
ensure_index(self: Any)
```

Create or refresh the per-agent index file (SCLI-P4.1).

---

## get_agent_status

```python
get_agent_status(self: Any)
```

Show per-agent staged changes (SCLI-P4.5).

---

## stage_files

```python
stage_files(self: Any, files: list[str])
```

Stage specific files using the agent's index (SCLI-P4.4).

---

## update_ref_cas

```python
update_ref_cas(self: Any, ref: str, new_hash: str, old_hash: str)
```

CAS (Compare-And-Swap) ref update with backoff + jitter (SCLI-P4.3).

---
