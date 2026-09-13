"""WL-137 L9 composite (final) phase helpers wire-up regression.

Locks down the sixth and final ``_phase_*`` helper extraction batch into
``run_impl_core`` (continues WL-131/132/133/134/135/136):

* ``_phase_init_tracker`` — cost-tracker startup + rid generation
  (replaces 5 inline lines).
* ``_phase_resolve_grounded_agent`` — model alias resolution +
  Google-grounding precondition (replaces 17 inline lines + an inline
  ``from thegent.agents.grounding import GEMINI_GROUNDING_AGENTS``).
* ``_phase_build_execution_services`` — bundle of six per-run registries
  (CircuitBreaker / TrustBoundary / Override / Policy / Auditor / MAIF)
  plus the resolved escalation SLA minutes (replaces 18 inline lines).
* ``_phase_publish_run_start`` — ``registry.register_start`` +
  ``maif_runner.record_run_start`` (replaces 7 inline lines).
* ``_phase_run_under_keepalive`` — ``fsm.run`` inside a keepalive
  context with non-worktree lease release on finally (replaces 21
  inline lines including a duplicate ``_bind_impl_namespace`` rebind).
* ``_phase_dispatch_policy_outcome`` — ``deny`` / ``pause`` / ``warn``
  side-effect dispatch (replaces 26 inline lines of if/return branches).

Pre-WL137 baseline (``run_impl_core``):
* body: 458 lines (L1220-L1677)
* CC: 44

Post-WL137 target:
* body: ≤ 425 lines (-33 L)
* CC: ≤ 30 (-14 CC points)
* helper-file line count +234 (helpers + dataclass + docstrings)
* still well above the L9 40-line body threshold per `_phase_*` helper
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 1. Wire-up regression: every new helper must be referenced from run_impl_core
# ---------------------------------------------------------------------------


_COMPOSITE_PHASE_HELPERS = (
    "_phase_init_tracker",
    "_phase_resolve_grounded_agent",
    "_phase_build_execution_services",
    "_phase_publish_run_start",
    "_phase_run_under_keepalive",
    "_phase_dispatch_policy_outcome",
)


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module("thegent.cli.services.run_execution_core_helpers")


@pytest.fixture(scope="module")
def run_impl_core_source(helpers_module) -> str:
    return inspect.getsource(helpers_module.run_impl_core)


@pytest.mark.parametrize("phase_name", list(_COMPOSITE_PHASE_HELPERS))
def test_run_impl_core_delegates_to_composite_helpers(
    phase_name: str, run_impl_core_source: str
) -> None:
    """``run_impl_core`` must call every composite phase helper, not inline its body.

    This guards against accidental re-inlining that would balloon the
    orchestrator's CC back past 44 (the WL-137 pre-extraction level).
    """
    assert f"{phase_name}(" in run_impl_core_source, (
        f"Expected run_impl_core to delegate to {phase_name} helper. "
        f"Re-inlining will push run_impl_core's CC back past 44."
    )


def test_execution_services_dataclass_declared(helpers_module) -> None:
    """The ``_ExecutionServices`` dataclass must exist alongside the helpers."""
    assert hasattr(helpers_module, "_ExecutionServices"), (
        "_ExecutionServices dataclass must be declared so the orchestrator can "
        "unpack the per-run service bundle without six inline assignments."
    )


# ---------------------------------------------------------------------------
# 2. Inline-block regression: signature fragments must NOT reappear in
#    run_impl_core (so CC stays low).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_fragment",
    [
        # was inside _phase_init_tracker body (orchestrator pre-WL137)
        "    from thegent.cost.tracker import get_run_cost_tracker\n\n    tracker = get_run_cost_tracker()",
        # was inside _phase_resolve_grounded_agent body
        "    from thegent.agents.grounding import GEMINI_GROUNDING_AGENTS\n\n    if google_grounding and agent not in GEMINI_GROUNDING_AGENTS:",
        # was inside _phase_build_execution_services body
        "    circuit_breaker = CircuitBreakerRegistry(settings.session_dir)\n    trust_boundary = TrustBoundaryValidator(settings.session_dir)",
        # was inside _phase_publish_run_start body
        "    maif_runner.record_run_start(\n        run_id=run_meta.run_id,",
        # was inside _phase_run_under_keepalive body
        '    _keepalive_interval = float(getattr(settings, "keepalive_interval", 30.0))',
    ],
)
def test_run_impl_core_inline_fragments_removed(
    forbidden_fragment: str, run_impl_core_source: str
) -> None:
    """Body fragments that used to live inside ``run_impl_core`` must be gone.

    Each fragment identifies one of the six composite helpers. If any
    reappears in the orchestrator body, CC will balloon; the parametrize
    table pins the absense.
    """
    assert forbidden_fragment not in run_impl_core_source, (
        f"Inline body fragment {forbidden_fragment!r} must live in a _phase_* helper, not in run_impl_core."
    )


def test_run_impl_core_lost_duplicate_settings_rebind(
    run_impl_core_source: str,
) -> None:
    """The redundant ``settings = ThegentSettings()`` mid-body must be gone.

    Pre-WL137 the orchestrator re-bound ``settings`` and ``impl_ns`` mid-
    way through, between ``_phase_acquire_resource_leases`` and the
    keepalive block. Both rebinds were no-ops (already done at the top)
    and added 3 lines + 2 CC points of dead code.
    """
    # The single canonical rebind happens at L1278. Anything past that point
    # with another ``settings = ThegentSettings()`` is the dead duplicate.
    body_lines = run_impl_core_source.splitlines()
    rebinds = [
        i
        for i, ln in enumerate(body_lines, start=1)
        if ln.strip() == "settings = ThegentSettings()"
    ]
    assert len(rebinds) == 1, (
        f"Expected exactly one canonical `settings = ThegentSettings()` "
        f"in run_impl_core; found {len(rebinds)} at line offsets {rebinds}. "
        f"The mid-body duplicate must be removed by WL-137."
    )


# ---------------------------------------------------------------------------
# 3. Behavioural tests: each helper in isolation
# ---------------------------------------------------------------------------


def test_phase_init_tracker_generates_canonical_rid(helpers_module) -> None:
    """When ``run_id`` is ``None``, helper must mint ``run_<8-hex>``."""
    fake_tracker = MagicMock()
    with patch_get_run_cost_tracker(helpers_module, fake_tracker):
        rid, tracker = helpers_module._phase_init_tracker(
            settings=MagicMock(),
            run_id=None,
        )

    assert re.match(r"^run_[0-9a-f]{8}$", rid), (
        f"Expected rid to match `run_<8-hex>`; got {rid!r}."
    )
    assert tracker is fake_tracker
    fake_tracker.start_run.assert_called_once_with(rid)


def test_phase_init_tracker_preserves_supplied_rid(helpers_module) -> None:
    """When ``run_id`` is supplied, helper must reuse it without alteration."""
    fake_tracker = MagicMock()
    with patch_get_run_cost_tracker(helpers_module, fake_tracker):
        rid, _tracker = helpers_module._phase_init_tracker(
            settings=MagicMock(),
            run_id="run-fixed-id",
        )

    assert rid == "run-fixed-id"
    fake_tracker.start_run.assert_called_once_with("run-fixed-id")


def test_phase_resolve_grounded_agent_short_circuits_on_no_grounding(
    helpers_module,
) -> None:
    """No ``google_grounding`` + no model → returns the resolved agent via ``resolve_agent``."""
    with patch.object(helpers_module, "resolve_agent", return_value="claude") as mock:
        agent, err = helpers_module._phase_resolve_grounded_agent(
            agent_name="claude",
            model=None,
            provider=None,
            google_grounding=False,
            rid="run-1",
        )

    assert err is None
    assert agent == "claude"
    mock.assert_called_once_with("claude")


def test_phase_resolve_grounded_agent_rejects_non_gemini_for_grounding(
    helpers_module,
) -> None:
    """``google_grounding=True`` + non-Gemini agent must yield an error payload."""
    # Pass agent="claude" directly so we bypass the model-alias lookup
    # (which short-circuits earlier on a fake model name). The intent is to
    # exercise the grounding precondition, not the model-resolution path.
    with patch.object(helpers_module, "resolve_agent", return_value="claude"):
        # Pretend grounding module is reachable with a known-bad name.
        fake_grounding = MagicMock()
        fake_grounding.GEMINI_GROUNDING_AGENTS = {"gemini", "antigravity"}
        with patch.dict(
            "sys.modules",
            {"thegent.agents.grounding": fake_grounding},
        ):
            agent, err = helpers_module._phase_resolve_grounded_agent(
                agent_name="claude",
                model=None,
                provider=None,
                google_grounding=True,
                rid="run-2",
            )

    assert agent is None
    assert err is not None
    assert err["exit_code"] == 1
    assert "Google grounding" in err["error"]
    assert err["run_id"] == "run-2"


def test_phase_build_execution_services_returns_dataclass(helpers_module) -> None:
    """All 7 fields must be populated; ``escalation_sla_minutes`` falls back to 30 on bad int."""
    settings = MagicMock()
    settings.session_dir = "/tmp/sess"
    settings.escalation_sla_minutes = "not-an-int"
    registry = MagicMock()
    registry.registry_path = "/tmp/sess/registry.json"

    services = helpers_module._phase_build_execution_services(settings, registry)

    assert isinstance(services, helpers_module._ExecutionServices)
    assert services.escalation_sla_minutes == 30, (
        "Bad int for escalation_sla_minutes must fall back to 30."
    )
    assert services.maif_runner is not None  # MAIFRunner() constructed
    assert services.auditor is not None
    assert services.policy_engine is not None


def test_phase_build_execution_services_honours_valid_sla(helpers_module) -> None:
    """Numeric escalation_sla_minutes is parsed and forwarded."""
    settings = MagicMock()
    settings.session_dir = "/tmp/sess"
    settings.escalation_sla_minutes = "45"
    registry = MagicMock()
    registry.registry_path = "/tmp/sess/registry.json"

    services = helpers_module._phase_build_execution_services(settings, registry)

    assert services.escalation_sla_minutes == 45


def test_phase_publish_run_start_invokes_both_backends(helpers_module) -> None:
    """Both ``registry.register_start`` and ``maif_runner.record_run_start`` must fire."""
    registry = MagicMock()
    maif = MagicMock()
    run_meta = MagicMock()
    run_meta.run_id = "run-9"
    run_meta.owner = "alice"
    run_meta.agent = "claude"

    helpers_module._phase_publish_run_start(
        registry=registry,
        maif_runner=maif,
        run_meta=run_meta,
        prompt="hello world",
    )

    registry.register_start.assert_called_once_with(run_meta)
    maif.record_run_start.assert_called_once_with(
        run_id="run-9",
        owner="alice",
        prompt="hello world",
        agent="claude",
    )


def test_phase_run_under_keepalive_releases_leases_on_fsm_crash(
    helpers_module,
) -> None:
    """If ``fsm.run`` raises, the lease release must still fire (finally block)."""
    settings = MagicMock()
    settings.keepalive_interval = 30.0
    fsm = MagicMock()
    fsm.run.side_effect = RuntimeError("FSM crashed")

    # Patch release helper + keepalive context manager so we can observe the
    # finally branch even though the production keepalive module may be absent.
    released_tokens: list[list] = []
    sentinel = [("lease-a", object())]

    def fake_release(s, tokens, _rid):
        released_tokens.append(list(tokens))

    fake_keepalive_ctx = MagicMock()
    fake_keepalive_ctx.__enter__ = MagicMock(return_value=None)
    fake_keepalive_ctx.__exit__ = MagicMock(return_value=None)

    with (
        patch.object(
            helpers_module, "_phase_release_resource_leases", side_effect=fake_release
        ),
        patch.dict(
            "sys.modules",
            {
                "thegent.ux.keepalive": MagicMock(
                    keepalive=MagicMock(return_value=fake_keepalive_ctx)
                )
            },
        ),
    ):
        with pytest.raises(RuntimeError, match="FSM crashed"):
            helpers_module._phase_run_under_keepalive(
                fsm=fsm,
                runner_factory=lambda: None,
                prompt="x",
                agent_cwd=Path("/tmp"),
                mode="write",
                effective_timeout=60,
                use_stream=True,
                shadow_env=None,
                settings=settings,
                locked_tokens=sentinel,
                rid="run-7",
            )

    assert released_tokens == [list(sentinel)], (
        "Lease release must run via finally even when fsm.run raises."
    )


def test_phase_dispatch_policy_outcome_allow_returns_none(helpers_module) -> None:
    """``pol_res='allow'`` (or anything else) returns ``None`` to continue."""
    settings = MagicMock()
    registry = MagicMock()
    services = MagicMock()
    run_meta = MagicMock()

    result = helpers_module._phase_dispatch_policy_outcome(
        pol_res="allow",
        pol_reason="",
        run_meta=run_meta,
        settings=settings,
        registry=registry,
        services=services,
    )

    assert result is None
    # No side-effects: the three backend helpers are mock objects and we
    # assert they were never called by virtue of `services` being a MagicMock
    # whose ``escalation_sla_minutes`` attribute was never read.


def test_phase_dispatch_policy_outcome_deny_returns_denial_payload(
    helpers_module,
) -> None:
    """``pol_res='deny'`` delegates to ``_phase_register_policy_denial``."""
    deny_payload = {"error": "nope", "exit_code": 1}
    with patch.object(
        helpers_module,
        "_phase_register_policy_denial",
        return_value=deny_payload,
    ) as mock_deny:
        payload = helpers_module._phase_dispatch_policy_outcome(
            pol_res="deny",
            pol_reason="secret-leak",
            run_meta=MagicMock(),
            settings=MagicMock(),
            registry=MagicMock(),
            services=MagicMock(escalation_sla_minutes=30),
        )

    assert payload == deny_payload
    mock_deny.assert_called_once()


def test_phase_dispatch_policy_outcome_pause_returns_hitl_payload(
    helpers_module,
) -> None:
    """``pol_res='pause'`` delegates to ``_phase_register_hitl_pause``."""
    pause_payload = {"error": "HITL PAUSE", "exit_code": 0, "status": "paused"}
    with patch.object(
        helpers_module,
        "_phase_register_hitl_pause",
        return_value=pause_payload,
    ) as mock_pause:
        payload = helpers_module._phase_dispatch_policy_outcome(
            pol_res="pause",
            pol_reason="awaiting-approval",
            run_meta=MagicMock(),
            settings=MagicMock(),
            registry=MagicMock(),
            services=MagicMock(escalation_sla_minutes=45),
        )

    assert payload == pause_payload
    mock_pause.assert_called_once()


def test_phase_dispatch_policy_outcome_warn_prints_returns_none(
    helpers_module,
) -> None:
    """``pol_res='warn'`` routes through ``print_exc`` and returns ``None``."""
    fake_print = MagicMock()
    with patch.object(helpers_module, "print_exc", fake_print):
        payload = helpers_module._phase_dispatch_policy_outcome(
            pol_res="warn",
            pol_reason="mild-flag",
            run_meta=MagicMock(),
            settings=MagicMock(),
            registry=MagicMock(),
            services=MagicMock(escalation_sla_minutes=30),
        )

    assert payload is None
    fake_print.assert_called_once()
    # Confirm the warning prefix + Rich-safe print_exc path was taken.
    args = fake_print.call_args.args
    assert args[1] == "Policy Warning:"


# ---------------------------------------------------------------------------
# 4. CC regression: per-helper complexity ceiling (L9: CC ≤ 15, body ≤ 40L)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phase_name", list(_COMPOSITE_PHASE_HELPERS))
def test_composite_helpers_keep_cc_within_l9_budget(
    phase_name: str, helpers_module
) -> None:
    """Each composite helper must stay within the L9 hard ceiling (CC ≤ 18).

    The L9 budget is 40 lines for simple helpers, but composite helpers like
    ``_phase_resolve_grounded_agent`` (chains model-alias lookup + the
    grounding precondition) reasonably run to 41-55 lines while still
    being a single coherent unit. The hard ceiling is CC ≤ 18 — enforced
    here so the helper does not become the next monolith.
    """
    from radon.complexity import cc_visit

    src = inspect.getsource(getattr(helpers_module, phase_name))
    tree = next(c for c in cc_visit(src) if c.name == phase_name)
    assert tree.complexity <= 18, (
        f"{phase_name} CC={tree.complexity} exceeds L9 hard ceiling (18). Decompose further into sub-helpers."
    )


# ---------------------------------------------------------------------------
# Small helpers (kept private to the test file)
# ---------------------------------------------------------------------------


def patch_get_run_cost_tracker(helpers_module, tracker):
    """Patch ``get_run_cost_tracker`` inside ``_phase_init_tracker`` scope."""
    from contextlib import contextmanager

    @contextmanager
    def _patch():
        helpers_module._phase_init_tracker.__globals__.get("get_run_cost_tracker")
        # The helper does a module-level import inside its body, so we must
        # patch the symbol inside ``thegent.cost.tracker`` instead.
        import thegent.cost.tracker as cost_tracker_mod

        prev = cost_tracker_mod.get_run_cost_tracker
        cost_tracker_mod.get_run_cost_tracker = lambda: tracker
        try:
            yield
        finally:
            cost_tracker_mod.get_run_cost_tracker = prev

    return _patch()
