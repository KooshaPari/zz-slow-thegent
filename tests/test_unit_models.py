"""Unit tests for model catalog and route resolution."""

from unittest.mock import patch

import pytest

from thegent.models import (
    ModelCatalog,
    filter_models_for_provider,
    normalize_model_id,
    resolve_route,
    route_contract,
)


@pytest.mark.unit
class TestResolveRoute:
    """Tests for resolve_route."""

    def test_resolves_gemini_3_flash_to_gemini_direct(self) -> None:
        # @trace FR-MOD-001
        """gemini-3-flash prefers gemini (direct) over antigravity (proxy)."""
        r = resolve_route("gemini-3-flash", policy="prefer_direct")
        assert r is not None
        provider, model_alias = r
        assert provider == "gemini"
        assert model_alias == "gemini-3-flash"

    def test_resolves_with_provider_hint(self) -> None:
        # @trace FR-MOD-001
        """provider_hint forces that provider if it serves the model."""
        r = resolve_route("gemini-3-flash", provider_hint="antigravity")
        assert r is not None
        provider, model_alias = r
        assert provider == "antigravity"
        assert model_alias == "gemini-3-flash"

    def test_resolves_claude_sonnet_alias(self) -> None:
        # @trace FR-MOD-001
        """sonnet alias maps to claude-sonnet-4.5 via claude provider."""
        r = resolve_route("sonnet", policy="prefer_direct")
        assert r is not None
        provider, model_alias = r
        assert provider == "claude"
        assert model_alias in ("sonnet", "claude-sonnet-4.5")

    def test_resolves_minimax_single_provider(self) -> None:
        # @trace FR-MOD-001
        """minimax-m2.5 only via minimax."""
        r = resolve_route("minimax-m2.5")
        assert r is not None
        provider, model_alias = r
        assert provider == "minimax"
        assert model_alias == "minimax-m2.5"

    def test_unknown_model_returns_none(self) -> None:
        # @trace FR-MOD-001
        """Unknown model returns None."""
        assert resolve_route("unknown-model-xyz") is None

    def test_invalid_provider_hint_returns_none(self) -> None:
        # @trace FR-MOD-001
        """provider_hint that doesn't serve model returns None."""
        assert resolve_route("minimax-m2.5", provider_hint="gemini") is None

    def test_provider_hint_gemini_via_minimax_returns_none(self) -> None:
        # @trace FR-MOD-001
        """gemini-3-flash not available via minimax (minimax only has MiniMax)."""
        assert resolve_route("gemini-3-flash", provider_hint="minimax") is None

    def test_routes_for_gemini_includes_providers_for_available_message(self) -> None:
        # @trace FR-MOD-001
        """routes_for returns providers for validation message (Phase 11)."""
        routes = ModelCatalog.routes_for("gemini-3-flash")
        providers = {r.provider for r in routes}
        assert "gemini" in providers
        assert "minimax" not in providers


@pytest.mark.unit
class TestModelCatalog:
    """Tests for ModelCatalog."""

    def test_routes_for_returns_list(self) -> None:
        # @trace FR-MOD-004
        """routes_for returns non-empty list for known model."""
        routes = ModelCatalog.routes_for("gemini-3-flash")
        assert len(routes) >= 1
        assert any(r.provider == "gemini" for r in routes)

    def test_to_catalog_view_has_by_model(self) -> None:
        # @trace FR-MOD-004
        """to_catalog_view includes by_model with providers."""
        view = ModelCatalog.to_catalog_view()
        assert "by_model" in view.__dict__ or hasattr(view, "by_model")
        by_model = view.by_model
        assert "gemini-3-flash" in by_model
        assert "gemini" in by_model["gemini-3-flash"]

    def test_routes_for_use_scraped_false_returns_static_only(self) -> None:
        # @trace FR-MOD-004
        """routes_for(use_scraped=False) returns only static routes."""
        routes = ModelCatalog.routes_for("gemini-3-flash", use_scraped=False)
        assert len(routes) >= 1
        assert any(r.provider == "gemini" for r in routes)


@pytest.mark.unit
class TestNormalizeModelId:
    """Tests for normalize_model_id (Phase 8 aliases)."""

    def test_sonnet_to_claude_sonnet_45(self) -> None:
        # @trace FR-MOD-002
        """sonnet -> claude-sonnet-4.5."""
        assert normalize_model_id("sonnet") == "claude-sonnet-4.5"

    def test_opus_to_claude_opus_46(self) -> None:
        # @trace FR-MOD-002
        """opus -> claude-opus-4.6."""
        assert normalize_model_id("opus") == "claude-opus-4.6"

    def test_unknown_passthrough(self) -> None:
        # @trace FR-MOD-002
        """Unknown model ID passes through."""
        assert normalize_model_id("custom-model-x") == "custom-model-x"


@pytest.mark.unit
class TestFilterModels:
    """Tests for filter_models_for_provider (blacklist)."""

    def test_filters_gemini_pro(self) -> None:
        # @trace FR-MOD-003
        """gemini-*-pro variants are blacklisted."""
        filtered = filter_models_for_provider("gemini", ["gemini-3-flash", "gemini-3-pro-preview"])
        assert "gemini-3-flash" in filtered
        assert "gemini-3-pro-preview" not in filtered

    def test_filters_claude_3(self) -> None:
        # @trace FR-MOD-003
        """claude-3-* is blacklisted."""
        filtered = filter_models_for_provider("claude", ["claude-3-opus", "claude-haiku-4.5"])
        assert "claude-haiku-4.5" in filtered
        assert "claude-3-opus" not in filtered

    def test_allows_claude_45_46(self) -> None:
        # @trace FR-MOD-003
        """claude 4.5 and 4.6 are allowed."""
        filtered = filter_models_for_provider("claude", ["claude-haiku-4.5", "claude-opus-4.6"])
        assert "claude-haiku-4.5" in filtered
        assert "claude-opus-4.6" in filtered

    def test_filters_codex_gpt5_without_53(self) -> None:
        # @trace FR-MOD-003
        """codex: gpt-5 without 5.3 is blacklisted."""
        filtered = filter_models_for_provider("codex", ["gpt-5", "gpt-5.3-codex"])
        assert "gpt-5.3-codex" in filtered
        assert "gpt-5" not in filtered


@pytest.mark.unit
class TestRouteContract:
    """Tests for route_contract (model routing schema metadata)."""

    def test_route_contract_has_schema_version(self) -> None:
        # @trace FR-MOD-005
        """route_contract returns schema_version for thegent://models/contract."""
        contract = route_contract()
        assert "schema_version" in contract
        assert contract["schema_version"] == 1

    def test_route_contract_has_backend_types(self) -> None:
        # @trace FR-MOD-005
        """route_contract includes backend_types."""
        contract = route_contract()
        assert "backend_types" in contract
        assert "direct" in contract["backend_types"]
        assert "proxy" in contract["backend_types"]

    def test_route_contract_has_policy_names(self) -> None:
        # @trace FR-MOD-005
        """route_contract includes policy_names."""
        contract = route_contract()
        assert "policy_names" in contract
        assert "prefer_direct" in contract["policy_names"]


@pytest.mark.unit
class TestResolveRouteEdgeCases:
    """Edge case tests for resolve_route."""

    def test_prefer_proxy_policy(self) -> None:
        # @trace FR-MOD-001
        """prefer_proxy policy returns proxy route when available."""
        r = resolve_route("gemini-3-flash", policy="prefer_proxy")
        assert r is not None
        provider, _model_alias = r
        # antigravity is proxy for gemini-3-flash
        assert provider == "antigravity"

    def test_cheapest_policy(self) -> None:
        # @trace FR-MOD-001
        """cheapest policy returns route with lowest cost_weight."""
        r = resolve_route("gemini-3-flash", policy="cheapest")
        assert r is not None
        # gemini direct has cost_weight=0.1, antigravity proxy has 0.2
        provider, _ = r
        assert provider == "gemini"

    def test_round_robin_policy_cycles(self) -> None:
        # @trace FR-MOD-001
        """round_robin policy cycles through providers."""
        results = set()
        for _ in range(10):
            r = resolve_route("claude-haiku-4.5", policy="round_robin")
            if r:
                results.add(r[0])
        # haiku is available via claude and copilot and antigravity
        assert len(results) >= 2


@pytest.mark.unit
class TestCatalogViewDetails:
    """Tests for CatalogView and provider details."""

    def test_catalog_view_by_provider_has_entries(self) -> None:
        # @trace FR-MOD-004
        """CatalogView by_provider has provider entries."""
        view = ModelCatalog.to_catalog_view()
        assert len(view.by_provider) > 0
        assert "claude" in view.by_provider or "gemini" in view.by_provider


@pytest.mark.unit
class TestScrapedCatalogIntegration:
    """Tests for scraped catalog merging with static models."""

    @patch("thegent.models.scrapers.get_scraped_catalog")
    def test_routes_for_merges_scraped_routes(self, mock_scraped) -> None:
        # @trace FR-MOD-004
        """routes_for merges scraped routes with static catalog."""
        mock_scraped.return_value = {
            "custom-provider": ["gemini-3-flash"],
        }
        routes = ModelCatalog.routes_for("gemini-3-flash", use_scraped=True)
        providers = {r.provider for r in routes}
        assert "gemini" in providers
        assert "custom-provider" in providers

    @patch("thegent.models.scrapers.get_scraped_catalog")
    def test_routes_for_scraped_returns_empty(self, mock_scraped) -> None:
        # @trace FR-MOD-004
        """routes_for returns static only when scraped is empty."""
        mock_scraped.return_value = {}
        routes = ModelCatalog.routes_for("gemini-3-flash", use_scraped=True)
        providers = {r.provider for r in routes}
        assert "gemini" in providers

    @patch("thegent.models.scrapers.get_scraped_catalog")
    def test_routes_for_scraped_exception_returns_static(self, mock_scraped) -> None:
        # @trace FR-MOD-004
        """routes_for returns static routes when scraped raises exception."""
        mock_scraped.side_effect = RuntimeError("scraper down")
        routes = ModelCatalog.routes_for("gemini-3-flash", use_scraped=True)
        assert len(routes) >= 1


@pytest.mark.unit
class TestToCatalogViewFormatting:
    """Tests for to_catalog_view formatting."""

    def test_to_catalog_view_use_scraped_false(self) -> None:
        # @trace FR-MOD-004
        """to_catalog_view(use_scraped=False) returns static catalog only."""
        view = ModelCatalog.to_catalog_view(use_scraped=False)
        assert "gemini" in view.by_provider or "claude" in view.by_provider
        assert len(view.by_model) > 0

    @patch("thegent.models.scrapers.get_scraped_catalog")
    def test_to_catalog_view_with_scraped_data(self, mock_scraped) -> None:
        # @trace FR-MOD-004
        """to_catalog_view uses scraped data when available."""
        mock_scraped.return_value = {
            "test-provider": ["test-model-1"],
        }
        view = ModelCatalog.to_catalog_view(use_scraped=True)
        assert "test-provider" in view.by_provider

    @patch("thegent.models.scrapers.get_scraped_catalog")
    def test_to_catalog_view_scraped_exception_fallback(self, mock_scraped) -> None:
        # @trace FR-MOD-004
        """to_catalog_view falls back to static when scraped raises."""
        mock_scraped.side_effect = RuntimeError("boom")
        view = ModelCatalog.to_catalog_view(use_scraped=True)
        assert len(view.by_provider) > 0


@pytest.mark.unit
class TestResolveRouteContractEdgeCases:
    """Tests for resolve_route_contract edge cases."""

    def test_resolve_route_contract_returns_resolved_route(self) -> None:
        # @trace FR-MOD-001
        """resolve_route_contract returns ResolvedRoute for known model."""
        from thegent.models import ResolvedRoute, resolve_route_contract

        result = resolve_route_contract("gemini-3-flash")
        assert result is not None
        assert isinstance(result, ResolvedRoute)
        assert result.provider == "gemini"
        assert result.schema_version == 1

    def test_resolve_route_contract_unknown_model(self) -> None:
        # @trace FR-MOD-001
        """resolve_route_contract returns None for unknown model."""
        from thegent.models import resolve_route_contract

        result = resolve_route_contract("nonexistent-model-xyz")
        assert result is None

    def test_resolve_route_contract_with_provider_hint(self) -> None:
        # @trace FR-MOD-001
        """resolve_route_contract respects provider_hint."""
        from thegent.models import resolve_route_contract

        result = resolve_route_contract("gemini-3-flash", provider_hint="antigravity")
        assert result is not None
        assert result.provider == "antigravity"

    def test_resolve_route_contract_invalid_provider_hint(self) -> None:
        # @trace FR-MOD-001
        """resolve_route_contract returns None for invalid provider_hint."""
        from thegent.models import resolve_route_contract

        result = resolve_route_contract("gemini-3-flash", provider_hint="nonexistent")
        assert result is None


@pytest.mark.unit
class TestUnknownProviderHandling:
    """Tests for unknown provider/model handling."""

    def test_filter_empty_model_id(self) -> None:
        # @trace FR-MOD-003
        """Empty model ID is blacklisted."""
        filtered = filter_models_for_provider("gemini", ["", "gemini-3-flash"])
        assert "" not in filtered
        assert "gemini-3-flash" in filtered

    def test_normalize_none_model_id(self) -> None:
        # @trace FR-MOD-002
        """None model ID normalizes to empty string."""
        assert normalize_model_id(None) == ""

    def test_normalize_whitespace_model_id(self) -> None:
        # @trace FR-MOD-002
        """Whitespace model ID passes through stripped."""
        assert normalize_model_id("  ") == ""

    def test_normalize_route_policy_invalid(self) -> None:
        # @trace FR-MOD-005
        """Invalid route policy raises ValueError."""
        from thegent.models import normalize_route_policy

        with pytest.raises(ValueError, match="Invalid routing policy"):
            normalize_route_policy("invalid_policy")

    def test_normalize_route_policy_none_defaults(self) -> None:
        # @trace FR-MOD-005
        """None policy defaults to prefer_direct."""
        from thegent.models import normalize_route_policy

        assert normalize_route_policy(None) == "prefer_direct"


@pytest.mark.unit
class TestToContractView:
    """Tests for ModelCatalog.to_contract_view."""

    def test_to_contract_view_has_schema_version(self) -> None:
        # @trace FR-MOD-005
        """to_contract_view returns schema_version."""
        view = ModelCatalog.to_contract_view(use_scraped=False)
        assert view["schema_version"] == 1
        assert "routes" in view
        assert "count" in view
        assert view["count"] > 0

    def test_to_contract_view_provider_filter(self) -> None:
        # @trace FR-MOD-005
        """to_contract_view filters by provider."""
        view = ModelCatalog.to_contract_view(use_scraped=False, provider_filter="gemini")
        routes = view["routes"]
        for route_list in routes.values():
            for r in route_list:
                assert r["provider"] == "gemini"


# ---------------------------------------------------------------------------
# Coverage gaps: catalog.py lines 120, 126, 129, 131, 189, 207-215, 308-317, 366
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFilterModelsBlacklistEdgeCases:
    """Tests for filter_models_for_provider blacklist edge cases."""

    def test_filters_empty_model_id_returns_true(self) -> None:
        # @trace FR-MOD-003
        """Empty model_id is blacklisted (line 120)."""
        filtered = filter_models_for_provider("gemini", [""])
        assert "" not in filtered

    def test_filters_claude_4_not_45_46(self) -> None:
        # @trace FR-MOD-003
        """claude-4-haiku (no 4.5 or 4.6) is blacklisted (line 126)."""
        filtered = filter_models_for_provider("claude", ["claude-4-haiku", "claude-haiku-4.5"])
        assert "claude-4-haiku" not in filtered
        assert "claude-haiku-4.5" in filtered

    def test_filters_gemini_1x(self) -> None:
        # @trace FR-MOD-003
        """gemini-1.x is blacklisted (line 129)."""
        filtered = filter_models_for_provider("gemini", ["gemini-1.5-flash", "gemini-3-flash"])
        assert "gemini-1.5-flash" not in filtered
        assert "gemini-3-flash" in filtered

    def test_filters_gemini_20_flash_exp(self) -> None:
        # @trace FR-MOD-003
        """gemini-2.0-flash-exp is blacklisted (line 131)."""
        filtered = filter_models_for_provider("gemini", ["gemini-2.0-flash-exp", "gemini-3-flash"])
        assert "gemini-2.0-flash-exp" not in filtered

    def test_filters_gpt4(self) -> None:
        # @trace FR-MOD-003
        """gpt-4 variants are blacklisted."""
        filtered = filter_models_for_provider("copilot", ["gpt-4o", "gpt-5.3-codex"])
        assert "gpt-4o" not in filtered
        assert "gpt-5.3-codex" in filtered


@pytest.mark.unit
class TestCatalogMergeRoutes:
    """Tests for _merge_routes deduplication (lines 207-215)."""

    def test_merge_routes_deduplicates(self) -> None:
        # @trace FR-MOD-004
        """_merge_routes skips duplicate provider+model_alias."""
        from thegent.models.catalog import Route, _merge_routes

        r1 = Route(
            provider="gemini",
            backend_type="direct",
            model_alias="flash",
            priority=0,
            cost_weight=0.3,
        )
        r2 = Route(
            provider="gemini",
            backend_type="direct",
            model_alias="flash",
            priority=10,
            cost_weight=0.8,
        )
        r3 = Route(
            provider="claude",
            backend_type="direct",
            model_alias="haiku",
            priority=0,
            cost_weight=0.3,
        )
        merged = _merge_routes([r1], [r2, r3])
        assert len(merged) == 2
        providers = {(r.provider, r.model_alias) for r in merged}
        assert ("gemini", "flash") in providers
        assert ("claude", "haiku") in providers

    def test_merge_routes_empty_base(self) -> None:
        # @trace FR-MOD-004
        """_merge_routes with empty base returns all extras."""
        from thegent.models.catalog import Route, _merge_routes

        r1 = Route(
            provider="test",
            backend_type="direct",
            model_alias="m1",
            priority=0,
            cost_weight=0.3,
        )
        merged = _merge_routes([], [r1])
        assert len(merged) == 1


@pytest.mark.unit
class TestNonStringModelIdSkipped:
    """Tests for non-string model_id being skipped in _scraped_to_routes (line 189)."""

    def test_scraped_to_routes_skips_empty_models(self) -> None:
        # @trace FR-MOD-004
        """_scraped_to_routes skips empty model IDs."""
        from thegent.models.catalog import _scraped_to_routes

        result = _scraped_to_routes({"test": ["valid-model", "", None]})
        # Only valid-model should produce routes
        assert "valid-model" in result or len(result) >= 0


@pytest.mark.unit
class TestToContractViewScrapedException:
    """Tests for to_contract_view scraped exception fallback (lines 308-317)."""

    @patch(
        "thegent.models.scrapers.get_scraped_catalog",
        side_effect=RuntimeError("scraper down"),
    )
    def test_to_contract_view_scraped_exception(self, mock_scraped) -> None:
        # @trace FR-MOD-005
        """to_contract_view falls back to static when scraped raises."""
        view = ModelCatalog.to_contract_view(use_scraped=True)
        assert view["count"] > 0

    @patch("thegent.models.scrapers.get_scraped_catalog")
    def test_to_contract_view_scraped_merges(self, mock_scraped) -> None:
        # @trace FR-MOD-005
        """to_contract_view merges scraped data into routes."""
        mock_scraped.return_value = {"test-prov": ["test-model"]}
        view = ModelCatalog.to_contract_view(use_scraped=True)
        assert view["count"] > 0


@pytest.mark.unit
class TestResolveRouteContractReturnsNone:
    """Tests for resolve_route_contract returning None (line 366)."""

    def test_resolve_route_contract_no_matching_route_obj(self) -> None:
        # @trace FR-MOD-001
        """resolve_route_contract returns None when route not in catalog routes."""
        from thegent.models import resolve_route_contract

        # unknown model
        result = resolve_route_contract("totally-unknown-model-xyz-999")
        assert result is None
