"""Unit tests for kratos_contract_smoke.py"""

import os
from unittest.mock import MagicMock, patch

import pytest


def test_wrong_auth_provider_fails():
    """Test that wrong THEGENT_AUTH_PROVIDER fails."""
    with patch.dict(os.environ, {"THEGENT_AUTH_PROVIDER": "local", "KRATOS_PUBLIC_URL": "http://localhost:4433"}):
        import kratos_contract_smoke as smoke

        with pytest.raises(RuntimeError, match="THEGENT_AUTH_PROVIDER is not 'kratos'"):
            smoke.main()


def test_missing_kratos_url_fails():
    """Test that missing KRATOS_PUBLIC_URL fails."""
    with patch.dict(os.environ, {"THEGENT_AUTH_PROVIDER": "kratos"}):
        # Clear KRATOS_PUBLIC_URL
        env = os.environ.copy()
        env.pop("KRATOS_PUBLIC_URL", None)

        with patch.dict(os.environ, env, clear=True):
            import kratos_contract_smoke as smoke

            with pytest.raises(RuntimeError, match="Missing required environment variable"):
                smoke._require_env("KRATOS_PUBLIC_URL")


def test_health_check_failure():
    """Test health check failure handling."""
    with patch.dict(os.environ, {"THEGENT_AUTH_PROVIDER": "kratos", "KRATOS_PUBLIC_URL": "http://localhost:4433"}):
        import kratos_contract_smoke as smoke

        async def mock_check():
            return 500

        with patch("kratos_contract_smoke.asyncio.run", return_value=500):
            with pytest.raises(RuntimeError, match="non-200 status"):
                smoke.main()


def test_health_check_success():
    """Test successful health check."""
    with patch.dict(os.environ, {"THEGENT_AUTH_PROVIDER": "kratos", "KRATOS_PUBLIC_URL": "http://localhost:4433"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_urlopen.return_value = mock_response

            import kratos_contract_smoke as smoke

            # Should not raise
            with pytest.raises(SystemExit) as exc_info:
                smoke.main()
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
