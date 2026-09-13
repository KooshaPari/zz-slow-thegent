# FastMCP Graceful Shutdown (G-OP-10)

**Purpose:** Design and document graceful shutdown for MCP server.
**Date:** 2026-02-14
**Scope:** G-OP-10

---

## 1. Current State

- **Lifespan:** `thegent_lifespan` stops bundled proxy on teardown.
- **Gap:** No explicit drain of in-flight requests; no wait for active background runs (up to 30s).

---

## 2. Design

### 2.1 Shutdown Sequence

1. Receive SIGTERM/SIGINT
2. Stop accepting new connections (FastMCP/Starlette default)
3. **Optional:** Wait up to `THGENT_SHUTDOWN_WAIT_S` for in-flight tool calls to complete
4. **Optional:** Wait up to N seconds for active background runs (thegent_bg sessions) to finish
5. Terminate bundled proxy
6. Exit

### 2.2 Configuration

| Env                           | Default | Description                                                                             |
| ----------------------------- | ------- | --------------------------------------------------------------------------------------- |
| THGENT_SHUTDOWN_WAIT_S        | 0       | Seconds to wait for in-flight requests before hard exit. 0 = no wait.                   |
| THGENT_SHUTDOWN_WAIT_ACTIVE_S | 0       | Seconds to poll for active background runs; wait until count=0 or timeout. 0 = no wait. |

### 2.3 Active Run Tracking

Background runs (thegent_bg) spawn subprocesses. The server does not block on them.

- **THGENT_SHUTDOWN_WAIT_ACTIVE_S:** When set, the lifespan teardown polls `ps_impl(all=True)` every 2s. If any session has `status == "running"`, it waits. Exits when no running sessions or timeout (max 120s).

---

## 3. Implementation Phases

| Phase | Deliverable                                                             | Status |
| ----- | ----------------------------------------------------------------------- | ------ |
| P1    | Design doc (this)                                                       | Done   |
| P2    | THGENT_SHUTDOWN_WAIT_S in lifespan; asyncio.sleep before yield teardown | Done   |
| P3    | Optional: poll ps_impl for active runs; THGENT_SHUTDOWN_WAIT_ACTIVE_S   | Done   |

---

## 4. References

- `src/thegent/mcp_server.py` — thegent_lifespan
- `docs/FASTMCP_OPTIMIZATION_AUDIT.md` — G-OP-10
