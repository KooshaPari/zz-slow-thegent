"""Canonical home for the ``run`` / ``bg`` impl-core dispatch shims.

This module exposes the AUDIT-N+16 canonical-home extraction for the
``run_impl`` / ``bg_impl`` entry points in
:mod:`thegent.cli.commands.impl`. The thin shims here:

1. Resolve the ``impl`` namespace (``thegent.cli.commands.impl``) so that
   the AUDIT-N+2 envelope-parity contract (which binds ``impl``'s
   globals into the helper module via ``_bind_impl_namespace``) closes.
2. Forward every caller kwarg verbatim to the real implementations in
   :mod:`thegent.cli.services.run_execution_core_helpers` (the
   ``run_impl_core`` / ``bg_impl_core`` functions there own the full
   execution pipeline: Pareto routing, policy, escalation, MAIF,
   observability).

The shims preserve the EXACT argument-passthrough contract pinned by
``tests/test_wl125_run_execution_core_helpers_parity.py`` and the
AUDIT-N+6 wrapper-delegation parity tests:

- ``prompt`` is forwarded as a keyword argument.
- Every caller kwarg (``agent``, ``model``, ``routing``, ``include_contract``,
  ``route_contract``, ``route_request``, ``image_paths``, ``audio_files``,
  ``google_grounding``, ``task_id``, ``lock``, ``remote``, ``debug``,
  ``shadow``, ``idempotency_token``, ``speculative``, ``continue_from``,
  ``continuation_include_stderr``, ``failover``, etc.) is forwarded
  verbatim.
- The ``impl_ns`` keyword is threaded into the helper-module call so the
  helper module's ``_bind_impl_namespace(impl_ns)`` can rebind the
  ``impl.<x>`` references the helpers depend on (e.g.
  ``_spawn_with_eagain_retry``, ``resolve_agent``, ``subprocess``,
  ``ThegentSettings``).

The lazy import of ``run_execution_core_helpers`` inside each function
body preserves import-order safety: ``impl.py`` is loaded before the
helper module during cold-start, and the helper module imports back
from ``impl.py`` at module-top via ``_LazyImpl``. Doing the import
inline (the same pattern as the prior wrappers) avoids any new
top-level cycle.

The ``_apply_pareto_routing`` re-export shim is retained as the
canonical home for the pareto-routing helper consumed at
``run_execution_core_helpers.py:125`` (the
``_apply_pareto_routing_local`` wrapper there delegates here).
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

from thegent.cli.commands.run import _apply_pareto_routing as _impl_apply


def _apply_pareto_routing(
    agent: str | None,
    model: str | None,
    routing: str | None,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
) -> tuple[str | None, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    return _impl_apply(agent, model, routing, include_contract, route_contract, route_request)


def _resolve_impl_namespace() -> Any:
    """Return the canonical ``thegent.cli.commands.impl`` module object.

    Prefers ``sys.modules`` lookup (fast path — the module is always
    present when ``run_impl`` / ``bg_impl`` are called from the CLI),
    falling back to an explicit ``importlib.import_module`` for cold
    edge cases (test harnesses that pop the entry from ``sys.modules``
    then re-import).
    """
    impl_ns = sys.modules.get("thegent.cli.commands.impl")
    if impl_ns is None:  # pragma: no cover - defensive cold path
        impl_ns = importlib.import_module("thegent.cli.commands.impl")
    return impl_ns


def run_impl_core(prompt: str, **kwargs: Any) -> dict[str, Any]:
    """Canonical ``run_impl_core`` dispatch shim.

    Resolves the ``impl`` namespace and forwards ``prompt`` (keyword)
    plus every caller kwarg verbatim to
    :func:`thegent.cli.services.run_execution_core_helpers.run_impl_core`.

    The lazy import of the helper module inside the function body keeps
    ``impl_core_runners.py`` import-order safe: ``run_execution_core_helpers``
    imports back from ``impl.py`` at module-top via ``_LazyImpl``, and
    itself imports ``thegent.cli.commands.run.impl_core_runners`` for the
    pareto-routing helper. Top-level imports here would close that cycle.
    """
    from thegent.cli.services import run_execution_core_helpers

    impl_ns = _resolve_impl_namespace()
    return run_execution_core_helpers.run_impl_core(prompt=prompt, impl_ns=impl_ns, **kwargs)


def bg_impl_core(prompt: str, **kwargs: Any) -> dict[str, Any]:
    """Canonical ``bg_impl_core`` dispatch shim.

    Mirrors :func:`run_impl_core`'s delegation contract so operators
    and tests can stub the core helper via ``monkeypatch.setattr`` on
    ``thegent.cli.services.run_execution_core_helpers``.
    """
    from thegent.cli.services import run_execution_core_helpers

    impl_ns = _resolve_impl_namespace()
    return run_execution_core_helpers.bg_impl_core(prompt=prompt, impl_ns=impl_ns, **kwargs)


__all__ = ["_apply_pareto_routing", "run_impl_core", "bg_impl_core"]
