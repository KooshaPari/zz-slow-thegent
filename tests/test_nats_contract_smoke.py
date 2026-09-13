"""Unit tests for nats_contract_smoke.py"""

import os
from unittest.mock import patch

import pytest


def _require_nats_servers() -> None:
    """Helper to require NATS_SERVERS."""
    import nats_contract_smoke as smoke

    smoke._require_env("NATS_SERVERS")


def test_missing_nats_servers_fails():
    """Test that missing NATS_SERVERS fails."""
    with patch_env({"THEGENT_EVENT_BUS": "nats"}):
        # Clear NATS_SERVERS
        env = os.environ.copy()
        env.pop("NATS_SERVERS", None)

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match="Missing required environment variable"):
                _require_nats_servers()


def test_wrong_event_bus_fails():
    """Test that wrong THEGENT_EVENT_BUS fails."""
    with patch.dict(os.environ, {"THEGENT_EVENT_BUS": "local", "NATS_SERVERS": "nats://localhost:4222"}):
        import nats_contract_smoke as smoke

        with pytest.raises(RuntimeError, match="THEGENT_EVENT_BUS is not 'nats'"):
            smoke.main()


def test_nats_py_not_installed():
    """Test behavior when nats-py not installed."""
    with patch.dict(os.environ, {"THEGENT_EVENT_BUS": "nats", "NATS_SERVERS": "nats://localhost:4222"}):
        import nats_contract_smoke as smoke

        # Mock _check_nats to simulate nats-py not installed
        async def mock_check():
            return {"ok": False, "target": "nats", "error": "nats-py not installed"}

        with patch("nats_contract_smoke._check_nats", mock_check):
            with pytest.raises(RuntimeError, match="nats-py not installed"):
                smoke.main()


def test_nats_connection_error():
    """Test NATS connection error handling."""
    with patch.dict(os.environ, {"THEGENT_EVENT_BUS": "nats", "NATS_SERVERS": "nats://localhost:4222"}):
        import nats_contract_smoke as smoke

        async def mock_check():
            return {"ok": False, "target": "nats", "error": "connection refused"}

        with patch("nats_contract_smoke._check_nats", mock_check):
            with pytest.raises(RuntimeError, match="connection refused"):
                smoke.main()


# Helper for patching
def patch_env(env: dict):
    return patch.dict(os.environ, env)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
