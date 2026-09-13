# Decommissioning and Sunset Plan

**Scope:** Temporary controls and legacy adapters in thegent
**Date:** 2026-02-14
**Related:** WP-6006, `docs/RUNBOOK.md` §5

## 1. Overview

This plan identifies temporary architectural shims, legacy adapters, and transitional controls that should be sunset as the platform matures.

## 2. Target Components for Sunset

| Component                     | Reason              | Sunset Trigger                                      | Target |
| ----------------------------- | ------------------- | --------------------------------------------------- | ------ |
| `GenericOutputAdapter`        | Loose normalization | 100% provider coverage with `XMLOutputAdapter`      | v1.2   |
| `fallback-plain` policy       | Low confidence      | 95% normalization success rate over 30 days         | v1.2   |
| `--override` flag (unlimited) | Security risk       | Implementation of TTL-based policy overrides        | v1.1   |
| Static model lists            | Brittle             | Stable `ModelScraper` performance for all providers | v1.2   |
| `history-legacy` command      | Hidden, superseded  | Already hidden                                      | v1.1   |

## 3. Migration Path

1. **Deprecation Phase:**
   - Emit warnings via `ContractTelemetry` when sunset components are used.
   - Update `CONTRACT_AUTHORITY.md` to mark versions as `deprecated`.
2. **Dual-Run Phase:**
   - Run legacy and new components in parallel where possible.
   - Log drift via `ContractTelemetry.detect_drift()` and `thegent govern conformance --check-drift`.
3. **Decommission Phase:**
   - Remove code from `src/thegent`.
   - Update conformance tests to ensure no regressions.

## 4. Rollback Strategy

In case of critical failures after sunset:

- Retain code in git history for rapid revert.
- Maintain `v-1` version compatibility in `ContractRegistry` for one major release.
