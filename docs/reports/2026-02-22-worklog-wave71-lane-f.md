# Worklog Wave 71 — Lane F (2026-02-22)

## Scope

- WL-197: Sync policy file contract
- WL-198: End-to-end replay fixture
- WL-199: Multi-project tenancy autosync docs
- WL-213: Dead-letter queue for remote writes
- WL-214: Dead-letter replay command

## Implementation Summary

- Added strict sync-policy contract loader/validator:
  - `src/thegent/integrations/sync_policy_contract.py`
  - Contract path resolution: explicit path > `THGENT_SYNC_POLICY_PATH` > `.thegent/sync-policy.yaml`
  - Validates schema version, connector policies, quotas, and multi-project tenancy root uniqueness.
- Wired contract usage into sync auditing:
  - `src/thegent/integrations/sync_auditor.py`
  - `SyncAuditor.load_policy_contract(...)` maps connector config into enabled connectors, quotas, and policy modes.
  - `src/thegent/cli/apps/sync.py` `sync audit` now loads and reports contract metadata.
- Implemented remote-write dead-letter queue:
  - `src/thegent/commands/sync.py`
  - Dead-letter model: `RemoteWriteDeadLetter`
  - Queue path: `THGENT_SYNC_DEAD_LETTER_PATH` override or `docs/reference/workstream_remote_writes_dead_letter.jsonl`
  - Board sync now persists failed item writes (`WL-*` keyed errors) into the dead-letter queue.
- Implemented dead-letter replay command:
  - `src/thegent/commands/sync.py` `replay_dead_letters(...)`
  - `src/thegent/cli/apps/sync.py` `thegent sync dead-letter-replay`
  - Supports filters (`--source`, `--board`), limit, and dry-run.
- Added replay fixture and e2e replay path:
  - Fixture: `tests/fixtures/workstream_autosync/replay/remote_write_dead_letter_fixture.jsonl`
  - E2E test: `tests/e2e/test_wl198_dead_letter_replay_fixture.py`
- Added multi-project tenancy autosync guide:
  - `docs/guides/AUTOSYNC_MULTI_PROJECT_TENANCY.md`

## Evidence

1. Targeted tests:
   - Command:
     - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -m pytest tests/test_wl197_sync_policy_contract.py tests/test_wl261_sync_audit.py tests/test_wl159_board_sync.py tests/commands/test_sync_board_autopilot_cli.py tests/e2e/test_wl198_dead_letter_replay_fixture.py -q`
   - Result:
     - `48 passed in 11.57s`
2. Compile validation:
   - Command:
     - `./.venv/bin/python -m py_compile src/thegent/integrations/sync_policy_contract.py src/thegent/integrations/sync_auditor.py src/thegent/commands/sync.py src/thegent/cli/apps/sync.py tests/test_wl197_sync_policy_contract.py tests/test_wl261_sync_audit.py tests/test_wl159_board_sync.py tests/commands/test_sync_board_autopilot_cli.py tests/e2e/test_wl198_dead_letter_replay_fixture.py`
   - Result:
     - success (no output)

## Gaps / Risks

1. Required full gate (`task quality`) fails on pre-existing max-lines violation outside this lane:
   - Failure:
     - `src/thegent/integrations/workstream_autosync.py: 2888 lines (max 2500)`
   - Notes:
     - Lane F did not modify `src/thegent/integrations/workstream_autosync.py`.
2. Sync audit now requires a valid sync-policy file when run:
   - If `.thegent/sync-policy.yaml` (or `--policy-path`) is missing/invalid, command exits with explicit failure.
