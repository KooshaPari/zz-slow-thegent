<DONE>
# MCP and Client Features for Session Notifications

**Date:** 2026-02-15
**Context:** Sitback Agent has no push notifications; hooks run in IDE context and don't notify the agent. Session updates go to `run_registry.jsonl`; the agent must poll. This doc explores MCP elicitation, Tasks, and client features to create proper notification systems.

---

## Summary of MCP Notification Capabilities

| Notification                         | Purpose                   | Server-initiated? | Client support                  |
| ------------------------------------ | ------------------------- | ----------------- | ------------------------------- |
| `notifications/tools/list_changed`   | Tool list changed         | Yes               | Standard; clients refresh tools |
| `notifications/tasks/status`         | Task status change        | Yes               | Optional; clients MUST NOT rely |
| `notifications/elicitation/complete` | URL mode elicitation done | Yes               | For elicitation flows only      |
| `notifications/progress`             | Progress within request   | Yes (or client)   | Tied to `progressToken`         |

---

## 1. MCP Elicitation

**What it is:** Servers request structured input from users _during_ tool execution (form mode or URL mode). Used for cwd/owner disambiguation, OAuth, etc.

**Relevance to notifications:** Elicitation is **request-scoped** — it pauses a tool call until the user responds. It does **not** provide a generic notification channel. The only elicitation-related notification is `notifications/elicitation/complete`, which is for URL mode out-of-band flows (e.g. OAuth callback). Not applicable to "session X finished."

**thegent usage:** Already uses elicitation for CWD/owner when ambiguous (`ELICIT_CWD_MSG`, `ELICIT_OWNER_MSG`).

---

## 2. MCP Tasks (SEP-1686, Experimental)

**What it is:** Task-augmented requests. Client sends `tools/call` with `task: {ttl}`; server returns `CreateTaskResult` with `taskId` instead of the actual result. Client polls `tasks/get` and retrieves result via `tasks/result` when done.

**Key feature:** Servers **MAY** send `notifications/tasks/status` when task status changes. This is **server-initiated push**.

**Relevance to thegent_bg:**

- `thegent_bg` spawns a background session and returns immediately with `session_id`.
- If we make `thegent_bg` support task augmentation:
  - Client calls `thegent_bg` with `task: {ttl: 3600000}`.
  - Server returns `CreateTaskResult` with `taskId` = session_id (or mapping).
  - The "task" represents the session lifecycle.
  - When the session observer detects completion, server sends `notifications/tasks/status` with `status: "completed"` or `"failed"`.
  - Client receives the notification without polling.

**Caveats:**

- Spec says: "Requestors **MUST NOT** rely on receiving the `notifications/tasks/status` notification, as it is optional."
- MCP Tasks are **experimental** (2025-11-25). Claude Code and Codex client support is TBD.
- FastMCP has `TaskConfig(mode="optional")` for tools; full Tasks capability would need to be implemented.

**Verdict:** Best MCP-native option if clients support Tasks. Implement as optional enhancement.

---

## 3. Progress Notifications

**What it is:** `notifications/progress` with `progressToken`, `progress`, `total`, `message`. Tied to an **active request** that included `progressToken` in `_meta`.

**Relevance:** Progress is request-scoped. When `thegent_bg` returns, there is no active request for the background session. Progress does not apply to "session X finished" events that occur after the tool returns.

**Exception:** `thegent_wait(session_id)` blocks until the session finishes. That call _could_ include a `progressToken` and receive progress updates during the wait (e.g. "still running... 45s elapsed"). thegent_run already uses `ctx.report_progress()` for long runs.

---

## 4. tools/list_changed

**What it is:** Server sends `notifications/tools/list_changed` when its tool list changes. Clients typically refresh `tools/list`.

**Relevance:** Semantically wrong — session completion is not a tool list change. Could be abused to trigger a client refresh, but the agent would not receive "session X finished" — it would only get a tools refresh. Unlikely to help.

---

## 5. EventStore / SSE

**What it is:** For Streamable HTTP, EventStore stores SSE events so clients can reconnect and resume. Used for long-running tool calls (e.g. `thegent_run`).

**Relevance:** SSE is tied to a **single request**. The client connects, sends a request, receives a streamed response. When the response completes, the stream closes. There is no standard "server holds connection open and pushes unrelated events" pattern in MCP. EventStore is for resumability of in-flight requests, not for cross-request notifications.

---

## 6. Out-of-Band Options (Non-MCP)

| Approach         | Description                                                                                               | Pros                        | Cons                                             |
| ---------------- | --------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------ |
| **File watcher** | Sitback Agent watches `run_registry.jsonl` via `inotify`/`watchdog`                                       | No MCP changes; works today | Agent must run a watcher; not push from server   |
| **Socket/queue** | Hook dispatcher or session observer writes to a socket/Redis when session ends; Sitback listener connects | True push                   | New infra; outside MCP                           |
| **Webhook**      | thegent HTTP endpoint that clients POST to on session end                                                 | Decoupled                   | Requires client to run a local receiver; complex |
| **Polling**      | Current approach: Sitback polls `thegent_sitback_dashboard` / `thegent_ps` every 60–90s                   | Simple; works               | Latency; no true push                            |

---

## Recommendations

### Short term (no code changes)

1. **Document** the polling model clearly (already in SKILL.md, clode_main, mcp_sitback).
2. **Use `thegent_wait(session_id)`** when the user explicitly wants to wait for a specific session — it blocks until done or timeout.
3. **Refresh immediately** after `thegent_run`, `thegent_bg`, `thegent_stop`; when user says "status", "refresh", "what's running".

### Medium term (MCP Tasks)

1. **Add Tasks capability** to thegent MCP server if FastMCP supports it.
2. **Make `thegent_bg` task-augmented (optional):**
   - When client sends `task: {ttl}`, return `CreateTaskResult` with `taskId` = session_id.
   - When session completes, send `notifications/tasks/status` with `status: "completed"` or `"failed"`.
3. **Verify** Claude Code and Codex support MCP Tasks and handle `notifications/tasks/status`.

### Long term (if Tasks insufficient)

1. **Propose MCP SEP** for a generic `notifications/event` or `notifications/custom` for application-defined events (e.g. `thegent/session_complete`).
2. **Or** implement an out-of-band channel (socket, Redis pub/sub) for environments that need true push.

---

## References

- [MCP Elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation.md)
- [MCP Tasks](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks.md)
- [MCP Progress](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress.md)
- [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture.md) — notifications
- [FastMCP Elicitation](https://gofastmcp.com/servers/elicitation)
- [FastMCP EventStore](https://gofastmcp.com/servers/storage-backends) — SSE polling, resumability

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added notification patterns
2. Added MCP configurations
3. Enhanced cross-references

### Cross-References Added

- MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md
- CODEX_HOOKS_AND_EXTENSION_OPTIONS.md

### Practical Additions

- Notification templates
- MCP configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md](./MCP_FULL_PARITY_AND_FASTMCP_AUDIT.md) - Parity audit
- [CODEX_HOOKS_AND_EXTENSION_OPTIONS.md](./CODEX_HOOKS_AND_EXTENSION_OPTIONS.md) - Codex hooks
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
