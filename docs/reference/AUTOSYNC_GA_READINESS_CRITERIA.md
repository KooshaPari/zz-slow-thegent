# Autosync GA Readiness Criteria

## Objective

Define hard gates for declaring autosync generally available (GA) and default-on capable.

## Reliability Gates

- Error-rate threshold stays below agreed target for 14 consecutive days.
- No unresolved P1 sync conflicts older than SLA threshold.
- Checkpoint restore verification passes in staging and production-like rehearsal.

## Safety Gates

- Emergency stop controls validated in staging and production.
- Max-changes-per-cycle guardrail enabled and tested.
- Required-field validation gate enabled for all write-enabled connectors.

## Operability Gates

- Incident runbook and troubleshooting matrix published and validated by operators.
- Connector health scoreboard and trend reporting active in status artifacts.
- Alert routing for SLA breaches and escalation TTL events is verified.

## Compliance/Audit Gates

- Signed/immutable cycle artifacts enabled where policy requires.
- Artifact redaction rules enforced for exported reports.
- Ownership metadata propagation audited across local/GitHub/Linear mappings.

## Release Decision

GA can proceed only when all categories above are green with explicit evidence links in `WORK_STREAM.md`.
