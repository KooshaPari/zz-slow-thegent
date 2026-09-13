"""Tests for WL-200: Autosync release and migration checklist.

# @trace WL-200
"""

from __future__ import annotations

import pytest

from thegent.integrations.autosync_checklist import (
    get_checklist_items,
    verify_prerequisites,
)


class TestGetChecklistItems:
    """Tests for get_checklist_items function."""

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_returns_list(self):
        """# @trace WL-200 — get_checklist_items returns a list."""
        items = get_checklist_items()
        assert isinstance(items, list)

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_non_empty(self):
        """# @trace WL-200 — get_checklist_items returns non-empty list."""
        items = get_checklist_items()
        assert len(items) > 0

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_all_strings(self):
        """# @trace WL-200 — all checklist items are strings."""
        items = get_checklist_items()
        assert all(isinstance(item, str) for item in items)

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_contains_environment_variable(self):
        """# @trace WL-200 — checklist includes environment variable setup."""
        items = get_checklist_items()
        env_items = [item for item in items if "THEGENT_AUTOSYNC_ENABLED" in item]
        assert len(env_items) > 0

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_contains_sync_interval(self):
        """# @trace WL-200 — checklist includes sync interval configuration."""
        items = get_checklist_items()
        interval_items = [item for item in items if "SYNC_INTERVAL" in item]
        assert len(interval_items) > 0

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_contains_token_setup(self):
        """# @trace WL-200 — checklist includes GitHub token setup."""
        items = get_checklist_items()
        token_items = [item for item in items if "token" in item.lower()]
        assert len(token_items) > 0

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_contains_testing(self):
        """# @trace WL-200 — checklist includes testing step."""
        items = get_checklist_items()
        test_items = [item for item in items if "test" in item.lower()]
        assert len(test_items) > 0

    @pytest.mark.requirement("WL-200")
    def test_get_checklist_items_contains_monitoring(self):
        """# @trace WL-200 — checklist includes monitoring step."""
        items = get_checklist_items()
        monitor_items = [
            item for item in items if "monitor" in item.lower() or "log" in item.lower()
        ]
        assert len(monitor_items) > 0


class TestVerifyPrerequisites:
    """Tests for verify_prerequisites function."""

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_empty_config(self):
        """# @trace WL-200 — verify_prerequisites with empty config returns missing items."""
        missing = verify_prerequisites({})
        assert isinstance(missing, list)
        assert len(missing) > 0

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_all_present(self):
        """# @trace WL-200 — verify_prerequisites returns empty list when all prerequisites present."""
        config = {
            "autosync_enabled": True,
            "sync_interval": 3600,
            "gh_token_present": True,
            "workflows_enabled": True,
            "policy_accepted": True,
        }
        missing = verify_prerequisites(config)
        assert missing == []

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_missing_autosync_enabled(self):
        """# @trace WL-200 — missing autosync_enabled is reported."""
        config = {
            "sync_interval": 3600,
            "gh_token_present": True,
            "workflows_enabled": True,
            "policy_accepted": True,
        }
        missing = verify_prerequisites(config)
        assert len(missing) > 0
        assert any("THEGENT_AUTOSYNC_ENABLED" in item for item in missing)

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_missing_sync_interval(self):
        """# @trace WL-200 — missing sync_interval is reported."""
        config = {
            "autosync_enabled": True,
            "gh_token_present": True,
            "workflows_enabled": True,
            "policy_accepted": True,
        }
        missing = verify_prerequisites(config)
        assert len(missing) > 0
        assert any("SYNC_INTERVAL" in item for item in missing)

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_missing_gh_token(self):
        """# @trace WL-200 — missing GitHub token is reported."""
        config = {
            "autosync_enabled": True,
            "sync_interval": 3600,
            "workflows_enabled": True,
            "policy_accepted": True,
        }
        missing = verify_prerequisites(config)
        assert len(missing) > 0
        assert any("GH_TOKEN" in item for item in missing)

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_missing_workflows(self):
        """# @trace WL-200 — missing workflows_enabled is reported."""
        config = {
            "autosync_enabled": True,
            "sync_interval": 3600,
            "gh_token_present": True,
            "policy_accepted": True,
        }
        missing = verify_prerequisites(config)
        assert len(missing) > 0
        assert any("workflow" in item.lower() for item in missing)

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_missing_policy_accepted(self):
        """# @trace WL-200 — missing policy_accepted is reported."""
        config = {
            "autosync_enabled": True,
            "sync_interval": 3600,
            "gh_token_present": True,
            "workflows_enabled": True,
        }
        missing = verify_prerequisites(config)
        assert len(missing) > 0
        assert any("policy" in item.lower() for item in missing)

    @pytest.mark.requirement("WL-200")
    def test_verify_prerequisites_multiple_missing(self):
        """# @trace WL-200 — multiple missing prerequisites are all reported."""
        config = {
            "autosync_enabled": False,
            "gh_token_present": False,
        }
        missing = verify_prerequisites(config)
        assert (
            len(missing) >= 3
        )  # At least autosync, token, sync_interval, workflows, policy
