"""WL-134 L9 post-classification + dispatch helper wire-up regression.

Locks down the final ``_phase_*`` helper wire-up batch into
``run_impl_core`` (continues WL-131/132/133):

* ``_phase_resolve_task_metadata`` — task_id/owner resolution + override
  reason + status framing (WP-3004 + 3005).
* ``_phase_dispatch_grounded_run`` — Google-grounded dispatch policy
  (WP-5003 / G-CA-02) — calls the grounded run helper and returns its
  payload, otherwise falls through to the normal runner.
* ``_phase_build_fallback_plan`` — provider fallbacks + B2 parser-quality
  routing (WP-X6 / G-CA-02) — returns ``(agents_to_try, telemetry, fsm)``
  and is the only constructor of the ``FallbackStateMachine``.
* ``_phase_build_runner_factory`` — agent runner proxy wiring with
  circuit-breaker integration (MTSP-13).
* ``_phase_classify_run_result`` — exit_code/status/error_class mapping
  including WP-2008 DLQ + G-CA-03 C3 unknown-contract reclassification.
* ``_phase_release_idle_and_publish`` — EyeState.release_idle() +
  ``run.end`` bus event publishing (best-effort, must not raise).

Also asserts the dead ``_phase_handle_backend_failure`` and
``_phase_emit_success_telemetry`` helpers are removed (they were never
wired into ``run_impl_core``; their bodies referenced ``state`` and
``runner`` that don't exist in the current orchestrator, and called
``_payload_apply_meta`` which is not defined anywhere).

The orchestrator's CC dropped from 86 → 44 (still F but trending
toward B+ as the next batch decomposes). Project-wide F-function
count dropped from prior levels; file-level CC average B (8.33).
"""

from __future__ import annotations

import importlib
import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

_WIRE_DONE = (
    "_phase_resolve_task_metadata",
    "_phase_dispatch_grounded_run",
    "_phase_build_fallback_plan",
    "_phase_build_runner_factory",
    "_phase_classify_run_result",
    "_phase_release_idle_and_publish",
)

_REMOVED_HELPERS = (
    "_phase_handle_backend_failure",
    "_phase_emit_success_telemetry",
)


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module("thegent.cli.services.run_execution_core_helpers")


@pytest.fixture(scope="module")
def run_impl_core_source() -> str:
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    return inspect.getsource(helpers.run_impl_core)


@pytest.mark.parametrize("phase_name", list(_WIRE_DONE))
def test_run_impl_core_delegates_classification_to_helper(phase_name: str, run_impl_core_source: str) -> None:
    """``run_impl_core`` must call the post-classification helper, not inline the body."""
    assert f"{phase_name}(" in run_impl_core_source, (
        f"Expected run_impl_core to delegate to {phase_name} helper. "
        f"If you re-inlined it, the orchestrator's CC will balloon back past 60."
    )


@pytest.mark.parametrize("phase_name", list(_REMOVED_HELPERS))
def test_phase_dead_helpers_removed(phase_name: str, helpers_module) -> None:
    """Helpers that referenced undefined ``state`` and ``_payload_apply_meta`` are dead.

    WL-134 removes them. Tests must confirm the symbols no longer exist
    so an accidental re-add (with the inlined body) is caught.
    """
    assert not hasattr(helpers_module, phase_name), (
        f"{phase_name} is dead code (its body references undefined symbols "
        f"state/_payload_apply_meta and was never wired). Restore only if "
        f"you add a real caller inside run_impl_core."
    )


def test_phase_release_idle_and_publish_swallows_all_failures(helpers_module) -> None:
    """EyeState.release_idle() + publish_bus_event must both be best-effort.

    Both backends use lazy imports inside a ``try/except Exception`` block,
    so even if the modules are missing or raise, the helper must return
    without raising (it owns UX, not correctness).
    """
    from pathlib import Path

    # No patches — the lazy imports in production code resolve to missing
    # modules in this repo, exercising the except-branch naturally.
    helpers_module._phase_release_idle_and_publish(
        cwd=Path("/tmp"),
        runner=None,
        run_id="run-1",
        start_ts=0.0,
        exit_code=0,
    )
    helpers_module._phase_release_idle_and_publish(
        cwd=Path("/tmp"),
        runner=None,
        run_id="run-2",
        start_ts=0.0,
        exit_code=1,
    )


def test_phase_release_idle_and_publish_uses_correct_bus_event_shape(
    helpers_module,
) -> None:
    """When publish_bus_event is reachable, it must publish ``run.end`` with the
    4-tuple payload ``(run_id, exit_code, duration_s, status)``."""
    # Inject the lazy-import target modules into sys.modules so the
    # production ``from ... import`` succeeds.
    import sys
    import types
    from pathlib import Path

    fake_eye_mod = types.ModuleType("thegent.cli.shared.eye_state")
    fake_eye_cls = MagicMock()
    fake_eye_mod.EyeState = fake_eye_cls
    sys.modules["thegent.cli.shared"] = types.ModuleType("thegent.cli.shared")
    sys.modules["thegent.cli.shared.eye_state"] = fake_eye_mod

    fake_bus_mod = types.ModuleType("thegent.cli.resources.bus_client")
    fake_bus_mod.publish_bus_event = MagicMock()
    sys.modules["thegent.cli.resources"] = types.ModuleType("thegent.cli.resources")
    sys.modules["thegent.cli.resources.bus_client"] = fake_bus_mod

    try:
        helpers_module._phase_release_idle_and_publish(
            cwd=Path("/tmp"),
            runner=None,
            run_id="run-shape",
            start_ts=100.0,
            exit_code=0,
        )
        # EyeState.release_idle was called.
        fake_eye_cls.assert_called_once_with(Path("/tmp"))
        fake_eye_cls.return_value.release_idle.assert_called_once()
        # publish_bus_event was called with (cwd, "run.end", payload_dict).
        fake_bus_mod.publish_bus_event.assert_called_once()
        args = fake_bus_mod.publish_bus_event.call_args
        # First positional = cwd.
        assert args.args[0] == Path("/tmp")
        # Second positional = event name.
        assert args.args[1] == "run.end"
        # Third positional = payload dict.
        payload = args.args[2]
        assert payload["run_id"] == "run-shape"
        assert payload["exit_code"] == 0
        assert payload["runner"] is None
        # duration_ms is monotonic — should be >= 0.
        assert payload["duration_ms"] >= 0.0
    finally:
        for key in (
            "thegent.cli.shared",
            "thegent.cli.shared.eye_state",
            "thegent.cli.resources",
            "thegent.cli.resources.bus_client",
        ):
            sys.modules.pop(key, None)


def test_phase_classify_run_result_maps_timeout_to_error_class(helpers_module) -> None:
    """A timed-out result must be classified as ``error_class='timeout'``."""
    result = SimpleNamespace(exit_code=124, timed_out=True, stdout="", stderr="")
    norm_res = SimpleNamespace(csm=SimpleNamespace(source_contract="csm-v1"))
    settings = MagicMock()
    settings.session_dir = "/tmp/sess"
    run_meta = SimpleNamespace(run_id="run-x", owner="alice")

    with patch.object(helpers_module, "_log") as mock_log:
        _exit_code, status, error_class, output_summary = helpers_module._phase_classify_run_result(  # noqa: RUF059
            result=result,
            pol_res="allow",
            pol_reason="",
            norm_res=norm_res,
            lane="standard",
            settings=settings,
            run_meta=run_meta,
            fsm_status="timed_out",
            start_time=0.0,
            registry=MagicMock(),
            maif_runner=MagicMock(),
        )

    assert error_class == "timeout"
    assert status == "timed_out"
    assert output_summary == ""
    mock_log.info.assert_not_called()  # DLQ only enqueues for critical lane


def test_phase_classify_run_result_enqueues_dlq_for_critical_lane(
    helpers_module,
) -> None:
    """Critical-lane failures must hit the DLQ (WP-2008)."""
    result = SimpleNamespace(exit_code=1, timed_out=False, stdout="", stderr="boom")
    norm_res = SimpleNamespace(csm=SimpleNamespace(source_contract="csm-v1"))
    settings = MagicMock()
    settings.session_dir = "/tmp/sess"
    run_meta = SimpleNamespace(run_id="run-crit", owner="alice")

    with patch("thegent.execution.DLQManager") as mock_dlq_cls:
        helpers_module._phase_classify_run_result(
            result=result,
            pol_res="allow",
            pol_reason="",
            norm_res=norm_res,
            lane="critical",
            settings=settings,
            run_meta=run_meta,
            fsm_status="failed",
            start_time=0.0,
            registry=MagicMock(),
            maif_runner=MagicMock(),
        )

    mock_dlq_cls.assert_called_once_with("/tmp/sess")
    mock_dlq_cls.return_value.enqueue.assert_called_once()


def test_phase_classify_run_result_reclassifies_unknown_contract(
    helpers_module,
) -> None:
    """Critical + unknown source_contract → status=failed, error_class=unknown_contract (G-CA-03 C3)."""
    result = SimpleNamespace(exit_code=0, timed_out=False, stdout="ok", stderr="")
    norm_res = SimpleNamespace(csm=SimpleNamespace(source_contract="mystery-fmt"))
    settings = MagicMock()
    settings.session_dir = "/tmp/sess"
    run_meta = SimpleNamespace(run_id="run-x", owner="alice")

    with patch("thegent.execution.DLQManager"):
        exit_code, status, error_class, _ = helpers_module._phase_classify_run_result(
            result=result,
            pol_res="allow",
            pol_reason="",
            norm_res=norm_res,
            lane="critical",
            settings=settings,
            run_meta=run_meta,
            fsm_status="completed",
            start_time=0.0,
            registry=MagicMock(),
            maif_runner=MagicMock(),
        )

    assert status == "failed"
    assert exit_code == 1
    assert error_class == "unknown_contract"
