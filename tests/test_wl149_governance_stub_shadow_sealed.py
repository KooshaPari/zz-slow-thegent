"""WL-149 regression: governance stub shadow surface must be sealed.

When the WL-124 monolith split landed, ``thegent.cli.commands.governance_cmds``
was left as a stub-only module. Production imports in ``thegent.cli.__init__``
were also re-routed through that stub module — meaning the canonical
governance implementations in
``thegent.cli.governance.governance_escalation_hitl_cmds`` and
``thegent.cli.governance.governance_policy_contracts_cmds`` were **shadowed**
by zero-returning stubs.

This regression test pins the resolved module for every governance command
that was historically stub-shadowed so that a future "consolidate the
governance wrappers" PR cannot re-introduce the shadow without a test
failure.

Functions pinned (the WL-149 set):

* ``drift_cmd``            — canonical: ``thegent.cli.governance.governance_policy_contracts_cmds``
* ``escalate_add_cmd``     — canonical: ``thegent.cli.governance.governance_escalation_hitl_cmds``
* ``escalate_list_cmd``    — canonical: ``thegent.cli.governance.governance_escalation_hitl_cmds``
* ``escalate_resolve_cmd`` — canonical: ``thegent.cli.governance.governance_escalation_hitl_cmds``
* ``migration_cmd``        — canonical: ``thegent.cli.governance.governance_policy_contracts_cmds``
* ``policy_show_cmd``      — canonical: ``thegent.cli.governance.governance_policy_contracts_cmds``
* ``sweep_cmd``            — canonical: ``thegent.cli.governance.governance_escalation_hitl_cmds``

Stub module that must NEVER be the source for these names:

* ``thegent.cli.commands.governance_cmds`` (the WL-124 stub-only monolith)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Canonical resolution pin — the seven shadowed functions.
# ---------------------------------------------------------------------------

CANONICAL_SOURCES: dict[str, str] = {
    "drift_cmd": "thegent.cli.governance.governance_policy_contracts_cmds",
    "escalate_add_cmd": "thegent.cli.governance.governance_escalation_hitl_cmds",
    "escalate_list_cmd": "thegent.cli.governance.governance_escalation_hitl_cmds",
    "escalate_resolve_cmd": "thegent.cli.governance.governance_escalation_hitl_cmds",
    "migration_cmd": "thegent.cli.governance.governance_policy_contracts_cmds",
    "policy_show_cmd": "thegent.cli.governance.governance_policy_contracts_cmds",
    "sweep_cmd": "thegent.cli.governance.governance_escalation_hitl_cmds",
}

STUB_MODULE = "thegent.cli.commands.governance_cmds"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolved_module(name: str) -> str:
    """Return ``__module__`` for the named attribute on ``thegent.cli``."""
    from thegent import cli

    attr = getattr(cli, name)
    return getattr(attr, "__module__", "<unknown>")


# ---------------------------------------------------------------------------
# Section 1 — every shadowed function resolves to its canonical module.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("func_name", "canonical_module"),
    list(CANONICAL_SOURCES.items()),
)
def test_shadowed_governance_cmd_resolves_to_canonical(
    func_name: str, canonical_module: str
) -> None:
    """``from thegent.cli import <func>`` must resolve to the canonical
    governance module, not the WL-124 stub monolith.

    The canonical module is the one that contains the real implementation
    (real ``console`` calls, real ``*_impl`` dispatch, real arg-binding).
    The stub module only contains zero-returning placeholders.
    """
    resolved = _resolved_module(func_name)
    assert resolved == canonical_module, (
        f"thegent.cli.{func_name} resolves to {resolved!r}; "
        f"expected canonical {canonical_module!r}. "
        f"The WL-124 stub in {STUB_MODULE!r} is shadowing the real implementation."
    )


# ---------------------------------------------------------------------------
# Section 2 — the stub module is a stub (defensive pin).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "func_name",
    list(CANONICAL_SOURCES.keys()),
)
def test_stub_module_only_contains_zero_returning_stubs(func_name: str) -> None:
    """If anyone ever re-imports from the stub module, the function must
    still be a zero-returning stub (i.e. the stub module itself is safe).

    This pins the safety net: if the stub module is ever readded into the
    ``thegent.cli`` re-export chain, the shadows must be zero-returning
    so they don't silently swallow real CLI invocations.
    """
    import importlib

    stub = importlib.import_module(STUB_MODULE)
    stub_fn = getattr(stub, func_name, None)
    if stub_fn is None:
        pytest.skip(
            f"{STUB_MODULE} no longer exposes {func_name} (stub namespace shrunk)"
        )
    # The stub should accept any args and return 0/None — exercise the
    # contract with a sentinel call.
    result = stub_fn("r1", "blocked", sla_minutes=15)
    assert result in (0, None), (
        f"{STUB_MODULE}.{func_name} returned {result!r}; "
        f"WL-124 stubs must be zero-returning so they can't shadow real "
        f"implementations with side effects."
    )


# ---------------------------------------------------------------------------
# Section 3 — the canonical module exposes the real implementation.
#
# Some canonical commands delegate to a ``*_impl`` symbol on
# ``thegent.cli.governance.governance_impl`` (the WL-124 thin-wrapper
# pattern). Others ARE the implementation (the policy/contracts module
# bodies encode the controller calls directly). The list below tracks
# which canonical commands dispatch to ``*_impl`` and what the dispatch
# source symbol is in ``governance_impl``.
# ---------------------------------------------------------------------------

# Map: (func_name, canonical_module) -> source symbol on governance_impl.
# Commands not in this map are direct implementations (no ``*_impl``
# delegation) — they only need to be present and callable on the
# canonical module.
IMPL_DISPATCH: dict[tuple[str, str], str] = {
    (
        "escalate_add_cmd",
        "thegent.cli.governance.governance_escalation_hitl_cmds",
    ): "escalate_add_impl",
    (
        "escalate_list_cmd",
        "thegent.cli.governance.governance_escalation_hitl_cmds",
    ): "escalate_list_impl",
    (
        "escalate_resolve_cmd",
        "thegent.cli.governance.governance_escalation_hitl_cmds",
    ): "escalate_resolve_impl",
    (
        "sweep_cmd",
        "thegent.cli.governance.governance_escalation_hitl_cmds",
    ): "sweep_impl",
}


@pytest.mark.parametrize(
    ("func_name", "canonical_module"),
    list(CANONICAL_SOURCES.items()),
)
def test_canonical_module_owns_real_implementation(
    func_name: str, canonical_module: str
) -> None:
    """The canonical module must expose the named command. If the
    command is a delegation wrapper, the body must dispatch to a real
    ``*_impl`` symbol from ``thegent.cli.governance.governance_impl``
    (and that symbol must exist). If the command is a direct
    implementation, only the presence + callability check applies.
    """
    import importlib
    import inspect

    canon = importlib.import_module(canonical_module)
    assert hasattr(canon, func_name), (
        f"{canonical_module} no longer exposes {func_name}"
    )
    assert callable(getattr(canon, func_name))

    dispatch_target = IMPL_DISPATCH.get((func_name, canonical_module))
    if dispatch_target is None:
        # Direct implementation — nothing more to check.
        return

    # Delegation wrapper: body must dispatch to ``*_impl`` and the
    # symbol must exist on ``governance_impl``.
    src = getattr(canon, func_name)
    try:
        source = inspect.getsource(src)
    except (OSError, TypeError) as exc:  # pragma: no cover — defensive
        pytest.fail(f"could not read source for {canonical_module}.{func_name}: {exc}")
    assert dispatch_target in source, (
        f"{canonical_module}.{func_name} body does not dispatch to "
        f"{dispatch_target!r} — the wrapper has been stubbed-over since "
        f"the WL-149 seal."
    )
    impl_mod = importlib.import_module("thegent.cli.governance.governance_impl")
    assert hasattr(impl_mod, dispatch_target), (
        f"thegent.cli.governance.governance_impl no longer exposes the dispatch "
        f"target {dispatch_target!r} for {canonical_module}.{func_name}"
    )
    assert callable(getattr(impl_mod, dispatch_target))


# ---------------------------------------------------------------------------
# Section 4 — ``thegent.cli.governance.governance_impl`` re-exports the
#              production impl symbols so the canonical wrappers can dispatch.
# ---------------------------------------------------------------------------

# Only the symbols actually delegated to are pinned here. The
# policy/contracts commands (policy_show/drift/migration) do NOT have
# ``*_impl`` siblings — they are direct implementations.
_REAL_IMPL_SYMBOLS = [
    "escalate_add_impl",
    "escalate_list_impl",
    "escalate_resolve_impl",
    "sweep_impl",
]


@pytest.mark.parametrize("impl_name", _REAL_IMPL_SYMBOLS)
def test_governance_impl_module_exposes_real_impl(impl_name: str) -> None:
    """Every ``*_impl`` symbol the canonical wrappers dispatch to must
    still exist on ``thegent.cli.governance.governance_impl``.
    """
    import importlib

    impl_mod = importlib.import_module("thegent.cli.governance.governance_impl")
    assert hasattr(impl_mod, impl_name), (
        f"thegent.cli.governance.governance_impl no longer exposes {impl_name}"
    )
    assert callable(getattr(impl_mod, impl_name))
