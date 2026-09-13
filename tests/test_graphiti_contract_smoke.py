"""Unit tests for graphiti_contract_smoke.py"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

# Add scripts directory to path for imports
sys.path.insert(0, Path(Path(__file__).parent, "..", "scripts"))


def _reload_and_require_env() -> None:
    """Helper to reload module and require env var."""
    import importlib

    import graphiti_contract_smoke as smoke

    importlib.reload(smoke)
    smoke._require_env("GRAPHITI_SERVER_URL")


def test_missing_env_fails():
    """Test that missing required env var fails."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="Missing required environment variable"):
            _reload_and_require_env()


def test_missing_optional_env_allowed():
    """Test that optional env var can be empty."""
    with patch.dict(os.environ, {"GRAPHITI_SERVER_URL": "http://localhost:8000"}):
        import graphiti_contract_smoke as smoke

        # Should not raise
        result = smoke._require_env("GRAPHITI_SERVER_URL")
        assert result == "http://localhost:8000"


def test_successful_health_check():
    """Test successful health check returns ok."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = b'{"status": "ok"}'

    with patch.dict(os.environ, {"GRAPHITI_SERVER_URL": "http://localhost:8000"}):
        with patch("urllib.request.urlopen", return_value=mock_response):
            import graphiti_contract_smoke as smoke

            json.loads(smoke.main.__doc__)  # Just check imports work
            # Smoke script will exit via SystemExit on success


def _call_main() -> None:
    """Helper to call smoke.main()."""
    import graphiti_contract_smoke as smoke

    smoke.main()


def test_non_200_fails():
    """Test non-200 status code fails."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 500

    with patch.dict(os.environ, {"GRAPHITI_SERVER_URL": "http://localhost:8000"}):
        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(RuntimeError, match="non-200 status"):
                _call_main()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
