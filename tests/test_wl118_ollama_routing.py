"""WL-118 Ollama routing slice tests."""

from __future__ import annotations

import pytest

from thegent.models.catalog import Route, resolve_route
from thegent.utils.routing_impl.litellm_router import _route_to_litellm_config
from thegent.utils.routing_impl.provider_types import normalize_provider_name


@pytest.mark.parametrize(
    "alias", ["ollama-local", "local-ollama", "ollama-localhost", "ollama@localhost"]
)
def test_resolve_route_supports_ollama_provider_hint_aliases(alias: str) -> None:
    route = resolve_route("llama3.3", provider_hint=alias)
    assert route == ("ollama", "llama3.3")


def test_litellm_config_sets_local_ollama_api_base() -> None:
    route = Route(
        provider=normalize_provider_name("ollama-local"),
        backend_type="direct",
        model_alias="llama3.3",
    )
    conf = _route_to_litellm_config(route)
    assert conf["litellm_params"]["model"] == "ollama/llama3.3"
    assert conf["litellm_params"]["api_base"] == "http://127.0.0.1:11434/v1"
