"""Tests for LiteLLM Router wrapper."""

from unittest.mock import MagicMock, patch

from thegent.utils.routing_impl.litellm_router import (
    _route_to_litellm_config,
    build_litellm_model_list,
    get_litellm_router,
)


class TestLiteLLMRouterBuilder:
    """Test LiteLLM Router configuration generation."""

    def test_build_model_list_excludes_native_cli(self):
        """Native CLI providers are excluded from LiteLLM model list."""
        model_list = build_litellm_model_list()
        providers_in_list = {cfg.get("model_name", "").split("/")[0] for cfg in model_list}
        # Should not contain codex or claude
        assert "codex" not in providers_in_list
        assert "claude" not in providers_in_list

    def test_build_model_list_includes_api_key_providers(self):
        """API key providers are included in model list."""
        model_list = build_litellm_model_list()
        model_names = [cfg.get("model_name", "") for cfg in model_list]
        # Should have entries for API key providers
        # At least minimax-m2.5 or glm-5 should be present
        assert any("minimax" in m or "glm" in m or "deepseek" in m for m in model_names)

    def test_route_to_litellm_config_api_key_provider(self):
        """API key providers get direct API config."""
        from thegent.models.catalog import Route

        route = Route(
            provider="minimax",
            backend_type="proxy",
            model_alias="minimax-m2.5",
            priority=0,
            cost_weight=0.4,
        )
        config = _route_to_litellm_config(route)
        assert config["model_name"] == "minimax-m2.5"
        # Should use litellm provider prefix
        assert "litellm_params" in config
        assert "model" in config["litellm_params"]

    def test_get_litellm_router_returns_router(self):
        """get_litellm_router returns a Router instance."""
        with patch("thegent.utils.routing_impl.litellm_router.Router") as mock_router:
            mock_router.return_value = MagicMock()
            router = get_litellm_router(policy="cheapest")
            assert router is not None
            mock_router.assert_called_once()
