# store API Reference

> **Source**: `src/thegent/maif/store.py`

MAIF Artifact Store implementation for thegent.

---

## MAIFArtifactStore

SQLite-based storage for MAIF artifacts.

### Methods

#### MAIFArtifactStore.**init**

```python
__init__(self: Any, db_path: Path)
```

---

#### MAIFArtifactStore.get

```python
get(self: Any, artifact_id: str)
```

Retrieve artifact by ID.

---

#### MAIFArtifactStore.list_by_session

```python
list_by_session(self: Any, session_id: str)
```

List all artifacts for a given session.

---

#### MAIFArtifactStore.store

```python
store(self: Any, artifact: MAIFArtifact)
```

Store artifact in local cache.

---

---

## get

```python
get(self: Any, artifact_id: str)
```

Retrieve artifact by ID.

---

## list_by_session

```python
list_by_session(self: Any, session_id: str)
```

List all artifacts for a given session.

---

## store

```python
store(self: Any, artifact: MAIFArtifact)
```

Store artifact in local cache.

---
