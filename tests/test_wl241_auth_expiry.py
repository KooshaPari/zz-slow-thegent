"""Tests for auth expiry detection (WL-241).

# @trace WL-241
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from thegent.integrations.auth_expiry import (
    AuthExpiryDetector,
    ExpiryStatus,
)


class TestAuthExpiryDetector:
    """Test AuthExpiryDetector class."""

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_valid(self):
        """Test detecting valid token."""
        detector = AuthExpiryDetector()
        future = datetime.now(UTC) + timedelta(hours=48)
        token_info = {"expires_at": future}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.VALID
        assert result.is_critical is False
        assert result.hours_remaining > 40

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_expiring_soon(self):
        """Test detecting token expiring soon."""
        detector = AuthExpiryDetector()
        soon = datetime.now(UTC) + timedelta(hours=12)
        token_info = {"expires_at": soon}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.EXPIRING_SOON
        assert result.is_critical is False  # 12 hours is not critical (< 1 hour is critical)
        assert result.hours_remaining < 24

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_expired(self):
        """Test detecting expired token."""
        detector = AuthExpiryDetector()
        past = datetime.now(UTC) - timedelta(hours=1)
        token_info = {"expires_at": past}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.EXPIRED
        assert result.is_critical is True
        assert result.hours_remaining == 0

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_with_timestamp(self):
        """Test detecting expiry from unix timestamp."""
        detector = AuthExpiryDetector()
        future = datetime.now(UTC) + timedelta(hours=48)
        timestamp = int(future.timestamp())
        token_info = {"expiry_timestamp": timestamp}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.VALID
        assert result.expires_at is not None

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_with_ttl(self):
        """Test detecting expiry from TTL (time to live)."""
        detector = AuthExpiryDetector()
        ttl_seconds = 48 * 3600  # 48 hours
        token_info = {"ttl": ttl_seconds}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.VALID
        assert result.hours_remaining > 40

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_with_expires_in(self):
        """Test detecting expiry from expires_in (seconds)."""
        detector = AuthExpiryDetector()
        expires_in = 12 * 3600  # 12 hours
        token_info = {"expires_in": expires_in}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.EXPIRING_SOON
        assert result.hours_remaining < 24

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_with_iso_string(self):
        """Test detecting expiry from ISO format string."""
        detector = AuthExpiryDetector()
        future = datetime.now(UTC) + timedelta(hours=48)
        token_info = {"expires_at": future.isoformat()}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.VALID

    @pytest.mark.requirement("WL-241")
    def test_detect_expiry_missing_info(self):
        """Test detecting expiry with missing info."""
        detector = AuthExpiryDetector()
        token_info = {}

        with pytest.raises(ValueError):
            detector.detect_expiry(token_info)

    @pytest.mark.requirement("WL-241")
    def test_is_expired_quick_check(self):
        """Test quick is_expired check."""
        detector = AuthExpiryDetector()
        past = datetime.now(UTC) - timedelta(hours=1)
        token_info = {"expires_at": past}

        assert detector.is_expired(token_info) is True

    @pytest.mark.requirement("WL-241")
    def test_is_expired_not_expired(self):
        """Test is_expired on valid token."""
        detector = AuthExpiryDetector()
        future = datetime.now(UTC) + timedelta(hours=48)
        token_info = {"expires_at": future}

        assert detector.is_expired(token_info) is False

    @pytest.mark.requirement("WL-241")
    def test_is_expiring_soon_quick_check(self):
        """Test quick is_expiring_soon check."""
        detector = AuthExpiryDetector()
        soon = datetime.now(UTC) + timedelta(hours=12)
        token_info = {"expires_at": soon}

        assert detector.is_expiring_soon(token_info) is True

    @pytest.mark.requirement("WL-241")
    def test_is_expiring_soon_not_expiring(self):
        """Test is_expiring_soon on valid token."""
        detector = AuthExpiryDetector()
        future = datetime.now(UTC) + timedelta(hours=48)
        token_info = {"expires_at": future}

        assert detector.is_expiring_soon(token_info) is False

    @pytest.mark.requirement("WL-241")
    def test_custom_threshold(self):
        """Test custom expiry threshold."""
        detector = AuthExpiryDetector(expiring_soon_threshold_hours=6)
        soon = datetime.now(UTC) + timedelta(hours=8)
        token_info = {"expires_at": soon}

        result = detector.detect_expiry(token_info)

        assert result.status == ExpiryStatus.VALID  # 8 hours > 6 hour threshold
