"""Tests for WP-3005: Policy drift detection."""

import time
from unittest.mock import MagicMock

import orjson as json
import pytest

from thegent.config import ThegentSettings
from thegent.governance.drift import DriftDetector


@pytest.fixture
def mock_settings(tmp_path):
    settings = MagicMock(spec=ThegentSettings)
    settings.session_dir = tmp_path / "session"
    settings.session_dir.mkdir(parents=True)
    return settings


def test_drift_detector_detects_expired_overrides(mock_settings):
    # Setup: create an expired override manually
    overrides_dir = mock_settings.session_dir / "overrides"
    overrides_dir.mkdir()

    expired_time = time.time() - 3600
    override = {
        "policy_id": "ov_expired",
        "by": "user",
        "expires_at": expired_time,
        "reason": "Old override",
        "created_at": time.time() - 7200,
        "metadata": {},
    }
    with (overrides_dir / "ov_expired.json").open("w") as f:
        json.dump(override, f)

    detector = DriftDetector(mock_settings)
    report = detector.detect_drift()

    assert report["drift_detected"] is True
    assert len(report["expired_overrides"]) == 1
    assert report["expired_overrides"][0]["id"] == "ov_expired"

    # Check log was created
    assert (mock_settings.session_dir / "policy_drift.jsonl").exists()


def test_drift_detector_sweep_cleans_overrides(mock_settings):
    overrides_dir = mock_settings.session_dir / "overrides"
    overrides_dir.mkdir()

    # Create one expired and one valid override
    expired_time = time.time() - 3600
    valid_time = time.time() + 3600

    with (overrides_dir / "expired.json").open("w") as f:
        json.dump(
            {
                "policy_id": "expired",
                "by": "u",
                "expires_at": expired_time,
                "reason": "r",
                "created_at": time.time(),
                "metadata": {},
            },
            f,
        )
    with (overrides_dir / "valid.json").open("w") as f:
        json.dump(
            {
                "policy_id": "valid",
                "by": "u",
                "expires_at": valid_time,
                "reason": "r",
                "created_at": time.time(),
                "metadata": {},
            },
            f,
        )

    detector = DriftDetector(mock_settings)
    results = detector.sweep()

    assert results["overrides_cleaned"] == 1
    assert not (overrides_dir / "expired.json").exists()
    assert (overrides_dir / "valid.json").exists()


def test_drift_detector_establishes_policy_baseline(mock_settings):
    contracts_dir = mock_settings.session_dir / "contracts"
    contracts_dir.mkdir()
    (contracts_dir / "policy.json").write_text(json.dumps({"allow": True}).decode(), encoding="utf-8")

    detector = DriftDetector(mock_settings)
    report = detector.detect_drift()

    assert report["baseline_established"] is True
    assert report["drift_detected"] is False
    baseline_path = mock_settings.session_dir / "policy_contracts_baseline.json"
    assert baseline_path.exists()


def test_drift_detector_detects_policy_contract_change(mock_settings):
    contracts_dir = mock_settings.session_dir / "contracts"
    contracts_dir.mkdir()
    contract_path = contracts_dir / "policy.json"
    contract_path.write_text(json.dumps({"allow": True}).decode(), encoding="utf-8")

    detector = DriftDetector(mock_settings)
    first_report = detector.detect_drift()
    assert first_report["baseline_established"] is True

    contract_path.write_text(json.dumps({"allow": False}).decode(), encoding="utf-8")
    second_report = detector.detect_drift()

    assert second_report["drift_detected"] is True
    assert second_report["policy_mismatches"][0]["contract"] == "policy.json"
    assert second_report["policy_mismatches"][0]["type"] == "changed"
    assert "baseline/policy.json" in second_report["policy_mismatches"][0]["diff"]
    assert "current/policy.json" in second_report["policy_mismatches"][0]["diff"]


def test_drift_detector_detects_policy_contract_add_and_remove(mock_settings):
    contracts_dir = mock_settings.session_dir / "contracts"
    contracts_dir.mkdir()
    first = contracts_dir / "first.json"
    second = contracts_dir / "second.json"
    first.write_text(json.dumps({"a": 1}).decode(), encoding="utf-8")
    second.write_text(json.dumps({"b": 2}).decode(), encoding="utf-8")

    detector = DriftDetector(mock_settings)
    detector.detect_drift()

    second.unlink()
    (contracts_dir / "third.json").write_text(json.dumps({"c": 3}).decode(), encoding="utf-8")

    report = detector.detect_drift()
    assert report["drift_detected"] is True
    mismatch_types = {(item["contract"], item["type"]) for item in report["policy_mismatches"]}
    assert ("second.json", "removed") in mismatch_types
    assert ("third.json", "added") in mismatch_types


def test_drift_detector_raises_on_invalid_baseline(mock_settings):
    baseline = mock_settings.session_dir / "policy_contracts_baseline.json"
    baseline.write_text(
        json.dumps({"generated_at_utc": "2026-02-23T00:00:00+00:00", "contracts": []}).decode(), encoding="utf-8"
    )

    detector = DriftDetector(mock_settings)
    with pytest.raises(ValueError, match="Invalid policy baseline format"):
        detector.detect_drift()
