"""Implementation core runners for the ``run`` command package.

Extracted from ``src/thegent/cli/services/run_execution_core_helpers.py`` so
that the pareto-routing path lives next to its siblings. The thin proxy
``_apply_pareto_routing`` is the only symbol currently consumed by the
``run_execution_core_helpers`` shim (line 114), and the stub preserves the
canonical 6-tuple return contract while deferring to ``thegent.cli.commands.impl``
so the patched name resolves correctly under
``@patch("thegent.cli.commands.impl._apply_pareto_routing")`` test decorators.
"""

from __future__ import annotations

from typing import Any


def _apply_pareto_routing(
    agent: str | None,
    model: str | None,
    routing: str | None,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
) -> tuple[str | None, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Apply pareto-routing selection to ``(agent, model)``.

    Returns the canonical 4-tuple ``(agent, model, route_contract, route_request)``
    unchanged when ``routing != "pareto"``. The pareto-router path is
    intentionally deferred to the test surface: when
    ``thegent.cli.commands.impl._apply_pareto_routing`` is patched, the
    proxy yields first.
    """
    if routing != "pareto":
        return agent, model, route_contract, route_request
    # Defer to the canonical impl-side helper (patchable by the test
    # surface) when routing="pareto" is requested.
    try:
        from thegent.cli.commands.impl import (
            _apply_pareto_routing as _impl_apply,  # noqa: PLC0415
        )
    except ImportError:
        return agent, model, route_contract, route_request
    return _impl_apply(agent, model, routing, include_contract, route_contract, route_request)


__all__ = ["_apply_pareto_routing"]
