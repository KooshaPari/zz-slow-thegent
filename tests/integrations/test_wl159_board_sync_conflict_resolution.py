"""Conflict-resolution tests for WL-159 board sync divergence policy."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from thegent.commands.sync import SyncCommand, SyncOperationStatus


def _write_work_stream(path: Path, contents: str) -> None:
    """Helper for writing deterministic WORK_STREAM payloads."""
    path.write_text(contents, encoding="utf-8")


class TestBoardSyncConflictResolution:
    """Validate explicit precedence policy applied before sync write."""

    @pytest.fixture
    def temp_root(self, tmp_path: Path) -> Path:
        """Create WORK_STREAM + policy root."""
        (tmp_path / "docs" / "reference").mkdir(parents=True, exist_ok=True)
        return tmp_path

    def test_sync_board_local_wins_prefers_local_status(self, temp_root: Path) -> None:
        """When local_wins is configured, local status is preserved."""
        work_stream = temp_root / "docs" / "reference" / "WORK_STREAM.md"
        _write_work_stream(
            work_stream,
            """# WORK_STREAM

### [WL-159] Divergence
**Status:** IN PROGRESS
""",
        )
        cmd = SyncCommand(project_root=temp_root)
        calls: list[dict[str, str]] = []

        def _fake_fetch_remote_statuses(
            *,
            board_id: str,
            source: str,
            work_stream_items: list[dict[str, str]],
        ) -> dict[str, str]:
            assert board_id == "acme:42"
            assert source == "github"
            assert work_stream_items[0]["id"] == "WL-159"
            return {"WL-159": "COMPLETED"}

        def _fake_perform_board_sync(
            board_id: str,
            source: str,
            work_stream_items: list[dict[str, str]],
            write_batch_size: int = 50,
        ) -> dict[str, object]:
            calls.append(
                {
                    "board_id": board_id,
                    "source": source,
                    "status": work_stream_items[0]["status"],
                }
            )
            return {
                "synced": 1,
                "failed": 0,
                "updated_items": work_stream_items,
                "errors": [],
                "batches": 1,
            }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                cmd,
                "_load_sync_policy_contract_if_present",
                lambda: SimpleNamespace(
                    conflict_precedence="local_wins",
                    connector_policy=lambda connector: SimpleNamespace(
                        conflict_precedence="local_wins",
                        enabled=True,
                        mode="enforce",
                        board_id="acme:42",
                    ),
                ),
            )
            mp.setattr(cmd, "_fetch_remote_statuses", _fake_fetch_remote_statuses)
            mp.setattr(cmd, "_perform_board_sync", _fake_perform_board_sync)
            result = cmd.sync_board(board_id=None, source="github", dry_run=False)

        assert result.status == SyncOperationStatus.SUCCESS
        assert calls == [{"board_id": "acme:42", "source": "github", "status": "IN_PROGRESS"}]
        assert result.details["conflict_precedence"] == "local_wins"
        assert result.details["reconciled_items"] == 0

    def test_sync_board_remote_wins_prefers_remote_status(self, temp_root: Path) -> None:
        """When remote_wins is configured, remote status overwrites local draft."""
        work_stream = temp_root / "docs" / "reference" / "WORK_STREAM.md"
        _write_work_stream(
            work_stream,
            """# WORK_STREAM

### [WL-160] Divergence
**Status:** BACKLOG
""",
        )
        cmd = SyncCommand(project_root=temp_root)
        calls: list[dict[str, str]] = []

        def _fake_fetch_remote_statuses(
            *,
            board_id: str,
            source: str,
            work_stream_items: list[dict[str, str]],
        ) -> dict[str, str]:
            assert board_id == "ignored"
            assert source == "github"
            return {"WL-160": "COMPLETED"}

        def _fake_perform_board_sync(
            board_id: str,
            source: str,
            work_stream_items: list[dict[str, str]],
            write_batch_size: int = 50,
        ) -> dict[str, object]:
            calls.append(
                {
                    "board_id": board_id,
                    "source": source,
                    "status": work_stream_items[0]["status"],
                }
            )
            return {
                "synced": 1,
                "failed": 0,
                "updated_items": work_stream_items,
                "errors": [],
                "batches": 1,
            }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                cmd,
                "_load_sync_policy_contract_if_present",
                lambda: SimpleNamespace(
                    conflict_precedence="remote_wins",
                    connector_policy=lambda connector: SimpleNamespace(
                        conflict_precedence="remote_wins",
                        enabled=True,
                        mode="enforce",
                        board_id="acme:42",
                    ),
                ),
            )
            mp.setattr(cmd, "_fetch_remote_statuses", _fake_fetch_remote_statuses)
            mp.setattr(cmd, "_perform_board_sync", _fake_perform_board_sync)
            result = cmd.sync_board(board_id="ignored", source="github", dry_run=False)

        assert result.status == SyncOperationStatus.SUCCESS
        assert calls == [{"board_id": "ignored", "source": "github", "status": "COMPLETED"}]
        assert result.details["conflict_precedence"] == "remote_wins"
        assert result.details["reconciled_items"] == 1
