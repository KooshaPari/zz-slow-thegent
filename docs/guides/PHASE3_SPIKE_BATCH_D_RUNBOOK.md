# Phase 3 Spike Batch D Runbook (Final)

Date: February 23, 2026

## Overview

Spike Batch D covers the final adopt repos:

- **searxng** (searxng/searxng) - Privacy-respecting search
- **doorstop** (doorstop-dev/doorstop) - Requirements management

## Smoke Tests

### SearXNG

```bash
# Required env vars:
export THEGENT_ENABLE_SEARXNG=1
export SEARXNG_URL=http://localhost:8888  # optional

# Run smoke test:
task integration:searxng:smoke
# or
uv run python scripts/searxng_contract_smoke.py
```

### Doorstop

```bash
# Required env vars:
export THEGENT_ENABLE_DOORSTOP=1
export DOORSTOP_PROJECT_DIR=./requirements  # optional

# Run smoke test:
task integration:doorstop:smoke
# or
uv run python scripts/doorstop_contract_smoke.py
```

## Integration Details

### SearXNG Integration

- **Module**: `src/thegent/integrations/searxng.py`
- **Feature Flag**: `THEGENT_ENABLE_SEARXNG`
- **Config Env Vars**:
  - `SEARXNG_URL` - Server URL (default: http://localhost:8888)

### Doorstop Integration

- **Module**: `src/thegent/integrations/doorstop.py`
- **Feature Flag**: `THEGENT_ENABLE_DOORSTOP`
- **Config Env Vars**:
  - `DOORSTOP_PROJECT_DIR` - Project directory (default: ./requirements)
  - `DOORSTOP_TREE_ROOT` - Tree root (default: REQ)
  - `DOORSTOP_VALIDATE_ON_BUILD` - Validate on build (default: true)

## Rollback Procedure

1. Disable the feature flag:

   ```bash
   export THEGENT_ENABLE_SEARXNG=0
   export THEGENT_ENABLE_DOORSTOP=0
   ```

2. Verify baseline:
   ```bash
   task quality
   ```

## Acceptance Criteria

- [ ] SearXNG smoke test passes
- [ ] Doorstop smoke test passes
- [ ] Integration modules import
- [ ] `task quality` green
