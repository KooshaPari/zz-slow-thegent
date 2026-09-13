from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# scripts package / beads_contract_smoke module was removed.
# Pass the dotted submodule path so importorskip can detect the missing
# leaf and trigger an early skip (the parent ``scripts`` package may
# still be importable on some envs, but the leaf is gone).
pytest.importorskip(
    "scripts.beads_contract_smoke",
    reason="scripts.beads_contract_smoke module no longer importable; beads contract smoke tests skipped",
)
from scripts import (
    beads_contract_smoke,  # noqa: E402  (importorskip may skip before this)
)


def test_main_fails_when_required_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BEADS_BASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="Missing required environment variable: BEADS_BASE_URL"):
        beads_contract_smoke.main()


def test_main_raises_on_non_200_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BEADS_BASE_URL", "https://beads.example")
    mock_response = MagicMock()
    mock_response.getcode.return_value = 500
    mock_response.read.return_value = b"internal error"
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_response
    mock_ctx.__exit__.return_value = False

    with patch("scripts.beads_contract_smoke.urllib.request.urlopen", return_value=mock_ctx):
        with pytest.raises(RuntimeError, match="beads health check returned non-200 status: 500"):
            beads_contract_smoke.main()


def test_main_returns_success_on_200(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("BEADS_BASE_URL", "https://beads.example/")
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = b"ok"
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_response
    mock_ctx.__exit__.return_value = False

    with patch("scripts.beads_contract_smoke.urllib.request.urlopen", return_value=mock_ctx):
        result = beads_contract_smoke.main()

    captured = capsys.readouterr().out
    assert result == 0
    assert '"ok": true' in captured
    assert '"target": "beads"' in captured
    assert '"status": 200' in captured
