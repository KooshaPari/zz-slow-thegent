# mcp_server API Reference

> **Source**: `src/thegent/mcp_server.py`

FastMCP server for thegent.

---

## BearerAuthMiddleware

G-FM-01: Bearer token authentication for MCP HTTP endpoints.

**Inherits from**: `BaseHTTPMiddleware`

---

## add_api_key

```python
add_api_key(provider: str, api_key: str)
```

Add or update API key for a provider.

---

## add_model_alias

```python
add_model_alias(provider: str, model: str, alias: str)
```

Add a model alias for a provider.

---

## add_provider

```python
add_provider(name: str, base_url: str, model: str, api_key: Any, extra_aliases: Any, login_url: Any)
```

Add a new provider configuration.

---

## delete_provider

```python
delete_provider(name: str, remove_credentials: bool)
```

Delete a provider configuration.

---

## discover_models

```python
discover_models(provider: Any)
```

Discover available models from provider APIs.

---

## get_default_cwd

```python
get_default_cwd(ctx: Context)
```

Inject cwd from request meta (meta.cwd). Client can send meta.cwd in request.

---

## get_default_owner

```python
get_default_owner(ctx: Context)
```

Inject owner from request meta (meta.owner). Client can send meta.owner in request.

---

## get_provider

```python
get_provider(name: str)
```

Get a specific provider configuration.

---

## http_app

```python
http_app(stateless_http: bool)
```

Return ASGI app with EventStore (mountable in FastAPI/Starlette).

stateless_http=True allows per-request JSON-RPC without SSE session (for simple clients, CI, verification).

---

## list_credentials

List all configured credentials (API keys and OAuth).

---

## list_models

```python
list_models(provider: Any)
```

List all models, optionally filtered by provider.

---

## list_providers

```python
list_providers(include_credentials: bool)
```

List all configured providers with their settings.

---

## remove_api_key

```python
remove_api_key(provider: str)
```

Remove API key for a provider.

---

## remove_model_alias

```python
remove_model_alias(provider: str, alias: str)
```

Remove a model alias from a provider.

---

## resource_agents

List available agents. Returns JSON array of {name, backend}.

---

## resource_dag

Get DAG from .factory/dag-session.md as {frontmatter, tasks} JSON.

---

## resource_events_session_complete

Event stream for session completion events (for auto-launch system).

---

## resource_meta

Server metadata: version, capabilities, health payload schema.

---

## resource_models

```python
resource_models(provider: Any, include_contract: bool)
```

List models, optionally filtered by provider.

---

## resource_models_contract

Return model routing contract schema metadata.

---

## resource_modes

```python
resource_modes(mode: Any)
```

Multi-agent orchestration modes: sequential_delegation, parallel_consensus, review_loop.

---

## resource_observe_summary

```python
resource_observe_summary(limit: int, drift_window: int, structural_budget_pct: float, semantic_budget_pct: float, provider: Any, trend_samples: int, top_escalations: int)
```

Observe summary payload for contract KPIs, drift status, and escalation backlog.

---

## resource_operations

```python
resource_operations(operation: Any)
```

Universal operation taxonomy: orchestrate, govern, recover, observe, plan.

---

## resource_session_contract_health_gate

```python
resource_session_contract_health_gate(owner: Any, all: bool, strict: bool, min_healthy_ratio: float, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float)
```

Contract health gate for CI/automation and policy enforcement.

Returns schema-aware payload with `schema_version` and `payload_type`.

---

## resource_session_contract_health_report

```python
resource_session_contract_health_report(owner: Any, all: bool, strict: bool, top_blocked: int, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float)
```

Contract health report for issue/owner triage and observability.

Returns schema-aware payload with `schema_version` and `payload_type`.

---

## resource_session_contract_health_trend

```python
resource_session_contract_health_trend(payload_type: str, owner: Any, all: bool, strict: bool, policy_profile: Any, min_healthy_ratio: float, top_blocked: int, limit: int)
```

Contract health trend snapshots for a scoped report/gate policy context.

---

## resource_session_contracts

```python
resource_session_contracts(owner: Any, all: bool, missing_only: bool, summary_only: bool, strict: bool)
```

Contract audit for sessions including completeness summary.

---

## resource_session_logs

```python
resource_session_logs(id: str, stderr: bool, tail: Any)
```

Get logs from a background session. Use ?stderr=true for stderr, ?tail=N for last N lines.

---

## resource_session_meta

```python
resource_session_meta(id: str, include_contract: bool)
```

Get session metadata (status, pid, owner) by ID.

---

## resource_sessions

```python
resource_sessions(include_contract: bool)
```

List all background sessions. Returns JSON array of session metadata.

---

## resource_workflow_gardening

Gardening workflow: converge to empty backlog and complete green.

---

## resource_workflow_triggers

Workflow instructions: idea→research→spec, quality green, next item. Injected on UserPromptSubmit.

---

## resource_workstream

Get the canonical WORK_STREAM.md content.

---

## resource_workstream_db

Workstream database metadata and schema info.

---

## run

```python
run(host: Any, port: Any)
```

Start the FastMCP server with EventStore and optional Docket.

---

## thegent_bg_task

```python
thegent_bg_task(agent: str, prompt: str, owner: Any)
```

Generate a prompt to start an agent task in the background.

Use thegent_bg tool to execute.

---

## thegent_config_resolve

```python
thegent_config_resolve(tenant_id: Any, session_id: Any, request_overrides: Any, keys: Any)
```

WP-1010: Resolve configuration for a given tenant/session context from the control plane.

Falls back to environment settings if control plane is unavailable.

**Parameters**:

- `tenant_id`: Optional tenant ID for context-aware config
- `session_id`: Optional session ID
- `request_overrides`: Optional dict of keys to override
- `keys`: Optional list of specific keys to resolve (resolves all if missing)

---

## thegent_continuity_snapshot

```python
thegent_continuity_snapshot(owner: str, run_ids: list[str], state_summary: Any, next_steps: Any)
```

WP-1009: Create a continuity snapshot for shift handoff.

**Parameters**:

- `owner`: Current owner
- `run_ids`: Run IDs to include in snapshot
- `state_summary`: Optional state summary dict
- `next_steps`: Optional list of next steps

---

## thegent_create_wbs

```python
thegent_create_wbs(feature: str, scope: Any)
```

Generate a prompt to create a Work Breakdown Structure (WBS) for a feature.

Use thegent_run with a planning agent (e.g. cursor, claude) to execute.

---

## thegent_dag_status

```python
thegent_dag_status(cd: Any)
```

For each DAG task with session_id, return id, status, session_id, session_status.

Equivalent to: thegent dag status

---

## thegent_ddg_search

```python
thegent_ddg_search(query: str, num_results: int)
```

Search DuckDuckGo for heavy web research.

**Parameters**:

- `query`: Search query string
- `num_results`: Max results to return (min: 1, max: 20, default: 5)

---

## thegent_deep_research

```python
thegent_deep_research(query: str, subreddits: Any)
```

Perform deep research using the Deep Research Protocol (DRP).

Bypasses blocks by using custom headers and direct API calls.

**Parameters**:

- `query`: Search query string
- `subreddits`: Comma-separated list of subreddits to prioritize

---

## thegent_do_next

```python
thegent_do_next(cd: Any, limit: int)
```

Find the next actionable work items from PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

Use when user says "what next", "find the next thing to do", "pick next task".
Returns next_items with id, description, source, prompt_suggestion. Use prompt_suggestion with thegent_run or thegent_bg to execute.

**Parameters**:

- `cd`: Optional working directory (default: cwd)
- `limit`: Max items to return (min: 1, max: 50, default: 5)

---

## thegent_escalate_add

```python
thegent_escalate_add(run_id: str, reason: str, sla_minutes: int, owner: Any, agent: Any, lane: str, priority: int)
```

Add a blocked run to the escalation queue. Equivalent to: thegent govern escalate add

---

## thegent_escalate_approve

```python
thegent_escalate_approve(run_id: str)
```

Approve an escalation (policy override). Equivalent to: thegent govern escalate approve

---

## thegent_escalate_list

```python
thegent_escalate_list(past_sla_only: bool, limit: int)
```

List escalation queue items (blocked runs). Equivalent to: thegent govern escalate list

---

## thegent_escalate_resolve

```python
thegent_escalate_resolve(run_id: str, resolution: str)
```

Mark an escalation item as resolved. Equivalent to: thegent govern escalate resolve

---

## thegent_handoff

```python
thegent_handoff(owner: str, cd: Any)
```

Create a handoff snapshot for shift handoff (WP-4006). Transfers active runs to snapshot.

Equivalent to: thegent orchestrate handoff `<owner>`

---

## thegent_handoff_confirm

```python
thegent_handoff_confirm(snapshot_id: str, incoming_owner: str, confidence: float)
```

Incoming owner confirms handoff completeness. Equivalent to: thegent orchestrate handoff-confirm

---

## thegent_handoff_list

```python
thegent_handoff_list(limit: int)
```

List pending handoff snapshots. Equivalent to: thegent orchestrate handoff-list

---

## thegent_handoff_show

```python
thegent_handoff_show(snapshot_id: str)
```

Show full handoff summary for a snapshot. Equivalent to: thegent orchestrate handoff-show

---

## thegent_heliosShield_status

Get status from heliosShield harness.

---

## thegent_history

```python
thegent_history(limit: int)
```

List execution history (recent runs). Equivalent to: thegent history --limit N

---

## thegent_inbox_list

```python
thegent_inbox_list(owner: Any, agent: Any, event_type: Any, status: Any, sources: Any, limit: int)
```

List unified inbox events (run registry + escalation) with optional filters.

**Parameters**:

- `owner`: Filter by owner
- `agent`: Filter by agent
- `event_type`: start|finish|feedback|pause|resume|escalation
- `status`: running|completed|failed
- `sources`: Comma-separated: registry,escalation (default: registry,escalation)
- `limit`: Max events to return (default: 50)

---

## thegent_inbox_wait

```python
thegent_inbox_wait(owner: Any, agent: Any, event_type: Any, status: Any, sources: Any, poll_interval: float, timeout: float)
```

Wait for next inbox event matching filters. Blocks until new event or timeout.

Auto-times out every 2 minutes to prevent Cursor timeout (4min guard).
Returns instruction to retry without terminating chat.

**Parameters**:

- `owner`: Filter by owner
- `agent`: Filter by agent
- `event_type`: start|finish|feedback|pause|resume|escalation
- `status`: running|completed|failed
- `sources`: Comma-separated: registry,escalation (default: registry,escalation)
- `poll_interval`: Poll interval in seconds (default: 2.0)
- `timeout`: Max wait seconds (default: 60, 0=unbounded)

---

## thegent_inspect

```python
thegent_inspect(session_ids: Any, owner: Any, tail: int, stderr: bool, include_contract: bool)
```

Multi-session status + logs.

**Parameters**:

- `session_ids`: Session ID(s) to inspect. Omit when using owner.
- `owner`: Inspect all sessions for this owner (alternative to session_ids)
- `tail`: Log lines per session (default: 50)
- `stderr`: Show stderr instead of stdout (default: False)

---

## thegent_list_agents

List available agents for routing.

Returns: JSON string with list of {name, backend}

---

## thegent_list_droids

```python
thegent_list_droids(cd: Any, default_cwd: Any)
```

List available droids.

**Parameters**:

- `cd`: Optional working directory (or use meta.cwd in request)
- `Returns`: JSON string with list of droid names

---

## thegent_list_models

```python
thegent_list_models(provider: Any, include_contract: bool, by_model: bool)
```

List available models (optionally filtered by provider).

**Parameters**:

- `provider`: Optional provider filter (minimax, glm, cursor, claude, codex; gemini/copilot via Codex proxy)
- `include_contract`: If true, return route metadata payload instead of provider/model map.
- `by_model`: If true, return {model_id: [provider, ...]} for routing (R5).

---

## thegent_list_modes

```python
thegent_list_modes(mode: Any)
```

List multi-agent orchestration modes (G-KD-04).

**Parameters**:

- `mode`: Optional filter (sequential_delegation | parallel_consensus | review_loop)

---

## thegent_list_operations

```python
thegent_list_operations(operation: Any)
```

List universal operation taxonomy: orchestrate, govern, recover, observe, plan.

**Parameters**:

- `operation`: Optional filter (orchestrate | govern | recover | observe | plan)

---

## thegent_lock_resource

```python
thegent_lock_resource(resource: str, ttl: int, cd: Any)
```

Acquire an exclusive lock on a resource (file or directory).

Returns a token that MUST be used with thegent_unlock_resource.
Use for non-worktree multi-tenancy coordination.

---

## thegent_logs

```python
thegent_logs(session_id: str, tail: Any, stderr: bool)
```

Read session log output with optional tail limit.

**Parameters**:

- `session_id`: Session ID to query
- `tail`: Number of lines to return from end (optional, default: all)
- `stderr`: Include stderr instead of stdout (default: False)

---

## thegent_observe_summary

```python
thegent_observe_summary(limit: int, drift_window: int, structural_budget_pct: float, semantic_budget_pct: float, provider: Any, trend_samples: int, top_escalations: int)
```

Get unified observability summary for KPIs, drift budget, and escalations.

---

## thegent_pause

```python
thegent_pause(session_id: str, reason: str)
```

WP-1009: Pause a background session (register pause event in registry).

**Parameters**:

- `session_id`: Session ID to pause
- `reason`: Reason for pause (default: Manual pause)

---

## thegent_plan_analyze

```python
thegent_plan_analyze(cd: Any, pert: bool, resources: bool, continuity: bool)
```

Run planning simulation overlays (XD1–XD3): PERT, resource contention, continuity risk.

Equivalent to: thegent plan analyze
If no flags set, runs all three overlays.

---

## thegent_plan_get_next

```python
thegent_plan_get_next(cd: Any)
```

Get first work item prompt for scripting. Use with thegent_run or thegent_bg.

Equivalent to: thegent plan get-next

---

## thegent_plan_incorporate

```python
thegent_plan_incorporate(cd: Any, dry_run: bool)
```

Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md BACKLOG.

Equivalent to: thegent plan incorporate

---

## thegent_plan_progress

```python
thegent_plan_progress(limit: int)
```

Show recent runs (work-package progress). Alias for thegent_history with smaller default.

Equivalent to: thegent plan progress --limit N

---

## thegent_plan_wait_next

```python
thegent_plan_wait_next(cd: Any, poll: float, timeout: float, sources: str)
```

Block until next actionable work exists (DAG ready, do_next, escalation, inbox).

Equivalent to: thegent plan wait-next

---

## thegent_ps

```python
thegent_ps(owner: Any, all: bool, include_contract: bool)
```

List background sessions for discovery.

**Parameters**:

- `owner`: Filter by owner tag (optional)
- `all`: Include completed/stopped sessions (default: False)
- `include_contract`: Include resolved route contract/request metadata (optional)

---

## thegent_queue_add

```python
thegent_queue_add(prompt: str, project: str, agent: Any)
```

Add a prompt to the queue (deferred execution). Equivalent to $defer in prompt.

---

## thegent_queue_claim

```python
thegent_queue_claim(claimer_id: str, project: Any, lease_seconds: int)
```

Atomically claim the first pending queue item. Returns claimed item with id, or null if queue empty.

Use project to filter by project path.

---

## thegent_queue_done

```python
thegent_queue_done(item_id: int)
```

Mark a queue item as done by id. Use id from thegent_queue_list or thegent_queue_claim.

---

## thegent_queue_edit

```python
thegent_queue_edit(item_id: int, prompt: str)
```

Edit prompt for a pending or claimed queue item. Cannot edit done items.

---

## thegent_queue_extend_lease

```python
thegent_queue_extend_lease(item_id: int, lease_seconds: int)
```

Extend lease for a claimed queue item. Use before lease expires.

---

## thegent_queue_list

```python
thegent_queue_list(include_done: bool, include_expired: bool, limit: Any)
```

List prompt queue items (deferred prompts). Use include_done=True to see completed items.

Returns items with id for claim/done/release/extend_lease/edit.

---

## thegent_queue_release

```python
thegent_queue_release(item_id: int)
```

Release a claimed queue item back to pending. Use when worker cannot complete.

---

## thegent_reddit_search

```python
thegent_reddit_search(query: str, num_results: int)
```

Search Reddit for discussions and community insights.

Uses Reddit API (if configured) or site-specific search.

**Parameters**:

- `query`: Search query string
- `num_results`: Max results to return (min: 1, max: 20, default: 5)

---

## thegent_resolve_model_route

```python
thegent_resolve_model_route(model: str, provider: Any, policy: str)
```

Resolve a model to a concrete routing target.

**Parameters**:

- `model`: Model identifier (alias or canonical)
- `provider`: Optional provider hint
- `policy`: Routing policy: prefer_direct, prefer_proxy, failover

---

## thegent_resume

```python
thegent_resume(session_id: str)
```

WP-1009: Resume a paused session (register resume event in registry).

**Parameters**:

- `session_id`: Session ID to resume

---

## thegent_retry

```python
thegent_retry(run_id: str, agent_override: Any, failover: bool, cd: Any, override_reason: Any)
```

Retry a failed run by run_id. Looks up prompt/agent from registry and re-runs.

Equivalent to: thegent retry `<run_id>`

---

## thegent_run_agent

```python
thegent_run_agent(agent: str, prompt: str, cd: Any, mode: str)
```

Generate a prompt to run an agent synchronously.

Use thegent_run tool to execute.

---

## thegent_session_contract_health_gate

```python
thegent_session_contract_health_gate(owner: Any, all: bool, strict: bool, min_healthy_ratio: float, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float)
```

Evaluate session contract health against a minimum ratio gate.

Returns a unified health payload with `schema_version`, `payload_type`,
`pass`, `status`, `total_sessions`, `healthy_sessions`, `unhealthy_sessions`,
`blocked_sessions_count`, `blocked_ratio`, and `blocked_sessions`.

---

## thegent_session_contract_health_report

```python
thegent_session_contract_health_report(owner: Any, all: bool, strict: bool, top_blocked: int, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float)
```

Get contract health report with issue taxonomy and owner-level breakdown.

Returns a unified health payload with `schema_version`, `payload_type`,
`status`, `total_sessions`, `healthy_sessions`, `unhealthy_sessions`,
`blocked_sessions_count`, `blocked_ratio`, `issue_breakdown`, and `owner_breakdown`.

---

## thegent_session_contract_health_trend

```python
thegent_session_contract_health_trend(payload_type: str, owner: Any, all: bool, strict: bool, policy_profile: Any, min_healthy_ratio: float, top_blocked: int, limit: int)
```

Get trend snapshots and deltas for session contract health scopes.

---

## thegent_session_contracts

```python
thegent_session_contracts(owner: Any, all: bool, missing_only: bool, summary_only: bool, strict: bool)
```

List session routing contract metadata and report completeness.

---

## thegent_status

```python
thegent_status(session_id: str, include_contract: bool)
```

Get session status for quick health check.

**Parameters**:

- `session_id`: Session ID to query

---

## thegent_stop

```python
thegent_stop(session_id: str, force: bool)
```

Stop a background session.

**Parameters**:

- `session_id`: Session ID to stop
- `force`: Use SIGKILL instead of SIGTERM (default: False)

---

## thegent_suggest_mode

```python
thegent_suggest_mode(risk: str, urgency: str, confidence: float)
```

WP-Y1: Suggest multi-agent mode based on risk, urgency, confidence (FR-032).

**Parameters**:

- `risk`: risk_profile (low | medium | high)
- `urgency`: urgency tier (normal | high | critical)
- `confidence`: confidence score 0.0-1.0

---

## thegent_terminal_attach

```python
thegent_terminal_attach(pane_id: str)
```

Get instructions to attach to a terminal session.

---

## thegent_terminal_inspect

```python
thegent_terminal_inspect(pane_id: str, last_lines: int)
```

Capture the content of a terminal pane.

---

## thegent_terminal_list

```python
thegent_terminal_list(all: bool)
```

List active terminal panes (tmux).

**Parameters**:

- `all`: Show all panes, not just Claude Code (default: False)

---

## thegent_terminal_route

```python
thegent_terminal_route(prompt: str, cd: Any)
```

Route a prompt to an active terminal session if matching. Falls back to thegent_run if none found.

Equivalent to: thegent route `<prompt>`

---

## thegent_terminal_send

```python
thegent_terminal_send(pane_id: str, text: str, enter: bool)
```

Send text/keys to a terminal pane.

---

## thegent_unlock_resource

```python
thegent_unlock_resource(resource: str, token: str, cd: Any)
```

Release an exclusive lock on a resource using the token from thegent_lock_resource.

---

## thegent_verify_context

```python
thegent_verify_context(files: list[str], cd: Any)
```

Verify if any of the given files have been modified (OCC check).

Returns current versions (hashes) of files for stale-state detection.

---

## thegent_wait

```python
thegent_wait(session_id: str, timeout: Any)
```

Block until session completes or timeout.

Auto-times out every 2 minutes to prevent Cursor timeout (4min guard).
Returns instruction to retry without terminating chat.

**Parameters**:

- `session_id`: Session ID to wait for
- `timeout`: Timeout in seconds (optional)

---

## thegent_workflow_gardening

Instructions for gardening: check gov traceability, tests, plan items; dispatch; converge to empty backlog and complete green.

Use when user says "garden", "converge", "empty backlog", "complete green".

---

## thegent_workflow_idea

```python
thegent_workflow_idea(idea: str)
```

Instructions for idea/task prompts: dump research, create specs, add work items.

Use when user gives research/explore/build/implement/design/create/feature prompts.

---

## thegent_workflow_next_item

Instructions to find and execute the next work item from the unified stream.

Use when user says "find the next thing to do", "what next", "pick next".

---

## thegent_workflow_quality_green

Instructions to run full quality pipeline until green.

Use when user says "get task quality green", "quality green", "make quality pass".

---

## thegent_workstream_claim

```python
thegent_workstream_claim(item_id: str, agent_id: str)
```

Claim an item in the unified work stream.

---

## thegent_workstream_complete

```python
thegent_workstream_complete(item_id: str, agent_id: str)
```

Mark an item as complete in the unified work stream.

---

## thegent_workstream_query

```python
thegent_workstream_query(query: str)
```

Execute SQL query on workstream database.

Returns query results as JSON. Use for exploring session/workstream data.
Example: "SELECT \* FROM sessions WHERE status='running' LIMIT 10"

---

## thegent_workstream_stats

Get workstream statistics.

Returns statistics including running/completed counts, success rate,
average duration, deferred tasks, and lane breakdown.

---

## update_provider

```python
update_provider(name: str, base_url: Any, model: Any, api_key: Any, extra_aliases: Any)
```

Update an existing provider configuration.

---

## validate_provider

```python
validate_provider(name: str)
```

Validate a provider by testing connectivity and credentials.

---
