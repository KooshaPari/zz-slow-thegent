# Phase 3 Spike Batch B Runbook

Date: February 23, 2026

## Overview

Spike Batch B covers three adopt-repos from the Phase 2 analysis:

- **graphiti** (getzep/graphiti) - Persistent agent memory with graph semantics
- **nats** (nats-io/nats-server) - Event backbone for orchestration
- **lmcache** (LMCache/LMCache) - KV-cache acceleration for inference

## Smoke Tests

### Graphiti

```bash
# Required env vars:
export GRAPHITI_SERVER_URL="http://localhost:8000"
export GRAPHITI_API_KEY=""  # optional

# Run smoke test:
task integration:graphiti:smoke
# or
uv run python scripts/graphiti_contract_smoke.py
```

### NATS

```bash
# Required env vars:
export THEGENT_EVENT_BUS="nats"
export NATS_SERVERS="nats://localhost:4222"

# Run smoke test:
task integration:nats:smoke
# or
uv run python scripts/nats_contract_smoke.py
```

### LMCache

```bash
# Required env vars (Redis backend):
export LMCACHE_ENABLED=1
export LMCACHE_BACKEND=redis
export LMCACHE_REDIS_HOST=localhost
export LMCACHE_REDIS_PORT=6379

# Or HTTP backend:
export LMCACHE_ENABLED=1
export LMCACHE_BACKEND=http
export LMCACHE_SERVER_URL=http://localhost:8080

# Run smoke test:
task integration:lmcache:smoke
# or
uv run python scripts/lmcache_contract_smoke.py
```

## Integration Details

### Graphiti Integration

- **Module**: `src/thegent/integrations/graphiti.py`
- **Feature Flag**: `THEGENT_ENABLE_GRAPHITI`
- **Config Env Vars**:
  - `GRAPHITI_SERVER_URL` - Server URL (default: http://localhost:8000)
  - `GRAPHITI_API_KEY` - API key for auth
  - `GRAPHITI_NAMESPACE` - Namespace (default: thegent)
  - `GRAPHITI_TIMEOUT_SECONDS` - Timeout (default: 30)
  - `GRAPHITI_MAX_CONTEXT_ITEMS` - Max items (default: 10)

### NATS Integration

- **Module**: `src/thegent/integrations/nats_event_bus.py`
- **Feature Flag**: `THEGENT_EVENT_BUS=nats`
- **Config Env Vars**:
  - `NATS_SERVERS` - Comma-separated server URLs
  - `NATS_TIMEOUT_SECONDS` - Timeout (default: 10)
  - `NATS_TLS` - Enable TLS (default: false)
  - `NATS_CREDS_FILE` - Credentials file path
  - `NATS_NKEY_SEED` - NKey for auth
  - `NATS_SUBJECT_PREFIX` - Subject prefix (default: thegent)
- **Event Types**:
  - `task.started`
  - `task.progress`
  - `task.completed`
  - `task.failed`

### LMCache Integration

- **Module**: `src/thegent/integrations/lmcache.py`
- **Feature Flag**: `LMCACHE_ENABLED`
- **Config Env Vars**:
  - `LMCACHE_SERVER_URL` - Server URL (HTTP backend)
  - `LMCACHE_BACKEND` - Backend type: redis, file, http
  - `LMCACHE_REDIS_HOST/PORT/DB/PASSWORD` - Redis config
  - `LMCACHE_KEY_PREFIX` - Cache key prefix (default: cliproxy)
  - `LMCACHE_TTL_SECONDS` - TTL (default: 3600)

## Rollback Procedure

If any integration fails:

1. **Disable the feature flag**:

   ```bash
   export THEGENT_ENABLE_GRAPHITI=0
   export THEGENT_EVENT_BUS=local  # or unset
   export LMCACHE_ENABLED=0
   ```

2. **Verify baseline behavior**:

   ```bash
   task quality
   task test
   ```

3. **Revert integration** (if needed):
   ```bash
   git revert HEAD  # or specific commit
   ```

## Acceptance Criteria

- [ ] Graphiti smoke test passes with mock server
- [ ] NATS smoke test passes with mock connection
- [ ] LMCache smoke test passes with mock Redis
- [ ] Unit tests pass: `pytest tests/test_*_contract_smoke.py`
- [ ] `task quality` remains green
- [ ] Integration modules import without errors
