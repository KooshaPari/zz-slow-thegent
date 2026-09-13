# Agent Helpers Guide

**Location**: `scripts/agent_helpers.py`
**Tests**: `tests/test_agent_helpers.py`

A reusable library of thin-wrapper helpers for patterns that recur across agents, hooks, and scripts. Import individual functions or the full module.

---

## Quick Import

```python
from agent_helpers import (
    log_friction,
    get_next_items,
    update_work_stream,
    run_quality_check,
    read_config,
    format_summary,
)
```

All helpers work without activating a virtual environment — they use standard library modules only (except `read_config`, which optionally loads `ThegentSettings`).

---

## Helpers

### 1. `log_friction`

Log a DX/UX/AX friction point to `docs/research/FRICTION_LOG.md`.

**Signature**

```python
def log_friction(
    category: str,
    description: str,
    impact: str = "medium",
    *,
    task_id: str | None = None,
    friction_type: str = "general",
    location: str = "unknown",
    solution: str = "",
    priority: str = "P2",
    friction_log_path: Path | None = None,
) -> bool:
```

**Parameters**

| Parameter           | Type           | Default          | Description                                      |
| ------------------- | -------------- | ---------------- | ------------------------------------------------ |
| `category`          | `str`          | required         | `dx`, `ux`, or `ax`                              |
| `description`       | `str`          | required         | What friction was observed                       |
| `impact`            | `str`          | `"medium"`       | `low`, `medium`, or `high`                       |
| `task_id`           | `str or None`  | auto             | Section header in log; auto-generated if omitted |
| `friction_type`     | `str`          | `"general"`      | Sub-type label (e.g. `verbosity`, `complexity`)  |
| `location`          | `str`          | `"unknown"`      | File, function, or pattern where friction occurs |
| `solution`          | `str`          | `""`             | Proposed fix; defaults to `TBD`                  |
| `priority`          | `str`          | `"P2"`           | `P1` (blocking) or `P2` (improvement)            |
| `friction_log_path` | `Path or None` | default log path | Override for testing                             |

**Returns**: `True` on success, `False` on write failure.

**Examples**

```python
# Minimal
log_friction("dx", "Multiple read_file calls for config loading")

# With all fields
log_friction(
    "ux",
    description="Users must cd && <cmd> to run CLI from subdirectories",
    impact="high",
    task_id="ux-cd-workaround-20260219",
    friction_type="verbosity",
    location="scripts/start_proxy.py",
    solution="Add --cd flag to CLI to set working directory",
    priority="P1",
)
```

---

### 2. `get_next_items`

Return the next actionable unclaimed items from `docs/reference/WORK_STREAM.md`.

Items are excluded when:

- They are already in the **CLAIMED** section.
- They are already in the **COMPLETED** section.
- Their `Depends` column references IDs not yet in COMPLETED.

**Signature**

```python
def get_next_items(
    limit: int = 5,
    *,
    priority: str | None = None,
    work_stream_path: Path | None = None,
) -> list[dict[str, str]]:
```

**Parameters**

| Parameter          | Type           | Default      | Description                                          |
| ------------------ | -------------- | ------------ | ---------------------------------------------------- |
| `limit`            | `int`          | `5`          | Maximum items to return                              |
| `priority`         | `str or None`  | `None`       | Filter by priority (e.g. `"P1"`); `None` returns all |
| `work_stream_path` | `Path or None` | default path | Override for testing                                 |

**Returns**: List of dicts with keys `id`, `title`, `source`, `priority`, `depends`.

**Examples**

```python
# Get the next 3 items of any priority
items = get_next_items(limit=3)
for item in items:
    print(f"[{item['priority']}] {item['id']}: {item['title']}")

# P1-only items
p1_items = get_next_items(limit=10, priority="P1")
```

---

### 3. `update_work_stream`

Claim or complete a work stream item in `WORK_STREAM.md`.

- **`"claimed"`** — removes the row from BACKLOG and inserts it into CLAIMED.
- **`"completed"`** — removes the row from both BACKLOG and CLAIMED and inserts it into COMPLETED.

**Signature**

```python
def update_work_stream(
    item_id: str,
    status: str,
    notes: str = "",
    *,
    agent_id: str = "agent-helpers",
    work_stream_path: Path | None = None,
) -> bool:
```

**Parameters**

| Parameter          | Type           | Default           | Description                      |
| ------------------ | -------------- | ----------------- | -------------------------------- |
| `item_id`          | `str`          | required          | Work-item ID                     |
| `status`           | `str`          | required          | `"claimed"` or `"completed"`     |
| `notes`            | `str`          | `""`              | Optional notes stored in the row |
| `agent_id`         | `str`          | `"agent-helpers"` | Agent performing the update      |
| `work_stream_path` | `Path or None` | default path      | Override for testing             |

**Returns**: `True` on success, `False` on write failure or missing file.

**Raises**: `ValueError` if `status` is not `"claimed"` or `"completed"`.

**Examples**

```python
# Claim an item before starting work
update_work_stream("cache-multi-level", "claimed", agent_id="my-agent-session")

# Complete it when done
update_work_stream("cache-multi-level", "completed", notes="diskcache integrated")
```

---

### 4. `run_quality_check`

Run `ruff check` (lint) and/or `pytest` and return structured results.

Both commands run via `uv run` to use the project virtual environment.

**Signature**

```python
def run_quality_check(
    *,
    project_root: Path | None = None,
    run_lint: bool = True,
    run_tests: bool = True,
    test_path: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
```

**Parameters**

| Parameter      | Type           | Default   | Description                          |
| -------------- | -------------- | --------- | ------------------------------------ |
| `project_root` | `Path or None` | repo root | Directory to run commands in         |
| `run_lint`     | `bool`         | `True`    | Whether to run ruff                  |
| `run_tests`    | `bool`         | `True`    | Whether to run pytest                |
| `test_path`    | `str or None`  | `None`    | Specific test path to pass to pytest |
| `timeout`      | `int`          | `120`     | Per-command timeout in seconds       |

**Return shape**

```python
{
    "lint_passed": bool,
    "lint_output": str,
    "tests_passed": bool,
    "tests_output": str,
    "overall_passed": bool,  # lint_passed AND tests_passed
    "errors": list[str],  # populated on any failure
}
```

**Examples**

```python
# Full check
result = run_quality_check()
if not result["overall_passed"]:
    for err in result["errors"]:
        print(err)

# Lint only, no tests
result = run_quality_check(run_tests=False)

# Run only the agent_helpers tests
result = run_quality_check(
    run_lint=False,
    test_path="tests/test_agent_helpers.py",
)
```

---

### 5. `read_config`

Read a configuration value from `ThegentSettings` with a default fallback.

Falls back to `default` when:

- `ThegentSettings` is not importable (running outside the package).
- The key does not exist on the settings class.
- Settings instantiation raises any exception.

**Signature**

```python
def read_config(key: str, default: Any = None) -> Any:
```

**Parameters**

| Parameter | Type  | Default  | Description                         |
| --------- | ----- | -------- | ----------------------------------- |
| `key`     | `str` | required | Attribute name on `ThegentSettings` |
| `default` | `Any` | `None`   | Fallback value                      |

**Examples**

```python
timeout = read_config("default_timeout", default=300)
session_dir = read_config("session_dir", default=Path("/tmp/thegent"))

# Safe access to any setting without try/except boilerplate
max_concurrency = read_config("max_concurrency", default=4)
```

**Available keys** (subset of `ThegentSettings`):

| Key                      | Type   | Description                     |
| ------------------------ | ------ | ------------------------------- |
| `default_timeout`        | `int`  | Default agent timeout (seconds) |
| `default_timeout_claude` | `int`  | Claude-specific timeout         |
| `default_timeout_free`   | `int`  | Free-tier timeout               |
| `session_dir`            | `Path` | Background session directory    |
| `cache_dir`              | `Path` | Global cache directory          |
| `max_concurrency`        | `int`  | Max concurrent agents           |

---

### 6. `format_summary`

Format a consistent Markdown agent output summary.

**Signature**

```python
def format_summary(title: str, items: list[Any]) -> str:
```

**Parameters**

| Parameter | Type        | Default  | Description                               |
| --------- | ----------- | -------- | ----------------------------------------- |
| `title`   | `str`       | required | Summary heading                           |
| `items`   | `list[Any]` | required | Items to list; each converted via `str()` |

**Returns**: Markdown string with a numbered list and UTC timestamp footer.

**Examples**

```python
# Basic usage
print(format_summary("Work Items Processed", ["task-alpha", "task-beta"]))
# Output:
# ## Work Items Processed (2 items)
#
# 1. task-alpha
# 2. task-beta
#
# _Generated: 2026-02-19T12:00:00Z_

# Empty list
print(format_summary("No Findings", []))
# Output:
# ## No Findings (0 items)
#
# _(no items)_
#
# _Generated: 2026-02-19T12:00:00Z_

# With structured items
results = [f"{item['id']}: {item['title']}" for item in get_next_items()]
print(format_summary("Next Work Items", results))
```

---

## CLI Usage

The module ships with a minimal CLI for quick manual use:

```bash
# Get next 5 work items (JSON output)
python scripts/agent_helpers.py next

# Get next 10 P1 items
python scripts/agent_helpers.py next --limit 10 --priority P1

# Log a friction point
python scripts/agent_helpers.py log-friction dx "Multiple subprocess calls without batching"

# Run quality check
python scripts/agent_helpers.py quality
```

---

## Design Notes

- **No lint suppressions**: The optional `ThegentSettings` import uses `importlib.import_module` rather than a bare import so that no annotation-level workarounds are needed. The project's suppression blocker hook blocks any new suppressions.
- **Thin wrappers only**: Each helper is under 50 lines of domain logic. Heavy lifting (retry, caching, file watching) is delegated to existing libraries (`tenacity`, `cachetools`, `watchdog`).
- **Test-friendly**: Every path-sensitive helper accepts an optional override parameter (`friction_log_path`, `work_stream_path`, `project_root`) so tests can operate on temporary directories without monkey-patching globals.
- **Explicit failures**: Helpers return `bool` or structured dicts rather than raising on common errors. `ValueError` is raised only for genuinely invalid arguments (e.g. bad `status`).
