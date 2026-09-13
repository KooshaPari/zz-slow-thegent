# Phase 3 Spike Batch C Runbook

Date: February 23, 2026

## Overview

Spike Batch C covers three more adopt-repos:

- **kratos** (ory/kratos) - Identity/auth middleware
- **pocketbase** (pocketbase/pocketbase) - Lightweight embedded backend
- **browser-use** (browser-use/browser-use) - Browser automation adapter

## Smoke Tests

### Kratos (Ory Kratos)

```bash
# Required env vars:
export THEGENT_AUTH_PROVIDER=kratos
export KRATOS_PUBLIC_URL=http://localhost:4433

# Run smoke test:
task integration:kratos:smoke
# or
uv run python scripts/kratos_contract_smoke.py
```

### PocketBase

```bash
# Required env vars:
export THEGENT_POCKETBASE_ENABLED=1
export POCKETBASE_HTTP_ADDR=127.0.0.1:8090  # optional

# Run smoke test:
task integration:pocketbase:smoke
# or
uv run python scripts/pocketbase_contract_smoke.py
```

### Browser-Use

```bash
# Required env vars:
export THEGENT_BROWSER_USE_ENABLED=1
export BROWSER_USE_ALLOWED_URLS=https://*  # optional allowlist

# Run smoke test:
task integration:browser-use:smoke
# or
uv run python scripts/browser_use_contract_smoke.py
```

## Integration Details

### Kratos Integration

- **Module**: `src/thegent/integrations/kratos_auth.py`
- **Feature Flag**: `THEGENT_AUTH_PROVIDER=kratos`
- **Config Env Vars**:
  - `KRATOS_PUBLIC_URL` - Public URL for session validation (default: http://localhost:4433)
  - `KRATOS_ADMIN_URL` - Admin URL for identity management
  - `KRATOS_API_KEY` - API key for admin endpoints
  - `KRATOS_COOKIE_NAME` - Session cookie name (default: ory_kratos_session)
  - `KRATOS_SESSION_TTL` - Session TTL in seconds (default: 3600)

### PocketBase Integration

- **Module**: `src/thegent/integrations/pocketbase_storage.py`
- **Feature Flag**: `THEGENT_POCKETBASE_ENABLED`
- **Config Env Vars**:
  - `POCKETBASE_BINARY` - Path to binary (default: ./pocketbase)
  - `POCKETBASE_DATA_DIR` - Data directory (default: ./data/pocketbase)
  - `POCKETBASE_ADMIN_EMAIL` - Admin email
  - `POCKETBASE_ADMIN_PASSWORD` - Admin password
  - `POCKETBASE_HTTP_ADDR` - HTTP listen address (default: 127.0.0.1:8090)
- **Collections**: `agent_sessions`, `proxy_events`

### Browser-Use Integration

- **Module**: `src/thegent/integrations/browser_use_adapter.py`
- **Feature Flag**: `THEGENT_BROWSER_USE_ENABLED`
- **Config Env Vars**:
  - `BROWSER_USE_VERSION` - Package version to pin (default: 0.1.0)
  - `BROWSER_USE_BROWSER` - Browser (default: chromium)
  - `BROWSER_USE_HEADLESS` - Headless mode (default: true)
  - `BROWSER_USE_TIMEOUT` - Timeout in seconds (default: 60)
  - `BROWSER_USE_ALLOWED_URLS` - URL allowlist (default: https://\*)
  - `BROWSER_USE_API_KEY` - Optional API key for cloud features

## Rollback Procedure

If any integration fails:

1. **Disable the feature flag**:

   ```bash
   export THEGENT_AUTH_PROVIDER=local  # or unset
   export THEGENT_POCKETBASE_ENABLED=0
   export THEGENT_BROWSER_USE_ENABLED=0
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

- [ ] Kratos smoke test passes with mock server
- [ ] PocketBase smoke test passes with mock server
- [ ] Browser-Use smoke test passes with uvx check
- [ ] Unit tests pass: `pytest tests/test_*_contract_smoke.py`
- [ ] `task quality` remains green
- [ ] Integration modules import without errors
