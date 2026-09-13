"""Regression test for AUDIT-N+29: `failover` kwarg forwarding on the foreground run path.

The CLI surface (``thegent run --failover ...``) threads ``failover=...`` into
``cli.run_cmd`` -> ``run_impl`` -> ``run_impl_core`` -> the underlying
``thegent.cli.services.run_execution_core_helpers.run_impl_core``.  Before the
fix the underlying helper's signature omitted ``failover`` and raised
``TypeError: run_impl_core() got an unexpected keyword argument 'failover'``.

This module pins the contract on both ends:

1. ``run_impl_core`` accepts ``failover`` (signature check).
2. ``run_impl`` forwards ``failover`` (kwarg forwarding contract).
3. ``run_impl_core`` (canonical shim in ``impl_core_runners``) also accepts
   ``failover`` (it forwards ``**kwargs`` verbatim).

The actual executable run-path is exercised separately by the full
``thegent run`` integration; here we focus on the parameter contract so the
regression is caught at unit-test granularity.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest


def _get_run_impl_core() -> Any:
    from thegent.cli.services.run_execution_core_helpers import run_impl_core

    return run_impl_core


def test_run_impl_core_accepts_failover_kwarg() -> None:
    """The underlying helper must accept ``failover``."""
    run_impl_core = _get_run_impl_core()
    sig = inspect.signature(run_impl_core)
    assert "failover" in sig.parameters, (
        "run_execution_core_helpers.run_impl_core must accept `failover` for CLI parity (AUDIT-N+29)"
    )
    param = sig.parameters["failover"]
    assert param.default is False, "failover default must be False"


def test_run_impl_forwards_failover_kwarg() -> None:
    """``run_impl`` must accept **kwargs and forward verbatim."""
    from thegent.cli.commands.impl import run_impl

    sig = inspect.signature(run_impl)
    assert "failover" in sig.parameters or any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    ), (
        "run_impl must accept `failover` either explicitly or via **kwargs "
        "so the CLI --failover flag reaches the underlying helper "
        "(AUDIT-N+29)"
    )


def test_canonical_shim_accepts_failover_kwarg() -> None:
    """The canonical shim ``run_impl_core`` forwards **kwargs verbatim."""
    from thegent.cli.commands.run.impl_core_runners import run_impl_core as shim

    sig = inspect.signature(shim)
    assert any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()), (
        "canonical run_impl_core shim must accept **kwargs to forward failover"
    )


def test_bg_impl_core_accepts_failover_kwarg() -> None:
    """``bg_impl_core`` has accepted ``failover`` since before AUDIT-N+29; pin it."""
    from thegent.cli.services.run_execution_core_helpers import bg_impl_core

    sig = inspect.signature(bg_impl_core)
    assert "failover" in sig.parameters


@pytest.mark.parametrize(
    "target_path",
    [
        "thegent.cli.services.run_execution_core_helpers.run_impl_core",
        "thegent.cli.commands.run.impl_core_runners.run_impl_core",
    ],
)
def test_run_impl_core_callable_with_failover(target_path: str) -> None:
    """Smoke-test that ``failover=True`` doesn't blow up at signature level."""
    import importlib

    module_path, attr = target_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    fn = getattr(module, attr)
    sig = inspect.signature(fn)
    assert "failover" in sig.parameters or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
