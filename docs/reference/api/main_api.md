# main API Reference

> **Source**: `src/thegent/main.py`

Thegent CLI entry point (subcommand-only).

---

## acp_client_cmd

```python
acp_client_cmd(command: str, prompt: str, cwd: Any)
```

Spawn an external ACP agent and run a prompt.

**Examples**:

```python
thegent acp client "npx -y @zed-industries/claude-agent-acp" --prompt "Analyze my code"
```

---

## acp_server_cmd

Run ACP server adapter (exposes thegent agents via ACP protocol).

This command runs an ACP server that exposes thegent agents as ACP-compatible agents.
Use this with ACP clients like gsh or Zed.

Example (gsh): # In ~/.gsh/repl.gsh:
acp Thegent {
command: "thegent",
args: ["acp", "server"],
}

Then use in gsh REPL:
gsh> @thegent analyze my codebase

---

## add_api_key_cmd

```python
add_api_key_cmd(provider: str, api_key: str)
```

Add API key for a provider.

---

## add_benchmark_cmd

```python
add_benchmark_cmd(provider: str, model: str, name: str, score: float, category: str, description: str)
```

Add a custom benchmark for a model.

---

## add_modality_cmd

```python
add_modality_cmd(provider: str, model: str, modality: str, value: str)
```

Add or update a modality/feature flag for a model.

---

## add_provider_cmd

```python
add_provider_cmd(name: str, base_url: str, model: str, alias: Any, api_key: Any, login_url: Any)
```

Add a new provider.

---

## agents_list

List available providers. Alias for thegent list-agents.

---

## agents_retry

```python
agents_retry(run_id: Any, agent: Any, failover: bool, cd: Any, override: Any)
```

Retry a failed run. With no run_id, list recent failed runs. Alias for thegent retry.

---

## archive

```python
archive(days: Any, domain: Any, tier: Any)
```

Archive old sessions (WP-6005). WP-3006: tiered retention (hot 30d, cold 1yr).

---

## benchmark

Report orchestration performance metrics (WP-6001).

---

## bg

```python
bg(prompt: str, agent: Any, cd: Any, mode: str, timeout: Any, full: bool, owner: Any, model: Any, provider: Any, routing: Any, failover: bool, format: Any, include_contract: bool, continuation: Any, continuation_stderr: bool, run_id: Any, lane: str, idempotency_token: Any, confidence: Any, arbitration: Any, override: Any, contract_version: Any, domain: Any, speculative: bool, debug: bool, task_id: Any)
```

Start a background run and register a session.

---

## cliproxy_ensure_config

Ensure proxy config exists (port, auth-dir). Add provider blocks manually. Restart proxy to apply.

---

## cliproxy_login

```python
cliproxy_login(provider: str, force: bool)
```

Run login for provider. Unified flow: open URL + prompt for API key. Preflight checks existing credentials.

---

## cliproxy_models_setup

Rich TUI for adding models and providers with harness configuration.

---

## cliproxy_restart

Ensure config, stop proxy, then start. Use after config changes.

---

## cliproxy_service

```python
cliproxy_service(action: str)
```

Manage proxy as launchd service (macOS). Runs at login, restarts on crash.

---

## cliproxy_start

Start proxy if not running. Uses ensure-config + CLIProxyAPIPlus binary.

---

## cliproxy_stop

Stop proxy (kill process on cliproxy port).

---

## closure_pack

```python
closure_pack(cd: Any)
```

Generate a formal closure pack for the current DAG session (WP-6002/6008/FR-024).

---

## cockpit

Show high-level operator cockpit summary.

---

## code

```python
code(prompt: str, cd: Any, bg: bool, model: Any, timeout: Any)
```

Feature implementation and coding tasks.

---

## compliance_export

```python
compliance_export(framework: str, output: str)
```

Export evidence bundle for SOC2, ISO27001, or EU-AI-ACT.

---

## compliance_plugin_check

```python
compliance_plugin_check(plugin_id: str, signature: str)
```

Verify a plugin contract (WP-15003).

---

## compliance_redact

```python
compliance_redact(text: str)
```

Test PII/Secret redaction (WP-15005).

---

## compliance_siem_test

```python
compliance_siem_test(message: str, severity: str)
```

Test SIEM event egress (WP-15001).

---

## concurrency_set

```python
concurrency_set(limit: int)
```

Set new concurrency limit.

---

## concurrency_show

```python
concurrency_show(format: Any)
```

Show current concurrency limit and utilization.

---

## config_check

```python
config_check(format: Any)
```

Validate config; fail-fast on misconfig (DX-010, ROB-013).

---

## config_concurrency

```python
config_concurrency(show: bool, set_limit: Any, format: Any)
```

View or set concurrency limit.

---

## config_show

```python
config_show(tenant_id: Any, session_id: Any, format: str)
```

Show resolved configuration for the current context.

---

## control_plane_serve

```python
control_plane_serve(socket_path: Any, port: int, host: str)
```

Start the control plane server. Unix: socket or port. Windows: port only.

---

## control_plane_start

Start the control plane stack (via process-compose).

---

## control_plane_status

Check if control plane is running (health endpoint).

---

## control_plane_stop

Stop the control plane stack (via process-compose).

---

## crew_add_agent

```python
crew_add_agent(crew_id: str, role: str, name: str, description: str, capabilities: str, model: str)
```

Add agent to crew.

---

## crew_add_task

```python
crew_add_task(crew_id: str, description: str, dependencies: str, agent_id: str)
```

Add task to crew.

---

## crew_create

```python
crew_create(name: str, description: str, execution_mode: str, output: str)
```

Create a new crew.

---

## crew_execute

```python
crew_execute(crew_id: str, cwd: str, mode: str, timeout: int, model: str)
```

Execute a crew.

---

## crew_list

List all crews.

---

## crew_show

```python
crew_show(crew_id: str)
```

Show crew details.

---

## crew_status

```python
crew_status(crew_id: str)
```

Show crew execution status.

---

## dag_add

```python
dag_add(task_id: str, agent: str, prompt: str, cd: Any, depends_on: Any, contract_version: Any)
```

Add a task to the DAG.

---

## dag_cancel

```python
dag_cancel(task_id: str, cd: Any)
```

Set task status to cancelled.

---

## dag_checkpoint

```python
dag_checkpoint(cd: Any, reason: str)
```

Create a point-in-time checkpoint of the DAG state.

---

## dag_checkpoints

```python
dag_checkpoints(limit: int)
```

List recent DAG checkpoints.

---

## dag_list

```python
dag_list(cd: Any, format: Any)
```

Parse and display DAG session from .factory/dag-session.md.

---

## dag_probe

```python
dag_probe(baseline_id: Any, cd: Any)
```

Compare current DAG state with a baseline checkpoint to detect regressions.

---

## dag_ready

```python
dag_ready(cd: Any, format: Any)
```

List task IDs with satisfied dependencies (ready to run).

---

## dag_reconcile

```python
dag_reconcile(cd: Any)
```

Reconcile DAG state with reality (clean up stuck 'running' tasks).

---

## dag_recover

```python
dag_recover(action: str, cd: Any)
```

Perform recovery playbook actions on the DAG.

---

## dag_remove

```python
dag_remove(task_id: str, cd: Any)
```

Remove a task from the DAG.

---

## dag_rollback

```python
dag_rollback(checkpoint_id: Any, cd: Any)
```

Rollback DAG state to a specific checkpoint.

---

## dag_run

```python
dag_run(cd: Any, dry_run: bool, task: Any, max_parallel: Any, lane: Any, check_drift: bool, contract_version: Any)
```

Spawn background tasks for each ready item; update status=running and session_id.

---

## dag_status

```python
dag_status(cd: Any, format: Any)
```

Show task + linked session status (running/exited:rc).

---

## dag_sync

```python
dag_sync(cd: Any, watch: bool, interval: int, auto_run_next: bool, no_auto_run_next: bool)
```

Update task status from session exit (running -> done/failed).

---

## dag_update

```python
dag_update(task_id: str, cd: Any, status: Any, prompt: Any, agent: Any, depends_on: Any, contract_version: Any)
```

Update a task in the DAG.

---

## dag_validate

```python
dag_validate(cd: Any)
```

Validate DAG: cycles, orphans, agent names. Exit 2 on failure.

---

## dag_wait_next

```python
dag_wait_next(cd: Any, poll: float, timeout: float, format: Any)
```

Block until DAG has next actionable work (sync + ready tasks). Does not return until ready tasks exist.

---

## deep_research

```python
deep_research(query: str, subreddits: str, output: Path)
```

Perform deep research using the Deep Research Protocol (DRP).

---

## deferral_list

List all currently deferred tasks.

---

## deferral_resume

```python
deferral_resume(run_id: str)
```

Manually resume a deferred task.

---

## discover_models_cmd

```python
discover_models_cmd(provider: Any, format: str)
```

Discover available models from providers.

---

## doctor_cmd

```python
doctor_cmd(fix: bool)
```

Verify environment health and fix performance bottlenecks.

---

## explain

```python
explain(prompt: str, cd: Any, bg: bool, model: Any, timeout: Any)
```

Clarification and educational explanation of complex concepts.

---

## explain_run

```python
explain_run(run_id: Any)
```

Show detailed explanation for an agent run (WP-4002).

---

## federation_list

List all federated namespaces (WP-13005).

---

## federation_status

Show detailed federation health and drift status (WP-13005).

---

## feedback

```python
feedback(run_id: Any, score: float, note: str)
```

Provide operator feedback for a specific run.

---

## finance_dashboard

Show financial safety dashboard (WP-Y1).

---

## fix

```python
fix(prompt: str, cd: Any, bg: bool, model: Any, timeout: Any)
```

Bug identification and resolution.

---

## forensics_snapshot

```python
forensics_snapshot(run_id: Any, phase: Any)
```

Capture a forensic snapshot of the current environment.

---

## free

```python
free(prompt: str, cd: Any, mode: str, timeout: int, do_next: bool, repeat: int, live: bool, bg: bool, diff: bool, lane: str)
```

Base free tier: Copilot gpt-5-mini. Alias for thegent run free "`<prompt>`".

---

## fuzzy_search_cmd

```python
fuzzy_search_cmd(query: str, provider: Any, limit: int)
```

Fuzzy search models by name, provider, or notes.

---

## git_lock_cleanup

```python
git_lock_cleanup(ctx: typer.Context, path: Any, max_age: int, dry_run: bool)
```

Remove stale .git/index.lock files. Uses mtime + lsof for safe removal.

Run periodically via 'thegent git lock-cleanup service install'.

---

## git_lock_cleanup_service

```python
git_lock_cleanup_service(action: str)
```

Install lock-cleanup daemon (launchd on macOS, systemd on Linux). Runs every 5 min.

---

## go_cycle

```python
go_cycle(cd: Any, force: bool, format: Any)
```

Run a single governance cycle.

---

## go_health

```python
go_health(cd: Any, format: Any)
```

Show current health score (composite 0-100, band, per-dimension breakdown).

---

## go_status

```python
go_status(cd: Any)
```

Show current governance status (state, cycle_id, shutdown_requested).

---

## go_watch

```python
go_watch(cd: Any, interval: int, max_cycles: Any)
```

Run continuous governance mode.

---

## govern_calibrate

Recalculate trust score calibration factors for all agents (G-GP-09).

---

## govern_compliance_report

```python
govern_compliance_report(format: Any, output: Any)
```

Generate compliance evidence retention report (WP-3006).

---

## govern_configure

```python
govern_configure(cd: Any, force: bool)
```

Bootstrap governance: create contracts/health-targets.json if missing.

---

## govern_conformance

```python
govern_conformance(format: Any, check_drift: bool, drift_window: int)
```

Run provider adapter conformance tests.

---

## govern_contracts

```python
govern_contracts(format: Any)
```

Show the contract registry and compatibility matrix.

---

## govern_cost

```python
govern_cost(owner: Any, days: int, format: Any)
```

Show daily cost aggregation (FR-GOV-002).

---

## govern_data_protection

```python
govern_data_protection(format: Any)
```

Show data protection and privacy controls status (WP-3006).

---

## govern_escalate_add

```python
govern_escalate_add(run_id: str, reason: str, sla_minutes: int, owner: Any, lane: str, priority: int)
```

Add a blocked run to the escalation queue (WP-3008).

---

## govern_escalate_approve

```python
govern_escalate_approve(run_id: Any)
```

Approve an escalation, recording an override for the owner (G-GP-05).

---

## govern_escalate_list

```python
govern_escalate_list(past_sla_only: bool, limit: int, format: Any)
```

List governance escalation queue.

---

## govern_escalate_resolve

```python
govern_escalate_resolve(run_id: Any, resolution: str)
```

Mark an escalation item as resolved.

---

## govern_guardrails_check

```python
govern_guardrails_check(prompt: str, agent: Any, model: Any)
```

Check a prompt against active guardrails (FR-GOV-003..006).

---

## govern_guardrails_show

Show active guardrail configuration (FR-GOV-007).

---

## govern_hook_watcher

```python
govern_hook_watcher(project_dir: Path, interval: int, foreground: bool)
```

P8: Start hook cache watcher daemon — pre-warms caches on file changes.

---

## govern_interruption_list

```python
govern_interruption_list(limit: int, format: Any)
```

List recent interruptions with taxonomy and fatigue score.

---

## govern_interruption_snooze

```python
govern_interruption_snooze(alert_id: str, minutes: int, type: str)
```

Snooze an alert; auto-escalates when expired.

---

## govern_migration

```python
govern_migration(contract_id: str, version: str, format: Any)
```

Evaluate migration status for a contract version.

---

## govern_negotiate

```python
govern_negotiate(contract_id: str, supported: str, format: Any)
```

Negotiate a contract version (WP-7001).

---

## govern_purge

```python
govern_purge(dry_run: bool)
```

WP-3006: Tiered retention purge (G-GP-07).

---

## govern_release_pack

```python
govern_release_pack(version: str)
```

Automated release documentation packaging (WP-12009).

---

## govern_roadmap

Successor roadmap generation (WP-6004).

---

## govern_self_heal_tests

```python
govern_self_heal_tests(test_output: Any)
```

Self-healing test suite: automated fix recommendations (WP-6006).

---

## govern_signatures_list

```python
govern_signatures_list(limit: int, format: Any)
```

List signed MAIF artifacts (WP-3002).

---

## govern_signatures_verify

```python
govern_signatures_verify(run_id: str)
```

Verify a signed MAIF artifact (WP-3002).

---

## govern_sweep

```python
govern_sweep(drift_window: int, include_audit: bool, format: Any)
```

WP-3005: Policy drift sweep - drift detection, budget check, past-SLA escalations (cron-ready).

---

## govern_trend_analysis

Detailed contract trend analysis (WP-7009/7010).

---

## govern_trust_status

```python
govern_trust_status(format: Any)
```

Show last environment and trust boundary status (WP-3007).

---

## hierarchy_relationships

```python
hierarchy_relationships(agent_id: str)
```

Show agent relationships.

---

## hierarchy_show

```python
hierarchy_show(agent_id: str, team_id: str, format: str)
```

Show agent hierarchy.

---

## hierarchy_tree

```python
hierarchy_tree(root_id: str)
```

Show hierarchy tree structure.

---

## history_audit_verify

```python
history_audit_verify(format: Any)
```

Verify the integrity of the execution run registry.

---

## history_events

```python
history_events(limit: int, run_id: Any, format: Any)
```

List raw telemetry events.

---

## history_legacy

```python
history_legacy(limit: int, format: Any, events: bool, run_id: Any)
```

List execution run history (sync and background).

---

## history_list

```python
history_list(limit: int, format: Any)
```

List execution run history (sync and background).

---

## history_root

```python
history_root(ctx: typer.Context, limit: int, format: Any)
```

Default `history` behavior: list runs when no subcommand is provided.

---

## inbox_list

```python
inbox_list(owner: Any, agent: Any, event_type: Any, status: Any, sources: Any, limit: int, format: Any)
```

List unified inbox events with optional filters.

---

## inbox_root

```python
inbox_root(ctx: typer.Context, owner: Any, agent: Any, event_type: Any, status: Any, sources: Any, limit: int, format: Any)
```

Default: list recent inbox events. Use 'inbox wait' to block until new event.

---

## inbox_wait

```python
inbox_wait(owner: Any, agent: Any, event_type: Any, status: Any, sources: Any, poll: float, timeout: float, notify: bool, format: Any)
```

Wait for next inbox event matching filters. Blocks until new event or timeout.

---

## init_cmd

```python
init_cmd(url: str, cli: bool)
```

Initialize thegent: configure MCP clients and background services.

---

## inspect

```python
inspect(session_ids: list[str], owner: Any, tail: int, stderr: bool, format: Any, include_contract: bool)
```

Show status and logs for one or more sessions. No shell loop needed.

---

## install_cmd

```python
install_cmd(target: str, prefix: Any, editable: bool, force: bool, undo: bool, interactive: bool, wizard: bool, service: bool, dry_run: bool, verbose: bool, url: str, bundle: list[str], bundle_manifest: Any, list_bundles: bool, validate_bundles: bool, bundle_conflict_policy: Any, system_deps: bool, use_nix: bool)
```

Managed installation of thegent components and MCP configuration.

---

## install_shims_cmd

```python
install_shims_cmd(bin_dir: Path, force: bool, all_tools: bool, system: bool, prefix: Any, uninstall: bool)
```

MTSP-10: Install optimized accelerators (shims) for common tools.

Accelerates git (multi-tenant), grep (rg), find (fd), jq (jaq).
Use --system to install git wrapper to /usr/local/bin for nix/direnv compatibility.

---

## leaderboard_cmd

```python
leaderboard_cmd(provider: Any, min_score: Any, limit: int)
```

Show model leaderboard by composite performance score.

---

## learning_list

List all candidate models in the learning registry.

---

## learning_promote

```python
learning_promote(model_id: str, approver: str)
```

Promote a candidate model to 'promoted' status (WP-14003).

---

## learning_rollback

```python
learning_rollback(model_id: str)
```

Rollback a promoted or candidate model (WP-14003).

---

## ledger_verify

Verify the integrity of the immutable incident ledger (WP-15002).

---

## list_agents

List available providers.

---

## list_droids

```python
list_droids(cd: Any)
```

List available droids.

---

## list_model_indices_cmd

```python
list_model_indices_cmd(provider: Any, sort_by: str, format: str, show_modalities: bool)
```

List models with context limits, cost ($/Mtok), speed (tps), and benchmarks.

---

## list_models

```python
list_models(provider: Any, by_model: bool, refresh: bool, include_contract: bool)
```

List known models (optionally filtered by provider).

---

## list_providers_cmd

```python
list_providers_cmd(format: str)
```

List all configured providers.

---

## lock_resource

```python
lock_resource(resource: str, agent: str, ttl: int, cd: Any)
```

Acquire an exclusive lock on a resource (non-worktree).

---

## login

```python
login(provider: str, force: bool)
```

Run login for provider. Alias for `thegent cliproxy login`. Unified: open URL + prompt for key.

---

## logs

```python
logs(session_id: Any, follow: bool, stderr: bool, tail: int, timeout: int)
```

Print session logs.

---

## loop

```python
loop(prompt: str, todo_spec: str, agent: Any, checker: str, mode: str, cd: Any)
```

Run a Lifecycle loop with Checker oversight.

---

## loop_send

```python
loop_send(session_id: Any, prompt: str)
```

Send prompt to a running loop. Human or agent can use this to inject the next instruction.

---

## loop_stop

```python
loop_stop(session_id: Any)
```

Send STOP signal to a running Lifecycle loop.

---

## lsp_auto_setup

```python
lsp_auto_setup(install_missing: bool, install_all: bool, auto_configure: bool)
```

Auto-setup all IDE integrations (JetBrains, Serena, Ghostty).

---

## lsp_format

```python
lsp_format(files: list[Path], project: Any)
```

Format files using JetBrains formatter.

---

## lsp_inspect

```python
lsp_inspect(project: Path, profile: Any)
```

Run code inspections using JetBrains.

---

## lsp_install

```python
lsp_install(language: Any, all_languages: bool, auto_confirm: bool)
```

Install LSP servers (specific language or all missing).

---

## lsp_list

```python
lsp_list(all_servers: bool)
```

List LSP servers (running or all available).

---

## lsp_serena_backend

Show detected Serena backend (LSP or JetBrains plugin).

---

## lsp_serena_jetbrains_setup

Auto-detect and guide setup for Serena JetBrains plugin.

---

## lsp_start

```python
lsp_start(language: str, auto_install: Any)
```

Start headless LSP server for language (auto-installs if missing by default).

---

## lsp_stop

```python
lsp_stop(language: str)
```

Stop LSP server for language.

---

## mcp_down_cmd

Stop MCP + proxy (process-compose).

---

## mcp_fix

```python
mcp_fix(client: str, workspace: Any)
```

Remove failing MCP servers (`playwright`) that cause 'MCP startup incomplete'.

Use thegent's bundled mounts instead. Run 'thegent mcp up' before using.

---

## mcp_install

```python
mcp_install(client: str, url: Any, workspace: Any, replace_playwright: bool, uni_mount: bool, http: bool)
```

Add thegent to MCP config for Cursor, Claude Code, Codex, or Claude Desktop. Bundles browser tools (playwright) by default.

---

## mcp_introspect

```python
mcp_introspect(json_output: bool, optimize: bool)
```

Introspect agent processes (Python, node, droid, claude, codex).

Checks parent chain for true orphans; does NOT assume leak. Use before prune.

---

## mcp_migrate_unimount

```python
mcp_migrate_unimount(client: str, url: Any, workspace: Any)
```

Migrate to uni-mount: keep existing MCP entries and ensure `thegent` + `codex_apps` use the uni-mount URL. Use this to normalize legacy and partially-migrated projects.

Thegent mounts playwright, serena, octocode — one URL, all tools. Run 'thegent mcp up' before using.

---

## mcp_prune

```python
mcp_prune(force: bool, dry_run: bool)
```

Kill redundant agent-related Node.js processes (LSPs, MCP servers, cc-status).

Use this when memory usage is high (>10GB) and many orphan processes are detected.
For automatic pruning on Stop, set THGENT_AUTO_PRUNE=1.

---

## mcp_prune_periodic

```python
mcp_prune_periodic(action: str)
```

Install periodic prune daemon (launchd on macOS, systemd on Linux).

Runs thegent mcp prune --force every 15 min. Catches orphans when Stop doesn't fire (headless, Codex).

---

## mcp_restart_cmd

Hot reload: restart MCP + proxy (down then up).

---

## mcp_service

```python
mcp_service(action: str)
```

Manage thegent MCP HTTP server as launchd service (macOS). Start server before clients connect.

---

## mcp_spotlight_exclude

```python
mcp_spotlight_exclude(force: bool)
```

Exclude heavy development and thegent metadata directories from Spotlight indexing (macOS).

Helps reduce mds_stores memory usage and CPU spikes during high-IO agent runs.

---

## mcp_stdio

Start the MCP server in stdio mode (for Claude Code).

---

## mcp_up_cmd

```python
mcp_up_cmd(reload: bool)
```

Start MCP + proxy via process-compose (bundled mode).

---

## memory_add_cmd

```python
memory_add_cmd(content: str, cat: str, scope: str)
```

MTSP-17: Manually record a memory fragment.

---

## memory_garden_cmd

MEM-AUD-02: Run the Gardener agent to prune memory into documentation.

---

## memory_issue

```python
memory_issue(content: str)
```

Shortcut for memory add --category issue.

---

## memory_remember

```python
memory_remember(content: str)
```

Shortcut for memory add --category note.

---

## memory_rule

```python
memory_rule(content: str, negative: bool)
```

Shortcut for memory add --category lesson_positive/negative.

---

## memory_scrape_cmd

MTSP-18: Scrape session history and record prompts to audit log.

---

## memory_synthesize_cmd

MTSP-17: Generate a synthesis report from the audit log.

---

## mgmt_ensure_proxy

```python
mgmt_ensure_proxy(timeout: float)
```

Ensure MCP + proxy are running. Starts via process-compose if needed. Agent self-service.

---

## mgmt_verify_codex_cliproxy

```python
mgmt_verify_codex_cliproxy(model: str, prompt: str, timeout: float)
```

Verify Codex works with CLIProxy adapter. Agent self-service: no user intervention needed.

---

## models_contract

Show route contract metadata for model catalog consumers.

---

## models_cost_values

```python
models_cost_values(format: Any)
```

Show cost values ($/1k tokens) for all model-provider pairs. Uses proxy metrics when reachable.

---

## models_metrics

```python
models_metrics(format: Any, no_cache: bool, limit: int)
```

Show cost, speed, and quality for all model-provider pairs (unified view).

---

## models_quality_index

```python
models_quality_index(format: Any, no_cache: bool)
```

Show quality index (0-1) for all models. Uses benchmarks.json (TB2.0, SWE-Bench, AIME).

---

## models_refresh

Invalidate models, speed-index, and quality-index caches. Next lookup will re-fetch.

---

## models_setup_cmd

Rich TUI for adding models and providers with full harness configuration.

---

## models_speed_index

```python
models_speed_index(format: Any, no_cache: bool)
```

Show speed index (0-1) for all model-provider pairs. Uses proxy metrics when reachable.

---

## modes

```python
modes(format: Any, mode: Any)
```

List multi-agent orchestration modes (G-KD-04).

---

## mutex_cmd

```python
mutex_cmd(resource: str, agent: str, ttl: int, cd: Any, command: List[str])
```

Run a command under a resource-specific lock.

---

## observe_cost_status

```python
observe_cost_status(format: Any)
```

Show cost budget utilization and cost-aware routing status (WP-5003).

---

## observe_dlq

```python
observe_dlq(status: Any, format: Any)
```

List items in the Dead-Letter Queue (WP-Y2/WP-2008).

---

## observe_drift

```python
observe_drift(window: int, structural_budget: float, semantic_budget: float, format: Any)
```

Detect significant drift in contract performance and check alert budgets (G-RV-07).

---

## observe_drift_monitor

```python
observe_drift_monitor(prompt: str, agents: str)
```

Cross-provider drift monitoring (WP-6002).

---

## observe_kpis

```python
observe_kpis(limit: int, format: Any)
```

Show fallback KPIs for dashboard/alerting (G-CA-02 B3).

---

## observe_load_status

```python
observe_load_status(format: Any)
```

Show load classification and safe-mode status (WP-5002).

---

## observe_summary

```python
observe_summary(limit: int, drift_window: int, structural_budget: float, semantic_budget: float, provider: Any, trend_samples: int, top_escalations: int, format: Any)
```

FR-X08: Unified observability summary (KPIs, drift, escalation).

---

## observe_traffic

TRAFFIC KPI Dashboard (WP-Y7).

---

## observe_trend

```python
observe_trend(payload_type: str, all_sessions: bool, owner: Any, strict: bool, limit: int, format: Any)
```

Read health trend snapshots for a report/gate policy scope.

---

## observe_usage

```python
observe_usage(format: Any, no_cost: bool)
```

Show plan usage: provider metrics from CLIProxyAPIPlus and cost status.

---

## operations

```python
operations(format: Any, operation: Any)
```

List universal operation taxonomy (orchestrate, govern, recover, observe, plan).

---

## orchestrate_fallbacks

```python
orchestrate_fallbacks(run_id: Any)
```

Show safe fallback options for a failed run (WP-4003).

---

## orchestrate_handoff

```python
orchestrate_handoff(owner: str)
```

Create a continuity snapshot for a shift handoff (WP-4006, WP-3008).

---

## orchestrate_handoff_confirm

```python
orchestrate_handoff_confirm(snapshot_id: str, incoming_owner: str, confidence: float)
```

Incoming owner confirms handoff completeness (WP-3008, WP-4006).

---

## orchestrate_handoff_list

```python
orchestrate_handoff_list(limit: int, format: Any)
```

List pending handoff snapshots (WP-4006).

---

## orchestrate_handoff_show

```python
orchestrate_handoff_show(snapshot_id: str, format: Any)
```

Show full handoff summary: state, evidence, next steps (WP-4006).

---

## orchestrate_replay

```python
orchestrate_replay(run_id: str, what_if_env: Any)
```

Decision replay and rationale snapshots (WP-4007).

---

## orchestrate_watchdog

```python
orchestrate_watchdog(max_idle: int)
```

Scan for stale sessions and recommend handoffs (WP-5005).

---

## pause

```python
pause(session_id: Any)
```

Mark a session as PAUSED in the registry (HITL).

---

## plan_analyze

```python
plan_analyze(cd: Any, pert: bool, resources: bool, continuity: bool, format: Any)
```

Run planning simulation overlays (XD1–XD3): PERT, resources, continuity risk.

---

## plan_claim

```python
plan_claim(item_id: str, agent_id: Any, cd: Any)
```

Claim an item in the unified work stream.

---

## plan_complete

```python
plan_complete(item_id: str, agent_id: Any, cd: Any)
```

Mark an item as complete in the unified work stream.

---

## plan_do_next

```python
plan_do_next(cd: Any, limit: int, format: Any)
```

Find next actionable work items from PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

**Examples**:

```python
thegent plan next
thegent plan next -l 10
thegent run free "$(thegent plan get-next)"
```

---

## plan_get_next

```python
plan_get_next(cd: Any, format: Any)
```

Get first work item prompt for scripting. Use: PROMPT=$(thegent plan get-next)

---

## plan_incorporate

```python
plan_incorporate(cd: Any, dry_run: bool)
```

Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md. Preserves CLAIMED and COMPLETED.

---

## plan_loop

```python
plan_loop(cd: Any, max_iterations: int, sleep_seconds: float, agent: str, dry_run: bool)
```

Loop: get next item -> run bg -> repeat until no items or --max reached.

---

## plan_progress

```python
plan_progress(limit: int, format: Any)
```

Show recent runs (work-package progress). Alias for history --limit N.

---

## plan_spawn_next

```python
plan_spawn_next(cd: Any, limit: int, agent: str, timeout: Any, dry_run: bool, format: Any)
```

Spawn N next work items in background (parallel batch). Manages 10-20 items alongside other agent managers.

---

## plan_wait_next

```python
plan_wait_next(cd: Any, poll: float, timeout: float, sources: Any, format: Any)
```

Block until next actionable work exists (DAG ready, do_next, escalation, inbox).

---

## policy_check

```python
policy_check(agent: str, model: Any, lane: str, confidence: float)
```

Evaluate a hypothetical run against governance policies (WP-3001).

---

## policy_purge

```python
policy_purge(dry_run: bool)
```

Purge expired history based on tiered retention (WP-3006).

---

## policy_show

Show active governance policies and thresholds.

---

## project_list

List all registered projects.

---

## project_register

```python
project_register(path: Path, name: Any)
```

Register a project in the global registry.

---

## provider_cmd

Interactive provider and model management (CRUD).

---

## ps

```python
ps(all_sessions: bool, owner: Any, format: Any, include_contract: bool, scan_ide: bool)
```

List registered background sessions.

---

## queue_list

```python
queue_list(watch: bool)
```

List pending prompts in the queue.

---

## recover_status

Show recovery stability and suggested playbooks.

---

## research

```python
research(prompt: str, cd: Any, bg: bool, model: Any, timeout: Any)
```

Deep dive research and comprehensive information gathering.

---

## resolve_model_route

```python
resolve_model_route(model: str, provider: Any, policy: str, quality_floor: float, lane: Any)
```

Resolve a model to a concrete provider+alias route.

---

## restore_backup_cmd

```python
restore_backup_cmd(backup_file: str, list_backups_flag: bool, cleanup: bool, keep: int)
```

Restore shell config from backup or manage backups.

---

## resume

```python
resume(session_id: Any)
```

Mark a paused session as RUNNING in the registry (HITL).

---

## retry

```python
retry(run_id: Any, agent: Any, failover: bool, cd: Any, override: Any)
```

Retry a failed run. With no run_id, list recent failed runs.

---

## review

```python
review(prompt: str, cd: Any, bg: bool, model: Any, timeout: Any)
```

Critical analysis and quality checks for code or documentation.

---

## route_probe

```python
route_probe(model: str, provider: Any, policy: str, quality_floor: float, lane: Any)
```

Dry-run route resolution: show which provider would be selected (DX-004). Alias for resolve-model-route.

---

## rules_sync

```python
rules_sync(force: bool, check: bool, cd: Any)
```

Sync CLAUDE.md to other platform-specific rule files (AGENTS.md, Cursor, Codex).

---

## run

```python
run(prompt: str, agent: Any, cd: Any, retry_run: bool, mode: str, timeout: Any, full: bool, live: bool, model: Any, provider: Any, failover: bool, routing: Any, include_contract: bool, run_id: Any, lane: str, idempotency_token: Any, confidence: Any, arbitration: Any, override: Any, contract_version: Any, domain: Any, speculative: bool, search: bool, debug: bool, task_id: Any, shadow: bool, lock: Optional[List[str]])
```

Run a foreground agent invocation. Use -M `<model>` without agent for model-first routing.

**Examples**:

```python
thegent run free "Fix bug in auth.py"
thegent run free "Implement feature" --model gemini-3-flash
thegent run free "Review code" --mode read-only
```

---

## run_diff

```python
run_diff(run_a: str, run_b: str)
```

Compare two execution runs (trace comparison).

---

## search_modalities_cmd

```python
search_modalities_cmd(required: list[str], provider: Any, sort_by: str)
```

Search models by modality requirements.

---

## search_models_cmd

```python
search_models_cmd(capability: str, min_context: Any, min_tps: Any, max_cost: Any)
```

Search models by capability (reasoning, vision, or benchmark score).

---

## serve

```python
serve(host: Any, port: Any, force: bool, http: bool, reload: bool)
```

Start the MCP server. Defaults to HTTP. Delegates to launchd/Homebrew service when available.

---

## session_contract_health_gate

```python
session_contract_health_gate(all_sessions: bool, owner: Any, format: Any, strict: bool, min_healthy_ratio: float, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float, output: Any, export_format: Any, overwrite: bool)
```

Fail if routing contract health is below threshold.

---

## session_contract_health_report

```python
session_contract_health_report(all_sessions: bool, owner: Any, format: Any, strict: bool, top_blocked: int, policy_profile: Any, no_worse_than_baseline: bool, regression_tolerance: float, output: Any, export_format: Any, overwrite: bool)
```

Create a policy-friendly session contract health report with issue and owner breakdown.

---

## session_contract_health_trend

```python
session_contract_health_trend(payload_type: str, all_sessions: bool, owner: Any, strict: bool, policy_profile: Any, min_healthy_ratio: float, top_blocked: int, limit: int, format: Any, output: Any, export_format: Any, overwrite: bool)
```

Read health trend snapshots for a report/gate policy scope.

---

## session_contracts

```python
session_contracts(all_sessions: bool, owner: Any, format: Any, missing_only: bool, summary_only: bool, strict: bool)
```

Audit session routing contract metadata coverage and completeness.

---

## show_modalities_cmd

```python
show_modalities_cmd(provider: Any, model: Any)
```

Show modality/feature flags for models.

---

## sitback_dashboard

```python
sitback_dashboard(refresh: Any, format: Any, profile: str)
```

Unified sitback dashboard: sessions, cockpit, terminals. CLI mirror of MCP tool.

---

## status

```python
status(session_id: Any, format: Any, include_contract: bool)
```

Show one session status.

---

## stop

```python
stop(session_id: Any, force: bool, wind_down: bool, grace: int)
```

Stop a running session.

---

## summarize

```python
summarize(prompt: str, cd: Any, bg: bool, model: Any, timeout: Any)
```

Summarize content with brevity and key takeaways.

---

## takeover

```python
takeover(session_id: str)
```

Attach to an interactive tmux session (takeover).

---

## team_create

```python
team_create(name: str, leader: str, teammates: str)
```

Create a new multi-agent team.

---

## team_task_add

```python
team_task_add(team_id: str, title: str, description: str)
```

Add a task to a team's backlog.

---

## team_task_list

```python
team_task_list(team_id: str)
```

List all tasks for a team.

---

## teammates_delegate

```python
teammates_delegate(teammate_id: str, prompt: str, parent_run_id: str)
```

Delegate a sub-task to a specialized teammate (WP-16002).

---

## teammates_list

List all discovered specialized agents available for delegation (WP-16001).

---

## teammates_status

```python
teammates_status(run_id: str)
```

Monitor the status of the teammate swarm (WP-16002).

---

## teams_add_member

```python
teams_add_member(team_id: str, agent_run_id: str)
```

Add member to team.

---

## teams_create

```python
teams_create(team_id: str, name: str, description: str, team_type: str, coordination_mode: str, lead_id: str)
```

Create a new team.

---

## teams_list

List all teams.

---

## teams_remove_member

```python
teams_remove_member(team_id: str, agent_run_id: str)
```

Remove member from team.

---

## teams_show

```python
teams_show(team_id: str)
```

Show team details.

---

## terminal_explorer

Launch the terminal explorer TUI.

---

## terminal_route

```python
terminal_route(prompt: str, cd: Any)
```

Route task to an active terminal session if available.

---

## trace_replay

```python
trace_replay(run_id: str)
```

Replay an execution trace in simulation mode (WP-16001).

---

## uninstall_system_deps_cmd

```python
uninstall_system_deps_cmd(remove_hooks: bool, uninstall_mise: bool, dry_run: bool, verbose: bool)
```

Uninstall system dependencies: remove mise hooks and optionally uninstall mise.

---

## unlock_resource

```python
unlock_resource(resource: str, token: str, agent: str, cd: Any)
```

Release an exclusive lock on a resource.

---

## upgrade_cmd

```python
upgrade_cmd(check_only: bool)
```

Check for newer thegent version and print upgrade instructions.

---

## validate_provider_cmd

```python
validate_provider_cmd(name: str)
```

Validate a provider by testing connectivity.

---

## wait

```python
wait(session_id: Any, timeout: int)
```

Wait for session completion and return session exit code.

---

## wait_next

```python
wait_next(cd: Any, poll: float, timeout: float, sources: Any, format: Any)
```

Block until next actionable work exists. Does not return until DAG ready, work item, escalation, or inbox event.

---

## workstream_dashboard

Launch workstream dashboard TUI.

---

## workstream_query

```python
workstream_query(query: str)
```

Execute SQL query on workstream database.

---

## workstream_stats

Get workstream statistics.

---
