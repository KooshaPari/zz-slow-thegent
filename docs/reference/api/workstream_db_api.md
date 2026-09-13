# workstream_db API Reference

> **Source**: `src/thegent/planning/workstream_db.py`

Workstream database for auto-launch system.

SQLite database for tracking sessions, workstream items, launches, and all related data.
Harmonized with EvidenceLedger, RunRegistry, and other thegent components.

---

## WorkstreamDB

SQLite database for workstream tracking and auto-launch observability.

Canonical PM: DB is primary; WORK_STREAM.md is generated view.

### Methods

#### WorkstreamDB.**init**

```python
__init__(self: Any, db_path: Any, settings: Any)
```

Initialize workstream database.

**Parameters**:

- `db_path`: Path to SQLite database file. Defaults to session_dir/workstream.db
- `settings`: ThegentSettings instance. Required if db_path not provided.

---

#### WorkstreamDB.execute_query

```python
execute_query(self: Any, query: str, params: tuple[(Any, Ellipsis)])
```

Execute a SQL query and return results as list of dicts.

---

#### WorkstreamDB.generate_work_stream_md

```python
generate_work_stream_md(self: Any, output_path: Path)
```

Generate WORK_STREAM.md from canonical DB.

---

#### WorkstreamDB.get_active_items

```python
get_active_items(self: Any)
```

Get active workstream items.

---

#### WorkstreamDB.get_dependency_graph

```python
get_dependency_graph(self: Any)
```

Get the full dependency graph.

---

#### WorkstreamDB.get_next_items

```python
get_next_items(self: Any, limit: int, completed_ids: Any)
```

Get next actionable items from canonical DB (do_next format).

---

#### WorkstreamDB.get_ready_items

```python
get_ready_items(self: Any, max_retries: int, base_backoff_sec: int)
```

Get items that are pending and have all dependencies satisfied.

Supports exponential backoff for failed items.

---

#### WorkstreamDB.get_recent_costs

```python
get_recent_costs(self: Any, limit: int)
```

Get recent cost tracking entries.

---

#### WorkstreamDB.get_running_count

```python
get_running_count(self: Any)
```

Get count of running sessions.

---

#### WorkstreamDB.get_running_count_by_lane

```python
get_running_count_by_lane(self: Any)
```

Get count of running sessions by lane.

---

#### WorkstreamDB.get_running_sessions

```python
get_running_sessions(self: Any)
```

Get all running sessions.

---

#### WorkstreamDB.get_session

```python
get_session(self: Any, session_id: str)
```

Get session by ID.

---

#### WorkstreamDB.get_statistics

```python
get_statistics(self: Any)
```

Get workstream statistics.

---

#### WorkstreamDB.get_top_agents

```python
get_top_agents(self: Any, limit: int)
```

Get top agents by XP.

---

#### WorkstreamDB.mark_session_complete

```python
mark_session_complete(self: Any, session_id: str, exit_code: int)
```

Mark a session as complete.

---

#### WorkstreamDB.record_constitutional_violation

```python
record_constitutional_violation(self: Any, item_id: str, session_id: Any, violation: Any)
```

Record a constitutional violation.

---

#### WorkstreamDB.record_cost

```python
record_cost(self: Any, session_id: str, cost_usd: float, tokens_total: int, model: Any)
```

Record cost for a session.

---

#### WorkstreamDB.record_launch

```python
record_launch(self: Any, item_id: str, session_id: str, lane: str, model: str, estimated_cost: float, trigger_type: str, pid: Any)
```

Record a launch in the database.

---

#### WorkstreamDB.record_resource_usage

```python
record_resource_usage(self: Any, session_id: str, usage: dict[(str, Any)])
```

Record resource usage for a session.

---

#### WorkstreamDB.record_session

```python
record_session(self: Any, session_id: str, agent: str, prompt: str, status: str, workstream_item_id: Any, lane: Any, model: Any, owner_tag: Any, team_id: Any, task_id: Any)
```

Record or update a session in the database.

---

#### WorkstreamDB.sync_from_agileplus

```python
sync_from_agileplus(self: Any, session_dir: Path)
```

Sync AgilePlus backlog.jsonl into canonical workstream. Returns count upserted.

---

#### WorkstreamDB.sync_from_queues

```python
sync_from_queues(self: Any, session_dir: Path)
```

Sync PromptQueue, EscalationQueue, DeferralQueue into canonical workstream. Returns count upserted.

---

#### WorkstreamDB.sync_with_markdown

```python
sync_with_markdown(self: Any, work_stream_path: Path)
```

Sync WORK_STREAM.md with the database.

Bidirectional sync:

1. Parse WORK_STREAM.md
2. Update database workstream_items and dependencies
3. (Optional) Could update markdown from DB if needed

---

#### WorkstreamDB.sync_workstream

```python
sync_workstream(self: Any, workstream_data: dict[(str, Any)])
```

Sync workstream data from markdown parser to database.

**Parameters**:

- `workstream_data`: Dict with 'backlog', 'claimed', 'completed' keys.

---

#### WorkstreamDB.upsert_canonical_item

```python
upsert_canonical_item(self: Any, item_id: str, title: str, source: str, source_system: str, priority: str, status: str, metadata: Any, depends: Any)
```

Upsert a work item into the canonical PM store.

---

---

## execute_query

```python
execute_query(self: Any, query: str, params: tuple[(Any, Ellipsis)])
```

Execute a SQL query and return results as list of dicts.

---

## generate_work_stream_md

```python
generate_work_stream_md(self: Any, output_path: Path)
```

Generate WORK_STREAM.md from canonical DB.

---

## get_active_items

```python
get_active_items(self: Any)
```

Get active workstream items.

---

## get_dependency_graph

```python
get_dependency_graph(self: Any)
```

Get the full dependency graph.

---

## get_next_items

```python
get_next_items(self: Any, limit: int, completed_ids: Any)
```

Get next actionable items from canonical DB (do_next format).

---

## get_ready_items

```python
get_ready_items(self: Any, max_retries: int, base_backoff_sec: int)
```

Get items that are pending and have all dependencies satisfied.

Supports exponential backoff for failed items.

---

## get_recent_costs

```python
get_recent_costs(self: Any, limit: int)
```

Get recent cost tracking entries.

---

## get_running_count

```python
get_running_count(self: Any)
```

Get count of running sessions.

---

## get_running_count_by_lane

```python
get_running_count_by_lane(self: Any)
```

Get count of running sessions by lane.

---

## get_running_sessions

```python
get_running_sessions(self: Any)
```

Get all running sessions.

---

## get_session

```python
get_session(self: Any, session_id: str)
```

Get session by ID.

---

## get_statistics

```python
get_statistics(self: Any)
```

Get workstream statistics.

---

## get_top_agents

```python
get_top_agents(self: Any, limit: int)
```

Get top agents by XP.

---

## mark_session_complete

```python
mark_session_complete(self: Any, session_id: str, exit_code: int)
```

Mark a session as complete.

---

## record_constitutional_violation

```python
record_constitutional_violation(self: Any, item_id: str, session_id: Any, violation: Any)
```

Record a constitutional violation.

---

## record_cost

```python
record_cost(self: Any, session_id: str, cost_usd: float, tokens_total: int, model: Any)
```

Record cost for a session.

---

## record_launch

```python
record_launch(self: Any, item_id: str, session_id: str, lane: str, model: str, estimated_cost: float, trigger_type: str, pid: Any)
```

Record a launch in the database.

---

## record_resource_usage

```python
record_resource_usage(self: Any, session_id: str, usage: dict[(str, Any)])
```

Record resource usage for a session.

---

## record_session

```python
record_session(self: Any, session_id: str, agent: str, prompt: str, status: str, workstream_item_id: Any, lane: Any, model: Any, owner_tag: Any, team_id: Any, task_id: Any)
```

Record or update a session in the database.

---

## sync_from_agileplus

```python
sync_from_agileplus(self: Any, session_dir: Path)
```

Sync AgilePlus backlog.jsonl into canonical workstream. Returns count upserted.

---

## sync_from_queues

```python
sync_from_queues(self: Any, session_dir: Path)
```

Sync PromptQueue, EscalationQueue, DeferralQueue into canonical workstream. Returns count upserted.

---

## sync_with_markdown

```python
sync_with_markdown(self: Any, work_stream_path: Path)
```

Sync WORK_STREAM.md with the database.

Bidirectional sync:

1. Parse WORK_STREAM.md
2. Update database workstream_items and dependencies
3. (Optional) Could update markdown from DB if needed

---

## sync_workstream

```python
sync_workstream(self: Any, workstream_data: dict[(str, Any)])
```

Sync workstream data from markdown parser to database.

**Parameters**:

- `workstream_data`: Dict with 'backlog', 'claimed', 'completed' keys.

---

## upsert_canonical_item

```python
upsert_canonical_item(self: Any, item_id: str, title: str, source: str, source_system: str, priority: str, status: str, metadata: Any, depends: Any)
```

Upsert a work item into the canonical PM store.

---
