# snapshot API Reference

> **Source**: `src/thegent/forensics/snapshot.py`

WP-12001: Forensic snapshotting for deep debugging and audit.

---

## ForensicSnapshotter

Captures detailed system and project state snapshots.

### Methods

#### ForensicSnapshotter.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### ForensicSnapshotter.capture_post_run

```python
capture_post_run(self: Any, run_id: str, project_root: Path, exit_code: int)
```

Capture state after a run, including git diff.

---

#### ForensicSnapshotter.capture_pre_run

```python
capture_pre_run(self: Any, run_id: str, project_root: Path)
```

Capture state before a run.

---

---

## capture_post_run

```python
capture_post_run(self: Any, run_id: str, project_root: Path, exit_code: int)
```

Capture state after a run, including git diff.

---

## capture_pre_run

```python
capture_pre_run(self: Any, run_id: str, project_root: Path)
```

Capture state before a run.

---
