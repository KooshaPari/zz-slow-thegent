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
