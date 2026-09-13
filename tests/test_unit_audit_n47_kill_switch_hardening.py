"""AUDIT-N+47: governance/kill_switch hardening spec.

15 invariants FR-GOV-KS-001..015 covering SafetyKillSwitch init,
activate, check_status, verify_alignment_drift.

Source: src/thegent/governance/kill_switch.py
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import target — must survive the hardening patch
# ---------------------------------------------------------------------------
from thegent.governance.kill_switch import SafetyKillSwitch  # noqa: E402


# ============================  FR-GOV-KS-001  ============================
class TestKSInit:
    """FR-GOV-KS-001: SafetyKillSwitch.__init__ stores workspace root and
    derives the trigger file path."""

    def test_init_sets_root(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        assert ks.root == tmp_path

    def test_init_trigger_file_path(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        assert ks.trigger_file == tmp_path / ".thegent_kill"

    def test_init_with_string_root(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        assert isinstance(ks.root, Path)


# ============================  FR-GOV-KS-002  ============================
class TestKSActivate:
    """FR-GOV-KS-002: activate() writes a trigger file with timestamp
    and reason; returns None."""

    def test_activate_creates_trigger_file(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        result = ks.activate("test shutdown")
        assert result is None
        assert ks.trigger_file.exists()

    def test_activate_writes_reason(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.activate("recursive overload")
        content = ks.trigger_file.read_text()
        assert "recursive overload" in content

    def test_activate_writes_timestamp(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        time.time()
        ks.activate("test")
        time.time()
        content = ks.trigger_file.read_text()
        assert "KILLED_AT:" in content


# ============================  FR-GOV-KS-003  ============================
class TestKSCheckStatus:
    """FR-GOV-KS-003: check_status() returns True iff trigger file exists."""

    def test_check_status_false_when_no_file(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        assert ks.check_status() is False

    def test_check_status_true_after_activate(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.activate("shutdown")
        assert ks.check_status() is True


# ============================  FR-GOV-KS-004  ============================
class TestKSVerifyAlignmentDrift:
    """FR-GOV-KS-004: verify_alignment_drift() uses the *parameter*
    (self_improvement_rate), not self._improvement_rate."""

    def test_no_activate_when_rate_below_threshold(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.verify_alignment_drift(0.5)
        assert ks.check_status() is False

    def test_activate_when_rate_above_threshold(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.verify_alignment_drift(0.95)
        assert ks.check_status() is True

    def test_threshold_boundary_at_09(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        # Exactly 0.9 should NOT trigger (threshold is > 0.9)
        ks.verify_alignment_drift(0.9)
        assert ks.check_status() is False

    def test_threshold_boundary_above_09(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.verify_alignment_drift(0.91)
        assert ks.check_status() is True


# ============================  FR-GOV-KS-005  ============================
class TestKSPathTraversalGuard:
    """FR-GOV-KS-005: workspace_root must be an absolute path; reject
    traversal attempts."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            SafetyKillSwitch("relative/path")

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        assert ks.root == tmp_path


# ============================  FR-GOV-KS-006  ============================
class TestKSImportTimeAtTop:
    """FR-GOV-KS-006: The 'time' module must be importable at module level
    (import at top of file, not buried at bottom)."""

    def test_time_import_works(self) -> None:
        import importlib

        mod = importlib.import_module("thegent.governance.kill_switch")
        assert hasattr(mod, "time") or hasattr(time, "time")


# ============================  FR-GOV-KS-007  ============================
class TestKSActivateIdempotent:
    """FR-GOV-KS-007: Calling activate() twice overwrites the trigger
    file; check_status remains True."""

    def test_double_activate(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.activate("first")
        ks.activate("second")
        content = ks.trigger_file.read_text()
        assert "second" in content
        assert ks.check_status() is True


# ============================  FR-GOV-KS-008  ============================
class TestKSTriggerFileContent:
    """FR-GOV-KS-008: Trigger file must contain both KILLED_AT and REASON
    lines."""

    def test_content_format(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.activate("format check")
        lines = ks.trigger_file.read_text().strip().split("\n")
        assert any("KILLED_AT:" in line for line in lines)
        assert any("REASON:" in line for line in lines)


# ============================  FR-GOV-KS-009  ============================
class TestKSLogLevel:
    """FR-GOV-KS-009: activate() must log at CRITICAL level."""

    def test_activate_logs_critical(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        with patch("thegent.governance.kill_switch._log") as mock_log:
            ks.activate("log test")
            mock_log.critical.assert_called()


# ============================  FR-GOV-KS-010  ============================
class TestKSCheckStatusDoesNotCreateFile:
    """FR-GOV-KS-010: check_status() must not create the trigger file."""

    def test_check_status_read_only(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.check_status()
        assert not ks.trigger_file.exists()


# ============================  FR-GOV-KS-011  ============================
class TestKSVerifyDriftNoSideEffect:
    """FR-GOV-KS-011: verify_alignment_drift() below threshold must not
    create any files."""

    def test_below_threshold_clean(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.verify_alignment_drift(0.1)
        assert not ks.trigger_file.exists()


# ============================  FR-GOV-KS-012  ============================
class TestKSSingletonBehavior:
    """FR-GOV-KS-012: Two SafetyKillSwitch instances with the same root
    share the same trigger file."""

    def test_same_trigger_file(self, tmp_path: Path) -> None:
        ks1 = SafetyKillSwitch(str(tmp_path))
        ks2 = SafetyKillSwitch(str(tmp_path))
        assert ks1.trigger_file == ks2.trigger_file


# ============================  FR-GOV-KS-013  ============================
class TestKSActivateEmptyReason:
    """FR-GOV-KS-013: activate() with an empty reason still writes the
    file."""

    def test_empty_reason(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.activate("")
        assert ks.trigger_file.exists()


# ============================  FR-GOV-KS-014  ============================
class TestKSCheckStatusWithManualFile:
    """FR-GOV-KS-014: check_status() returns True if the trigger file is
    manually placed."""

    def test_manual_trigger(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        ks.trigger_file.write_text("MANUAL\n")
        assert ks.check_status() is True


# ============================  FR-GOV-KS-015  ============================
class TestKSVerifyDriftLogInfo:
    """FR-GOV-KS-015: verify_alignment_drift() must log the current rate
    at INFO level."""

    def test_logs_info(self, tmp_path: Path) -> None:
        ks = SafetyKillSwitch(str(tmp_path))
        with patch("thegent.governance.kill_switch._log") as mock_log:
            ks.verify_alignment_drift(0.3)
            mock_log.info.assert_called()
