# Worklog Wave 70 Lane 5 Triage Packet (2026-02-22)

## WL-259 - Operator Acceptance Tests

- Problem statement: End-to-end operator journeys for autosync (setup -> cycle run -> steady-state signals) are not covered, leaving regressions undetected at command/runtime boundaries.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/commands/sync.py`, `tests/e2e/test_next70_lane5.py`, `tests/test_wl160_workstream_autosync.py`.
- First concrete implementation step: Add one failing e2e test that executes operator bootstrap + one sync cycle and asserts status/report artifacts are produced.
- Verification command(s): `python -m pytest -q tests/e2e/test_next70_lane5.py`; `python -m pytest -q tests/test_wl160_workstream_autosync.py`.
- Risk note: E2E test flakiness from timing/async loops can create intermittent failures unless cycle timing is deterministic.

## WL-260 - Default Enablement Migration Plan

- Problem statement: Enabling autosync by default lacks a safe migration sequence for existing repos and current opt-in assumptions.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/config_defaults.py`, `src/thegent/integrations/connector_toggle.py`, `docs/reference/WORK_STREAM.md`.
- First concrete implementation step: Define explicit migration phases (detect current state, staged default-on, rollback trigger) and encode the phase-1 default gate in config defaults.
- Verification command(s): `python -m pytest -q tests/test_wl160_workstream_autosync.py`; `python -m pytest -q tests/test_wl131_feature_flags.py`.
- Risk note: Changing defaults can silently alter behavior in long-lived repos if migration state detection is incomplete.

## WL-222 - Blackout Calendar Support

- Problem statement: Autosync lacks project-level blackout windows to pause mutation during sensitive windows.
- Target code area(s): `src/thegent/integrations/maintenance_calendar.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/integrations/test_wl282_maintenance_calendar.py`.
- First concrete implementation step: Add project-scoped blackout window parsing and enforce a hard skip in sync cycle execution when blackout is active.
- Verification command(s): `python -m pytest -q tests/integrations/test_wl282_maintenance_calendar.py`; `python -m pytest -q tests/test_wl160_workstream_autosync.py -k maintenance`.
- Risk note: Timezone or boundary handling mistakes may skip valid sync windows or permit forbidden writes.

## WL-223 - Actor/Impersonation Guardrails

- Problem statement: Connector writes do not consistently enforce actor identity, allowing accidental or spoofed impersonation paths.
- Target code area(s): `src/thegent/agents/identity.py`, `src/thegent/infra/identity_proxy.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/infra/test_identity_proxy.py`.
- First concrete implementation step: Require actor identity fields at write boundaries and fail writes when identity validation or signature checks are missing/invalid.
- Verification command(s): `python -m pytest -q tests/infra/test_identity_proxy.py`; `python -m pytest -q tests/test_wl160_workstream_autosync.py`.
- Risk note: Over-strict validation may block legitimate automation paths until all connectors provide required identity metadata.

## WL-224 - Workstream Schema Linter

- Problem statement: WORK_STREAM structure errors are discovered late, causing parser/automation drift and brittle downstream tooling.
- Target code area(s): `src/thegent/commands/workstream.py`, `src/thegent/utils/workstream_ops.py`, `src/thegent/cli/commands/work_stream_impl.py`, `tests/test_workstream_ops.py`, `tests/test_plan_verify_workstream_cmd.py`.
- First concrete implementation step: Implement a schema-lint command that validates required sections/table shape and emits explicit failing diagnostics.
- Verification command(s): `python -m pytest -q tests/test_workstream_ops.py`; `python -m pytest -q tests/test_plan_verify_workstream_cmd.py`.
- Risk note: If lint rules are too rigid, valid but currently tolerated WORK_STREAM variants will start hard-failing.

## WL-225 - WL Sort/Normalize Command

- Problem statement: Manual edits produce unstable WL ordering/formatting, creating noisy diffs and merge conflicts.
- Target code area(s): `src/thegent/utils/workstream_ops.py`, `src/thegent/commands/workstream.py`, `src/thegent/cli/commands/work_stream_impl.py`, `tests/test_workstream_ops.py`.
- First concrete implementation step: Add deterministic sort + normalization logic (ID, status grouping, canonical spacing) with a CLI entrypoint.
- Verification command(s): `python -m pytest -q tests/test_workstream_ops.py`; `python -m pytest -q tests/test_workstream_helper.py`.
- Risk note: Normalization rewrites can unintentionally alter semantic fields if parser/serializer symmetry is not preserved.

## WL-226 - Remote Payload Checksums

- Problem statement: Reflection currently lacks payload-level integrity checks, so tampered or partial remote data can be applied.
- Target code area(s): `src/thegent/integrations/policy_checksum.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/integrations/test_wl312_policy_checksum.py`.
- First concrete implementation step: Compute and compare checksums on inbound/outbound reflection payloads before apply; fail cycle on mismatch.
- Verification command(s): `python -m pytest -q tests/integrations/test_wl312_policy_checksum.py`; `python -m pytest -q tests/test_wl160_workstream_autosync.py`.
- Risk note: Cross-system canonicalization differences may trigger false checksum mismatches unless serialization rules are fixed.

## WL-227 - Metadata Enrichment

- Problem statement: Reflected items are missing consistent source links/tags/metadata, reducing auditability and triage speed.
- Target code area(s): `src/thegent/integrations/sync_provenance.py`, `src/thegent/integrations/reflection_event_log.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/test_wl201_sync_provenance.py`.
- First concrete implementation step: Extend sync record stamping to include required source URL/tag metadata and propagate into reflection outputs.
- Verification command(s): `python -m pytest -q tests/test_wl201_sync_provenance.py`; `python -m pytest -q tests/test_wl261_sync_audit.py`.
- Risk note: Metadata schema growth can break consumers expecting minimal payloads unless versioned or contract-tested.

## WL-228 - Connector Capability Discovery

- Problem statement: Sync behavior gates are not derived from explicit connector capabilities, causing inconsistent behavior across connectors.
- Target code area(s): `src/thegent/contracts/capability_registry.py`, `src/thegent/agents/capability_index.py`, `src/thegent/integrations/capability_alerts.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/test_wl305_capability_alerts.py`.
- First concrete implementation step: Add runtime capability probe + cache and enforce capability checks before connector-specific operations execute.
- Verification command(s): `python -m pytest -q tests/test_wl305_capability_alerts.py`; `python -m pytest -q tests/test_wl160_workstream_autosync.py`.
- Risk note: Stale capability cache data can produce incorrect allow/deny decisions during connector incidents.

## WL-229 - Maintenance Banner Propagation

- Problem statement: Maintenance mode status is not consistently surfaced in CLI/report outputs, so operators miss degraded-mode context.
- Target code area(s): `src/thegent/integrations/maintenance_calendar.py`, `src/thegent/commands/sync.py`, `src/thegent/observability/async_logger.py`, `tests/test_sync_command.py`.
- First concrete implementation step: Add a shared maintenance-banner formatter and inject it into sync command/status/report render paths.
- Verification command(s): `python -m pytest -q tests/test_sync_command.py`; `python -m pytest -q tests/integrations/test_wl282_maintenance_calendar.py`.
- Risk note: Banner propagation can become noisy and obscure actionable output if not scoped to active maintenance conditions only.
