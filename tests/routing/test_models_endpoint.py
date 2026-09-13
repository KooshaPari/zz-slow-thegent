"""Tests for the /v1/models endpoint fix for Codex 0.104.0 compatibility.

Codex 0.104.0 requires:
- GET /v1/models -> {"fetched_at": "...", "client_version": "...", "models": [...]}
  (Codex API format with "models" key — NOT OpenAI "data" key)
- x-models-etag response header (SHA256 of sorted model IDs)
- Each model has the full Codex metadata schema (slug, shell_type, supported_reasoning_levels, etc.)

Coverage:
- @trace FR-PROXY-001  Models response uses Codex "models" key
- @trace FR-PROXY-002  x-models-etag header present and correct
- @trace FR-PROXY-003  Model metadata enrichment (full Codex schema fields)
- @trace FR-PROXY-004  Handles "models" key input (from CLIProxy native format)
- @trace FR-PROXY-005  Handles "data" key input (OpenAI-standard format from upstream)
- @trace FR-PROXY-006  ETag is deterministic and changes when model list changes
- @trace FR-PROXY-007  Malformed input returns None
"""

from __future__ import annotations

import hashlib

import orjson as json

from thegent.cliproxy_adapter import _compute_models_etag, _transform_models_response

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_MODELS_WITH_DATA_KEY = [
    {"id": "gpt-5.3-codex-spark", "object": "model", "created": 1770912000, "owned_by": "openai"},
    {"id": "gpt-5.3-codex", "object": "model", "created": 1770307200, "owned_by": "openai"},
    {"id": "claude-haiku-4.5", "object": "model", "created": 1732752000, "owned_by": "anthropic"},
]

SAMPLE_MODELS_WITH_MODELS_KEY = [
    {"id": "gemini-3-flash", "object": "model", "created": 1771580291, "owned_by": "antigravity"},
    {"id": "gpt-4o", "object": "model", "created": 1771574764, "owned_by": "zen"},
]


def _make_cliproxy_response(models: list, key: str = "data") -> bytes:
    """Produce a CLIProxy-format /v1/models response body."""
    return json.dumps({"object": "list", key: models}).decode().encode()


# ---------------------------------------------------------------------------
# _compute_models_etag
# ---------------------------------------------------------------------------


class TestComputeModelsEtag:
    """@trace FR-PROXY-002"""

    def test_returns_sha256_hex_string(self) -> None:
        models = [{"id": "gpt-5.3-codex"}, {"id": "claude-haiku-4.5"}]
        etag = _compute_models_etag(models)
        assert isinstance(etag, str)
        assert len(etag) == 64  # SHA256 hex digest length

    def test_deterministic_for_same_ids(self) -> None:
        models = [{"id": "gpt-5.3-codex"}, {"id": "claude-haiku-4.5"}]
        etag1 = _compute_models_etag(models)
        etag2 = _compute_models_etag(models)
        assert etag1 == etag2

    def test_order_independent(self) -> None:
        """ETag sorts model IDs so order of the list does not matter."""
        models_a = [{"id": "gpt-5.3-codex"}, {"id": "claude-haiku-4.5"}]
        models_b = [{"id": "claude-haiku-4.5"}, {"id": "gpt-5.3-codex"}]
        assert _compute_models_etag(models_a) == _compute_models_etag(models_b)

    def test_changes_when_model_added(self) -> None:
        """@trace FR-PROXY-006"""
        models_before = [{"id": "gpt-5.3-codex"}]
        models_after = [{"id": "gpt-5.3-codex"}, {"id": "new-model"}]
        assert _compute_models_etag(models_before) != _compute_models_etag(models_after)

    def test_matches_manual_sha256(self) -> None:
        models = [{"id": "gpt-5.3-codex"}, {"id": "claude-haiku-4.5"}]
        expected = hashlib.sha256(",".join(sorted(["gpt-5.3-codex", "claude-haiku-4.5"])).encode()).hexdigest()
        assert _compute_models_etag(models) == expected

    def test_skips_non_dict_entries(self) -> None:
        """Non-dict entries in the list do not cause errors."""
        models = [{"id": "gpt-5.3-codex"}, "not-a-dict", None]
        etag = _compute_models_etag(models)
        assert len(etag) == 64

    def test_empty_list(self) -> None:
        etag = _compute_models_etag([])
        expected = hashlib.sha256(b"").hexdigest()
        assert etag == expected


# ---------------------------------------------------------------------------
# _transform_models_response - output format
# ---------------------------------------------------------------------------


class TestTransformModelsResponseFormat:
    """@trace FR-PROXY-001"""

    def test_uses_models_key_not_data_key(self) -> None:
        """Codex 0.104.0 requires 'models' key in the response body (Codex API format)."""
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY, key="data")
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert "models" in parsed, "Response must contain 'models' key for Codex 0.104.0"
        assert "data" not in parsed, "'data' key must NOT be present; Codex 0.104.0 uses 'models'"

    def test_input_with_models_key_is_preserved(self) -> None:
        """CLIProxy native format uses 'models' key; adapter preserves it."""
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_MODELS_KEY, key="models")
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert "models" in parsed
        assert "data" not in parsed
        assert len(parsed["models"]) == len(SAMPLE_MODELS_WITH_MODELS_KEY)

    def test_has_fetched_at_field(self) -> None:
        """Response includes fetched_at field (Codex API format)."""
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert "fetched_at" in parsed

    def test_model_list_preserved(self) -> None:
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        ids = {m["id"] for m in parsed["models"]}
        expected_ids = {m["id"] for m in SAMPLE_MODELS_WITH_DATA_KEY}
        assert ids == expected_ids

    def test_model_standard_fields_present(self) -> None:
        """Each model retains id, object, created, owned_by."""
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        for model in parsed["models"]:
            assert "id" in model
            assert "object" in model
            assert "created" in model
            assert "owned_by" in model


# ---------------------------------------------------------------------------
# _transform_models_response - ETag header
# ---------------------------------------------------------------------------


class TestTransformModelsResponseEtag:
    """@trace FR-PROXY-002"""

    def test_returns_etag(self) -> None:
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY)
        result = _transform_models_response(content)
        assert result is not None
        _, etag = result
        assert isinstance(etag, str)
        assert len(etag) == 64

    def test_etag_matches_compute_function(self) -> None:
        content = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY)
        result = _transform_models_response(content)
        assert result is not None
        body, etag = result
        parsed = json.loads(body)
        expected_etag = _compute_models_etag(parsed["models"])
        assert etag == expected_etag

    def test_etag_changes_with_different_models(self) -> None:
        """@trace FR-PROXY-006"""
        content_a = _make_cliproxy_response(SAMPLE_MODELS_WITH_DATA_KEY)
        content_b = _make_cliproxy_response(SAMPLE_MODELS_WITH_MODELS_KEY)
        result_a = _transform_models_response(content_a)
        result_b = _transform_models_response(content_b)
        assert result_a is not None
        assert result_b is not None
        _, etag_a = result_a
        _, etag_b = result_b
        assert etag_a != etag_b


# ---------------------------------------------------------------------------
# _transform_models_response - Codex schema enrichment
# ---------------------------------------------------------------------------


class TestTransformModelsResponseCodexSchema:
    """@trace FR-PROXY-003 - All required Codex schema fields"""

    REQUIRED_CODEX_FIELDS = (
        "slug",
        "display_name",
        "shell_type",
        "visibility",
        "supported_in_api",
        "supported_reasoning_levels",
        "prefer_websockets",
        "context_window",
        "apply_patch_tool_type",
        "supports_parallel_tool_calls",
        "input_modalities",
    )

    def test_all_required_codex_fields_present(self) -> None:
        """Every model must have the full Codex metadata schema."""
        models = [{"id": "gpt-5.3-codex-spark", "object": "model", "created": 1770912000, "owned_by": "openai"}]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        model = parsed["models"][0]
        for field in self.REQUIRED_CODEX_FIELDS:
            assert field in model, f"Required Codex field '{field}' missing from model"

    def test_enriches_known_model_with_context_window(self) -> None:
        """Known models (in model_metadata.py) get context_window added."""
        models = [{"id": "gpt-5.3-codex-spark", "object": "model", "created": 1770912000, "owned_by": "openai"}]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        model = parsed["models"][0]
        assert "context_window" in model
        assert model["context_window"] == 128000

    def test_enriches_known_model_with_max_completion_tokens(self) -> None:
        models = [{"id": "gpt-5.3-codex", "object": "model", "created": 1770307200, "owned_by": "openai"}]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        model = parsed["models"][0]
        assert "max_completion_tokens" in model
        assert model["max_completion_tokens"] == min(128000, 8192)

    def test_does_not_overwrite_existing_context_window(self) -> None:
        """If the model already has context_window, do not overwrite."""
        models = [
            {
                "id": "gpt-5.3-codex",
                "object": "model",
                "created": 1770307200,
                "owned_by": "openai",
                "context_window": 999,
            }
        ]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert parsed["models"][0]["context_window"] == 999

    def test_unknown_model_gets_slug_and_defaults(self) -> None:
        """Unknown models get slug and all default Codex fields."""
        models = [{"id": "unknown-future-model-xyz", "object": "model", "created": 1, "owned_by": "unknown"}]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        model = parsed["models"][0]
        assert model["slug"] == "unknown-future-model-xyz"
        assert model["shell_type"] == "shell_command"
        assert model["prefer_websockets"] is False
        assert isinstance(model["supported_reasoning_levels"], list)

    def test_known_model_gets_slug(self) -> None:
        models = [{"id": "claude-haiku-4.5", "object": "model", "created": 1732752000, "owned_by": "anthropic"}]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert parsed["models"][0]["slug"] == "claude-haiku-4.5"

    def test_does_not_overwrite_existing_slug(self) -> None:
        """Existing slug is preserved."""
        models = [
            {
                "id": "gpt-5.3-codex",
                "object": "model",
                "created": 1770307200,
                "owned_by": "openai",
                "slug": "custom-slug",
            }
        ]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert parsed["models"][0]["slug"] == "custom-slug"


# ---------------------------------------------------------------------------
# _transform_models_response - error / edge cases
# ---------------------------------------------------------------------------


class TestTransformModelsResponseEdgeCases:
    """@trace FR-PROXY-007"""

    def test_malformed_json_returns_none(self) -> None:
        result = _transform_models_response(b"not-json{{{")
        assert result is None

    def test_empty_bytes_returns_none(self) -> None:
        result = _transform_models_response(b"")
        assert result is None

    def test_empty_model_list(self) -> None:
        content = _make_cliproxy_response([])
        result = _transform_models_response(content)
        assert result is not None
        body, etag = result
        parsed = json.loads(body)
        assert parsed["models"] == []
        assert len(etag) == 64

    def test_non_list_data_returns_none(self) -> None:
        content = json.dumps({"object": "list", "data": "not-a-list"}).decode().encode()
        result = _transform_models_response(content)
        assert result is None

    def test_missing_model_id_skipped_gracefully(self) -> None:
        """Models without 'id' are preserved but not enriched."""
        models = [
            {"object": "model", "created": 1, "owned_by": "unknown"},  # no id
            {"id": "gpt-5.3-codex", "object": "model", "created": 1770307200, "owned_by": "openai"},
        ]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        assert len(parsed["models"]) == 2

    def test_model_with_slash_id_tries_suffix_lookup(self) -> None:
        """For models like 'z-ai/glm-5', tries suffix lookup 'glm-5'."""
        models = [{"id": "z-ai/glm-5", "object": "model", "created": 1771574763, "owned_by": "nim"}]
        content = _make_cliproxy_response(models)
        result = _transform_models_response(content)
        assert result is not None
        body, _ = result
        parsed = json.loads(body)
        model = parsed["models"][0]
        # Should have slug at minimum
        assert "slug" in model
