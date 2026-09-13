# FastMCP Deployment Guide (G-FM-01 Phase 5)

**Status:** Authoritative
**Date:** 2026-02-14
**Scope:** Production readiness — auth, stateless, Redis, session state, deployment

---

## 1. Overview

This guide covers deploying the thegent MCP server in production. Per G-FM-01 Phase 5: auth (Bearer/OAuth), stateless HTTP, Redis backend, session state store, and deployment steps.

---

## 2. Current Capabilities

| Feature                 | Status       | Config                                                             |
| ----------------------- | ------------ | ------------------------------------------------------------------ |
| **Stateless HTTP**      | ✓ Supported  | `stateless_http=True` (default) — per-request JSON-RPC without SSE |
| **Redis EventStore**    | ✓ Supported  | `FASTMCP_EVENT_STORE_URL=redis://host:port`                        |
| **Session state**       | ✓ EventStore | In-memory default; Redis when URL set                              |
| **Auth (Bearer/OAuth)** | □ To add     | See §4                                                             |
| **Deployment**          | ✓ Uvicorn    | `thegent mcp run` or `python -m thegent.mcp_server`                |

---

## 3. Environment Variables

| Variable                  | Default   | Description                                  |
| ------------------------- | --------- | -------------------------------------------- |
| `THGENT_MCP_HOST`         | 127.0.0.1 | Bind address                                 |
| `THGENT_MCP_PORT`         | 3847      | Port                                         |
| `FASTMCP_EVENT_STORE_URL` | —         | Redis URL for EventStore; omit for in-memory |
| `FASTMCP_DOCKET_URL`      | —         | Task backend for background tasks (optional) |

---

## 4. Auth (Bearer / OAuth)

### 4.1 Bearer Token (Simple)

Add middleware to validate `Authorization: Bearer <token>`:

```python
# In mcp_server.py (future)
from starlette.middleware.base import BaseHTTPMiddleware


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return JSONResponse({"error": "Missing or invalid Authorization"}, status=401)
        token = auth[7:]
        if not await validate_token(token):  # Your validation logic
            return JSONResponse({"error": "Invalid token"}, status=401)
        return await call_next(request)
```

Config: `THGENT_MCP_AUTH_MODE=bearer`, `THGENT_MCP_BEARER_TOKENS=token1,token2` (or validate against external service).

### 4.2 OAuth (Production)

Per `docs/research/FASTMCP_STORAGE_EVENTSTORE.md`:

```python
from fastmcp.server.auth.providers.github import GitHubProvider
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.fernet_encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet

auth = GitHubProvider(
    client_storage=FernetEncryptionWrapper(
        key_value=RedisStore(url=os.environ["REDIS_URL"]), fernet=Fernet(os.environ["STORAGE_ENCRYPTION_KEY"])
    )
)
mcp.add_auth_provider(auth)
```

- Use `FernetEncryptionWrapper` for production (tokens encrypted at rest)
- Store OAuth state in Redis for multi-instance deployments

---

## 5. Redis Backend

### 5.1 EventStore (SSE / Long Runs)

Set `FASTMCP_EVENT_STORE_URL=redis://localhost:6379` (or your Redis URL). The server uses `RedisStore` for EventStore when this is set.

### 5.2 Session State

EventStore holds SSE stream events. For stateless HTTP (`stateless_http=True`), no persistent session — each request is independent. For streamable HTTP with SSE, EventStore enables client reconnect and resume.

### 5.3 Response Cache (Optional)

To use Redis for response caching (ps, list_agents, list_models), configure `ResponseCachingMiddleware` with `RedisStore`. See `docs/research/FASTMCP_STORAGE_EVENTSTORE.md` §3.

---

## 6. Deployment Steps

### 6.1 Single Instance (Uvicorn)

```bash
# Development
thegent mcp run

# Production (bind all interfaces)
THGENT_MCP_HOST=0.0.0.0 thegent mcp run
```

### 6.2 With Reverse Proxy (Nginx)

```nginx
location /mcp {
    proxy_pass http://127.0.0.1:3847;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

### 6.3 Process Manager (systemd)

```ini
[Unit]
Description=Thegent MCP Server
After=network.target redis.service

[Service]
Type=simple
User=thegent
Environment="FASTMCP_EVENT_STORE_URL=redis://localhost:6379"
ExecStart=/path/to/.venv/bin/thegent mcp run --host 0.0.0.0 --port 3847
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 6.4 Docker (Example)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENV FASTMCP_EVENT_STORE_URL=redis://redis:6379
EXPOSE 3847
CMD ["thegent", "mcp", "run", "--host", "0.0.0.0"]
```

---

## 7. Checklist: Production Readiness

- [ ] Set `FASTMCP_EVENT_STORE_URL` for Redis EventStore
- [ ] Add Bearer or OAuth auth per §4
- [ ] Use reverse proxy with TLS termination
- [ ] Configure process manager (systemd/supervisor)
- [ ] Set `THGENT_ENVIRONMENT=production`
- [ ] Verify `thegent observe drift` and `govern conformance --check-drift` in CI

---

## 8. References

- `docs/research/FASTMCP_STORAGE_EVENTSTORE.md` — Redis, DiskStore, EventStore
- `docs/research/FASTMCP_TRANSFORMS_DEPLOYMENT.md` — EventStore, http_app
- `docs/VERIFICATION_RUNBOOK.md` — Server verification checklist
