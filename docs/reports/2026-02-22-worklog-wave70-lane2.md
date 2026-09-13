# Worklog Wave 70 Lane 2 Triage Packet (2026-02-22)

## WL-265 Field Mapping Bootstrap Wizard

- Problem statement: First-run autosync setup lacks guided field/state mapping, causing misconfigured connector mappings and early drift.
- Target code area(s): `src/thegent/integrations/connector_mapping_cache.py`, `src/thegent/integrations/workstream_autosync.py`, `src/thegent/cli/apps/sync.py`, `src/thegent/config.py`, `tests/integrations/test_wl191_connector_mapping_cache.py`.
- First concrete implementation step: Add a `bootstrap_required()` gate in mapping cache + CLI wizard entrypoint in `thegent sync autopilot` that collects and persists minimum required field/state mappings before first apply.
- Verification command(s): `python -m pytest tests/integrations/test_wl191_connector_mapping_cache.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k mapping`; `python -m pytest tests/commands/test_sync.py -k autopilot`.
- Risk note: Incorrect normalization between connector schemas can lock in bad mappings and amplify downstream sync conflicts.

## WL-266 Pre-Apply Connector Health Probe

- Problem statement: Apply cycles can run against degraded connectors, converting known connector outages into avoidable failed writes.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/connector_toggle.py`, `src/thegent/integrations/connector_quota.py`, `tests/test_wl160_workstream_autosync.py`, `tests/integrations/test_wl306_connector_toggle.py`.
- First concrete implementation step: Insert a mandatory pre-apply `probe_connectors()` phase in the autosync cycle runner that hard-fails the apply phase when health state is degraded.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "health or probe"`; `python -m pytest tests/integrations/test_wl306_connector_toggle.py`; `python -m pytest tests/test_wl221_connector_quota.py`.
- Risk note: Probe strictness can produce false positives and unnecessary pauses if timeout and degradation thresholds are not tuned.

## WL-267 Adaptive Sync Interval Controller

- Problem statement: Fixed sync intervals either overload connectors under turbulence or waste cycles when drift is low.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/rescan_scheduler.py`, `src/research_engine/scheduler.py`, `src/thegent/config.py`, `tests/test_wl207_rescan_scheduler.py`.
- First concrete implementation step: Introduce an interval policy function that computes next cycle delay from drift/error/load metrics and wire it into runner sleep scheduling.
- Verification command(s): `python -m pytest tests/test_wl207_rescan_scheduler.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k interval`; `python -m pytest tests/research_engine/test_scheduler.py`.
- Risk note: Aggressive interval shrink can trigger feedback loops (more retries -> more load -> tighter loops).

## WL-268 Incident Snapshot Bundle

- Problem statement: Postmortems lack immutable, cycle-scoped incident bundles tying failures, policies, and connector state into one artifact.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/sync_auditor.py`, `src/thegent/sync/audit_framework.py`, `tests/test_wl261_sync_audit.py`.
- First concrete implementation step: Add a `build_incident_snapshot_bundle(cycle_ctx)` path that writes append-only snapshot artifacts with policy hash, connector health, errors, and mutation summary.
- Verification command(s): `python -m pytest tests/test_wl261_sync_audit.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k incident`; `python -m pytest tests/test_sync_work_stream.py -k audit`.
- Risk note: Snapshot payloads can leak sensitive connector metadata if redaction boundaries are not enforced.

## WL-269 Conflict Triage Categories

- Problem statement: Conflict events are not categorized by severity/owner, delaying routing and response in high-conflict periods.
- Target code area(s): `src/thegent/integrations/conflict_queue.py`, `src/thegent/integrations/conflict_guardrails.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/integrations/test_wl205_conflict_queue.py`, `tests/test_wl304_conflict_guardrails.py`.
- First concrete implementation step: Add deterministic conflict classification (`category`, `severity`, `owner_domain`) at conflict enqueue time and surface it in cycle outputs.
- Verification command(s): `python -m pytest tests/integrations/test_wl205_conflict_queue.py`; `python -m pytest tests/test_wl304_conflict_guardrails.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k conflict`.
- Risk note: Misclassification rules can route urgent integrity incidents to low-priority queues.

## WL-270 Metadata Freshness TTL

- Problem statement: Stale connector metadata can be applied as current truth, causing outdated mappings and incorrect reconciliation.
- Target code area(s): `src/thegent/integrations/connector_mapping_cache.py`, `src/thegent/routing/model_metadata.py`, `src/thegent/integrations/workstream_autosync.py`, `src/thegent/config.py`, `tests/test_router_metadata.py`.
- First concrete implementation step: Add metadata TTL validation at read boundaries and stamp stale entries with explicit marker status before use.
- Verification command(s): `python -m pytest tests/test_router_metadata.py`; `python -m pytest tests/integrations/test_wl191_connector_mapping_cache.py -k ttl`; `python -m pytest tests/test_wl160_workstream_autosync.py -k metadata`.
- Risk note: TTL invalidation can cause bursty refresh traffic and temporary sync slowdowns during cache churn.

## WL-271 Split-Brain Remote State Detector

- Problem statement: Divergent remote state across connectors for the same board item can persist undetected and corrupt downstream reflection.
- Target code area(s): `src/thegent/integrations/cross_connector_verifier.py`, `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/sync_provenance.py`, `tests/test_wl301_cross_connector_verifier.py`.
- First concrete implementation step: Extend cross-connector verifier with per-item state fingerprint comparison and emit split-brain findings into conflict/audit channels.
- Verification command(s): `python -m pytest tests/test_wl301_cross_connector_verifier.py`; `python -m pytest tests/test_wl201_sync_provenance.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k "split or brain"`.
- Risk note: Fingerprint fields must be stable and canonicalized, or harmless representation differences will produce false alarms.

## WL-273 Selective Retry Queue

- Problem statement: Current retry handling can replay successful writes when retrying transient failures, increasing duplicate mutations.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/conflict_queue.py`, `src/thegent/task_queue/queue.py`, `src/thegent/queue/storage.py`, `tests/mesh/test_task_queue.py`.
- First concrete implementation step: Add retry queue records keyed by operation id + failure class, enqueue only transient failures, and skip already-acknowledged successful operations.
- Verification command(s): `python -m pytest tests/mesh/test_task_queue.py`; `python -m pytest tests/integrations/test_wl205_conflict_queue.py -k retry`; `python -m pytest tests/test_wl160_workstream_autosync.py -k retry`.
- Risk note: Incorrect idempotency keys can either suppress required retries or duplicate writes.

## WL-274 Connector Sandbox Project Mode

- Problem statement: Connector validation currently risks touching production targets when testing new mappings/policies.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/gh_project_sync.py`, `src/thegent/config.py`, `src/thegent/cli/apps/sync.py`, `tests/test_wl157_gh_project_sync.py`.
- First concrete implementation step: Add explicit sandbox target configuration and enforce connector writes to sandbox project IDs when sandbox mode is enabled.
- Verification command(s): `python -m pytest tests/test_wl157_gh_project_sync.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k sandbox`; `python -m pytest tests/commands/test_sync.py -k sandbox`.
- Risk note: Mis-bound sandbox/production IDs can cause cross-environment contamination.

## WL-275 CI Benchmark Gates

- Problem statement: CI currently lacks hard regression gates for autosync latency and throughput.
- Target code area(s): `Taskfile.yml`, `tests/performance/test_python_benchmark_suite.py`, `tests/performance/test_python_benchmark_regression.py`, `tests/test_benchmark_harness.py`, `tests/test_benchmark_report.py`.
- First concrete implementation step: Define baseline thresholds and add a CI quality target that fails when benchmark regression tests exceed permitted latency/throughput deltas.
- Verification command(s): `python -m pytest tests/performance/test_python_benchmark_suite.py`; `python -m pytest tests/performance/test_python_benchmark_regression.py`; `python -m pytest tests/test_benchmark_harness.py tests/test_benchmark_report.py`; `task quality`.
- Risk note: Noisy benchmark environments can create flaky gate failures unless variance windows and warmup controls are explicit.
