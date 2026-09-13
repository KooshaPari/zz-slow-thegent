"""Tests for WL-159: Cross-Repo Board Sync Operationalization.

# @trace WL-159
"""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from thegent.commands.sync import SyncCommand, SyncOperationStatus
from thegent.observability.prometheus import (
    get_metrics_collector,
    reset_metrics_collector,
)


class TestBoardSyncWorkflow:
    """Test suite for board sync operationalization."""

    @pytest.fixture
    def temp_project(self) -> Generator[Path]:
        """Create temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs" / "reference").mkdir(parents=True)
            yield root

    def test_board_sync_no_board_id(self, temp_project: Path) -> None:
        """Board sync should skip when no board_id is configured."""
        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id=None, source="github", dry_run=False)

        assert result.status == SyncOperationStatus.SKIPPED
        assert "no board_id" in result.message

    def test_board_sync_dry_run(self, temp_project: Path) -> None:
        """Board sync dry-run should report what would be synced."""
        # Create WORK_STREAM.md with sample items
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Cross-Repo Board Sync
**Status:** IN PROGRESS
**Priority:** P2

### [WL-160] Full Automatic Workstream Reflection
**Status:** BACKLOG
**Priority:** P1
"""
        )

        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id="123", source="github", dry_run=True)

        assert result.status == SyncOperationStatus.DRY_RUN
        assert "dry-run" in result.message.lower()
        assert result.ok is True
        assert result.details["board_id"] == "123"
        assert result.details["source"] == "github"

    def test_board_sync_no_items(self, temp_project: Path) -> None:
        """Board sync should succeed with no items when WORK_STREAM.md is empty."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text("# WORK_STREAM\n\nNo items yet.\n")

        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id="123", source="github", dry_run=False)

        assert result.status == SyncOperationStatus.SUCCESS
        assert "no work stream items" in result.message.lower()
        assert result.details["items"] == 0

    def test_board_sync_records_metrics(self, temp_project: Path) -> None:
        """Board sync increments board-cycle metrics on success."""
        reset_metrics_collector()
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Cross-Repo Board Sync
**Status:** BACKLOG
""",
            encoding="utf-8",
        )

        cmd = SyncCommand(project_root=temp_project)
        fake_result = {
            "synced": 1,
            "failed": 0,
            "updated_items": [{"id": "WL-159"}],
            "errors": [],
        }
        with patch.object(cmd, "_perform_board_sync", return_value=fake_result):
            result = cmd.sync_board(board_id="123", source="github", dry_run=False)

        assert result.status == SyncOperationStatus.SUCCESS
        metrics = get_metrics_collector().render_text()
        assert (
            'thegent_board_sync_cycles_total{source="github",status="success"} 1'
            in metrics
        )

    def test_board_sync_success(self, temp_project: Path) -> None:
        """Board sync should succeed and sync work items."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Cross-Repo Board Sync
**Status:** IN PROGRESS

### [WL-160] Workstream Reflection
**Status:** COMPLETED

### [WL-161] Board-ID Reconciliation
**Status:** BACKLOG
"""
        )

        cmd = SyncCommand(project_root=temp_project)
        fake_result = {
            "synced": 3,
            "failed": 0,
            "updated_items": [
                {"id": "WL-159"},
                {"id": "WL-160"},
                {"id": "WL-161"},
            ],
            "errors": [],
        }
        with patch.object(cmd, "_perform_board_sync", return_value=fake_result):
            result = cmd.sync_board(board_id="456", source="linear", dry_run=False)

        assert result.status == SyncOperationStatus.SUCCESS
        assert "Board sync complete" in result.message
        assert result.details["board_id"] == "456"
        assert result.details["source"] == "linear"
        assert result.details["items_synced"] >= 3

    @pytest.mark.requirement("WL-229")
    def test_board_sync_includes_maintenance_banner_when_active(
        self, temp_project: Path, monkeypatch
    ) -> None:
        """Maintenance mode should propagate a banner into board sync outputs."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Cross-Repo Board Sync
**Status:** IN PROGRESS
""",
            encoding="utf-8",
        )

        monkeypatch.setenv("THGENT_SYNC_MAINTENANCE_ACTIVE", "true")
        monkeypatch.setenv("THGENT_SYNC_MAINTENANCE_REASON", "release-window")
        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id="123", source="github", dry_run=True)

        assert result.status == SyncOperationStatus.DRY_RUN
        assert "[MAINTENANCE] connector=github reason=release-window" in result.message
        assert result.changes
        assert (
            "[MAINTENANCE] connector=github reason=release-window" in result.changes[0]
        )

    def test_parse_work_stream_items(self, temp_project: Path) -> None:
        """Test parsing of WORK_STREAM.md items with status."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Cross-Repo Board Sync
**Status:** IN PROGRESS
**Priority:** P2

### [WL-160] Workstream Reflection
**Status:** COMPLETED

### [WL-161] Board-ID Reconciliation
**Status:** BACKLOG
"""
        )

        cmd = SyncCommand(project_root=temp_project)
        items = cmd._parse_work_stream_items()

        assert len(items) >= 3
        item_ids = [item["id"] for item in items]
        assert "WL-159" in item_ids
        assert "WL-160" in item_ids
        assert "WL-161" in item_ids

        # Check status parsing
        wl159 = next(item for item in items if item["id"] == "WL-159")
        assert wl159["status"] == "IN_PROGRESS"

    @pytest.mark.requirement("WL-184")
    def test_parse_work_stream_items_normalizes_malformed_headers(
        self, temp_project: Path
    ) -> None:
        """Malformed WL headers are normalized before parsing."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### WL184 Header Needs Normalization
**Status:** BACKLOG

### [wl_185] Another Header
**Status:** IN PROGRESS
""",
            encoding="utf-8",
        )

        cmd = SyncCommand(project_root=temp_project)
        items = cmd._parse_work_stream_items()

        item_ids = [item["id"] for item in items]
        assert "WL-184" in item_ids
        assert "WL-185" in item_ids

    @pytest.mark.requirement("WL-188")
    def test_board_sync_filters_by_wl_range(self, temp_project: Path) -> None:
        """WL-range options restrict synced items to the requested interval."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-183] Item A
**Status:** BACKLOG

### [WL-184] Item B
**Status:** IN PROGRESS

### [WL-188] Item C
**Status:** COMPLETED

### [WL-189] Item D
**Status:** BACKLOG
""",
            encoding="utf-8",
        )

        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(
            board_id="123", source="github", dry_run=True, wl_start=184, wl_end=188
        )

        assert result.status == SyncOperationStatus.DRY_RUN
        assert result.details["items_to_sync"] == 2
        assert any("WL-184" in line for line in result.changes)
        assert any("WL-188" in line for line in result.changes)
        assert all("WL-183" not in line for line in result.changes)
        assert all("WL-189" not in line for line in result.changes)

    @pytest.mark.requirement("WL-186")
    def test_board_sync_dry_run_emits_human_readable_diffs(
        self, temp_project: Path
    ) -> None:
        """Dry-run output includes human-readable local->remote field deltas."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-184] Diff Demo
**Status:** IN PROGRESS
""",
            encoding="utf-8",
        )

        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id="123", source="github", dry_run=True)

        assert result.status == SyncOperationStatus.DRY_RUN
        assert any("remote=<unknown> -> local=" in line for line in result.changes)

    @pytest.mark.requirement("WL-187")
    def test_board_sync_batches_external_writes(self, temp_project: Path) -> None:
        """External writes are partitioned into deterministic batches."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-184] Item 184
**Status:** BACKLOG

### [WL-185] Item 185
**Status:** BACKLOG

### [WL-186] Item 186
**Status:** BACKLOG
""",
            encoding="utf-8",
        )

        cmd = SyncCommand(project_root=temp_project)
        batch_sizes: list[int] = []

        def _fake_sync(
            *, board_id: str, work_stream_items: list[dict[str, str]]
        ) -> dict[str, object]:
            assert board_id == "777"
            batch_sizes.append(len(work_stream_items))
            return {
                "synced": len(work_stream_items),
                "failed": 0,
                "updated_items": work_stream_items,
                "errors": [],
            }

        class _FakeAdapter:
            def sync(
                self, board_id: str, work_stream_items: list[dict[str, str]]
            ) -> dict[str, object]:
                return _fake_sync(
                    board_id=board_id, work_stream_items=work_stream_items
                )

        with patch(
            "thegent.sync.board_adapters.resolve_board_adapter",
            return_value=_FakeAdapter(),
        ):
            result = cmd.sync_board(
                board_id="777", source="github", dry_run=False, write_batch_size=2
            )

        assert result.status == SyncOperationStatus.SUCCESS
        assert batch_sizes == [2, 1]
        assert result.details["batches"] == 2

    def test_parse_work_stream_no_file(self, temp_project: Path) -> None:
        """Test parsing when WORK_STREAM.md doesn't exist."""
        cmd = SyncCommand(project_root=temp_project)
        items = cmd._parse_work_stream_items()

        assert items == []

    def test_perform_board_sync_uses_adapter(self, temp_project: Path) -> None:
        """_perform_board_sync dispatches to source adapter."""
        items = [
            {"id": "WL-159", "title": "Board Sync", "status": "IN_PROGRESS"},
            {"id": "WL-160", "title": "Workstream Reflection", "status": "COMPLETED"},
        ]

        cmd = SyncCommand(project_root=temp_project)
        fake_result = {"synced": 2, "failed": 0, "updated_items": items, "errors": []}

        class _FakeAdapter:
            source = "github"

            def sync(
                self, board_id: str, work_stream_items: list[dict[str, str]]
            ) -> dict[str, object]:
                assert board_id == "123"
                assert work_stream_items == items
                return fake_result

        with patch(
            "thegent.sync.board_adapters.resolve_board_adapter",
            return_value=_FakeAdapter(),
        ):
            result = cmd._perform_board_sync("123", "github", items)

        assert result["synced"] == fake_result["synced"]
        assert result["failed"] == fake_result["failed"]
        assert result["updated_items"] == fake_result["updated_items"]
        assert result["errors"] == fake_result["errors"]
        assert result["batches"] == 1

    @pytest.mark.requirement("FR-SYNC-041")
    def test_board_sync_cli_integration(self, temp_project: Path) -> None:
        """Integration test: board sync command via CLI interface."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Cross-Repo Board Sync
**Status:** IN PROGRESS
"""
        )

        cmd = SyncCommand(project_root=temp_project)

        # Test with board_id
        result = cmd.sync_board(board_id="789", source="github", dry_run=True)
        assert result.ok is True
        assert "dry-run" in result.message.lower()

    def test_board_sync_github_source(self, temp_project: Path) -> None:
        """Test board sync with GitHub as source."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Board Sync
**Status:** IN PROGRESS
"""
        )

        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id="123", source="github", dry_run=True)

        assert result.details["source"] == "github"
        assert result.ok is True

    def test_board_sync_linear_source(self, temp_project: Path) -> None:
        """Test board sync with Linear as source."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-159] Board Sync
**Status:** COMPLETED
"""
        )

        cmd = SyncCommand(project_root=temp_project)
        result = cmd.sync_board(board_id="PROJ-1", source="linear", dry_run=True)

        assert result.details["source"] == "linear"
        assert result.ok is True


class TestBoardSyncErrorHandling:
    """Test error handling in board sync."""

    @pytest.fixture
    def temp_project(self) -> Generator[Path]:
        """Create temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs" / "reference").mkdir(parents=True)
            yield root

    def test_board_sync_malformed_work_stream(self, temp_project: Path) -> None:
        """Board sync should handle malformed WORK_STREAM.md gracefully."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text("### Invalid markdown without closing\n\nNo status")

        cmd = SyncCommand(project_root=temp_project)
        with patch.object(
            cmd,
            "_perform_board_sync",
            return_value={"synced": 0, "failed": 0, "updated_items": [], "errors": []},
        ):
            result = cmd.sync_board(board_id="123", source="github", dry_run=False)

        # Should succeed with 0 items parsed
        assert result.status in (
            SyncOperationStatus.SUCCESS,
            SyncOperationStatus.SKIPPED,
        )

    def test_board_sync_exception_handling(self, temp_project: Path) -> None:
        """Board sync should report errors properly."""
        # Create a scenario where parsing might fail
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            "# WORK_STREAM\n\n### [WL-159] Test\n**Status:** INVALID"
        )

        cmd = SyncCommand(project_root=temp_project)
        # Even with invalid status, should not raise
        with patch.object(
            cmd,
            "_perform_board_sync",
            return_value={
                "synced": 1,
                "failed": 0,
                "updated_items": [{"id": "WL-159"}],
                "errors": [],
            },
        ):
            result = cmd.sync_board(board_id="123", source="github", dry_run=False)

        assert result.status != SyncOperationStatus.FAILED or result.errors

    def test_board_sync_records_remote_write_dead_letter(
        self, temp_project: Path
    ) -> None:
        """Failed remote item writes should be persisted to dead-letter queue."""
        work_stream = temp_project / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.write_text(
            """# WORK_STREAM

### [WL-213] Dead-Letter Queue for Remote Writes
**Status:** IN PROGRESS

### [WL-214] Dead-Letter Replay Command
**Status:** BACKLOG
"""
        )

        cmd = SyncCommand(project_root=temp_project)
        with (
            patch.object(
                cmd,
                "_perform_board_sync",
                return_value={
                    "synced": 1,
                    "failed": 1,
                    "updated_items": [{"id": "WL-213"}],
                    "errors": ["WL-214: remote write failed"],
                    "batches": 1,
                },
            ),
            patch.object(
                cmd,
                "_fetch_remote_statuses",
                return_value={},
            ),
        ):
            result = cmd.sync_board(board_id="123", source="github", dry_run=False)

        assert result.status == SyncOperationStatus.SUCCESS
        assert result.details["dead_letters_written"] == 1

        queue_path = (
            temp_project
            / "docs"
            / "reference"
            / "workstream_remote_writes_dead_letter.jsonl"
        )
        lines = queue_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["item"]["id"] == "WL-214"
        assert payload["status"] == "pending"

    def test_dead_letter_replay_marks_entry_replayed(self, temp_project: Path) -> None:
        """Replay should mark pending dead-letter entries as replayed when successful."""
        queue_path = (
            temp_project
            / "docs"
            / "reference"
            / "workstream_remote_writes_dead_letter.jsonl"
        )
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.write_text(
            (
                '{"entry_id":"dlq-1","source":"github","board_id":"123",'
                '"item":{"id":"WL-214","title":"Dead-Letter Replay Command","status":"BACKLOG"},'
                '"error":"WL-214: remote write failed","status":"pending","attempts":0,'
                '"first_failed_at":"2026-02-22T00:00:00+00:00","last_attempt_at":null,"resolved_at":null}\n'
            ),
            encoding="utf-8",
        )

        cmd = SyncCommand(project_root=temp_project)
        with patch.object(
            cmd,
            "_perform_board_sync",
            return_value={
                "synced": 1,
                "failed": 0,
                "updated_items": [{"id": "WL-214"}],
                "errors": [],
                "batches": 1,
            },
        ):
            result = cmd.replay_dead_letters(
                source="github", board_id="123", limit=10, dry_run=False
            )

        assert result.status == SyncOperationStatus.SUCCESS
        assert result.details["replayed"] == 1

        payload = json.loads(
            queue_path.read_text(encoding="utf-8").strip().splitlines()[0]
        )
        assert payload["status"] == "replayed"
        assert payload["resolved_at"] is not None
