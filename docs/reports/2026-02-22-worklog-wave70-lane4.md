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
