"""Unit tests for post-agent-run hook dispatch wiring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.agents.base import RunResult
from thegent.governance.post_agent_run_hook import _dispatch_post_agent_run_hook


def test_dispatch_post_agent_run_hook_sends_expected_payload_and_env(tmp_path: Path) -> None:
    """Dispatch uses hook-dispatcher postagentrun with JSON stdin and required env vars."""
    with patch("thegent.governance.post_agent_run_hook.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _dispatch_post_agent_run_hook(
            result=RunResult(exit_code=0, stdout="ok", stderr=""),
            run_id="run-123",
            session_id="sess-456",
            cwd=tmp_path,
            extra_context={"vetter_policy": "strict", "source": "unit-test"},
        )

    assert mock_run.call_count == 1
    args = mock_run.call_args.args[0]
    kwargs = mock_run.call_args.kwargs
    assert args == ["hook-dispatcher", "postagentrun"]
    assert kwargs["cwd"] == str(tmp_path)
    payload = json.loads(kwargs["input"])
    assert payload["run_id"] == "run-123"
    assert payload["session_id"] == "sess-456"
    assert payload["cwd"] == str(tmp_path)
    assert payload["context"]["source"] == "unit-test"
    assert payload["result"]["exit_code"] == 0
    assert kwargs["env"]["THGENT_RUN_ID"] == "run-123"
    assert kwargs["env"]["THGENT_SESSION_ID"] == "sess-456"
    assert kwargs["env"]["THGENT_VETTER_POLICY"] == "strict"


def test_dispatch_post_agent_run_hook_raises_on_non_zero_exit() -> None:
    """Dispatcher non-zero exit fails fast with RuntimeError."""
    with patch("thegent.governance.post_agent_run_hook.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=7, stdout="", stderr="dispatcher failed")
        with pytest.raises(RuntimeError, match="hook-dispatcher postagentrun failed"):
            _dispatch_post_agent_run_hook(
                result={"status": "failed"},
                run_id="run-1",
                session_id="sess-1",
                cwd=None,
                extra_context={},
            )
