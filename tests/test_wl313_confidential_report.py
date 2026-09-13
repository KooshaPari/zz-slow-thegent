"""Tests for WL-313: Confidential Report Mode.

@trace WL-313
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.confidential_report import (
    ConfidentialReportFilter,
    ReportSensitivity,
)


@pytest.mark.requirement("WL-313")
def test_report_sensitivity_enum() -> None:
    """Test ReportSensitivity enum values."""
    assert ReportSensitivity.PUBLIC.value == "public"
    assert ReportSensitivity.CONFIDENTIAL.value == "confidential"


@pytest.mark.requirement("WL-313")
def test_redact_fields_constant() -> None:
    """Test REDACT_FIELDS contains expected patterns."""
    fields = ConfidentialReportFilter.REDACT_FIELDS
    assert "token" in fields
    assert "secret" in fields
    assert "password" in fields
    assert "api_key" in fields
    assert "auth" in fields
    assert "credential" in fields


@pytest.mark.requirement("WL-313")
def test_redact_public_returns_unchanged() -> None:
    """Test that PUBLIC sensitivity returns data unchanged."""
    data = {"user": "alice", "token": "secret123"}
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.PUBLIC)
    assert result == data
    assert result["token"] == "secret123"


@pytest.mark.requirement("WL-313")
def test_redact_confidential_simple() -> None:
    """Test CONFIDENTIAL redacts simple sensitive fields."""
    data = {"user": "alice", "token": "secret123"}
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.CONFIDENTIAL)
    assert result["user"] == "alice"
    assert result["token"] == "[REDACTED]"


@pytest.mark.requirement("WL-313")
def test_redact_confidential_case_insensitive() -> None:
    """Test redaction is case-insensitive."""
    data = {
        "api_token": "secret1",
        "API_KEY": "secret2",
        "Password": "secret3",
    }
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.CONFIDENTIAL)
    assert result["api_token"] == "[REDACTED]"
    assert result["API_KEY"] == "[REDACTED]"
    assert result["Password"] == "[REDACTED]"


@pytest.mark.requirement("WL-313")
def test_redact_confidential_substring_matching() -> None:
    """Test redaction matches substrings."""
    data = {
        "my_token": "secret1",
        "auth_header": "secret2",
        "credential_store": "secret3",
        "name": "alice",
    }
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.CONFIDENTIAL)
    assert result["my_token"] == "[REDACTED]"
    assert result["auth_header"] == "[REDACTED]"
    assert result["credential_store"] == "[REDACTED]"
    assert result["name"] == "alice"


@pytest.mark.requirement("WL-313")
def test_redact_confidential_nested_dicts() -> None:
    """Test redaction works recursively on nested dicts."""
    data = {
        "user": "alice",
        "config": {
            "api_key": "secret1",
            "db": {
                "password": "secret2",
            },
        },
    }
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.CONFIDENTIAL)
    assert result["user"] == "alice"
    assert result["config"]["api_key"] == "[REDACTED]"
    assert result["config"]["db"]["password"] == "[REDACTED]"


@pytest.mark.requirement("WL-313")
def test_redact_confidential_lists_with_sensitive_keys() -> None:
    """Test redaction on fields with sensitive key names."""
    data = {
        "token_list": ["secret1", "secret2"],
        "usernames": ["alice", "bob"],
    }
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.CONFIDENTIAL)
    # "token_list" key contains "token" so it gets redacted
    assert result["token_list"] == "[REDACTED]"
    # "usernames" does not match any redact pattern
    assert result["usernames"] == ["alice", "bob"]


@pytest.mark.requirement("WL-313")
def test_redact_confidential_nested_lists_and_dicts() -> None:
    """Test redaction on complex nested structures."""
    data = {
        "users": [
            {
                "name": "alice",
                "api_key": "secret1",
            },
            {
                "name": "bob",
                "token": "secret2",
            },
        ],
    }
    result = ConfidentialReportFilter.redact(data, ReportSensitivity.CONFIDENTIAL)
    assert result["users"][0]["name"] == "alice"
    assert result["users"][0]["api_key"] == "[REDACTED]"
    assert result["users"][1]["name"] == "bob"
    assert result["users"][1]["token"] == "[REDACTED]"


@pytest.mark.requirement("WL-313")
def test_wrap_report_public() -> None:
    """Test wrap_report with PUBLIC sensitivity."""
    report = {"user": "alice", "token": "secret123"}
    result = ConfidentialReportFilter.wrap_report(report, ReportSensitivity.PUBLIC, "REP-001")
    assert result["report_id"] == "REP-001"
    assert result["sensitivity"] == "public"
    assert result["data"]["token"] == "secret123"
    assert "generated_at" in result
    # Verify ISO format timestamp
    datetime.fromisoformat(result["generated_at"])


@pytest.mark.requirement("WL-313")
def test_wrap_report_confidential() -> None:
    """Test wrap_report with CONFIDENTIAL sensitivity."""
    report = {"user": "alice", "token": "secret123"}
    result = ConfidentialReportFilter.wrap_report(report, ReportSensitivity.CONFIDENTIAL, "REP-002")
    assert result["report_id"] == "REP-002"
    assert result["sensitivity"] == "confidential"
    assert result["data"]["user"] == "alice"
    assert result["data"]["token"] == "[REDACTED]"
    assert "generated_at" in result


@pytest.mark.requirement("WL-313")
def test_wrap_report_includes_iso_timestamp() -> None:
    """Test wrap_report includes valid ISO timestamp."""
    report = {"data": "test"}
    before = datetime.now(UTC)
    result = ConfidentialReportFilter.wrap_report(report, ReportSensitivity.PUBLIC, "REP-003")
    after = datetime.now(UTC)

    timestamp = datetime.fromisoformat(result["generated_at"])
    assert before <= timestamp <= after
