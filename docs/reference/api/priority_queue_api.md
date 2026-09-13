# priority_queue API Reference

> **Source**: `src/thegent/orchestration/execution/priority_queue.py`

Priority queue for thegent swarm run scheduling.

Implements a thread-safe priority queue that orders run items by lane priority,
supporting FIFO within the same priority level. Integrates with the existing
lanes.py lane model.

WP-1002, FR-019: Respects lane priorities from LaneModel (critical=0, standard=10,
recovery=20, background=100). Lower priority_score = dispatched first.

---

## QueuedRun

A run item waiting in the priority queue.

### Methods

#### QueuedRun.from_lane

```python
from_lane(cls: Any, run_id: str, lane_name: str, metadata: Any)
```

Create a QueuedRun with priority_score derived from the lane model.

Uses `LaneModel.get_priority` so the score matches the canonical lane
ordering defined in `lanes.py`.

**Parameters**:

- `run_id`: Unique identifier for this run.
- `lane_name`: One of "critical", "standard", "recovery", "background",
  or any lane name understood by LaneModel.
- `metadata`: Optional caller-supplied key/value pairs.

**Returns**: A `QueuedRun` with `priority_score` set from the lane model.

---

---

## RunPriorityQueue

Thread-safe priority queue for swarm run scheduling.

Runs are ordered by `priority_score` ascending (lower score = dispatched
first). Within the same score, FIFO order is preserved via an internal
sequence counter.

The interface mirrors `queue.PriorityQueue` / `queue.Queue` so callers
can swap without restructuring code.

### Methods

#### RunPriorityQueue.**init**

```python
__init__(self: Any)
```

---

#### RunPriorityQueue.cancel

```python
cancel(self: Any, run_id: str)
```

Remove the run with _run_id_ from the queue.

Because the underlying data structure is a heap, this requires a linear
scan followed by a heap rebuild (O(n)). Use sparingly on hot paths.

**Parameters**:

- `run_id`: The `run_id` of the `QueuedRun` to remove.

**Returns**: `True` if a matching run was found and removed, `False`
otherwise.

---

#### RunPriorityQueue.drain

```python
drain(self: Any)
```

Remove and return all items in priority order.

**Returns**: A list of all `QueuedRun` items sorted by priority (lowest score
first), with FIFO ordering within the same score.

---

#### RunPriorityQueue.empty

```python
empty(self: Any)
```

Return `True` if the queue is empty.

---

#### RunPriorityQueue.full

```python
full(self: Any)
```

Return `True` if the queue is at `maxsize`.

Always returns `False` when `maxsize` is `0` (unbounded).

---

#### RunPriorityQueue.get

```python
get(self: Any, block: bool, timeout: Any)
```

Dequeue and return the highest-priority run (lowest score).

Within the same `priority_score`, items are returned in FIFO order.

**Parameters**:

- `block`: If `True` (default), block until an item is available.
- `timeout`: Maximum seconds to wait when `block=True` and the queue
  is empty. `None` means wait indefinitely.

**Returns**: The next `QueuedRun` in priority order.

---

#### RunPriorityQueue.get_nowait

```python
get_nowait(self: Any)
```

Dequeue and return the highest-priority run without blocking.

---

#### RunPriorityQueue.peek

```python
peek(self: Any)
```

Return the next item without removing it, or `None` if empty.

---

#### RunPriorityQueue.put

```python
put(self: Any, run: QueuedRun, block: bool, timeout: Any)
```

Enqueue _run_, blocking if the queue is full and `block=True`.

**Parameters**:

- `run`: The run item to enqueue.
- `block`: If `True` (default), block until space is available.
- `timeout`: Maximum seconds to wait when `block=True` and the queue
  is full. `None` means wait indefinitely.

---

#### RunPriorityQueue.put_nowait

```python
put_nowait(self: Any, run: QueuedRun)
```

Enqueue _run_ without blocking.

---

#### RunPriorityQueue.qsize

```python
qsize(self: Any)
```

Return the approximate number of items in the queue.

---

---

## cancel

```python
cancel(self: Any, run_id: str)
```

Remove the run with _run_id_ from the queue.

Because the underlying data structure is a heap, this requires a linear
scan followed by a heap rebuild (O(n)). Use sparingly on hot paths.

**Parameters**:

- `run_id`: The `run_id` of the `QueuedRun` to remove.

**Returns**: `True` if a matching run was found and removed, `False`
otherwise.

---

## drain

```python
drain(self: Any)
```

Remove and return all items in priority order.

**Returns**: A list of all `QueuedRun` items sorted by priority (lowest score
first), with FIFO ordering within the same score.

---

## empty

```python
empty(self: Any)
```

Return `True` if the queue is empty.

---

## from_lane

```python
from_lane(cls: Any, run_id: str, lane_name: str, metadata: Any)
```

Create a QueuedRun with priority_score derived from the lane model.

Uses `LaneModel.get_priority` so the score matches the canonical lane
ordering defined in `lanes.py`.

**Parameters**:

- `run_id`: Unique identifier for this run.
- `lane_name`: One of "critical", "standard", "recovery", "background",
  or any lane name understood by LaneModel.
- `metadata`: Optional caller-supplied key/value pairs.

**Returns**: A `QueuedRun` with `priority_score` set from the lane model.

---

## full

```python
full(self: Any)
```

Return `True` if the queue is at `maxsize`.

Always returns `False` when `maxsize` is `0` (unbounded).

---

## get

```python
get(self: Any, block: bool, timeout: Any)
```

Dequeue and return the highest-priority run (lowest score).

Within the same `priority_score`, items are returned in FIFO order.

**Parameters**:

- `block`: If `True` (default), block until an item is available.
- `timeout`: Maximum seconds to wait when `block=True` and the queue
  is empty. `None` means wait indefinitely.

**Returns**: The next `QueuedRun` in priority order.

**Raises**:

- `Empty`: If `block=False` (or timeout expires) and the queue is
  empty.

---

## get_nowait

```python
get_nowait(self: Any)
```

Dequeue and return the highest-priority run without blocking.

**Raises**:

- `Empty`: If the queue is empty.

---

## make_priority_queue

```python
make_priority_queue(maxsize: int)
```

Factory function for `RunPriorityQueue`.

**Parameters**:

- `maxsize`: Maximum queue capacity. `0` means unbounded.

**Returns**: A new `RunPriorityQueue` instance.

---

## peek

```python
peek(self: Any)
```

Return the next item without removing it, or `None` if empty.

---

## put

```python
put(self: Any, run: QueuedRun, block: bool, timeout: Any)
```

Enqueue _run_, blocking if the queue is full and `block=True`.

**Parameters**:

- `run`: The run item to enqueue.
- `block`: If `True` (default), block until space is available.
- `timeout`: Maximum seconds to wait when `block=True` and the queue
  is full. `None` means wait indefinitely.

**Raises**:

- `Full`: If `block=False` (or timeout expires) and the queue is full.

---

## put_nowait

```python
put_nowait(self: Any, run: QueuedRun)
```

Enqueue _run_ without blocking.

**Raises**:

- `Full`: If the queue is full (only when `maxsize &gt; 0`).

---

## qsize

```python
qsize(self: Any)
```

Return the approximate number of items in the queue.

---
