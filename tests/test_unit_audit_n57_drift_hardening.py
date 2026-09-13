"""AUDIT-N+57: governance/drift hardening spec (SOTA pass-37).

15 invariants FR-GOV-DR-001..015 covering DriftDetector init,
absolute-path guard, detect_drift (baseline / drift / contracts),
_check_override_file (corrupt / float-expiry / string-expiry),
_log_drift JSONL append, sweep count, __all__, and importability.

Source: src/thegent/governance/drift.py

@trace AUDIT-N+57  FR-GOV-DR-001..015
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.governance import drift as _mod
from thegent.governance.drift import DriftDetector

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _MockSettings:
    """Minimal stand-in for ThegentSettings with a ``session_dir`` attribute."""

    session_dir: Path


def _make_detector(tmp_path: Path) -> DriftDetector:
    """Construct a DriftDetector wired to *tmp_path*."""
    return DriftDetector(_MockSettings(session_dir=tmp_path))


# ---------------------------------------------------------------------------
# FR-GOV-DR-001 -- DriftDetector accepts settings with absolute session_dir
# ---------------------------------------------------------------------------


class TestDRInitAbsolute:
    """FR-GOV-DR-001: ``DriftDetector`` accepts absolute ``session_dir``."""

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        assert det.settings.session_dir == tmp_path

    def test_drift_log_points_into_session_dir(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        assert det.drift_log == tmp_path / "policy_drift.jsonl"


# ---------------------------------------------------------------------------
# FR-GOV-DR-002 -- DriftDetector rejects settings with relative session_dir
# ---------------------------------------------------------------------------


class TestDRPathGuard:
    """FR-GOV-DR-002: ``session_dir`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            DriftDetector(_MockSettings(session_dir=Path("relative/session")))

    def test_rejects_empty_string_based_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            DriftDetector(_MockSettings(session_dir=Path()))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        assert det.settings.session_dir.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-DR-003 -- detect_drift returns baseline_established=True on first run
# ---------------------------------------------------------------------------


class TestDRBaselineEstablished:
    """FR-GOV-DR-003: first ``detect_drift`` establishes a baseline."""

    def test_baseline_established_on_first_run(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert report["baseline_established"] is True

    def test_baseline_file_created(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        det.detect_drift()
        baseline = tmp_path / "policy_contracts_baseline.json"
        assert baseline.exists()


# ---------------------------------------------------------------------------
# FR-GOV-DR-004 -- detect_drift detects removed contracts vs baseline
# ---------------------------------------------------------------------------


class TestDREmptyFirstRun:
    """FR-GOV-DR-004: removed contracts detected when baseline has entries."""

    def test_detects_removed_contract(self, tmp_path: Path) -> None:
        # Seed baseline with a contract that won't exist in current
        baseline = tmp_path / "policy_contracts_baseline.json"
        baseline.write_text(
            json.dumps(
                {
                    "generated_at_utc": "2025-01-01T00:00:00+00:00",
                    "contracts": {"alpha.json": "content-a"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert report["drift_detected"] is True
        types = [m["type"] for m in report["policy_mismatches"]]
        assert "removed" in types


# ---------------------------------------------------------------------------
# FR-GOV-DR-005 -- detect_drift detects added contracts vs baseline
# ---------------------------------------------------------------------------


class TestDRAddedContracts:
    """FR-GOV-DR-005: added contracts detected when current has new entries."""

    def test_detects_added_contract(self, tmp_path: Path) -> None:
        baseline = tmp_path / "policy_contracts_baseline.json"
        baseline.write_text(
            json.dumps(
                {
                    "generated_at_utc": "2025-01-01T00:00:00+00:00",
                    "contracts": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        # Create a contract file that wasn't in the baseline
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "beta.json").write_text("content-b", encoding="utf-8")
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert report["drift_detected"] is True
        types = [m["type"] for m in report["policy_mismatches"]]
        assert "added" in types


# ---------------------------------------------------------------------------
# FR-GOV-DR-006 -- detect_drift detects changed contracts vs baseline
# ---------------------------------------------------------------------------


class TestDRChangedContracts:
    """FR-GOV-DR-006: changed contracts detected when content differs."""

    def test_detects_changed_contract(self, tmp_path: Path) -> None:
        baseline = tmp_path / "policy_contracts_baseline.json"
        baseline.write_text(
            json.dumps(
                {
                    "generated_at_utc": "2025-01-01T00:00:00+00:00",
                    "contracts": {"gamma.json": "old-content"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "gamma.json").write_text("new-content", encoding="utf-8")
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert report["drift_detected"] is True
        types = [m["type"] for m in report["policy_mismatches"]]
        assert "changed" in types


# ---------------------------------------------------------------------------
# FR-GOV-DR-007 -- detect_drift returns drift_detected=False when match
# ---------------------------------------------------------------------------


class TestDRNoDrift:
    """FR-GOV-DR-007: no drift when current contracts match baseline."""

    def test_no_drift_when_contracts_match(self, tmp_path: Path) -> None:
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "delta.json").write_text("stable", encoding="utf-8")
        # Establish baseline from current state
        det = _make_detector(tmp_path)
        first = det.detect_drift()
        assert first["baseline_established"] is True
        # Second run — should detect no drift
        second = det.detect_drift()
        assert second["drift_detected"] is False


# ---------------------------------------------------------------------------
# FR-GOV-DR-008 -- _check_override_file handles corrupt JSON gracefully
# ---------------------------------------------------------------------------


class TestDRCorruptOverride:
    """FR-GOV-DR-008: corrupt override JSON does not crash detection."""

    def test_corrupt_json_skipped(self, tmp_path: Path) -> None:
        overrides_dir = tmp_path / "overrides"
        overrides_dir.mkdir()
        (overrides_dir / "bad.json").write_text("{not-valid-json", encoding="utf-8")
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        # Corrupt file is silently skipped — no expired overrides recorded
        assert report["expired_overrides"] == []


# ---------------------------------------------------------------------------
# FR-GOV-DR-009 -- _check_override_file detects expired float-timestamp
# ---------------------------------------------------------------------------


class TestDRExpiredFloat:
    """FR-GOV-DR-009: float ``expires_at`` in the past triggers drift."""

    def test_expired_float_detected(self, tmp_path: Path) -> None:
        overrides_dir = tmp_path / "overrides"
        overrides_dir.mkdir()
        (overrides_dir / "ov1.json").write_text(
            json.dumps(
                {
                    "policy_id": "pol-1",
                    "by": "tester",
                    "expires_at": time.time() - 3600,
                }
            ),
            encoding="utf-8",
        )
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert len(report["expired_overrides"]) == 1
        assert report["expired_overrides"][0]["id"] == "pol-1"
        assert report["drift_detected"] is True


# ---------------------------------------------------------------------------
# FR-GOV-DR-010 -- _check_override_file detects expired string-timestamp
# ---------------------------------------------------------------------------


class TestDRExpiredString:
    """FR-GOV-DR-010: ISO-string ``expires_at`` in the past triggers drift."""

    def test_expired_string_detected(self, tmp_path: Path) -> None:
        overrides_dir = tmp_path / "overrides"
        overrides_dir.mkdir()
        (overrides_dir / "ov2.json").write_text(
            json.dumps(
                {
                    "policy_id": "pol-2",
                    "by": "tester",
                    "expires_at": "2020-01-01T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert len(report["expired_overrides"]) == 1
        assert report["expired_overrides"][0]["id"] == "pol-2"
        assert report["drift_detected"] is True


# ---------------------------------------------------------------------------
# FR-GOV-DR-011 -- _log_drift appends JSONL entries
# ---------------------------------------------------------------------------


class TestDRLogDrift:
    """FR-GOV-DR-011: ``_log_drift`` writes valid JSONL lines."""

    def test_log_drift_appends_jsonl(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        report = {"drift_detected": True, "detail": "test-entry"}
        det._log_drift(report)
        assert det.drift_log.exists()
        lines = det.drift_log.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["detail"] == "test-entry"

    def test_log_drift_appends_multiple(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        det._log_drift({"seq": 1})
        det._log_drift({"seq": 2})
        lines = det.drift_log.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["seq"] == 1
        assert json.loads(lines[1])["seq"] == 2


# ---------------------------------------------------------------------------
# FR-GOV-DR-012 -- sweep returns overrides_cleaned count
# ---------------------------------------------------------------------------


class TestDRSweep:
    """FR-GOV-DR-012: ``sweep`` delegates to OverrideManager and returns count."""

    def test_sweep_returns_overrides_cleaned(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        # Patch cleanup_expired to avoid needing real expired override files
        with patch.object(det.om, "cleanup_expired", return_value=3):
            result = det.sweep()
        assert result == {"overrides_cleaned": 3}

    def test_sweep_returns_zero_when_nothing_cleaned(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        with patch.object(det.om, "cleanup_expired", return_value=0):
            result = det.sweep()
        assert result == {"overrides_cleaned": 0}


# ---------------------------------------------------------------------------
# FR-GOV-DR-013 -- detect_drift creates drift_log file when drift detected
# ---------------------------------------------------------------------------


class TestDRDriftLogFile:
    """FR-GOV-DR-013: drift log file is created when drift is found."""

    def test_drift_log_created_on_drift(self, tmp_path: Path) -> None:
        baseline = tmp_path / "policy_contracts_baseline.json"
        baseline.write_text(
            json.dumps(
                {
                    "generated_at_utc": "2025-01-01T00:00:00+00:00",
                    "contracts": {"x.json": "old"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        det = _make_detector(tmp_path)
        report = det.detect_drift()
        assert report["drift_detected"] is True
        assert det.drift_log.exists()
        lines = det.drift_log.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 1

    def test_drift_log_not_created_when_no_drift(self, tmp_path: Path) -> None:
        det = _make_detector(tmp_path)
        det.detect_drift()  # baseline established, no drift
        assert not det.drift_log.exists()


# ---------------------------------------------------------------------------
# FR-GOV-DR-014 -- __all__ exports DriftDetector
# ---------------------------------------------------------------------------


class TestDRAll:
    """FR-GOV-DR-014: canonical public surface."""

    def test_all_exposes_drift_detector(self) -> None:
        assert "DriftDetector" in _mod.__all__

    def test_all_contains_only_drift_detector(self) -> None:
        assert _mod.__all__ == ["DriftDetector"]


# ---------------------------------------------------------------------------
# FR-GOV-DR-015 -- module is importable without error
# ---------------------------------------------------------------------------


class TestDRImportable:
    """FR-GOV-DR-015: module imports cleanly."""

    def test_module_has_no_import_errors(self) -> None:
        import importlib

        mod = importlib.import_module("thegent.governance.drift")
        assert hasattr(mod, "DriftDetector")
