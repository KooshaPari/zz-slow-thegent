"""WL-118 Ollama local provider tests.

Tests cover:
- ollama_provider module: availability detection, model discovery, alias resolution,
  litellm entry building, and OllamaUnavailableError propagation
- harness_model_mapping: OLLAMA_MODEL_ALIASES dict and resolver helpers
- model_metadata: Ollama model entries registered with cost_per_mtok == 0.0
- provider_types: normalization and execution-path classification
- litellm_router: api_base and model prefix for Ollama routes

# @trace WL-118
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# ollama_provider module
# ---------------------------------------------------------------------------


class TestIsOllamaAvailable:
    """Tests for ollama_provider.is_ollama_available."""

    def test_returns_true_on_http_200(self) -> None:
        """is_ollama_available returns True when daemon responds 200."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import is_ollama_available

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=mock_resp):
            assert is_ollama_available() is True

    def test_returns_false_on_non_200(self) -> None:
        """is_ollama_available returns False when daemon returns non-200."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import is_ollama_available

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=mock_resp):
            assert is_ollama_available() is False

    def test_returns_false_on_connect_error(self) -> None:
        """is_ollama_available returns False when daemon is not reachable."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import is_ollama_available

        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", side_effect=httpx.ConnectError("refused")):
            assert is_ollama_available() is False

    def test_returns_false_on_timeout(self) -> None:
        """is_ollama_available returns False on timeout."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import is_ollama_available

        with patch(
            "thegent.utils.routing_impl.ollama_provider.httpx.get",
            side_effect=httpx.TimeoutException("timed out"),
        ):
            assert is_ollama_available() is False

    def test_probes_correct_endpoint(self) -> None:
        """is_ollama_available probes /api/tags at localhost:11434."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import (
            OLLAMA_TAGS_ENDPOINT,
            is_ollama_available,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=mock_resp) as mock_get:
            is_ollama_available()
            call_url = mock_get.call_args[0][0]
            assert call_url == OLLAMA_TAGS_ENDPOINT
            assert "11434" in call_url
            assert "/api/tags" in call_url


class TestGetAvailableModels:
    """Tests for ollama_provider.get_available_models."""

    def _make_response(self, status_code: int, models: list[dict]) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.content = b"x"
        resp.json.return_value = {"models": models}
        return resp

    def test_returns_sorted_model_names(self) -> None:
        """get_available_models returns sorted model names."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import get_available_models

        resp = self._make_response(200, [{"name": "mistral:latest"}, {"name": "llama3.3:latest"}])
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=resp):
            models = get_available_models()
        assert models == ["llama3.3", "mistral"]

    def test_strips_tag_suffix(self) -> None:
        """get_available_models strips :tag suffix (e.g. 'llama3.3:latest' -> 'llama3.3')."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import get_available_models

        resp = self._make_response(200, [{"name": "qwen2.5-coder:7b"}])
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=resp):
            models = get_available_models()
        assert "qwen2.5-coder" in models

    def test_returns_empty_list_when_no_models(self) -> None:
        """get_available_models returns [] when models array is empty."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import get_available_models

        resp = self._make_response(200, [])
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=resp):
            assert get_available_models() == []

    def test_raises_on_connect_error(self) -> None:
        """get_available_models raises OllamaUnavailableError on ConnectError."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import (
            OllamaUnavailableError,
            get_available_models,
        )

        with patch(
            "thegent.utils.routing_impl.ollama_provider.httpx.get",
            side_effect=httpx.ConnectError("refused"),
        ), pytest.raises(OllamaUnavailableError):
            get_available_models()

    def test_raises_on_non_200(self) -> None:
        """get_available_models raises OllamaUnavailableError on non-200 response."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import (
            OllamaUnavailableError,
            get_available_models,
        )

        resp = MagicMock()
        resp.status_code = 500
        resp.content = b""
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=resp):
            with pytest.raises(OllamaUnavailableError, match="HTTP 500"):
                get_available_models()

    def test_deduplicates_model_names(self) -> None:
        """get_available_models deduplicates when same base name appears multiple times."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import get_available_models

        resp = self._make_response(200, [{"name": "mistral:latest"}, {"name": "mistral:7b"}])
        with patch("thegent.utils.routing_impl.ollama_provider.httpx.get", return_value=resp):
            models = get_available_models()
        assert models.count("mistral") == 1


class TestAssertOllamaAvailable:
    """Tests for ollama_provider.assert_ollama_available."""

    def test_does_not_raise_when_available(self) -> None:
        """assert_ollama_available does not raise when is_ollama_available returns True."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import assert_ollama_available

        with patch("thegent.utils.routing_impl.ollama_provider.is_ollama_available", return_value=True):
            assert_ollama_available()  # should not raise

    def test_raises_when_unavailable(self) -> None:
        """assert_ollama_available raises OllamaUnavailableError when daemon is down."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import (
            OllamaUnavailableError,
            assert_ollama_available,
        )

        with patch("thegent.utils.routing_impl.ollama_provider.is_ollama_available", return_value=False):
            with pytest.raises(OllamaUnavailableError):
                assert_ollama_available()

    def test_error_message_mentions_ollama_serve(self) -> None:
        """assert_ollama_available error message includes actionable instructions."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import (
            OllamaUnavailableError,
            assert_ollama_available,
        )

        with patch("thegent.utils.routing_impl.ollama_provider.is_ollama_available", return_value=False):
            with pytest.raises(OllamaUnavailableError, match="ollama serve"):
                assert_ollama_available()


class TestResolveOllamaModel:
    """Tests for ollama_provider.resolve_ollama_model."""

    def test_strips_ollama_prefix(self) -> None:
        """resolve_ollama_model strips 'ollama/' prefix."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import resolve_ollama_model

        assert resolve_ollama_model("ollama/llama3.3") == "llama3.3"

    def test_returns_alias_for_known_model(self) -> None:
        """resolve_ollama_model returns canonical name for known aliases."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import resolve_ollama_model

        assert resolve_ollama_model("mistral") == "mistral"

    def test_passthrough_for_unknown_model(self) -> None:
        """resolve_ollama_model passes through unknown model names unchanged."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import resolve_ollama_model

        assert resolve_ollama_model("some-custom-model:tag") == "some-custom-model:tag"

    def test_known_aliases_include_qwen_coder(self) -> None:
        """resolve_ollama_model knows about qwen2.5-coder alias."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import resolve_ollama_model

        assert resolve_ollama_model("qwen2.5-coder") == "qwen2.5-coder"


class TestBuildLitellmEntry:
    """Tests for ollama_provider.build_litellm_entry."""

    def test_model_name_set_to_canonical(self) -> None:
        """build_litellm_entry sets model_name to canonical Ollama model name."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import build_litellm_entry

        entry = build_litellm_entry("llama3.3")
        assert entry["model_name"] == "llama3.3"

    def test_litellm_model_has_ollama_prefix(self) -> None:
        """build_litellm_entry sets litellm_params.model to 'ollama/<name>'."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import build_litellm_entry

        entry = build_litellm_entry("mistral")
        assert entry["litellm_params"]["model"] == "ollama/mistral"  # type: ignore[index]

    def test_api_base_points_to_localhost(self) -> None:
        """build_litellm_entry sets api_base to http://localhost:11434/v1."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import (
            OLLAMA_OPENAI_BASE,
            build_litellm_entry,
        )

        entry = build_litellm_entry("llama3.3")
        assert entry["litellm_params"]["api_base"] == OLLAMA_OPENAI_BASE  # type: ignore[index]
        assert "11434/v1" in entry["litellm_params"]["api_base"]  # type: ignore[index]

    def test_api_key_is_sentinel(self) -> None:
        """build_litellm_entry uses a sentinel api_key (Ollama needs no real key)."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import build_litellm_entry

        entry = build_litellm_entry("llama3.3")
        key = entry["litellm_params"]["api_key"]  # type: ignore[index]
        assert isinstance(key, str)
        assert len(key) > 0

    def test_strips_prefix_before_building(self) -> None:
        """build_litellm_entry strips 'ollama/' prefix when resolving model name."""
        # @trace WL-118
        from thegent.utils.routing_impl.ollama_provider import build_litellm_entry

        entry_with_prefix = build_litellm_entry("ollama/mistral")
        entry_plain = build_litellm_entry("mistral")
        assert entry_with_prefix["model_name"] == entry_plain["model_name"]


# ---------------------------------------------------------------------------
# harness_model_mapping: OLLAMA_MODEL_ALIASES
# ---------------------------------------------------------------------------


class TestOllamaModelAliasesMapping:
    """Tests for OLLAMA_MODEL_ALIASES in harness_model_mapping."""

    def test_llama33_alias_present(self) -> None:
        """OLLAMA_MODEL_ALIASES includes llama3.3."""
        # @trace WL-118
        from thegent.utils.routing_impl.harness_model_mapping import (
            OLLAMA_MODEL_ALIASES,
        )

        assert "llama3.3" in OLLAMA_MODEL_ALIASES

    def test_qwen_coder_alias_present(self) -> None:
        """OLLAMA_MODEL_ALIASES includes qwen2.5-coder."""
        # @trace WL-118
        from thegent.utils.routing_impl.harness_model_mapping import (
            OLLAMA_MODEL_ALIASES,
        )

        assert "qwen2.5-coder" in OLLAMA_MODEL_ALIASES

    def test_mistral_alias_present(self) -> None:
        """OLLAMA_MODEL_ALIASES includes mistral."""
        # @trace WL-118
        from thegent.utils.routing_impl.harness_model_mapping import (
            OLLAMA_MODEL_ALIASES,
        )

        assert "mistral" in OLLAMA_MODEL_ALIASES

    def test_resolve_ollama_model_alias_strips_prefix(self) -> None:
        """resolve_ollama_model_alias strips 'ollama/' prefix before lookup."""
        # @trace WL-118
        from thegent.utils.routing_impl.harness_model_mapping import (
            resolve_ollama_model_alias,
        )

        assert resolve_ollama_model_alias("ollama/llama3.3") == "llama3.3"

    def test_resolve_ollama_model_alias_passthrough_unknown(self) -> None:
        """resolve_ollama_model_alias passes through unregistered model names."""
        # @trace WL-118
        from thegent.utils.routing_impl.harness_model_mapping import (
            resolve_ollama_model_alias,
        )

        assert resolve_ollama_model_alias("my-custom-model") == "my-custom-model"

    def test_get_ollama_models_returns_list(self) -> None:
        """get_ollama_models returns a non-empty list of string aliases."""
        # @trace WL-118
        from thegent.utils.routing_impl.harness_model_mapping import get_ollama_models

        models = get_ollama_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, str) for m in models)


# ---------------------------------------------------------------------------
# model_metadata: Ollama models have zero cost
# ---------------------------------------------------------------------------


class TestOllamaModelMetadata:
    """Tests for Ollama model entries in MODEL_METADATA."""

    def test_llama33_metadata_has_zero_cost(self) -> None:
        """llama3.3 metadata has cost_per_mtok == 0.0 (zero-cost local execution)."""
        # @trace WL-118
        from thegent.utils.routing_impl.model_metadata import get_model_metadata

        meta = get_model_metadata("llama3.3")
        assert meta is not None
        assert meta["cost_per_mtok"] == 0.0

    def test_llama33_metadata_provider_is_ollama(self) -> None:
        """llama3.3 metadata identifies provider as 'ollama'."""
        # @trace WL-118
        from thegent.utils.routing_impl.model_metadata import get_model_metadata

        meta = get_model_metadata("llama3.3")
        assert meta is not None
        assert meta["provider"] == "ollama"

    def test_mistral_metadata_has_zero_cost(self) -> None:
        """mistral metadata has cost_per_mtok == 0.0."""
        # @trace WL-118
        from thegent.utils.routing_impl.model_metadata import get_model_metadata

        meta = get_model_metadata("mistral")
        assert meta is not None
        assert meta["cost_per_mtok"] == 0.0

    def test_qwen_coder_metadata_registered(self) -> None:
        """qwen2.5-coder metadata is registered."""
        # @trace WL-118
        from thegent.utils.routing_impl.model_metadata import has_model_metadata

        assert has_model_metadata("qwen2.5-coder")


class TestModelMetadataAliases:
    """Tests for backend/provider alias metadata normalization."""

    def test_codex_minimax_alias_resolves_to_minimax_metadata(self) -> None:
        """Backend aliases like codex-MiniMax-M2.5 resolve to minimax metadata."""
        from thegent.utils.routing_impl.model_metadata import get_model_metadata

        assert get_model_metadata("codex-MiniMax-M2.5") is not None
        meta = get_model_metadata("codex-MiniMax-M2.5")
        assert meta is not None
        assert meta["provider"] == "minimax"

    def test_codex_minimax_alias_with_provider_prefix_resolves(self) -> None:
        """Provider wrapper prefixes like custom:codex-MiniMax-M2.5 resolve too."""
        from thegent.utils.routing_impl.model_metadata import get_model_metadata

        meta = get_model_metadata("custom:codex-MiniMax-M2.5")
        assert meta is not None
        assert meta["provider"] == "minimax"

    def test_codex_lowercase_minimax_alias_resolves(self) -> None:
        """Lowercase codex minimax alias resolves to minimax metadata."""
        from thegent.utils.routing_impl.model_metadata import get_model_metadata

        meta = get_model_metadata("codex-minimax-m2.5")
        assert meta is not None
        assert meta["provider"] == "minimax"


# ---------------------------------------------------------------------------
# provider_types: ollama normalization and execution path
# ---------------------------------------------------------------------------


class TestOllamaProviderTypes:
    """Tests for provider_types normalization and execution path for Ollama."""

    def test_normalize_ollama_local_alias(self) -> None:
        """normalize_provider_name maps 'ollama-local' to 'ollama'."""
        # @trace WL-118
        from thegent.utils.routing_impl.provider_types import normalize_provider_name

        assert normalize_provider_name("ollama-local") == "ollama"

    def test_normalize_local_ollama_alias(self) -> None:
        """normalize_provider_name maps 'local-ollama' to 'ollama'."""
        # @trace WL-118
        from thegent.utils.routing_impl.provider_types import normalize_provider_name

        assert normalize_provider_name("local-ollama") == "ollama"

    def test_normalize_ollama_localhost_alias(self) -> None:
        """normalize_provider_name maps 'ollama-localhost' to 'ollama'."""
        # @trace WL-118
        from thegent.utils.routing_impl.provider_types import normalize_provider_name

        assert normalize_provider_name("ollama-localhost") == "ollama"

    def test_normalize_ollama_at_localhost_alias(self) -> None:
        """normalize_provider_name maps 'ollama@localhost' to 'ollama'."""
        # @trace WL-118
        from thegent.utils.routing_impl.provider_types import normalize_provider_name

        assert normalize_provider_name("ollama@localhost") == "ollama"

    def test_ollama_execution_path_is_litellm_api(self) -> None:
        """get_execution_path returns LITELLM_API for 'ollama'."""
        # @trace WL-118
        from thegent.utils.routing_impl.provider_types import (
            ExecutionPath,
            get_execution_path,
        )

        assert get_execution_path("ollama") == ExecutionPath.LITELLM_API

    def test_ollama_in_api_key_providers_set(self) -> None:
        """'ollama' appears in API_KEY_PROVIDERS (routes via LiteLLM, not CLIProxy)."""
        # @trace WL-118
        from thegent.utils.routing_impl.provider_types import API_KEY_PROVIDERS

        assert "ollama" in API_KEY_PROVIDERS


# ---------------------------------------------------------------------------
# litellm_router: Ollama api_base configuration
# ---------------------------------------------------------------------------


class TestLitellmRouterOllama:
    """Tests for _route_to_litellm_config with Ollama routes."""

    def test_ollama_route_sets_api_base(self) -> None:
        """_route_to_litellm_config sets api_base to http://127.0.0.1:11434/v1 for ollama."""
        # @trace WL-118
        # Import Route directly to avoid circular-import via __init__
        from thegent.models.catalog import Route
        from thegent.utils.routing_impl.litellm_router import _route_to_litellm_config
        from thegent.utils.routing_impl.provider_types import normalize_provider_name

        route = Route(
            provider=normalize_provider_name("ollama"),
            backend_type="direct",
            model_alias="llama3.3",
        )
        conf = _route_to_litellm_config(route)
        assert conf["litellm_params"]["api_base"] == "http://127.0.0.1:11434/v1"

    def test_ollama_route_litellm_model_prefix(self) -> None:
        """_route_to_litellm_config sets litellm model as 'ollama/llama3.3'."""
        # @trace WL-118
        from thegent.models.catalog import Route
        from thegent.utils.routing_impl.litellm_router import _route_to_litellm_config
        from thegent.utils.routing_impl.provider_types import normalize_provider_name

        route = Route(
            provider=normalize_provider_name("ollama"),
            backend_type="direct",
            model_alias="llama3.3",
        )
        conf = _route_to_litellm_config(route)
        assert conf["litellm_params"]["model"] == "ollama/llama3.3"
