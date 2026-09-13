# CLI Command Reference

## `thegent -run-role`

**Description**: Run a task with a specific role-based system prompt.

**Usage**:

```bash
thegent -run-role [options]
```

**Options**:

- `--role` - Parameter
- `--prompt` - Parameter
- `--cd` - Parameter
- `--mode` - Parameter
- `--timeout` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--agent` - Parameter
- `--owner` - Parameter
- `--live` - Parameter
- `--full` - Parameter

---

## `thegent add`

**Description**: Add a blocked run to the escalation queue (WP-3008).

**Usage**:

```bash
thegent add [options]
```

**Options**:

- `--run-id` - Parameter
- `--reason` - Parameter
- `--sla-minutes` - Parameter
- `--owner` - Parameter
- `--lane` - Parameter
- `--priority` - Parameter

---

## `thegent add`

**Description**: Add a task to the DAG.

**Usage**:

```bash
thegent add [options]
```

**Options**:

- `--task-id` - Parameter
- `--agent` - Parameter
- `--prompt` - Parameter
- `--cd` - Parameter
- `--depends-on` - Parameter
- `--contract-version` - Parameter

---

## `thegent add`

**Description**: MTSP-17: Manually record a memory fragment.

**Usage**:

```bash
thegent add [options]
```

**Options**:

- `--content` - Parameter
- `--cat` - Parameter
- `--scope` - Parameter

---

## `thegent add-task`

**Description**: Add a task to a team's backlog.

**Usage**:

```bash
thegent add-task [options]
```

**Options**:

- `--team-id` - Parameter
- `--title` - Parameter
- `--description` - Parameter

---

## `thegent analyze`

**Description**: Run planning simulation overlays (XD1–XD3): PERT, resources, continuity risk.

**Usage**:

```bash
thegent analyze [options]
```

**Options**:

- `--cd` - Parameter
- `--pert` - Parameter
- `--resources` - Parameter
- `--continuity` - Parameter
- `--format` - Parameter

---

## `thegent approve`

**Description**: Approve an escalation, recording an override for the owner (G-GP-05).

**Usage**:

```bash
thegent approve [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent archive`

**Description**: Archive old sessions (WP-6005). WP-3006: tiered retention (hot 30d, cold 1yr).

**Usage**:

```bash
thegent archive [options]
```

**Options**:

- `--days` - Parameter
- `--domain` - Parameter
- `--tier` - Parameter

---

## `thegent benchmark`

**Description**: Report orchestration performance metrics (WP-6001).

**Usage**:

```bash
thegent benchmark
```

---

## `thegent bg`

**Description**: Start a background run and register a session.

**Usage**:

```bash
thegent bg [options]
```

**Options**:

- `--prompt` - Parameter
- `--agent` - Parameter
- `--cd` - Parameter
- `--mode` - Parameter
- `--timeout` - Parameter
- `--full` - Parameter
- `--owner` - Parameter
- `--model` - Parameter
- `--provider` - Parameter
- `--routing` - Parameter
- `--failover` - Parameter
- `--format` - Parameter
- `--include-contract` - Parameter
- `--continuation` - Parameter
- `--continuation-stderr` - Parameter
- `--run-id` - Parameter
- `--lane` - Parameter
- `--idempotency-token` - Parameter
- `--confidence` - Parameter
- `--arbitration` - Parameter
- `--override` - Parameter
- `--contract-version` - Parameter
- `--domain` - Parameter
- `--speculative` - Parameter
- `--debug` - Parameter

---

## `thegent calibrate`

**Description**: Recalculate trust score calibration factors for all agents (G-GP-09).

**Usage**:

```bash
thegent calibrate
```

---

## `thegent cancel`

**Description**: Set task status to cancelled.

**Usage**:

```bash
thegent cancel [options]
```

**Options**:

- `--task-id` - Parameter
- `--cd` - Parameter

---

## `thegent check`

**Description**: Validate config; fail-fast on misconfig (DX-010, ROB-013).

**Usage**:

```bash
thegent check [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent check`

**Description**: Check a prompt against active guardrails (FR-GOV-003..006).

**Usage**:

```bash
thegent check [options]
```

**Options**:

- `--prompt` - Parameter
- `--agent` - Parameter
- `--model` - Parameter

---

## `thegent check-policy`

**Description**: Evaluate a hypothetical run against governance policies (WP-3001).

**Usage**:

```bash
thegent check-policy [options]
```

**Options**:

- `--agent` - Parameter
- `--model` - Parameter
- `--lane` - Parameter
- `--confidence` - Parameter

---

## `thegent checkpoint`

**Description**: Create a point-in-time checkpoint of the DAG state.

**Usage**:

```bash
thegent checkpoint [options]
```

**Options**:

- `--cd` - Parameter
- `--reason` - Parameter

---

## `thegent checkpoints`

**Description**: List recent DAG checkpoints.

**Usage**:

```bash
thegent checkpoints [options]
```

**Options**:

- `--limit` - Parameter

---

## `thegent claim`

**Description**: Claim an item in the unified work stream.

**Usage**:

```bash
thegent claim [options]
```

**Options**:

- `--item-id` - Parameter
- `--agent-id` - Parameter
- `--cd` - Parameter

---

## `thegent closure-pack`

**Description**: Generate a formal closure pack for the current DAG session (WP-6002/6008/FR-024).

**Usage**:

```bash
thegent closure-pack [options]
```

**Options**:

- `--cd` - Parameter

---

## `thegent cockpit`

**Description**: Show high-level operator cockpit summary.

**Usage**:

```bash
thegent cockpit
```

---

## `thegent code`

**Description**: Feature implementation and coding tasks.

**Usage**:

```bash
thegent code [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--timeout` - Parameter

---

## `thegent complete`

**Description**: Mark an item as complete in the unified work stream.

**Usage**:

```bash
thegent complete [options]
```

**Options**:

- `--item-id` - Parameter
- `--agent-id` - Parameter
- `--cd` - Parameter

---

## `thegent compliance-report`

**Description**: Generate compliance evidence retention report (WP-3006).

**Usage**:

```bash
thegent compliance-report [options]
```

**Options**:

- `--format` - Parameter
- `--output` - Parameter

---

## `thegent configure`

**Description**: Bootstrap governance: create contracts/health-targets.json if missing.

**Usage**:

```bash
thegent configure [options]
```

**Options**:

- `--cd` - Parameter
- `--force` - Parameter

---

## `thegent conformance`

**Description**: Run provider adapter conformance tests.

**Usage**:

```bash
thegent conformance [options]
```

**Options**:

- `--format` - Parameter
- `--check-drift` - Parameter
- `--drift-window` - Parameter

---

## `thegent contract`

**Description**: Show route contract metadata for model catalog consumers.

**Usage**:

```bash
thegent contract
```

---

## `thegent contracts`

**Description**: Show the contract registry and compatibility matrix.

**Usage**:

```bash
thegent contracts [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent cost`

**Description**: Show daily cost aggregation (FR-GOV-002).

**Usage**:

```bash
thegent cost [options]
```

**Options**:

- `--owner` - Parameter
- `--days` - Parameter
- `--format` - Parameter

---

## `thegent cost-status`

**Description**: Show cost budget utilization and cost-aware routing status (WP-5003).

**Usage**:

```bash
thegent cost-status [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent cost-values`

**Description**: Show cost values ($/1k tokens) for all model-provider pairs. Uses proxy metrics when reachable.

**Usage**:

```bash
thegent cost-values [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent create`

**Description**: Create a new multi-agent team.

**Usage**:

```bash
thegent create [options]
```

**Options**:

- `--name` - Parameter
- `--leader` - Parameter
- `--teammates` - Parameter

---

## `thegent cycle`

**Description**: Run a single governance cycle.

**Usage**:

```bash
thegent cycle [options]
```

**Options**:

- `--cd` - Parameter
- `--force` - Parameter
- `--format` - Parameter

---

## `thegent dag-recover`

**Description**: Perform recovery playbook actions on the DAG.

**Usage**:

```bash
thegent dag-recover [options]
```

**Options**:

- `--action` - Parameter
- `--cd` - Parameter

---

## `thegent dashboard`

**Description**: Show financial safety dashboard (WP-Y1).

**Usage**:

```bash
thegent dashboard
```

---

## `thegent data-protection`

**Description**: Show data protection and privacy controls status (WP-3006).

**Usage**:

```bash
thegent data-protection [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent delegate`

**Description**: Delegate a sub-task to a specialized teammate (WP-16002).

**Usage**:

```bash
thegent delegate [options]
```

**Options**:

- `--teammate-id` - Parameter
- `--prompt` - Parameter
- `--parent-run-id` - Parameter

---

## `thegent dlq`

**Description**: List items in the Dead-Letter Queue (WP-Y2/WP-2008).

**Usage**:

```bash
thegent dlq [options]
```

**Options**:

- `--status` - Parameter
- `--format` - Parameter

---

## `thegent do-next`

**Description**: Find next actionable work items from PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

**Usage**:

```bash
thegent do-next [options]
```

**Options**:

- `--cd` - Parameter
- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent drift`

**Description**: Detect significant drift in contract performance and check alert budgets (G-RV-07).

**Usage**:

```bash
thegent drift [options]
```

**Options**:

- `--window` - Parameter
- `--structural-budget` - Parameter
- `--semantic-budget` - Parameter
- `--format` - Parameter

---

## `thegent drift-monitor`

**Description**: Cross-provider drift monitoring (WP-6002).

**Usage**:

```bash
thegent drift-monitor [options]
```

**Options**:

- `--prompt` - Parameter
- `--agents` - Parameter

---

## `thegent ensure-config`

**Description**: Ensure proxy config exists (port, auth-dir). Add provider blocks manually. Restart proxy to apply.

**Usage**:

```bash
thegent ensure-config
```

---

## `thegent ensure-proxy`

**Description**: Ensure MCP + proxy are running. Starts via process-compose if needed. Agent self-service.

**Usage**:

```bash
thegent ensure-proxy [options]
```

**Options**:

- `--timeout` - Parameter

---

## `thegent events`

**Description**: List raw telemetry events.

**Usage**:

```bash
thegent events [options]
```

**Options**:

- `--limit` - Parameter
- `--run-id` - Parameter
- `--format` - Parameter

---

## `thegent explain`

**Description**: Clarification and educational explanation of complex concepts.

**Usage**:

```bash
thegent explain [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--timeout` - Parameter

---

## `thegent explain`

**Description**: Show detailed explanation for an agent run (WP-4002).

**Usage**:

```bash
thegent explain [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent explorer`

**Description**: Launch the terminal explorer TUI.

**Usage**:

```bash
thegent explorer
```

---

## `thegent export`

**Description**: Export evidence bundle for SOC2, ISO27001, or EU-AI-ACT.

**Usage**:

```bash
thegent export [options]
```

**Options**:

- `--framework` - Parameter
- `--output` - Parameter

---

## `thegent fallbacks`

**Description**: Show safe fallback options for a failed run (WP-4003).

**Usage**:

```bash
thegent fallbacks [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent feedback`

**Description**: Provide operator feedback for a specific run.

**Usage**:

```bash
thegent feedback [options]
```

**Options**:

- `--run-id` - Parameter
- `--score` - Parameter
- `--note` - Parameter

---

## `thegent fix`

**Description**: Bug identification and resolution.

**Usage**:

```bash
thegent fix [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--timeout` - Parameter

---

## `thegent mcp fix`

**Description**: Remove failing MCP servers (`playwright`) that cause 'MCP startup incomplete'.

**Usage**:

```bash
thegent mcp fix [options]
```

**Options**:

- `--client` - Parameter
- `--workspace` - Parameter

---

## `thegent free`

**Description**: Base free tier: Copilot gpt-5-mini. Alias for thegent run "`<prompt>`" free.

**Usage**:

```bash
thegent free [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--mode` - Parameter
- `--timeout` - Parameter
- `--do-next` - Parameter
- `--repeat` - Parameter
- `--live` - Parameter
- `--bg` - Parameter
- `--diff` - Parameter

---

## `thegent garden`

**Description**: MEM-AUD-02: Run the Gardener agent to prune memory into documentation.

**Usage**:

```bash
thegent garden
```

---

## `thegent get-next`

**Description**: Get first work item prompt for scripting. Use: PROMPT=$(thegent plan get-next)

**Usage**:

```bash
thegent get-next [options]
```

**Options**:

- `--cd` - Parameter
- `--format` - Parameter

---

## `thegent handoff`

**Description**: Create a continuity snapshot for a shift handoff (WP-4006, WP-3008).

**Usage**:

```bash
thegent handoff [options]
```

**Options**:

- `--owner` - Parameter

---

## `thegent handoff-confirm`

**Description**: Incoming owner confirms handoff completeness (WP-3008, WP-4006).

**Usage**:

```bash
thegent handoff-confirm [options]
```

**Options**:

- `--snapshot-id` - Parameter
- `--incoming-owner` - Parameter
- `--confidence` - Parameter

---

## `thegent handoff-list`

**Description**: List pending handoff snapshots (WP-4006).

**Usage**:

```bash
thegent handoff-list [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent handoff-show`

**Description**: Show full handoff summary: state, evidence, next steps (WP-4006).

**Usage**:

```bash
thegent handoff-show [options]
```

**Options**:

- `--snapshot-id` - Parameter
- `--format` - Parameter

---

## `thegent health`

**Description**: Show current health score (composite 0-100, band, per-dimension breakdown).

**Usage**:

```bash
thegent health [options]
```

**Options**:

- `--cd` - Parameter
- `--format` - Parameter

---

## `thegent health-gate`

**Description**: Fail if routing contract health is below threshold.

**Usage**:

```bash
thegent health-gate [options]
```

**Options**:

- `--all-sessions` - Parameter
- `--owner` - Parameter
- `--format` - Parameter
- `--strict` - Parameter
- `--min-healthy-ratio` - Parameter
- `--policy-profile` - Parameter
- `--no-worse-than-baseline` - Parameter
- `--regression-tolerance` - Parameter
- `--output` - Parameter
- `--export-format` - Parameter
- `--overwrite` - Parameter

---

## `thegent health-report`

**Description**: Create a policy-friendly session contract health report with issue and owner breakdown.

**Usage**:

```bash
thegent health-report [options]
```

**Options**:

- `--all-sessions` - Parameter
- `--owner` - Parameter
- `--format` - Parameter
- `--strict` - Parameter
- `--top-blocked` - Parameter
- `--policy-profile` - Parameter
- `--no-worse-than-baseline` - Parameter
- `--regression-tolerance` - Parameter
- `--output` - Parameter
- `--export-format` - Parameter
- `--overwrite` - Parameter

---

## `thegent health-trend`

**Description**: Read health trend snapshots for a report/gate policy scope.

**Usage**:

```bash
thegent health-trend [options]
```

**Options**:

- `--payload-type` - Parameter
- `--all-sessions` - Parameter
- `--owner` - Parameter
- `--strict` - Parameter
- `--policy-profile` - Parameter
- `--min-healthy-ratio` - Parameter
- `--top-blocked` - Parameter
- `--limit` - Parameter
- `--format` - Parameter
- `--output` - Parameter
- `--export-format` - Parameter
- `--overwrite` - Parameter

---

## `thegent history`

**Description**: List execution run history (sync and background).

**Usage**:

```bash
thegent history [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent history-legacy`

**Description**: List execution run history (sync and background).

**Usage**:

```bash
thegent history-legacy [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter
- `--events` - Parameter
- `--run-id` - Parameter

---

## `thegent hook-watcher`

**Description**: P8: Start hook cache watcher daemon — pre-warms caches on file changes.

**Usage**:

```bash
thegent hook-watcher [options]
```

**Options**:

- `--project-dir` - Parameter
- `--interval` - Parameter
- `--foreground` - Parameter

---

## `thegent inbox`

**Description**: List unified inbox events with optional filters.

**Usage**:

```bash
thegent inbox [options]
```

**Options**:

- `--owner` - Parameter
- `--agent` - Parameter
- `--event-type` - Parameter
- `--status` - Parameter
- `--sources` - Parameter
- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent incorporate`

**Description**: Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md. Preserves CLAIMED and COMPLETED.

**Usage**:

```bash
thegent incorporate [options]
```

**Options**:

- `--cd` - Parameter
- `--dry-run` - Parameter

---

## `thegent init`

**Description**: Initialize thegent: configure MCP clients and background services.

**Usage**:

```bash
thegent init [options]
```

**Options**:

- `--url` - Parameter
- `--cli` - Parameter

---

## `thegent inspect`

**Description**: Show status and logs for one or more sessions. No shell loop needed.

**Usage**:

```bash
thegent inspect [options]
```

**Options**:

- `--session-ids` - Parameter
- `--owner` - Parameter
- `--tail` - Parameter
- `--stderr` - Parameter
- `--format` - Parameter
- `--include-contract` - Parameter

---

## `thegent install`

**Description**: Add thegent to MCP config for Cursor, Claude Code, Codex, or Claude Desktop. Bundles browser tools (playwright) by default.

**Usage**:

```bash
thegent install [options]
```

**Options**:

- `--client` - Parameter
- `--url` - Parameter
- `--workspace` - Parameter
- `--replace-playwright` - Parameter
- `--uni-mount` - Parameter
- `--http` - Parameter

---

## `thegent install`

**Description**: Managed installation of thegent components and MCP configuration.

**Usage**:

```bash
thegent install [options]
```

**Options**:

- `--target` - Parameter
- `--editable` - Parameter
- `--force` - Parameter
- `--undo` - Parameter
- `--interactive` - Parameter
- `--wizard` - Parameter
- `--service` - Parameter
- `--dry-run` - Parameter
- `--verbose` - Parameter
- `--url` - Parameter
- `--bundle` - Parameter
- `--bundle-manifest` - Parameter
- `--list-bundles` - Parameter
- `--validate-bundles` - Parameter
- `--bundle-conflict-policy` - Parameter

---

## `thegent install-shims`

**Description**: MTSP-10: Install optimized accelerators (shims) for common tools.

**Usage**:

```bash
thegent install-shims [options]
```

**Options**:

- `--bin-dir` - Parameter
- `--force` - Parameter
- `--all-tools` - Parameter

---

## `thegent issue`

**Description**: Shortcut for memory add --category issue.

**Usage**:

```bash
thegent issue [options]
```

**Options**:

- `--content` - Parameter

---

## `thegent kpis`

**Description**: Show fallback KPIs for dashboard/alerting (G-CA-02 B3).

**Usage**:

```bash
thegent kpis [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent ledger-verify`

**Description**: Verify the integrity of the immutable incident ledger (WP-15002).

**Usage**:

```bash
thegent ledger-verify
```

---

## `thegent list`

**Description**: List all registered projects.

**Usage**:

```bash
thegent list
```

---

## `thegent list`

**Description**: List all currently deferred tasks.

**Usage**:

```bash
thegent list
```

---

## `thegent list`

**Description**: List all discovered specialized agents available for delegation (WP-16001).

**Usage**:

```bash
thegent list
```

---

## `thegent list`

**Description**: List signed MAIF artifacts (WP-3002).

**Usage**:

```bash
thegent list [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent list`

**Description**: List all candidate models in the learning registry.

**Usage**:

```bash
thegent list
```

---

## `thegent list`

**Description**: List all federated namespaces (WP-13005).

**Usage**:

```bash
thegent list
```

---

## `thegent list`

**Description**: List pending prompts in the queue.

**Usage**:

```bash
thegent list [options]
```

**Options**:

- `--watch` - Parameter

---

## `thegent list`

**Description**: List governance escalation queue.

**Usage**:

```bash
thegent list [options]
```

**Options**:

- `--past-sla-only` - Parameter
- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent list`

**Description**: List recent interruptions with taxonomy and fatigue score.

**Usage**:

```bash
thegent list [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent list`

**Description**: List available providers. Alias for thegent list-agents.

**Usage**:

```bash
thegent list
```

---

## `thegent list`

**Description**: Parse and display DAG session from .factory/dag-session.md.

**Usage**:

```bash
thegent list [options]
```

**Options**:

- `--cd` - Parameter
- `--format` - Parameter

---

## `thegent list-agents`

**Description**: List available providers.

**Usage**:

```bash
thegent list-agents
```

---

## `thegent list-droids`

**Description**: List available droids.

**Usage**:

```bash
thegent list-droids [options]
```

**Options**:

- `--cd` - Parameter

---

## `thegent list-models`

**Description**: List known models (optionally filtered by provider).

**Usage**:

```bash
thegent list-models [options]
```

**Options**:

- `--provider` - Parameter
- `--by-model` - Parameter
- `--refresh` - Parameter
- `--include-contract` - Parameter

---

## `thegent list-tasks`

**Description**: List all tasks for a team.

**Usage**:

```bash
thegent list-tasks [options]
```

**Options**:

- `--team-id` - Parameter

---

## `thegent load-status`

**Description**: Show load classification and safe-mode status (WP-5002).

**Usage**:

```bash
thegent load-status [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent login`

**Description**: Run login for provider. Unified flow: open URL + prompt for API key. Preflight checks existing credentials.

**Usage**:

```bash
thegent login [options]
```

**Options**:

- `--provider` - Parameter
- `--force` - Parameter

---

## `thegent login`

**Description**: Run login for provider. Alias for `thegent cliproxy login`. Unified: open URL + prompt for key.

**Usage**:

```bash
thegent login [options]
```

**Options**:

- `--provider` - Parameter
- `--force` - Parameter

---

## `thegent logs`

**Description**: Print session logs.

**Usage**:

```bash
thegent logs [options]
```

**Options**:

- `--session-id` - Parameter
- `--follow` - Parameter
- `--stderr` - Parameter
- `--tail` - Parameter
- `--timeout` - Parameter

---

## `thegent loop`

**Description**: Run a Lifecycle loop with Checker oversight.

**Usage**:

```bash
thegent loop [options]
```

**Options**:

- `--prompt` - Parameter
- `--todo-spec` - Parameter
- `--agent` - Parameter
- `--checker` - Parameter
- `--mode` - Parameter
- `--cd` - Parameter

---

## `thegent loop`

**Description**: Loop: get next item -> run bg -> repeat until no items or --max reached.

**Usage**:

```bash
thegent loop [options]
```

**Options**:

- `--cd` - Parameter
- `--max-iterations` - Parameter
- `--sleep-seconds` - Parameter
- `--agent` - Parameter
- `--dry-run` - Parameter

---

## `thegent loop-send`

**Description**: Send prompt to a running loop. Human or agent can use this to inject the next instruction.

**Usage**:

```bash
thegent loop-send [options]
```

**Options**:

- `--session-id` - Parameter
- `--prompt` - Parameter

---

## `thegent loop-stop`

**Description**: Send STOP signal to a running Lifecycle loop.

**Usage**:

```bash
thegent loop-stop [options]
```

**Options**:

- `--session-id` - Parameter

---

## `thegent mcp-down`

**Description**: Stop MCP + proxy (process-compose).

**Usage**:

```bash
thegent mcp-down
```

---

## `thegent mcp-stdio`

**Description**: Start the MCP server in stdio mode (for Claude Code).

**Usage**:

```bash
thegent mcp-stdio
```

---

## `thegent metrics`

**Description**: Show cost, speed, and quality for all model-provider pairs (unified view).

**Usage**:

```bash
thegent metrics [options]
```

**Options**:

- `--format` - Parameter
- `--no-cache` - Parameter
- `--limit` - Parameter

---

## `thegent migrate-unimount`

**Description**: Migrate to uni-mount: keep existing MCP entries and force `thegent` + `codex_apps` to the active MCP URL. Existing non-thegent tools remain available for mixed tooling flows.

Use this both for existing projects (brownfield) and partially/fully scaffolded new projects after MCP entries are created.

**Usage**:

```bash
thegent migrate-unimount [options]
```

**Options**:

- `--client` - Parameter
- `--url` - Parameter
- `--workspace` - Parameter

---

## `thegent migration`

**Description**: Evaluate migration status for a contract version.

**Usage**:

```bash
thegent migration [options]
```

**Options**:

- `--contract-id` - Parameter
- `--version` - Parameter
- `--format` - Parameter

---

## `thegent modes`

**Description**: List multi-agent orchestration modes (G-KD-04).

**Usage**:

```bash
thegent modes [options]
```

**Options**:

- `--format` - Parameter
- `--mode` - Parameter

---

## `thegent negotiate`

**Description**: Negotiate a contract version (WP-7001).

**Usage**:

```bash
thegent negotiate [options]
```

**Options**:

- `--contract-id` - Parameter
- `--supported` - Parameter
- `--format` - Parameter

---

## `thegent operations`

**Description**: List universal operation taxonomy (orchestrate, govern, recover, observe, plan).

**Usage**:

```bash
thegent operations [options]
```

**Options**:

- `--format` - Parameter
- `--operation` - Parameter

---

## `thegent pause`

**Description**: Mark a session as PAUSED in the registry (HITL).

**Usage**:

```bash
thegent pause [options]
```

**Options**:

- `--session-id` - Parameter

---

## `thegent plugin-check`

**Description**: Verify a plugin contract (WP-15003).

**Usage**:

```bash
thegent plugin-check [options]
```

**Options**:

- `--plugin-id` - Parameter
- `--signature` - Parameter

---

## `thegent probe`

**Description**: Compare current DAG state with a baseline checkpoint to detect regressions.

**Usage**:

```bash
thegent probe [options]
```

**Options**:

- `--baseline-id` - Parameter
- `--cd` - Parameter

---

## `thegent progress`

**Description**: Show recent runs (work-package progress). Alias for history --limit N.

**Usage**:

```bash
thegent progress [options]
```

**Options**:

- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent promote`

**Description**: Promote a candidate model to 'promoted' status (WP-14003).

**Usage**:

```bash
thegent promote [options]
```

**Options**:

- `--model-id` - Parameter
- `--approver` - Parameter

---

## `thegent prune`

**Description**: Kill redundant agent-related Node.js processes (LSPs, MCP servers, cc-status).

**Usage**:

```bash
thegent prune [options]
```

**Options**:

- `--force` - Parameter
- `--dry-run` - Parameter

---

## `thegent prune-periodic`

**Description**: Install periodic prune daemon (launchd on macOS, systemd on Linux).

**Usage**:

```bash
thegent prune-periodic [options]
```

**Options**:

- `--action` - Parameter

---

## `thegent ps`

**Description**: List registered background sessions.

**Usage**:

```bash
thegent ps [options]
```

**Options**:

- `--all-sessions` - Parameter
- `--owner` - Parameter
- `--format` - Parameter
- `--include-contract` - Parameter

---

## `thegent purge`

**Description**: WP-3006: Tiered retention purge (G-GP-07).

**Usage**:

```bash
thegent purge [options]
```

**Options**:

- `--dry-run` - Parameter

---

## `thegent purge-history`

**Description**: Purge expired history based on tiered retention (WP-3006).

**Usage**:

```bash
thegent purge-history [options]
```

**Options**:

- `--dry-run` - Parameter

---

## `thegent quality-index`

**Description**: Show quality index (0-1) for all models. Uses benchmarks.json (TB2.0, SWE-Bench, AIME).

**Usage**:

```bash
thegent quality-index [options]
```

**Options**:

- `--format` - Parameter
- `--no-cache` - Parameter

---

## `thegent ready`

**Description**: List task IDs with satisfied dependencies (ready to run).

**Usage**:

```bash
thegent ready [options]
```

**Options**:

- `--cd` - Parameter
- `--format` - Parameter

---

## `thegent reconcile`

**Description**: Reconcile DAG state with reality (clean up stuck 'running' tasks).

**Usage**:

```bash
thegent reconcile [options]
```

**Options**:

- `--cd` - Parameter

---

## `thegent redact`

**Description**: Test PII/Secret redaction (WP-15005).

**Usage**:

```bash
thegent redact [options]
```

**Options**:

- `--text` - Parameter

---

## `thegent refresh`

**Description**: Invalidate models, speed-index, and quality-index caches. Next lookup will re-fetch.

**Usage**:

```bash
thegent refresh
```

---

## `thegent register`

**Description**: Register a project in the global registry.

**Usage**:

```bash
thegent register [options]
```

**Options**:

- `--path` - Parameter
- `--name` - Parameter

---

## `thegent release-pack`

**Description**: Automated release documentation packaging (WP-12009).

**Usage**:

```bash
thegent release-pack [options]
```

**Options**:

- `--version` - Parameter

---

## `thegent remember`

**Description**: Shortcut for memory add --category note.

**Usage**:

```bash
thegent remember [options]
```

**Options**:

- `--content` - Parameter

---

## `thegent remove`

**Description**: Remove a task from the DAG.

**Usage**:

```bash
thegent remove [options]
```

**Options**:

- `--task-id` - Parameter
- `--cd` - Parameter

---

## `thegent replay`

**Description**: Decision replay and rationale snapshots (WP-4007).

**Usage**:

```bash
thegent replay [options]
```

**Options**:

- `--run-id` - Parameter
- `--what-if-env` - Parameter

---

## `thegent research`

**Description**: Deep dive research and comprehensive information gathering.

**Usage**:

```bash
thegent research [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--timeout` - Parameter

---

## `thegent resolve`

**Description**: Mark an escalation item as resolved.

**Usage**:

```bash
thegent resolve [options]
```

**Options**:

- `--run-id` - Parameter
- `--resolution` - Parameter

---

## `thegent resolve-model-route`

**Description**: Resolve a model to a concrete provider+alias route.

**Usage**:

```bash
thegent resolve-model-route [options]
```

**Options**:

- `--model` - Parameter
- `--provider` - Parameter
- `--policy` - Parameter
- `--quality-floor` - Parameter
- `--lane` - Parameter

---

## `thegent restart`

**Description**: Ensure config, stop proxy, then start. Use after config changes.

**Usage**:

```bash
thegent restart
```

---

## `thegent restart`

**Description**: Hot reload: restart MCP + proxy (down then up).

**Usage**:

```bash
thegent restart
```

---

## `thegent resume`

**Description**: Manually resume a deferred task.

**Usage**:

```bash
thegent resume [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent resume`

**Description**: Mark a paused session as RUNNING in the registry (HITL).

**Usage**:

```bash
thegent resume [options]
```

**Options**:

- `--session-id` - Parameter

---

## `thegent retry`

**Description**: Retry a failed run. With no run_id, list recent failed runs.

**Usage**:

```bash
thegent retry [options]
```

**Options**:

- `--run-id` - Parameter
- `--agent` - Parameter
- `--failover` - Parameter
- `--cd` - Parameter
- `--override` - Parameter

---

## `thegent retry`

**Description**: Retry a failed run. With no run_id, list recent failed runs. Alias for thegent retry.

**Usage**:

```bash
thegent retry [options]
```

**Options**:

- `--run-id` - Parameter
- `--agent` - Parameter
- `--failover` - Parameter
- `--cd` - Parameter
- `--override` - Parameter

---

## `thegent review`

**Description**: Critical analysis and quality checks for code or documentation.

**Usage**:

```bash
thegent review [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--timeout` - Parameter

---

## `thegent roadmap`

**Description**: Successor roadmap generation (WP-6004).

**Usage**:

```bash
thegent roadmap
```

---

## `thegent rollback`

**Description**: Rollback a promoted or candidate model (WP-14003).

**Usage**:

```bash
thegent rollback [options]
```

**Options**:

- `--model-id` - Parameter

---

## `thegent rollback`

**Description**: Rollback DAG state to a specific checkpoint.

**Usage**:

```bash
thegent rollback [options]
```

**Options**:

- `--checkpoint-id` - Parameter
- `--cd` - Parameter

---

## `thegent route`

**Description**: Route task to an active terminal session if available.

**Usage**:

```bash
thegent route [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter

---

## `thegent route-probe`

**Description**: Dry-run route resolution: show which provider would be selected (DX-004). Alias for resolve-model-route.

**Usage**:

```bash
thegent route-probe [options]
```

**Options**:

- `--model` - Parameter
- `--provider` - Parameter
- `--policy` - Parameter
- `--quality-floor` - Parameter
- `--lane` - Parameter

---

## `thegent rule`

**Description**: Shortcut for memory add --category lesson_positive/negative.

**Usage**:

```bash
thegent rule [options]
```

**Options**:

- `--content` - Parameter
- `--negative` - Parameter

---

## `thegent run`

**Description**: Run a foreground agent invocation. Use -M `<model>` without agent for model-first routing.

**Usage**:

```bash
thegent run [options]
```

**Options**:

- `--prompt` - Parameter
- `--agent` - Parameter
- `--cd` - Parameter
- `--retry-run` - Parameter
- `--mode` - Parameter
- `--timeout` - Parameter
- `--full` - Parameter
- `--live` - Parameter
- `--model` - Parameter
- `--provider` - Parameter
- `--failover` - Parameter
- `--routing` - Parameter
- `--include-contract` - Parameter
- `--run-id` - Parameter
- `--lane` - Parameter
- `--idempotency-token` - Parameter
- `--confidence` - Parameter
- `--arbitration` - Parameter
- `--override` - Parameter
- `--contract-version` - Parameter
- `--domain` - Parameter
- `--speculative` - Parameter
- `--search` - Parameter
- `--debug` - Parameter

---

## `thegent run`

**Description**: Spawn thegent bg for each ready task; update status=running and session_id.

**Usage**:

```bash
thegent run [options]
```

**Options**:

- `--cd` - Parameter
- `--dry-run` - Parameter
- `--task` - Parameter
- `--max-parallel` - Parameter
- `--lane` - Parameter
- `--check-drift` - Parameter
- `--contract-version` - Parameter

---

## `thegent run-diff`

**Description**: Compare two execution runs (trace comparison).

**Usage**:

```bash
thegent run-diff [options]
```

**Options**:

- `--run-a` - Parameter
- `--run-b` - Parameter

---

## `thegent scrape`

**Description**: MTSP-18: Scrape session history and record prompts to audit log.

**Usage**:

```bash
thegent scrape
```

---

## `thegent self-heal-tests`

**Description**: Self-healing test suite: automated fix recommendations (WP-6006).

**Usage**:

```bash
thegent self-heal-tests [options]
```

**Options**:

- `--test-output` - Parameter

---

## `thegent serve`

**Description**: Start the MCP server. Defaults to HTTP. Delegates to launchd/Homebrew service when available.

**Usage**:

```bash
thegent serve [options]
```

**Options**:

- `--host` - Parameter
- `--port` - Parameter
- `--force` - Parameter
- `--http` - Parameter
- `--reload` - Parameter

---

## `thegent service`

**Description**: Manage proxy as launchd service (macOS). Runs at login, restarts on crash.

**Usage**:

```bash
thegent service [options]
```

**Options**:

- `--action` - Parameter

---

## `thegent service`

**Description**: Manage thegent MCP HTTP server as launchd service (macOS). Start server before clients connect.

**Usage**:

```bash
thegent service [options]
```

**Options**:

- `--action` - Parameter

---

## `thegent session-contracts`

**Description**: Audit session routing contract metadata coverage and completeness.

**Usage**:

```bash
thegent session-contracts [options]
```

**Options**:

- `--all-sessions` - Parameter
- `--owner` - Parameter
- `--format` - Parameter
- `--missing-only` - Parameter
- `--summary-only` - Parameter
- `--strict` - Parameter

---

## `thegent show`

**Description**: Show active guardrail configuration (FR-GOV-007).

**Usage**:

```bash
thegent show
```

---

## `thegent show-policy`

**Description**: Show active governance policies and thresholds.

**Usage**:

```bash
thegent show-policy
```

---

## `thegent siem-test`

**Description**: Test SIEM event egress (WP-15001).

**Usage**:

```bash
thegent siem-test [options]
```

**Options**:

- `--message` - Parameter
- `--severity` - Parameter

---

## `thegent sitback-dashboard`

**Description**: Unified sitback dashboard: sessions, cockpit, terminals. CLI mirror of MCP tool.

**Usage**:

```bash
thegent sitback-dashboard [options]
```

**Options**:

- `--refresh` - Parameter
- `--format` - Parameter
- `--profile` - Parameter

---

## `thegent snapshot`

**Description**: Capture a forensic snapshot of the current environment.

**Usage**:

```bash
thegent snapshot [options]
```

**Options**:

- `--run-id` - Parameter
- `--phase` - Parameter

---

## `thegent snooze`

**Description**: Snooze an alert; auto-escalates when expired.

**Usage**:

```bash
thegent snooze [options]
```

**Options**:

- `--alert-id` - Parameter
- `--minutes` - Parameter
- `--type` - Parameter

---

## `thegent speed-index`

**Description**: Show speed index (0-1) for all model-provider pairs. Uses proxy metrics when reachable.

**Usage**:

```bash
thegent speed-index [options]
```

**Options**:

- `--format` - Parameter
- `--no-cache` - Parameter

---

## `thegent spotlight-exclude`

**Description**: Exclude heavy development and thegent metadata directories from Spotlight indexing (macOS).

**Usage**:

```bash
thegent spotlight-exclude [options]
```

**Options**:

- `--force` - Parameter

---

## `thegent start`

**Description**: Start proxy if not running. Uses ensure-config + CLIProxyAPIPlus binary.

**Usage**:

```bash
thegent start
```

---

## `thegent status`

**Description**: Monitor the status of the teammate swarm (WP-16002).

**Usage**:

```bash
thegent status [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent status`

**Description**: Show last environment and trust boundary status (WP-3007).

**Usage**:

```bash
thegent status [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent status`

**Description**: Show detailed federation health and drift status (WP-13005).

**Usage**:

```bash
thegent status
```

---

## `thegent status`

**Description**: Show current governance status (state, cycle_id, shutdown_requested).

**Usage**:

```bash
thegent status [options]
```

**Options**:

- `--cd` - Parameter

---

## `thegent status`

**Description**: Show recovery stability and suggested playbooks.

**Usage**:

```bash
thegent status
```

---

## `thegent status`

**Description**: Show one session status.

**Usage**:

```bash
thegent status [options]
```

**Options**:

- `--session-id` - Parameter
- `--format` - Parameter
- `--include-contract` - Parameter

---

## `thegent status`

**Description**: Show task + linked session status (running/exited:rc).

**Usage**:

```bash
thegent status [options]
```

**Options**:

- `--cd` - Parameter
- `--format` - Parameter

---

## `thegent stop`

**Description**: Stop a running session.

**Usage**:

```bash
thegent stop [options]
```

**Options**:

- `--session-id` - Parameter
- `--force` - Parameter
- `--wind-down` - Parameter
- `--grace` - Parameter

---

## `thegent stop`

**Description**: Stop proxy (kill process on cliproxy port).

**Usage**:

```bash
thegent stop
```

---

## `thegent summarize`

**Description**: Summarize content with brevity and key takeaways.

**Usage**:

```bash
thegent summarize [options]
```

**Options**:

- `--prompt` - Parameter
- `--cd` - Parameter
- `--bg` - Parameter
- `--model` - Parameter
- `--timeout` - Parameter

---

## `thegent summary`

**Description**: FR-X08: Unified observability summary (KPIs, drift, escalation).

**Usage**:

```bash
thegent summary [options]
```

**Options**:

- `--limit` - Parameter
- `--drift-window` - Parameter
- `--structural-budget` - Parameter
- `--semantic-budget` - Parameter
- `--provider` - Parameter
- `--trend-samples` - Parameter
- `--top-escalations` - Parameter
- `--format` - Parameter

---

## `thegent sweep`

**Description**: WP-3005: Policy drift sweep - drift detection, budget check, past-SLA escalations (cron-ready).

**Usage**:

```bash
thegent sweep [options]
```

**Options**:

- `--drift-window` - Parameter
- `--include-audit` - Parameter
- `--format` - Parameter

---

## `thegent sync`

**Description**: Sync CLAUDE.md to other platform-specific rule files (AGENTS.md, Cursor, Codex).

**Usage**:

```bash
thegent sync [options]
```

**Options**:

- `--force` - Parameter
- `--check` - Parameter
- `--cd` - Parameter

---

## `thegent sync`

**Description**: Update task status from session exit (running -> done/failed).

**Usage**:

```bash
thegent sync [options]
```

**Options**:

- `--cd` - Parameter
- `--watch` - Parameter
- `--interval` - Parameter
- `--auto-run-next` - Parameter
- `--no-auto-run-next` - Parameter

---

## `thegent synthesize`

**Description**: MTSP-17: Generate a synthesis report from the audit log.

**Usage**:

```bash
thegent synthesize
```

---

## `thegent takeover`

**Description**: Attach to an interactive tmux session (takeover).

**Usage**:

```bash
thegent takeover [options]
```

**Options**:

- `--session-id` - Parameter

---

## `thegent trace-replay`

**Description**: Replay an execution trace in simulation mode (WP-16001).

**Usage**:

```bash
thegent trace-replay [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent traffic`

**Description**: TRAFFIC KPI Dashboard (WP-Y7).

**Usage**:

```bash
thegent traffic
```

---

## `thegent trend`

**Description**: Read health trend snapshots for a report/gate policy scope.

**Usage**:

```bash
thegent trend [options]
```

**Options**:

- `--payload-type` - Parameter
- `--all-sessions` - Parameter
- `--owner` - Parameter
- `--strict` - Parameter
- `--limit` - Parameter
- `--format` - Parameter

---

## `thegent trend-analysis`

**Description**: Detailed contract trend analysis (WP-7009/7010).

**Usage**:

```bash
thegent trend-analysis
```

---

## `thegent up`

**Description**: Start MCP + proxy via process-compose (bundled mode).

**Usage**:

```bash
thegent up [options]
```

**Options**:

- `--reload` - Parameter

---

## `thegent update`

**Description**: Update a task in the DAG.

**Usage**:

```bash
thegent update [options]
```

**Options**:

- `--task-id` - Parameter
- `--cd` - Parameter
- `--status` - Parameter
- `--prompt` - Parameter
- `--agent` - Parameter
- `--depends-on` - Parameter
- `--contract-version` - Parameter

---

## `thegent usage`

**Description**: Show plan usage: provider metrics from CLIProxyAPIPlus and cost status.

**Usage**:

```bash
thegent usage [options]
```

**Options**:

- `--format` - Parameter
- `--no-cost` - Parameter

---

## `thegent validate`

**Description**: Validate DAG: cycles, orphans, agent names. Exit 2 on failure.

**Usage**:

```bash
thegent validate [options]
```

**Options**:

- `--cd` - Parameter

---

## `thegent verify`

**Description**: Verify a signed MAIF artifact (WP-3002).

**Usage**:

```bash
thegent verify [options]
```

**Options**:

- `--run-id` - Parameter

---

## `thegent verify`

**Description**: Verify the integrity of the execution run registry.

**Usage**:

```bash
thegent verify [options]
```

**Options**:

- `--format` - Parameter

---

## `thegent verify-codex-cliproxy`

**Description**: Verify Codex works with CLIProxy adapter. Agent self-service: no user intervention needed.

**Usage**:

```bash
thegent verify-codex-cliproxy [options]
```

**Options**:

- `--model` - Parameter
- `--prompt` - Parameter
- `--timeout` - Parameter

---

## `thegent wait`

**Description**: Wait for next inbox event matching filters. Blocks until new event or timeout.

**Usage**:

```bash
thegent wait [options]
```

**Options**:

- `--owner` - Parameter
- `--agent` - Parameter
- `--event-type` - Parameter
- `--status` - Parameter
- `--sources` - Parameter
- `--poll` - Parameter
- `--timeout` - Parameter
- `--notify` - Parameter
- `--format` - Parameter

---

## `thegent wait`

**Description**: Wait for session completion and return session exit code.

**Usage**:

```bash
thegent wait [options]
```

**Options**:

- `--session-id` - Parameter
- `--timeout` - Parameter

---

## `thegent wait-next`

**Description**: Block until next actionable work exists. Does not return until DAG ready, work item, escalation, or inbox event.

**Usage**:

```bash
thegent wait-next [options]
```

**Options**:

- `--cd` - Parameter
- `--poll` - Parameter
- `--timeout` - Parameter
- `--sources` - Parameter
- `--format` - Parameter

---

## `thegent wait-next`

**Description**: Block until next actionable work exists (DAG ready, do_next, escalation, inbox).

**Usage**:

```bash
thegent wait-next [options]
```

**Options**:

- `--cd` - Parameter
- `--poll` - Parameter
- `--timeout` - Parameter
- `--sources` - Parameter
- `--format` - Parameter

---

## `thegent wait-next`

**Description**: Block until DAG has next actionable work (sync + ready tasks). Does not return until ready tasks exist.

**Usage**:

```bash
thegent wait-next [options]
```

**Options**:

- `--cd` - Parameter
- `--poll` - Parameter
- `--timeout` - Parameter
- `--format` - Parameter

---

## `thegent watch`

**Description**: Run continuous governance mode.

**Usage**:

```bash
thegent watch [options]
```

**Options**:

- `--cd` - Parameter
- `--interval` - Parameter
- `--max-cycles` - Parameter

---

## `thegent watchdog`

**Description**: Scan for stale sessions and recommend handoffs (WP-5005).

**Usage**:

```bash
thegent watchdog [options]
```

**Options**:

- `--max-idle` - Parameter

---
