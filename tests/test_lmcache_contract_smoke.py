"""Unit tests for lmcache_contract_smoke.py"""

import os
from unittest.mock import MagicMock, patch

import pytest


def test_missing_lmcache_enabled_fails():
    """Test that LMCACHE_ENABLED must be set."""
    with patch.dict(os.environ, {"LMCACHE_ENABLED": ""}):
        import lmcache_contract_smoke as smoke

        result = lmcache_contract_smoke.asyncio.run(smoke._check_lmcache())

        assert result["ok"] is False
        assert "not set" in result["error"]


def test_redis_backend_missing_env():
    """Test Redis backend fails without redis env vars."""
    with patch.dict(os.environ, {"LMCACHE_ENABLED": "1", "LMCACHE_BACKEND": "redis"}):
        with patch("redis.Redis", side_effect=Exception("connection refused")):
            import lmcache_contract_smoke as smoke

            result = lmcache_contract_smoke.asyncio.run(smoke._check_lmcache())

            assert result["ok"] is False
            assert "connection refused" in result["error"].lower()


def test_redis_backend_success():
    """Test Redis backend success."""
    with patch.dict(
        os.environ,
        {
            "LMCACHE_ENABLED": "1",
            "LMCACHE_BACKEND": "redis",
            "LMCACHE_REDIS_HOST": "localhost",
            "LMCACHE_REDIS_PORT": "6379",
        },
    ), patch("redis.Redis") as mock_redis:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_redis.return_value = mock_instance

        import lmcache_contract_smoke as smoke

        result = lmcache_contract_smoke.asyncio.run(smoke._check_lmcache())

        assert result["ok"] is True
        assert result["backend"] == "redis"


def test_http_backend_missing_url():
    """Test HTTP backend fails without URL."""
    with patch.dict(os.environ, {"LMCACHE_ENABLED": "1", "LMCACHE_BACKEND": "http"}):
        import lmcache_contract_smoke as smoke

        # Without LMCACHE_SERVER_URL, should use default
        result = lmcache_contract_smoke.asyncio.run(smoke._check_lmcache())

        # Will try default URL which won't exist, so should fail
        assert result["ok"] is False


def test_backend_not_installed():
    """Test behavior when redis-py not installed."""
    with patch.dict(os.environ, {"LMCACHE_ENABLED": "1", "LMCACHE_BACKEND": "redis"}):
        # Temporarily remove redis from modules
        import sys

        import lmcache_contract_smoke as smoke

        redis_backup = sys.modules.pop("redis", None)

        try:
            result = lmcache_contract_smoke.asyncio.run(smoke._check_lmcache())
            assert result["ok"] is False
            assert "not installed" in result["error"]
        finally:
            if redis_backup:
                sys.modules["redis"] = redis_backup


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
