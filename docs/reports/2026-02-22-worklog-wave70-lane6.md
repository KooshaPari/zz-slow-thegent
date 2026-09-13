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
