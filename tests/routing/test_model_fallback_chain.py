"""Tests for GW-12: model fallback chain via models[] array.

@trace FR-ROUTE-012
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

# ---------------------------------------------------------------------------
# Helper factories (shared with other routing tests)
# ---------------------------------------------------------------------------


def _make_message_item(role: str = "user", content: Any = "Hello") -> dict[str, Any]:
    return {"type": "message", "role": role, "content": content}


def _make_responses_body(
    model: str = "gpt-4o",
    input_items: list[dict] | None = None,
    stream: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "input": input_items if input_items is not None else [_make_message_item()],
        "stream": stream,
    }
    body.update(kwargs)
    return body


# ---------------------------------------------------------------------------
# Test: models[] sets primary model
# ---------------------------------------------------------------------------


class TestModelsArraySetsPrimaryModel:
    """GW-12: When models[] is present, the first entry becomes the primary model.

    @trace FR-ROUTE-012
    """

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_models_array_sets_primary_model(self) -> None:
        """When request has models: [gpt-4o, claude-sonnet-4.6], primary model is gpt-4o."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = _make_responses_body(
            model="gpt-4o",
            models=["gpt-4o", "claude-sonnet-4.6"],
        )
        result = _responses_to_chat_completions(body)
        # Primary model is the first entry from models[]
        assert result["model"] == "gpt-4o"

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_models_array_primary_overrides_empty_model(self) -> None:
        """When model is absent but models[] is present, first models[] entry becomes model."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = {
            "model": "",
            "input": [_make_message_item()],
            "stream": False,
            "models": ["claude-sonnet-4.6", "gpt-4o"],
        }
        result = _responses_to_chat_completions(body)
        assert result["model"] == "claude-sonnet-4.6"

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_single_model_in_models_array(self) -> None:
        """A single-entry models[] still sets the primary model correctly."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = _make_responses_body(model="gpt-4o", models=["gpt-4o"])
        result = _responses_to_chat_completions(body)
        assert result["model"] == "gpt-4o"


# ---------------------------------------------------------------------------
# Test: _responses_to_chat_completions extracts _models
# ---------------------------------------------------------------------------


class TestResponsesToChatCompletionsExtractsModels:
    """GW-12: _responses_to_chat_completions stores models[] as _models.

    @trace FR-ROUTE-012
    """

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_responses_to_chat_completions_extracts_models(self) -> None:
        """Verify _responses_to_chat_completions stores _models in output."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = _make_responses_body(
            model="gpt-4o",
            models=["gpt-4o", "claude-sonnet-4.6", "deepseek-v3.2"],
        )
        result = _responses_to_chat_completions(body)
        assert "_models" in result
        assert result["_models"] == ["gpt-4o", "claude-sonnet-4.6", "deepseek-v3.2"]

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_no_models_array_no_underscore_models_key(self) -> None:
        """When models[] is absent, _models key is not present in output."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = _make_responses_body(model="gpt-4o")
        result = _responses_to_chat_completions(body)
        assert "_models" not in result

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_empty_models_array_produces_no_underscore_models(self) -> None:
        """An empty models[] list must not produce _models in output."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = _make_responses_body(model="gpt-4o", models=[])
        result = _responses_to_chat_completions(body)
        assert "_models" not in result

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_models_key_not_forwarded_as_plain_models(self) -> None:
        """The raw 'models' key must not appear in the output (it becomes _models)."""
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _responses_to_chat_completions,
        )

        body = _make_responses_body(
            model="gpt-4o",
            models=["gpt-4o", "claude-sonnet-4.6"],
        )
        result = _responses_to_chat_completions(body)
        # 'models' as a plain passthrough key should not be present;
        # only _models should carry the fallback chain.
        assert "models" not in result


# ---------------------------------------------------------------------------
# Test: build_dynamic_fallback_router returns a Router
# ---------------------------------------------------------------------------


class TestBuildDynamicFallbackRouter:
    """GW-12: build_dynamic_fallback_router returns a LiteLLM Router.

    @trace FR-ROUTE-012
    """

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_build_dynamic_fallback_router_returns_router(self) -> None:
        """Calling build_dynamic_fallback_router with valid models returns a LiteLLM Router."""
        from litellm import Router

        from thegent.utils.routing_impl.litellm_router import (
            build_dynamic_fallback_router,
        )

        # Patch build_litellm_model_list to avoid real catalog dependency
        minimal_model_list = [
            {
                "model_name": "gpt-4o",
                "litellm_params": {
                    "model": "openai/gpt-4o",
                    "api_key": "dummy",
                },
            },
            {
                "model_name": "claude-sonnet-4.6",
                "litellm_params": {
                    "model": "anthropic/claude-sonnet-4.6",
                    "api_key": "dummy",
                },
            },
        ]
        with patch(
            "thegent.utils.routing_impl.litellm_router.build_litellm_model_list",
            return_value=minimal_model_list,
        ):
            router = build_dynamic_fallback_router(["gpt-4o", "claude-sonnet-4.6"])

        assert isinstance(router, Router)

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_build_dynamic_fallback_router_configures_fallbacks(self) -> None:
        """The returned Router has fallbacks configured with primary -> rest."""
        from litellm import Router

        from thegent.utils.routing_impl.litellm_router import (
            build_dynamic_fallback_router,
        )

        minimal_model_list = [
            {
                "model_name": "gpt-4o",
                "litellm_params": {"model": "openai/gpt-4o", "api_key": "dummy"},
            },
            {
                "model_name": "claude-sonnet-4.6",
                "litellm_params": {
                    "model": "anthropic/claude-sonnet-4.6",
                    "api_key": "dummy",
                },
            },
            {
                "model_name": "deepseek-v3.2",
                "litellm_params": {"model": "openai/deepseek-v3.2", "api_key": "dummy"},
            },
        ]
        with patch(
            "thegent.utils.routing_impl.litellm_router.build_litellm_model_list",
            return_value=minimal_model_list,
        ):
            router = build_dynamic_fallback_router(
                ["gpt-4o", "claude-sonnet-4.6", "deepseek-v3.2"]
            )

        assert isinstance(router, Router)
        # Verify fallback configuration is present
        assert router.fallbacks is not None
        assert len(router.fallbacks) == 1
        assert "gpt-4o" in router.fallbacks[0]
        assert router.fallbacks[0]["gpt-4o"] == ["claude-sonnet-4.6", "deepseek-v3.2"]

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_build_dynamic_fallback_router_empty_list_raises(self) -> None:
        """Passing an empty models list must raise ValueError immediately."""
        from thegent.utils.routing_impl.litellm_router import (
            build_dynamic_fallback_router,
        )

        with pytest.raises(ValueError, match="models list must not be empty"):
            build_dynamic_fallback_router([])

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_build_dynamic_fallback_router_unknown_model_uses_passthrough(self) -> None:
        """Unknown models not in catalog get a minimal passthrough config, not a silent skip."""
        from litellm import Router

        from thegent.utils.routing_impl.litellm_router import (
            build_dynamic_fallback_router,
        )

        # Empty catalog — all models unknown
        with patch(
            "thegent.utils.routing_impl.litellm_router.build_litellm_model_list",
            return_value=[],
        ):
            router = build_dynamic_fallback_router(
                ["unknown-model-x", "unknown-model-y"]
            )

        assert isinstance(router, Router)
        # Both unknown models should appear in model_list with passthrough config
        model_names = [entry["model_name"] for entry in router.model_list]
        assert "unknown-model-x" in model_names
        assert "unknown-model-y" in model_names


# ---------------------------------------------------------------------------
# Test: single model uses default router
# ---------------------------------------------------------------------------


class TestSingleModelUsesDefaultRouter:
    """GW-12: When only one model is specified, default get_litellm_router() is used.

    @trace FR-ROUTE-012
    """

    @pytest.mark.requirement("FR-ROUTE-012")
    @pytest.mark.asyncio
    async def test_single_model_uses_default_router(self) -> None:
        """Single model[] or no models[] uses get_litellm_router, not build_dynamic_fallback_router."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "response from single model"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.id = "resp_single"
        mock_response.model = "gpt-4o"

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = json.dumps(
            _make_responses_body(model="gpt-4o", models=["gpt-4o"]).decode()
        ).encode()

        dynamic_router_call_count = 0

        def _track_dynamic(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal dynamic_router_call_count
            dynamic_router_call_count += 1
            return mock_router

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.build_dynamic_fallback_router",
                side_effect=_track_dynamic,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(
                routes=[
                    Route("/v1/responses", handle_responses_request, methods=["POST"])
                ]
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        # Dynamic router must NOT have been called for a single-model request
        assert dynamic_router_call_count == 0

    @pytest.mark.requirement("FR-ROUTE-012")
    @pytest.mark.asyncio
    async def test_no_models_array_uses_default_router(self) -> None:
        """When models[] is absent entirely, get_litellm_router is used."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "plain response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.id = "resp_plain"
        mock_response.model = "gpt-4o"

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = json.dumps(_make_responses_body(model="gpt-4o").decode()).encode()

        dynamic_router_call_count = 0

        def _track_dynamic(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal dynamic_router_call_count
            dynamic_router_call_count += 1
            return mock_router

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.build_dynamic_fallback_router",
                side_effect=_track_dynamic,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(
                routes=[
                    Route("/v1/responses", handle_responses_request, methods=["POST"])
                ]
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        assert dynamic_router_call_count == 0


# ---------------------------------------------------------------------------
# Test: multi-model request uses dynamic router
# ---------------------------------------------------------------------------


class TestMultiModelUsesDynamicRouter:
    """GW-12: When models[] has 2+ entries, build_dynamic_fallback_router is used.

    @trace FR-ROUTE-012
    """

    @pytest.mark.requirement("FR-ROUTE-012")
    @pytest.mark.asyncio
    async def test_multi_model_uses_dynamic_fallback_router(self) -> None:
        """Request with models: [A, B, C] invokes build_dynamic_fallback_router."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "multi-model response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.id = "resp_multi"
        mock_response.model = "gpt-4o"

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = (
            json.dumps(
                _make_responses_body(
                    model="gpt-4o",
                    models=["gpt-4o", "claude-sonnet-4.6", "deepseek-v3.2"],
                )
            )
            .decode()
            .encode()
        )

        captured_models: list[list[str]] = []

        def _capture_dynamic(models: list[str], **kwargs: Any) -> MagicMock:
            captured_models.append(list(models))
            return mock_router

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.build_dynamic_fallback_router",
                side_effect=_capture_dynamic,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(
                routes=[
                    Route("/v1/responses", handle_responses_request, methods=["POST"])
                ]
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        assert len(captured_models) == 1
        assert captured_models[0] == ["gpt-4o", "claude-sonnet-4.6", "deepseek-v3.2"]

    @pytest.mark.requirement("FR-ROUTE-012")
    @pytest.mark.asyncio
    async def test_multi_model_fallback_params_injected_to_acompletion(self) -> None:
        """router.acompletion receives fallbacks= kwarg when models[] has 2+ entries."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "ok"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.id = "resp_fb"
        mock_response.model = "gpt-4o"

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = (
            json.dumps(
                _make_responses_body(
                    model="gpt-4o",
                    models=["gpt-4o", "claude-sonnet-4.6"],
                )
            )
            .decode()
            .encode()
        )

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.build_dynamic_fallback_router",
                return_value=mock_router,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(
                routes=[
                    Route("/v1/responses", handle_responses_request, methods=["POST"])
                ]
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        call_kwargs = mock_router.acompletion.call_args.kwargs
        # fallbacks kwarg must be present and contain the right structure
        assert "fallbacks" in call_kwargs
        assert call_kwargs["fallbacks"] == [{"gpt-4o": ["claude-sonnet-4.6"]}]


# ---------------------------------------------------------------------------
# Test: _build_fallback_chain_extra helper
# ---------------------------------------------------------------------------


class TestBuildFallbackChainExtra:
    """GW-12: _build_fallback_chain_extra returns correct extra kwargs.

    @trace FR-ROUTE-012
    """

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_two_models_returns_fallbacks_dict(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _build_fallback_chain_extra,
        )

        result = _build_fallback_chain_extra(["gpt-4o", "claude-sonnet-4.6"], "gpt-4o")
        assert result == {"fallbacks": [{"gpt-4o": ["claude-sonnet-4.6"]}]}

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_three_models_fallbacks_contains_all_non_primary(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _build_fallback_chain_extra,
        )

        result = _build_fallback_chain_extra(
            ["gpt-4o", "claude-sonnet-4.6", "deepseek-v3.2"], "gpt-4o"
        )
        assert result == {
            "fallbacks": [{"gpt-4o": ["claude-sonnet-4.6", "deepseek-v3.2"]}]
        }

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_single_model_returns_empty_dict(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _build_fallback_chain_extra,
        )

        result = _build_fallback_chain_extra(["gpt-4o"], "gpt-4o")
        assert result == {}

    @pytest.mark.requirement("FR-ROUTE-012")
    def test_empty_models_returns_empty_dict(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _build_fallback_chain_extra,
        )

        result = _build_fallback_chain_extra([], "gpt-4o")
        assert result == {}
