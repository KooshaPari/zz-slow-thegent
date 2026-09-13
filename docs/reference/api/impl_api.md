# impl API Reference

> **Source**: `src/thegent/cli/commands/impl.py`

Thegent implementation layer: functions that return dict/str instead of printing.

\_resolve_cwd() defaults to Path.cwd() when no project indicators found, so no
"cd &amp;&amp;" patterns are needed. Use --cd /path for explicit directory override.
MCP tools may still elicit cwd when meta.cwd is absent (see gofastmcp.com/servers/elicitation).

---

## DagDocument

Parsed DAG session document with structure preserved for round-trip.

---

## RunnerProxy

**Inherits from**: `AgentRunner`

### Methods

#### RunnerProxy.run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int)
```

---

---

## bg_impl

Start a background run. Returns dict with keys: session_id, log_path, owner.

---

## concurrency_set_impl

```python
concurrency_set_impl(limit: int, load_based: bool)
```

Set maximum concurrency limit.

Note: This currently only updates the current process/environment
recommendations for persistence.

---

## concurrency_show_impl

Show current concurrency limits and load-based status.

---

## continuity_snapshot_impl

```python
continuity_snapshot_impl(owner: str, run_ids: list[str], state_summary: Any, next_steps: Any)
```

Create a continuity snapshot for shift handoff (WP-1009).

**Parameters**:

- `owner`: Current owner tag
- `run_ids`: List of run IDs to include in snapshot
- `state_summary`: Optional state summary dictionary
- `next_steps`: Optional list of next steps

**Returns**: Dictionary with snapshot_id and metadata

---

## dag_list_impl

```python
dag_list_impl(cd: Any)
```

List DAG tasks. Returns {frontmatter, tasks} or error.

---

## dag_raw_impl

```python
dag_raw_impl(cd: Any)
```

Get raw DAG markdown content. Returns markdown string or error message.

---

## dag_ready_impl

```python
dag_ready_impl(cd: Any)
```

List task ids that are ready (pending with all deps done|cancelled|skipped).

---

## dag_run_impl

```python
dag_run_impl(cd: Any, dry_run: bool, task: Any, max_parallel: Any, lane: Any, check_drift: bool, contract_version: Any)
```

Spawn thegent bg for each ready task; update status=running and session_id.

---

## dag_status_impl

```python
dag_status_impl(cd: Any)
```

For each task with session_id show id, status, session_id, session_status.

---

## dag_sync_impl

```python
dag_sync_impl(cd: Any, auto_run_next: bool)
```

For tasks with session_id and status=running, if pid not running set status=done or failed from rc.

If --auto-run-next, spawn next ready tasks after sync.

---

## do_next_impl

```python
do_next_impl(cd: Any, limit: int)
```

Find next actionable work items from WORK_STREAM.md and all queued sources.

Sources (in priority order):

- ESCALATION: Past-SLA blocked runs (resolve first)
- PROMPT_QUEUE: $defer prompts (use thegent_queue_claim/done)
- DEFERRAL: Deferred runs to resume (use thegent orchestrate deferral resume)
- BACKLOG: AgilePlus pending findings
- WORK_STREAM: BACKLOG items with deps satisfied, not claimed/completed

**Parameters**:

- `cd`: Optional working directory (default: inferred from cwd)
- `limit`: Max items to return (default: 5, min: 1, max: 100)

**Returns**: dict with:

- next_items: list of {id, description, source, prompt_suggestion, queue_item_id?, run_id?}
- count: number of items returned
- sources_checked: list of sources checked
- empty_reason: optional reason if no items found

---

## escalate_add_impl

```python
escalate_add_impl(run_id: str, reason: str, sla_minutes: int, owner: Any, agent: Any, lane: str, priority: int)
```

WP-3008: Add a blocked run to the escalation queue.

---

## escalate_approve_impl

```python
escalate_approve_impl(run_id: str)
```

WP-3008: Approve an escalation, marking it as approved in the queue (G-GP-05).

---

## escalate_list_impl

```python
escalate_list_impl(past_sla_only: bool, limit: int)
```

WP-3008: List escalation queue items (blocked runs with SLA).

---

## escalate_resolve_impl

```python
escalate_resolve_impl(run_id: str, resolution: str)
```

WP-3008: Mark an escalation item as resolved.

---

## events_impl

```python
events_impl(run_id: Any, limit: int)
```

List raw telemetry events from the run registry.

---

## explain_run_impl

```python
explain_run_impl(run_id: str)
```

WP-4002: Multi-tier explanation framework for run decisions.

---

## generate_monitor_layout

---

## get_data_protection_status_impl

Return status of data protection and privacy controls (WP-3006).

---

## get_server_meta_impl

Return server metadata dict for thegent://meta resource.

---

## history_impl

```python
history_impl(limit: int)
```

List execution history from the run registry.

---

## inbox_list_impl

```python
inbox_list_impl(owner: Any, agent: Any, event_type: Any, status: Any, sources: tuple[(str, Ellipsis)], limit: int)
```

List unified inbox events (run registry + escalation) with optional filters.

**Parameters**:

- `owner`: Filter by owner
- `agent`: Filter by agent
- `event_type`: Filter by event type (start|finish|feedback|pause|resume|escalation)
- `status`: Filter by status (running|completed|failed)
- `sources`: Tuple of sources to include (registry, escalation)
- `limit`: Max events to return

**Returns**: List of inbox events

---

## inbox_wait_impl

```python
inbox_wait_impl(timeout: Any)
```

Wait for inbox items to become available (WP-1008).

**Parameters**:

- `timeout`: Optional timeout in seconds (default: None, wait indefinitely)

**Returns**: Dictionary with inbox items or timeout status

---

## incorporate_impl

```python
incorporate_impl(cd: Any, dry_run: bool)
```

Merge fragments from 02-UNIFIED-WBS and other docs into WORK_STREAM.md. Preserves CLAIMED and COMPLETED.

Now enhanced with task validation and auto-sync to tasks/ directory (Phase 4).

---

## inspect_impl

```python
inspect_impl(session_ids: list[str], owner: Any, tail: int, stderr: bool, include_contract: bool)
```

Get status and logs for one or more sessions. Returns list of {session_id, status, logs}.

---

## isolation_check_impl

```python
isolation_check_impl(mode: str)
```

Implementation of 'thegent isolation check'.

---

## list_agents_impl

List available agents. Returns list of {name, backend}. name is label (cursor) for display.

---

## list_droids_impl

```python
list_droids_impl(cd: Any)
```

List available droids. Returns list of droid names.

---

## list_models_impl

```python
list_models_impl(provider: Any, use_scraped: bool, refresh: bool, include_contract: bool, by_model: bool)
```

List available models.

By default returns {provider: [model_names]}.
If include_contract=True, returns structured contract metadata for route discovery.
If by_model=True, returns {model_id: [provider, ...]} (R4, R5).

---

## list_session_contracts_impl

```python
list_session_contracts_impl(owner: Any, all: bool, strict: bool)
```

Return sessions with route-request/route-contract metadata and contract quality signal.

---

## lock_resource_impl

```python
lock_resource_impl(resource_path: str, agent_id: str, ttl: int, cd: Any)
```

Claim a lease on a resource (file or directory).

---

## logs_impl

```python
logs_impl(session_id: str, tail: Any, stderr: bool, follow: bool)
```

Get or follow logs from a background session. Returns log text or None if following.

---

## loop_impl

```python
loop_impl(agent: str, prompt: str, todo_spec: str, checker: str, mode: str, cd: Any, on_worker_output: Any, on_progress: Any, max_iterations: int)
```

Run a lifecycle loop with checker oversight.

This is a simplified implementation that runs iterations until completion
or max_iterations is reached.

**Parameters**:

- `agent`: Agent name to use
- `prompt`: Initial prompt for the loop
- `todo_spec`: Task specification for the checker
- `checker`: Checker configuration name
- `mode`: Loop mode (auto, manual, step)
- `cd`: Working directory
- `on_worker_output`: Callback for worker output
- `on_progress`: Callback for progress updates
- `max_iterations`: Maximum iterations before stopping
- `**kwargs`: Additional arguments

**Returns**: Dict with loop results including iterations count

---

## metrics_impl

Gather metrics for the agent registry (WP-9005).

---

## monitor_impl

```python
monitor_impl(interval: float)
```

Monitor sessions and plan progress in real-time (WP-8001).

---

## observe_summary_impl

```python
observe_summary_impl(limit: int, drift_window: int, structural_budget_pct: float, semantic_budget_pct: float, provider: Any, top_escalations: int, trend_samples: Any)
```

FR-X08: Unified observability summary aggregating KPIs, drift, escalation.

---

## plan_analyze_impl

```python
plan_analyze_impl(cd: Any, pert: bool, resources: bool, continuity: bool)
```

Run planning simulation overlays (XD1–XD3): PERT, resource contention, continuity risk.

**Parameters**:

- `cd`: Working directory (default: inferred from cwd)
- `pert`: Run PERT overlay on DAG tasks
- `resources`: Simulate resource contention
- `continuity`: Score continuity risk for handoff

**Returns**: Dictionary with analysis results

---

## prune_sessions_impl

```python
prune_sessions_impl(days: Any)
```

Prune old session data (WP-3006).

---

## ps_impl

```python
ps_impl(owner: Any, all: bool, agent: Any, status: Any, limit: int, scan_ide: bool, include_contract: bool)
```

List agent sessions (managed + discovered) (WP-9006).

**Parameters**:

- `owner`: Filter by owner (default: current user)
- `all`: Show sessions for all owners
- `agent`: Filter by agent name
- `status`: Filter by status (running, completed, failed, paused)
- `limit`: Max sessions to return
- `scan_ide`: Include IDE-managed sessions (Cursor, Claude CLI, Codex)
- `include_contract`: Include route contract metadata

---

## purge_impl

```python
purge_impl(dry_run: bool)
```

WP-3006: Tiered retention purge implementation (G-GP-07).

---

## retry_impl

```python
retry_impl(run_id: str, agent_override: Any, failover: bool, cd: Any, override_reason: Any)
```

Retry a failed run by run_id. Looks up prompt/agent from registry and re-runs.

**Parameters**:

- `run_id`: Run ID to retry
- `agent_override`: Override agent for retry
- `failover`: Use next agent in fallback chain
- `cd`: Working directory
- `override_reason`: Policy override reason

**Returns**: Dictionary with retry result (session_id, status) or error

---

## rules_sync_impl

```python
rules_sync_impl(cd: Any, force: bool, check: bool)
```

Sync rules implementation (WP-9002).

---

## run

```python
run(self: Any, prompt: str, cwd: Any, mode: str, timeout: int) -> RunResult
```

---

## run_impl

```python
run_impl(agent: Any, prompt: str, cd: Any, mode: str, timeout: Any, full: bool, live: bool, model: Any, provider: Any, run_id: Any, owner: Any, include_contract: bool, route_contract: Any, route_request: Any, lane: str, confidence: Any, override_reason: Any, contract_version: Any, domain: Any, idempotency_token: Any, correlation_id: Any, speculative: bool, arbitration: Any, routing: Any, enable_search: bool, debug: bool, task_id: Any, shadow: bool, lock: Any, remote: Any, config_provider: ConfigProvider | None, tenant_id: Any)
```

Run an agent or droid with the given prompt.

Returns dict with keys: stdout, stderr, exit_code, timed_out.
Model-first: agent=None, model set; provider hint for routing.

---

## runner_factory

```python
runner_factory(agent_name: str) -> Any
```

---

## session_contract_audit_impl

```python
session_contract_audit_impl(owner: Any, all: bool, missing_only: bool, summary_only: bool, strict: bool)
```

Return session contract audit rows with optional filtering and summary.

---

## session_contract_health_gate_impl

```python
session_contract_health_gate_impl(owner: Any, all: bool, strict: bool, min_healthy_ratio: float, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float)
```

Evaluate routing contract health against a minimum healthy-ratio gate.

---

## session_contract_health_report_impl

```python
session_contract_health_report_impl(owner: Any, all: bool, strict: bool, top_blocked: int, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float)
```

Return health report with issue taxonomy and owner-level breakdown.

---

## session_contract_health_trend_impl

```python
session_contract_health_trend_impl(payload_type: str, owner: Any, all: bool, strict: bool, policy_profile: Any, min_healthy_ratio: float, top_blocked: int, limit: int)
```

Return recent health snapshots and deltas for a given policy/query scope.

---

## session_contract_negotiate_impl

```python
session_contract_negotiate_impl(contract_id: str, supported_versions: list[str])
```

WP-7001: Implementation of contract negotiation logic.

---

## session_meta_impl

```python
session_meta_impl(session_id: str)
```

Get full session metadata. Returns meta dict or error.

---

## session_send_impl

```python
session_send_impl(session_id: str, message: str, msg_type: str)
```

Send a message to a running session by queuing it in the registry (WP-9004).

---

## sitback_dashboard_impl

```python
sitback_dashboard_impl(profile: str)
```

Unified sitback dashboard: sessions, cockpit (circuits, drift, budget), terminals.

For FastMCP tool/resource: single call replaces cockpit + terminal list + ps.
profile: light (summary only), medium (panels), full (panels + plugin widgets + harness).

---

## spawn_next_impl

```python
spawn_next_impl(cd: Any, limit: int, agent: str, timeout: Any, lane: str, override_reason: str, claim: bool)
```

Spawn N next work items in background (parallel batch).

Gets up to `limit` items from do_next_impl, claims each, then spawns bg_impl.
Uses lane=critical and override_reason to avoid load-based deferral.
Designed for 10-20 items in addition to other agent managers (5-20 each).

**Parameters**:

- `cd`: Working directory
- `limit`: Max items to spawn (default 10, max 20)
- `agent`: Agent for bg runs (default: free)
- `timeout`: Per-run timeout in seconds (default: from config, 600 for 10m)
- `lane`: Lane for runs (default: critical to avoid deferral)
- `override_reason`: Override reason for load bypass (default: manual-next-step)
- `claim`: Whether to claim items before spawning (default: True)

**Returns**: dict with: spawned (list of {item_id, session_id}), errors (list), count

---

## status_impl

```python
status_impl(session_id: str, include_contract: bool)
```

Get status of a background session.

---

## stop_impl

```python
stop_impl(session_id: str, force: bool)
```

Stop a background session.

---

## sweep_impl

```python
sweep_impl(drift_window: int, structural_budget: float, semantic_budget: float, include_audit: bool)
```

WP-3005: Policy drift sweep - runs drift detection, budget check, past-SLA escalations.

---

## unlock_resource_impl

```python
unlock_resource_impl(resource_path: str, agent_id: str, token: str, cd: Any)
```

Release a lease on a resource.

---

## update_calibration_impl

G-GP-09: Recalculate and persist calibration factors for all agents.

---

## verify_context_impl

```python
verify_context_impl(files: list[str], cd: Any)
```

Verify if any of the given files have been modified (OCC check).

---

## wait_impl

```python
wait_impl(session_id: str, timeout: Any)
```

Wait for a background session to complete.

---

## wait_next_impl

```python
wait_next_impl(cd: Any, poll_interval: float, timeout: float, sources: tuple[(str, Ellipsis)])
```

Block until next actionable work exists, polling at intervals.

**Parameters**:

- `cd`: Optional working directory
- `poll_interval`: Seconds between polls (default: 2.0)
- `timeout`: Max seconds to wait (0 = no timeout, default: 0.0)
- `sources`: Tuple of source names to check (default: ("do_next",))

**Returns**: dict with:

- action: dict with {id, description, source, prompt_suggestion} or None if timeout
- elapsed_s: seconds elapsed
- poll_count: number of polls performed

---

## work_stream_claim_impl

```python
work_stream_claim_impl(item_id: str, agent_id: str, cd: Any)
```

Claim a work item (move from BACKLOG to CLAIMED in WORK_STREAM.md).

---

## work_stream_complete_impl

```python
work_stream_complete_impl(item_id: str, agent_id: str, cd: Any)
```

Complete a work item (move from CLAIMED to COMPLETED in WORK_STREAM.md).

---

## wrapped_run

---
