"""Tests for GW-10 (route_config) and GW-11 (provider_preferences).

All tests are tagged with the FR-ROUTE-010 requirement marker.
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.provider_preferences import (
    PriceConstraint,
    ProviderOptions,
    ProviderPreferences,
    extract_provider_options,
    extract_provider_preferences,
    filter_models_by_preferences,
    to_openrouter_provider_body,
)
from thegent.utils.routing_impl.route_config import (
    CacheConfig,
    CircuitBreakerConfig,
    RetryConfig,
    RouteConfig,
    RouteTarget,
    from_request_body,
    models_to_targets,
)

# ---------------------------------------------------------------------------
# GW-10: RouteConfig
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-010")
class TestRouteConfig:
    """Tests for the recursive RouteConfig schema (GW-10)."""

    # -- Dataclass defaults --------------------------------------------------

    def test_cache_config_defaults(self) -> None:
        cfg = CacheConfig()
        assert cfg.mode == "none"
        assert cfg.max_age == 300
        assert cfg.namespace is None

    def test_retry_config_defaults(self) -> None:
        cfg = RetryConfig()
        assert cfg.attempts == 2
        assert cfg.on_status_codes == [429, 500, 502, 503]
        assert cfg.backoff_factor == 1.5

    def test_circuit_breaker_config_defaults(self) -> None:
        cfg = CircuitBreakerConfig()
        assert cfg.failure_threshold == 5
        assert cfg.success_threshold == 2
        assert cfg.timeout_sec == 60.0

    def test_route_target_defaults(self) -> None:
        t = RouteTarget(provider="openai", model="gpt-4o")
        assert t.weight == 1.0
        assert t.strategy is None
        assert t.targets == []
        assert t.cache is None
        assert t.retry is None
        assert t.circuit_breaker is None
        assert t.on_status_codes == [429, 500, 502, 503, 529]

    def test_route_config_defaults(self) -> None:
        cfg = RouteConfig()
        assert cfg.strategy == "fallback"
        assert cfg.targets == []
        assert cfg.models == []
        assert isinstance(cfg.cache, CacheConfig)
        assert isinstance(cfg.retry, RetryConfig)
        assert isinstance(cfg.circuit_breaker, CircuitBreakerConfig)

    # -- is_leaf property ----------------------------------------------------

    def test_is_leaf_true_when_provider_set_and_no_strategy(self) -> None:
        t = RouteTarget(provider="openai", model="gpt-4o")
        assert t.is_leaf is True

    def test_is_leaf_false_when_strategy_set(self) -> None:
        t = RouteTarget(
            strategy="fallback",
            targets=[RouteTarget(provider="openai", model="gpt-4o")],
        )
        assert t.is_leaf is False

    def test_is_leaf_false_when_provider_is_none(self) -> None:
        t = RouteTarget(model="gpt-4o")
        assert t.is_leaf is False

    # -- models_to_targets ---------------------------------------------------

    def test_models_to_targets_with_slash(self) -> None:
        targets = models_to_targets(["openai/gpt-4o", "anthropic/claude-3-5-sonnet"])
        assert len(targets) == 2
        assert targets[0].provider == "openai"
        assert targets[0].model == "gpt-4o"
        assert targets[1].provider == "anthropic"
        assert targets[1].model == "claude-3-5-sonnet"

    def test_models_to_targets_without_slash(self) -> None:
        targets = models_to_targets(["gpt-4o"])
        assert targets[0].provider is None
        assert targets[0].model == "gpt-4o"

    def test_models_to_targets_empty(self) -> None:
        assert models_to_targets([]) == []

    def test_models_to_targets_all_are_leaves(self) -> None:
        targets = models_to_targets(["openai/gpt-4o", "openai/gpt-4o-mini"])
        for t in targets:
            # provider is set, strategy is None → is_leaf True
            assert t.strategy is None

    def test_models_to_targets_preserves_order(self) -> None:
        names = ["openai/gpt-4o", "anthropic/claude-sonnet-4-6", "google/gemini-pro"]
        targets = models_to_targets(names)
        assert [t.model for t in targets] == [
            "gpt-4o",
            "claude-sonnet-4-6",
            "gemini-pro",
        ]

    def test_models_to_targets_splits_only_first_slash(self) -> None:
        # "openai/gpt-4o/preview" → provider="openai", model="gpt-4o/preview"
        targets = models_to_targets(["openai/gpt-4o/preview"])
        assert targets[0].provider == "openai"
        assert targets[0].model == "gpt-4o/preview"

    # -- from_request_body ---------------------------------------------------

    def test_from_request_body_returns_none_when_no_keys(self) -> None:
        result = from_request_body({"messages": []})
        assert result is None

    def test_from_request_body_reads_models_list(self) -> None:
        body = {"models": ["openai/gpt-4o", "anthropic/claude-sonnet-4-6"]}
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.strategy == "fallback"
        assert len(cfg.targets) == 2
        assert cfg.models == ["openai/gpt-4o", "anthropic/claude-sonnet-4-6"]

    def test_from_request_body_models_target_providers(self) -> None:
        body = {"models": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"]}
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.targets[0].provider == "openai"
        assert cfg.targets[1].provider == "anthropic"

    def test_from_request_body_reads_route_config(self) -> None:
        body = {
            "route_config": {
                "strategy": "loadbalance",
                "targets": [
                    {"provider": "openai", "model": "gpt-4o", "weight": 0.7},
                    {"provider": "anthropic", "model": "claude-3-5-sonnet", "weight": 0.3},
                ],
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.strategy == "loadbalance"
        assert len(cfg.targets) == 2
        assert cfg.targets[0].weight == 0.7
        assert cfg.targets[1].weight == 0.3

    def test_from_request_body_route_config_with_cache(self) -> None:
        body = {
            "route_config": {
                "strategy": "fallback",
                "targets": [{"provider": "openai", "model": "gpt-4o"}],
                "cache": {"mode": "semantic", "max_age": 600, "namespace": "test"},
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.cache.mode == "semantic"
        assert cfg.cache.max_age == 600
        assert cfg.cache.namespace == "test"

    def test_from_request_body_route_config_with_retry(self) -> None:
        body = {
            "route_config": {
                "strategy": "fallback",
                "targets": [{"provider": "openai", "model": "gpt-4o"}],
                "retry": {"attempts": 5, "backoff_factor": 2.0},
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.retry.attempts == 5
        assert cfg.retry.backoff_factor == 2.0

    def test_from_request_body_route_config_with_circuit_breaker(self) -> None:
        body = {
            "route_config": {
                "strategy": "fallback",
                "targets": [{"provider": "openai", "model": "gpt-4o"}],
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "success_threshold": 1,
                    "timeout_sec": 30.0,
                },
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.circuit_breaker.failure_threshold == 3
        assert cfg.circuit_breaker.success_threshold == 1
        assert cfg.circuit_breaker.timeout_sec == 30.0

    def test_from_request_body_route_config_prefers_route_config_key(self) -> None:
        """When both keys present, "route_config" takes precedence."""
        body = {
            "models": ["openai/gpt-4o"],
            "route_config": {
                "strategy": "loadbalance",
                "targets": [
                    {"provider": "anthropic", "model": "claude-3-5-sonnet"},
                ],
            },
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.strategy == "loadbalance"
        assert cfg.targets[0].provider == "anthropic"

    # -- Nested strategy deserialization -------------------------------------

    def test_nested_route_target_deserialization(self) -> None:
        body = {
            "route_config": {
                "strategy": "fallback",
                "targets": [
                    {
                        "strategy": "loadbalance",
                        "targets": [
                            {"provider": "openai", "model": "gpt-4o", "weight": 0.6},
                            {"provider": "openai", "model": "gpt-4o-mini", "weight": 0.4},
                        ],
                    },
                    {"provider": "anthropic", "model": "claude-3-5-sonnet"},
                ],
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.strategy == "fallback"
        inner = cfg.targets[0]
        assert inner.strategy == "loadbalance"
        assert inner.is_leaf is False
        assert len(inner.targets) == 2
        assert inner.targets[0].model == "gpt-4o"
        fallback_leaf = cfg.targets[1]
        assert fallback_leaf.is_leaf is True

    # -- Per-target overrides ------------------------------------------------

    def test_per_target_cache_override(self) -> None:
        body = {
            "route_config": {
                "strategy": "fallback",
                "targets": [
                    {
                        "provider": "openai",
                        "model": "gpt-4o",
                        "cache": {"mode": "exact", "max_age": 120},
                    }
                ],
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.targets[0].cache is not None
        assert cfg.targets[0].cache.mode == "exact"
        assert cfg.targets[0].cache.max_age == 120

    def test_per_target_on_status_codes_override(self) -> None:
        body = {
            "route_config": {
                "strategy": "fallback",
                "targets": [
                    {
                        "provider": "openai",
                        "model": "gpt-4o",
                        "on_status_codes": [503],
                    }
                ],
            }
        }
        cfg = from_request_body(body)
        assert cfg is not None
        assert cfg.targets[0].on_status_codes == [503]


# ---------------------------------------------------------------------------
# GW-11: ProviderPreferences
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-010")
class TestProviderPreferences:
    """Tests for provider routing preferences (GW-11)."""

    # -- Dataclass defaults --------------------------------------------------

    def test_provider_preferences_defaults(self) -> None:
        prefs = ProviderPreferences()
        assert prefs.order == []
        assert prefs.only == []
        assert prefs.ignore == []
        assert prefs.allow_fallbacks is True
        assert prefs.data_collection == "allow"
        assert prefs.quantizations == []
        assert prefs.sort is None
        assert isinstance(prefs.max_price, PriceConstraint)

    def test_price_constraint_defaults(self) -> None:
        pc = PriceConstraint()
        assert pc.prompt is None
        assert pc.completion is None

    def test_provider_options_defaults(self) -> None:
        opts = ProviderOptions()
        assert opts.options == {}

    # -- extract_provider_preferences ----------------------------------------

    def test_extract_returns_none_when_key_absent(self) -> None:
        assert extract_provider_preferences({}) is None

    def test_extract_returns_none_when_value_not_dict(self) -> None:
        assert extract_provider_preferences({"provider": "openai"}) is None

    def test_extract_basic_order(self) -> None:
        body = {"provider": {"order": ["openai", "anthropic"]}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.order == ["openai", "anthropic"]

    def test_extract_only_and_ignore(self) -> None:
        body = {"provider": {"only": ["openai"], "ignore": ["cohere"]}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.only == ["openai"]
        assert prefs.ignore == ["cohere"]

    def test_extract_allow_fallbacks_false(self) -> None:
        body = {"provider": {"allow_fallbacks": False}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.allow_fallbacks is False

    def test_extract_data_collection_deny(self) -> None:
        body = {"provider": {"data_collection": "deny"}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.data_collection == "deny"

    def test_extract_quantizations(self) -> None:
        body = {"provider": {"quantizations": ["fp16", "bf16"]}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.quantizations == ["fp16", "bf16"]

    def test_extract_sort(self) -> None:
        body = {"provider": {"sort": "latency"}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.sort == "latency"

    def test_extract_max_price(self) -> None:
        body = {"provider": {"max_price": {"prompt": 0.5, "completion": 1.5}}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.max_price.prompt == 0.5
        assert prefs.max_price.completion == 1.5

    def test_extract_max_price_partial(self) -> None:
        body = {"provider": {"max_price": {"prompt": 0.25}}}
        prefs = extract_provider_preferences(body)
        assert prefs is not None
        assert prefs.max_price.prompt == 0.25
        assert prefs.max_price.completion is None

    # -- extract_provider_options --------------------------------------------

    def test_extract_options_returns_none_when_absent(self) -> None:
        assert extract_provider_options({}) is None

    def test_extract_options_returns_none_for_non_dict(self) -> None:
        assert extract_provider_options({"providerOptions": "bad"}) is None

    def test_extract_options_basic(self) -> None:
        body = {
            "providerOptions": {
                "openai": {"organization": "org-xyz"},
                "anthropic": {"timeout": 30},
            }
        }
        opts = extract_provider_options(body)
        assert opts is not None
        assert opts.options["openai"] == {"organization": "org-xyz"}
        assert opts.options["anthropic"] == {"timeout": 30}

    def test_extract_options_skips_non_dict_values(self) -> None:
        body = {"providerOptions": {"openai": {"key": "val"}, "bad": "string"}}
        opts = extract_provider_options(body)
        assert opts is not None
        assert "openai" in opts.options
        assert "bad" not in opts.options

    # -- filter_models_by_preferences ----------------------------------------

    def test_filter_no_preferences_returns_all(self) -> None:
        models = ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"]
        prefs = ProviderPreferences()
        result = filter_models_by_preferences(models, prefs)
        assert result == models

    def test_filter_only_whitelist(self) -> None:
        models = ["openai/gpt-4o", "anthropic/claude-3-5-sonnet", "cohere/command-r"]
        prefs = ProviderPreferences(only=["openai", "anthropic"])
        result = filter_models_by_preferences(models, prefs)
        assert "cohere/command-r" not in result
        assert "openai/gpt-4o" in result
        assert "anthropic/claude-3-5-sonnet" in result

    def test_filter_ignore_blacklist(self) -> None:
        models = ["openai/gpt-4o", "cohere/command-r"]
        prefs = ProviderPreferences(ignore=["cohere"])
        result = filter_models_by_preferences(models, prefs)
        assert result == ["openai/gpt-4o"]

    def test_filter_order_brings_priority_to_front(self) -> None:
        models = ["openai/gpt-4o", "anthropic/claude-3-5-sonnet", "google/gemini-pro"]
        prefs = ProviderPreferences(order=["anthropic", "openai"])
        result = filter_models_by_preferences(models, prefs)
        # anthropic first, then openai, then google (fallback)
        assert result.index("anthropic/claude-3-5-sonnet") < result.index("openai/gpt-4o")
        assert "google/gemini-pro" in result

    def test_filter_order_without_fallbacks_drops_non_priority(self) -> None:
        models = ["openai/gpt-4o", "anthropic/claude-3-5-sonnet", "google/gemini-pro"]
        prefs = ProviderPreferences(order=["anthropic"], allow_fallbacks=False)
        result = filter_models_by_preferences(models, prefs)
        assert result == ["anthropic/claude-3-5-sonnet"]

    def test_filter_quantization(self) -> None:
        models = ["openai/gpt-4o-fp16", "openai/gpt-4o-int8", "openai/gpt-4o"]
        prefs = ProviderPreferences(quantizations=["fp16"])
        result = filter_models_by_preferences(models, prefs)
        assert result == ["openai/gpt-4o-fp16"]

    def test_filter_quantization_multiple(self) -> None:
        models = ["openai/gpt-4o-fp16", "openai/gpt-4o-bf16", "openai/gpt-4o-int8"]
        prefs = ProviderPreferences(quantizations=["fp16", "bf16"])
        result = filter_models_by_preferences(models, prefs)
        assert "openai/gpt-4o-int8" not in result
        assert "openai/gpt-4o-fp16" in result
        assert "openai/gpt-4o-bf16" in result

    def test_filter_empty_models_returns_empty(self) -> None:
        prefs = ProviderPreferences(order=["openai"])
        assert filter_models_by_preferences([], prefs) == []

    def test_filter_only_and_ignore_combined(self) -> None:
        models = ["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-3-5-sonnet"]
        prefs = ProviderPreferences(only=["openai", "anthropic"], ignore=["anthropic"])
        result = filter_models_by_preferences(models, prefs)
        assert all("anthropic" not in m for m in result)
        assert "openai/gpt-4o" in result

    def test_filter_bare_model_names_without_slash(self) -> None:
        models = ["gpt-4o", "claude-3-5-sonnet"]
        prefs = ProviderPreferences(ignore=["gpt-4o"])
        # bare names: provider == full string
        result = filter_models_by_preferences(models, prefs)
        # "gpt-4o" is ignored because _provider_of("gpt-4o") == "gpt-4o"
        assert "gpt-4o" not in result
        assert "claude-3-5-sonnet" in result

    # -- to_openrouter_provider_body -----------------------------------------

    def test_to_openrouter_body_basic_fields(self) -> None:
        prefs = ProviderPreferences(order=["openai"], allow_fallbacks=False)
        body = to_openrouter_provider_body(prefs)
        assert body["order"] == ["openai"]
        assert body["allow_fallbacks"] is False
        assert body["data_collection"] == "allow"
        assert body["quantizations"] == []

    def test_to_openrouter_body_sort_included_when_set(self) -> None:
        prefs = ProviderPreferences(sort="price")
        body = to_openrouter_provider_body(prefs)
        assert body["sort"] == "price"

    def test_to_openrouter_body_sort_absent_when_none(self) -> None:
        prefs = ProviderPreferences()
        body = to_openrouter_provider_body(prefs)
        assert "sort" not in body

    def test_to_openrouter_body_max_price_included(self) -> None:
        prefs = ProviderPreferences(max_price=PriceConstraint(prompt=0.5, completion=1.0))
        body = to_openrouter_provider_body(prefs)
        assert body["max_price"] == {"prompt": 0.5, "completion": 1.0}

    def test_to_openrouter_body_max_price_absent_when_empty(self) -> None:
        prefs = ProviderPreferences()
        body = to_openrouter_provider_body(prefs)
        assert "max_price" not in body

    def test_to_openrouter_body_max_price_partial(self) -> None:
        prefs = ProviderPreferences(max_price=PriceConstraint(prompt=0.1))
        body = to_openrouter_provider_body(prefs)
        assert body["max_price"] == {"prompt": 0.1}
        assert "completion" not in body["max_price"]

    def test_to_openrouter_body_roundtrip(self) -> None:
        """Serialized body should round-trip through extract_provider_preferences."""
        prefs = ProviderPreferences(
            order=["openai", "anthropic"],
            only=["openai"],
            ignore=["cohere"],
            allow_fallbacks=False,
            data_collection="deny",
            quantizations=["fp16"],
            sort="latency",
            max_price=PriceConstraint(prompt=1.0, completion=2.0),
        )
        wire = to_openrouter_provider_body(prefs)
        restored = extract_provider_preferences({"provider": wire})
        assert restored is not None
        assert restored.order == prefs.order
        assert restored.only == prefs.only
        assert restored.ignore == prefs.ignore
        assert restored.allow_fallbacks == prefs.allow_fallbacks
        assert restored.data_collection == prefs.data_collection
        assert restored.quantizations == prefs.quantizations
        assert restored.sort == prefs.sort
        assert restored.max_price.prompt == prefs.max_price.prompt
        assert restored.max_price.completion == prefs.max_price.completion
