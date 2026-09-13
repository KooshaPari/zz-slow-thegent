"""Unit tests for WP-3003: Policy overrides."""

from unittest.mock import MagicMock

import pytest

from thegent.config import ThegentSettings
from thegent.governance.overrides import OverrideManager


@pytest.fixture
def mock_settings(tmp_path):
    settings = MagicMock(spec=ThegentSettings)
    settings.session_dir = tmp_path / "sessions"
    settings.session_dir.mkdir()
    return settings


def test_override_apply_and_check(mock_settings):
    """Test applying and checking an override."""
    manager = OverrideManager(settings=mock_settings)

    # Apply override for 60 minutes
    manager.apply_override("HIGH_RISK_RULE", "Emergency fix", "human-1", duration_minutes=60)

    override = manager.get_override("HIGH_RISK_RULE")
    assert override is not None
    assert override.reason == "Emergency fix"
    assert override.by == "human-1"
    assert override.is_active() is True


def test_override_expiration(mock_settings):
    """Test that overrides expire correctly."""
    manager = OverrideManager(settings=mock_settings)

    # Apply override that is already expired (0 duration)
    manager.apply_override("EXPIRED_RULE", "Test", "human-1", duration_minutes=-1)

    override = manager.get_override("EXPIRED_RULE")
    assert override is None


def test_override_cleanup(mock_settings):
    """Test that expired overrides are cleaned up from disk."""
    manager = OverrideManager(settings=mock_settings)
    policy_id = "CLEANUP_RULE"

    manager.apply_override(policy_id, "Test", "human-1", duration_minutes=-1)

    file_path = mock_settings.session_dir / "overrides" / f"{policy_id}.json"
    assert file_path.exists()

    # Checking it should trigger deletion
    assert manager.get_override(policy_id) is None
    assert not file_path.exists()
