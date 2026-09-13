"""Unit tests for process registry cleanup behavior."""

import logging
from unittest.mock import patch

from thegent.infra.process_registry import ProcessRegistry


def test_signal_registration_failure_is_logged_without_raising(caplog):
    """Signal registration failure should be captured and not abort registry setup."""
    with patch("thegent.infra.process_registry.atexit.register"):
        with patch(
            "thegent.infra.process_registry.signal.signal",
            side_effect=ValueError("unsupported signal"),
        ):
            with caplog.at_level(logging.DEBUG):
                registry = ProcessRegistry()

    assert registry._cleanup_registered
    assert "Signal registration failed" in caplog.text
    assert "unsupported signal" in caplog.text
