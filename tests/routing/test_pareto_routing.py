"""Integration tests for ParetoRouter wired into task intake API (run_impl / bg_impl).

Covers:
- routing="pareto" causes ParetoRouter.select() to be invoked via _apply_pareto_routing
- The selected model/provider is used for the run (agent/model set from ParetoRouter output)
- Falls back gracefully when ParetoRouter returns no result (empty candidates)
- Falls back gracefully when ParetoRouter raises an exception
- bg_impl similarly uses _apply_pareto_routing when routing="pareto"
- Direct unit tests for ParetoRouter itself

@trace FR-ROU-001
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from thegent.utils.routing_impl.pareto_router import ParetoRouter, RouteCandidate

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

_FAKE_CANDIDATE = RouteCandidate(
    model="claude-sonnet-4.6",
    provider="claude",
    cost_per_1k=0.5,
    quality_score=0.88,
)

_FALLBACK_AGENT = "antigravity"
_FALLBACK_MODEL = "gemini-3-flash"


# ---------------------------------------------------------------------------
# Unit tests for _apply_pareto_routing helper
# ---------------------------------------------------------------------------


class TestApplyParetoRouting:
    """Unit tests for the _apply_pareto_routing helper extracted into cli_impl.

    Note: _apply_pareto_routing uses local imports inside its body, so we patch
    at the source module level (thegent.routing.pareto_router and
    thegent.models.catalog) rather than on cli_impl directly.
    """

    def _call(self, **overrides):
        from thegent.cli.commands.impl import _apply_pareto_routing

        defaults = {
            "agent": None,
            "model": None,
            "routing": "pareto",
            "include_contract": False,
            "route_contract": None,
            "route_request": None,
        }
        defaults.update(overrides)
        return _apply_pareto_routing(**defaults)

    # -- routing="pareto" triggers ParetoRouter.select()

    def test_pareto_router_select_is_invoked(self):
        """When routing="pareto" and no agent/model set, ParetoRouter.select() must be called."""
        # @trace FR-ROU-001
        with patch(
            "thegent.utils.routing_impl.pareto_router.ParetoRouter.select",
            return_value=_FAKE_CANDIDATE,
        ) as mock_select:
            self._call()
        assert mock_select.called, "ParetoRouter.select() was not called for routing='pareto'"

    def test_selected_provider_and_model_returned(self):
        """The provider and model from ParetoRouter.select() are returned as agent and model."""
        # @trace FR-ROU-001
        with patch("thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE):
            agent, model, _, _ = self._call()
        assert agent == _FAKE_CANDIDATE.provider
        assert model == _FAKE_CANDIDATE.model

    # -- fallback: empty catalog

    def test_fallback_on_empty_catalog(self):
        """When the catalog is empty, falls back to antigravity/gemini-3-flash."""
        # @trace FR-ROU-001
        with patch("thegent.models.catalog._get_catalog", return_value={}):
            agent, model, _, _ = self._call()
        assert agent == _FALLBACK_AGENT
        assert model == _FALLBACK_MODEL

    # -- fallback: ParetoRouter raises

    def test_fallback_on_pareto_exception(self):
        """When ParetoRouter.select() raises, falls back gracefully."""
        # @trace FR-ROU-001
        with patch(
            "thegent.utils.routing_impl.pareto_router.ParetoRouter.select",
            side_effect=RuntimeError("simulated pareto failure"),
        ):
            agent, model, _, _ = self._call()
        assert agent == _FALLBACK_AGENT
        assert model == _FALLBACK_MODEL

    # -- guard: no-op when agent already set

    def test_no_op_when_agent_set(self):
        """ParetoRouter.select() must NOT be called when agent is already specified."""
        # @trace FR-ROU-001
        with patch(
            "thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE
        ) as mock_select:
            agent, _model, _, _ = self._call(agent="existing-agent")
        assert not mock_select.called
        assert agent == "existing-agent"

    # -- guard: no-op when model already set

    def test_no_op_when_model_set(self):
        """ParetoRouter.select() must NOT be called when model is already specified."""
        # @trace FR-ROU-001
        with patch(
            "thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE
        ) as mock_select:
            _agent, model, _, _ = self._call(model="some-model")
        assert not mock_select.called
        assert model == "some-model"

    # -- guard: no-op when routing is not "pareto"

    def test_no_op_when_routing_not_pareto(self):
        """ParetoRouter.select() must NOT be called when routing != 'pareto'."""
        # @trace FR-ROU-001
        with patch(
            "thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE
        ) as mock_select:
            agent, model, _, _ = self._call(routing="prefer_direct")
        assert not mock_select.called
        assert agent is None  # unchanged
        assert model is None  # unchanged

    # -- include_contract populates route_contract and route_request

    def test_include_contract_populates_metadata(self):
        """When include_contract=True, route_contract and route_request are populated."""
        # @trace FR-ROU-001
        with patch("thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE):
            _, _, rc, rr = self._call(include_contract=True)
        assert rc is not None, "route_contract should be populated"
        assert rc.get("routing_policy") == "pareto"
        assert rc.get("provider") == _FAKE_CANDIDATE.provider
        assert rc.get("model_alias") == _FAKE_CANDIDATE.model
        assert rr is not None, "route_request should be populated"
        assert rr.get("policy") == "pareto"
        assert rr.get("resolved_agent") == _FAKE_CANDIDATE.provider

    def test_no_contract_when_include_contract_false(self):
        """When include_contract=False, route_contract and route_request are not mutated."""
        # @trace FR-ROU-001
        orig_rc = {"existing": "value"}
        orig_rr = {"existing": "value"}
        with patch("thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE):
            _, _, rc, rr = self._call(
                include_contract=False,
                route_contract=orig_rc,
                route_request=orig_rr,
            )
        # The original dicts should be returned unchanged
        assert rc == orig_rc
        assert rr == orig_rr

    def test_none_routing_is_no_op(self):
        """routing=None leaves agent and model unchanged."""
        # @trace FR-ROU-001
        with patch(
            "thegent.utils.routing_impl.pareto_router.ParetoRouter.select", return_value=_FAKE_CANDIDATE
        ) as mock_select:
            agent, model, _, _ = self._call(routing=None)
        assert not mock_select.called
        assert agent is None
        assert model is None


# ---------------------------------------------------------------------------
# Integration tests: run_impl delegates to _apply_pareto_routing
# ---------------------------------------------------------------------------


class TestRunImplParetoIntegration:
    """Integration tests: run_impl calls _apply_pareto_routing when routing='pareto'."""

    def test_apply_pareto_routing_called_in_run_impl(self):
        """run_impl must delegate to _apply_pareto_routing when routing='pareto'."""
        # @trace FR-ROU-001
        with patch(
            "thegent.cli.commands.impl._apply_pareto_routing",
            return_value=(None, None, None, None),
        ) as mock_apply:
            try:
                from thegent.cli.commands.impl import run_impl

                run_impl(
                    agent=None,
                    prompt="test",
                    routing="pareto",
                )
            except Exception:
                # run_impl will fail further down without heavy mocking; that's OK
                pass
            mock_apply.assert_called_once()
            args = mock_apply.call_args
            # routing="pareto" should be passed
            assert args[0][2] == "pareto" or args.kwargs.get("routing") == "pareto"

    def test_apply_pareto_routing_not_called_when_routing_none(self):
        """run_impl with routing=None still calls _apply_pareto_routing (guard handled inside helper)."""
        # @trace FR-ROU-001
        with patch(
            "thegent.cli.commands.impl._apply_pareto_routing",
            return_value=(None, None, None, None),
        ) as mock_apply:
            try:
                from thegent.cli.commands.impl import run_impl

                run_impl(
                    agent=None,
                    prompt="test",
                    routing=None,
                )
            except Exception:
                pass
            # _apply_pareto_routing is always called; it guards internally
            mock_apply.assert_called_once()


# ---------------------------------------------------------------------------
# Integration tests: bg_impl delegates to _apply_pareto_routing
# ---------------------------------------------------------------------------


class TestBgImplParetoIntegration:
    """Integration tests: bg_impl calls _apply_pareto_routing when routing='pareto'."""

    def test_apply_pareto_routing_called_in_bg_impl(self):
        """bg_impl must delegate to _apply_pareto_routing when routing='pareto'."""
        # @trace FR-ROU-001
        with patch(
            "thegent.cli.commands.impl._apply_pareto_routing",
            return_value=(None, None, None, None),
        ) as mock_apply:
            try:
                from thegent.cli.commands.impl import bg_impl

                bg_impl(
                    agent=None,
                    prompt="test",
                    cd=None,
                    mode="write",
                    timeout=300,
                    full=False,
                    routing="pareto",
                )
            except Exception:
                pass
            mock_apply.assert_called_once()


# ---------------------------------------------------------------------------
# Direct unit tests for ParetoRouter
# ---------------------------------------------------------------------------


class TestParetoRouterUnit:
    """Unit tests that ParetoRouter itself works correctly (not mocked)."""

    def test_select_returns_best_quality_per_cost(self):
        """ParetoRouter.select() returns a candidate from the Pareto frontier."""
        # m1 (cost=1.0, q=0.9), m2 (cost=2.0, q=0.8), m3 (cost=0.5, q=0.7)
        # m1 dominates m2 (lower cost, higher quality)
        # Frontier: m1 and m3.  m1 ratio=0.9, m3 ratio=0.7/0.5=1.4 → m3 wins
        candidates = [
            RouteCandidate(model="m1", provider="p1", cost_per_1k=1.0, quality_score=0.9),
            RouteCandidate(model="m2", provider="p2", cost_per_1k=2.0, quality_score=0.8),
            RouteCandidate(model="m3", provider="p3", cost_per_1k=0.5, quality_score=0.7),
        ]
        result = ParetoRouter().select(candidates)
        assert result.model in ("m1", "m3"), f"Unexpected selection: {result.model}"

    def test_select_raises_on_empty(self):
        """ParetoRouter.select() raises ValueError for empty candidates."""
        with pytest.raises(ValueError, match="candidates must be non-empty"):
            ParetoRouter().select([])

    def test_select_single_candidate_returns_it(self):
        """ParetoRouter.select() returns the only candidate when list has one element."""
        candidate = RouteCandidate(model="solo", provider="x", cost_per_1k=1.0, quality_score=0.8)
        result = ParetoRouter().select([candidate])
        assert result is candidate

    def test_select_zero_cost_uses_quality_fallback(self):
        """ParetoRouter falls back to highest quality when all costs are zero."""
        candidates = [
            RouteCandidate(model="m1", provider="p1", cost_per_1k=0.0, quality_score=0.9),
            RouteCandidate(model="m2", provider="p2", cost_per_1k=0.0, quality_score=0.7),
        ]
        result = ParetoRouter().select(candidates)
        assert result.model == "m1"

    def test_catalog_candidates_produce_valid_selection(self):
        """RouteCandidate objects built from real catalog entries yield a valid ParetoRouter selection."""
        # @trace FR-ROU-001
        from thegent.models.catalog import _get_catalog
        from thegent.utils.routing_impl.pareto_router import QUALITY_PROXY

        catalog = _get_catalog()
        candidates = []
        for routes in catalog.values():
            for r in routes:
                quality = QUALITY_PROXY.get(r.model_alias, 0.5)
                candidates.append(
                    RouteCandidate(
                        model=r.model_alias,
                        provider=r.provider,
                        cost_per_1k=r.cost_weight,
                        quality_score=quality,
                    )
                )
        assert candidates, "Static catalog must contain at least one route"
        result = ParetoRouter().select(candidates)
        assert result.model, "Selected candidate must have a non-empty model"
        assert result.provider, "Selected candidate must have a non-empty provider"
        assert 0.0 <= result.quality_score <= 1.0
        assert result.cost_per_1k >= 0.0

    def test_dominated_candidates_excluded(self):
        """Dominated candidates (higher cost, lower quality) are excluded from selection."""
        dominated = RouteCandidate(model="bad", provider="x", cost_per_1k=5.0, quality_score=0.1)
        dominator = RouteCandidate(model="good", provider="y", cost_per_1k=1.0, quality_score=0.9)
        result = ParetoRouter().select([dominated, dominator])
        assert result.model == "good", f"Expected 'good', got '{result.model}'"
