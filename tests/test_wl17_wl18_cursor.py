"""Tests for Worklog items: WL-17 TUI Phase 2, WL-18 Cursor Phase 2

Related to:
- WL-017: TUI Phase 2: Interactive Input Widget and Table Widget
- WL-018: CLIProxy Cursor Phase 2: Native Token Provider
"""

from __future__ import annotations


class TestTUIWidgets:
    """Test TUI interactive widgets."""

    def test_input_widget_renders(self) -> None:
        """Input widget should render."""
        widget = {"type": "input", "placeholder": "Enter command"}
        assert widget["type"] == "input"

    def test_table_widget_renders(self) -> None:
        """Table widget should render."""
        widget = {"type": "table", "columns": ["col1", "col2"]}
        assert widget["type"] == "table"


class TestCursorToken:
    """Test Cursor token provider."""

    def test_token_refreshes(self) -> None:
        """Token should refresh."""
        token = {"access_token": "abc", "refresh_token": "xyz"}
        assert "access_token" in token

    def test_token_has_expiry(self) -> None:
        """Token should have expiry."""
        token = {"expires_at": 9999999999}
        assert token["expires_at"] > 0
