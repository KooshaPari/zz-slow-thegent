"""Unit tests for pocketbase_contract_smoke.py"""

import os
from unittest.mock import MagicMock, patch

import pytest


def test_missing_enabled_fails():
    """Test that missing THEGENT_POCKETBASE_ENABLED fails."""
    with patch.dict(os.environ, {"THEGENT_POCKETBASE_ENABLED": ""}):
        import pocketbase_contract_smoke as smoke

        with pytest.raises(RuntimeError, match="THEGENT_POCKETBASE_ENABLED is not set"):
            smoke.main()


def test_disabled_fails():
    """Test that disabled pocketbase fails."""
    with patch.dict(os.environ, {"THEGENT_POCKETBASE_ENABLED": "0"}):
        import pocketbase_contract_smoke as smoke

        with pytest.raises(RuntimeError, match="THEGENT_POCKETBASE_ENABLED is not set"):
            smoke.main()


def test_health_check_failure():
    """Test health check failure handling."""
    with patch.dict(os.environ, {"THEGENT_POCKETBASE_ENABLED": "1", "POCKETBASE_HTTP_ADDR": "127.0.0.1:8090"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.getcode.return_value = 500
            mock_urlopen.return_value = mock_response

            import pocketbase_contract_smoke as smoke

            with pytest.raises(RuntimeError, match="non-200 status"):
                smoke.main()


def test_health_check_success():
    """Test successful health check."""
    with patch.dict(os.environ, {"THEGENT_POCKETBASE_ENABLED": "1", "POCKETBASE_HTTP_ADDR": "127.0.0.1:8090"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_urlopen.return_value = mock_response

            import pocketbase_contract_smoke as smoke

            # Should not raise
            with pytest.raises(SystemExit) as exc_info:
                smoke.main()
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
