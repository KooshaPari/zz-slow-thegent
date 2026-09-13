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
