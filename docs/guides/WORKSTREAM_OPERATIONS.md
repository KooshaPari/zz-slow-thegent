# Work Stream Operations Guide

> **Purpose**: Agents should never manually parse WORK_STREAM.md.
> Use `scripts/workstream_helper.py` instead.

---

## Overview

`scripts/workstream_helper.py` provides a structured Python API for reading and
mutating `docs/reference/WORK_STREAM.md`. It uses file locking (`fcntl.LOCK_EX`)
so concurrent agents can safely claim and complete items without races.

---

## Data Model

### WorkStreamItem

```python
@dataclass
class WorkStreamItem:
    id: str  # unique slug, e.g. "swarm-fix-macos-sampling"
    title: str  # human-readable description
    source: str = ""  # origin document
    priority: str = "P2"  # P0 through P4
    depends: str = "-"  # dash or comma-separated dependency IDs
    status: str = "backlog"  # "backlog" | "claimed" | "completed"
    agent: str = ""  # agent that claimed/completed (claimed/completed only)
    timestamp: str = ""  # ISO-8601 when claimed/completed
    notes: str = ""  # free-form notes (completed only)
```

**Methods:**

| Method                          | Description                                     |
| ------------------------------- | ----------------------------------------------- |
| `dependency_ids() -> list[str]` | Returns list of dependency IDs, empty when none |
| `priority_key() -> int`         | Integer sort key (P0=0, P1=1, …, P4=4)          |

### WorkStreamState

```python
@dataclass
class WorkStreamState:
    backlog: list[WorkStreamItem]
    claimed: list[WorkStreamItem]
    completed: list[WorkStreamItem]
```

**Methods:**

| Method                                          | Description                |
| ----------------------------------------------- | -------------------------- |
| `claimed_ids() -> set[str]`                     | IDs of all claimed items   |
| `completed_ids() -> set[str]`                   | IDs of all completed items |
| `all_items() -> list[WorkStreamItem]`           | All items across sections  |
| `find_by_id(item_id) -> WorkStreamItem or None` | Lookup by ID               |

---

## API Reference

### parse_work_stream

```python
def parse_work_stream(path: Path | str | None = None) -> WorkStreamState
```

Parse `WORK_STREAM.md` into a `WorkStreamState`. Returns empty lists when the
file does not exist. Pass `path` to override the default location.

```python
from scripts.workstream_helper import parse_work_stream

state = parse_work_stream()
print(f"Backlog: {len(state.backlog)} items")
print(f"Claimed: {len(state.claimed)} items")
```

---

### get_next_items

```python
def get_next_items(
    n: int = 5,
    min_priority: str = "P2",
    path: Path | str | None = None,
) -> list[WorkStreamItem]
```

Return up to `n` unblocked, unclaimed backlog items sorted by priority
(P0 first). Items are excluded when:

- already in CLAIMED, or
- their `min_priority` rank exceeds the threshold, or
- any dependency has not yet appeared in COMPLETED.

```python
from scripts.workstream_helper import get_next_items

# Top 5 P1-or-higher items ready to work on
items = get_next_items(n=5, min_priority="P1")
for item in items:
    print(f"[{item.priority}] {item.id}: {item.title}")
```

---

### get_blocked_items

```python
def get_blocked_items(path: Path | str | None = None) -> list[WorkStreamItem]
```

Return all backlog items whose dependencies are not yet in COMPLETED.

```python
from scripts.workstream_helper import get_blocked_items

for item in get_blocked_items():
    missing = [d for d in item.dependency_ids() if d not in completed_ids]
    print(f"{item.id} is waiting for: {missing}")
```

---

### claim_item

```python
def claim_item(item_id: str, agent_id: str, path: Path | str | None = None) -> bool
```

Atomically add `item_id` to the CLAIMED section with `agent_id` and the
current UTC timestamp. Returns `False` when:

- the item does not exist in BACKLOG,
- the item is already claimed, or
- the file cannot be written.

```python
from scripts.workstream_helper import claim_item

success = claim_item("swarm-fix-macos-sampling", "agent-1")
if not success:
    print("Item is already claimed or does not exist.")
```

---

### complete_item

```python
def complete_item(
    item_id: str,
    agent_id: str,
    notes: str = "",
    path: Path | str | None = None,
) -> bool
```

Atomically move `item_id` from CLAIMED (or BACKLOG) to COMPLETED. Returns
`False` when the item is not found or the file cannot be written.

```python
from scripts.workstream_helper import complete_item

complete_item("swarm-fix-macos-sampling", "agent-1", notes="Fixed vm_stat calls.")
```

---

### add_backlog_item

```python
def add_backlog_item(item: WorkStreamItem, path: Path | str | None = None) -> bool
```

Append `item` to the BACKLOG section. Returns `False` on duplicates or when
the file does not exist.

```python
from scripts.workstream_helper import WorkStreamItem, add_backlog_item

new_task = WorkStreamItem(
    id="my-new-task",
    title="Implement feature X",
    source="FEATURE_X_PLAN.md",
    priority="P2",
    depends="prerequisite-task",
)
add_backlog_item(new_task)
```

---

## Typical Agent Workflow

```python
from scripts.workstream_helper import (
    get_next_items,
    claim_item,
    complete_item,
)

AGENT_ID = "agent-session-abc123"

# 1. Find the next item to work on
items = get_next_items(n=1, min_priority="P2")
if not items:
    print("No work available.")
else:
    item = items[0]

    # 2. Claim it before starting
    if claim_item(item.id, AGENT_ID):
        print(f"Working on: {item.id}")

        # 3. ... do the actual work ...

        # 4. Mark complete when done
        complete_item(item.id, AGENT_ID, notes="Implementation merged.")
    else:
        print(f"{item.id} was already claimed by another agent.")
```

---

## CLI Usage

```bash
# List next 5 ready items (JSON)
python scripts/workstream_helper.py next 5

# List blocked items
python scripts/workstream_helper.py blocked

# Print section counts
python scripts/workstream_helper.py parse
```

---

## Testing

```bash
python -m pytest tests/test_workstream_helper.py -v
```

All tests use `tmp_path` fixtures and never touch the production
`docs/reference/WORK_STREAM.md`.

---

## File Locking

`claim_item`, `complete_item`, and `add_backlog_item` acquire an exclusive
`fcntl` lock on `WORK_STREAM.md` before reading and writing. This prevents
two agents running concurrently from both claiming the same item, as long as
they both use these helpers. Direct file edits bypass the lock.

> **Note**: `fcntl` locks are advisory on most POSIX systems. All writers
> must use this helper to benefit from the lock.

---

## Path Override

All functions accept an optional `path` argument for testing against a copy
of the file or a fixture:

```python
state = parse_work_stream(path="/tmp/test-work-stream.md")
items = get_next_items(path=Path("/tmp/test-work-stream.md"))
```
