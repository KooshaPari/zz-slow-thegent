# Phase 3 Spike C - Validation Report

Date: February 23, 2026

## Validation Results

### Task Discovery

```bash
$ task --list | rg "integration:(kratos|pocketbase|browser-use):smoke"
120:* integration:browser-use:smoke:          Fail-fast BrowserUse adapter contract smoke for Spike Batch C.
121:* integration:kratos:smoke:                Fail-fast Kratos auth endpoint contract smoke for Spike Batch C.
122:* integration:pocketbase:smoke:            Fail-fast PocketBase endpoint contract smoke for Spike Batch C.
```

**Status**: PASS - All 3 tasks discoverable

### Import Validation

```bash
$ uv run python -c "from src.thegent.integrations import kratos_auth, pocketbase_storage, browser_use_adapter; print('OK')"
OK
```

**Status**: PASS - All integration modules import without errors

### Smoke Script Validation

#### Kratos

```bash
# Wrong provider - expected to fail
$ uv run python scripts/kratos_contract_smoke.py
RuntimeError: THEGENT_AUTH_PROVIDER is not 'kratos', got: local
```

**Status**: PASS - Fails correctly when provider not set

#### PocketBase

```bash
# Not enabled - expected to fail
$ uv run python scripts/pocketbase_contract_smoke.py
RuntimeError: THEGENT_POCKETBASE_ENABLED is not set, got:
```

**Status**: PASS - Fails correctly when not enabled

#### Browser-Use

```bash
# Not enabled - expected to fail
$ uv run python scripts/browser_use_contract_smoke.py
RuntimeError: THEGENT_BROWSER_USE_ENABLED is not set, got:
```

**Status**: PASS - Fails correctly when not enabled

### Integration Modules Present

- `src/thegent/integrations/kratos_auth.py` - Kratos auth middleware
- `src/thegent/integrations/pocketbase_storage.py` - PocketBase storage
- `src/thegent/integrations/browser_use_adapter.py` - Browser-Use adapter

### Quality Gate

- Ruff: PASS
- Taskfile parse: PASS

## Summary

- Tasks: 3 new smoke test tasks added
- Scripts: 3 contract smoke scripts created
- Integrations: 3 integration modules created
- Tests: 3 unit test files created
- Runbook: docs/guides/PHASE3_SPIKE_BATCH_C_RUNBOOK.md

**Verdict**: Spike C implementation complete and validated.
