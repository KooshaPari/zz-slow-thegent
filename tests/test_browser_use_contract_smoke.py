"""Unit tests for browser_use_contract_smoke.py"""

import os
from unittest.mock import MagicMock, patch

import pytest


def test_missing_enabled_fails():
    """Test that missing THEGENT_BROWSER_USE_ENABLED fails."""
    with patch.dict(os.environ, {"THEGENT_BROWSER_USE_ENABLED": ""}):
        import browser_use_contract_smoke as smoke

        with pytest.raises(RuntimeError, match="THEGENT_BROWSER_USE_ENABLED is not set"):
            smoke.main()


def test_uvx_not_found():
    """Test behavior when uvx is not found."""
    with patch.dict(os.environ, {"THEGENT_BROWSER_USE_ENABLED": "1"}):
        import browser_use_contract_smoke as smoke

        with patch("subprocess.run", side_effect=FileNotFoundError("uvx not found")):
            with pytest.raises(RuntimeError, match="uvx not found"):
                smoke.main()


def test_browser_use_version_failure():
    """Test browser-use version check failure."""
    with patch.dict(os.environ, {"THEGENT_BROWSER_USE_ENABLED": "1"}):
        import browser_use_contract_smoke as smoke

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Some error"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="browser-use --version failed"):
                smoke.main()


def test_browser_use_available():
    """Test browser-use availability check success."""
    with patch.dict(os.environ, {"THEGENT_BROWSER_USE_ENABLED": "1"}):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.strip.return_value = "0.1.0"

        with patch("subprocess.run", return_value=mock_result):
            import browser_use_contract_smoke as smoke

            # Should not raise
            with pytest.raises(SystemExit) as exc_info:
                smoke.main()
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
