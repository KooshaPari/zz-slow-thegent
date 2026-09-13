# Autosync Troubleshooting Matrix

## Purpose

Quick operator reference for common autosync failures across local workstream, GitHub, and Linear integrations.

## Matrix

| Symptom                                       | Likely Cause                                 | Diagnostics                                                               | Fix                                                                |
| --------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| GitHub issue sync fails with 401/403          | Missing/expired token or insufficient scopes | Check `thegent sync autopilot-status`; verify env/token source and scopes | Refresh token, re-run auth setup, verify repo/project permissions  |
| Linear writes fail with auth error            | Wrong team key or expired token              | Check connector health output and auth source resolution                  | Rotate token and validate team/workspace binding                   |
| Items stuck in conflict queue                 | Local and remote changed same fields         | Inspect conflict bundle + cycle artifacts                                 | Apply conflict policy, resolve manually, re-run single cycle       |
| Repeated retries with no progress             | Connector degraded or rate limited           | Review error classes and retry counters                                   | Enable selective retry, increase backoff, pause degraded connector |
| Local status differs from remote after apply  | Partial write or stale metadata              | Compare cycle manifests and transition history log                        | Reconcile with replay from last good checkpoint                    |
| Missing remote item for local WL entry        | Orphan mapping                               | Run orphan detection commands and mapping checks                          | Create/repair mapping, then sync                                   |
| Missing local WL for remote item              | Remote orphan not imported                   | Run remote-orphan scan                                                    | Import into WL namespace and attach ownership metadata             |
| Sync loop too slow                            | Overloaded connector or high drift volume    | Check cycle duration, batch size, queue depth                             | Reduce batch size, isolate connector, tune interval policy         |
| HTML/report artifacts expose sensitive fields | Missing redaction policy                     | Inspect generated artifact fields                                         | Apply redaction policy pack and regenerate artifacts               |

## Standard Diagnostic Sequence

1. `thegent sync work-stream`
2. `thegent sync autopilot --once`
3. `thegent sync autopilot-status`
4. Inspect latest cycle artifacts and conflict queue
5. Apply targeted remediation, then re-run single-cycle sync

## Escalation Rules

- Escalate immediately for auth failures across multiple connectors.
- Escalate if conflict queue grows for 3 consecutive cycles.
- Escalate if state divergence persists after a checkpoint restore verification.
