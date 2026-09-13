"""Unit tests for confidence calibration loading diagnostics."""

from pathlib import Path

import pytest

from thegent.ux.calibration import ConfidenceCalibrator


class _Settings:
    def __init__(self, session_dir: Path) -> None:
        self.session_dir = session_dir


def test_load_calibration_logs_corrupt_json_and_returns_empty(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text("{bad", encoding="utf-8")

    caplog.set_level("WARNING", logger="thegent.ux.calibration")
    calibrator = ConfidenceCalibrator(_Settings(tmp_path))
    assert calibrator.bias_map == {}
    assert "Failed to parse calibration JSON" in caplog.text


def test_load_calibration_logs_wrong_shape_and_returns_empty(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text('["not", "a", "map"]', encoding="utf-8")

    caplog.set_level("WARNING", logger="thegent.ux.calibration")
    calibrator = ConfidenceCalibrator(_Settings(tmp_path))
    assert calibrator.bias_map == {}
    assert "Invalid calibration schema" in caplog.text


def test_load_calibration_valid_map(tmp_path: Path) -> None:
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text('{"agent-a": 0.2, "agent-b": -0.1}', encoding="utf-8")

    calibrator = ConfidenceCalibrator(_Settings(tmp_path))
    assert calibrator.bias_map == {"agent-a": 0.2, "agent-b": -0.1}
