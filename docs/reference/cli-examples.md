# CLI Examples

Interactive examples of thegent CLI commands.

---

## `thegent archive`

Archive old sessions (WP-6005). WP-3006: tiered retention (hot 30d, cold 1yr).

<details>
<summary>Full documentation</summary>

Archive old sessions (WP-6005). WP-3006: tiered retention (hot 30d, cold 1yr).

</details>

<CodePlayground lang='bash' code='thegent archive --days VALUE --domain VALUE --tier VALUE' />

---

## `thegent audit-verify`

Verify the integrity of the execution run registry.

<details>
<summary>Full documentation</summary>

Verify the integrity of the execution run registry.

</details>

<CodePlayground lang='bash' code='thegent audit-verify --format VALUE' />

---

## `thegent benchmark`

Report orchestration performance metrics (WP-6001).

<details>
<summary>Full documentation</summary>

Report orchestration performance metrics (WP-6001).

</details>

<CodePlayground lang='bash' code='thegent benchmark' />

---

## `thegent run`

<CodePlayground lang='bash' code='thegent run agent "Analyze repository docs" --agent codex --bg' />

---

## `thegent cliproxy-login`

Run login for provider. Unified flow: open URL + prompt for API key. Preflight checks existing credentials.

<details>
<summary>Full documentation</summary>

Run login for provider. Unified flow: open URL + prompt for API key. Preflight checks existing credentials.

</details>

<CodePlayground lang='bash' code='thegent cliproxy-login --provider VALUE --force VALUE' />

---

## `thegent closure-pack`

Generate a formal closure pack for the current DAG session (WP-6002/6008/FR-024).

<details>
<summary>Full documentation</summary>

Generate a formal closure pack for the current DAG session (WP-6002/6008/FR-024).

</details>

<CodePlayground lang='bash' code='thegent closure-pack --cd VALUE' />

---

## `thegent cockpit`

Show high-level operator cockpit summary.

<details>
<summary>Full documentation</summary>

Show high-level operator cockpit summary.

</details>

<CodePlayground lang='bash' code='thegent cockpit' />

---

## `thegent compliance-plugin-check`

Verify a plugin contract (WP-15003).

<details>
<summary>Full documentation</summary>

Verify a plugin contract (WP-15003).

</details>

<CodePlayground lang='bash' code='thegent compliance-plugin-check --plugin-id VALUE --signature VALUE' />

---

## `thegent compliance-redact`

Test PII/Secret redaction (WP-15005).

<details>
<summary>Full documentation</summary>

Test PII/Secret redaction (WP-15005).

</details>

<CodePlayground lang='bash' code='thegent compliance-redact --text VALUE' />

---

## `thegent compliance-report`

Generate compliance evidence retention report (WP-3006).

<details>
<summary>Full documentation</summary>

Generate compliance evidence retention report (WP-3006).

</details>

<CodePlayground lang='bash' code='thegent compliance-report --format VALUE --output VALUE' />

---

## `thegent compliance-siem-test`

Test SIEM event egress (WP-15001).

<details>
<summary>Full documentation</summary>

Test SIEM event egress (WP-15001).

</details>

<CodePlayground lang='bash' code='thegent compliance-siem-test --message VALUE --severity VALUE' />

---

## `thegent concurrency-set`

Set concurrency limit (updates .env file).

<details>
<summary>Full documentation</summary>

Set concurrency limit (updates .env file).

</details>

<CodePlayground lang='bash' code='thegent concurrency-set --limit VALUE' />

---

## `thegent concurrency-show`

Show current concurrency limit and utilization (WP-5001).

<details>
<summary>Full documentation</summary>

Show current concurrency limit and utilization (WP-5001).

</details>

<CodePlayground lang='bash' code='thegent concurrency-show --format VALUE' />

---

## `thegent config-check`

Validate config and report issues (DX-010, ROB-013).

<details>
<summary>Full documentation</summary>

Validate config and report issues (DX-010, ROB-013).

</details>

<CodePlayground lang='bash' code='thegent config-check --format VALUE' />

---

## `thegent contracts-conformance`

Run provider adapter conformance tests.

<details>
<summary>Full documentation</summary>

Run provider adapter conformance tests.

</details>

<CodePlayground lang='bash' code='thegent contracts-conformance --format VALUE --check-drift VALUE --drift-window VALUE' />

---

## `thegent contracts-registry`

Show the contract registry and compatibility matrix.

<details>
<summary>Full documentation</summary>

Show the contract registry and compatibility matrix.

</details>

<CodePlayground lang='bash' code='thegent contracts-registry --format VALUE' />

---

## `thegent cost-status`

Show cost budget utilization and cost-aware routing status (WP-5003).

<details>
<summary>Full documentation</summary>

Show cost budget utilization and cost-aware routing status (WP-5003).

</details>

<CodePlayground lang='bash' code='thegent cost-status --format VALUE' />

---

## `thegent cost-values`

Show cost values ($/1k tokens) for all model-provider pairs.

<details>
<summary>Full documentation</summary>

Show cost values ($/1k tokens) for all model-provider pairs.

Uses CLIProxyAPIPlus metrics when reachable; falls back to static values.

</details>

<CodePlayground lang='bash' code='thegent cost-values --format VALUE' />

---

## `thegent dag-add`

Add a task to the DAG. XA4: contract_version in task metadata.

<details>
<summary>Full documentation</summary>

Add a task to the DAG. XA4: contract_version in task metadata.

</details>

<CodePlayground lang='bash' code='thegent dag-add --task-id VALUE --agent VALUE --prompt VALUE ...' />

---

## `thegent dag-cancel`

Cancel a task (set status to cancelled).

<details>
<summary>Full documentation</summary>

Cancel a task (set status to cancelled).

</details>

<CodePlayground lang='bash' code='thegent dag-cancel --task-id VALUE --cd VALUE' />

---

## `thegent dag-checkpoint`

Create a point-in-time checkpoint of the DAG state.

<details>
<summary>Full documentation</summary>

Create a point-in-time checkpoint of the DAG state.

</details>

<CodePlayground lang='bash' code='thegent dag-checkpoint --cd VALUE --reason VALUE' />

---

## `thegent dag-checkpoints`

List recent DAG checkpoints.

<details>
<summary>Full documentation</summary>

List recent DAG checkpoints.

</details>

<CodePlayground lang='bash' code='thegent dag-checkpoints --limit VALUE' />

---

## `thegent dag-list`

Parse and display DAG session from .factory/dag-session.md.

<details>
<summary>Full documentation</summary>

Parse and display DAG session from .factory/dag-session.md.

</details>

<CodePlayground lang='bash' code='thegent dag-list --cd VALUE --format VALUE' />

---

## `thegent dag-probe`

Compare current DAG state with a baseline checkpoint to detect regressions.

<details>
<summary>Full documentation</summary>

Compare current DAG state with a baseline checkpoint to detect regressions.

</details>

<CodePlayground lang='bash' code='thegent dag-probe --cd VALUE --baseline-id VALUE' />

---

## `thegent dag-ready`

List task ids that are ready (pending with all deps done|cancelled|skipped).

<details>
<summary>Full documentation</summary>

List task ids that are ready (pending with all deps done|cancelled|skipped).

</details>

<CodePlayground lang='bash' code='thegent dag-ready --cd VALUE --format VALUE' />

---

## `thegent dag-reconcile`

Reconcile DAG state with reality (clean up stuck 'running' tasks).

<details>
<summary>Full documentation</summary>

Reconcile DAG state with reality (clean up stuck 'running' tasks).

</details>

<CodePlayground lang='bash' code='thegent dag-reconcile --cd VALUE' />

---

## `thegent dag-recover`

Perform recovery playbook actions on the DAG.

<details>
<summary>Full documentation</summary>

Perform recovery playbook actions on the DAG.

</details>

<CodePlayground lang='bash' code='thegent dag-recover --cd VALUE --action VALUE' />

---

## `thegent dag-remove`

Remove a task from the DAG.

<details>
<summary>Full documentation</summary>

Remove a task from the DAG.

</details>

<CodePlayground lang='bash' code='thegent dag-remove --task-id VALUE --cd VALUE' />

---

## `thegent dag-rollback`

Rollback DAG state to a specific checkpoint.

<details>
<summary>Full documentation</summary>

Rollback DAG state to a specific checkpoint.

</details>

<CodePlayground lang='bash' code='thegent dag-rollback --checkpoint-id VALUE --cd VALUE' />

---

## `thegent dag-run`

Spawn background `thegent run agent` tasks for each ready task; update status=running and session_id.

<details>
<summary>Full documentation</summary>

Spawn background `thegent run agent` tasks for each ready task; update status=running and session_id.

</details>

<CodePlayground lang='bash' code='thegent dag-run --cd VALUE --dry-run VALUE --task VALUE ...' />

---

## `thegent dag-status`

For each task with session_id show id, status, session_id, session_status (running/exited:rc).

<details>
<summary>Full documentation</summary>

For each task with session_id show id, status, session_id, session_status (running/exited:rc).

</details>

<CodePlayground lang='bash' code='thegent dag-status --cd VALUE --format VALUE' />

---

## `thegent dag-sync`

For tasks with session_id and status=running, if pid not running set status=done or failed from rc.

<details>
<summary>Full documentation</summary>

For tasks with session_id and status=running, if pid not running set status=done or failed from rc.
If --auto-run-next, spawn next ready tasks after sync.

</details>

<CodePlayground lang='bash' code='thegent dag-sync --cd VALUE --auto-run-next VALUE' />

---

## `thegent dag-update`

Update a task in the DAG. XA4: contract_version in task metadata.

<details>
<summary>Full documentation</summary>

Update a task in the DAG. XA4: contract_version in task metadata.

</details>

<CodePlayground lang='bash' code='thegent dag-update --task-id VALUE --cd VALUE --status VALUE ...' />

---

## `thegent dag-validate`

Validate DAG session from .factory/dag-session.md. Exit 2 on validation errors.

<details>
<summary>Full documentation</summary>

Validate DAG session from .factory/dag-session.md. Exit 2 on validation errors.

</details>

<CodePlayground lang='bash' code='thegent dag-validate --cd VALUE' />

---

## `thegent data-protection`

Show status of data protection and privacy controls.

<details>
<summary>Full documentation</summary>

Show status of data protection and privacy controls.

</details>

<CodePlayground lang='bash' code='thegent data-protection --format VALUE' />

---

## `thegent deep-research`

Perform deep research using the Deep Research Protocol (DRP).

<details>
<summary>Full documentation</summary>

Perform deep research using the Deep Research Protocol (DRP).

</details>

<CodePlayground lang='bash' code='thegent deep-research --query VALUE --subreddits VALUE --output VALUE' />

---

## `thegent deferral-list`

List all currently deferred tasks (WP-5004).

<details>
<summary>Full documentation</summary>

List all currently deferred tasks (WP-5004).

</details>

<CodePlayground lang='bash' code='thegent deferral-list' />

---

## `thegent deferral-resume`

Manually resume a deferred task (WP-5004).

<details>
<summary>Full documentation</summary>

Manually resume a deferred task (WP-5004).

</details>

<CodePlayground lang='bash' code='thegent deferral-resume --run-id VALUE' />

---

## `thegent discovery-parse`

Parse CLI output for session information and register them.

<details>
<summary>Full documentation</summary>

Parse CLI output for session information and register them.

</details>

<CodePlayground lang='bash' code='thegent discovery-parse --text VALUE --register VALUE --ppid VALUE' />

---

## `thegent discovery-register`

Register or update a discovered external agent (WP-4008).

<details>
<summary>Full documentation</summary>

Register or update a discovered external agent (WP-4008).

</details>

<CodePlayground lang='bash' code='thegent discovery-register --agent VALUE --pid VALUE --ppid VALUE ...' />

---

## `thegent discovery-scan`

Scan process tree for agent CLI sessions and auto-register them.

<details>
<summary>Full documentation</summary>

Scan process tree for agent CLI sessions and auto-register them.

Detects running cursor-agent, Claude Code, and Codex processes,
extracts session IDs from --resume= when present, and registers them
for introspection via thegent ps, terminal takeover, and inbox.

</details>

<CodePlayground lang='bash' code='thegent discovery-scan --format VALUE' />

---

## `thegent dlq-list`

List items in the Dead-Letter Queue (WP-Y2/WP-2008).

<details>
<summary>Full documentation</summary>

List items in the Dead-Letter Queue (WP-Y2/WP-2008).

</details>

<CodePlayground lang='bash' code='thegent dlq-list --status VALUE --format VALUE' />

---

## `thegent drift`

Detect significant drift in contract performance and check alert budgets (G-RV-07).

<details>
<summary>Full documentation</summary>

Detect significant drift in contract performance and check alert budgets (G-RV-07).

</details>

<CodePlayground lang='bash' code='thegent drift --window VALUE --format VALUE --structural-budget VALUE ...' />

---

## `thegent drift-monitor`

Monitor drift across multiple providers for the same prompt (WP-3001).

<details>
<summary>Full documentation</summary>

Monitor drift across multiple providers for the same prompt (WP-3001).

</details>

<CodePlayground lang='bash' code='thegent drift-monitor --prompt VALUE --agents VALUE' />

---

## `thegent escalate-add`

Add a blocked run to the escalation queue (WP-3008).

<details>
<summary>Full documentation</summary>

Add a blocked run to the escalation queue (WP-3008).

</details>

<CodePlayground lang='bash' code='thegent escalate-add --run-id VALUE --reason VALUE --sla-minutes VALUE ...' />

---

## `thegent escalate-approve`

Approve an escalation, recording an override for the owner (G-GP-05).

<details>
<summary>Full documentation</summary>

Approve an escalation, recording an override for the owner (G-GP-05).

</details>

<CodePlayground lang='bash' code='thegent escalate-approve --run-id VALUE' />

---

## `thegent escalate-list`

List governance escalation queue (WP-3008).

<details>
<summary>Full documentation</summary>

List governance escalation queue (WP-3008).

</details>

<CodePlayground lang='bash' code='thegent escalate-list --past-sla-only VALUE --limit VALUE --format VALUE' />

---

## `thegent escalate-resolve`

Mark an escalation item as resolved (WP-3008).

<details>
<summary>Full documentation</summary>

Mark an escalation item as resolved (WP-3008).

</details>

<CodePlayground lang='bash' code='thegent escalate-resolve --run-id VALUE --resolution VALUE' />

---

## `thegent events`

List raw telemetry events.

<details>
<summary>Full documentation</summary>

List raw telemetry events.

</details>

<CodePlayground lang='bash' code='thegent events --run-id VALUE --limit VALUE --format VALUE' />

---

## `thegent explain`

Show detailed explanation for an agent run (WP-4002).

<details>
<summary>Full documentation</summary>

Show detailed explanation for an agent run (WP-4002).

</details>

<CodePlayground lang='bash' code='thegent explain --run-id VALUE' />

---

## `thegent explorer`

Launch the terminal explorer TUI.

<details>
<summary>Full documentation</summary>

Launch the terminal explorer TUI.

</details>

<CodePlayground lang='bash' code='thegent explorer' />

---

## `thegent fallbacks`

Show safe fallback options for a failed or blocked run (WP-4003).

<details>
<summary>Full documentation</summary>

Show safe fallback options for a failed or blocked run (WP-4003).

</details>

<CodePlayground lang='bash' code='thegent fallbacks --run-id VALUE' />

---

## `thegent feedback`

Provide operator feedback for a specific run.

<details>
<summary>Full documentation</summary>

Provide operator feedback for a specific run.

</details>

<CodePlayground lang='bash' code='thegent feedback --run-id VALUE --score VALUE --note VALUE' />

---

## `thegent forensics-snapshot`

Take a forensics snapshot of an agent run (WP-3002).

<details>
<summary>Full documentation</summary>

Take a forensics snapshot of an agent run (WP-3002).

</details>

<CodePlayground lang='bash' code='thegent forensics-snapshot --run-id VALUE --phase VALUE' />

---

## `thegent govern-configure`

Bootstrap governance: create contracts/health-targets.json if missing.

<details>
<summary>Full documentation</summary>

Bootstrap governance: create contracts/health-targets.json if missing.

</details>

<CodePlayground lang='bash' code='thegent govern-configure --cd VALUE --force VALUE' />

---

## `thegent govern-cost`

Show daily cost aggregation (FR-GOV-002).

<details>
<summary>Full documentation</summary>

Show daily cost aggregation (FR-GOV-002).

</details>

<CodePlayground lang='bash' code='thegent govern-cost --owner VALUE --days VALUE --format VALUE' />

---

## `thegent govern-go-cycle`

Run a single governance cycle.

<details>
<summary>Full documentation</summary>

Run a single governance cycle.

</details>

<CodePlayground lang='bash' code='thegent govern-go-cycle --cd VALUE --force VALUE --format VALUE' />

---

## `thegent govern-go-health`

Show current health score (composite 0-100, band, per-dimension breakdown).

<details>
<summary>Full documentation</summary>

Show current health score (composite 0-100, band, per-dimension breakdown).

</details>

<CodePlayground lang='bash' code='thegent govern-go-health --cd VALUE --format VALUE' />

---

## `thegent govern-go-status`

Show current governance status (state, cycle_id, shutdown_requested).

<details>
<summary>Full documentation</summary>

Show current governance status (state, cycle_id, shutdown_requested).

</details>

<CodePlayground lang='bash' code='thegent govern-go-status --cd VALUE' />

---

## `thegent govern-go-watch`

Run continuous governance mode.

<details>
<summary>Full documentation</summary>

Run continuous governance mode.

</details>

<CodePlayground lang='bash' code='thegent govern-go-watch --cd VALUE --interval VALUE --max-cycles VALUE' />

---

## `thegent guardrails-check`

Check a prompt against active guardrails (FR-GOV-003..006).

<details>
<summary>Full documentation</summary>

Check a prompt against active guardrails (FR-GOV-003..006).

</details>

<CodePlayground lang='bash' code='thegent guardrails-check --prompt VALUE --agent VALUE --model VALUE' />

---

## `thegent guardrails-show`

Show active guardrail configuration (FR-GOV-007).

<details>
<summary>Full documentation</summary>

Show active guardrail configuration (FR-GOV-007).

</details>

<CodePlayground lang='bash' code='thegent guardrails-show' />

---

## `thegent handoff`

Create a continuity snapshot for a shift handoff (WP-4006, WP-3008).

<details>
<summary>Full documentation</summary>

Create a continuity snapshot for a shift handoff (WP-4006, WP-3008).

</details>

<CodePlayground lang='bash' code='thegent handoff --owner VALUE' />

---

## `thegent handoff-confirm`

Incoming owner confirms handoff completeness (WP-3008, WP-4006).

<details>
<summary>Full documentation</summary>

Incoming owner confirms handoff completeness (WP-3008, WP-4006).

</details>

<CodePlayground lang='bash' code='thegent handoff-confirm --snapshot-id VALUE --incoming-owner VALUE --confidence VALUE' />

---

## `thegent handoff-list`

List pending handoff snapshots (WP-4006).

<details>
<summary>Full documentation</summary>

List pending handoff snapshots (WP-4006).

</details>

<CodePlayground lang='bash' code='thegent handoff-list --limit VALUE --format VALUE' />

---

## `thegent handoff-show`

Show full handoff summary (state, evidence, next steps) for a snapshot (WP-4006).

<details>
<summary>Full documentation</summary>

Show full handoff summary (state, evidence, next steps) for a snapshot (WP-4006).

</details>

<CodePlayground lang='bash' code='thegent handoff-show --snapshot-id VALUE --format VALUE' />

---

## `thegent history`

List execution run history (sync and background).

<details>
<summary>Full documentation</summary>

List execution run history (sync and background).

</details>

<CodePlayground lang='bash' code='thegent history --limit VALUE --format VALUE' />

---

## `thegent inbox-list`

List unified inbox events (run registry + escalation) with optional filters.

<details>
<summary>Full documentation</summary>

List unified inbox events (run registry + escalation) with optional filters.

</details>

<CodePlayground lang='bash' code='thegent inbox-list --owner VALUE --agent VALUE --event-type VALUE ...' />

---

## `thegent inbox-wait`

Wait for next inbox event matching filters. Blocks until new event or timeout.

<details>
<summary>Full documentation</summary>

Wait for next inbox event matching filters. Blocks until new event or timeout.

</details>

<CodePlayground lang='bash' code='thegent inbox-wait --owner VALUE --agent VALUE --event-type VALUE ...' />

---

## `thegent inspect`

Show status and logs for one or more sessions. No shell loop needed.

<details>
<summary>Full documentation</summary>

Show status and logs for one or more sessions. No shell loop needed.

</details>

<CodePlayground lang='bash' code='thegent inspect --session-ids VALUE --owner VALUE --tail VALUE ...' />

---

## `thegent interruption-list`

List recent interruptions (WP-4004).

<details>
<summary>Full documentation</summary>

List recent interruptions (WP-4004).

</details>

<CodePlayground lang='bash' code='thegent interruption-list --limit VALUE --format VALUE' />

---

## `thegent interruption-snooze`

Snooze an alert; expires → auto-escalation (WP-4004).

<details>
<summary>Full documentation</summary>

Snooze an alert; expires → auto-escalation (WP-4004).

</details>

<CodePlayground lang='bash' code='thegent interruption-snooze --alert-id VALUE --minutes VALUE --itype VALUE' />

---

## `thegent list-agents`

List available agents.

<details>
<summary>Full documentation</summary>

List available agents.

</details>

<CodePlayground lang='bash' code='thegent list-agents' />

---

## `thegent list-droids`

List available droids.

<details>
<summary>Full documentation</summary>

List available droids.

</details>

<CodePlayground lang='bash' code='thegent list-droids --cd VALUE' />

---

## `thegent list-model-contract-schema`

Print the route contract schema metadata used by contract views.

<details>
<summary>Full documentation</summary>

Print the route contract schema metadata used by contract views.

</details>

<CodePlayground lang='bash' code='thegent list-model-contract-schema' />

---

## `thegent list-models`

List available models (scraped from CLIs/config).

<details>
<summary>Full documentation</summary>

List available models (scraped from CLIs/config).

</details>

<CodePlayground lang='bash' code='thegent list-models --provider VALUE --by-model VALUE --refresh VALUE ...' />

---

## `thegent load-status`

Show load classification and safe-mode status (WP-5002).

<details>
<summary>Full documentation</summary>

Show load classification and safe-mode status (WP-5002).

</details>

<CodePlayground lang='bash' code='thegent load-status --format VALUE' />

---

## `thegent logs`

<CodePlayground lang='bash' code='thegent logs --session-id VALUE --follow VALUE --stderr VALUE ...' />

---

## `thegent loop`

Run a Lifecycle loop with Checker oversight.

<details>
<summary>Full documentation</summary>

Run a Lifecycle loop with Checker oversight.

</details>

<CodePlayground lang='bash' code='thegent loop --prompt VALUE --todo-spec VALUE --agent VALUE ...' />

---

## `thegent loop-send`

Send a prompt to a running Lifecycle loop (human or agent takeover).

<details>
<summary>Full documentation</summary>

Send a prompt to a running Lifecycle loop (human or agent takeover).

</details>

<CodePlayground lang='bash' code='thegent loop-send --session-id VALUE --prompt VALUE' />

---

## `thegent loop-stop`

Send STOP signal to a running Lifecycle loop.

<details>
<summary>Full documentation</summary>

Send STOP signal to a running Lifecycle loop.

</details>

<CodePlayground lang='bash' code='thegent loop-stop --session-id VALUE' />

---

## `thegent metrics`

Show cost, speed, and quality indices for all model-provider pairs (unified view).

<details>
<summary>Full documentation</summary>

Show cost, speed, and quality indices for all model-provider pairs (unified view).

</details>

<CodePlayground lang='bash' code='thegent metrics --format VALUE --no-cache VALUE --limit VALUE' />

---

## `thegent migration`

Evaluate migration status for a contract version.

<details>
<summary>Full documentation</summary>

Evaluate migration status for a contract version.

</details>

<CodePlayground lang='bash' code='thegent migration --contract-id VALUE --version VALUE --format VALUE' />

---

## `thegent modes`

List multi-agent orchestration modes (sequential_delegation, parallel_consensus, review_loop).

<details>
<summary>Full documentation</summary>

List multi-agent orchestration modes (sequential_delegation, parallel_consensus, review_loop).

</details>

<CodePlayground lang='bash' code='thegent modes --format VALUE --mode VALUE' />

---

## `thegent monitor`

Monitor sessions and plan progress in real-time (WP-8001).

<details>
<summary>Full documentation</summary>

Monitor sessions and plan progress in real-time (WP-8001).

</details>

<CodePlayground lang='bash' code='thegent monitor --interval VALUE' />

---

## `thegent observe-summary`

FR-X08: Unified observability summary (KPIs, drift, escalation).

<details>
<summary>Full documentation</summary>

FR-X08: Unified observability summary (KPIs, drift, escalation).

</details>

<CodePlayground lang='bash' code='thegent observe-summary --limit VALUE --drift-window VALUE --structural-budget VALUE ...' />

---

## `thegent operations`

List universal operation taxonomy (orchestrate, govern, recover, observe, plan).

<details>
<summary>Full documentation</summary>

List universal operation taxonomy (orchestrate, govern, recover, observe, plan).

</details>

<CodePlayground lang='bash' code='thegent operations --format VALUE --operation VALUE' />

---

## `thegent pause`

Pause a background session (register pause event).

<details>
<summary>Full documentation</summary>

Pause a background session (register pause event).

</details>

<CodePlayground lang='bash' code='thegent pause --session-id VALUE' />

---

## `thegent plan-analyze`

Run planning simulation overlays (XD1–XD3): PERT, resource contention, continuity risk.

<details>
<summary>Full documentation</summary>

Run planning simulation overlays (XD1–XD3): PERT, resource contention, continuity risk.

</details>

<CodePlayground lang='bash' code='thegent plan-analyze --cd VALUE --pert VALUE --resources VALUE ...' />

---

## `thegent plan-claim`

Claim an item in the unified work stream.

<details>
<summary>Full documentation</summary>

Claim an item in the unified work stream.

</details>

<CodePlayground lang='bash' code='thegent plan-claim --item-id VALUE --agent-id VALUE --cd VALUE' />

---

## `thegent plan-complete`

Mark an item as complete in the unified work stream.

<details>
<summary>Full documentation</summary>

Mark an item as complete in the unified work stream.

</details>

<CodePlayground lang='bash' code='thegent plan-complete --item-id VALUE --agent-id VALUE --cd VALUE' />

---

## `thegent plan-do-next`

Find next actionable work items from WORK_STREAM, PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

<details>
<summary>Full documentation</summary>

Find next actionable work items from WORK_STREAM, PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

</details>

<CodePlayground lang='bash' code='thegent plan-do-next --cd VALUE --limit VALUE --format VALUE' />

---

## `thegent plan-get-next`

Get first work item prompt for scripting. Use: PROMPT=$(thegent plan get-next)

<details>
<summary>Full documentation</summary>

Get first work item prompt for scripting. Use: PROMPT=$(thegent plan get-next)

</details>

<CodePlayground lang='bash' code='thegent plan-get-next --cd VALUE --format VALUE' />

---

## `thegent plan-incorporate`

Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md. Preserves CLAIMED and COMPLETED.

<details>
<summary>Full documentation</summary>

Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md. Preserves CLAIMED and COMPLETED.

</details>

<CodePlayground lang='bash' code='thegent plan-incorporate --cd VALUE --dry-run VALUE' />

---

## `thegent plan-loop`

Loop: get next item -> run bg -> repeat until no items or --max reached.

<details>
<summary>Full documentation</summary>

Loop: get next item -> run bg -> repeat until no items or --max reached.

</details>

<CodePlayground lang='bash' code='thegent plan-loop --cd VALUE --max-iterations VALUE --sleep-seconds VALUE ...' />

---

## `thegent plan-progress`

Show recent runs (work-package progress). Alias for history --limit N.

<details>
<summary>Full documentation</summary>

Show recent runs (work-package progress). Alias for history --limit N.

</details>

<CodePlayground lang='bash' code='thegent plan-progress --limit VALUE --format VALUE' />

---

## `thegent plan-wait-next`

Block until next actionable work exists (DAG ready, do_next, escalation, inbox).

<details>
<summary>Full documentation</summary>

Block until next actionable work exists (DAG ready, do_next, escalation, inbox).

</details>

<CodePlayground lang='bash' code='thegent plan-wait-next --cd VALUE --poll VALUE --timeout VALUE ...' />

---

## `thegent policy-check`

Evaluate a hypothetical run against governance policies (WP-3001).

<details>
<summary>Full documentation</summary>

Evaluate a hypothetical run against governance policies (WP-3001).

</details>

<CodePlayground lang='bash' code='thegent policy-check --agent VALUE --model VALUE --lane VALUE ...' />

---

## `thegent policy-purge`

Purge expired history based on tiered retention (WP-3006).

<details>
<summary>Full documentation</summary>

Purge expired history based on tiered retention (WP-3006).

</details>

<CodePlayground lang='bash' code='thegent policy-purge --dry-run VALUE' />

---

## `thegent policy-show`

Show active governance policies and thresholds.

<details>
<summary>Full documentation</summary>

Show active governance policies and thresholds.

</details>

<CodePlayground lang='bash' code='thegent policy-show' />

---

## `thegent project list`

List all registered projects (WP-4008).

<details>
<summary>Full documentation</summary>

List all registered projects (WP-4008).

</details>

<CodePlayground lang='bash' code='thegent project list' />

---

## `thegent project init`

Register a new project (WP-4008).

<details>
<summary>Full documentation</summary>

Register a new project (WP-4008).

</details>

<CodePlayground lang='bash' code='thegent project init --path VALUE --name VALUE --tenant VALUE --template VALUE' />

---

## `thegent project greenfield`

Create a new project scaffold via initialize-project presets.

<details>
<summary>Full documentation</summary>

Greenfield bootstrap variant that uses preset scaffolds and optional runtime install.

</details>

<CodePlayground lang='bash' code='thegent project greenfield DESTINATION --profile service_api --name VALUE --install-runtime' />

---

## `thegent project brownfield`

Migrate or adopt an existing project into Thegent project tenancy.

<details>
<summary>Full documentation</summary>

Brownfield migration with optional template adoption mode (`auto`, `ag-dd`, `none`).

</details>

<CodePlayground lang='bash' code='thegent project brownfield /path/to/repo --template ag-dd --register --install-runtime' />

---

## `thegent project ag-dd`

Brownfield variant locked to AG-DD template mode.

<details>
<summary>Full documentation</summary>

Use AG-DD-specific migration mode when adapting existing projects.

</details>

<CodePlayground lang='bash' code='thegent project ag-dd /path/to/repo --install-runtime --dry-run' />

---

## `thegent project none`

Brownfield variant with no template overlay.

<details>
<summary>Full documentation</summary>

Adopt an existing project without applying a new template overlay.

</details>

<CodePlayground lang='bash' code='thegent project none /path/to/repo --install-runtime --dry-run' />

---

## `thegent ps`

<CodePlayground lang='bash' code='thegent ps --all-sessions VALUE --owner VALUE --format VALUE ...' />

---

## `thegent purge`

WP-3006: Tiered retention purge (G-GP-07).

<details>
<summary>Full documentation</summary>

WP-3006: Tiered retention purge (G-GP-07).

</details>

<CodePlayground lang='bash' code='thegent purge --dry-run VALUE' />

---

## `thegent quality-index`

Show quality index (0-1) for all models.

<details>
<summary>Full documentation</summary>

Show quality index (0-1) for all models.

Uses benchmarks.json (Terminal Bench 2.0, SWE-Bench, AIME) when available;
falls back to Route.accuracy_score.

</details>

<CodePlayground lang='bash' code='thegent quality-index --format VALUE --no-cache VALUE' />

---

## `thegent queue-list`

WP-7002: List pending prompts in the queue.

<details>
<summary>Full documentation</summary>

WP-7002: List pending prompts in the queue.

</details>

<CodePlayground lang='bash' code='thegent queue-list --watch VALUE' />

---

## `thegent recover-status`

Show current recovery status (WP-7001).

<details>
<summary>Full documentation</summary>

Show current recovery status (WP-7001).

</details>

<CodePlayground lang='bash' code='thegent recover-status' />

---

## `thegent release-pack`

Automated release documentation packaging (WP-12009).

<details>
<summary>Full documentation</summary>

Automated release documentation packaging (WP-12009).

</details>

<CodePlayground lang='bash' code='thegent release-pack --version VALUE' />

---

## `thegent replay`

Decision replay and rationale snapshots (WP-4007).

<details>
<summary>Full documentation</summary>

Decision replay and rationale snapshots (WP-4007).

</details>

<CodePlayground lang='bash' code='thegent replay --run-id VALUE --what-if-env VALUE' />

---

## `thegent resolve-model-route`

Resolve a model to a preferred route and emit contract-style output.

<details>
<summary>Full documentation</summary>

Resolve a model to a preferred route and emit contract-style output.

</details>

<CodePlayground lang='bash' code='thegent resolve-model-route --model VALUE --provider VALUE --policy VALUE ...' />

---

## `thegent resume`

Resume a background session (register resume event).

<details>
<summary>Full documentation</summary>

Resume a background session using the stable WL-110 state contract.

- With no `--session-id`, `thegent` selects the most recent resumable `state.json`
  under `~/.thegent/sessions/*/state.json`.
- A resumable state contract must include non-empty string values for:
  - `session_id`
  - `run_id`
- Malformed state contracts are skipped during auto-selection and rejected when
  explicitly targeted.

</details>

<CodePlayground lang='bash' code='thegent resume --session-id VALUE' />

---

## `thegent retry`

Retry a failed run. With no run_id, list recent failed runs.

<details>
<summary>Full documentation</summary>

Retry a failed run. With no run_id, list recent failed runs.

</details>

<CodePlayground lang='bash' code='thegent retry --run-id VALUE --agent VALUE --failover VALUE ...' />

---

## `thegent roadmap`

Successor roadmap generation (WP-6004).

<details>
<summary>Full documentation</summary>

Successor roadmap generation (WP-6004).

</details>

<CodePlayground lang='bash' code='thegent roadmap' />

---

## `thegent rules-sync`

Sync CLAUDE.md to other platform-specific rule files (AGENTS.md, Cursor, Codex).

<details>
<summary>Full documentation</summary>

Sync CLAUDE.md to other platform-specific rule files (AGENTS.md, Cursor, Codex).

</details>

<CodePlayground lang='bash' code='thegent rules-sync --force VALUE --check VALUE --cd VALUE' />

---

## `thegent run`

Run an agent or droid with the given prompt. Model-first: agent=None, model set.

<details>
<summary>Full documentation</summary>

Run an agent or droid with the given prompt. Model-first: agent=None, model set.

</details>

<CodePlayground lang='bash' code='thegent run agent "VALUE" --agent VALUE --cd VALUE ...' />

---

## `thegent run-diff`

Compare two execution runs (WP-16001).

<details>
<summary>Full documentation</summary>

Compare two execution runs (WP-16001).

</details>

<CodePlayground lang='bash' code='thegent run-diff --run-a VALUE --run-b VALUE' />

---

## `thegent self-heal-tests`

Self-healing test suite: automated fix recommendations (WP-6006).

<details>
<summary>Full documentation</summary>

Self-healing test suite: automated fix recommendations (WP-6006).

</details>

<CodePlayground lang='bash' code='thegent self-heal-tests --test-output VALUE' />

---

## `thegent session`

Rich TUI for session management with subagent monitoring (WP-8002).

<details>
<summary>Full documentation</summary>

Rich TUI for session management with subagent monitoring (WP-8002).

</details>

<CodePlayground lang='bash' code='thegent session --session-id VALUE --watch VALUE --action VALUE' />

---

## `thegent session-contract-health-gate`

<CodePlayground lang='bash' code='thegent session-contract-health-gate --all-sessions VALUE --owner VALUE --strict VALUE ...' />

---

## `thegent session-contract-health-report`

<CodePlayground lang='bash' code='thegent session-contract-health-report --all-sessions VALUE --owner VALUE --strict VALUE ...' />

---

## `thegent session-contract-health-trend`

<CodePlayground lang='bash' code='thegent session-contract-health-trend --payload-type VALUE --all-sessions VALUE --owner VALUE ...' />

---

## `thegent session-contract-negotiate`

Negotiate a contract version (WP-7001).

<details>
<summary>Full documentation</summary>

Negotiate a contract version (WP-7001).

</details>

<CodePlayground lang='bash' code='thegent session-contract-negotiate --contract-id VALUE --supported-versions VALUE --format VALUE' />

---

## `thegent session-contract-trend-analysis`

Detailed contract trend analysis (WP-7009/7010).

<details>
<summary>Full documentation</summary>

Detailed contract trend analysis (WP-7009/7010).

</details>

<CodePlayground lang='bash' code='thegent session-contract-trend-analysis' />

---

## `thegent session-contracts`

<CodePlayground lang='bash' code='thegent session-contracts --all-sessions VALUE --owner VALUE --format VALUE ...' />

---

## `thegent setup`

Unified setup: configure providers (same flow as cliproxy login) and install shortcuts.

<details>
<summary>Full documentation</summary>

Unified setup: configure providers (same flow as cliproxy login) and install shortcuts.

Examples:
thegent setup # Interactive wizard
thegent setup --full # Full setup: install, shims, services, harness
thegent setup --harness # Install/update heliosShield harness only
thegent setup --hooks --skills # Project: git hooks + skills

</details>

<CodePlayground lang='bash' code='thegent setup --api-key VALUE --model VALUE --openrouter-key VALUE ...' />

---

## `thegent sys setup project scaffold`

Bootstrap a new project from initialize-project presets.

<details>
<summary>Full documentation</summary>

Preset scaffold command with profile defaults and optional tenancy/runtime wiring.

Examples:
thegent sys setup project scaffold ./my-service --profile service_api
thegent sys setup project scaffold ./my-service --profile service_api --dry-run --json
thegent sys setup project scaffold ./my-service --profile service_api --register --install-runtime

</details>

<CodePlayground lang='bash' code='thegent sys setup project scaffold DESTINATION --profile VALUE --name VALUE --description VALUE --language VALUE --register --install-runtime --dry-run --json' />

---

## `thegent sys setup project scaffold-profiles`

List available scaffold preset profiles.

<details>
<summary>Full documentation</summary>

Show supported profile names and optionally emit JSON.

Examples:
thegent sys setup project scaffold-profiles
thegent sys setup project scaffold-profiles --json

</details>

<CodePlayground lang='bash' code='thegent sys setup project scaffold-profiles --json' />

---

## `thegent signatures-list`

List signed MAIF artifacts (WP-3002).

<details>
<summary>Full documentation</summary>

List signed MAIF artifacts (WP-3002).

</details>

<CodePlayground lang='bash' code='thegent signatures-list --limit VALUE --format VALUE' />

---

## `thegent signatures-verify`

Verify a signed MAIF artifact (WP-3002).

<details>
<summary>Full documentation</summary>

Verify a signed MAIF artifact (WP-3002).

</details>

<CodePlayground lang='bash' code='thegent signatures-verify --run-id VALUE' />

---

## `thegent sitback-dashboard`

Unified sitback dashboard: sessions, cockpit (circuits, drift, budget), terminals.

<details>
<summary>Full documentation</summary>

Unified sitback dashboard: sessions, cockpit (circuits, drift, budget), terminals.
CLI mirror of thegent_sitback_dashboard MCP tool.
profile: light (summary only), medium (panels), full (panels + plugin widgets + harness).

</details>

<CodePlayground lang='bash' code='thegent sitback-dashboard --refresh VALUE --format VALUE --profile VALUE' />

---

## `thegent speed-index`

Show speed index (0-1, higher=faster) for all model-provider pairs.

<details>
<summary>Full documentation</summary>

Show speed index (0-1, higher=faster) for all model-provider pairs.

Uses CLIProxyAPIPlus metrics (tps_1m, latency_p50_ms, success_rate) when reachable;
falls back to Route.latency_ms.

</details>

<CodePlayground lang='bash' code='thegent speed-index --format VALUE --no-cache VALUE' />

---

## `thegent status`

<CodePlayground lang='bash' code='thegent status --session-id VALUE --format VALUE --include-contract VALUE' />

---

## `thegent stop`

<CodePlayground lang='bash' code='thegent stop --session-id VALUE --force VALUE --wind-down VALUE ...' />

---

## `thegent summary`

FR-X09: Unified summary and audit log across runs, chats, and commits.

<details>
<summary>Full documentation</summary>

FR-X09: Unified summary and audit log across runs, chats, and commits.

</details>

<CodePlayground lang='bash' code='thegent summary --period VALUE --project VALUE --summarize VALUE ...' />

---

## `thegent sweep`

WP-3005: Policy drift sweep - runs drift detection, budget check, past-SLA escalations.

<details>
<summary>Full documentation</summary>

WP-3005: Policy drift sweep - runs drift detection, budget check, past-SLA escalations.

</details>

<CodePlayground lang='bash' code='thegent sweep --drift-window VALUE --include-audit VALUE --format VALUE' />

---

## `thegent takeover`

Take over an active terminal session via tmux (WP-4008).

<details>
<summary>Full documentation</summary>

Take over an active terminal session via tmux (WP-4008).

</details>

<CodePlayground lang='bash' code='thegent takeover --session-id VALUE' />

---

## `thegent team-create`

WP-6008: Create a new multi-agent team.

<details>
<summary>Full documentation</summary>

WP-6008: Create a new multi-agent team.

</details>

<CodePlayground lang='bash' code='thegent team-create --name VALUE --leader VALUE --teammates VALUE' />

---

## `thegent team-task-add`

WP-6008: Add a task to a team's backlog.

<details>
<summary>Full documentation</summary>

WP-6008: Add a task to a team's backlog.

</details>

<CodePlayground lang='bash' code='thegent team-task-add --team-id VALUE --title VALUE --description VALUE' />

---

## `thegent team-task-list`

WP-6008: List all tasks for a team.

<details>
<summary>Full documentation</summary>

WP-6008: List all tasks for a team.

</details>

<CodePlayground lang='bash' code='thegent team-task-list --team-id VALUE' />

---

## `thegent teammates-delegate`

WP-16002: Delegate a sub-task to a specialized teammate.

<details>
<summary>Full documentation</summary>

WP-16002: Delegate a sub-task to a specialized teammate.

</details>

<CodePlayground lang='bash' code='thegent teammates-delegate --teammate-id VALUE --prompt VALUE --parent-run-id VALUE' />

---

## `thegent teammates-list`

WP-16001: List all discovered specialized agents available for delegation.

<details>
<summary>Full documentation</summary>

WP-16001: List all discovered specialized agents available for delegation.

</details>

<CodePlayground lang='bash' code='thegent teammates-list' />

---

## `thegent teammates-status`

WP-16002: Monitor the status of the teammate swarm.

<details>
<summary>Full documentation</summary>

WP-16002: Monitor the status of the teammate swarm.

</details>

<CodePlayground lang='bash' code='thegent teammates-status --run-id VALUE' />

---

## `thegent terminal-route`

Automatically route a prompt to an active terminal session if matching.

<details>
<summary>Full documentation</summary>

Automatically route a prompt to an active terminal session if matching.

</details>

<CodePlayground lang='bash' code='thegent terminal-route --prompt VALUE --cd VALUE' />

---

## `thegent trace-replay`

WP-16001: Replay an execution trace in sandbox mode.

<details>
<summary>Full documentation</summary>

WP-16001: Replay an execution trace in sandbox mode.

</details>

<CodePlayground lang='bash' code='thegent trace-replay --run-id VALUE' />

---

## `thegent traffic`

TRAFFIC KPI Dashboard (WP-Y7).

<details>
<summary>Full documentation</summary>

TRAFFIC KPI Dashboard (WP-Y7).

</details>

<CodePlayground lang='bash' code='thegent traffic' />

---

## `thegent trust-status`

Show last environment and trust boundary status (WP-3007).

<details>
<summary>Full documentation</summary>

Show last environment and trust boundary status (WP-3007).

</details>

<CodePlayground lang='bash' code='thegent trust-status --format VALUE' />

---

## `thegent usage`

Show plan usage: provider metrics from CLIProxyAPIPlus and cost status (WP-5003).

<details>
<summary>Full documentation</summary>

Show plan usage: provider metrics from CLIProxyAPIPlus and cost status (WP-5003).

For cross-provider session parsing (OpenCode, Claude Code, Codex, Gemini, Cursor, etc.),
use: bunx tokscale@latest

</details>

<CodePlayground lang='bash' code='thegent usage --format VALUE --include-cost VALUE' />

---

## `thegent wait`

<CodePlayground lang='bash' code='thegent wait --session-id VALUE --timeout VALUE' />

---

## `thegent watchdog`

Scan for stale sessions and recommend handoffs (WP-5005).

<details>
<summary>Full documentation</summary>

Scan for stale sessions and recommend handoffs (WP-5005).

</details>

<CodePlayground lang='bash' code='thegent watchdog --max-idle-s VALUE' />

---

## `thegent workstream-dashboard`

Launch workstream dashboard TUI.

<details>
<summary>Full documentation</summary>

Launch workstream dashboard TUI.

</details>

<CodePlayground lang='bash' code='thegent workstream-dashboard' />

---

## `thegent workstream-dependencies`

Show the workstream dependency graph.

<details>
<summary>Full documentation</summary>

Show the workstream dependency graph.

</details>

<CodePlayground lang='bash' code='thegent workstream-dependencies' />

---

## `thegent workstream-launch`

Launch the auto-launch system in the background.

<details>
<summary>Full documentation</summary>

Launch the auto-launch system in the background.

</details>

<CodePlayground lang='bash' code='thegent workstream-launch' />

---

## `thegent workstream-query`

Execute SQL query on workstream database.

<details>
<summary>Full documentation</summary>

Execute SQL query on workstream database.

</details>

<CodePlayground lang='bash' code='thegent workstream-query --query VALUE' />

---

## `thegent workstream-stats`

Get workstream statistics.

<details>
<summary>Full documentation</summary>

Get workstream statistics.

</details>

<CodePlayground lang='bash' code='thegent workstream-stats' />

---
