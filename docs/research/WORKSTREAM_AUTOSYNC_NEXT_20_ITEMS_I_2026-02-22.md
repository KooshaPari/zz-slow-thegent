<DONE>
# WORKSTREAM_AUTOSYNC_NEXT_20_ITEMS_I (WL-321..WL-332)

Date: 2026-02-22
Owner lane: Wave82 Lane A
Scope: Restore missing evidence document referenced by `docs/reference/WORK_STREAM.md` for WL-321 through WL-332.

## Coverage Map (WL-321..WL-332)

| Initiative | WLs                    |
| ---------- | ---------------------- |
| Watchdog   | WL-321, WL-322, WL-323 |
| Diff       | WL-324, WL-325, WL-326 |
| Replay     | WL-327, WL-328, WL-331 |
| Throttle   | WL-329, WL-330, WL-332 |

## Watchdog Initiative

Applies to: WL-321, WL-322, WL-323

Acceptance criteria:

- Connector watchdog runs event-driven checks without polling loops for steady-state health.
- Validation failures produce structured, traceable diagnostics (connector id, run id, failure reason).
- Watchdog detects stalled connector cycles and emits one bounded recovery action per cycle.

Validation commands:

```bash
python -m pytest -q tests -k "wl321 or wl322 or wl323"
python -m pytest --collect-only tests -k "watchdog and connector"
thegent doctor --strict
```

## Diff Initiative

Applies to: WL-324, WL-325, WL-326

Acceptance criteria:

- Connector state diffs are deterministic for identical inputs and environment.
- Reconciliation distinguishes no-op, additive, and conflicting changes in audit output.
- Integrity checks fail fast on malformed diff payloads with actionable error messages.

Validation commands:

```bash
python -m pytest -q tests -k "wl324 or wl325 or wl326"
python -m pytest -q tests -k "connector and diff"
thegent trace diff --help
```

## Replay Initiative

Applies to: WL-327, WL-328, WL-331

Acceptance criteria:

- Replay restores checkpointed connector state without reapplying already acknowledged writes.
- Queue replay is idempotent across repeated runs with identical replay input.
- Replay output includes run correlation metadata for post-incident traceability.

Validation commands:

```bash
python -m pytest -q tests -k "wl327 or wl328 or wl331"
python -m pytest -q tests -k "replay and connector"
thegent replay --help
```

## Throttle Initiative

Applies to: WL-329, WL-330, WL-332

Acceptance criteria:

- Throttle policies enforce per-connector and global limits with deterministic backoff behavior.
- Telemetry exports include throttle decisions (allow, delay, drop) and bounded cardinality tags.
- Throttle saturation does not starve higher-priority recovery operations.

Validation commands:

```bash
python -m pytest -q tests -k "wl329 or wl330 or wl332"
python -m pytest -q tests -k "connector and throttle"
thegent metrics --help
```

## Completion Note

This document restores the missing evidence target for WL-321..WL-332 references under `docs/reference/WORK_STREAM.md` and records acceptance/validation gates for implementation and verification passes.
