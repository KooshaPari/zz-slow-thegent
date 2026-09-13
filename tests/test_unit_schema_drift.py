"""Unit tests for schema drift detection.

# @trace WL-210
"""

from __future__ import annotations

import pytest

from thegent.sync.schema import detect_schema_drift


@pytest.mark.requirement("WL-210")
def test_detect_schema_drift_reports_missing_and_unexpected():
    report = detect_schema_drift(mapped_fields={"a", "b", "c"}, remote_fields={"b", "c", "d"})
    assert report.missing_fields == ["a"]
    assert report.unexpected_fields == ["d"]
    assert report.has_drift is True


@pytest.mark.requirement("WL-210")
def test_detect_schema_drift_no_drift():
    report = detect_schema_drift(mapped_fields={"a", "b"}, remote_fields={"a", "b"})
    assert report.missing_fields == []
    assert report.unexpected_fields == []
    assert report.has_drift is False
