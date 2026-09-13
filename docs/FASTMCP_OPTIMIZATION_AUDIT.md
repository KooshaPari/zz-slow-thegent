# FastMCP Optimization & Polish Audit (G-OP-04–G-OP-10)

**Purpose:** Audit tool descriptions, parameter docs, error messages, ToolResult shape, SLO targets, health route, graceful shutdown.
**Date:** 2026-02-14
**Scope:** G-OP-04 through G-OP-10

---

## 1. G-OP-04: Tool Descriptions

| Tool                | Current                                     | Assessment                                                                              |
| ------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------- |
| thegent_run         | "Run an agent synchronously with a prompt." | ⚠ Add action-oriented: "Execute agent task; blocks until complete. Use for sync runs." |
| thegent_bg          | "Start an agent run in the background."     | ⚠ Add: "Fire-and-forget; returns session_id for logs/status/wait."                     |
| thegent_stop        | —                                           | Verify destructive hint; add "Stop background session; confirm before use."             |
| thegent_logs        | —                                           | "Read session log output; supports tail limit."                                         |
| thegent_ps          | —                                           | "List background sessions; discovery."                                                  |
| thegent_status      | —                                           | "Session status; quick health check."                                                   |
| thegent_wait        | —                                           | "Block until session completes or timeout."                                             |
| thegent_inspect     | —                                           | "Multi-session status + logs."                                                          |
| thegent_list_agents | —                                           | "List available agents."                                                                |
| thegent_list_droids | —                                           | "List droids."                                                                          |
| thegent_list_models | —                                           | "Model catalog; include_contract for routing."                                          |
| thegent_dag_list    | —                                           | "DAG task list."                                                                        |

**Status:** Descriptions exist; some could be more action-oriented. Annotations (readOnlyHint, destructiveHint, idempotentHint) are present.

---

## 2. G-OP-05: Parameter Docs

| Parameter         | Tool(s)                 | Default | Units       | Assessment          |
| ----------------- | ----------------------- | ------- | ----------- | ------------------- |
| timeout           | run, bg, wait           | 90      | seconds     | ✓ Documented        |
| tail              | logs                    | —       | lines       | Verify in docstring |
| cd                | run, bg, dag_list, etc. | —       | path        | ✓                   |
| mode              | run, bg                 | write   | write\|full | ✓                   |
| min_healthy_ratio | health gate             | 1.0     | 0.0–1.0     | ✓                   |

**Status:** Core params documented; tail/limit constraints should be explicit.

---

## 3. G-OP-06: Error Messages

| Error Pattern                    | Example                                                    | Remediation Hint                               |
| -------------------------------- | ---------------------------------------------------------- | ---------------------------------------------- |
| No route for model               | "No route for model 'X'. Try thegent list-models."         | ✓ Actionable                                   |
| Model not available via provider | "Model 'X' not available via provider 'Y'. Available: ..." | ✓                                              |
| Provide agent or model           | "Provide agent or model for routing."                      | ⚠ Add: "Use thegent list-models to discover." |
| Ambiguous cwd                    | "Ambiguous cwd. Provide --cd /path explicitly."            | ✓                                              |
| User declined elicitation        | "User declined to provide working directory."              | ✓                                              |
| Elicitation cancelled            | "Elicitation cancelled."                                   | ✓                                              |

**Status:** Most errors actionable; minor additions for discovery hints.

---

## 4. G-OP-07: ToolResult structured_content + meta.execution_time_ms

| Tool                        | structured_content      | execution_time_ms |
| --------------------------- | ----------------------- | ----------------- |
| thegent_run                 | ✓ (when dict result)    | ✓                 |
| thegent_bg                  | ✗ (returns JSON string) | ✗ (meta={})       |
| thegent_stop                | —                       | —                 |
| thegent_logs                | —                       | —                 |
| thegent_ps                  | ✓ (ps_impl dict)        | ✓                 |
| thegent_status              | ✓                       | ✓                 |
| thegent_wait                | ✓                       | ✓                 |
| thegent_inspect             | ✓                       | ✓                 |
| thegent_list_agents         | ✓                       | ✓                 |
| thegent_list_droids         | ✓                       | ✓                 |
| thegent_list_models         | ✗                       | ✓                 |
| thegent_dag_list            | ✗                       | ✓                 |
| thegent_resolve_model_route | ✓                       | ✓                 |
| Health gate/report/trend    | ✓                       | ✓                 |

**Status:** thegent_bg error returns now have structured_content + execution_time_ms; thegent_list_models, thegent_list_droids, thegent_dag_list have structured_content.

---

## 5. G-OP-08: SLO Targets

| Tool                | Target      | Notes                            |
| ------------------- | ----------- | -------------------------------- |
| thegent_ps          | p50 < 50ms  | Cached (TTL 30s); list operation |
| thegent_status      | p50 < 20ms  | Lightweight session lookup       |
| thegent_list_agents | p50 < 30ms  | Static list                      |
| thegent_list_droids | p50 < 30ms  | Dir scan                         |
| thegent_list_models | p50 < 200ms | Scraped catalog; cache hit ~50ms |
| thegent_run         | N/A         | Depends on agent; timeout 90s    |
| thegent_logs        | p95 < 500ms | File read; tail limit 500k       |

**Status:** Targets not enforced; document as aspirational. ResponseLimitingMiddleware (500k) and ResponseCachingMiddleware (30s) support SLOs.

---

## 6. G-OP-09: Health Route

| Item                                          | Status                                  |
| --------------------------------------------- | --------------------------------------- |
| @mcp.custom_route("/health", methods=["GET"]) | ✓ Implemented                           |
| Response                                      | `{"status": "ok", "server": "thegent"}` |
| Use                                           | Monitoring, load balancer health checks |

**Status:** ✓ Done.

---

## 7. G-OP-10: Graceful Shutdown

| Item                 | Status                                          |
| -------------------- | ----------------------------------------------- |
| Drain in-flight      | ⚠ FastMCP/Starlette default; no explicit drain |
| Wait for active runs | ⚠ No 30s wait for background runs              |
| Lifespan teardown    | ✓ thegent_lifespan stops bundled proxy          |

**Gap:** No explicit "wait for active runs up to 30s" in shutdown. Background runs (thegent_bg) are subprocess; server can exit without waiting. Document as known limitation; optional: add shutdown hook to wait for active session count.

---

## 8. Middleware Verification (G-OP-01–03)

| Middleware                 | Config                                                           | Status |
| -------------------------- | ---------------------------------------------------------------- | ------ |
| ResponseCachingMiddleware  | TTL 30s, tools: ps, list_agents, list_droids, list_models, trend | ✓      |
| RateLimitingMiddleware     | max_requests_per_second=10, burst=20                             | ✓      |
| ResponseLimitingMiddleware | max_size=500_000                                                 | ✓      |

---

## 9. Recommended Actions

| Priority | Action                                                                                   |
| -------- | ---------------------------------------------------------------------------------------- |
| P1       | Add structured_content to thegent_bg success payload; execution_time_ms to error returns |
| P1       | Add structured_content to thegent_list_models (result is dict)                           |
| P2       | Document SLO targets in FASTMCP_DEPLOYMENT_GUIDE or runbook                              |
| P2       | Add graceful shutdown design: optional THGENT_SHUTDOWN_WAIT_S                            |
| P3       | Expand tool descriptions for agent-optimized clarity                                     |

---

## 10. References

- `src/thegent/mcp_server.py` — tools, middleware, health route
- `docs/FASTMCP_DEPLOYMENT_GUIDE.md`
- `docs/VERIFICATION_RUNBOOK.md`
