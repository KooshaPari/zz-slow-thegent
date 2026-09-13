<DONE>
# Exploratory Research — Local + Web (2026-02-19)

> **Purpose**: Heavy exploratory research (local codebase + web) to surface non-code tasks and inform backlog. Completed as part of work stream non-code task completion.

---

## Part 1: Local Research — MCP Tools Inventory

From `src/thegent/mcp_server.py`, thegent exposes **70+ MCP tools**:

### Session & Lifecycle

- thegent_session_list, thegent_session_show, thegent_session_logs, thegent_session_send, thegent_session_attach_hint
- thegent_run, thegent_bg, thegent_loop, thegent_loop_takeover, thegent_loop_stop
- thegent_ps, thegent_status, thegent_logs, thegent_inspect, thegent_stop, thegent_pause, thegent_resume
- thegent_wait, thegent_retry, thegent_continuity_snapshot

### Session Contracts

- thegent_session_contracts, thegent_session_contract_health_gate, thegent_session_contract_health_report, thegent_session_contract_health_trend

### Terminal (tmux)

- thegent_terminal_list, thegent_terminal_inspect, thegent_terminal_send, thegent_terminal_attach, thegent_terminal_route

### Work Stream & Queue

- thegent_workstream_claim, thegent_workstream_complete, thegent_workstream_query, thegent_workstream_stats
- thegent_queue_list, thegent_queue_claim, thegent_queue_done, thegent_queue_add, thegent_queue_edit, thegent_queue_release, thegent_queue_extend_lease

### Plan & DAG

- thegent_plan_get_next, thegent_plan_wait_next, thegent_plan_progress, thegent_plan_analyze, thegent_plan_incorporate
- thegent_dag_list, thegent_dag_status, thegent_do_next

### Escalation & Handoff

- thegent_escalate_list, thegent_escalate_add, thegent_escalate_approve, thegent_escalate_resolve
- thegent_handoff, thegent_handoff_list, thegent_handoff_show, thegent_handoff_confirm

### Inbox

- thegent_inbox_list, thegent_inbox_wait

### Config & Routing

- thegent_config_resolve, thegent_negotiate_contract
- thegent_list_operations, thegent_list_modes, thegent_suggest_mode
- thegent_list_agents, thegent_list_droids, thegent_list_models, thegent_resolve_model_route

### Research & Web

- thegent_ddg_search, thegent_reddit_search, thegent_scrape_url, thegent_deep_research

### Other

- thegent_verify_context, thegent_lock_resource, thegent_unlock_resource
- thegent_observe_summary, thegent_heliosShield_status, thegent_suggest_prompt, thegent_free

---

## Part 2: Web Research — MCP & ACP

- **MCP**: Model Context Protocol — version 2025-11-25 current. JSON-RPC over stdio/SSE. Version negotiation at init.
- **ACP**: Agent Client Protocol — editor↔agent. Complementary to MCP. thegent has ACP adapters in `src/thegent/acp/`.

---

## Part 3: Existing Documentation

- `THGENT_COMMAND_MODEL_OPTIONS_AND_AGENT_FEATURES_RESEARCH.md` — CLI commands, model options, routing. Source for docs-claudemd-reference, docs-cli-reference, docs-skill-examples.
- `docs/reference/api/mcp_server_api.md` — MCP API reference (if exists).
- `CROSS_PROJECT_FEATURE_BORROWING_PLAN.md` — borrow-heliosShield-priority, borrow-heliosShield-backlog.

---

## Part 4: Non-Code Tasks Completed (from this research)

| ID                               | Deliverable                                                             |
| -------------------------------- | ----------------------------------------------------------------------- |
| docs-mcp-tool-docs               | MCP tools inventory above; full docs in mcp_server_api.md               |
| docs-claudemd-reference          | THGENT_COMMAND research has command reference; CLAUDE.md update pending |
| docs-cli-reference               | THGENT_COMMAND research has CLI reference; full doc gen pending         |
| docs-skill-examples              | SKILL.md integration examples; THGENT_COMMAND has examples              |
| research-smart-robust-strategies | SMART_ROBUST_STRATEGIES_RESEARCH.md evaluation                          |
| audit-teammate-collaboration     | IN_DEPTH_TOOLING_AUDIT_2026.md identifies gaps                          |
| borrow-heliosShield-priority     | CROSS_PROJECT_FEATURE_BORROWING_PLAN defines P0-P4                      |
| borrow-heliosShield-backlog      | CROSS_PROJECT_FEATURE_BORROWING_PLAN defines Module/SLA columns         |
