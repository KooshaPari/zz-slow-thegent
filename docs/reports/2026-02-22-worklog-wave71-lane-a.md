# Worklog Wave 71 - Lane A Evidence (2026-02-22)

## Scope

Lane A ownership implemented for:

- WL-162 (sync connector mapping parity)
- WL-164 (state mapping table + fail-fast validation)
- WL-166 (idempotency index behavior)
- WL-167 (remote archive/delete policy)
- WL-168 (sync scope filters)

## Item-by-item changes

### WL-162 - GitHub field update parity

- Added GitHub project field parity updates for both `Status` and `Priority` single-select fields during sync write/create flows.
- Added option-resolution logic for priority mapping (`P0..P3` to project option candidates).
- Cached resolved field IDs in connector mapping cache.

Files touched:

- `src/thegent/integrations/gh_project_sync.py`
- `tests/test_wl157_gh_project_sync.py`

### WL-164 - Linear state mapping table

- Added explicit required Linear state-type mapping table (`unstarted`, `started`, `completed`).
- Added fail-fast validation when required mapping entries are missing.
- Switched Linear sync write path to consume the explicit mapping builder.

Files touched:

- `src/thegent/integrations/linear_graphql.py`
- `tests/test_wl164_linear_state_mapping.py`

### WL-166 - Idempotency index cache

- Added content index keyed by `(connector, wl_id, content_hash)` in idempotency cache.
- Added content-equivalence check API (`check_content`) and index/deindex hooks on load/record/invalidate/clear operations.
- Wired autosync write paths to skip duplicate equivalent content entries before recording mutation IDs.

Files touched:

- `src/thegent/integrations/idempotency_cache.py`
- `src/thegent/integrations/workstream_autosync.py`
- `tests/test_wl166_idempotency_cache.py`

### WL-167 - Remote archive/delete policy

- Added config policy enum for missing remote items:
  - `ignore`
  - `archive`
  - `delete`
- Added remote reflection merge helper that marks missing local WL items as `ARCHIVED` or `DELETED` when policy requires.
- Applied policy in both GitHub->local and Linear->local reflection paths.

Files touched:

- `src/thegent/integrations/workstream_autosync.py`
- `tests/test_wl160_workstream_autosync.py`

### WL-168 - Sync scope filters

- Added config-level sync scope filters for:
  - area
  - status
  - priority
  - WL numeric ranges (`WL-N..WL-M`)
- Added filter matching/validation logic and applied it in sync-cycle item selection.
- Added CLI flags on `thegent sync autopilot`:
  - `--area`
  - `--status`
  - `--priority`
  - `--wl-range`
  - `--remote-missing-item-policy`
- Added env parsing for scope filters and remote-missing policy.

Files touched:

- `src/thegent/integrations/workstream_autosync.py`
- `src/thegent/cli/apps/sync.py`
- `tests/test_wl160_workstream_autosync.py`

## Full file list touched (lane changes)

- `src/thegent/integrations/idempotency_cache.py`
- `src/thegent/integrations/linear_graphql.py`
- `src/thegent/integrations/gh_project_sync.py`
- `src/thegent/integrations/workstream_autosync.py`
- `src/thegent/cli/apps/sync.py`
- `tests/test_wl166_idempotency_cache.py`
- `tests/test_wl164_linear_state_mapping.py`
- `tests/test_wl157_gh_project_sync.py`
- `tests/test_wl160_workstream_autosync.py`

## Tests run and results

### Targeted pytest (focused WL surfaces)

Command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q \
  tests/test_wl166_idempotency_cache.py \
  tests/test_wl164_linear_state_mapping.py \
  tests/test_wl157_gh_project_sync.py::TestSyncToGithub::test_write_only_config_allows_sync \
  tests/test_wl157_gh_project_sync.py::TestImportFromCsv::test_write_only_config_allows_import \
  tests/test_wl157_gh_project_sync.py::TestImportFromCsv::test_sync_to_github_updates_priority_and_status_fields \
  tests/test_wl160_workstream_autosync.py::TestWorkstreamParser::test_scope_filters_match_area_status_priority_and_range \
  tests/test_wl160_workstream_autosync.py::TestWorkstreamAutosyncRunner::test_remote_missing_item_policy_archive \
  tests/test_wl160_workstream_autosync.py::TestLoadAutosyncConfigFromEnv::test_load_scope_filters_and_remote_missing_policy
```

Result: `25 passed`

### Compile sanity

Command:

```bash
.venv/bin/python -m py_compile \
  src/thegent/integrations/idempotency_cache.py \
  src/thegent/integrations/linear_graphql.py \
  src/thegent/integrations/gh_project_sync.py \
  src/thegent/integrations/workstream_autosync.py \
  src/thegent/cli/apps/sync.py \
  tests/test_wl166_idempotency_cache.py \
  tests/test_wl157_gh_project_sync.py \
  tests/test_wl160_workstream_autosync.py \
  tests/test_wl164_linear_state_mapping.py
```

Result: success (no syntax errors)

## Remaining gaps / follow-ups

- Did not run full repository quality gate (`task quality`) due broad concurrent workspace churn and unrelated failing surfaces outside this lane.
- Async-heavy autosync suites were not run end-to-end in this pass; only targeted lane-specific test nodes were executed.
- `src/thegent/cli/apps/sync.py` has substantial concurrent in-flight edits outside Lane A scope; this lane only added autopilot scope/policy flags and did not reconcile unrelated command-surface drift.
