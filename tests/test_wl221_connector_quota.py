"""Tests for connector quota budgets (WL-221).

# @trace WL-221
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from thegent.integrations.connector_quota import (
    ConnectorQuota,
    QuotaBudgetManager,
    QuotaExhaustedError,
)


class TestConnectorQuota:
    """Test ConnectorQuota dataclass."""

    @pytest.mark.requirement("WL-221")
    def test_quota_creation(self):
        """Test basic quota creation."""
        quota = ConnectorQuota(connector_name="github", daily_limit=100)
        assert quota.connector_name == "github"
        assert quota.daily_limit == 100
        assert quota.used_today == 0
        assert quota.reset_at is not None

    @pytest.mark.requirement("WL-221")
    def test_quota_remaining(self):
        """Test remaining quota calculation."""
        quota = ConnectorQuota(connector_name="github", daily_limit=100, used_today=30)
        assert quota.remaining() == 70

    @pytest.mark.requirement("WL-221")
    def test_quota_remaining_when_exhausted(self):
        """Test remaining quota when exhausted."""
        quota = ConnectorQuota(connector_name="github", daily_limit=100, used_today=100)
        assert quota.remaining() == 0

    @pytest.mark.requirement("WL-221")
    def test_quota_is_exhausted(self):
        """Test is_exhausted method."""
        quota = ConnectorQuota(connector_name="github", daily_limit=100, used_today=100)
        assert quota.is_exhausted() is True

        quota.used_today = 99
        assert quota.is_exhausted() is False


class TestQuotaBudgetManager:
    """Test QuotaBudgetManager class."""

    @pytest.mark.requirement("WL-221")
    def test_register_connector(self):
        """Test registering a connector."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)
        assert "github" in manager._quotas

    @pytest.mark.requirement("WL-221")
    def test_register_invalid_limit(self):
        """Test registering with invalid limit."""
        manager = QuotaBudgetManager()
        with pytest.raises(ValueError):
            manager.register("github", 0)

    @pytest.mark.requirement("WL-221")
    def test_check_quota_available(self):
        """Test checking available quota."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)
        assert manager.check_quota("github") is True
        assert manager.check_quota("github", 50) is True
        assert manager.check_quota("github", 100) is True

    @pytest.mark.requirement("WL-221")
    def test_check_quota_unavailable(self):
        """Test checking when quota is unavailable."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)
        assert manager.check_quota("github", 101) is False

    @pytest.mark.requirement("WL-221")
    def test_check_quota_unregistered(self):
        """Test checking quota for unregistered connector."""
        manager = QuotaBudgetManager()
        with pytest.raises(KeyError):
            manager.check_quota("unknown")

    @pytest.mark.requirement("WL-221")
    def test_consume_quota(self):
        """Test consuming quota."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)
        manager.consume("github", 30)
        quota = manager.get_quota("github")
        assert quota.used_today == 30
        assert quota.remaining() == 70

    @pytest.mark.requirement("WL-221")
    def test_consume_quota_exhausted(self):
        """Test consuming quota when exhausted."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)
        manager.consume("github", 100)
        with pytest.raises(QuotaExhaustedError):
            manager.consume("github", 1)

    @pytest.mark.requirement("WL-221")
    def test_reset_daily(self):
        """Test resetting daily quota."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)

        # Manually set reset time to past
        quota = manager.get_quota("github")
        quota.used_today = 100
        quota.reset_at = datetime.now(UTC) - timedelta(hours=1)

        manager.reset_daily()
        assert quota.used_today == 0
        assert quota.reset_at > datetime.now(UTC)

    @pytest.mark.requirement("WL-221")
    def test_get_all_quotas(self):
        """Test getting all quotas."""
        manager = QuotaBudgetManager()
        manager.register("github", 100)
        manager.register("gitlab", 50)
        quotas = manager.get_all_quotas()
        assert len(quotas) == 2
        assert "github" in quotas
        assert "gitlab" in quotas
