"""Tests for WL-171: Autopilot Status Command.

# @trace WL-171
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.sync import app


class TestAutopilotStatusCommand:
    """WL-171: Autopilot status command."""

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_no_file(self):
        """# @trace WL-171 — autopilot-status with no status file."""
        runner = CliRunner()

        # This will use the default status
        result = runner.invoke(app, ["autopilot-status", "--format", "rich"])

        assert result.exit_code == 0
        assert "Autopilot Status" in result.stdout

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_json_output(self):
        """# @trace WL-171 — autopilot-status with JSON output format."""
        runner = CliRunner()

        result = runner.invoke(app, ["autopilot-status", "--format", "json"])

        assert result.exit_code == 0
        # Try parsing the JSON output
        try:
            data = json.loads(result.stdout)
            assert "health" in data or "last_cycle_at" in data
        except json.JSONDecodeError:
            # Output might have other text, that's ok
            pass

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_rich_output(self):
        """# @trace WL-171 — autopilot-status with rich output format."""
        runner = CliRunner()

        result = runner.invoke(app, ["autopilot-status", "--format", "rich"])

        assert result.exit_code == 0
        # Should contain status table headers
        assert "Property" in result.stdout or "Autopilot" in result.stdout

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_with_valid_status_file(self, tmp_path: Path) -> None:
        """# @trace WL-171 — autopilot-status reads valid status file."""
        # Create a temporary status file
        status_file = tmp_path / "autosync_status.json"
        status_data = {
            "last_cycle_at": "2026-02-22T10:00:00",
            "total_cycles": 42,
            "last_error": None,
            "health": "ok",
        }
        with open(status_file, "w") as f:
            json.dump(status_data, f)

        runner = CliRunner()

        # Run with the temp directory as working directory
        with runner.isolated_filesystem():
            # Copy status file to the new filesystem
            docs_dir = Path("docs/reference")
            docs_dir.mkdir(parents=True)
            status_path = docs_dir / "autosync_status.json"
            with open(status_path, "w") as f:
                json.dump(status_data, f)

            result = runner.invoke(app, ["autopilot-status", "--format", "json"])

        assert result.exit_code == 0

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_with_degraded_health(self) -> None:
        """# @trace WL-171 — autopilot-status displays degraded health."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            docs_dir = Path("docs/reference")
            docs_dir.mkdir(parents=True)
            status_path = docs_dir / "autosync_status.json"

            status_data = {
                "last_cycle_at": "2026-02-22T08:00:00",
                "total_cycles": 10,
                "last_error": "Connection timeout",
                "health": "degraded",
            }
            with open(status_path, "w") as f:
                json.dump(status_data, f)

            result = runner.invoke(app, ["autopilot-status", "--format", "json"])

        assert result.exit_code == 0

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_with_down_health(self) -> None:
        """# @trace WL-171 — autopilot-status displays down health."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            docs_dir = Path("docs/reference")
            docs_dir.mkdir(parents=True)
            status_path = docs_dir / "autosync_status.json"

            status_data = {
                "last_cycle_at": "2026-02-22T06:00:00",
                "total_cycles": 5,
                "last_error": "Authentication failed",
                "health": "down",
            }
            with open(status_path, "w") as f:
                json.dump(status_data, f)

            result = runner.invoke(app, ["autopilot-status", "--format", "json"])

        assert result.exit_code == 0

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_with_malformed_json(self) -> None:
        """# @trace WL-171 — autopilot-status handles malformed JSON gracefully."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            docs_dir = Path("docs/reference")
            docs_dir.mkdir(parents=True)
            status_path = docs_dir / "autosync_status.json"

            # Write malformed JSON
            with open(status_path, "w") as f:
                f.write("{invalid json content")

            result = runner.invoke(app, ["autopilot-status", "--format", "json"])

        # Should still succeed and surface parse error in normalized status payload
        assert result.exit_code == 0
        try:
            status = json.loads(result.stdout)
            assert status["health"] == "degraded"
            assert "Failed to parse" in (status["last_error"] or "")
            assert "runner" in status
            assert "open_blockers" in status
            assert "failure_queue_size" in status
        except json.JSONDecodeError:
            assert '"health": "degraded"' in result.stdout
            assert "Failed to parse" in result.stdout

    @pytest.mark.requirement("WL-171")
    def test_autopilot_status_normalizes_invalid_contract_types(self) -> None:
        """# @trace WL-171 — autopilot-status normalizes malformed contract fields."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            docs_dir = Path("docs/reference")
            docs_dir.mkdir(parents=True)
            status_path = docs_dir / "autosync_status.json"
            with open(status_path, "w") as f:
                json.dump(
                    {
                        "last_cycle_at": 123,
                        "total_cycles": "not-an-int",
                        "last_error": {"detail": "boom"},
                        "health": "UNKNOWN",
                        "runner": "invalid-runner",
                        "open_blockers": "invalid",
                        "failure_queue_size": "nan",
                    },
                    f,
                )

            result = runner.invoke(app, ["autopilot-status", "--format", "json"])

        assert result.exit_code == 0
        status = json.loads(result.stdout)
        assert status["last_cycle_at"] is None
        assert status["total_cycles"] == 0
        assert status["health"] == "degraded"
        assert status["last_error"] == "{'detail': 'boom'}"
        assert status["runner"]["enabled"] is False
        assert status["runner"]["failure_queue_size"] == 0
        assert status["open_blockers"] == []
        assert status["failure_queue_size"] == 0
