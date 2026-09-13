"""WL-133 L9 post-success helpers wire-up regression.

Locks down the final ``_phase_*`` helper wire-up batch into
``run_impl_core`` (continues WL-131 / WL-132):

* ``_phase_update_teammate_status`` — TeammateManager.update_status
  block (WP-16002). Pre-extraction this lived inline as a 14-line
  try/except block guarded by ``getattr(run_meta, "task_id", None)``.

Also removes the dead ``_phase_condense_output`` helper (its body was
duplicated inside ``_phase_assemble_payload`` so the helper was never
called from any site).

Each helper is contract-pinned in ``run_execution_core_helpers.py``;
this test guards against accidental re-inlining of the historical
bodies so the orchestrator's CC reduction is preserved.
"""

from __future__ import annotations

import importlib
import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

_WIRE_DONE = ("_phase_update_teammate_status",)


@pytest.fixture(scope="module")
def run_impl_core_source() -> str:
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    return inspect.getsource(helpers.run_impl_core)


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module("thegent.cli.services.run_execution_core_helpers")


@pytest.mark.parametrize("phase_name", list(_WIRE_DONE))
def test_run_impl_core_delegates_postsuccess_to_helper(phase_name: str, run_impl_core_source: str) -> None:
    """``run_impl_core`` must call the post-success helper, not inline the body."""
    assert f"{phase_name}(" in run_impl_core_source, (
        f"Expected run_impl_core to delegate to {phase_name} helper for "
        f"post-success parity with the pre-extraction monolith."
    )


def test_run_impl_core_has_no_inline_teammate_block(run_impl_core_source: str) -> None:
    """TeammateManager import + instantiation must live in the helper, not the orchestrator.

    The pre-extraction body imported ``from thegent.governance.teammates
    import TeammateManager`` inline and called ``mgr.update_status(...)``
    inside ``run_impl_core``.  That block must be gone.
    """
    forbidden = [
        "from thegent.governance.teammates import TeammateManager",
        'TeammateManager(settings.cache_dir / "teammates.json")',
        "mgr.update_status",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline teammate block fragment {sig!r}; must be delegated to _phase_update_teammate_status."
        )


def test_phase_update_teammate_status_no_task_id_is_noop(helpers_module) -> None:
    """Helper must be a no-op (no manager instantiation) when task_id is falsy."""
    settings = MagicMock()
    result = SimpleNamespace(stdout="hello", stderr="oops")
    with patch("thegent.governance.teammates.TeammateManager") as mock_mgr:
        helpers_module._phase_update_teammate_status(
            settings=settings,
            task_id="",
            status="completed",
            result=result,
        )
        mock_mgr.assert_not_called()


def test_phase_update_teammate_status_completed_uses_stdout(helpers_module) -> None:
    """status='completed' → summary is result.stdout[:500]."""
    settings = MagicMock()
    settings.cache_dir = MagicMock()
    result = SimpleNamespace(stdout="x" * 1000, stderr="yerr")
    with patch("thegent.governance.teammates.TeammateManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        helpers_module._phase_update_teammate_status(
            settings=settings,
            task_id="task-42",
            status="completed",
            result=result,
        )
        mock_mgr_cls.assert_called_once_with(settings.cache_dir / "teammates.json")
        mock_mgr.update_status.assert_called_once()
        args, kwargs = mock_mgr.update_status.call_args
        assert args[0] == "task-42"
        assert args[1] == "completed"
        assert len(kwargs["summary"]) == 500


def test_phase_update_teammate_status_failed_uses_stderr(helpers_module) -> None:
    """status='failed' → summary is result.stderr[:500] (or fallback)."""
    settings = MagicMock()
    settings.cache_dir = MagicMock()
    result = SimpleNamespace(stdout="hello", stderr="e" * 1000)
    with patch("thegent.governance.teammates.TeammateManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        helpers_module._phase_update_teammate_status(
            settings=settings,
            task_id="task-42",
            status="failed",
            result=result,
        )
        mock_mgr.update_status.assert_called_once()
        args, kwargs = mock_mgr.update_status.call_args
        assert args[1] == "failed"
        assert len(kwargs["summary"]) == 500
        assert kwargs["summary"].startswith("e")


def test_phase_update_teammate_status_failed_no_stderr_uses_fallback(
    helpers_module,
) -> None:
    """status='failed' with empty stderr → summary is 'Failed without stderr'."""
    settings = MagicMock()
    settings.cache_dir = MagicMock()
    result = SimpleNamespace(stdout="hello", stderr="")
    with patch("thegent.governance.teammates.TeammateManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        helpers_module._phase_update_teammate_status(
            settings=settings,
            task_id="task-42",
            status="failed",
            result=result,
        )
        _args, kwargs = mock_mgr.update_status.call_args
        assert kwargs["summary"] == "Failed without stderr"


def test_phase_update_teammate_status_no_result_uses_fallback(helpers_module) -> None:
    """result is None → summary is 'Failed without stderr' for non-completed statuses."""
    settings = MagicMock()
    settings.cache_dir = MagicMock()
    with patch("thegent.governance.teammates.TeammateManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        helpers_module._phase_update_teammate_status(
            settings=settings,
            task_id="task-42",
            status="failed",
            result=None,
        )
        _args, kwargs = mock_mgr.update_status.call_args
        assert kwargs["summary"] == "Failed without stderr"


def test_phase_update_teammate_status_swallows_exceptions(helpers_module) -> None:
    """A TeammateManager failure must be caught and logged at debug level."""
    settings = MagicMock()
    settings.cache_dir = MagicMock()
    result = SimpleNamespace(stdout="hello", stderr="oops")
    with patch("thegent.governance.teammates.TeammateManager") as mock_mgr_cls:
        mock_mgr_cls.side_effect = RuntimeError("disk full")
        # Must not raise.
        helpers_module._phase_update_teammate_status(
            settings=settings,
            task_id="task-42",
            status="completed",
            result=result,
        )


def test_phase_condense_output_helper_removed(helpers_module) -> None:
    """``_phase_condense_output`` was dead code (logic duplicated in _phase_assemble_payload).

    WL-133 removes it; tests must confirm the symbol no longer exists
    so an accidental re-add (with the inlined body) is caught.
    """
    assert not hasattr(helpers_module, "_phase_condense_output"), (
        "_phase_condense_output is dead code; its logic lives in "
        "_phase_assemble_payload. Restore only if you add a caller."
    )
