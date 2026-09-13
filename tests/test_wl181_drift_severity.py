# @trace WL-181
"""Tests for Status Drift Severity Classification.

Validates severity tier classification and escalation threshold behavior
for status drift in sync operations.
"""

from __future__ import annotations

import pytest

from thegent.integrations.drift_severity import (
    DriftEscalationThresholds,
    DriftSeverity,
    classify_drift,
    get_default_thresholds,
)


@pytest.mark.requirement("WL-181")
def test_drift_severity_enum_values():
    """Test that DriftSeverity enum has required values."""
    assert DriftSeverity.LOW.value == "low"
    assert DriftSeverity.MEDIUM.value == "medium"
    assert DriftSeverity.HIGH.value == "high"
    assert DriftSeverity.CRITICAL.value == "critical"


@pytest.mark.requirement("WL-181")
def test_classify_drift_no_drift_matching_status():
    """Test that matching statuses result in LOW severity."""
    severity = classify_drift("open", "open", age_hours=100)
    assert severity == DriftSeverity.LOW


@pytest.mark.requirement("WL-181")
def test_classify_drift_low_age():
    """Test that drift with low age is classified as LOW."""
    thresholds = DriftEscalationThresholds(medium_age_hours=6)
    severity = classify_drift("open", "closed", age_hours=3, thresholds=thresholds)
    assert severity == DriftSeverity.LOW


@pytest.mark.requirement("WL-181")
def test_classify_drift_medium_age():
    """Test that drift with medium age is classified as MEDIUM."""
    thresholds = DriftEscalationThresholds(
        medium_age_hours=6, high_age_hours=24, critical_age_hours=72
    )
    severity = classify_drift("open", "closed", age_hours=12, thresholds=thresholds)
    assert severity == DriftSeverity.MEDIUM


@pytest.mark.requirement("WL-181")
def test_classify_drift_high_age():
    """Test that drift with high age is classified as HIGH."""
    thresholds = DriftEscalationThresholds(
        medium_age_hours=6, high_age_hours=24, critical_age_hours=72
    )
    severity = classify_drift("open", "closed", age_hours=48, thresholds=thresholds)
    assert severity == DriftSeverity.HIGH


@pytest.mark.requirement("WL-181")
def test_classify_drift_critical_age():
    """Test that drift with critical age is classified as CRITICAL."""
    thresholds = DriftEscalationThresholds(
        medium_age_hours=6, high_age_hours=24, critical_age_hours=72
    )
    severity = classify_drift("open", "closed", age_hours=100, thresholds=thresholds)
    assert severity == DriftSeverity.CRITICAL


@pytest.mark.requirement("WL-181")
def test_classify_drift_default_thresholds():
    """Test classification with default thresholds."""
    # Default: medium=6, high=24, critical=72
    assert classify_drift("a", "b", age_hours=3) == DriftSeverity.LOW
    assert classify_drift("a", "b", age_hours=12) == DriftSeverity.MEDIUM
    assert classify_drift("a", "b", age_hours=36) == DriftSeverity.HIGH
    assert classify_drift("a", "b", age_hours=100) == DriftSeverity.CRITICAL


@pytest.mark.requirement("WL-181")
def test_classify_drift_negative_age_raises_error():
    """Test that negative age raises ValueError."""
    with pytest.raises(ValueError, match="must be non-negative"):
        classify_drift("open", "closed", age_hours=-1)


@pytest.mark.requirement("WL-181")
def test_drift_escalation_thresholds_validate():
    """Test threshold validation."""
    # Valid thresholds
    thresholds = DriftEscalationThresholds(
        medium_age_hours=6, high_age_hours=24, critical_age_hours=72
    )
    assert thresholds.validate() is True

    # Invalid: out of order
    invalid = DriftEscalationThresholds(
        medium_age_hours=24, high_age_hours=6, critical_age_hours=72
    )
    with pytest.raises(ValueError, match="ascending order"):
        invalid.validate()


@pytest.mark.requirement("WL-181")
def test_get_default_thresholds():
    """Test the default thresholds factory."""
    thresholds = get_default_thresholds()
    assert thresholds.medium_age_hours == 6
    assert thresholds.high_age_hours == 24
    assert thresholds.critical_age_hours == 72


@pytest.mark.requirement("WL-181")
def test_classify_drift_boundary_values():
    """Test classification at exact threshold boundaries."""
    thresholds = DriftEscalationThresholds(
        medium_age_hours=6, high_age_hours=24, critical_age_hours=72
    )

    # At boundary: age > threshold triggers next level
    assert (
        classify_drift("a", "b", age_hours=6, thresholds=thresholds)
        == DriftSeverity.LOW
    )
    assert (
        classify_drift("a", "b", age_hours=6.01, thresholds=thresholds)
        == DriftSeverity.MEDIUM
    )
    assert (
        classify_drift("a", "b", age_hours=24, thresholds=thresholds)
        == DriftSeverity.MEDIUM
    )
    assert (
        classify_drift("a", "b", age_hours=24.01, thresholds=thresholds)
        == DriftSeverity.HIGH
    )
    assert (
        classify_drift("a", "b", age_hours=72, thresholds=thresholds)
        == DriftSeverity.HIGH
    )
    assert (
        classify_drift("a", "b", age_hours=72.01, thresholds=thresholds)
        == DriftSeverity.CRITICAL
    )
