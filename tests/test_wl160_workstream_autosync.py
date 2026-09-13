"""Tests for WL-160: Full Automatic Workstream Reflection (GitHub Projects + Linear).

Tests cover:
- Configuration validation
- Standalone-safe behavior (no crash when disabled or credentials missing)
- Cycle runner initialization and control
- Workstream item parsing
- Platform-specific sync operations (stubs with proper structure)
- Autosync command-line interface
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from thegent.docgen.code_annotation import CodeAnnotationGenerator
from thegent.execution import EscalationQueue
from thegent.integrations.idempotency_cache import IdempotencyCache
from thegent.integrations.policy_checksum import compute_payload_checksum
from thegent.integrations.reflection_event_log import (
    ReflectionDecision,
    ReflectionEventLog,
)
from thegent.integrations.workstream_autosync import (
    ConnectorSLAThresholds,
    MaintenanceWindow,
    RemoteMissingItemPolicy,
    RetryClass,
    SyncDirection,
    SyncOperation,
    WorkstreamAutosyncConfig,
    WorkstreamAutosyncConfigError,
    WorkstreamAutosyncRunner,
    WorkstreamItem,
    WorkstreamParser,
    load_autosync_config_from_env,
)


@pytest.fixture
def valid_github_config():
    """Valid GitHub Projects configuration."""
    return WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="kooshapari",
        github_project_number=1,
        github_direction=SyncDirection.BIDIRECTIONAL,
        standalone_mode=True,
    )


@pytest.fixture
def valid_linear_config():
    """Valid Linear configuration."""
    return WorkstreamAutosyncConfig(
        enabled=True,
        linear_enabled=True,
        linear_api_key="test-key-123",
        linear_team_key="test-team",
        linear_direction=SyncDirection.BIDIRECTIONAL,
        standalone_mode=True,
    )


@pytest.fixture
def disabled_config():
    """Disabled autosync configuration."""
    return WorkstreamAutosyncConfig(
        enabled=False,
        github_enabled=True,
        github_owner="kooshapari",
        github_project_number=1,
        standalone_mode=True,
    )


@pytest.fixture
def sample_work_stream_file(tmp_path):
    """Create a sample WORK_STREAM.md for testing."""
    work_stream = tmp_path / "WORK_STREAM.md"
    content = """# Work Stream

### [WL-160] Full Automatic Workstream Reflection
**Status:** IN PROGRESS
**Priority:** P1
**Area:** sync, automation
**Blocked by:** external credentials

Make board/tooling concerns transparent.

### [WL-161] Board-ID-First Reconciliation
**Status:** BACKLOG
**Priority:** P1
**Area:** sync

Define deterministic conflict precedence.
"""
    work_stream.write_text(content)
    return work_stream


class TestWorkstreamAutosyncConfig:
    """Test WorkstreamAutosyncConfig validation."""

    def test_valid_github_config(self, valid_github_config):
        """Valid GitHub config passes validation."""
        assert valid_github_config.is_valid() is True
        assert valid_github_config.should_sync_github() is True
        assert valid_github_config.should_sync_linear() is False

    def test_valid_linear_config(self, valid_linear_config):
        """Valid Linear config passes validation."""
        assert valid_linear_config.is_valid() is True
        assert valid_linear_config.should_sync_linear() is True
        assert valid_linear_config.should_sync_github() is False

    def test_disabled_config(self, disabled_config):
        """Disabled config fails validation."""
        assert disabled_config.is_valid() is False

    def test_github_permissions(self, valid_github_config):
        """Test GitHub read/write permissions based on direction."""
        # Bidirectional
        assert valid_github_config.github_can_read() is True
        assert valid_github_config.github_can_write() is True

        # Read-only
        ro_config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="test",
            github_project_number=1,
            github_direction=SyncDirection.READ_ONLY,
        )
        assert ro_config.github_can_read() is True
        assert ro_config.github_can_write() is False

        # Write-only
        wo_config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="test",
            github_project_number=1,
            github_direction=SyncDirection.WRITE_ONLY,
        )
        assert wo_config.github_can_read() is False
        assert wo_config.github_can_write() is True

    def test_linear_permissions(self, valid_linear_config):
        """Test Linear read/write permissions based on direction."""
        # Bidirectional
        assert valid_linear_config.linear_can_read() is True
        assert valid_linear_config.linear_can_write() is True

        # Read-only
        ro_config = WorkstreamAutosyncConfig(
            enabled=True,
            linear_enabled=True,
            linear_api_key="key",
            linear_team_key="team",
            linear_direction=SyncDirection.READ_ONLY,
        )
        assert ro_config.linear_can_read() is True
        assert ro_config.linear_can_write() is False


class TestWorkstreamParser:
    """Test workstream markdown parsing."""

    def test_parse_valid_items(self, sample_work_stream_file):
        """Parse valid work stream items."""
        items = WorkstreamParser.parse_items(sample_work_stream_file)

        assert len(items) == 2
        assert items[0].item_id == "WL-160"
        assert items[0].title == "Full Automatic Workstream Reflection"
        assert items[0].status == "IN PROGRESS"
        assert items[0].priority == "P1"
        assert items[0].area == "sync, automation"

        assert items[1].item_id == "WL-161"
        assert items[1].status == "BACKLOG"

    def test_parse_missing_file(self, tmp_path):
        """Handle missing WORK_STREAM.md gracefully."""
        missing_file = tmp_path / "missing.md"
        items = WorkstreamParser.parse_items(missing_file)
        assert items == []

    def test_parse_extract_blocked_by(self, tmp_path):
        """Extract blocked_by field from metadata."""
        work_stream = tmp_path / "WORK_STREAM.md"
        content = """
### [WL-100] Test Item
**Status:** BACKLOG
**Blocked by:** WL-099
"""
        work_stream.write_text(content)
        items = WorkstreamParser.parse_items(work_stream)

        assert len(items) == 1
        assert items[0].blocked_by == "WL-099"

    def test_parse_tags_and_sla(self, tmp_path):
        """Parse tags and SLA metadata."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-100] Test Tags
**Status:** BACKLOG
**Tags:** urgent, critical, UI
**SLA:** 6h
"""
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].tags == ["urgent", "critical", "ui"]
        assert items[0].sla_hours == 6.0
        assert items[0].raw_section is not None
        assert "SLA" in items[0].raw_section

    @pytest.mark.requirement("WL-245")
    def test_parse_owner_metadata(self, tmp_path):
        """Parse owner metadata from WORK_STREAM.md."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-100] Test Owner
**Status:** BACKLOG
**Owner:** dev-team-alice
"""
        )

        items = WorkstreamParser.parse_items(work_stream)

        assert len(items) == 1
        assert items[0].owner == "dev-team-alice"

    def test_open_blocker_digest(self):
        """Build digest for blocked open items."""
        items = [
            WorkstreamItem(
                item_id="WL-1",
                title="A",
                status="IN PROGRESS",
                priority="P1",
                area="core",
                blocked_by="WL-2",
            ),
            WorkstreamItem(
                item_id="WL-2",
                title="B",
                status="COMPLETED",
                priority="P1",
                area="core",
                blocked_by="WL-3",
            ),
            WorkstreamItem(
                item_id="WL-3",
                title="C",
                status="BACKLOG",
                priority="P1",
                area="core",
                blocked_by="none",
            ),
        ]

        digest = WorkstreamParser.open_blocker_digest(items)

        assert digest == ["WL-1:A -> WL-2"]

    def test_duplicate_titles(self):
        """Detect duplicate item titles."""
        items = [
            WorkstreamItem(item_id="WL-1", title="same", status="BACKLOG", priority="P1", area="core"),
            WorkstreamItem(item_id="WL-2", title="same", status="BACKLOG", priority="P1", area="core"),
            WorkstreamItem(item_id="WL-3", title="unique", status="BACKLOG", priority="P1", area="core"),
        ]

        duplicates = WorkstreamParser.duplicate_titles(items)
        assert len(duplicates) == 1
        assert duplicates[0][0] == "same"

    def test_validate_tags_and_partitioning(self):
        """Validate tags and partition ranges."""
        items = [
            WorkstreamItem(item_id="WL-1", title="a", status="BACKLOG", priority="P1", area="core", tags=["api"]),
            WorkstreamItem(item_id="WL-2", title="b", status="BACKLOG", priority="P1", area="core", tags=["ui"]),
            WorkstreamItem(item_id="WL-3", title="c", status="BACKLOG", priority="P1", area="core", tags=["infra"]),
        ]
        is_valid, invalid = WorkstreamParser.validate_tags(items, allowed_tags=["api", "ui"], strict=False)
        assert is_valid is True
        assert invalid == ["infra"]

        is_valid, invalid = WorkstreamParser.validate_tags(items, allowed_tags=["api", "ui"], strict=True)
        assert is_valid is False
        assert invalid == ["infra"]

        partitions = WorkstreamParser.split_items(items, partition_size=2)
        assert len(partitions) == 2
        assert len(partitions[0]) == 2
        assert len(partitions[1]) == 1

    def test_sync_sla_annotations(self, tmp_path):
        """Ensure SLA values are reflected in markdown blocks."""
        content = """### [WL-1] Test
**Status:** BACKLOG
"""
        updated = WorkstreamParser.sync_sla_annotations(
            content,
            items=[
                WorkstreamItem(
                    item_id="WL-1", title="Test", status="BACKLOG", priority="P1", area="core", sla_hours=12.5
                )
            ],
        )
        assert "**SLA:** 12.5h" in updated

    def test_scope_filters_match_area_status_priority_and_range(self):
        """WL-168 scope filters should include only matching items."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            scope_areas=["sync, automation"],
            scope_statuses=["BACKLOG"],
            scope_priorities=["P1"],
            scope_wl_ranges=["WL-160..WL-170"],
        )
        matching = WorkstreamItem(
            item_id="WL-160",
            title="match",
            status="BACKLOG",
            priority="P1",
            area="sync, automation",
        )
        excluded = WorkstreamItem(
            item_id="WL-190",
            title="skip",
            status="BACKLOG",
            priority="P1",
            area="sync, automation",
        )

        assert config.matches_scope_filters(matching) is True
        assert config.matches_scope_filters(excluded) is False

    def test_sync_status_annotations(self):
        """Ensure status lines are reflected in markdown blocks."""
        content = """### [WL-1] Test
**Status:** BACKLOG
"""
        updated = WorkstreamParser.sync_status_annotations(
            content,
            statuses={"WL-1": "COMPLETED"},
        )
        assert "**Status:** COMPLETED" in updated


class TestWorkstreamItem:
    """Test WorkstreamItem model."""

    def test_item_to_dict(self):
        """Convert item to dictionary."""
        item = WorkstreamItem(
            item_id="WL-160",
            title="Test Item",
            status="IN PROGRESS",
            priority="P1",
            area="test",
            blocked_by="WL-159",
            source_line=10,
        )

        d = item.to_dict()
        assert d["item_id"] == "WL-160"
        assert d["status"] == "IN PROGRESS"
        assert d["blocked_by"] == "WL-159"


class TestSyncOperation:
    """Test SyncOperation model."""

    def test_operation_to_dict(self):
        """Convert operation to dictionary."""
        op = SyncOperation(
            operation_id="test-op-1",
            platform="github",
            direction="write",
            items_processed=10,
            items_successful=9,
            items_failed=1,
            errors=["Failed to sync item WL-100"],
        )

        d = op.to_dict()
        assert d["operation_id"] == "test-op-1"
        assert d["platform"] == "github"
        assert d["items_successful"] == 9
        assert d["errors"] == ["Failed to sync item WL-100"]


class TestWorkstreamAutosyncRunner:
    """Test WorkstreamAutosyncRunner."""

    @pytest.mark.asyncio
    async def test_runner_init(self, valid_github_config):
        """Test runner initialization."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        assert runner.config == valid_github_config
        assert runner.is_running is False
        assert runner.last_sync_time is None

    @pytest.mark.asyncio
    async def test_runner_start_with_valid_config(self, valid_github_config):
        """Test runner starts with valid config."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        await runner.start()

        # Check that task was created
        assert runner.is_running is True
        assert runner._task is not None

        # Clean up
        await runner.stop()

    @pytest.mark.asyncio
    async def test_runner_start_with_invalid_config(self, disabled_config):
        """Test runner doesn't start with invalid config."""
        runner = WorkstreamAutosyncRunner(disabled_config)
        await runner.start()

        # Should not start due to invalid config
        assert runner.is_running is False

    @pytest.mark.asyncio
    async def test_runner_stop(self, valid_github_config):
        """Test runner can be stopped."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        await runner.start()
        assert runner.is_running is True

        await runner.stop()
        assert runner.is_running is False

    @pytest.mark.asyncio
    async def test_perform_sync_cycle_with_items(self, valid_github_config, sample_work_stream_file):
        """Test sync cycle with work stream items."""
        valid_github_config.work_stream_path = sample_work_stream_file

        runner = WorkstreamAutosyncRunner(valid_github_config)
        with (
            patch(
                "thegent.integrations.workstream_autosync.gh_sync_to_github",
                return_value={"items_created": 0, "items_updated": 1, "errors": []},
            ),
            patch(
                "thegent.integrations.workstream_autosync.gh_sync_from_github",
                return_value={"items": [{"item_id": "WL-160", "status": "IN PROGRESS"}], "errors": []},
            ),
        ):
            await runner._perform_sync_cycle()

        # Should have recorded a sync time
        assert runner.last_sync_time is not None

    @pytest.mark.asyncio
    async def test_record_failure_stores_retry_class_and_correlation(self, tmp_path):
        """Recorded failures should preserve retry classification and correlation ID."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            failure_queue_path=tmp_path / "failures.json",
        )
        runner = WorkstreamAutosyncRunner(config)
        runner._current_run_correlation_id = "run-251"

        retry_class = await runner._record_failure(
            connector="github",
            direction="write",
            item_id="WL-160",
            message="429 rate limit exceeded",
        )

        assert retry_class == RetryClass.RATE_LIMIT
        snapshot = runner._failure_queue.snapshot()
        assert len(snapshot) == 1
        record = snapshot[0]
        assert record.retry_class == RetryClass.RATE_LIMIT.value
        assert record.correlation_id == "run-251"

        reloaded = WorkstreamAutosyncRunner(config)
        persisted = reloaded._failure_queue.snapshot()
        assert len(persisted) == 1
        assert persisted[0].retry_class == RetryClass.RATE_LIMIT.value
        assert persisted[0].correlation_id == "run-251"

    @pytest.mark.asyncio
    async def test_perform_sync_cycle_simulation_mode_marks_no_op(
        self, valid_github_config, sample_work_stream_file, tmp_path
    ):
        """Simulation mode should skip connector partitions and mark the cycle as no-op."""
        valid_github_config.work_stream_path = sample_work_stream_file
        valid_github_config.simulation_mode = True
        valid_github_config.status_file_path = tmp_path / "autosync_status.json"
        valid_github_config.cycle_manifest_path = tmp_path / "cycle_manifest.jsonl"
        valid_github_config.change_digest_path = tmp_path / "change_digest.jsonl"
        valid_github_config.failure_queue_path = tmp_path / "failures.json"
        valid_github_config.trend_file_path = tmp_path / "trend.jsonl"
        valid_github_config.checkpoint_file_path = tmp_path / "checkpoint.json"
        valid_github_config.incident_bundle_path = tmp_path / "incident_snapshots.jsonl"

        runner = WorkstreamAutosyncRunner(valid_github_config)
        with patch.object(runner, "_sync_in_partitions", autospec=True) as sync_partitions:
            await runner._perform_sync_cycle()

        assert sync_partitions.call_count == 0
        assert runner._no_op_summary is not None
        assert runner._no_op_summary["no_op"] is True
        assert runner._no_op_summary["reason"] == "simulation_mode"
        assert runner.last_error is None
        assert runner.total_cycles == 1

    @pytest.mark.asyncio
    async def test_perform_sync_cycle_no_workstream_items_fast_path(self, valid_github_config, tmp_path):
        """No-workstream state should return a no-op cycle without connector calls."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text("# Work Stream\\n", encoding="utf-8")
        valid_github_config.work_stream_path = work_stream
        valid_github_config.status_file_path = tmp_path / "autosync_status.json"
        valid_github_config.cycle_manifest_path = tmp_path / "cycle_manifest.jsonl"
        valid_github_config.change_digest_path = tmp_path / "change_digest.jsonl"
        valid_github_config.failure_queue_path = tmp_path / "failures.json"
        valid_github_config.trend_file_path = tmp_path / "trend.jsonl"
        valid_github_config.checkpoint_file_path = tmp_path / "checkpoint.json"

        runner = WorkstreamAutosyncRunner(valid_github_config)
        with patch.object(runner, "_sync_in_partitions", autospec=True) as sync_partitions:
            await runner._perform_sync_cycle()

        assert sync_partitions.call_count == 0
        assert runner.total_cycles == 1
        assert runner.last_error is None
        assert runner._no_op_summary is not None
        assert runner._no_op_summary["no_op"] is True
        assert runner._no_op_summary["reason"] == "no_workstream_items"

    @pytest.mark.asyncio
    async def test_perform_sync_cycle_unchanged_state_fast_path(
        self, valid_github_config, sample_work_stream_file, tmp_path
    ):
        """Unchanged workstream state should skip all connector sync calls."""
        valid_github_config.work_stream_path = sample_work_stream_file
        valid_github_config.status_file_path = tmp_path / "autosync_status.json"
        valid_github_config.cycle_manifest_path = tmp_path / "cycle_manifest.jsonl"
        valid_github_config.change_digest_path = tmp_path / "change_digest.jsonl"
        valid_github_config.failure_queue_path = tmp_path / "failures.json"
        valid_github_config.trend_file_path = tmp_path / "trend.jsonl"
        valid_github_config.checkpoint_file_path = tmp_path / "checkpoint.json"

        items = WorkstreamParser.parse_items(sample_work_stream_file)
        runner = WorkstreamAutosyncRunner(valid_github_config)
        runner._last_cycle_fingerprint = runner._compute_cycle_fingerprint(items)

        with patch.object(runner, "_sync_in_partitions", autospec=True) as sync_partitions:
            await runner._perform_sync_cycle()

        assert sync_partitions.call_count == 0
        assert runner.total_cycles == 1
        assert runner.last_error is None
        assert runner._no_op_summary is not None
        assert runner._no_op_summary["no_op"] is True
        assert runner._no_op_summary["reason"] == "unchanged_workstream_state"

    @pytest.mark.asyncio
    async def test_run_cycle_skips_maintenance(self, valid_github_config, sample_work_stream_file):
        """Run cycle should skip connectors in maintenance window."""
        now = datetime.now(UTC)
        valid_github_config.work_stream_path = sample_work_stream_file
        runner = WorkstreamAutosyncRunner(valid_github_config)

        async def boom(_items):
            raise RuntimeError("should not run")

        runner._sync_to_github = boom  # type: ignore[method-assign]
        valid_github_config.maintenance_windows = [
            MaintenanceWindow(
                connector="github",
                start_utc=now - timedelta(minutes=1),
                end_utc=now + timedelta(minutes=1),
            )
        ]
        await runner._perform_sync_cycle()
        assert runner.last_sync_time is not None
        assert runner._checkpoint is None

    @pytest.mark.asyncio
    async def test_run_cycle_stops_on_emergency_env_flag(self, valid_github_config, sample_work_stream_file):
        """Emergency stop env should block autosync cycle."""
        valid_github_config.work_stream_path = sample_work_stream_file
        valid_github_config.emergency_stop_env_var = "THGENT_AUTOSYNC_EMERGENCY_STOP"
        runner = WorkstreamAutosyncRunner(valid_github_config)
        with patch.dict("os.environ", {"THGENT_AUTOSYNC_EMERGENCY_STOP": "1"}):
            await runner._perform_sync_cycle()
        assert runner.last_error is not None
        assert "Emergency stop active" in runner.last_error

    @pytest.mark.asyncio
    async def test_maintenance_windows_are_project_scoped(self, valid_github_config):
        """Maintenance window checks can be scoped to specific project IDs."""
        now = datetime.now(UTC)
        valid_github_config.maintenance_windows = [
            MaintenanceWindow(
                connector="github",
                project="proj-alpha",
                start_utc=now - timedelta(minutes=1),
                end_utc=now + timedelta(minutes=1),
            )
        ]
        assert valid_github_config.is_maintenance_active("github", at=now, project="proj-alpha") is True
        assert valid_github_config.is_maintenance_active("github", at=now, project="proj-beta") is False

    @pytest.mark.asyncio
    async def test_write_entrypoint_blocks_when_emergency_stop_file_exists(self, valid_github_config, tmp_path):
        """Write entrypoints fail fast when emergency stop sentinel file is present."""
        sentinel = tmp_path / "autosync.stop"
        sentinel.write_text("stop", encoding="utf-8")
        valid_github_config.emergency_stop_file_path = sentinel
        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = [WorkstreamItem(item_id="WL-1", title="One", status="BACKLOG", priority="P1", area="sync")]
        with pytest.raises(WorkstreamAutosyncConfigError, match="Emergency stop active"):
            await runner._sync_to_github(items)

    @pytest.mark.asyncio
    async def test_operation_ids_are_replay_safe_for_same_batch(self, valid_github_config):
        """Write op ID should be deterministic for same connector+direction+batch."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = [WorkstreamItem(item_id="WL-1", title="One", status="BACKLOG", priority="P1", area="sync")]
        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_to_github",
            return_value={"items_created": 0, "items_updated": 1, "errors": []},
        ):
            await runner._sync_to_github(items)
            first_id = runner.last_operation.operation_id if runner.last_operation else None
            await runner._sync_to_github(items)
            second_id = runner.last_operation.operation_id if runner.last_operation else None
        assert first_id is not None
        assert second_id is not None
        assert first_id == second_id
        assert first_id.startswith("gh-write-")

    @pytest.mark.asyncio
    async def test_replay_safe_mutations_skip_second_write(self, valid_github_config, tmp_path):
        """Second write for same batch should be skipped by idempotency cache."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        runner._idempotency_cache = IdempotencyCache(tmp_path / "idempotency.json")
        items = [
            WorkstreamItem(item_id="WL-1", title="One", status="BACKLOG", priority="P1", area="sync"),
            WorkstreamItem(item_id="WL-2", title="Two", status="BACKLOG", priority="P1", area="sync"),
        ]
        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_to_github",
            return_value={"items_created": 0, "items_updated": 2, "errors": []},
        ):
            await runner._sync_to_github(items)
            assert runner.last_operation is not None
            assert runner.last_operation.items_successful == 2

            await runner._sync_to_github(items)
            assert runner.last_operation is not None
            assert runner.last_operation.items_successful == 0

    @pytest.mark.asyncio
    async def test_sync_to_github_enforces_actor_identity(self, valid_github_config):
        """Write syncs require actor identity when enforcement is enabled."""
        valid_github_config.require_actor_identity = True
        valid_github_config.actor_id = "agent-alpha"
        valid_github_config.actor_signature = "bad-signature"
        valid_github_config.actor_signing_key = "secret"
        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = [WorkstreamItem(item_id="WL-1", title="One", status="BACKLOG", priority="P1", area="sync")]

        with patch(
            "thegent.integrations.workstream_autosync.SSHIdentityProxy.require_actor_identity",
            side_effect=ValueError("invalid actor signature"),
        ):
            with pytest.raises(ValueError, match="invalid actor signature"):
                await runner._sync_to_github(items)

    @pytest.mark.asyncio
    @pytest.mark.requirement("WL-228")
    async def test_sync_to_github_blocks_missing_required_connector_capability(self, valid_github_config):
        """Write syncs must fail when connector lacks required capabilities."""
        valid_github_config.connector_capabilities = {"github": ["status-read"]}
        valid_github_config.required_connector_capabilities = {"github": ["status-read", "issue-write"]}
        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = [
            WorkstreamItem(
                item_id="WL-1",
                title="Test",
                status="BACKLOG",
                priority="P1",
                area="sync",
            )
        ]

        with pytest.raises(
            WorkstreamAutosyncConfigError,
            match="Connector capability mismatch for github: missing issue-write",
        ):
            await runner._sync_to_github(items)

    @pytest.mark.requirement("WL-235")
    def test_connector_chaos_timeout_fixture(self):
        """Deterministic timeout fixture should request retries and escalation."""
        payload = WorkstreamAutosyncRunner.simulate_connector_chaos("github", "timeout", items_count=4)
        assert payload["scenario"] == "timeout"
        assert payload["retry_count"] == 3
        assert payload["escalate"] is True
        assert payload["outcome"] == "outage"

    @pytest.mark.requirement("WL-235")
    def test_connector_chaos_partial_ack_fixture(self):
        """Partial ack fixture should report deterministic partial completion."""
        payload = WorkstreamAutosyncRunner.simulate_connector_chaos("linear", "partial_ack", items_count=5)
        assert payload["items_attempted"] == 5
        assert payload["items_acked"] == 4
        assert payload["escalate"] is True

    @pytest.mark.requirement("WL-235")
    def test_connector_chaos_http_5xx_fixture(self):
        """HTTP 5xx chaos should be deterministic and escalate."""
        payload = WorkstreamAutosyncRunner.simulate_connector_chaos("github", "http_5xx", items_count=4)
        assert payload["scenario"] == "http_5xx"
        assert payload["items_attempted"] == 4
        assert payload["items_acked"] == 0
        assert payload["outcome"] == "server_error"
        assert payload["escalate"] is True

    @pytest.mark.requirement("WL-235")
    def test_connector_chaos_partial_ack_one_item_boundary(self):
        """Boundary case for partial ack with single-item payload."""
        payload = WorkstreamAutosyncRunner.simulate_connector_chaos("linear", "partial_ack", items_count=1)
        assert payload["items_attempted"] == 1
        assert payload["items_acked"] == 0
        assert payload["outcome"] == "partial"

    @pytest.mark.requirement("WL-235")
    def test_connector_chaos_unknown_fixture_raises(self):
        """Unsupported chaos scenarios must fail loudly."""
        with pytest.raises(ValueError, match="Unsupported chaos scenario"):
            WorkstreamAutosyncRunner.simulate_connector_chaos("github", "unknown", items_count=1)

    def test_local_reflection_events_are_logged_with_schema_and_direction(self, tmp_path):
        """Local reflection logs should emit local_to_remote annotations."""
        runner = WorkstreamAutosyncRunner(
            WorkstreamAutosyncConfig(
                enabled=True,
                github_enabled=True,
                github_owner="owner",
                github_project_number=1,
                reflection_event_log_path=tmp_path / "local_reflections.jsonl",
                standalone_mode=True,
            )
        )
        operation = SyncOperation(
            operation_id="op-local",
            platform="github",
            direction="write",
            items_processed=2,
            items_successful=1,
            items_failed=1,
            errors=["error"],
        )
        operation.completed_at = datetime.now(UTC)
        operation.duration_seconds = 0.01

        runner._record_local_reflection_events(connector="github", operation=operation)

        lines = (tmp_path / "local_reflections.jsonl").read_text(encoding="utf-8").splitlines()
        assert lines
        payload = json.loads(lines[0])
        assert payload["direction"] == "local_to_remote"
        assert payload["annotation"]["direction"] == "local_to_remote"
        assert payload["annotation"]["schema"] == "reflection-annotation-v1"
        assert payload["wl_id"] == operation.operation_id

    def test_remote_reflection_events_are_logged_with_schema_and_direction(self, tmp_path):
        """Remote reflection logs should emit remote_to_local annotations."""
        runner = WorkstreamAutosyncRunner(
            WorkstreamAutosyncConfig(
                enabled=True,
                github_enabled=True,
                github_owner="owner",
                github_project_number=1,
                reflection_event_log_path=tmp_path / "remote_reflections.jsonl",
                standalone_mode=True,
            )
        )
        local_items = [
            WorkstreamItem(item_id="WL-100", title="One", status="BACKLOG", priority="P1", area="core"),
            WorkstreamItem(item_id="WL-101", title="Two", status="BACKLOG", priority="P1", area="core"),
        ]
        runner._log_remote_reflection_events(
            connector="github",
            local_items=local_items,
            status_updates={"WL-100": "COMPLETED"},
        )

        lines = (tmp_path / "remote_reflections.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["direction"] == "remote_to_local"
        assert payload["annotation"]["direction"] == "remote_to_local"
        assert payload["annotation"]["schema"] == "reflection-annotation-v1"
        assert payload["wl_id"] == "WL-100"

    @pytest.mark.asyncio
    async def test_checkpoint_resume_on_failure(self, tmp_path):
        """Resume sync from checkpoint after a partition failure."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-1] One
**Status:** BACKLOG

### [WL-2] Two
**Status:** BACKLOG

### [WL-3] Three
**Status:** BACKLOG
"""
        )

        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            max_partition_size=1,
            checkpoint_file_path=tmp_path / "checkpoint.json",
            standalone_mode=True,
        )
        config.should_sync_github()
        runner = WorkstreamAutosyncRunner(config)
        runner.config.work_stream_path = work_stream

        calls = []

        async def flaky_sync(items: list[WorkstreamItem]) -> None:
            calls.append([item.item_id for item in items])
            if len(calls) == 1:
                raise RuntimeError("flaky")

        await runner._sync_in_partitions(
            connector="github",
            direction="write",
            items=WorkstreamParser.parse_items(work_stream),
            sync_fn=flaky_sync,
        )
        assert calls == [["WL-1"]]
        assert runner._checkpoint is None

        async def sync_identity(items: list[WorkstreamItem]) -> None:
            calls.append([item.item_id for item in items])

        await runner._sync_in_partitions(
            connector="github",
            direction="write",
            items=WorkstreamParser.parse_items(work_stream),
            sync_fn=sync_identity,
        )
        assert calls == [["WL-1"], ["WL-1"], ["WL-2"], ["WL-3"]]

    @pytest.mark.asyncio
    async def test_sync_to_github(self, valid_github_config):
        """Test GitHub sync operation."""
        runner = WorkstreamAutosyncRunner(valid_github_config)

        items = [
            WorkstreamItem(
                item_id="WL-160",
                title="Test",
                status="IN PROGRESS",
                priority="P1",
                area="test",
            )
        ]

        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_to_github",
            return_value={"items_created": 0, "items_updated": 1, "errors": []},
        ):
            await runner._sync_to_github(items)

        # Should record operation
        assert runner.last_operation is not None
        assert runner.last_operation.platform == "github"
        assert runner.last_operation.direction == "write"

    @pytest.mark.asyncio
    async def test_sync_to_github_closes_issue_on_local_completion(self, valid_github_config, tmp_path):
        """Completed local item should auto-close mapped GitHub issue."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-160] Do a thing owner/repo#123
**Status:** COMPLETED
**Priority:** P1
**Area:** sync
Extra: owner/repo#456
### [WL-161] Stay open owner/repo#789
**Status:** IN PROGRESS
**Priority:** P1
**Area:** sync
"""
        )
        valid_github_config.work_stream_path = work_stream
        valid_github_config.github_auto_close_issues = True
        valid_github_config.github_auto_close_comment = "Closed via autosync."

        runner = WorkstreamAutosyncRunner(valid_github_config)
        runner._idempotency_cache = IdempotencyCache(cache_path=tmp_path / "idempotency_cache.json")
        items = WorkstreamParser.parse_items(work_stream)

        with (
            patch(
                "thegent.integrations.workstream_autosync.gh_sync_to_github",
                return_value={"items_created": 0, "items_updated": 2, "errors": []},
            ),
            patch(
                "thegent.integrations.workstream_autosync.close_or_comment_github_issue_refs",
                return_value={
                    "items_processed": 1,
                    "items_updated": 1,
                    "items_commented": 1,
                    "issues": [
                        {
                            "issue_ref": "owner/repo#123",
                            "commented": True,
                            "closed": True,
                            "status": "ok",
                        }
                    ],
                    "errors": [],
                },
            ) as close_mock,
        ):
            await runner._sync_to_github(items)

        assert close_mock.call_count == 1
        called_args, called_kwargs = close_mock.call_args
        assert set(called_args[0]) == {"#123", "owner/repo#123", "#456", "owner/repo#456"}
        assert called_kwargs["close_comment"] == "Closed via autosync."

    @pytest.mark.asyncio
    @pytest.mark.requirement("WL-243")
    async def test_sync_to_github_shadow_mode_blocks_mutation(self, valid_github_config):
        """Shadow mode should block all GitHub mutation calls."""
        valid_github_config.shadow_mode = True
        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = [
            WorkstreamItem(
                item_id="WL-160",
                title="Test",
                status="IN PROGRESS",
                priority="P1",
                area="test",
            )
        ]

        with patch("thegent.integrations.workstream_autosync.gh_sync_to_github") as sync_mock:
            await runner._sync_to_github(items)

        sync_mock.assert_not_called()
        assert runner.last_operation is not None
        assert runner.last_operation.platform == "github"
        assert runner.last_operation.direction == "write"

    @pytest.mark.asyncio
    @pytest.mark.requirement("WL-243")
    async def test_sync_to_linear_shadow_mode_blocks_mutation(self, valid_linear_config):
        """Shadow mode should block all Linear mutation calls."""
        valid_linear_config.shadow_mode = True
        runner = WorkstreamAutosyncRunner(valid_linear_config)
        items = [
            WorkstreamItem(
                item_id="WL-160",
                title="Test",
                status="IN PROGRESS",
                priority="P1",
                area="test",
            )
        ]

        with patch("thegent.integrations.workstream_autosync.linear_sync_to") as sync_mock:
            await runner._sync_to_linear(items)

        sync_mock.assert_not_called()
        assert runner.last_operation is not None
        assert runner.last_operation.platform == "linear"
        assert runner.last_operation.direction == "write"

    @pytest.mark.asyncio
    @pytest.mark.requirement("WL-245")
    async def test_sync_to_github_includes_owner_metadata(self, valid_github_config, tmp_path):
        """Outbound GitHub payload should include canonical and connector owner metadata."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        runner._idempotency_cache = IdempotencyCache(tmp_path / "idempotency.json")
        items = [
            WorkstreamItem(
                item_id="WL-160",
                title="Test",
                status="IN PROGRESS",
                priority="P1",
                area="test",
                owner="dev-team-alice",
            )
        ]

        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_to_github",
            return_value={"items_created": 0, "items_updated": 1, "errors": []},
        ) as sync_mock:
            await runner._sync_to_github(items)

        payload = sync_mock.call_args.args[1][0]
        if isinstance(payload, list):
            payload = payload[0]
        assert payload["owner"] == "dev-team-alice"
        assert payload["github_owner"] == "dev-team-alice"
        assert payload["linear_assignee"] == "dev-team-alice"
        assert payload["__sync_metadata__"]["source_url"] == "github://workstream/WL-160"
        assert payload["__sync_metadata__"]["source_tag"] == "github"

    @pytest.mark.asyncio
    async def test_sync_from_github(self, valid_github_config, tmp_path):
        """Test reading from GitHub Projects."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text("# Test\n")
        valid_github_config.work_stream_path = work_stream

        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = []

        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_from_github",
            return_value={"items": [{"item_id": "WL-160", "status": "COMPLETED"}], "errors": []},
        ):
            await runner._sync_from_github(items, work_stream)

        # Should record operation
        assert runner.last_operation is not None
        assert runner.last_operation.platform == "github"
        assert runner.last_operation.direction == "read"

    @pytest.mark.asyncio
    async def test_sync_from_github_closes_issue_on_completion_transition(self, valid_github_config, tmp_path):
        """Remote completion transition should trigger GitHub issue auto-close flow."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-160] Test
**Status:** IN PROGRESS
"""
        )
        valid_github_config.work_stream_path = work_stream
        valid_github_config.github_auto_close_issues = True
        valid_github_config.github_auto_close_comment = "Closed via autosync."

        runner = WorkstreamAutosyncRunner(valid_github_config)
        items = WorkstreamParser.parse_items(work_stream)

        with (
            patch(
                "thegent.integrations.workstream_autosync.extract_github_issue_refs",
                return_value=["owner/repo#123"],
            ),
            patch(
                "thegent.integrations.workstream_autosync.gh_sync_from_github",
                return_value={
                    "items": [
                        {
                            "item_id": "WL-160",
                            "status": "COMPLETED",
                            "body": "Completes owner/repo#123",
                        }
                    ],
                    "errors": [],
                },
            ),
            patch(
                "thegent.integrations.workstream_autosync.close_or_comment_github_issue_refs",
                return_value={
                    "items_processed": 1,
                    "items_updated": 1,
                    "items_commented": 1,
                    "issues": [
                        {
                            "issue_ref": "owner/repo#123",
                            "commented": True,
                            "closed": True,
                            "status": "ok",
                        }
                    ],
                    "errors": [],
                },
            ) as close_mock,
        ):
            await runner._sync_from_github(items, work_stream)

        updated = work_stream.read_text(encoding="utf-8")
        assert "**Status:** COMPLETED" in updated
        close_mock.assert_called_once_with(["owner/repo#123"], close_comment="Closed via autosync.")

    @pytest.mark.asyncio
    async def test_sync_from_github_enforces_payload_checksum(self, tmp_path):
        """Read sync succeeds when checksum matches configured expected value."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-160] Test
**Status:** IN PROGRESS
"""
        )
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            payload_checksum_enforced=True,
            standalone_mode=True,
            work_stream_path=work_stream,
        )
        runner = WorkstreamAutosyncRunner(config)
        items = WorkstreamParser.parse_items(work_stream)

        remote_items = [{"item_id": "WL-160", "status": "COMPLETED"}]
        checksum = compute_payload_checksum(remote_items)
        config.expected_payload_checksum = checksum

        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_from_github",
            return_value={"items": remote_items, "errors": []},
        ):
            await runner._sync_from_github(items, work_stream)

        updated = work_stream.read_text(encoding="utf-8")
        assert "**Status:** COMPLETED" in updated

    @pytest.mark.asyncio
    async def test_sync_from_github_rejects_bad_remote_payload_checksum(self, tmp_path):
        """Read sync fails when remote payload checksum does not match."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-160] Test
**Status:** IN PROGRESS
"""
        )
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            payload_checksum_enforced=True,
            expected_payload_checksum="bad-checksum",
            standalone_mode=False,
            work_stream_path=work_stream,
        )
        runner = WorkstreamAutosyncRunner(config)
        items = WorkstreamParser.parse_items(work_stream)

        remote_items = [{"item_id": "WL-160", "status": "COMPLETED"}]
        with patch(
            "thegent.integrations.workstream_autosync.gh_sync_from_github",
            return_value={"items": remote_items, "errors": []},
        ), pytest.raises(ValueError, match="Payload checksum mismatch"):
            await runner._sync_from_github(items, work_stream)

    @pytest.mark.asyncio
    async def test_compact_snapshots_keeps_latest_only(self, tmp_path):
        """Snapshot compaction should keep only the configured retention count."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            snapshot_retention_count=3,
        )
        runner = WorkstreamAutosyncRunner(config)

        status_path = tmp_path / "autosync_status.json"
        for index in range(5):
            (tmp_path / f"autosync_snapshot_{index:04d}.json").write_text(f'{{"run":"{index}"}}', encoding="utf-8")

        runner._compact_snapshots(status_path)

        remaining = sorted(tmp_path.glob("autosync_snapshot_*.json"))
        assert len(remaining) == 3
        assert [path.stem for path in remaining] == [
            "autosync_snapshot_0002",
            "autosync_snapshot_0003",
            "autosync_snapshot_0004",
        ]

    def test_artifact_encrypt_and_decrypt_round_trip(self, tmp_path):
        """Encrypted artifact payloads should round-trip through serializer."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            artifact_encryption_enabled=True,
            artifact_encryption_key="secret",
        )
        runner = WorkstreamAutosyncRunner(config)
        payload = {"run_id": "run-254", "items": [1, 2, 3]}

        serialized = runner._serialize_artifact_payload(payload)
        loaded = runner._deserialize_artifact_payload(serialized)

        assert loaded == payload
        assert json.loads(serialized).get("encrypted") is True

    def test_artifact_encryption_requires_key(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """Encrypted artifact handling should fail when no key is configured."""
        monkeypatch.delenv("THGENT_AUTOSYNC_ARTIFACT_KEY", raising=False)
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            artifact_encryption_enabled=True,
        )
        runner = WorkstreamAutosyncRunner(config)

        with pytest.raises(
            WorkstreamAutosyncConfigError,
            match="Artifact encryption is enabled but no key is configured",
        ):
            runner._serialize_artifact_payload({"run_id": "run-254"})

    def test_correlation_id_in_manifest_and_incident_snapshot_inputs(self, tmp_path):
        """Run correlation IDs should be present in manifest and incident snapshot payloads."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            cycle_manifest_path=tmp_path / "manifest.jsonl",
            incident_bundle_path=tmp_path / "incidents.jsonl",
        )
        runner = WorkstreamAutosyncRunner(config)
        runner._current_run_correlation_id = "run-255"
        runner.total_cycles = 4
        runner._append_cycle_manifest(
            status="success",
            started_at=datetime(2026, 2, 22, 0, 0, tzinfo=UTC),
            items=[
                WorkstreamItem(item_id="WL-1", title="One", status="BACKLOG", priority="P1", area="sync"),
            ],
            decisions={"github_enabled": True},
            outputs={"result": "ok"},
        )

        manifest_payload = json.loads((tmp_path / "manifest.jsonl").read_text(encoding="utf-8").strip())
        assert manifest_payload["inputs"]["run_id"] == "run-255"

        incident = runner._build_incident_snapshot_bundle(
            items_count=1,
            metadata_state={"status": "fresh", "age_seconds": 0},
        )
        assert incident["correlation_id"] == "run-255"

    @pytest.mark.asyncio
    async def test_finalize_incident_snapshot_enqueues_slo_escalation(self, valid_github_config, tmp_path):
        """Snapshot with stale age and budget breach should enqueue escalation entry."""
        status_path = tmp_path / "autosync_status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path = status_path.parent / "autosync_snapshot_old.json"
        snapshot_path.write_text("{}", encoding="utf-8")
        old_time = datetime.now(UTC).timestamp() - 3_600
        os.utime(snapshot_path, (old_time, old_time))

        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            status_file_path=status_path,
            error_budget_max_consecutive_failures=1,
            error_budget_max_failure_rate=0.1,
            error_budget_escalation_after=1,
            autosync_stale_snapshot_seconds=1,
        )
        runner = WorkstreamAutosyncRunner(config)
        runner._current_run_correlation_id = "run-123"
        runner._error_budget.record_failure()

        runner._finalize_incident_snapshot(items_count=3, metadata_state={"status": "fresh", "age_seconds": 0})

        snapshot = runner._latest_incident_snapshot
        assert any("autosync snapshot stale" in reason for reason in snapshot["slo_alerts"])
        assert any("error budget" in reason for reason in snapshot["slo_alerts"])

        queue = EscalationQueue(status_path.parent)
        pending = queue.list_pending()
        assert any("autosync snapshot stale" in str(item.get("reason", "")) for item in pending)

    @pytest.mark.asyncio
    async def test_finalize_incident_snapshot_enqueues_hard_fail_escalation(self, valid_github_config, tmp_path):
        """Snapshot with error budget hard-fail should enqueue escalation entry."""
        status_path = tmp_path / "autosync_status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)

        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            status_file_path=status_path,
            error_budget_max_consecutive_failures=0,
            error_budget_max_failure_rate=0.0,
            error_budget_escalation_after=100,
            autosync_stale_snapshot_seconds=9999,
        )
        runner = WorkstreamAutosyncRunner(config)
        runner._current_run_correlation_id = "run-hard-fail"
        runner._error_budget.record_failure()

        runner._finalize_incident_snapshot(items_count=2, metadata_state={"status": "fresh", "age_seconds": 0})

        snapshot = runner._latest_incident_snapshot
        assert any("hard-fail threshold reached" in reason for reason in snapshot["slo_alerts"])

        queue = EscalationQueue(status_path.parent)
        pending = queue.list_pending()
        assert any("hard-fail threshold reached" in str(item.get("reason", "")) for item in pending)

    @pytest.mark.requirement("WL-233")
    def test_evaluate_slo_state_flags_connector_sla_breaches(self, tmp_path):
        """Connector SLA breaches should appear in SLO alert set."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="owner",
            github_project_number=1,
            standalone_mode=True,
            failure_queue_path=tmp_path / "failures.json",
            reflection_event_log_path=tmp_path / "reflection_events.jsonl",
            connector_sla_thresholds={
                "github": ConnectorSLAThresholds(p95_latency_ms=100.0, max_failure_rate=0.1),
            },
        )
        runner = WorkstreamAutosyncRunner(config)
        runner._current_run_correlation_id = "run-123"
        runner._record_connector_latency("github", duration_seconds=0.2)
        runner._connector_error_budget("github").record_failure()
        runner._connector_error_budget("github").record_failure()

        alerts = runner._evaluate_slo_state()
        assert any("connector github" in alert and "latency" in alert for alert in alerts)
        assert any("connector github" in alert and "failure rate" in alert for alert in alerts)

    @pytest.mark.asyncio
    async def test_sync_to_linear(self, valid_linear_config):
        """Test Linear sync operation."""
        runner = WorkstreamAutosyncRunner(valid_linear_config)

        items = [
            WorkstreamItem(
                item_id="WL-160",
                title="Test",
                status="IN PROGRESS",
                priority="P1",
                area="test",
            )
        ]

        with patch(
            "thegent.integrations.workstream_autosync.linear_sync_to",
            return_value={"items_created": 0, "items_updated": 1, "errors": []},
        ):
            await runner._sync_to_linear(items)

        # Should record operation
        assert runner.last_operation is not None
        assert runner.last_operation.platform == "linear"
        assert runner.last_operation.direction == "write"

    @pytest.mark.asyncio
    @pytest.mark.requirement("WL-245")
    async def test_sync_to_linear_includes_owner_metadata(self, valid_linear_config, tmp_path):
        """Outbound Linear payload should include canonical and connector owner metadata."""
        runner = WorkstreamAutosyncRunner(valid_linear_config)
        runner._idempotency_cache = IdempotencyCache(tmp_path / "idempotency.json")
        items = [
            WorkstreamItem(
                item_id="WL-160",
                title="Test",
                status="IN PROGRESS",
                priority="P1",
                area="test",
                owner="dev-team-alice",
            )
        ]

        with patch(
            "thegent.integrations.workstream_autosync.linear_sync_to",
            return_value={"items_created": 0, "items_updated": 1, "errors": []},
        ) as sync_mock:
            await runner._sync_to_linear(items)

        payload = sync_mock.call_args.args[1][0]
        if isinstance(payload, list):
            payload = payload[0]
        assert payload["owner"] == "dev-team-alice"
        assert payload["github_owner"] == "dev-team-alice"
        assert payload["linear_assignee"] == "dev-team-alice"
        assert payload["__sync_metadata__"]["source_url"] == "linear://workstream/WL-160"
        assert payload["__sync_metadata__"]["source_tag"] == "linear"

    @pytest.mark.asyncio
    async def test_sync_from_linear(self, valid_linear_config, tmp_path):
        """Test reading from Linear."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text("# Test\n")
        valid_linear_config.work_stream_path = work_stream

        runner = WorkstreamAutosyncRunner(valid_linear_config)
        items = []

        with patch(
            "thegent.integrations.workstream_autosync.linear_sync_from",
            return_value={"items": [{"item_id": "WL-160", "status": "COMPLETED"}], "errors": []},
        ):
            await runner._sync_from_linear(items, work_stream)

        # Should record operation
        assert runner.last_operation is not None
        assert runner.last_operation.platform == "linear"
        assert runner.last_operation.direction == "read"

    @pytest.mark.asyncio
    async def test_sync_from_linear_rejects_bad_remote_payload_checksum(self, tmp_path):
        """Read sync fails when Linear payload checksum does not match."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-160] Test
**Status:** IN PROGRESS
"""
        )
        config = WorkstreamAutosyncConfig(
            enabled=True,
            linear_enabled=True,
            linear_api_key="key",
            linear_team_key="team",
            payload_checksum_enforced=True,
            expected_payload_checksum="bad-checksum",
            standalone_mode=False,
            work_stream_path=work_stream,
        )
        runner = WorkstreamAutosyncRunner(config)
        items = WorkstreamParser.parse_items(work_stream)

        remote_items = [{"item_id": "WL-160", "status": "COMPLETED"}]
        with patch(
            "thegent.integrations.workstream_autosync.linear_sync_from",
            return_value={"items": remote_items, "errors": []},
        ), pytest.raises(ValueError, match="Payload checksum mismatch"):
            await runner._sync_from_linear(items, work_stream)

    @pytest.mark.asyncio
    async def test_sync_from_linear_accepts_expected_payload_checksum(self, tmp_path):
        """Read sync succeeds when checksum matches configured Linear payload."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-160] Test
**Status:** IN PROGRESS
"""
        )
        remote_items = [{"item_id": "WL-160", "status": "COMPLETED"}]
        config = WorkstreamAutosyncConfig(
            enabled=True,
            linear_enabled=True,
            linear_api_key="key",
            linear_team_key="team",
            payload_checksum_enforced=True,
            expected_payload_checksum=compute_payload_checksum(remote_items),
            standalone_mode=True,
            work_stream_path=work_stream,
        )
        runner = WorkstreamAutosyncRunner(config)
        items = WorkstreamParser.parse_items(work_stream)

        with patch(
            "thegent.integrations.workstream_autosync.linear_sync_from",
            return_value={"items": remote_items, "errors": []},
        ):
            await runner._sync_from_linear(items, work_stream)

        updated = work_stream.read_text(encoding="utf-8")
        assert "**Status:** COMPLETED" in updated

    def test_get_status(self, valid_github_config):
        """Test getting runner status."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        status = runner.get_status()

        assert status["enabled"] is True
        assert status["is_running"] is False
        assert status["github_enabled"] is True
        assert status["linear_enabled"] is False
        assert status["last_operation"] is None

    def test_get_status_with_operation(self, valid_github_config):
        """Test status includes last operation."""
        runner = WorkstreamAutosyncRunner(valid_github_config)
        runner.last_operation = SyncOperation(
            operation_id="test-op",
            platform="github",
            direction="write",
            items_processed=5,
            items_successful=5,
        )

        status = runner.get_status()
        assert status["last_operation"] is not None
        assert status["last_operation"]["operation_id"] == "test-op"

    def test_remote_missing_item_policy_archive(self, valid_github_config):
        """WL-167 archive policy should mark missing remote items as ARCHIVED."""
        valid_github_config.remote_missing_item_policy = RemoteMissingItemPolicy.ARCHIVE
        runner = WorkstreamAutosyncRunner(valid_github_config)
        local = [
            WorkstreamItem(item_id="WL-160", title="A", status="BACKLOG", priority="P1", area="sync"),
            WorkstreamItem(item_id="WL-161", title="B", status="BACKLOG", priority="P1", area="sync"),
        ]
        updates = runner._build_remote_reflection_status_updates(
            local_items=local,
            remote_status_updates={"WL-160": "IN PROGRESS"},
        )
        assert updates["WL-160"] == "IN PROGRESS"
        assert updates["WL-161"] == "ARCHIVED"


class TestLoadAutosyncConfigFromEnv:
    """Test loading config from environment."""

    def test_load_with_github_enabled(self):
        """Load config with GitHub enabled."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "test-owner",
                "THGENT_GITHUB_PROJECT_NUMBER": "42",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.enabled is True
            assert config.github_enabled is True
            assert config.github_owner == "test-owner"
            assert config.github_project_number == 42

    def test_load_with_linear_enabled(self):
        """Load config with Linear enabled."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_LINEAR_ENABLED": "true",
                "THGENT_LINEAR_API_KEY": "test-key",
                "THGENT_LINEAR_TEAM_KEY": "test-team",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.enabled is True
            assert config.linear_enabled is True
            assert config.linear_api_key == "test-key"

    def test_load_with_custom_interval(self):
        """Load config with custom cycle interval."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_WORKSTREAM_AUTOSYNC_INTERVAL": "600",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.cycle_interval_seconds == 600

    def test_load_defaults(self):
        """Load config with all defaults."""
        with patch.dict("os.environ", {}, clear=True):
            config = load_autosync_config_from_env()
            assert config.enabled is False
            assert config.cycle_interval_seconds == 300

    def test_load_with_sync_directions(self):
        """Load config with custom sync directions."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "test",
                "THGENT_GITHUB_PROJECT_NUMBER": "1",
                "THGENT_GITHUB_DIRECTION": "read_only",
                "THGENT_LINEAR_ENABLED": "true",
                "THGENT_LINEAR_API_KEY": "key",
                "THGENT_LINEAR_TEAM_KEY": "team",
                "THGENT_LINEAR_DIRECTION": "write_only",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.github_direction == SyncDirection.READ_ONLY
            assert config.linear_direction == SyncDirection.WRITE_ONLY

    def test_load_maintenance_windows_support_project_scoped_token_format(self):
        """Maintenance window token parser supports project-scoped entries."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_AUTOSYNC_MAINTENANCE_WINDOWS": (
                    "github:2026-02-22T00:00:00Z:2026-02-22T01:00:00Z:project-alpha:release-window"
                )
            },
        ):
            config = load_autosync_config_from_env()
            windows = config.maintenance_windows
            assert len(windows) == 1
            assert windows[0].project == "project-alpha"
            assert windows[0].reason == "release-window"

        with patch.dict(
            "os.environ",
            {"THGENT_AUTOSYNC_MAINTENANCE_WINDOWS": ("linear:2026-02-22T00:00:00Z:2026-02-22T01:00:00Z:legacy-reason")},
        ):
            config = load_autosync_config_from_env()
            windows = config.maintenance_windows
            assert len(windows) == 1
            assert windows[0].project == "default"
            assert windows[0].reason == "legacy-reason"

    def test_load_emergency_stop_settings(self):
        """Load emergency-stop settings from env."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "test-owner",
                "THGENT_GITHUB_PROJECT_NUMBER": "1",
                "THGENT_AUTOSYNC_EMERGENCY_STOP_ENABLED": "true",
                "THGENT_AUTOSYNC_EMERGENCY_STOP_FILE_PATH": "/tmp/thegent-stop",
                "THGENT_AUTOSYNC_EMERGENCY_STOP_ENV_VAR": "CUSTOM_STOP",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.emergency_stop_enabled is True
            assert str(config.emergency_stop_file_path) == "/tmp/thegent-stop"
            assert config.emergency_stop_env_var == "CUSTOM_STOP"

    def test_load_scope_filters_and_remote_missing_policy(self):
        """WL-168/WL-167 env config should populate scope filters and missing-item policy."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "test-owner",
                "THGENT_GITHUB_PROJECT_NUMBER": "1",
                "THGENT_WORKSTREAM_SYNC_SCOPE_AREAS": "sync,automation",
                "THGENT_WORKSTREAM_SYNC_SCOPE_STATUSES": "backlog,in progress",
                "THGENT_WORKSTREAM_SYNC_SCOPE_PRIORITIES": "p0,p1",
                "THGENT_WORKSTREAM_SYNC_SCOPE_WL_RANGES": "WL-160..WL-168",
                "THGENT_WORKSTREAM_REMOTE_MISSING_ITEM_POLICY": "archive",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.scope_areas == ["sync", "automation"]
            assert config.scope_statuses == ["BACKLOG", "IN PROGRESS"]
            assert config.scope_priorities == ["P0", "P1"]
            assert config.scope_wl_ranges == ["WL-160..WL-168"]
            assert config.remote_missing_item_policy == RemoteMissingItemPolicy.ARCHIVE

    def test_load_slo_and_stale_snapshot_env(self):
        """Load error budget thresholds and stale snapshot threshold from environment."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "test-owner",
                "THGENT_GITHUB_PROJECT_NUMBER": "1",
                "THGENT_AUTOSYNC_ERROR_BUDGET_MAX_CONSECUTIVE_FAILURES": "2",
                "THGENT_AUTOSYNC_ERROR_BUDGET_MAX_FAILURE_RATE": "0.2",
                "THGENT_AUTOSYNC_ERROR_BUDGET_ESCALATION_AFTER": "4",
                "THGENT_AUTOSYNC_STALE_SNAPSHOT_SECONDS": "1200",
            },
        ):
            config = load_autosync_config_from_env()
            assert config.error_budget_max_consecutive_failures == 2
            assert config.error_budget_max_failure_rate == 0.2
            assert config.error_budget_escalation_after == 4
            assert config.autosync_stale_snapshot_seconds == 1200

    def test_load_digest_and_reflection_event_log_paths_from_env(self):
        """Digest and reflection log paths should be accepted from env."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "owner",
                "THGENT_GITHUB_PROJECT_NUMBER": "1",
                "THGENT_WORKSTREAM_AUTOSYNC_CHANGE_DIGEST_PATH": "/tmp/autosync/change-digest.jsonl",
                "THGENT_WORKSTREAM_AUTOSYNC_REFLECTION_EVENT_LOG_PATH": "/tmp/autosync/reflections.jsonl",
            },
        ):
            config = load_autosync_config_from_env()
            assert str(config.change_digest_path) == "/tmp/autosync/change-digest.jsonl"
            assert str(config.reflection_event_log_path) == "/tmp/autosync/reflections.jsonl"

    @pytest.mark.requirement("WL-233")
    def test_load_connector_sla_thresholds_env(self):
        """Load connector SLA thresholds from JSON env map."""
        with patch.dict(
            "os.environ",
            {
                "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
                "THGENT_GITHUB_ENABLED": "true",
                "THGENT_GITHUB_OWNER": "owner",
                "THGENT_GITHUB_PROJECT_NUMBER": "1",
                "THGENT_AUTOSYNC_CONNECTOR_SLA_THRESHOLDS": (
                    '{"github":{"p95_latency_ms":150.0,"max_failure_rate":0.25}}'
                ),
            },
        ):
            config = load_autosync_config_from_env()
            thresholds = config.connector_sla_thresholds["github"]
            assert thresholds.p95_latency_ms == 150.0
            assert thresholds.max_failure_rate == 0.25


class TestStandaloneMode:
    """Test standalone-safe behavior."""

    @pytest.mark.asyncio
    async def test_graceful_skip_when_disabled(self):
        """Gracefully skip when autosync disabled."""
        config = WorkstreamAutosyncConfig(
            enabled=False,
            standalone_mode=True,
        )

        runner = WorkstreamAutosyncRunner(config)
        await runner.start()

        # Should not crash, just not start
        assert runner.is_running is False


class TestAnnotationAndReflectionStandard:
    """Tests for WL-238 remote->local annotation schema standard."""

    @pytest.mark.requirement("WL-238")
    def test_annotation_schema_requires_canonical_keys(self) -> None:
        gen = CodeAnnotationGenerator(annotation_format="json")
        payload = gen.format_reflection_annotation(
            {
                "schema": "reflection-annotation-v1",
                "wl_id": "WL-238",
                "connector": "github",
                "direction": "remote_to_local",
                "decision": "apply",
                "mutation_id": "github-mutation-WL-238-abc",
                "timestamp": "2026-02-22T00:00:00Z",
                "extra": "ok",
            }
        )
        assert list(payload.keys())[:7] == list(CodeAnnotationGenerator.REQUIRED_REFLECTION_KEYS)
        assert payload["extra"] == "ok"

    @pytest.mark.requirement("WL-238")
    def test_reflection_event_log_writes_annotation_block(self, tmp_path) -> None:
        log_path = tmp_path / "reflection.jsonl"
        log = ReflectionEventLog(log_path)
        decision = ReflectionDecision(
            wl_id="WL-238",
            decision_type="apply",
            before_value="BACKLOG",
            after_value="IN PROGRESS",
            connector="github",
            timestamp="2026-02-22T00:00:00Z",
            cycle_id="cycle-1",
        )
        log.log(decision)
        raw = log_path.read_text(encoding="utf-8").strip()
        assert '"annotation"' in raw
        assert '"schema": "reflection-annotation-v1"' in raw


class TestAutosyncRunbookCoverage:
    """Runbook documentation coverage for autosync incidents."""

    @pytest.mark.requirement("WL-234")
    def test_runbook_contains_autosync_incident_and_recovery_steps(self) -> None:
        runbook_path = Path(os.getcwd()) / "docs" / "site" / "operations" / "runbooks.md"
        with open(runbook_path, encoding="utf-8") as fp:
            content = fp.read()

        assert "Autosync Incident" in content
        assert "Rollback" in content
        assert "autosync" in content.lower()

    @pytest.mark.asyncio
    async def test_graceful_skip_when_credentials_missing(self):
        """Gracefully skip when credentials missing."""
        config = WorkstreamAutosyncConfig(
            enabled=True,
            github_enabled=True,
            github_owner="",  # Missing required field
            standalone_mode=True,
        )

        runner = WorkstreamAutosyncRunner(config)
        await runner.start()

        # Should not crash, just not start
        assert runner.is_running is False
