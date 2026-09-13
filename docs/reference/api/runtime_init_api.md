# runtime_init API Reference

> **Source**: `src/thegent/infra/runtime_init.py`

Runtime infrastructure initialization and cleanup.

---

## get_resource_stats

Get current resource statistics.

**Returns**: ResourceStats if monitoring is active, None otherwise.

---

## initialize_runtime_infrastructure

Initialize runtime infrastructure (resource limits and monitoring).

This function:

1. Sets up resource limits (FD, process count)
2. Starts resource monitoring in background thread
3. Registers cleanup handlers for graceful shutdown

Safe to call multiple times (idempotent).

---

## is_initialized

Check if runtime infrastructure is initialized.

---
