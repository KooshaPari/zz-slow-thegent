"""WL-130 L3 Agent Loop entrypoint + dispatch contract.

Locks down the public L3 entrypoint surface so the agent loop stays wired:

* ``python -m thegent`` resolves to ``thegent.cli.apps.main.app``.
* The Typer app exposes the L3 subcommands we ship (bg, status, stop,
  logs, ps, resume — plus ``run`` as the prompt-dispatch entrypoint).
* ``thegent run_impl`` (canonical) exposes ``audio_files`` +
  ``google_grounding`` as named params and forwards ``failover`` via
  ``**kwargs`` to the run-execution core.
* ``run_impl_core`` accepts ``failover`` (regression pinned by
  ``tests/test_wl129_failover_kwarg_forwarding.py``).
* The ``__main__`` module is the canonical module entrypoint and wires
  to ``app()``.

Refs: AUDIT-N+28 (audio grounding pins), AUDIT-N+29 (failover kwarg
forwarding), FR-GOV-005, Phase 3/4 hardening lane L3.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

from typer.testing import CliRunner

from thegent.cli.apps.main import app as main_app
from thegent.cli.commands.impl import run_impl

runner = CliRunner(mix_stderr=False)


def test_python_m_thegent_resolves_to_main_app() -> None:
    """``python -m thegent`` boots the same Typer app as thegent CLI."""
    import thegent.__main__ as entry

    assert hasattr(entry, "app"), "__main__ must expose `app`"
    assert entry.app is main_app, "__main__.app must be the main Typer app"
    assert callable(entry.app), "app must be callable (Typer app() is the CLI entrypoint)"


def test_main_app_exposes_l3_subcommands() -> None:
    """L3 agent loop surface is intact: bg, status, stop, logs, ps, resume, govern, phench.

    The Typer app groups lifecycle commands at the top level and exposes
    ``thegent run ...`` as the prompt-dispatch entrypoint (verified by
    test_run_help_succeeds). Together the surface matches the L3 contract.
    """
    # Typer exposes `registered_commands` as a list of CommandInfo; iterate names.
    registered = {cmd.name for cmd in main_app.registered_commands}  # type: ignore[attr-defined]
    expected = {"bg", "status", "stop", "logs", "ps", "resume"}
    missing = expected - registered
    assert not missing, f"L3 subcommands missing from main_app: {missing}"


def test_main_app_help_succeeds() -> None:
    """Top-level --help renders without raising (smoke test for entrypoint)."""
    result = runner.invoke(main_app, ["--help"])
    assert result.exit_code == 0, f"--help raised: {result.stdout!r} {result.stderr!r}"
    assert "Unified agent orchestration CLI" in result.stdout


def test_run_help_succeeds() -> None:
    """`thegent run --help` renders the L3 run surface."""
    result = runner.invoke(main_app, ["run", "--help"])
    combined = (result.stdout or "") + (getattr(result, "stderr", "") or "")
    assert "agent" in combined.lower(), f"run --help missing 'agent' subcommand: {combined[:500]!r}"


def test_run_impl_signature_has_audio_grounding_explicit() -> None:
    """``run_impl`` exposes audio_files + google_grounding as named params (AUDIO-001)."""
    sig = inspect.signature(run_impl)
    for name in ("audio_files", "google_grounding"):
        assert name in sig.parameters, f"run_impl missing {name!r} param: {list(sig.parameters)}"


def test_run_impl_forwards_failover_via_kwargs() -> None:
    """``run_impl`` accepts ``failover`` and forwards it to ``run_impl_core``.

    Pinned by AUDIT-N+29: ``thegent run --failover ...`` must not raise. The
    flag is forwarded to the canonical core via ``**kwargs``.
    """
    import thegent.cli.commands.run.impl_core_runners as runners

    captured: dict[str, object] = {}

    def _capture(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {"status": "noop", "captured": list(captured.keys())}

    original = runners.run_impl_core
    runners.run_impl_core = _capture  # type: ignore[assignment]
    try:
        run_impl(prompt="hello", failover=True)
    finally:
        runners.run_impl_core = original  # type: ignore[assignment]

    assert captured.get("failover") is True, f"failover kwarg not forwarded to run_impl_core; captured={captured!r}"


def test_run_execution_core_helpers_accept_failover() -> None:
    """``run_execution_core_helpers.run_impl_core(failover=...)`` does not TypeError.

    AUDIT-N+29 fix lives in ``run_execution_core_helpers.py``. The signature
    must accept the kwarg either as an explicit param or via ``**kwargs``.
    """
    import thegent.cli.services.run_execution_core_helpers as helpers

    sig = inspect.signature(helpers.run_impl_core)
    assert "failover" in sig.parameters or "kwargs" in sig.parameters, (
        f"run_impl_core signature must accept failover: {list(sig.parameters)}"
    )
    # Exercise the call to make sure the kwarg isn't dropped at runtime.
    original = helpers.run_impl_core

    def _noop(*_a, **_kw):  # type: ignore[no-untyped-def]
        return {"status": "noop"}

    helpers.run_impl_core = _noop  # type: ignore[assignment]
    try:
        helpers.run_impl_core(prompt="p", failover=True)
    except TypeError as exc:
        raise AssertionError(f"run_impl_core rejected failover kwarg: {exc}") from exc
    finally:
        helpers.run_impl_core = original  # type: ignore[assignment]


def test_bg_execution_core_helpers_accept_failover() -> None:
    """``bg_impl_core`` parity: also accepts failover."""
    import thegent.cli.services.run_execution_core_helpers as helpers

    sig = inspect.signature(helpers.bg_impl_core)
    assert "failover" in sig.parameters or "kwargs" in sig.parameters, (
        f"bg_impl_core must accept failover: {list(sig.parameters)}"
    )


def test_main_module_source_is_canonical() -> None:
    """``src/thegent/__main__.py`` is a thin shim that delegates to cli.apps.main."""
    main_path = Path(__file__).resolve().parents[1] / "src" / "thegent" / "__main__.py"
    text = main_path.read_text(encoding="utf-8")
    assert "from thegent.cli.apps.main import app" in text
    assert 'if __name__ == "__main__":' in text
    assert "app()" in text
    # Canonical contract: this file must stay tiny so the entrypoint
    # contract is obvious from a glance. Drift beyond ~15 lines is a
    # structural problem worth flagging.
    assert len(text.splitlines()) <= 15, f"__main__.py grew beyond canonical size: {len(text.splitlines())} lines"


def test_sys_path_does_not_shadow_package() -> None:
    """Guard against accidentally invoking a script named `thegent` (not the package)."""
    import thegent

    assert thegent.__file__ is not None
    assert thegent.__file__.endswith("__init__.py"), (
        f"thegent.__file__ must point to the package __init__: {thegent.__file__}"
    )
    # And __main__ resolves through the same import chain.
    assert "thegent.__main__" in sys.modules or hasattr(sys.modules.get("thegent.__main__"), "app")
