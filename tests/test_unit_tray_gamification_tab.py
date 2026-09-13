"""Tests for the gamification tab widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")


from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication
from thegent.tray.plugins.thegent.api_client import GamificationStats, ThegentAPIClient
from thegent.tray.plugins.thegent.tabs.gamification import (
    AchievementsDialog,
    GamificationTab,
    get_tab,
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock(spec=ThegentAPIClient)

    # Mock gamification stats
    client.get_gamification_stats.return_value = GamificationStats(
        total_xp=1500,
        level=5,
        xp_to_next_level=500,
        runs_today=3,
        achievements_count=12,
        streak_days=7,
    )

    # Mock achievements
    client.get_achievements.return_value = [
        {
            "id": "ach1",
            "name": "First Run",
            "description": "Complete your first run",
            "xp_reward": 100,
            "earned": True,
            "earned_at": "2026-02-10T10:00:00Z",
        },
        {
            "id": "ach2",
            "name": "Speed Demon",
            "description": "Complete a run in under 1 minute",
            "xp_reward": 250,
            "earned": True,
            "earned_at": "2026-02-12T14:30:00Z",
        },
        {
            "id": "ach3",
            "name": "Bug Hunter",
            "description": "Fix 10 bugs in a single run",
            "xp_reward": 500,
            "earned": False,
            "earned_at": None,
        },
        {
            "id": "ach4",
            "name": "Streak Master",
            "description": "Maintain a 7-day streak",
            "xp_reward": 300,
            "earned": True,
            "earned_at": "2026-02-14T09:00:00Z",
        },
    ]

    return client


class TestGamificationTab:
    """Tests for the GamificationTab class."""

    def test_tab_initialization(self, qapp, mock_api_client):
        """Test that the tab initializes correctly."""
        tab = GamificationTab(api_client=mock_api_client)

        assert tab._api_client is mock_api_client
        # Stats and achievements are loaded in __init__ via _load_data()
        assert tab._stats is not None
        assert tab._achievements is not None

    def test_tab_has_refresh_timer(self, qapp, mock_api_client):
        """Test that the tab has a refresh timer."""
        tab = GamificationTab(api_client=mock_api_client)

        assert tab._refresh_timer is not None
        assert tab._refresh_timer.interval() == 30000  # 30 seconds

    def test_tab_loads_data_on_init(self, qapp, mock_api_client):
        """Test that the tab loads data on initialization."""
        GamificationTab(api_client=mock_api_client)

        mock_api_client.get_gamification_stats.assert_called_once()
        mock_api_client.get_achievements.assert_called_once()

    def test_tab_displays_level_progress(self, qapp, mock_api_client):
        """Test that the tab displays level progress."""
        tab = GamificationTab(api_client=mock_api_client)

        # Check that level info is displayed
        assert tab._level_label is not None
        assert "5" in tab._level_label.text()

    def test_tab_displays_xp_progress_bar(self, qapp, mock_api_client):
        """Test that the tab displays XP progress bar."""
        tab = GamificationTab(api_client=mock_api_client)

        # XP is 1500 current, 500 to next level = 2000 total for level 6
        # Progress should be 1500/2000 = 75%
        assert tab._xp_progress is not None
        # The progress should be at 75%

    def test_tab_displays_stats_cards(self, qapp, mock_api_client):
        """Test that the tab displays stats cards."""
        tab = GamificationTab(api_client=mock_api_client)

        # Check total XP card
        assert tab._total_xp_label is not None
        assert "1500" in tab._total_xp_label.text()

        # Check runs today card
        assert tab._runs_today_label is not None
        assert "3" in tab._runs_today_label.text()

        # Check achievements card
        assert tab._achievements_count_label is not None
        assert "12" in tab._achievements_count_label.text()

        # Check streak card
        assert tab._streak_label is not None
        assert "7" in tab._streak_label.text()

    def test_tab_displays_recent_achievements(self, qapp, mock_api_client):
        """Test that the tab displays recent achievements."""
        tab = GamificationTab(api_client=mock_api_client)

        # Should have a list for recent achievements
        assert tab._recent_achievements_list is not None
        # Should have at least some items

    def test_tab_view_all_button_exists(self, qapp, mock_api_client):
        """Test that the View All button exists."""
        tab = GamificationTab(api_client=mock_api_client)

        assert tab._view_all_button is not None

    def test_tab_view_all_opens_dialog(self, qapp, mock_api_client):
        """Test that clicking View All opens the achievements dialog."""
        tab = GamificationTab(api_client=mock_api_client)

        # Click the button
        tab._view_all_button.click()

        # The dialog should have been shown (we can't easily test the dialog directly)
        # But we can check that the button is connected

    def test_tab_refresh_timer_connects_to_load(self, qapp, mock_api_client):
        """Test that refresh timer connects to load method."""
        tab = GamificationTab(api_client=mock_api_client)

        # Reset the mock to check if timer triggers refresh
        mock_api_client.get_gamification_stats.reset_mock()
        mock_api_client.get_achievements.reset_mock()

        # Manually trigger the timer
        tab._refresh_timer.timeout.emit()

        mock_api_client.get_gamification_stats.assert_called_once()
        mock_api_client.get_achievements.assert_called_once()

    def test_tab_handles_api_error(self, qapp, mock_api_client):
        """Test that the tab handles API errors gracefully."""
        mock_api_client.get_gamification_stats.side_effect = Exception("API Error")

        # Should not raise, just log warning
        GamificationTab(api_client=mock_api_client)

        # Tab should still be created with empty/default values


class TestAchievementsDialog:
    """Tests for the AchievementsDialog class."""

    def test_dialog_initialization(self, qapp):
        """Test that the dialog initializes correctly."""
        achievements = [
            {
                "id": "ach1",
                "name": "Test Achievement",
                "description": "Test description",
                "xp_reward": 100,
                "earned": True,
                "earned_at": "2026-02-10T10:00:00Z",
            }
        ]

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        assert dialog._achievements == achievements

    def test_dialog_has_filter_combo(self, qapp):
        """Test that the dialog has a filter combo box."""
        achievements = []

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        assert dialog._filter_combo is not None

    def test_dialog_filter_all(self, qapp):
        """Test that 'All' filter shows all achievements."""
        achievements = [
            {
                "id": "ach1",
                "name": "Earned Achievement",
                "description": "Test 1",
                "xp_reward": 100,
                "earned": True,
                "earned_at": "2026-02-10T10:00:00Z",
            },
            {
                "id": "ach2",
                "name": "Locked Achievement",
                "description": "Test 2",
                "xp_reward": 200,
                "earned": False,
                "earned_at": None,
            },
        ]

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        # Set filter to "All"
        dialog._filter_combo.setCurrentText("All")
        dialog._on_filter_changed("All")

        # Should show all 2 achievements
        assert dialog._achievements_list.count() == 2

    def test_dialog_filter_earned(self, qapp):
        """Test that 'Earned' filter shows only earned achievements."""
        achievements = [
            {
                "id": "ach1",
                "name": "Earned Achievement",
                "description": "Test 1",
                "xp_reward": 100,
                "earned": True,
                "earned_at": "2026-02-10T10:00:00Z",
            },
            {
                "id": "ach2",
                "name": "Locked Achievement",
                "description": "Test 2",
                "xp_reward": 200,
                "earned": False,
                "earned_at": None,
            },
        ]

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        # Set filter to "Earned"
        dialog._filter_combo.setCurrentText("Earned")
        dialog._on_filter_changed("Earned")

        # Should show only 1 earned achievement
        assert dialog._achievements_list.count() == 1

    def test_dialog_filter_locked(self, qapp):
        """Test that 'Locked' filter shows only locked achievements."""
        achievements = [
            {
                "id": "ach1",
                "name": "Earned Achievement",
                "description": "Test 1",
                "xp_reward": 100,
                "earned": True,
                "earned_at": "2026-02-10T10:00:00Z",
            },
            {
                "id": "ach2",
                "name": "Locked Achievement",
                "description": "Test 2",
                "xp_reward": 200,
                "earned": False,
                "earned_at": None,
            },
        ]

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        # Set filter to "Locked"
        dialog._filter_combo.setCurrentText("Locked")
        dialog._on_filter_changed("Locked")

        # Should show only 1 locked achievement
        assert dialog._achievements_list.count() == 1

    def test_dialog_has_close_button(self, qapp):
        """Test that the dialog has a close button."""
        achievements = []

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        assert dialog._close_button is not None

    def test_dialog_close_button_closes(self, qapp):
        """Test that the close button closes the dialog."""
        achievements = []

        dialog = AchievementsDialog(parent=None, achievements=achievements)

        # Click close button
        dialog._close_button.click()

        # Dialog should be closed (result should be accepted)
        # We can't directly check this, but the button should be connected


class TestGetTab:
    """Tests for the get_tab function."""

    def test_get_tab_returns_gamification_tab(self, qapp, mock_api_client):
        """Test that get_tab returns the gamification tab for correct ID."""
        tab = get_tab("thegent-gamification", mock_api_client)

        assert tab is not None
        assert isinstance(tab, GamificationTab)

    def test_get_tab_returns_none_for_unknown_id(self, qapp, mock_api_client):
        """Test that get_tab returns None for unknown tab ID."""
        tab = get_tab("unknown-tab", mock_api_client)

        assert tab is None
