# Worklog Wave 70 Master Packet

Date: 2026-02-22
Execution split: 6 child agents x 10 items each + 10 items handled in main lane (70 total).

## Lane Files

1. `docs/reports/2026-02-22-worklog-wave70-lane1.md`
2. `docs/reports/2026-02-22-worklog-wave70-lane2.md`
3. `docs/reports/2026-02-22-worklog-wave70-lane3.md`
4. `docs/reports/2026-02-22-worklog-wave70-lane4.md`
5. `docs/reports/2026-02-22-worklog-wave70-lane5.md`
6. `docs/reports/2026-02-22-worklog-wave70-lane6.md`
7. `docs/reports/2026-02-22-worklog-wave70-lane7.md`

---

## Lane 1

# Lane 1 Triage Packet - Wave 70 (2026-02-22)

## WL-293 - Signed Capability Cache

- Problem statement: Capability cache objects exist but are not enforced at autosync execution boundaries, so stale/unsigned capability data can still drive connector operations.
- Target code area(s): `src/thegent/integrations/signed_capability_cache.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/integrations/test_wl293_signed_capability_cache.py`, `tests/test_wl160_workstream_autosync.py`.
- First concrete implementation step: Wire a `SignedCapabilityCache` instance into `WorkstreamAutosyncRunner` and gate GitHub/Linear sync paths with `get()/is_expired()` + explicit renewal/fail behavior.
- Verification command(s): `python -m pytest tests/integrations/test_wl293_signed_capability_cache.py -q`; `python -m pytest tests/test_wl160_workstream_autosync.py -k "checkpoint or failure_queue" -q`.
- Risk note: Signing key lifecycle/policy is currently unspecified; implementation can drift if key rotation semantics are not fixed first.

## WL-294 - Policy What-If Simulation

- Problem statement: Policy checking exists, but there is no deterministic command path that simulates proposed sync policy changes against realistic run/sync inputs.
- Target code area(s): `src/thegent/cli/commands/governance_cmds.py`, `src/thegent/execution.py` (`PolicyEngine`), `src/thegent/cli/commands/run_cmds.py`, `tests/commands/test_governance_commands_compat.py`.
- First concrete implementation step: Add a dedicated CLI surface (or extend `policy_check_cmd`) that accepts a proposed policy delta and evaluates it against synthesized `RunMeta` scenarios with machine-readable output.
- Verification command(s): `python -m pytest tests/commands/test_governance_commands_compat.py -k policy_check_cmd -q`; `python -m pytest tests/test_wl124_cli_split.py -k policy_check_cmd -q`.
- Risk note: Simulations that do not share the same evaluation path as production policy checks will produce false confidence.

## WL-295 - Pull Pagination Resilience Tests

- Problem statement: Pull remains stubbed and partition/checkpoint logic is untested for real multi-page pull edge cases (empty page, repeated cursor, mid-stream failure).
- Target code area(s): `src/thegent/commands/sync.py` (`pull`), `src/thegent/integrations/workstream_autosync.py` (`_sync_in_partitions`, checkpoint/failure queue), `tests/commands/test_sync.py`, `tests/test_wl160_workstream_autosync.py`.
- First concrete implementation step: Add failing tests that model multi-page pull responses and assert resume behavior after page-level failure using persisted checkpoint state.
- Verification command(s): `python -m pytest tests/commands/test_sync.py -k pull -q`; `python -m pytest tests/test_wl160_workstream_autosync.py -k "partition or checkpoint" -q`.
- Risk note: Cursor/offset semantics can diverge across connectors; tests must lock one canonical pagination contract before implementation.

## WL-296 - Restore Verifier

- Problem statement: Snapshot/rollback exists, but there is no dedicated verifier that proves restored outputs match expected checkpoint content and metadata.
- Target code area(s): `src/thegent/integrations/reflection_rollback.py`, `src/thegent/planning/work_stream.py`, `tests/integrations/test_wl185_reflection_rollback.py`, `tests/test_plan_verify_workstream_cmd.py`.
- First concrete implementation step: Add a restore verification function that compares restored workstream content/checksum against snapshot payload and returns explicit mismatch diagnostics.
- Verification command(s): `python -m pytest tests/integrations/test_wl185_reflection_rollback.py -q`; `python -m pytest tests/test_plan_verify_workstream_cmd.py -q`.
- Risk note: Restoring only file bytes without validating section-level invariants can reintroduce logically inconsistent state.

## WL-297 - Connector Cost Accounting

- Problem statement: Quota limits exist, but there is no per-connector cost ledger tied to autosync operations for budget visibility and forecasting.
- Target code area(s): `src/thegent/integrations/connector_quota.py`, `src/thegent/cost/tracker.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/test_wl221_connector_quota.py`, `tests/test_integration_cost_governance.py`.
- First concrete implementation step: Extend cost entry schema to include connector identifier and emit connector-scoped cost records from autosync read/write operations.
- Verification command(s): `python -m pytest tests/test_wl221_connector_quota.py -q`; `python -m pytest tests/test_integration_cost_governance.py -q`.
- Risk note: Missing provider-to-connector normalization will fragment totals and make budget reporting inaccurate.

## WL-299 - Reliability Score Targets

- Problem statement: Health/score utilities exist, but target thresholds and time-based reliability scoring for autosync are not concretely defined/enforced.
- Target code area(s): `src/thegent/governance/health_scorer.py`, `src/thegent/integrations/rollout_scorecard.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/test_governance_health_scorer.py`, `tests/integrations/test_wl320_rollout_scorecard.py`.
- First concrete implementation step: Define reliability dimensions (success rate, stale-checkpoint rate, failure-queue growth, recovery latency) in a committed targets config and score them in one report path.
- Verification command(s): `python -m pytest tests/test_governance_health_scorer.py -q`; `python -m pytest tests/integrations/test_wl320_rollout_scorecard.py -q`.
- Risk note: Thresholds that are not aligned to current baseline telemetry will either always pass or always fail.

## WL-300 - Default-On Guardrail Pack

- Problem statement: Guardrail/checklist pieces exist, but there is no packaged, default-on migration path that enables them consistently for autosync rollout.
- Target code area(s): `src/thegent/integrations/autosync_checklist.py`, `src/thegent/integrations/conflict_guardrails.py`, `src/thegent/governance/input_guardrails.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/test_wl200_autosync_checklist.py`, `tests/test_wl304_conflict_guardrails.py`.
- First concrete implementation step: Add a single guardrail preset/config loader that enables required checks by default and fails startup when required guardrails are disabled.
- Verification command(s): `python -m pytest tests/test_wl200_autosync_checklist.py -q`; `python -m pytest tests/test_wl304_conflict_guardrails.py -q`.
- Risk note: Enabling guardrails by default without a migration diff can break existing deployments unexpectedly.

## WL-262 - Failure Remediation Suggestions

- Problem statement: Failures are logged, but users do not get deterministic remediation guidance by failure class.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (`_record_failure`, `get_status`), `src/thegent/mcp/server_result_helpers.py`, `src/thegent/mcp/server/tools_workstream_lsp.py`, `tests/test_wl160_workstream_autosync.py`.
- First concrete implementation step: Introduce a failure-classifier map (`auth`, `rate_limit`, `network`, `validation`, `maintenance`) to attach remediation text at failure record creation time.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "failure_queue or get_status" -q`; `python -m pytest tests/test_hook_governance_gate_selector.py -q`.
- Risk note: Over-broad pattern matching can assign wrong remediation, increasing operator error during incidents.

## WL-263 - Credential Source Validator

- Problem statement: Credential precedence is implicit and first-non-empty; ambiguous multi-source auth config is not rejected early.
- Target code area(s): `src/thegent/config_parsers.py` (`parse_first_nonempty_env`), `src/thegent/config.py` validators, `src/thegent/mcp/server/auth.py`, `tests/test_unit_config.py`.
- First concrete implementation step: Add strict credential source validation that errors when multiple mutually exclusive credential sources are simultaneously set for one auth surface.
- Verification command(s): `python -m pytest tests/test_unit_config.py -q`; `python -m pytest tests/commands/test_governance_commands_compat.py -k policy_check_cmd -q`.
- Risk note: Enforcing ambiguity checks can break currently tolerated env setups; rollout needs explicit migration notes.

## WL-264 - WL Block Formatter

- Problem statement: WL block parsing is permissive and no strict formatter enforces canonical block structure/metadata normalization.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (`WorkstreamParser`), `src/thegent/cli/services/run_workstream_helpers.py`, `src/thegent/planning/work_stream.py`, `tests/test_wl160_workstream_autosync.py`, `tests/test_plan_verify_workstream_cmd.py`.
- First concrete implementation step: Add a formatter that rewrites each `### [WL-xxx]` block into canonical metadata order and normalized field values, then expose it via a verify/fix command mode.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k parse -q`; `python -m pytest tests/test_plan_verify_workstream_cmd.py -q`.
- Risk note: Auto-formatting may alter hand-edited comments/spacing unless block boundaries are parsed losslessly.

---

## Lane 2

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

---

## Lane 3

# Worklog Wave 70 Lane 3 Triage Packet

Date: 2026-02-22
Scope: WL-276, WL-277, WL-278, WL-242, WL-243, WL-244, WL-245, WL-246, WL-247, WL-248

## WL-276 - Artifact Redaction Pipeline

- Problem statement: Sync/report artifacts can leak secrets or sensitive identifiers because no deterministic redaction pass runs before write/export.
- Target code area(s): `src/thegent/integrations/confidential_report.py`, `src/thegent/maif/artifact_generator.py`, `src/docs_engine/export/json_export.py`, `tests/` (new redaction tests).
- First concrete implementation step: Add a strict redaction policy map (field-name + regex rules) and apply it in the artifact serialization path before any file write.
- Verification command(s): `python -m pytest tests/test_wl276_artifact_redaction.py -q`; `python -m pytest tests/test_wl160_workstream_autosync.py -q`
- Risk note: Over-redaction can remove operationally required fields and make audit artifacts unusable.

## WL-277 - Artifact Format Versioning

- Problem statement: Artifact consumers have no explicit schema contract, so format changes can silently break downstream parsers.
- Target code area(s): `src/docs_engine/export/json_export.py`, `src/thegent/maif/artifacts.py`, `schemas/`, `tests/` (new schema/version compatibility tests).
- First concrete implementation step: Introduce required top-level `schema_version` in every emitted artifact and reject artifacts missing/unknown versions on import.
- Verification command(s): `python -m pytest tests/test_wl277_artifact_versioning.py -q`; `python -m pytest tests/docs_engine/test_cli.py -q`
- Risk note: Version gate can block existing artifacts unless migration/upgrade path is clearly defined.

## WL-278 - Operator Command Aliases

- Problem statement: Frequent operator workflows require long command paths, slowing triage and increasing CLI typo rate.
- Target code area(s): `src/thegent/terminal_cli.py`, `src/thegent/shell_cli.py`, `tests/test_e2e_cli_aliases.py`.
- First concrete implementation step: Register explicit short aliases that map 1:1 to existing commands without changing command behavior or output schema.
- Verification command(s): `python -m pytest tests/test_e2e_cli_aliases.py -q`; `python -m pytest tests/test_unit_cli.py -q`
- Risk note: Alias collisions can shadow existing commands and create ambiguous help text.

## WL-242 - Immutable Cycle Manifest

- Problem statement: Autosync cycles are not captured in immutable manifests, reducing reproducibility and post-incident audit confidence.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/sync_auditor.py`, `artifacts/`, `tests/` (new manifest immutability tests).
- First concrete implementation step: Emit one append-only cycle manifest per run containing inputs, decisions, outputs, and hash digest.
- Verification command(s): `python -m pytest tests/test_wl242_cycle_manifest.py -q`; `python -m pytest tests/test_wl261_sync_audit.py -q`
- Risk note: Manifest size and write frequency can increase I/O cost in short-cycle environments.

## WL-243 - Dual-Write Shadow Mode

- Problem statement: Direct external mutation has no observe-only probation phase, increasing rollout blast radius.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/gh_project_sync.py`, `src/thegent/commands/sync.py` (direction/control flags), `tests/` (shadow mode behavior tests).
- First concrete implementation step: Add `shadow_mode` config that computes and logs outbound mutations but blocks remote writes.
- Verification command(s): `python -m pytest tests/test_wl243_dual_write_shadow.py -q`; `python -m pytest tests/test_wl160_workstream_autosync.py -q`
- Risk note: Divergence can grow between observed and actual remote state if shadow mode is left enabled too long.

## WL-244 - HTML Diff Artifact

- Problem statement: Local-vs-remote state differences are hard to review quickly in plain logs or JSON.
- Target code area(s): `src/thegent/integrations/sync_auditor.py`, `src/thegent/maif/artifact_generator.py`, `docs/reports/` artifact output path, `tests/` (HTML diff generation tests).
- First concrete implementation step: Generate deterministic side-by-side HTML diff output from normalized local/remote snapshots after each compare pass.
- Verification command(s): `python -m pytest tests/test_wl244_html_diff_artifact.py -q`; `python -m pytest tests/test_wl261_sync_audit.py -q`
- Risk note: Large diffs can produce oversized HTML artifacts and slow report rendering.

## WL-245 - Ownership Metadata Propagation

- Problem statement: Ownership fields drift across local workstream, GitHub, and Linear, making escalation routing unreliable.
- Target code area(s): `src/thegent/commands/workstream.py`, `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/sync_provenance.py`, `tests/` (ownership roundtrip tests).
- First concrete implementation step: Define canonical owner field mapping and enforce it in both local parse/write and remote adapter payload transforms.
- Verification command(s): `python -m pytest tests/test_wl245_ownership_propagation.py -q`; `python -m pytest tests/test_wl201_sync_provenance.py -q`
- Risk note: Inconsistent owner identity formats (handle/email/display-name) can cause false mismatches.

## WL-246 - Env Profile Drift Validator

- Problem statement: Dev/staging/prod autosync profiles can diverge undetected, causing environment-specific failures.
- Target code area(s): `src/thegent/phases/compliance_profile.py`, `src/thegent/commands/audit.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/governance/` and `tests/` validator tests.
- First concrete implementation step: Add profile diff validator that compares required autosync keys and fails on non-whitelisted drift.
- Verification command(s): `python -m pytest tests/test_wl246_env_profile_drift.py -q`; `python -m pytest tests/governance/test_compliance_profiles.py -q`
- Risk note: Strict drift checks can block legitimate temporary overrides during incident response.

## WL-247 - Legacy Board ID Migration Tool

- Problem statement: Legacy board identifiers are not normalized into WL namespace, producing unstable cross-system linkage.
- Target code area(s): `src/thegent/integrations/board_id_guard.py`, `src/thegent/integrations/board_id_uniqueness.py`, `src/thegent/commands/sync.py`, `tests/` migration CLI tests.
- First concrete implementation step: Implement a dedicated migration subcommand that parses legacy IDs, validates uniqueness, and writes canonical WL IDs.
- Verification command(s): `python -m pytest tests/test_wl247_board_id_migration.py -q`; `python -m pytest tests/test_sync_command.py -q`
- Risk note: One-way migration without preview/backup can orphan references if parsing rules are wrong.

## WL-248 - Remote-Orphan Detector

- Problem statement: Remote tracker items without local WORK_STREAM representation remain invisible to local planning and quality gates.
- Target code area(s): `src/thegent/commands/sync.py`, `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/sync_auditor.py`, `tests/` orphan detection tests.
- First concrete implementation step: Add detector pass that diffs remote item IDs against parsed local WL IDs and emits a structured orphan report.
- Verification command(s): `python -m pytest tests/test_wl248_remote_orphan_detector.py -q`; `python -m pytest tests/test_sync_command.py -q`
- Risk note: API pagination or filtered queries can create false orphan positives.

---

## Lane 4

# Worklog Wave 70 - Lane 4 Triage Packet (2026-02-22)

## WL-249 - Local-Orphan Detector

- Problem statement: Local `WORK_STREAM.md` items can exist without any remote tracker mapping, creating silent divergence between local and connector state.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/connector_mapping_cache.py`, `src/thegent/cli/apps/sync.py` (`sync audit`/`autopilot-status`).
- First concrete implementation step: Add a detector pass in autosync cycle that computes `local_ids - mapped_remote_ids` and emits a structured orphan report payload.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py`; `python -m pytest tests/test_wl261_sync_audit.py`.
- Risk note: False positives if mapping cache is stale or partially loaded during cycle boundaries.

## WL-250 - Conflict TTL and Escalation

- Problem statement: Cross-connector conflicts can persist indefinitely without a hard timeout and escalation signal.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (failure queue/checkpoint path), `src/thegent/integrations/cross_connector_verifier.py`, `src/thegent/cli/apps/sync.py` (`sync status`).
- First concrete implementation step: Extend conflict records with `first_seen_at` and `ttl_seconds`, then mark conflicts as escalated once TTL is exceeded.
- Verification command(s): `python -m pytest tests/test_wl301_cross_connector_verifier.py`; `python -m pytest tests/test_wl160_workstream_autosync.py -k "checkpoint or maintenance"`.
- Risk note: Incorrect TTL defaults can over-escalate transient connector lag.

## WL-251 - Retry Class Policy

- Problem statement: Retry behavior is not explicitly classified by error type, causing wasted retries on permanent failures.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (`_record_failure`, partition sync), `src/thegent/integrations/connector_quota.py`, `src/thegent/integrations/sync_auditor.py`.
- First concrete implementation step: Introduce a strict error classifier (`transient`, `rate_limit`, `permanent`) and route retry/backoff decisions from that class.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py`; `python -m pytest tests/test_wl261_sync_audit.py`.
- Risk note: Misclassification can either starve recoverable operations or create retry storms.

## WL-252 - Offline Simulation Mode

- Problem statement: There is no deterministic offline simulation path for verifying connector logic without live credentials.
- Target code area(s): `src/thegent/cli/apps/sync.py` (`sync autopilot`), `src/thegent/integrations/workstream_autosync.py`, `src/thegent/commands/sync.py`.
- First concrete implementation step: Add an explicit simulation mode flag that forces connector adapters into local stub mode while still executing full cycle orchestration.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "graceful_skip or load_with"`; `python -m pytest tests/commands/test_sync.py`.
- Risk note: Simulation behavior can drift from production connector contracts if not schema-locked.

## WL-253 - Snapshot Compaction

- Problem statement: Long-running autosync artifacts/checkpoints can accumulate and bloat `docs/reference` storage.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (status/failure/checkpoint file writers), `src/thegent/cli/apps/sync.py` (`sync rollback`), `src/thegent/planning/workstream_db.py`.
- First concrete implementation step: Add retention policy constants (count/time window) and prune old snapshot artifacts immediately after successful cycle completion.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "checkpoint"`; `python -m pytest tests/test_sync_command.py`.
- Risk note: Aggressive compaction can remove forensic evidence needed for incident recovery.

## WL-254 - Encrypted Artifact Option

- Problem statement: Sync artifacts are written in plaintext by default, which may violate stricter compliance requirements.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (`_write_status_snapshot`, failure/checkpoint writes), `src/thegent/config.py`, `src/thegent/cli/apps/sync.py` (`autopilot-status`).
- First concrete implementation step: Add config-gated artifact writer abstraction with mandatory key presence checks before enabling encryption-at-rest.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py`; `python -m pytest tests/commands/test_sync.py -k "status"`.
- Risk note: Key management mistakes can make status artifacts unreadable and degrade operability.

## WL-255 - Run Correlation IDs

- Problem statement: Sync events across connectors lack a shared run-level correlation identifier, limiting traceability.
- Target code area(s): `src/thegent/integrations/sync_provenance.py`, `src/thegent/integrations/workstream_autosync.py`, `src/thegent/cli/apps/sync.py` (`status`/`autopilot-status`).
- First concrete implementation step: Generate a run UUID at cycle start and stamp it into all provenance/event records emitted in that cycle.
- Verification command(s): `python -m pytest tests/test_wl201_sync_provenance.py`; `python -m pytest tests/test_wl160_workstream_autosync.py`.
- Risk note: Partial propagation across code paths can create mixed correlated/uncorrelated logs.

## WL-256 - No-Op Fast Path

- Problem statement: Unchanged cycles still traverse expensive sync stages instead of exiting early with explicit no-op telemetry.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py` (`_perform_sync_cycle`), `src/thegent/cli/apps/sync.py` (`autopilot-status` output).
- First concrete implementation step: Add pre-sync diff check and early return path that records `no_op=true`, reason, and skipped connector counts.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "no work stream items"`; `python -m pytest tests/commands/test_sync.py`.
- Risk note: Overly broad no-op detection can incorrectly suppress legitimate outbound updates.

## WL-257 - Historical Trend Reports

- Problem statement: Operators cannot quickly inspect longitudinal drift/error/latency behavior for autosync cycles.
- Target code area(s): `src/thegent/governance/slo_trend.py`, `src/thegent/cli/commands/output/health_trend_jsonl_serializer.py`, `src/thegent/cli/commands/output/health_trend_csv_serializer.py`, `src/thegent/cli/apps/sync.py`.
- First concrete implementation step: Define a normalized cycle-metrics schema and persist one trend sample per completed autosync cycle.
- Verification command(s): `python -m pytest tests/governance/test_wl135_slo_trend.py`; `python -m pytest tests/test_unit_health_trend.py`; `python -m pytest tests/test_e2e_health_trend_cli.py`.
- Risk note: Metric-cardinality growth can inflate storage and degrade report generation latency.

## WL-258 - Docs Freshness Checker

- Problem statement: Sync command docs can drift from implemented CLI behavior and status contract fields.
- Target code area(s): `docs/reference/api/cli_sync_api.md`, `docs/reference/api/sync_api.md`, `src/thegent/cli/apps/sync.py`, `tests/e2e/test_governance_sync_contracts.py`.
- First concrete implementation step: Add a docs-freshness assertion that compares declared sync/autopilot command surfaces against Typer command registration and key status fields.
- Verification command(s): `python -m pytest tests/e2e/test_governance_sync_contracts.py`; `python -m pytest tests/commands/test_sync.py`.
- Risk note: Tight doc/runtime parity checks can become brittle if command help text changes frequently.

---

## Lane 5

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

---

## Lane 6

# Worklog Wave 70 Lane 6 Triage Packet

## WL-230 Emergency Stop Switch

- Problem statement: Autosync currently lacks a hard operator kill-switch, so bad sync cycles can continue writing after a critical incident is detected.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/commands/sync.py`, `tests/test_wl160_workstream_autosync.py`.
- First concrete implementation step: Add an `is_emergency_stop_enabled()` guard (env var + sentinel file) and fail fast at the first write-capable autosync entrypoint.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "emergency_stop or stop_switch"`
- Risk note: A mis-scoped guard can block non-mutating status/report flows if inserted too high in the call graph.

## WL-231 Replay-Safe Mutation IDs

- Problem statement: Replayed sync operations can apply duplicate remote mutations because write events do not carry stable operation IDs.
- Target code area(s): `src/thegent/integrations/workstream_autosync.py`, `src/thegent/integrations/idempotency_cache.py`, `tests/test_wl166_idempotency_cache.py`.
- First concrete implementation step: Thread a deterministic `mutation_id` into each remote write request and persist completion state in `IdempotencyCache` before acknowledging success.
- Verification command(s): `python -m pytest tests/test_wl166_idempotency_cache.py tests/test_wl160_workstream_autosync.py -k "mutation_id or replay"`
- Risk note: ID derivation that includes unstable fields (timestamps/randomness) will break replay protection and cause false misses.

## WL-232 Signed Audit Artifact Chain

- Problem statement: Audit outputs are not cryptographically chained, so tamper-evidence and provenance guarantees are insufficient for compliance use.
- Target code area(s): `src/thegent/integrations/sync_provenance.py`, `src/thegent/integrations/signed_capability_cache.py`, `src/thegent/integrations/sync_auditor.py`, `tests/test_wl261_sync_audit.py`.
- First concrete implementation step: Extend artifact metadata with `prev_hash` + signature fields and verify chain continuity on each append.
- Verification command(s): `python -m pytest tests/test_wl261_sync_audit.py -k "signature or chain or provenance"`
- Risk note: Key lifecycle/rotation gaps can invalidate otherwise-correct chains and create operational lockouts.

## WL-233 Connector SLA Tracking

- Problem statement: Connector latency/error thresholds are not continuously scored against SLA budgets, delaying breach detection.
- Target code area(s): `src/thegent/integrations/pipeline_percentiles.py`, `src/thegent/integrations/error_budget.py`, `src/thegent/integrations/capability_alerts.py`, `tests/integrations/test_wl306_connector_toggle.py`.
- First concrete implementation step: Emit per-connector rolling latency/error windows and evaluate them against explicit SLA thresholds in one evaluator.
- Verification command(s): `python -m pytest tests/integrations/test_wl306_connector_toggle.py -k "sla or latency or error_budget"`
- Risk note: Windowing mismatches (sample interval vs alert interval) can cause noisy false positives.

## WL-234 Incident Runbook

- Problem statement: Autosync incident and rollback handling is not codified in a single operator runbook, creating response variability.
- Target code area(s): `docs/site/operations/runbooks.md`, `src/thegent/integrations/reflection_rollback.py`, `src/thegent/commands/sync.py`.
- First concrete implementation step: Add a dedicated “Autosync Incident/Recovery” section with trigger conditions, rollback commands, and validation checkpoints.
- Verification command(s): `rg -n "autosync|incident|rollback" docs/site/operations/runbooks.md && python -m pytest tests/test_wl160_workstream_autosync.py -k rollback`
- Risk note: Documentation drift versus actual CLI behavior can make runbook steps unsafe during live incidents.

## WL-235 Connector Chaos Tests

- Problem statement: Connector outage and partial-failure behavior is under-tested, so resilience regressions can ship unnoticed.
- Target code area(s): `src/thegent/integrations/latency_chaos.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/test_wl160_workstream_autosync.py`, `tests/integrations/test_wl306_connector_toggle.py`.
- First concrete implementation step: Add deterministic chaos fixtures (timeout, 5xx, partial ack) and assert retry/backoff/escalation behavior per connector.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py tests/integrations/test_wl306_connector_toggle.py -k "chaos or outage or partial"`
- Risk note: Non-deterministic fault injection can destabilize CI and hide true regressions behind flaky failures.

## WL-236 Cold/Warm Benchmark Split

- Problem statement: Benchmark reporting mixes cold-start and warm-cache runs, obscuring real runtime performance deltas.
- Target code area(s): `scripts/benchmark_python_suite.py`, `scripts/benchmark-report.py`, `benchmarks/results/python/latest.json`, `tests/performance/test_python_benchmark_suite.py`.
- First concrete implementation step: Add explicit benchmark mode tagging (`cold`, `warm`) and emit split aggregates in report generation.
- Verification command(s): `python scripts/benchmark_python_suite.py --help && python -m pytest tests/performance/test_python_benchmark_suite.py -k "cold or warm"`
- Risk note: Cache state leakage between modes can invalidate comparison accuracy.

## WL-237 Hourly Change Digest

- Problem statement: Operators lack compact hourly summaries of local/remote delta activity, slowing situational awareness.
- Target code area(s): `src/research_engine/digest.py`, `src/thegent/integrations/decision_journal.py`, `src/thegent/integrations/workstream_autosync.py`, `tests/research_engine/test_digest.py`.
- First concrete implementation step: Introduce an hourly digest builder that groups mutation events by connector, action type, and outcome.
- Verification command(s): `python -m pytest tests/research_engine/test_digest.py tests/test_wl160_workstream_autosync.py -k "hourly or digest"`
- Risk note: Over-aggregation can hide critical low-volume failures if digest bucketing is too coarse.

## WL-238 Remote→Local Annotation Standard

- Problem statement: Reflection annotations are inconsistent across outputs, reducing parseability and review reliability.
- Target code area(s): `src/thegent/docgen/code_annotation.py`, `src/thegent/integrations/reflection_event_log.py`, `docs/reference/api/code_annotation_api.md`.
- First concrete implementation step: Define one canonical annotation schema (required keys/order) and route all reflection emitters through the shared formatter.
- Verification command(s): `python -m pytest tests/test_wl160_workstream_autosync.py -k "annotation or reflection" && rg -n "annotation" docs/reference/api/code_annotation_api.md`
- Risk note: Tight schema enforcement can break downstream consumers that implicitly depend on legacy field names.

## WL-239 Staged Rollout Profiles

- Problem statement: Rollout controls are not packaged as environment-specific profiles, so safe defaults are inconsistently applied.
- Target code area(s): `src/thegent/integrations/rollout_scorecard.py`, `src/thegent/integrations/reconciliation_policy.py`, `src/thegent/integrations/status_hysteresis.py`, `tests/integrations/test_wl320_rollout_scorecard.py`.
- First concrete implementation step: Add explicit `dev/staging/prod` rollout profile objects with strict defaults and profile validation at load time.
- Verification command(s): `python -m pytest tests/integrations/test_wl320_rollout_scorecard.py -k "profile or staged or rollout"`
- Risk note: Incorrect default thresholds can either over-block production rollout or permit unsafe promotion.

---

## Lane 7

# Worklog Wave 70 - Lane 7 (WL-240, WL-203..WL-212)

Date: 2026-02-22
Scope: implementation-ready triage for 10 backlog items.

## WL-240 — GA Readiness Criteria

Problem statement:
Define GA/default-on criteria and final readiness review checklist.
Target code areas:
src/thegent/cli/commands/sync.py, src/thegent/cli/commands/doctor.py, docs/reference/WORK_STREAM.md
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_autosync_doctor.py tests/test_cli_sync.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-203 — Local Decision Journal

Problem statement:
Persist replayable journal entries for each sync decision.
Target code areas:
src/thegent/sync/, src/thegent/core/logging.py, docs/reference/api/backlog_api.md
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_journal.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-204 — Conflict Surface Command

Problem statement:
Add CLI command to list unresolved sync conflicts and recommended actions.
Target code areas:
src/thegent/cli/commands/sync.py, src/thegent/sync/conflicts.py
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_conflicts.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-205 — Manual Conflict Queue

Problem statement:
Add machine-readable conflict queue file for deterministic manual resolution.
Target code areas:
src/thegent/sync/queue.py, src/thegent/cli/commands/sync.py
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_queue.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-206 — Sync Freeze/Unfreeze Controls

Problem statement:
Add maintenance controls to pause and resume automatic sync safely.
Target code areas:
src/thegent/sync/controller.py, src/thegent/cli/commands/sync.py
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_controller.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-208 — Max-Changes Per Cycle Guardrail

Problem statement:
Cap per-cycle mutation volume with explicit fail-loud behavior when exceeded.
Target code areas:
src/thegent/sync/engine.py, src/thegent/config.py
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_engine.py -k max_changes`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-209 — Connector Health Scoreboard

Problem statement:
Publish connector health and drift scores in CLI/report artifacts.
Target code areas:
src/thegent/sync/health.py, src/thegent/cli/commands/sync.py
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_health.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-210 — Field/Schema Drift Detection

Problem statement:
Detect remote field/schema changes that invalidate current sync mappings.
Target code areas:
src/thegent/sync/schema.py, src/thegent/connectors/
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_schema_drift.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-211 — Required Field Validation Gate

Problem statement:
Add strict validation that required custom fields exist before external writes.
Target code areas:
src/thegent/sync/validation.py, src/thegent/connectors/
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_required_field_validation.py`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.

## WL-212 — Pull-Only-on-Failure Mode

Problem statement:
Add explicit, visible pull-only mode for degraded write conditions.
Target code areas:
src/thegent/sync/engine.py, src/thegent/sync/retry.py
First concrete implementation step:
Create failing unit tests for the core behavior first, then implement the minimal production path to satisfy those tests.
Verification command(s):
`uv run python -m pytest -q tests/test_unit_sync_retry.py -k pull_only`
Risk note:
Cross-connector behavior can diverge; enforce deterministic fixtures and schema contracts before broad rollout.
