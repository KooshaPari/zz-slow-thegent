# episode_controller API Reference

> **Source**: `src/thegent/audit/episode_controller.py`

Episode lifecycle controller.

Manages agent episode lifecycle (start/end/suspend/resume) by integrating
with ProjectRegistry for episode records and ShadowAuditGit for audit
trail entries at episode boundaries.

WBS: wp-71003-episode-ctrl
FR Traceability: FR-VER-004 (episode lifecycle management)

---

## EpisodeController

Manages the lifecycle of an agent episode.

Can be used as a context manager::

    with EpisodeController(project_id="p1", agent_id="a1", registry=reg, shadow=shadow):
        # agent work happens here
        ...

On normal exit the episode is marked completed; on exception it is
marked failed.

### Methods

#### EpisodeController.**init**

```python
__init__(self: Any, project_id: str, agent_id: str, registry: ProjectRegistry, shadow: ShadowAuditGit, metadata: Any)
```

---

#### EpisodeController.end

```python
end(self: Any)
```

End the current episode. Raises RuntimeError if not started.

---

#### EpisodeController.episode

```python
episode(self: Any)
```

The current episode record, or None if not started.

---

#### EpisodeController.resume

```python
resume(self: Any)
```

Resume a suspended episode. Raises RuntimeError if not suspended.

---

#### EpisodeController.start

```python
start(self: Any)
```

Start a new episode. Raises RuntimeError if already started.

---

#### EpisodeController.suspend

```python
suspend(self: Any)
```

Suspend the current episode. Raises RuntimeError if not started.

---

---

## end

```python
end(self: Any)
```

End the current episode. Raises RuntimeError if not started.

---

## episode

```python
episode(self: Any)
```

The current episode record, or None if not started.

---

## resume

```python
resume(self: Any)
```

Resume a suspended episode. Raises RuntimeError if not suspended.

---

## start

```python
start(self: Any)
```

Start a new episode. Raises RuntimeError if already started.

---

## suspend

```python
suspend(self: Any)
```

Suspend the current episode. Raises RuntimeError if not started.

---
