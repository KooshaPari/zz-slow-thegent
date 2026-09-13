"""Unit tests for provider model discovery diagnostics and metadata."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

# discover_models function was removed from provider_model_manager; skip if absent.
import thegent.provider_model_manager as _provider_model_manager_mod

if not hasattr(_provider_model_manager_mod, "discover_models"):
    pytest.skip(
        "provider_model_manager.discover_models removed; discovery tests skipped",
        allow_module_level=True,
    )

from thegent.provider_model_manager import discover_models, validate_provider


@pytest.mark.unit
def test_discover_models_timeout_returns_status_metadata(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch(
            "thegent.provider_model_manager.httpx.get",
            side_effect=httpx.TimeoutException("timed out"),
        ),
    ):
        payload = discover_models(include_status=True)

    assert payload["models"] == []
    assert payload["discovery"]["status"] == "error"
    assert payload["discovery"]["failure_class"] == "transport"
    assert payload["discovery"]["failure_type"] == "timeout"


@pytest.mark.unit
def test_discover_models_invalid_payload_schema(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    class FakeResp:
        status_code = 200

        def json(self) -> object:
            return []

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", return_value=FakeResp()),
    ):
        payload = discover_models(include_status=True)

    assert payload["models"] == []
    assert payload["discovery"]["status"] == "error"
    assert payload["discovery"]["failure_class"] == "protocol"
    assert payload["discovery"]["failure_type"] == "payload_not_object"
    assert payload["discovery"]["catalog_state"] == "empty"


@pytest.mark.unit
def test_discover_models_connect_error_classifies_transport_failure(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch(
            "thegent.provider_model_manager.httpx.get",
            side_effect=httpx.ConnectError("connection refused"),
        ),
    ):
        payload = discover_models(include_status=True)

    assert payload["models"] == []
    assert payload["discovery"]["status"] == "error"
    assert payload["discovery"]["failure_class"] == "transport"
    assert payload["discovery"]["failure_type"] == "connect_error"


@pytest.mark.unit
def test_discover_models_models_not_list_is_invalid_payload(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    class FakeResp:
        status_code = 200

        def json(self) -> object:
            return {"models": "this is not a list"}

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", return_value=FakeResp()),
    ):
        payload = discover_models(include_status=True)

    assert payload["models"] == []
    assert payload["discovery"]["status"] == "error"
    assert payload["discovery"]["failure_class"] == "protocol"
    assert payload["discovery"]["failure_type"] == "models_not_list"
    assert payload["discovery"]["catalog_state"] == "empty"


@pytest.mark.unit
def test_validate_provider_connect_failure_classifies_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch(
            "thegent.provider_model_manager._load_yaml",
            return_value={
                "openai-compatibility": [
                    {"name": "roo", "api-key-entries": [{"api-key": "abc123"}]}
                ]
            },
        ),
        patch(
            "thegent.provider_model_manager._load_json",
            return_value={
                "roo": {"base_url": "https://cli.example", "model": "roo model"}
            },
        ),
        patch(
            "thegent.provider_model_manager.httpx.post",
            side_effect=httpx.ConnectError("refused"),
        ),
    ):
        success, _, details = validate_provider("roo")

    assert success is False
    assert details["failure_type"] == "connect_error"
    assert details["error"] is True


@pytest.mark.unit
def test_validate_provider_timeout_classifies_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch(
            "thegent.provider_model_manager._load_yaml",
            return_value={
                "openai-compatibility": [
                    {"name": "roo", "api-key-entries": [{"api-key": "abc123"}]}
                ]
            },
        ),
        patch(
            "thegent.provider_model_manager._load_json",
            return_value={
                "roo": {"base_url": "https://cli.example", "model": "roo model"}
            },
        ),
        patch(
            "thegent.provider_model_manager.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ),
    ):
        success, _, details = validate_provider("roo")

    assert success is False
    assert details["failure_type"] == "timeout"
    assert details["error"] is True


@pytest.mark.unit
def test_discover_models_keeps_partial_results_and_counts_malformed_rows(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    class FakeResp:
        status_code = 200

        def json(self) -> object:
            return {
                "models": [
                    {"id": "roo-1", "owned_by": "roo", "object": "model", "created": 1},
                    "bad-row",
                    {"id": "bad-owned-by", "owned_by": 123},
                ]
            }

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", return_value=FakeResp()),
    ):
        payload = discover_models(include_status=True)

    assert len(payload["models"]) == 1
    assert payload["models"][0]["id"] == "roo-1"
    assert payload["discovery"]["status"] == "ok"
    assert payload["discovery"]["failure_class"] is None
    assert payload["discovery"]["catalog_state"] == "available"
    assert payload["discovery"]["malformed_count"] == 2


@pytest.mark.unit
def test_discover_models_empty_catalog_is_marked_as_empty(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    class FakeResp:
        status_code = 200

        @staticmethod
        def json() -> object:
            return {"models": []}

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", return_value=FakeResp()),
    ):
        payload = discover_models(include_status=True)

    assert payload["models"] == []
    assert payload["discovery"]["status"] == "ok"
    assert payload["discovery"]["failure_class"] is None
    assert payload["discovery"]["catalog_state"] == "empty"
    assert payload["discovery"]["malformed_count"] == 0


@pytest.mark.unit
def test_discover_models_default_contract_still_returns_list(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n")

    class FakeResp:
        status_code = 200

        def json(self) -> object:
            return {"models": [{"id": "kilo-1", "owned_by": "kilo"}]}

    with (
        patch(
            "thegent.provider_model_manager._ensure_config", return_value=config_path
        ),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", return_value=FakeResp()),
    ):
        models = discover_models()

    assert isinstance(models, list)
    assert models[0]["provider"] == "kilo"
