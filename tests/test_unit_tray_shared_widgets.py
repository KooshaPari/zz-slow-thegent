"""Unit tests for tray shared widgets."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestCardStyle:
    """Tests for CARD_STYLE constant."""

    def test_card_style_exists(self) -> None:
        """CARD_STYLE is defined."""
        from thegent.tray.core.shared_widgets import CARD_STYLE

        assert isinstance(CARD_STYLE, str)
        assert len(CARD_STYLE) > 0


@pytest.mark.unit
class TestMetricCard:
    """Tests for metric_card function."""

    def test_creates_groupbox(self) -> None:
        """metric_card creates a QGroupBox."""
        with (
            patch("thegent.tray.core.shared_widgets.QGroupBox") as mock_groupbox,
            patch("thegent.tray.core.shared_widgets.QGridLayout") as mock_layout,
            patch("thegent.tray.core.shared_widgets.QLabel") as mock_label,
        ):
            # Setup mocks
            instance = MagicMock()
            mock_groupbox.return_value = instance
            mock_layout_instance = MagicMock()
            mock_layout.return_value = mock_layout_instance
            mock_label_instance = MagicMock()
            mock_label.return_value = mock_label_instance

            from thegent.tray.core.shared_widgets import metric_card

            metric_card("CPU", "45", "%")

            # Verify QGroupBox was called
            mock_groupbox.assert_called_once_with("CPU")

    def test_sets_title(self) -> None:
        """metric_card sets the title via constructor."""
        with (
            patch("thegent.tray.core.shared_widgets.QGroupBox") as mock_groupbox,
            patch("thegent.tray.core.shared_widgets.QGridLayout"),
            patch("thegent.tray.core.shared_widgets.QLabel"),
        ):
            instance = MagicMock()
            mock_groupbox.return_value = instance

            from thegent.tray.core.shared_widgets import metric_card

            metric_card("Memory", "1024", "MB")

            # Verify title was set via constructor
            mock_groupbox.assert_called_with("Memory")

    def test_contains_value_and_unit(self) -> None:
        """metric_card displays value and unit."""
        with (
            patch("thegent.tray.core.shared_widgets.QGroupBox"),
            patch("thegent.tray.core.shared_widgets.QGridLayout") as mock_layout,
            patch("thegent.tray.core.shared_widgets.QLabel") as mock_label,
        ):
            mock_layout_instance = MagicMock()
            mock_layout.return_value = mock_layout_instance
            mock_label.side_effect = [MagicMock(), MagicMock()]

            from thegent.tray.core.shared_widgets import metric_card

            metric_card("Disk", "500", "GB")

            # Verify layout has widgets added
            assert mock_layout_instance.addWidget.call_count == 2


@pytest.mark.unit
class TestCreateStatusBadge:
    """Tests for create_status_badge function."""

    def test_success_status(self) -> None:
        """create_status_badge creates green badge for 'success'."""
        with (
            patch("thegent.tray.core.shared_widgets.QLabel") as mock_label,
            patch("thegent.tray.core.shared_widgets.QColor") as mock_color,
        ):
            mock_instance = MagicMock()
            mock_label.return_value = mock_instance
            mock_color.return_value = MagicMock(name="#22c55e")

            from thegent.tray.core.shared_widgets import create_status_badge

            create_status_badge("success")

            # Verify QLabel was created with correct text
            mock_label.assert_called_once_with("Success")

    def test_warning_status(self) -> None:
        """create_status_badge creates yellow badge for 'warning'."""
        with (
            patch("thegent.tray.core.shared_widgets.QLabel") as mock_label,
            patch("thegent.tray.core.shared_widgets.QColor"),
        ):
            mock_instance = MagicMock()
            mock_label.return_value = mock_instance

            from thegent.tray.core.shared_widgets import create_status_badge

            create_status_badge("warning")

            mock_label.assert_called_once_with("Warning")

    def test_error_status(self) -> None:
        """create_status_badge creates red badge for 'error'."""
        with (
            patch("thegent.tray.core.shared_widgets.QLabel") as mock_label,
            patch("thegent.tray.core.shared_widgets.QColor"),
        ):
            mock_instance = MagicMock()
            mock_label.return_value = mock_instance

            from thegent.tray.core.shared_widgets import create_status_badge

            create_status_badge("error")

            mock_label.assert_called_once_with("Error")

    def test_unknown_status(self) -> None:
        """create_status_badge creates default badge for unknown status."""
        with (
            patch("thegent.tray.core.shared_widgets.QLabel") as mock_label,
            patch("thegent.tray.core.shared_widgets.QColor"),
        ):
            mock_instance = MagicMock()
            mock_label.return_value = mock_instance

            from thegent.tray.core.shared_widgets import create_status_badge

            create_status_badge("unknown")

            mock_label.assert_called_once_with("Unknown")
