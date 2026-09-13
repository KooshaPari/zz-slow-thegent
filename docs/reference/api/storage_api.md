# storage API Reference

> **Source**: `src/thegent/queue/storage.py`

WP-7001: Unified prompt queue storage.

---

## PromptQueue

Manages a unified queue of deferred agent prompts.

### Methods

#### PromptQueue.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### PromptQueue.append

```python
append(self: Any, prompt: str, project: str, agent: Any)
```

Append a new prompt to the queue.

---

#### PromptQueue.claim

```python
claim(self: Any, claimer_id: str, lease_seconds: int, project: Any)
```

Atomically claim the first pending item. Returns claimed item or None.

---

#### PromptQueue.done

```python
done(self: Any, item_id: int)
```

Mark item by id as done. Returns True if found and updated.

---

#### PromptQueue.edit

```python
edit(self: Any, item_id: int, prompt: str)
```

Edit prompt for an item. Only pending or claimed items. Returns True if updated.

---

#### PromptQueue.extend_lease

```python
extend_lease(self: Any, item_id: int, lease_seconds: int)
```

Extend lease for a claimed item. Returns True if found and updated.

---

#### PromptQueue.get_pending_count

```python
get_pending_count(self: Any)
```

Return count of pending items.

---

#### PromptQueue.list_all

```python
list_all(self: Any, include_done: bool, include_expired: bool, limit: Any)
```

List queue items with optional filters. Each item gets an 'id' (0-based position).

---

#### PromptQueue.list_pending

```python
list_pending(self: Any)
```

List all pending (unclaimed) items.

---

#### PromptQueue.release

```python
release(self: Any, item_id: int)
```

Release a claim by item id. Returns True if found and updated.

---

---

## append

```python
append(self: Any, prompt: str, project: str, agent: Any)
```

Append a new prompt to the queue.

---

## claim

```python
claim(self: Any, claimer_id: str, lease_seconds: int, project: Any)
```

Atomically claim the first pending item. Returns claimed item or None.

---

## done

```python
done(self: Any, item_id: int)
```

Mark item by id as done. Returns True if found and updated.

---

## edit

```python
edit(self: Any, item_id: int, prompt: str)
```

Edit prompt for an item. Only pending or claimed items. Returns True if updated.

---

## extend_lease

```python
extend_lease(self: Any, item_id: int, lease_seconds: int)
```

Extend lease for a claimed item. Returns True if found and updated.

---

## get_pending_count

```python
get_pending_count(self: Any)
```

Return count of pending items.

---

## list_all

```python
list_all(self: Any, include_done: bool, include_expired: bool, limit: Any)
```

List queue items with optional filters. Each item gets an 'id' (0-based position).

---

## list_pending

```python
list_pending(self: Any)
```

List all pending (unclaimed) items.

---

## release

```python
release(self: Any, item_id: int)
```

Release a claim by item id. Returns True if found and updated.

---
